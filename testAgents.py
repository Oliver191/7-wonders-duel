
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
        if function == 'main' or function == 'mausoleum':
            if 'r0' in valid_moves:
                redeem, choice = self.token_law(state)
                if redeem: return self.choose(choice, input_string)
            victory_cards, cards_constructable = self.card_victory_points(valid_moves, state, function)
            victory_wonders, wonders_constructable = self.wonder_victory_points(valid_moves, state)
            max_card = max(victory_cards) if sum(victory_cards) > 0 else 0
            max_wonder = max(victory_wonders) if sum(victory_wonders) > 0 else 0
            if not (sum(victory_cards) == 0 and sum(victory_wonders) == 0):
                if max_card > max_wonder:
                    choice = 'c' + str(cards_constructable[victory_cards.index(max(victory_cards))])
                else:
                    wonder = wonders_constructable[victory_wonders.index(max(victory_wonders))]
                    wonder_moves = [move for move in valid_moves if move[0] == 'w']
                    wonder_moves = [move for move in wonder_moves if int(move[-1]) == wonder]
                    choice = random.choice(wonder_moves)
                return self.choose(choice, input_string)
        elif function == 'token' or function == 'library':
            victory_tokens, tokens_constructable = self.token_victory_points(state, valid_moves, function)
            if not sum(victory_tokens) == 0:
                choice = 'c' + str(tokens_constructable[victory_tokens.index(max(victory_tokens))])
                return self.choose(choice, input_string)
        elif function == 'law':
            redeem, choice = self.token_law(state)
            if redeem: return self.choose(choice, input_string)
        choice = random.choice(valid_moves)
        return self.choose(choice, input_string)

    def choose(self, choice, input_string):
        self.print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice

    # determines if the law token should be redeemed
    def token_law(self, state):
        tokens = [token.token_name for token in state['progress_board'].tokens if token.token_in_slot]
        science_equal_1 = [sci == 1 for sci in state['player'].science]
        redeem, choice = False, None
        if any(token in ['Philosophy', 'Agriculture', 'Mathematics'] for token in tokens) and any(science_equal_1):
            redeem = True
            choice = 'r' + str(science_equal_1.index(True))
        return redeem, choice

    # determines the victory points of constructable cards
    def card_victory_points(self, valid_moves, state, function):
        cards_constructable = [int(move[1:]) for move in valid_moves if move[0] == 'c']
        if function == 'mausoleum': cards = state['state_variables'].discarded_cards
        else: cards = [state['age_board'][i].card_in_slot for i in cards_constructable]
        victory_cards = []
        for card in cards:
            if card.card_type == 'Purple':
                victory_cards.append(self.guild_victory_points(state, card.card_effect_passive))
            elif card.card_type == 'Red':
                military_points = int(card.card_effect_passive[0])
                if 'Strategy' in [token.token_name for token in state['player'].progress_tokens_in_play]: military_points += 1
                points = self.military_victory_points(state, military_points) + self.guild_effect(state, card)
                victory_cards.append(points)
            elif 'V' in card.card_effect_passive:
                points = int(card.card_effect_passive[0]) + self.guild_effect(state, card)
                victory_cards.append(points)
            else:
                victory_cards.append(0)
        return victory_cards, cards_constructable

    # determines the victory points of constructable wonders
    def wonder_victory_points(self, valid_moves, state):
        wonders_constructable = list(set([int(move[-1]) for move in valid_moves if move[0] == 'w']))
        wonders = [state['player'].wonders_in_hand[i] for i in wonders_constructable]
        owned_guild_cards = [guild_card.card_effect_passive.split()[2] for guild_card in state['player'].cards_in_play
                             if guild_card.card_type == 'Purple']
        victory_wonders = []
        for wonder in wonders:
            points = 0
            if 'Wonder' in owned_guild_cards:
                points += 2
            if 'V' in wonder.wonder_effect_when_played:
                points += int(wonder.wonder_effect_when_played[0])
            if 'M' in wonder.wonder_effect_when_played:
                points += self.military_victory_points(state, int(wonder.wonder_effect_when_played[-2]))
            victory_wonders.append(points)
        return victory_wonders, wonders_constructable

    # determines the true value of purple cards
    def guild_victory_points(self, state, effect):
        color = effect.split()[2]
        if 'Grey' in effect.split() and 'Brown' in effect.split():
            type_count = len([1 for card in state['player'].cards_in_play if card.card_type in ['Grey', 'Brown']])
            type_count = max(type_count, len([1 for card in state['opponent'].cards_in_play if card.card_type in ['Grey', 'Brown']]))
        elif 'Wonder' in effect.split():
            type_count = len(state['player'].wonders_in_play)
            type_count = max(type_count, len(state['opponent'].wonders_in_play))
            type_count *= 2  # wonders are worth 2 victory points instead of 1
        elif '$$$' in effect.split():
            type_count = state['player'].coins // 3
            type_count = max(type_count, state['opponent'].coins // 3)
        else:  # handle 'Yellow', 'Blue', 'Green', 'Red'
            type_count = len([1 for card in state['player'].cards_in_play if card.card_type == color])
            type_count = max(type_count, len([1 for card in state['opponent'].cards_in_play if card.card_type == color]))
        return type_count

    # increases the victory points of a card based on owned guild cards
    def guild_effect(self, state, card):
        owned_guild_cards = [guild_card.card_effect_passive.split()[2] for guild_card in state['player'].cards_in_play if guild_card.card_type == 'Purple']
        if 'Grey' in owned_guild_cards: owned_guild_cards.append('Brown')
        points = 0
        if card.card_type in owned_guild_cards:
            points += 1
        return points

    # determine the victory points gained through military cards
    def military_victory_points(self, state, military_points):
        if state['state_variables'].turn_player == 1: military_points *= (-1)
        military_points = state['state_variables'].military_track + military_points
        if abs(military_points) in [0]: points = 0
        elif abs(military_points) in [1, 2]: points = 2
        elif abs(military_points) in [3, 4, 5]: points = 5
        elif abs(military_points) in [6, 7, 8]: points = 10
        else: points = 30
        if military_points < 0: points *= (-1)
        return abs(points - state['state_variables'].victory_points_awarded)

    # determine the victory points gained through each token
    def token_victory_points(self, state, valid_moves, function):
        tokens_constructable = [int(move[1]) for move in valid_moves]
        if function == 'library': tokens = [token.token_name for token in state['progress_board'].discarded_tokens]
        else: tokens = [state['progress_board'].tokens[i].token_name for i in tokens_constructable]
        owned_tokens = [token.token_name for token in state['player'].progress_tokens_in_play]
        victory_tokens = []
        for token in tokens:
            if token == 'Philosophy':
                victory_tokens.append(7)
            elif token == 'Agriculture':
                victory_tokens.append(4)
            elif token == 'Mathematics':
                victory_tokens.append((len(owned_tokens)+1)*3)
            else:
                victory_tokens.append(0)
        return victory_tokens, tokens_constructable

# A greedy agent which always chooses the action with the highest military points
class GreedyMilitaryAgent:

    def __init__(self, defined_print):
        self.original_print = print
        self.print = defined_print


    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, input_string, state, function):
        if function == 'main' or function == 'mausoleum':
            if 'r0' in valid_moves:
                redeem, choice = self.token_law(state)
                if redeem: return self.choose(choice, input_string)
            military_cards, cards_constructable = self.card_military_points(valid_moves, state, function)
            military_wonders, wonders_constructable = self.wonder_military_points(valid_moves, state)
            max_card = max(military_cards) if sum(military_cards) > 0 else 0
            max_wonder = max(military_wonders) if sum(military_wonders) > 0 else 0
            if not (sum(military_cards) == 0 and sum(military_wonders) == 0):
                if max_card > max_wonder:
                    choice = 'c' + str(cards_constructable[military_cards.index(max(military_cards))])
                else:
                    wonder = wonders_constructable[military_wonders.index(max(military_wonders))]
                    wonder_moves = [move for move in valid_moves if move[0] == 'w']
                    wonder_moves = [move for move in wonder_moves if int(move[-1]) == wonder]
                    choice = random.choice(wonder_moves)
                return self.choose(choice, input_string)
        elif function == 'token' or function == 'library':
            victory_tokens, tokens_constructable = self.token_strategy(state, valid_moves, function)
            if not sum(victory_tokens) == 0:
                choice = 'c' + str(tokens_constructable[victory_tokens.index(max(victory_tokens))])
                return self.choose(choice, input_string)
        elif function == 'law':
            redeem, choice = self.token_law(state)
            if redeem: return self.choose(choice, input_string)
        choice = random.choice(valid_moves)
        return self.choose(choice, input_string)

    def choose(self, choice, input_string):
        self.print(input_string + str(fg.red + "Choice of Agent: " + choice + rs.all))
        return choice

    # choose strategy token if available otherwise random choice
    def token_strategy(self, state, valid_moves, function):
        tokens_constructable = [int(move[1]) for move in valid_moves]
        if function == 'library': tokens = [token.token_name for token in state['progress_board'].discarded_tokens]
        else: tokens = [state['progress_board'].tokens[i].token_name for i in tokens_constructable]
        victory_tokens = []
        for token in tokens:
            if token == 'Strategy':
                victory_tokens.append(5)
            else:
                victory_tokens.append(0)
        return victory_tokens, tokens_constructable

    # determines if the law token should be redeemed
    def token_law(self, state):
        tokens = [token.token_name for token in state['progress_board'].tokens if token.token_in_slot]
        science_equal_1 = [sci == 1 for sci in state['player'].science]
        redeem, choice = False, None
        if 'Strategy' in tokens and any(science_equal_1):
            redeem = True
            choice = 'r' + str(science_equal_1.index(True))
        return redeem, choice

    # determines the military points of constructable cards
    def card_military_points(self, valid_moves, state, function):
        cards_constructable = [int(move[1:]) for move in valid_moves if move[0] == 'c']
        if function == 'mausoleum': cards = state['state_variables'].discarded_cards
        else: cards = [state['age_board'][i].card_in_slot for i in cards_constructable]
        military_cards = []
        for card in cards:
            if card.card_type == 'Red':
                military_points = int(card.card_effect_passive[0])
                if 'Strategy' in [token.token_name for token in state['player'].progress_tokens_in_play]: military_points += 1
                military_cards.append(military_points)
            else:
                military_cards.append(0)
        return military_cards, cards_constructable

    # determines the military points of constructable wonders
    def wonder_military_points(self, valid_moves, state):
        wonders_constructable = list(set([int(move[-1]) for move in valid_moves if move[0] == 'w']))
        wonders = [state['player'].wonders_in_hand[i] for i in wonders_constructable]
        military_wonders = []
        for wonder in wonders:
            points = 0
            if 'M' in wonder.wonder_effect_when_played:
                points += int(wonder.wonder_effect_when_played[-2])
            military_wonders.append(points)
        return military_wonders, wonders_constructable


