import copy
import random
from sty import fg, bg, rs
from collections import Counter
import pickle
import numpy as np

class GameState:
    '''Wrapper class to extract useful information from game state'''

    def __init__(self, state, function, cards_wonders):
        self.state = state
        self.key = self.convertKey(state, function, cards_wonders)

    # given a state of the game, convert it to a unique key
    def convertKey(self, state, function, cards_wonders):
        key = ''
        player = state['player']
        opponent = state['opponent']
        victory = (player.victory_points + player.coins // 3) - (opponent.victory_points + opponent.coins // 3)
        key += 'Victory: ' + str(True if victory > 0 else False)
        military = [True if (player.military_points - opponent.military_points) < thres else False for thres in [-8, -5, -2, 0]]
        military += [True if (player.military_points - opponent.military_points) > thres else False for thres in [0, 2, 5, 8]]
        key += ', Military: ' + str(military)
        key += ', Science: ' + str([True if symbol > 0 else False for symbol in player.science])
        # key += ', Science: ' + str(player.science)
        # colors = ['Brown', 'Grey', 'Green', 'Yellow'] #['Brown', 'Grey', 'Blue', 'Red', 'Green', 'Yellow', 'Purple']
        # color_counts = Counter({color: 0 for color in colors})
        # for color in [card.card_type for card in player.cards_in_play if card.card_type not in ['Blue', 'Red', 'Purple']]:
        #     color_counts[color] += 1
        # color_counts['Brown'] += color_counts['Grey']
        # del color_counts['Grey']
        # key += 'Colors: ' + str(list(color_counts.values()))
        yellow = len([1 for card in player.cards_in_play if card.card_type == 'Yellow'])
        key += ', Resources: ' + str(sum([player.clay, player.wood, player.stone, player.paper, player.glass])+yellow)
        # key += ', Resources: ' + str([player.clay, player.wood, player.stone, player.paper, player.glass, yellow])
        # owned_cards = [card.card_name for card in player.cards_in_play]
        # owned_wonders = [wonder.wonder_name for wonder in player.wonders_in_play]
        # key = [True if card in owned_cards else False for card in cards_wonders[0]]
        # key += [True if wonder in owned_wonders else False for wonder in cards_wonders[1]]
        # print('\n Key: ', key, '\n')
        return str(key)

    # computes the score of the state based on victory points and coins
    def getScore(self):
        score = []
        for play in ['player', 'opponent']:
            score.append(self.state[play].victory_points +
                         self.state[play].military_points +
                         self.state[play].coins // 3 +
                         self.state[play].clay + self.state[play].wood + self.state[play].stone +
                         self.state[play].paper + self.state[play].glass + sum(self.state[play].science)*4 +
                         len([1 for card in self.state[play].cards_in_play if card.card_type == 'Yellow'])*2)
        return score[0]

class LearningAgent:

    def __init__(self, defined_print, numTraining, load_save_names, hyperparams):
        self.original_print = print
        self.print = defined_print
        self.lastState, self.lastAction, self.lastFunction, self.lastValidMoves = None, None, None, []
        self.episodes = 0
        self.load_name, self.save_name = load_save_names
        if self.load_name is None:
            self.qValue, self.actionFrequency = Counter(), Counter()
        else:
            self.qValue, self.actionFrequency = self.load_agent(self.load_name)

        # Set an optimisticReward that is used to force exploration
        self.optimisticReward = 100
        # card_list = list(np.genfromtxt('card_list.csv', delimiter=',', skip_header=1, dtype=str)[:,0])
        # wonder_list = list(np.genfromtxt('wonder_list.csv', delimiter=',', skip_header=1, dtype=str)[:,0])
        self.cards_wonders = [] #[card_list, wonder_list]
        self.episodeHistory = []

        self.numTraining = numTraining
        self.set_hyperparams(hyperparams)

    def set_hyperparams(self, hyperparams):
        if self.numTraining > 0:
            self.alpha = 0.05 if not hyperparams[0] else hyperparams[0]
            self.epsilon = 0.02 if not hyperparams[1] else hyperparams[1]
            self.gamma = 0.65 if not hyperparams[2] else hyperparams[2]
            self.maxAttempts = 2 if not hyperparams[3] else hyperparams[3]
        else:
            self.alpha = 0.0
            self.epsilon = 0.0
            self.gamma = 0.0
            self.maxAttempts = 0

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, input_string, state, function):
        endState = GameState(state, function, self.cards_wonders)
        # Skip learning if the game just started and there is no last action
        if self.lastAction is not None:
            self.episodeHistory.append((self.lastState, self.lastAction, self.lastFunction, self.lastValidMoves))
            lastActionName = self.convertActionName(self.lastState, self.lastAction, self.lastFunction)
            startState = GameState(self.lastState, self.lastFunction, self.cards_wonders)
            reward = self.computeReward(startState, endState)
            self.learn(startState, lastActionName, reward, endState, valid_moves, function)
            self.actionFrequency[(startState.key, lastActionName)] += 1
        random.shuffle(valid_moves)
        utility = []
        for action in valid_moves:
            actionName = self.convertActionName(state, action, function)
            utility.append(self.explorationFn(self.qValue[(endState.key,actionName)], self.actionFrequency[(endState.key, actionName)]))
        choice = valid_moves[utility.index(max(utility))]
        choice = np.random.choice(np.array([random.choice(valid_moves), choice]), p=np.array([self.epsilon, 1 - self.epsilon]))

        # Store the previous state and action
        self.lastState = copy.deepcopy(state)
        self.lastAction = choice
        self.lastFunction = copy.deepcopy(function)
        self.lastValidMoves = valid_moves[:]
        return self.choose(choice, input_string)

    # Handles the end of game update
    def final(self, state, outcome):
        if 'Player' in outcome:
            if state['player'].player_number + 1 == int(outcome.split()[1]):
                reward, function = 100, 'win'
            else:
                reward, function = -50, 'loss'
        else:
            reward, function = 10, 'draw'
        self.episodeHistory.append((state, None, function, []))

        startState = GameState(self.lastState, self.lastFunction, self.cards_wonders)
        lastActionName = self.convertActionName(self.lastState, self.lastAction, self.lastFunction)
        self.updateQValues(reward)
        self.actionFrequency[(startState.key, lastActionName)] += 1

        #reset values
        self.episodeHistory = []
        self.lastState, self.lastAction, self.lastFunction, self.lastValidMoves = None, None, None, []

        # set learning parameters to zero after training is done
        self.episodes += 1
        if self.episodes == self.numTraining:
            self.alpha, self.epsilon, self.gamma, self.maxAttempts = 0.0, 0.0, 0.0, 0
            self.original_print('\n', len(self.actionFrequency), '\n', list(self.actionFrequency.items())[:20],'\n')
            self.original_print('\n', len(self.qValue), '\n', list(self.qValue.items())[:20], '\n')
            if self.save_name is not None: self.save_agent(self.qValue, self.actionFrequency, self.save_name)

    def save_agent(self, qValue, actionFrequency, name):
        file_path = f'saved_agents/{name}_qValue.pkl'
        with open(file_path, 'wb') as file:
            pickle.dump(qValue, file)
        file_path = f'saved_agents/{name}_actionFrequency.pkl'
        with open(file_path, 'wb') as file:
            pickle.dump(actionFrequency, file)

    def load_agent(self, name):
        try:
            file_path = f'saved_agents/{name}_qValue.pkl'
            with open(file_path, 'rb') as file:
                qValue = pickle.load(file)
            file_path = f'saved_agents/{name}_actionFrequency.pkl'
            with open(file_path, 'rb') as file:
                actionFrequency = pickle.load(file)
            qValue = Counter(qValue)
            actionFrequency = Counter(actionFrequency)
            return qValue, actionFrequency
        except FileNotFoundError:
            return Counter(), Counter()

    def updateQValues(self, reward):
        # Iterate over the episode history in reverse order
        discount = 0
        for i in range(len(self.episodeHistory) - 1, -1, -1):
            state, action, function, valid_moves = self.episodeHistory[i]
            if i > 0: lastState, lastAction, lastFunction, lastValidMoves = self.episodeHistory[i-1]

            # Compute the startState and endState
            startState = GameState(self.episodeHistory[i-1][0], self.episodeHistory[i-1][2], self.cards_wonders) if i > 0 else None
            endState = GameState(state, function, self.cards_wonders)

            # Update Q-value if there is a previous state
            if startState is not None and action is not None:
                lastActionName = self.convertActionName(lastState, lastAction, lastFunction)
                discounted_reward = reward * 0.95**discount
                self.learn(startState, lastActionName, discounted_reward, endState, valid_moves, function)
                discount += 1

    def convertActionName(self, state, action, function):
        if isinstance(function, dict):
            actionName = 'choose ' + list(function.keys())[int(action[1])].wonder_name
        elif function == 'main':
            if action[0] == 'c':
                actionName = 'construct ' + state['age_board'][int(action[1:])].card_in_slot.card_name
            elif action[0] == 'd':
                # actionName = 'discard ' + state['age_board'][int(action[1:])].card_in_slot.card_name
                actionName = 'discard ' + state['age_board'][int(action[1:])].card_in_slot.card_type
            elif action[0] == 'w':
                actionName = 'construct ' + state['player'].wonders_in_hand[int(action[-1])].wonder_name
                # actionName += ', discard ' + state['age_board'][int(action.split()[0][1:])].card_in_slot.card_name
            else:
                actionName = action
        elif function == 'mausoleum':
            actionName = 'construct ' + state['state_variables'].discarded_cards[int(action[1:])].card_name
        elif function == 'token':
            actionName = 'construct ' + state['progress_board'].tokens[int(action[1])].token_name
        elif function == 'library':
            actionName = 'construct ' + state['progress_board'].discarded_tokens[int(action[1])].token_name
        elif function == 'law':
            actionName = action
        elif 'destroy' in function.split():
            # opponent_cards = [card.card_name for card in state['opponent'].cards_in_play if card.card_type == function.split()[1]]
            # actionName = 'destroy ' + opponent_cards[int(action[1:])]
            opponent_cards = [card.card_effect_passive for card in state['opponent'].cards_in_play if card.card_type == function.split()[1]]
            actionName = 'destroy ' + opponent_cards[int(action[1:])]
        return actionName

    # print the chosen action if print not supressed
    def choose(self, choice, input_string):
        self.print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice

    # Given a startState and an endState compute the reward as the difference in score
    def computeReward(self, startState, endState):
        reward = float(endState.getScore() - startState.getScore())
        return reward

    # Get the maximum qValue of all possible actions from the current state
    def maxQValue(self, endState, valid_moves, function):
        maxValues = []
        for action in valid_moves:
            actionName = self.convertActionName(endState.state, action, function)
            maxValues.append(self.qValue[(endState.key,actionName)])
        return max(maxValues) if valid_moves else 0

    # Update the qValue of the startState based on the action, the received reward, and the maxQValue of the endState
    def learn(self, startState, action, reward, endState, valid_moves, function):
        self.qValue[(startState.key,action)] += self.alpha * (
                    reward + self.gamma * self.maxQValue(endState, valid_moves, function) - self.qValue[(startState.key,action)])

    # Exploration function: force agent to pick the action if it is below the threshold maxAttempts
    def explorationFn(self, utility, counts):
        return float(self.optimisticReward) if counts < self.maxAttempts else utility