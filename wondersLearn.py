import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv
from Player1Agents import *

from stable_baselines3.common.callbacks import BaseCallback
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

def evaluate(agent2, num_steps):
    wins_agent1, wins_agent2, draws = [0,0,0], [0,0,0], 0
    for game in range(num_steps):
        done = False
        obs, info = env.reset()
        while not done:
            action_masks = get_action_masks(env)
            action, _ = agent2.predict(obs, action_masks=action_masks)
            obs, reward, done, truncated, info = env.step(action)
        if 'Player' in env.outcome:
            if 'Civilian' in env.outcome: id = 0
            elif 'Military' in env.outcome: id = 1
            elif 'Scientific' in env.outcome: id = 2
            if env.outcome.split()[1] == "1":
                if env.agent_num == 0:
                    wins_agent1[id] += 1
                else:
                    wins_agent2[id] += 1
            elif env.outcome.split()[1] == "2":
                if env.agent_num == 0:
                    wins_agent2[id] += 1
                else:
                    wins_agent1[id] += 1
        else:
            draws += 1
    print("Wins Agent 1: " + str(sum(wins_agent1)) + "/" + str(num_steps) + " (" + agent1_name + ")")
    print(f"Civilian: {wins_agent1[0]}, Military: {wins_agent1[1]}, Scientific: {wins_agent1[2]}")
    print("Wins Agent 2: " + str(sum(wins_agent2)) + "/" + str(num_steps) + " (" + agent2_name + ")")
    print(f"Civilian: {wins_agent2[0]}, Military: {wins_agent2[1]}, Scientific: {wins_agent2[2]}")
    print("Draws: " + str(draws) + "/" + str(num_steps))
    print()
    # print("Mean Reward Agent 1: " + str(sum(wins_agent1) / num_steps))
    # print("Mean Reward Agent 2: " + str(sum(wins_agent2) / num_steps))

    return wins_agent1, wins_agent2

class EarlyStoppingCallback(BaseCallback):
    def __init__(self, check_freq: int, eval_steps, patience=10000):
        super(EarlyStoppingCallback, self).__init__()
        self.check_freq = check_freq
        self.eval_steps = eval_steps
        self.patience = patience
        self.best_mean_reward = -np.inf
        self.no_improvement_steps = 0

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            mean_reward = evaluate(self.model, self.eval_steps)
            print(f"\nMean reward: {mean_reward} at step {self.num_timesteps}\n")

            if mean_reward > self.best_mean_reward:
                self.best_mean_reward = mean_reward
                self.no_improvement_steps = 0
                name = 'PPO_' + str(mean_reward) + '_'+ str(int(self.model.num_timesteps / 1000)) + '_EarlyStopping_' + str(hyperparams_name)
                self.model.save(f'baselines3_agents/{name}')
            else:
                self.no_improvement_steps += self.check_freq

            if self.no_improvement_steps >= self.patience:
                print("Stopping training because the mean reward has not improved in the last steps.")
                return False
        return True

# agent1 = 'PPO_15M_Random_RuleBased'
# player1 = 'RuleBasedAgent'
player1 = 'PPO_0.854_1508k_[2245, 0.999, 8.39e-05, 7.8e-06, 0.43153117, 17]'
# agent1 = RandomAgent
# agent1 = 'PPO_1350_EarlyStopping_[1571, 0.99, 0.00061148, 3e-07, 0.37536595, 13]'

if player1 in globals():
    agent1 = globals()[player1]
    agent1_name = player1
else:
    agent1 = player1
    agent1_name = player1 + '_Agent'

show = False
env = WondersEnv(show, agent=agent1)
env = ActionMasker(env, mask_fn)
obs, info = env.reset()
done = False
games = 3
n_steps = 500000

# import optuna
# path = 'sqlite:///C:/Users/olive/Documents/GitHub/7-wonders-duel/optimizeRuleBased.db'
# study = optuna.create_study(direction="maximize", storage=path, study_name="optimizeRuleBased", load_if_exists=True)
# trial_ = study.best_trial
# params = trial_.params
# del params['n_steps']
# params['n_epochs'] = int(params['n_epochs'])

# name = 'PPO_0.7785_503k_[4059, 0.97, 0.00094417, 1e-08, 0.431799, 13]'
# model = MaskablePPO.load(f'baselines3_agents/{name}', env=env)
#
# params = {
#     'n_steps': model.n_steps,
#     'gamma': model.gamma,
#     'learning_rate': model.learning_rate,
#     'ent_coef': model.ent_coef,
#     'clip_range': model.clip_range,
#     'n_epochs': model.n_epochs,
# }
# params['clip_range'] = params['clip_range']('_')
#
# print(params)

agent2 = MaskablePPO(MaskableMultiInputActorCriticPolicy, env, verbose=1, tensorboard_log="./tensorboard4/")
# agent2 = MaskablePPO(MaskableMultiInputActorCriticPolicy, env, verbose=1, tensorboard_log="./tensorboard4/", **params)
# player2 = 'PPO_noMask_1.25M_RuleBased_[2107, 0.98, 0.000103489, 1.612e-06, 0.460791665, 10]'
# agent2 = MaskablePPO.load(f'baselines3_agents/{player2}', env=env, verbose=1, tensorboard_log="./tensorboard4/", **params)
# params['clip_range'] = params['clip_range']('_')
# hyperparams_name = list(params.values())
# for i, param in enumerate(hyperparams_name):
#     hyperparams_name[i] = round(param, 9)

# callback = EarlyStoppingCallback(check_freq=100000, eval_steps=2000, patience=500000)

for game in range(games):
    obs, info = env.reset()
    agent2._last_obs = None
    # number = round((agent2.num_timesteps + n_steps)/ 1000000, 1)
    number = round(((game+1)* n_steps) / 1000000, 1)
    # agent2.learn(n_steps, callback=callback, reset_num_timesteps=False, progress_bar=True, use_masking=True, tb_log_name= 'train' + '_15M_' + str(hyperparams_name))
    agent2.learn(n_steps, reset_num_timesteps=False, progress_bar=True, use_masking=True, tb_log_name= f'train_vs_final_{number}M')

name = f'PPO_vs_Final_{number}M'
agent2.save(f'baselines3_agents/{name}')
agent2_name = name + '_Agent'
evaluate(agent2, 1000)



# Save the trained agents if needed
# name = 'PPO_15M_' + str(int(agent2.num_timesteps/1000)) + '_' + str(hyperparams_name)
# agent2.save(f'baselines3_agents/{name}')