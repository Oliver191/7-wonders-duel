import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv

from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

show = False
env = WondersEnv(show)
env = ActionMasker(env, mask_fn)
obs, info = env.reset()
done = False
games = 1
n_steps = 100000


# agent2 = MaskablePPO(MaskableActorCriticPolicy, env, verbose=1)
agent2 = MaskablePPO(MaskableMultiInputActorCriticPolicy, env, verbose=1)

# for step in range(n_steps):
#     player = env.state_variables.turn_player
#     action_masks = get_action_masks(env)
#     if player == 0:
#         valid_actions = np.where(action_masks == 1)[0]
#         action_names = [env.all_actions[action] for action in valid_actions]
#         random_action = np.random.choice(valid_actions)
#         obs, reward, done, truncated, info = env.step(random_action)
#     elif player == 1:
#         action, _ = agent2.predict(obs, action_masks=action_masks)
#         obs, reward, done, truncated, info = env.step(action)
#         agent2.learn(games, reset_num_timesteps=False, progress_bar=True, use_masking=True)
#         # agent2.collect_rollouts(env, callback, rollout_buffer, n_rollout_steps=1, use_masking=True)
#     if done:
#         obs, info = env.reset()

for game in range(games):
    obs, info = env.reset()
    agent2._last_obs = None
    agent2.learn(n_steps, reset_num_timesteps=False, progress_bar=True, use_masking=True)

# Save the trained agents if needed
name = 'PPO_test'
agent2.save(f'baselines3_agents/{name}')