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
        key = self.convertFunction(state, function)
        # player = state['player']
        # key += str([player.coins, player.victory_points, player.military_points, player.science, player.clay,
        #            player.wood, player.stone, player.paper, player.glass])
        # print('\n Key: ', key, '\n')
        return key

    def convertFunction(self, state, function):
        if isinstance(function, dict):
            return '' # str(sorted([wonder.wonder_name for wonder in function.keys() if function[wonder]]))
        elif function == 'main':
            cards = []
            for cardslot in state['age_board']:
                if cardslot.card_in_slot is not None and cardslot.card_selectable == 1: #cardslot.card_visible == 1:
                    cards.append(cardslot.card_in_slot.card_name)
            cards += [wonder.wonder_name for wonder in state['player'].wonders_in_hand if not wonder.wonder_in_play]
            return '' # str(sorted(cards))
        elif function == 'mausoleum':
            return '' # str(sorted([card.card_name for card in state['state_variables'].discarded_cards]))
        elif function == 'token':
            return '' # str(sorted([token.token_name for token in state['progress_board'].tokens if token.token_in_slot]))
        elif function == 'library':
            return '' # str(sorted([token.token_name for token in  state['progress_board'].discarded_tokens]))
        elif function == 'law':
            return '' # str(state['player'].science)
        elif 'destroy' in function.split():
            return ''
        else:
            return function

    # computes the score of the state based on victory points and coins
    def getScore(self):
        score = self.state['player'].victory_points + \
                self.state['player'].military_points - self.state['opponent'].military_points + \
                self.state['player'].coins // 3 + \
                self.state['player'].clay + self.state['player'].wood + self.state['player'].stone + \
                self.state['player'].paper + self.state['player'].glass + sum(self.state['player'].science)*2
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
            lastActionName = self.convertActionName(self.lastState, self.lastAction, self.lastFunction)
            startState = GameState(self.lastState, self.lastFunction)
            reward = self.computeReward(startState, endState)
            self.learn(startState, lastActionName, reward, endState, valid_moves, function)
            self.actionFrequency[(startState.key, lastActionName)] += 1
        random.shuffle(valid_moves)
        utility = []
        for action in valid_moves:
            actionName = self.convertActionName(state, action, function)
            utility.append(self.explorationFn(self.qValue[(endState.key,actionName)], self.actionFrequency[(endState.key, actionName)]))
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
        lastActionName = self.convertActionName(self.lastState, self.lastAction, self.lastFunction)
        self.learn(startState, lastActionName, reward, endState, [], function)
        self.actionFrequency[(startState.key, lastActionName)] += 1

        #reset values
        self.lastState, self.lastAction, self.lastFunction = None, None, None

        # set learning parameters to zero after training is done
        self.episodes += 1
        if self.episodes == self.numTraining:
            self.alpha = 0.0
            self.epsilon = 0.0

    def convertActionName(self, state, action, function):
        if isinstance(function, dict):
            actionName = 'choose ' + list(function.keys())[int(action[1])].wonder_name
        elif function == 'main':
            if action[0] == 'c':
                actionName = 'construct ' + state['age_board'][int(action[1:])].card_in_slot.card_name
            elif action[0] == 'd':
                actionName = 'discard ' + state['age_board'][int(action[1:])].card_in_slot.card_name
            elif action[0] == 'w':
                actionName = 'construct ' + state['player'].wonders_in_hand[int(action[-1])].wonder_name
                actionName += ', discard ' + state['age_board'][int(action.split()[0][1:])].card_in_slot.card_name
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
            opponent_cards = [card.card_name for card in state['opponent'].cards_in_play if card.card_type == function.split()[1]]
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