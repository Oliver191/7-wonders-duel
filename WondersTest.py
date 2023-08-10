import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv
from baselineAgents import *
from collections import Counter

from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
import time
import os

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

player1 = 'PPO_final_DRL_agent_1.5M' #PPO_15M_Random_RuleBased
# player2 = 'RandomAgent'
# player2 = 'GreedyCivilianAgent'
# player2 = 'GreedyMilitaryAgent'
# player2 = 'GreedyScientificAgent'
player2 = 'RuleBasedAgent'
# player2 = 'PPO_1M_15PPO_newReward_[0.33761737, 5.94e-06, 0.99, 0.00189646, 9, 1237]'

#no Tuning
#PPO_noTuning_1.5M_RuleBased
#PPO_noTuningOrMask_1.5M
#PPO_noMask_1.5M_RuleBased_[2245, 0.999, 8.3903e-05, 7.803e-06, 0.431531171, 17]

#Order on which model was trained:
#000k-500k  : PPO_final_0.7785_503k_[4059, 0.97, 0.00094417, 1e-08, 0.431799, 13]
#500k-750k  : PPO_final_0.7935_756k_[4020, 0.97, 0.00012852, 2e-09, 0.53012684, 19]
#750k-1000k : PPO_final_0.834_1006k_[2034, 0.99, 0.00016857, 7.23e-06, 0.29984413, 7]
#1000k-1250k: PPO_final_0.853_1257k_[2107, 0.98, 0.00010349, 1.61e-06, 0.46079166, 10]
#1250k-1500l: PPO_final_0.854_1508k_[2245, 0.999, 8.39e-05, 7.8e-06, 0.43153117, 17]
#PPO_1500k_final_0854
##PPO_final_DRL_agent_1.5M

if player1 in globals():
    agent1 = globals()[player1]
    agent1_name = player1
else:
    agent1 = player1
    agent1_name = player1 + '_Agent'

show = False
games = 100
start_time = time.time()
types = ['Brown', 'Grey', 'Blue', 'Green', 'Red', 'Yellow', 'Purple', 'Wonder']
card_types_1, card_types_2 = Counter(), Counter()
card_types_1.update({elem: 0 for elem in types})
card_types_2.update({elem: 0 for elem in types})

def evaluate(num_steps):
    env = WondersEnv(show, agent=agent1)
    env = ActionMasker(env, mask_fn)
    if player2 in globals():
        agent2_class = globals()[player2]
        agent2 = agent2_class(show)
        agent2_name = player2
        PPO = False
    else:
        agent2 = MaskablePPO.load(f'baselines3_agents/{player2}', env=env)
        agent2_name = player2 + '_Agent'
        PPO = True
    wins_agent1, wins_agent2, draws = [0,0,0], [0,0,0], 0
    for game in range(num_steps):
        done = False
        obs, info = env.reset()
        while not done:
            action_masks = get_action_masks(env)
            if PPO: action, _ = agent2.predict(obs, action_masks=action_masks)
            else: action = agent2.getAction(env.valid_moves(), env.convertActionName, env.all_actions, env.getAgentState(), env.mode)
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
        if env.agent_num == 0: player = 0
        else: player = 1
        for card_type in [card.card_type for card in env.players[player].cards_in_play]:
            card_types_1[card_type] += 1
        card_types_1["Wonder"] += len(env.players[player].wonders_in_play)
        for card_type in [card.card_type for card in env.players[player^1].cards_in_play]:
            card_types_2[card_type] += 1
        card_types_2["Wonder"] += len(env.players[player^1].wonders_in_play)
    print("Wins Agent 1: " + str(sum(wins_agent1)) + "/" + str(num_steps) + " (" + agent1_name + ")")
    print(f"Civilian: {wins_agent1[0]}, Military: {wins_agent1[1]}, Scientific: {wins_agent1[2]}")
    print("Wins Agent 2: " + str(sum(wins_agent2)) + "/" + str(num_steps) + " (" + agent2_name + ")")
    print(f"Civilian: {wins_agent2[0]}, Military: {wins_agent2[1]}, Scientific: {wins_agent2[2]}")
    print("Draws: " + str(draws) + "/" + str(num_steps))
    print()
    # print("Mean Reward Agent 1: " + str(sum(wins_agent1) / num_steps))
    # print("Mean Reward Agent 2: " + str(sum(wins_agent2) / num_steps))

    return wins_agent1, wins_agent2

evaluate(games)

avg_card_types_1 = {element: round(count / games, 4) for element, count in card_types_1.items()}
avg_card_types_2 = {element: round(count / games, 4) for element, count in card_types_2.items()}
print("Card Types Agent 1: ", avg_card_types_1)
print("Card Types Agent 2: ", avg_card_types_2)

# repeat = 50
# wins = np.zeros((repeat,8), dtype=int)
#
# for i in range(repeat):
#     wins1, wins2 = evaluate(games)
#     wins[i] = np.array([sum(wins1)] + wins1 + [sum(wins2)] + wins2, dtype=int)
#
# filename = 'DRLvsNoMask100x1000.csv'
#
# # acquire lock
# while True:
#     if os.path.exists(filename):
#         try:
#             # try to rename the file, which should fail if the file is currently open
#             os.rename(filename, filename)
#             break
#         except OSError:
#             print("File is open, waiting...")
#             time.sleep(1)
#     else:
#         break
#
# with open(filename, 'a') as f:
#     np.savetxt(f, wins, delimiter=',', fmt='%i')

end_time = time.time()
execution_time = end_time - start_time

print(f"\nExecution time: {execution_time} seconds")