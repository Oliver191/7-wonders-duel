import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv
from Player1Agents import *

from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
import time

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

#PPO_2000k_RuleBased, PPO_2000k_Random, PPO_10000k_newScore, PPO_10000k_Random_RuleBased
#RuleBasedAgent, RandomAgent, GreedyCivilianAgent, GreedyMilitaryAgent, GreedyScientificAgent
player1 = 'RuleBasedAgent'
player2 = 'PPO_16M_WinReward'

if player1 in globals():
    agent1 = globals()[player1]
    agent1_name = player1
else:
    agent1 = player1
    agent1_name = player1 + '_Agent'

show = False
env = WondersEnv(show, agent=agent1)
env = ActionMasker(env, mask_fn)
wins_agent1, wins_agent2, draws = 0, 0, 0
games = 1000

if player2 in globals():
    agent2_class = globals()[player2]
    agent2 = agent2_class(show)
    agent2_name = player2
    PPO = False
else:
    agent2 = MaskablePPO.load(f'baselines3_agents/{player2}', env=env)
    agent2_name = player2 + '_Agent'
    PPO = True
start_time = time.time()

for game in range(games):
    done = False
    obs, info = env.reset()
    while not done:
        action_masks = get_action_masks(env)
        if PPO: action, _ = agent2.predict(obs, action_masks=action_masks)
        else: action = agent2.getAction(env.valid_moves(), env.convertActionName, env.all_actions, env.getAgentState(), env.mode)
        obs, reward, done, truncated, info = env.step(action)
        if show: print(reward)
    if 'Player' in env.outcome:
        if env.outcome.split()[1] == "1":
            if env.agent_num == 0: wins_agent1 += 1
            else: wins_agent2 += 1
        elif env.outcome.split()[1] == "2":
            if env.agent_num == 0: wins_agent2 += 1
            else: wins_agent1 += 1
    else:
        draws += 1

end_time = time.time()
execution_time = end_time - start_time

print("Wins Agent 1: " + str(wins_agent1) + "/" + str(games) + " (" + agent1_name + ")")
print("Wins Agent 2: " + str(wins_agent2) + "/" + str(games) + " (" + agent2_name + ")")
print("Draws: " + str(draws) + "/" + str(games))

print(f"\nExecution time: {execution_time} seconds")