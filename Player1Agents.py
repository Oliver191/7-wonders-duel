import numpy as np
import random
from sty import fg, bg, rs

class RandomAgent:

    def __init__(self, display):
        self.display = display

    def getAction(self, valid_moves, convertActionName, all_actions, state, mode):
        action = np.random.choice(valid_moves)
        action = convertActionName(action)
        if self.display: print(str(fg.green + "RANDOM: " + action + rs.all))
        action = all_actions.index(action)
        return action


class RuleBasedAgent:

    def __init__(self, display):
        self.display = display
        self.util = AgentUtil()
        self.wonders = ['Piraeus', 'The Appian Way', 'The Great Library', 'The Mausoleum', 'The Hanging Gardens', 'The Temple of Artemis', 'The Sphinx']

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, convertActionName, all_actions, state, mode):
        if mode == 'wonders':
            choice, _ = self.util.wonder_selection(valid_moves,state,self.wonders)
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'main' or mode == 'The Mausoleum':
            if 'r0' in valid_moves:
                redeem, choice = self.util.token_law(state)
                if redeem: return self.choose(choice, convertActionName, all_actions)
            choice = self.card_selection(state, valid_moves, mode)
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'token' or mode == 'The Great Library':
            tokens = ['Law', 'Theology', 'Economy', 'Strategy', 'Philosophy']
            choice, _ = self.util.token_selection(state, valid_moves, mode, tokens)
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'law':
            redeem, choice = self.util.token_law(state)
            if redeem: return self.choose(choice, convertActionName, all_actions)
            else: return self.choose('q', convertActionName, all_actions)

        less_valid_moves = self.delete_redemption(valid_moves)
        choice = random.choice(less_valid_moves)
        return self.choose(choice, convertActionName, all_actions)

    def choose(self, choice, convertActionName, all_actions):
        action = convertActionName(choice)
        if self.display: print(str(fg.green + "RuleBased: " + action + rs.all))
        action = all_actions.index(action)
        return action

    def delete_redemption(self, valid_moves):
        less_valid_moves = valid_moves.copy()
        for i in ['r0', 'r1', 'r2', 'r3', 'r4', 'r5']:
            if i in less_valid_moves:
                less_valid_moves.remove(i)
        return less_valid_moves

    # select cards based on their color
    def card_selection(self, state, valid_moves, mode):
        cards_constructable = [int(move[1:]) for move in valid_moves if move[0] == 'c']
        if mode == 'The Mausoleum': cards = state['state_variables'].discarded_cards
        else: cards = [state['age_board'][i].card_in_slot for i in cards_constructable]
        card_types = [card.card_type for card in cards]
        card_prerequisites = [card.card_prerequisite for card in cards]
        owned_cards = [card.card_name for card in state['player'].cards_in_play]
        wonders_constructable = [move for move in valid_moves if move[0] == 'w']

        if abs(state['state_variables'].military_track) >= 4 and 'Red' in card_types:
            military_points = [int(card.card_effect_passive[0]) if card.card_type == 'Red' else 0 for card in cards]
            return 'c' + str(cards_constructable[military_points.index(max(military_points))])
        elif 'Green' in card_types: #construct any green cards
            return self.green_card(state, cards, cards_constructable)
        for prerequisite in card_prerequisites: #construct any free cards
            if prerequisite in owned_cards:
                return 'c' + str(cards_constructable[card_prerequisites.index(prerequisite)])
        if 'Yellow' in card_types: #construct any yellow cards
            return 'c' + str(cards_constructable[card_types.index('Yellow')])
        elif wonders_constructable: #construct any wonders
            return self.wonder_selection(state, wonders_constructable)
        for color in ['Grey', 'Brown', 'Red']: #construct any grey, brown, or red cards
            if color in card_types:
                return 'c' + str(cards_constructable[card_types.index(color)])
        less_valid_moves = self.delete_redemption(valid_moves)
        choice = random.choice(less_valid_moves)
        if choice[0] == 'd':
            choice = self.discard_card(state, valid_moves, choice)
        return choice

    # select a scientific symbol not yet owned, otherwise select any green card
    def green_card(self, state, cards, cards_constructable):
        green_cards = [card for card in cards if card.card_type == 'Green']
        for i, card in enumerate(green_cards):
            symbol = int(card.card_effect_passive[-1]) - 1
            if state['player'].science[symbol] == 0:
                return 'c' + str(cards_constructable[cards.index(green_cards[i])])
        for i, card in enumerate(green_cards):
            symbol = int(card.card_effect_passive[-1]) - 1
            if state['player'].science[symbol] == 1:
                return 'c' + str(cards_constructable[cards.index(green_cards[i])])
        return 'c' + str(cards_constructable[cards.index(random.choice(green_cards))])

    # Select one of the specified wonders, if possible, otherwise pick a random one
    def wonder_selection(self, state, wonders_constructable):
        selectable = [int(move[-1]) for move in wonders_constructable]
        wonders_selectable = [state['player'].wonders_in_hand[i].wonder_name for i in selectable]
        for wonder in self.wonders:
            if wonder in wonders_selectable:
                return wonders_constructable[wonders_selectable.index(wonder)]
        return random.choice(wonders_constructable)

    # pick a good card to discard
    def discard_card(self, state, valid_moves, choice):
        cards_discardable = [int(move[1:]) for move in valid_moves if move[0] == 'd']
        cards = [state['age_board'][i].card_in_slot for i in cards_discardable]
        card_types = [card.card_type for card in cards]
        for color in ['Red', 'Blue', 'Purple', 'Green', 'Yellow']:
            if color in card_types:
                return 'd' + str(cards_discardable[card_types.index(color)])
        return choice


