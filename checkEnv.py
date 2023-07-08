from stable_baselines3.common.env_checker import check_env
import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks

# env = WondersEnv()
# check_env(env)

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

show = True
env = WondersEnv(show, agent=None)
env = ActionMasker(env, mask_fn)
episodes = 1

player2 = 'PPO_10000k_Random_RuleBased'
agent2 = MaskablePPO.load(f'baselines3_agents/{player2}', env=env)
agent2_name = player2 + '_Agent'

def request_player_input(valid_moves, mode, convertActionName, all_actions):
    choice = input("Select a a valid move: ")
    if choice == '':
        print("Select a valid action!\n")
        return request_player_input(env.valid_moves(), env.mode, env.convertActionName, env.all_actions)
    action, position = choice[0], choice[1:]
    if choice in valid_moves:
        action_index = convertActionName(choice)
        action_index = all_actions.index(action_index)
        return action_index
    elif action == 's':
        return action
    elif action == 'q' and mode == 'main':
        return action
    elif choice == 'clear' and mode == 'main':
        return choice
    else:
        print("Action not in valid moves!\n")
        return request_player_input(env.valid_moves(), env.mode, env.convertActionName, env.all_actions)

for episode in range(episodes):
    done = False
    obs, info = env.reset()
    if show: env.render()
    print("Valid moves: " + str(env.valid_moves()))
    while not done:
        action_masks = get_action_masks(env)
        if env.state_variables.turn_player == 0:
            action = request_player_input(env.valid_moves(), env.mode, env.convertActionName, env.all_actions)
        elif env.state_variables.turn_player == 1:
            action, _ = agent2.predict(obs, action_masks=action_masks)
        obs, reward, done, truncated, info = env.step(action)
        if action != 's' and show: env.render()
        print("Valid moves: " + str(env.valid_moves()))
