from mcts import mcts
from WondersDuelEnv import WondersEnv
from Player1Agents import *
import copy
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

human = False
show = False
player1 = 'RuleBasedAgent' #RuleBasedAgent
if player1 in globals():
    agent1 = globals()[player1]
    agent1_name = player1 if not human else 'HumanAgent'
else:
    agent1 = player1
    agent1_name = player1 + '_Agent'

env = WondersEnvWrapper(WondersEnv(show, agent=agent1 if not human else None))
wins_agent1, wins_agent2, draws = 0, 0, 0
mcts = mcts(timeLimit=5000)
games = 1
start_time = time.time()

for game in range(games):
    done = False
    obs, info = env.game.reset()
    # if show: env.game.render()
    print("Valid moves: " + str(env.getPossibleActions()))
    while not done:
        if human:
            if env.game.state_variables.turn_player == env.game.agent_num:
                action = request_player_input(env.game.valid_moves(), env.game.mode)
            else:
                if show: env.game.display = False
                env.game.agent = agent1
                env.game.initialize_agents()
                action = mcts.search(initialState=env)
                env.game.agent, env.game.agent1 = None, None
                if show: env.game.display = True
                if show: print('Choice: ' + action)
        else:
            action = mcts.search(initialState=env)
        obs, reward, done, truncated, info = env.game.step(action)
        # if action != 's' and show: env.game.render()
        print("Valid moves: " + str(env.getPossibleActions()))
    if 'Player' in env.game.outcome:
        if env.game.outcome.split()[1] == "1":
            if env.game.agent_num == 0: wins_agent1 += 1
            else: wins_agent2 += 1
        elif env.game.outcome.split()[1] == "2":
            if env.game.agent_num == 0: wins_agent2 += 1
            else: wins_agent1 += 1
    else:
        draws += 1

end_time = time.time()
execution_time = end_time - start_time

print("Wins Agent 1: " + str(wins_agent1) + "/" + str(games) + " (" + agent1_name + ")")
print("Wins Agent 2: " + str(wins_agent2) + "/" + str(games) + " (" + 'MCTS_Agent' + ")")
print("Draws: " + str(draws) + "/" + str(games))

print(f"\nExecution time: {execution_time} seconds")