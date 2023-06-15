
import random
from sty import fg, bg, rs

# A very simple agent. Just makes a random pick every time that it is
# asked for an action.
class RandomAgent:

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, input_string):
        choice = random.choice(valid_moves)

        print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice

class HumanAgent:

    # given the legal actions and information about the game state, return an action
    def getAction(self, input_string):
        choice = input(input_string)
        return choice