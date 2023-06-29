import copy
import random
from sty import fg, bg, rs
from collections import Counter

class GameState:
    '''Wrapper class to extract useful information from game state'''

    def __init__(self, state, function):
        self.state = state
        self.key = self.convertKey(state, function)

    # given a state of the game, convert it to a unique key
    def convertKey(self, state, function):
        player = state['player']
        key = str([player.coins, player.victory_points, player.military_points, player.science, player.clay,
                   player.wood, player.stone, player.paper, player.glass])
        key += str(function) if type(function) == str else 'wonders'
        cards = []
        for cardslot in state['age_board']:
            if cardslot.card_in_slot is not None and cardslot.card_visible == 1:
                cards.append(cardslot.card_in_slot.card_name)
        cards = sorted(cards)
        key += str(cards)
        # print('\n Key: ', key, '\n')
        return key

    # computes the score of the state based on victory points and coins
    def getScore(self):
        score = self.state['player'].victory_points + \
                self.state['player'].military_points + \
                self.state['player'].coins // 3 + \
                self.state['player'].clay + self.state['player'].wood + self.state['player'].stone + \
                self.state['player'].paper + self.state['player'].glass + sum(self.state['player'].science)
        return score

class LearningAgent:

    def __init__(self, defined_print, numTraining):
        self.original_print = print
        self.print = defined_print
        self.lastState, self.lastAction, self.lastFunction = None, None, None
        self.episodes = 0
        self.qValue = Counter()
        self.actionFrequency = Counter()
        # Set an optimisticReward that is used to force exploration
        self.optimisticReward = 100

        self.alpha = 0.2
        self.epsilon = 0.1
        self.gamma = 0.6
        self.maxAttempts = 3
        self.numTraining = numTraining

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, input_string, state, function):
        endState = GameState(state, function)
        # Skip learning if the game just started and there is no last action
        if self.lastAction is not None:
            startState = GameState(self.lastState, self.lastFunction)
            reward = self.computeReward(startState, endState)
            self.learn(startState, self.lastAction, reward, endState, valid_moves)
            self.actionFrequency[(startState.key, self.lastAction)] += 1
        random.shuffle(valid_moves)
        utility = []
        for action in valid_moves:
            utility.append(self.explorationFn(self.qValue[(endState.key,action)], self.actionFrequency[(endState.key, action)]))
        choice = valid_moves[utility.index(max(utility))]

        # Store the previous state and action
        self.lastState = copy.deepcopy(state)
        self.lastAction = choice
        self.lastFunction = copy.deepcopy(function)
        return self.choose(choice, input_string)

    # Handles the end of game update
    def final(self, state, outcome):
        if 'Player' in outcome:
            if state['player'].player_number + 1 == int(outcome.split()[1]):
                reward, function = 100, 'win'
            else:
                reward, function = -100, 'loss'
        else:
            reward, function = 10, 'draw'

        startState = GameState(self.lastState, self.lastFunction)
        endState = GameState(state, function)
        self.learn(startState, self.lastAction, reward, endState, [])
        self.actionFrequency[(startState.key, self.lastAction)] += 1

        #reset values
        self.lastState, self.lastAction, self.lastFunction = None, None, None

        # set learning parameters to zero after training is done
        self.episodes += 1
        if self.episodes == self.numTraining:
            self.alpha = 0.0
            self.epsilon = 0.0

    # print the chosen action if print not supressed
    def choose(self, choice, input_string):
        self.print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice

    # Given a startState and an endState compute the reward as the difference in score
    def computeReward(self, startState, endState):
        reward = float(endState.getScore() - startState.getScore())
        return reward

    # Get the maximum qValue of all possible actions from the current state
    def maxQValue(self, state, valid_moves):
        maxValues = []
        for action in valid_moves:
            maxValues.append(self.qValue[(state.key,action)])
        return max(maxValues) if valid_moves else 0

    # Update the qValue of the startState based on the action, the received reward, and the maxQValue of the endState
    def learn(self, startState, action, reward, endState, valid_moves):
        self.qValue[(startState.key,action)] += self.alpha * (
                    reward + self.gamma * self.maxQValue(endState, valid_moves) - self.qValue[(startState.key,action)])

    # Exploration function: force agent to pick the action if it is below the threshold maxAttempts
    def explorationFn(self, utility, counts):
        return float(self.optimisticReward) if counts < self.maxAttempts else utility