import random
from sty import fg, bg, rs

class LearningAgent:

    def __init__(self, defined_print):
        self.original_print = print
        self.print = defined_print
        self.startState = None
        self.lastAction = None
        self.episodes = 0

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, input_string, state, function):
        choice = random.choice(valid_moves)

        # Store the previous state and action
        self.startState = state.copy()
        self.lastAction = choice
        return self.choose(choice, input_string)

    # Handles the end of game update
    def final(self, state, outcome):
        self.episodes += 1
        pass

    # print the chosen action if print not supressed
    def choose(self, choice, input_string):
        self.print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice