from stable_baselines3.common.env_checker import check_env
from WondersDuelEnv import WondersEnv

# env = WondersEnv()
# check_env(env)

env = WondersEnv()
episodes = 50

def request_player_input(valid_moves):
    choice = input("Select a a valid move: ")
    if choice == '':
        print("Select a valid action!\n")
        return request_player_input(valid_moves)
    action, position = choice[0], choice[1:]
    if action == 's': #TODO add show functionality back in
        return action
    elif choice in valid_moves:
        return valid_moves.index(choice)
    else:
        print("Action not in valid moves!\n")
        return request_player_input(valid_moves)

for episode in range(episodes):
    done = False
    env.render()
    obs = env.reset()
    print("Valid moves: " + str(env.valid_moves()))
    while not done:  # not done:
        random_action = env.action_space.sample()
        player = env.state_variables.turn_player
        if player == 0:
            random_action = request_player_input(env.valid_moves())
        print(f"Player {player+1} action: ", random_action)
        obs, reward, done, truncated, info = env.step(random_action)
        print('reward', reward, '\n')
        print("Valid moves: " + str(env.valid_moves()))
