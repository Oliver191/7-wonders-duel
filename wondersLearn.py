import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv
from Player1Agents import *

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
n_steps = 500000


# agent2 = MaskablePPO(MaskableActorCriticPolicy, env, verbose=1)
agent2 = MaskablePPO(MaskableMultiInputActorCriticPolicy, env, verbose=1)

for game in range(games):
    obs, info = env.reset()
    agent2._last_obs = None
    agent2.learn(n_steps, reset_num_timesteps=False, progress_bar=True, use_masking=True)

# Save the trained agents if needed
name = 'PPO_500k_Random'
agent2.save(f'baselines3_agents/{name}')