# A greedy agent which always chooses the action with the highest number of victory points
class GreedyCivilianAgent:

    def __init__(self, display):
        self.display = display
        self.util = AgentUtil()
        self.random = False

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, convertActionName, all_actions, state, mode):
        self.random = False
        if mode == 'wonders':
            choice, self.random = self.util.wonder_selection(valid_moves,state,['The Pyramids', 'The Sphinx', 'The Great Lighthouse', 'The Great Library'])
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'main' or mode == 'The Mausoleum':
            if 'r0' in valid_moves:
                redeem, choice = self.token_law(state)
                if redeem: return self.choose(choice, convertActionName, all_actions)
            victory_cards, cards_constructable = self.card_victory_points(valid_moves, state, mode)
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
                return self.choose(choice, convertActionName, all_actions)
        elif mode == 'token' or mode == 'The Great Library':
            owned_tokens = [token.token_name for token in state['player'].progress_tokens_in_play]
            token_dict = {'Philosophy':7, 'Agriculture':4, 'Mathematics':(len(owned_tokens)+1)*3}
            victory_tokens, tokens_constructable = self.token_selection(state, valid_moves, mode, token_dict)
            if not sum(victory_tokens) == 0:
                choice = 'c' + str(tokens_constructable[victory_tokens.index(max(victory_tokens))])
                return self.choose(choice, convertActionName, all_actions)
        elif mode == 'law':
            redeem, choice = self.token_law(state)
            if redeem: return self.choose(choice, convertActionName, all_actions)
        choice = random.choice(valid_moves)
        self.random = True
        return self.choose(choice, convertActionName, all_actions)

    def choose(self, choice, convertActionName, all_actions):
        action = convertActionName(choice)
        if self.display: print(str(fg.green + "RuleBased: " + action + rs.all))
        action = all_actions.index(action)
        return action

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
    def card_victory_points(self, valid_moves, state, mode):
        cards_constructable = [int(move[1:]) for move in valid_moves if move[0] == 'c']
        if mode == 'The Mausoleum': cards = state['state_variables'].discarded_cards
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

    # chooses the specified token if available otherwise random choice
    def token_selection(self, state, valid_moves, mode, token_dict):
        tokens_constructable = [int(move[1]) for move in valid_moves]
        if mode == 'The Great Library': tokens = [token.token_name for token in state['progress_board'].discarded_tokens]
        else: tokens = [state['progress_board'].tokens[i].token_name for i in tokens_constructable]
        victory_tokens = []
        for token in tokens:
            if token in token_dict.keys():
                victory_tokens.append(token_dict[token])
            else:
                victory_tokens.append(0)
        return victory_tokens, tokens_constructable


