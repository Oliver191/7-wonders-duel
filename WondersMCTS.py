from mcts import mcts
from WondersDuelEnv import WondersEnv
from baselineAgents import *
import copy
import multiprocessing
from multiprocessing import Pool
import time

class WondersEnvWrapper:
    def __init__(self, game):
        self.game = game

    def getPossibleActions(self):
        return self.game.valid_moves()

    def takeAction(self, action):
        newState = copy.deepcopy(self)
        newState.game.step(action)
        return newState

    def isTerminal(self):
        return self.game.done

    def getReward(self):
        self.game.get_reward()
        return self.game.reward

    def __deepcopy__(self, memo):
        if self in memo:
            return memo[self]
        new_instance = self.__class__(copy.deepcopy(self.game, memo))

        memo[self] = new_instance
        return new_instance

def request_player_input(valid_moves, mode):
    choice = input("Select a a valid move: ")
    if choice == '':
        print("Select a valid action!\n")
        return request_player_input(valid_moves, mode)
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
        return request_player_input(valid_moves, mode)

human = True
show = True
player1 = 'RandomAgent' #RuleBasedAgent #RandomAgent, #PPO_15M_Random_RuleBased
if player1 in globals():
    agent1 = globals()[player1]
    agent1_name = player1 if not human else 'HumanAgent'
else:
    agent1 = player1
    agent1_name = player1 + '_Agent'

mcts = mcts(timeLimit=2000)

def run_game(game_num, results):
    done = False
    with SuppressPrints():
        env = WondersEnvWrapper(WondersEnv(show, agent=agent1 if not human else None))
    obs, info = env.game.reset()
    # if show: env.game.render()
    # print("Valid moves: " + str(env.getPossibleActions()))
    while not done:
        if human:
            if show: env.game.render()
            if env.game.state_variables.turn_player == env.game.agent_num:
                action = request_player_input(env.game.valid_moves(), env.game.mode)
            else:
                with SuppressPrints():
                    env.game.agent = agent1
                    env.game.initialize_agents()
                    action = mcts.search(initialState=env)
                env.game.agent, env.game.agent1 = None, None
                if show: print('Choice: ' + action)
        else:
            with SuppressPrints():
                action = mcts.search(initialState=env)
        obs, reward, done, truncated, info = env.game.step(action)
        # if action != 's' and show: env.game.render()
        # print("Valid moves: " + str(env.getPossibleActions()))
    if 'Player' in env.game.outcome:
        if env.game.outcome.split()[1] == "1":
            if env.game.agent_num == 0: results[0] += 1
            else: results[1] += 1
        elif env.game.outcome.split()[1] == "2":
            if env.game.agent_num == 0: results[1] += 1
            else: results[0] += 1
    else:
        results[2] += 1
    print(game_num)

def parallel_execution(num_games):
    with Pool(processes=10) as pool:
        results = multiprocessing.Manager().list([0, 0, 0])
        game_numbers = range(num_games)
        input_values = [(game_num, results) for game_num in game_numbers]
        pool.starmap(run_game, input_values)
    return results

import os, sys
class SuppressPrints:
    def __init__(self, suppress=True):
        self.suppress = suppress

    def __enter__(self):
        if self.suppress:
            self._original_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.suppress:
            sys.stdout.close()
            sys.stdout = self._original_stdout

# if __name__ == '__main__':
#     start_time = time.time()
#
#     games = 10
#     results = parallel_execution(games)
#
#     end_time = time.time()
#     execution_time = end_time - start_time
#
#     print("Wins Agent 1: " + str(results[0]) + "/" + str(games) + " (" + agent1_name + ")")
#     print("Wins Agent 2: " + str(results[1]) + "/" + str(games) + " (" + 'MCTS_Agent' + ")")
#     print("Draws: " + str(results[2]) + "/" + str(games))
#
#     print(f"\nExecution time: {execution_time} seconds")

run_game(0, [0,0,0])