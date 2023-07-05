from stable_baselines3.common.env_checker import check_env
from WondersDuelEnv import WondersEnv

# env = WondersEnv()
# check_env(env)
show = False
env = WondersEnv(show)
episodes = 1

def request_player_input(valid_moves, mode):
    choice = input("Select a a valid move: ")
    if choice == '':
        print("Select a valid action!\n")
        return request_player_input(valid_moves, mode)
    action, position = choice[0], choice[1:]
    if choice in valid_moves:
        return valid_moves.index(choice)
    elif action == 's':
        return action
    elif action == 'q' and mode == 'main':
        return action
    elif choice == 'clear' and mode == 'main':
        return choice
    else:
        print("Action not in valid moves!\n")
        return request_player_input(valid_moves, mode)

for episode in range(episodes):
    done = False
    obs = env.reset()
    if show: env.render()
    print("Valid moves: " + str(env.valid_moves()))
    while not done:  # not done:
        random_action = env.action_space.sample()
        player = env.state_variables.turn_player
        # if player == 0:
        #     random_action = request_player_input(env.valid_moves(), env.mode)
        print(f"Player {player+1} action: ", random_action)
        obs, reward, done, truncated, info = env.step(random_action)
        if random_action != 's' and show: env.render()
        print('reward', reward, '\n')
        print("Valid moves: " + str(env.valid_moves()))