# A greedy agent which always chooses the action with the highest military points
class GreedyMilitaryAgent:

    def __init__(self, display):
        self.display = display
        self.util = AgentUtil()
        self.random = False

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, convertActionName, all_actions, state, mode):
        self.random = False
        if mode == 'wonders':
            choice, self.random = self.util.wonder_selection(valid_moves,state,['The Colossus', 'The Statue of Zeus', 'Circus Maximus'])
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'main' or mode == 'The Mausoleum':
            if 'r0' in valid_moves:
                redeem, choice = self.token_law(state)
                if redeem: return self.choose(choice, convertActionName, all_actions)
            military_cards, cards_constructable = self.card_military_points(valid_moves, state, mode)
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
                return self.choose(choice, convertActionName, all_actions)
        elif mode == 'token' or mode == 'The Great Library':
            choice, self.random = self.util.token_selection(state, valid_moves, mode, ['Strategy'])
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'law':
            redeem, choice = self.token_law(state)
            if redeem: return self.choose(choice, convertActionName, all_actions)
        choice = random.choice(valid_moves)
        self.random = True
        return self.choose(choice, convertActionName, all_actions)

    def choose(self, choice, convertActionName, all_actions):
        action = convertActionName(choice)
        if self.display: print(str(fg.green + "RuleBased: " + action + rs.all))
        action = all_actions.index(action)
        return action

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
    def card_military_points(self, valid_moves, state, mode):
        cards_constructable = [int(move[1:]) for move in valid_moves if move[0] == 'c']
        if mode == 'The Mausoleum': cards = state['state_variables'].discarded_cards
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

