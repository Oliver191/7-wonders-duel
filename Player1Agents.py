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
        choice = random.choice(valid_moves)
        return self.choose(choice, convertActionName, all_actions)

    def choose(self, choice, convertActionName, all_actions):
        action = convertActionName(choice)
        if self.display: print(str(fg.green + "RuleBased: " + action + rs.all))
        action = all_actions.index(action)
        return action

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
        choice = random.choice(valid_moves)
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