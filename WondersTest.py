import numpy as np
from gymnasium import Env
from WondersDuelEnv import WondersEnv
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
import time

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

name = 'PPO_test'

show = False
env = WondersEnv(show)
env = ActionMasker(env, mask_fn)
wins_player1, wins_player2, draws = 0, 0, 0
agent2 = MaskablePPO.load(f'baselines3_agents/{name}', env=env)
games = 100
start_time = time.time()

for game in range(games):
    done = False
    obs, info = env.reset()
    while not done:
        player = env.state_variables.turn_player
        action_masks = get_action_masks(env)
        if player == 0:
            valid_actions = np.where(action_masks == 1)[0]
            action_names = [env.all_actions[action] for action in valid_actions]
            random_action = np.random.choice(valid_actions)
            obs, reward, done, truncated, info = env.step(random_action)
        elif player == 1:
            action, _ = agent2.predict(obs, action_masks=action_masks)
            obs, reward, done, truncated, info = env.step(action)
    if 'Player' in env.outcome:
        if env.outcome.split()[1] == "1":
            wins_player1 += 1
        elif env.outcome.split()[1] == "2":
            wins_player2 += 1
    else:
        draws += 1

end_time = time.time()
execution_time = end_time - start_time

print("Wins Player 1: " + str(wins_player1) + "/" + str(games) + " (" + 'RandomAgent' + ")")
print("Wins Player 2: " + str(wins_player2) + "/" + str(games) + " (" + 'PPO_Agent' + ")")
print("Draws: " + str(draws) + "/" + str(games))

print(f"\nExecution time: {execution_time} seconds")