# A greedy agent which always chooses science cards
class GreedyScientificAgent:

    def __init__(self, display):
        self.display = display
        self.util = AgentUtil()
        self.random = False

    # given the legal actions and information about the game state, return an action
    def getAction(self, valid_moves, convertActionName, all_actions, state, mode):
        self.random = False
        if mode == 'wonders':
            choice, self.random = self.util.wonder_selection(valid_moves,state,['The Great Library', 'The Mausoleum'])
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'main' or mode == 'The Mausoleum':
            if 'r0' in valid_moves:
                redeem, choice = self.util.token_law(state)
                if redeem: return self.choose(choice, convertActionName, all_actions)
            science_cards, cards_constructable = self.card_science_symbols(valid_moves, state, mode)
            science_wonders, wonders_constructable = self.wonder_science_symbols(valid_moves, state)
            max_card = max(science_cards) if sum(science_cards) > 0 else 0
            max_wonder = max(science_wonders) if sum(science_wonders) > 0 else 0
            if not (sum(science_cards) == 0 and sum(science_wonders) == 0):
                if max_card > max_wonder:
                    choice = 'c' + str(cards_constructable[science_cards.index(max(science_cards))])
                else:
                    wonder = wonders_constructable[science_wonders.index(max(science_wonders))]
                    wonder_moves = [move for move in valid_moves if move[0] == 'w']
                    wonder_moves = [move for move in wonder_moves if int(move[-1]) == wonder]
                    choice = random.choice(wonder_moves)
                return self.choose(choice, convertActionName, all_actions)
        elif mode == 'token' or mode == 'The Great Library':
            choice, self.random = self.util.token_selection(state, valid_moves, mode, ['Law'])
            return self.choose(choice, convertActionName, all_actions)
        elif mode == 'law':
            redeem, choice = self.util.token_law(state)
            if redeem: return self.choose(choice, convertActionName, all_actions)
            else: return self.choose('q', convertActionName, all_actions)
        choice = random.choice(valid_moves)
        self.random = True
        return self.choose(choice, convertActionName, all_actions)

    def choose(self, choice, convertActionName, all_actions):
        action = convertActionName(choice)
        if self.display: print(str(fg.green + "RuleBased: " + action + rs.all))
        action = all_actions.index(action)
        return action

    # determines scientific symbols of constructable cards
    def card_science_symbols(self, valid_moves, state, mode):
        cards_constructable = [int(move[1:]) for move in valid_moves if move[0] == 'c']
        if mode == 'The Mausoleum': cards = state['state_variables'].discarded_cards
        else: cards = [state['age_board'][i].card_in_slot for i in cards_constructable]
        science_cards = []
        for card in cards:
            if card.card_type == 'Green':
                symbol = int(card.card_effect_passive[-1])-1
                if state['player'].science[symbol] == 0:
                    science_cards.append(11)
                else:
                    science_cards.append(5)
            else:
                science_cards.append(0)
        return science_cards, cards_constructable

    # determines if great library or mausoleum should be built
    def wonder_science_symbols(self, valid_moves, state):
        wonders_constructable = list(set([int(move[-1]) for move in valid_moves if move[0] == 'w']))
        wonders = [state['player'].wonders_in_hand[i] for i in wonders_constructable]
        card_symbols = [int(card.card_effect_passive[-1])-1 for card in state['state_variables'].discarded_cards if card.card_type == 'Green']
        tokens = [token.token_name for token in state['progress_board'].tokens if token.token_in_slot]
        all_tokens = [token.token_name for token in state['progress_board'].tokens]
        mausoleum = False
        for i in card_symbols:
            if state['player'].science[i] == 0 or (state['player'].science[i] == 1 and 'Law' in tokens):
                mausoleum = True
        science_wonders = []
        for wonder in wonders:
            points = 0
            if wonder.wonder_name == 'The Great Library' and 'Law' not in all_tokens:
                points = 10
            if wonder.wonder_name == 'The Mausoleum' and mausoleum:
                points = 10
            science_wonders.append(points)
        return science_wonders, wonders_constructable


# A class summarizing useful modes shared by agents
class AgentUtil:

    # chooses the specified token if available otherwise random choice
    def token_selection(self, state, valid_moves, mode, token_list):
        if mode == 'The Great Library': selectable_tokens = [token.token_name for token in state['progress_board'].discarded_tokens]
        else: selectable_tokens = [token.token_name if token.token_in_slot else None for token in state['progress_board'].tokens]
        selectable = []
        for token in token_list:
            if token in selectable_tokens:
                selectable.append(True)
            else:
                selectable.append(False)
        if any(selectable):
            return 'c' + str(selectable_tokens.index(token_list[selectable.index(True)])), False
        else:
            return random.choice(valid_moves), True


    # chooses one of the specified wonders if it is selectable
    def wonder_selection(self, valid_moves, state, wonder_list):
        shift = 0 if any(state['wonders_selectable'][:4]) else 4
        selectable_wonders = [wonder.wonder_name if state['wonders_selectable'][0+shift:4+shift][i] else None for i, wonder in enumerate(state['wonders'][0+shift:4+shift])]
        selectable = []
        for wonder in wonder_list:
            if wonder in selectable_wonders:
                selectable.append(True)
            else:
                selectable.append(False)
        if any(selectable):
            return 'w' + str(selectable_wonders.index(wonder_list[selectable.index(True)])), False
        else:
            return random.choice(valid_moves), True

    # determines if the law token should be redeemed
    def token_law(self, state):
        redeem, choice = False, None
        if state['player'].science.count(0) == 1:
            redeem = True
            choice = 'r' + str(state['player'].science.index(0))
        elif state['state_variables'].current_age == 2 and state['player'].science.count(0) > 2 and state['player'].science.count(1) > 0:
            redeem = True
            choice = 'r' + str(state['player'].science.index(1))
        return redeem, choice