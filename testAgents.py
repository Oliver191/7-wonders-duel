
import random
from sty import fg, bg, rs

# A very simple agent. Just makes a random pick every time that it is asked for an action.
class RandomAgent:

    def __init__(self, defined_print):
        self.print = defined_print

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, input_string, state, function):
        choice = random.choice(valid_moves)

        self.print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice

# Ask for human input through the command line
class HumanAgent:

    # given the legal actions and information about the game state, return an action
    def getAction(self, input_string):
        choice = input(input_string)
        return choice

# A greedy agent which always chooses the action with the highest number of victory points
class GreedyCivilianAgent:

    def __init__(self, defined_print):
        self.original_print = print
        self.print = defined_print

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, input_string, state, function):
        if function == 'main':
            victory_cards, cards_constructable, victory_wonders, wonders_constructable = self.victory_points(valid_moves, state)
            max_card = max(victory_cards) if sum(victory_cards) > 0 else 0
            max_wonder = max(victory_wonders) if sum(victory_wonders) > 0 else 0
            if sum(victory_cards) == 0 and sum(victory_wonders) == 0:
                choice = random.choice(valid_moves)
            else:
                if max_card > max_wonder:
                    choice = 'c' + str(cards_constructable[victory_cards.index(max(victory_cards))])
                else:
                    wonder = wonders_constructable[victory_wonders.index(max(victory_wonders))]
                    wonder_moves = [move for move in valid_moves if move[0] == 'w']
                    wonder_moves = [move for move in wonder_moves if int(move[-1]) == wonder]
                    choice = random.choice(wonder_moves)
        else:
            choice = random.choice(valid_moves)
        self.print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice

    # determines the victory points of constructable cards and wonders
    def victory_points(self, valid_moves, state):
        cards_constructable = [int(move[1:]) for move in valid_moves if move[0] == 'c']
        cards = [state['age_board'][i].card_in_slot for i in cards_constructable]
        wonders_constructable = [int(move[-1]) for move in valid_moves if move[0] == 'w']
        wonders = [state['player'].wonders_in_hand[i] for i in wonders_constructable]
        victory_cards, victory_wonders = [], []
        for card in cards:
            if 'V' in card.card_effect_passive:
                victory_cards.append(int(card.card_effect_passive[0]))
            else:
                victory_cards.append(0)
        for wonder in wonders:
            if 'V' in wonder.wonder_effect_when_played:
                victory_wonders.append(int(wonder.wonder_effect_when_played[0]))
            else:
                victory_wonders.append(0)
        return victory_cards, cards_constructable, victory_wonders, wonders_constructable
