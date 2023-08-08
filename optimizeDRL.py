import optuna
import numpy as np
import time
import os

from gymnasium import Env
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from stable_baselines3.common.vec_env import DummyVecEnv
from WondersDuelEnv import WondersEnv  # Import your environment and wrapper
from sb3_contrib.common.maskable.utils import get_action_masks
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from Player1Agents import *

from stable_baselines3.common.callbacks import BaseCallback

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

show = False
agent1 = RuleBasedAgent
# agent1 = 'PPO_15M_Random_RuleBased'

class TrackTrainingProgressCallback(BaseCallback):
    def __init__(self):
        super().__init__()
        self.current_step = 0

    def _on_step(self) -> bool:
        self.current_step = self.num_timesteps
        return True

def evaluate(model, num_steps):
    # env = WondersEnv(show, agent=agent1)
    env = WondersEnv(show, agent=RuleBasedAgent)
    env = ActionMasker(env, mask_fn)
    wins_agent1, wins_agent2, draws = 0, 0, 0
    for game in range(num_steps):
        done = False
        obs, info = env.reset()
        while not done:
            action_masks = get_action_masks(env)
            action, _ = model.predict(obs, action_masks=action_masks)
            obs, reward, done, truncated, info = env.step(action)
        if 'Player' in env.outcome:
            if env.outcome.split()[1] == "1":
                if env.agent_num == 0:
                    wins_agent1 += 1
                else:
                    wins_agent2 += 1
            elif env.outcome.split()[1] == "2":
                if env.agent_num == 0:
                    wins_agent2 += 1
                else:
                    wins_agent1 += 1
        else:
            draws += 1
    mean_reward = wins_agent2/num_steps
    return mean_reward

class EarlyStoppingCallback(BaseCallback):
    def __init__(self, check_freq: int, reward_threshold: float):
        super(EarlyStoppingCallback, self).__init__()
        self.check_freq = check_freq
        self.reward_threshold = reward_threshold
        self.checks_since_last_progress = 0
        self.mean_reward = 0

    def _on_step(self) -> bool:
        if self.n_calls == self.check_freq:

          # Get the mean reward
          self.mean_reward = evaluate(self.model, num_steps=1000)

          # Stop the training if mean reward is below the threshold
          if self.mean_reward < self.reward_threshold:
              print("Early stopping due to low performance")
              return False

        return True

def objective(trial):
    hyperparams = {
        'n_steps': int(trial.suggest_int('n_steps', 512, 4096, log=True)),
        'gamma': trial.suggest_categorical('gamma', [0.96, 0.97, 0.98, 0.99, 0.995, 0.999]),
        'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-3, log=True),
        'ent_coef': trial.suggest_float('ent_coef', 1e-9, 1e-5, log=True),
        'clip_range': trial.suggest_float('clip_range', 0.05, 0.55),
        'n_epochs': int(trial.suggest_int('n_epochs', 5, 25, log=True)),
    }

    env = DummyVecEnv([lambda: ActionMasker(WondersEnv(show, agent=agent1), mask_fn)])
    # model = MaskablePPO(MaskableMultiInputActorCriticPolicy, env, verbose=0, tensorboard_log="./tensorboard4/", **hyperparams)
    player2 = 'PPO_0.853_1257k_[2107, 0.98, 0.00010349, 1.61e-06, 0.46079166, 10]'
    model = MaskablePPO.load(f'baselines3_agents/{player2}', env=env, verbose=0, tensorboard_log="./tensorboard4/", **hyperparams)

    try:
        progress_callback = TrackTrainingProgressCallback()
        early_callback = EarlyStoppingCallback(check_freq=50000, reward_threshold=0.8)
        hyperparams_name = list(hyperparams.values())
        for i, param in enumerate(hyperparams_name):
            hyperparams_name[i] = round(param, 8)
        model.learn(total_timesteps=250000, callback=[progress_callback, early_callback], reset_num_timesteps=False, use_masking=True, tb_log_name= '0.0_' + str(trial.number) + '_100k_' + str(hyperparams_name))
    except ValueError as e:
        trial.report(float('nan'), progress_callback.current_step)
        old_dir_name = "./tensorboard4/" + '0.0_' + str(trial.number) + '_100k_' + str(hyperparams_name) + '_0'
        new_dir_name = "./tensorboard4/" + '0.0_pruned_' + str(trial.number) + '_100k_' + str(hyperparams_name)
        os.rename(old_dir_name, new_dir_name)
        raise optuna.exceptions.TrialPruned()

    if early_callback.mean_reward < early_callback.reward_threshold:
        mean_reward = early_callback.mean_reward
    else:
        mean_reward = evaluate(model, num_steps=2000)
    old_dir_name = "./tensorboard4/" + '0.0_' + str(trial.number) + '_100k_' + str(hyperparams_name) + '_0'
    if trial.number > 0:
        if mean_reward <= study.best_value:
            new_dir_name = "./tensorboard4/" + f'PPO_low_{mean_reward}_{trial.number}_{int(model.num_timesteps/1000)}k_{hyperparams_name}'
        else:
            new_dir_name = "./tensorboard4/" + f'PPO_{mean_reward}_{trial.number}_{int(model.num_timesteps/1000)}k_{hyperparams_name}'
            name = f'PPO_{mean_reward}_{int(model.num_timesteps/1000)}k_{hyperparams_name}'
            model.save(f'baselines3_agents/{name}')
    else:
        new_dir_name = "./tensorboard4/" + f'PPO_{mean_reward}_{trial.number}_{int(model.num_timesteps / 1000)}k_{hyperparams_name}'
        name = f'PPO_{mean_reward}_{int(model.num_timesteps / 1000)}k_{hyperparams_name}'
        model.save(f'baselines3_agents/{name}')

    os.rename(old_dir_name, new_dir_name)
    return mean_reward

start_time = time.time()

path = 'sqlite:///C:/Users/olive/Documents/GitHub/7-wonders-duel/optimizeRuleBased750k.db'
study = optuna.create_study(direction="maximize", storage=path, study_name="optimizeRuleBased750k", load_if_exists=True)

study.optimize(objective, n_trials=10)


print("Best trial:")
trial_ = study.best_trial
print(" Trial number: ", trial_.number)
print(" Value: ", trial_.value)
print(" Params: ")
for key, value in trial_.params.items():
    print(f"    {key}: {value}")

end_time = time.time()
execution_time = end_time - start_time
print(f"\nExecution time: {execution_time} seconds")