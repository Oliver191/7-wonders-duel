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

agent1 = 'PPO_15M_Random_RuleBased'
# agent1 = RuleBasedAgent

show = False
env = WondersEnv(show, agent=agent1)
env = ActionMasker(env, mask_fn)
obs, info = env.reset()
done = False
games = 2
n_steps = 500000


# agent2 = MaskablePPO(MaskableActorCriticPolicy, env, verbose=1)
# agent2 = MaskablePPO(MaskableMultiInputActorCriticPolicy, env, verbose=1)
player2 = 'PPO_15M_Random_RuleBased'
agent2 = MaskablePPO.load(f'baselines3_agents/{player2}', env=env)

for game in range(games):
    obs, info = env.reset()
    agent2._last_obs = None
    agent2.learn(n_steps, reset_num_timesteps=True, progress_bar=True, use_masking=True)
    # number = int(((game+1)*n_steps + 5000000)/1000)
    # name = f'PPO_{number}k_vs_PPO_10000k'
    # agent2.save(f'baselines3_agents/{name}')

# Save the trained agents if needed
name = 'PPO_16M_WinReward'
agent2.save(f'baselines3_agents/{name}')