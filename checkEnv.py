from stable_baselines3.common.env_checker import check_env
import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
from Player1Agents import *

# env = WondersEnv()
# check_env(env)

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

show = True
env = WondersEnv(show, agent=None)
env = ActionMasker(env, mask_fn)
episodes = 1

player2 = 'PPO_15M_Random_RuleBased'
agent2 = MaskablePPO.load(f'baselines3_agents/{player2}', env=env)
agent2_name = player2 + '_Agent'
# print("\n", agent2.policy, "\n")

# agent2 = RuleBasedAgent(False)
# agent2_name = 'RuleBasedAgent'

def request_player_input(valid_moves, mode):
    choice = input("Select a a valid move: ")
    if choice == '':
        print("Select a valid action!\n")
        return request_player_input(env.valid_moves(), env.mode)
    action, position = choice[0], choice[1:]
    if choice in valid_moves:
        return choice
    elif action == 's':
        return action
    elif action == 'q' and mode == 'main':
        return action
    elif choice == 'clear' and mode == 'main':
        return choice
    else:
        print("Action not in valid moves!\n")
        return request_player_input(env.valid_moves(), env.mode)

for episode in range(episodes):
    done = False
    obs, info = env.reset()
    if show: env.render()
    print("Valid moves: " + str(env.valid_moves()))
    while not done:
        action_masks = get_action_masks(env)
        if env.state_variables.turn_player == 0:
            action = request_player_input(env.valid_moves(), env.mode)
        elif env.state_variables.turn_player == 1:
            action, _ = agent2.predict(obs, action_masks=action_masks)
            # action = agent2.getAction(env.valid_moves(), env.convertActionName, env.all_actions, env.getAgentState(), env.mode)
        obs, reward, done, truncated, info = env.step(action)
        if action != 's' and show: env.render()
        print("Valid moves: " + str(env.valid_moves()))
