'''Module to play a game of Seven Wonders Duel'''
import numpy as np
from numpy.random import default_rng
from sty import fg, bg, rs
from seven_wonders_visual import ImageDisplay
from collections import Counter
import copy

from gymnasium import Env
import gymnasium.spaces as spaces
from Player1Agents import *
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO

def mask_fn(env: Env) -> np.ndarray:
    return env.valid_action_mask()

class WondersEnv(Env):
    """Custom Environment that follows the Gym interface."""

    metadata = {"render.modes": ["human"]}

    def __init__(self, display=False, agent=RandomAgent):
        super(WondersEnv, self).__init__()

        self.csv_dict = self.read_data()
        self.name_mapping = self.map_name_int()
        self.all_actions = self.enumerate_all_actions()
        self.action_space = spaces.Discrete(len(self.all_actions))
        self.observation_space = spaces.Dict({'age_board': spaces.Box(low=0, high=200, shape=(26,), dtype=int), #2,13
                                              'player': spaces.Box(low=0, high=200, shape=(15,), dtype=int),
                                              'player_cards': spaces.Box(low=0, high=200, shape=(128,), dtype=int), #4,30
                                              'opponent': spaces.Box(low=0, high=200, shape=(15,), dtype=int),
                                              'opponent_cards': spaces.Box(low=0, high=200, shape=(128,), dtype=int), #4,30
                                              'state_variables': spaces.Box(low=0, high=200, shape=(3,), dtype=int),
                                              'progress_board': spaces.Box(low=0, high=200, shape=(10,), dtype=int), #2,5
                                             })
        # self.observation_space = spaces.Box(low=0, high=200, shape=(15,), dtype=int)
        self.display = display
        self.agent = agent
        self.initialize_agents()
        self.perform_check = False

    def __repr__(self):
        return repr(self.outcome)

    def __deepcopy__(self, memo):
        if self in memo:
            return memo[self]
        new_instance = WondersEnv(self.display, self.agent)
        new_instance.reset()

        for attr, value in self.__dict__.items():
            setattr(new_instance, attr, copy.deepcopy(value, memo))

        memo[self] = new_instance
        return new_instance

    def step(self, action):
        action = self.convertAction(action)
        player = self.state_variables.turn_player
        opponent = player ^ 1
        discarded_cards = self.state_variables.discarded_cards
        if action == 'illegal':
            self.reward = -10
        elif self.mode == 'wonders':
            self.draft_wonders(action)
        elif self.mode == 'main':
            self.select_action(action)
        elif self.mode == 'token':
            self.select_token(action)
        elif self.mode == 'law':
            self.players[player].token_law(action, self.progress_board, self.display)
            if action != 's':
                self.mode = 'main'
                self.check_progress_tokens(player)
        elif self.mode in ['Circus Maximus', 'The Statue of Zeus']:
            color = 'Grey' if self.mode == 'Circus Maximus' else 'Brown'
            wonder_name = 'Circus Maximus' if self.mode == 'Circus Maximus' else 'The Statue of Zeus'
            self.players[player].wonder_destory_card(action, self.players[opponent], color, player,discarded_cards, wonder_name, self.display)
            if action != 's': self.mode = 'main'
        elif self.mode == 'The Mausoleum':
            self.players[player].wonder_mausoleum(action, discarded_cards, self.players[player].cards_in_play,self.players[opponent].cards_in_play, self.display)
            if action != 's':
                self.mode = 'main'
                self.check_progress_tokens(player)
        elif self.mode == 'The Great Library':
            self.players[player].wonder_great_library(action, self.progress_board.discarded_tokens, self.display)
            if action != 's': self.mode = 'main'
            if self.players[player].law: self.mode = 'law'

        if self.perform_check and self.mode == 'main' and action != 'illegal':
            self.perform_checks()
            self.perform_check = False

        if self.state_variables.turn_player == self.agent_num and not self.done and self.agent1 is not None:
            if not isinstance(self.agent1, MaskablePPO):
                self.step(self.getAction())
            else:
                self.get_observation()
                action_masks = self.valid_action_mask()
                action, _ = self.agent1.predict(self.state, action_masks=action_masks)
                self.step(action)

        self.get_observation()
        if action != 'illegal': self.get_reward()
        return self.state, self.reward, self.done, False, {}

    def reset(self, seed=None, options=None):
        self.done = False
        self.nameAction = {}
        self.players = [Player(0, 'human', None), Player(1, 'human', None)]
        self.age_boards = [Age(age, self.csv_dict) for age in range(1, 4)]
        self.state_variables = StateVariables()
        self.progress_board = ProgressBoard(self.csv_dict)
        self.outcome, self.state, self.constructable_dict = None, None, {}
        self.mode, self.reward, self.agent_num = 'wonders', 0, np.random.choice([0,1])
        self.wonders, self.wonders_selectable = self.set_wonders()
        self.display_wonders()
        self.science_awarded = [False for _ in range(6)]
        self.masks = self.valid_action_mask()
        if self.state_variables.turn_player == self.agent_num and self.agent1 is not None:
            if not isinstance(self.agent1, MaskablePPO):
                self.step(self.getAction())
            else:
                self.get_observation()
                action_masks = self.valid_action_mask()
                action, _ = self.agent1.predict(self.state, action_masks=action_masks)
                self.step(action)
        self.get_observation()
        return self.state, {}

    def render(self):
        self.step('s')

    def initialize_agents(self):
        if not isinstance(self.agent, str):
            self.agent1 = self.agent(self.display) if self.agent is not None else None
        else:
            env = ActionMasker(self, mask_fn)
            self.agent1 = MaskablePPO.load(f'baselines3_agents/{self.agent}', env=env)

    def getAction(self):
        state = self.getAgentState()
        action = self.agent1.getAction(self.valid_moves(), self.convertActionName, self.all_actions, state, self.mode)
        return action

    def getAgentState(self):
        state = {'age_board': self.age_boards[self.state_variables.current_age].card_positions,
                 'player': self.players[self.state_variables.turn_player],
                 'opponent': self.players[self.state_variables.turn_player ^ 1],
                 'state_variables': self.state_variables,
                 'progress_board': self.progress_board,
                 'wonders': self.wonders,
                 'wonders_selectable': self.wonders_selectable}
        return state


    def read_data(self):
        csv_dict = {'age_layouts': np.genfromtxt('age_layout.csv', delimiter=',', skip_header=1, dtype=str),
                    'age_layouts_labels': np.genfromtxt('age_layout.csv', delimiter=',', dtype=str, max_rows=1),
                    'card_list': np.genfromtxt('card_list.csv', delimiter=',', skip_header=1, dtype=str),
                    'card_list_labels': np.genfromtxt('card_list.csv', delimiter=',', dtype=str, max_rows=1),
                    'token_list': np.genfromtxt('progress_tokens.csv', delimiter=',', skip_header=1, dtype=str),
                    'wonder_list': np.genfromtxt('wonder_list.csv', delimiter=',', skip_header=1, dtype=str)}
        return csv_dict

    def map_name_int(self):
        name_list = list(self.csv_dict['card_list'][:, 0])
        name_list += list(self.csv_dict['wonder_list'][:, 0])
        name_list += list(self.csv_dict['token_list'][:, 0])
        mapping = {}
        for i, name in enumerate(name_list):
            mapping[name] = i+1
        return mapping

    def convertAction(self, action):
        if type(action) != str:
            action_masks = self.valid_action_mask()
            if action_masks[int(action)] == 1:
                action = self.all_actions[int(action)]
                if self.display: print(str(fg.red + "Choice: " + action + rs.all))
                action = self.convertNameAction(action)
            else:
                print("\n", str(fg.red + "Illegal action: " + self.all_actions[int(action)] + rs.all), "\n")
                # action = np.random.choice(self.valid_moves())
                action = 'illegal'
        return action

    def get_reward(self):
        if self.done:
            if 'Player' in self.outcome:
                if self.outcome.split()[1] == "1":
                    self.reward = -100 if self.agent_num == 0 else 100
                elif self.outcome.split()[1] == "2":
                    self.reward = 100 if self.agent_num == 0 else -100
            else:
                self.reward = 10
        else:
            # self.reward = 0
            self.reward = self.getScore()

    def getScore(self):
        score = 0
        player = self.state_variables.turn_player
        for i in range(len(self.players[player].science)):
            if self.players[player].science[i] == 1 and not self.science_awarded[i]:
                score += 2 #1
                self.science_awarded[i] = True
        if self.players[player].law: score += 2 #1
        return score

    def get_observation(self):
        player = self.state_variables.turn_player
        player_attributes, player_cards = self.convert_player(self.players[player])
        opponent_attributes, opponent_cards = self.convert_player(self.players[player^1])
        self.state = {'age_board': self.convert_age_board(),
                      'player': player_attributes,
                      'player_cards': player_cards,
                      'opponent': opponent_attributes,
                      'opponent_cards': opponent_cards,
                      'state_variables': self.convert_state_variables(),
                      'progress_board': self.convert_progress_board()
                     }
        self.valid_action_mask()

    def update_constructable(self):
        player = self.state_variables.turn_player
        self.constructable_dict = {'cards': [card.card_name for card in self.players[player].cards_in_play],
                                   'wonders': [wonder.wonder_name for wonder in self.players[player].wonders_in_play],
                                   'owned_tokens': [token.token_name for token in self.players[player].progress_tokens_in_play],
                                   'opponent_tokens': [token.token_name for token in self.players[player ^ 1].progress_tokens_in_play]}

    def convert_to_np(self, *arrays, max_len=None):
        lengths = [len(arr) for arr in arrays]
        if max_len is None: max_len = max(lengths)
        result = np.zeros((len(arrays), max_len), dtype=int)
        for i, arr in enumerate(arrays):
            result[i, :lengths[i]] = np.array(arr, dtype=int)
        return result

    def convert_age_board(self):
        cardSlots = self.age_boards[self.state_variables.current_age].card_positions
        shift = 0 if any(self.wonders_selectable[:4]) else 4
        cards = [self.name_mapping[cardSlot.card_in_slot.card_name] for cardSlot in cardSlots if cardSlot.card_visible == 1 and cardSlot.card_in_slot is not None]
        wonders = [self.name_mapping[wonder.wonder_name] for i, wonder in enumerate(self.wonders[0+shift:4+shift]) if self.wonders_selectable[0+shift:4+shift][i]]
        return self.convert_to_np(cards, wonders, max_len=13).flatten()

    def convert_player(self, custom_class):
        class_dict = {}
        for attr_name, attr_value in vars(custom_class).items():
            if attr_name not in ['player_type', 'agent', 'law', 'replay', 'wonder_effects', 'science']:
                class_dict[attr_name] = attr_value
        cards_in_play = [self.name_mapping[card.card_name] for card in class_dict['cards_in_play']]
        wonders_in_hand = [self.name_mapping[wonder.wonder_name] for wonder in class_dict['wonders_in_hand'] if not wonder.wonder_in_play]
        wonders_in_play = [self.name_mapping[wonder.wonder_name] for wonder in class_dict['wonders_in_play']]
        progress_tokens_in_play = [self.name_mapping[token.token_name] for token in class_dict['progress_tokens_in_play']]
        player_cards = self.convert_to_np(cards_in_play, wonders_in_hand, wonders_in_play, progress_tokens_in_play, max_len=32) # size 4
        for name in ['cards_in_play', 'wonders_in_hand', 'wonders_in_play', 'progress_tokens_in_play']:
            del class_dict[name]
        player_attributes = np.array(list(class_dict.values()) + custom_class.science, dtype=int) # size 15
        return player_attributes, player_cards.flatten()

    def convert_state_variables(self):
        list1 = [self.state_variables.turn_player]
        list2 = [self.state_variables.current_age]
        list3 = [1 if self.state_variables.turn_choice else 0]
        # discarded_cards = [0]
        # if self.mode == 'The Mausoleum':
        #     discarded_cards = [self.name_mapping[card.card_name] for card in self.state_variables.discarded_cards]
        # return self.convert_to_np(list1, list2, list3, discarded_cards)
        return np.array(list1+list2+list3, dtype=int)

    def convert_progress_board(self):
        tokens = [self.name_mapping[token.token_name] for token in self.progress_board.tokens if token.token_in_slot]
        discarded_tokens = []
        if self.mode == 'The Great Library':
            discarded_tokens = [self.name_mapping[token.token_name] for token in self.progress_board.discarded_tokens]
        return self.convert_to_np(tokens, discarded_tokens, max_len=5).flatten()

    def set_wonders(self):
        wonder_count = 8
        chosen_wonders = self.csv_dict['wonder_list'][np.random.choice(self.csv_dict['wonder_list'].shape[0], wonder_count, replace=False)]
        wonders, wonders_selectable = [], []
        for wonder in chosen_wonders:
            wonders.append(Wonder(wonder[0], wonder[1], wonder[2], wonder[3], False))
            wonders_selectable.append(True)
        return wonders, wonders_selectable

    def draft_wonders(self, action):
        if action == 's': return self.show_wonders()
        player = self.state_variables.turn_player
        opponent = player ^ 1
        shift = 0 if any(self.wonders_selectable[:4]) else 4
        choice = int(action[1])+shift
        self.choose_wonder(player, choice)
        if self.wonders_selectable[0+shift:4+shift].count(True) == 3:
            self.state_variables.change_turn_player()
        elif self.wonders_selectable[0+shift:4+shift].count(True) == 1:
            choice = self.wonders_selectable[0+shift:4+shift].index(True) + shift
            self.choose_wonder(opponent, choice)
        if not any(self.wonders_selectable):
            self.mode = 'main'
            self.display_game_state()
        else:
            self.display_wonders()

    def choose_wonder(self, player, choice):
        self.players[player].wonders_in_hand.append(self.wonders[choice])
        self.wonders_selectable[choice] = False

    def display_wonders(self):
        if self.display:
            shift = 0 if any(self.wonders_selectable[:4]) else 4
            selectable_wonders = '['
            for i, wonder in enumerate(self.wonders[0+shift:4+shift]):
                if self.wonders_selectable[i + shift]:
                    selectable_wonders += '#' + str(i) + ' ' + str(wonder)
                selectable_wonders += ', '
            selectable_wonders = selectable_wonders[:-2]
            selectable_wonders += ']'
            print("Wonders available: ", selectable_wonders)

    def show_wonders(self):
        shift = 0 if any(self.wonders_selectable[:4]) else 4
        image = ImageDisplay(220, 350)
        p1_wonders, p2_wonders = self.players[0].wonders_in_hand, self.players[1].wonders_in_hand
        image.display_wonder(self.wonders[0+shift:4+shift], self.wonders_selectable, shift, p1_wonders, p2_wonders)

    def valid_moves(self):
        player = self.state_variables.turn_player
        opponent = player ^ 1
        if self.mode == 'wonders':
            shift = 0 if any(self.wonders_selectable[:4]) else 4
            valid_moves = ['w' + str(i) for i in range(len(self.wonders[0+shift:4+shift])) if self.wonders_selectable[0+shift:4+shift][i]]
        elif self.mode == 'main':
            valid_moves = self.valid_moves_main()
        elif self.mode == 'token':
            valid_moves = ['c' + str(i) for i in range(len(self.progress_board.tokens)) if self.progress_board.tokens[i].token_in_slot]
        elif self.mode == 'law':
            valid_moves = ['r' + str(i) for i in range(len(self.players[player].science))]
            valid_moves.append('q')
        elif self.mode in ['Circus Maximus', 'The Statue of Zeus']:
            color = 'Grey' if self.mode == 'Circus Maximus' else 'Brown'
            opponent_cards = [card for card in self.players[opponent].cards_in_play if card.card_type == color]
            valid_moves = ['d' + str(i) for i in range(len(opponent_cards))]
        elif self.mode == 'The Mausoleum':
            valid_moves = ['c' + str(i) for i in range(len(self.state_variables.discarded_cards))]
        elif self.mode == 'The Great Library':
            valid_moves = ['c' + str(i) for i in range(len(self.progress_board.discarded_tokens))]
        return valid_moves

    def valid_moves_main(self):
        '''Returns list of valid moves for given board state and player states'''
        self.update_constructable()
        player = self.state_variables.turn_player
        opponent = player ^ 1
        cards = self.age_boards[self.state_variables.current_age].card_positions
        selectable = [cardslot.card_board_position for cardslot in cards if cardslot.card_selectable == 1 and cardslot.card_in_slot is not None]
        valid_moves = []
        for i in selectable:
            if self.card_constructable(self.players[player], self.players[opponent], cards[i].card_in_slot, True):
                valid_moves.append('c'+str(i))
        wonder_played = [wonder.wonder_in_play for wonder in self.players[player].wonders_in_hand]
        for i in range(len(wonder_played)):
            if not wonder_played[i]:
                if self.wonder_constructable(self.players[player], self.players[opponent], i, True):
                    valid_moves += ['w' + str(j) + ' ' + str(i) for j in selectable]
        if self.state_variables.turn_choice:
            valid_moves.append('turn')
        if self.players[player].law:
            valid_moves += ['r' + str(i) for i in range(len(self.players[player].science))]
        valid_moves += ['d' + str(i) for i in selectable]
        return valid_moves

    def update_mask(self):
        action_masks = np.zeros((len(self.all_actions),), dtype=int)
        valid_moves = self.valid_moves()
        for move in valid_moves:
            actionName = self.convertActionName(move)
            index = self.all_actions.index(actionName)
            action_masks[index] = 1
        return action_masks

    def valid_action_mask(self):
        self.masks = self.update_mask()
        return self.masks

    def enumerate_all_actions(self):
        # 1065 different actions or 201 when choosing random card when constructing wonder
        # (could also include discarded card type to choose) -> 273 actions
        all_actions = []
        cards = list(self.csv_dict['card_list'][:, 0])
        card_types = list(self.csv_dict['card_list'][:,2])
        unique_types = list(set(card_types))
        wonders = list(self.csv_dict['wonder_list'][:, 0])
        tokens = list(self.csv_dict['token_list'][:, 0])
        all_actions += ['choose ' + wonder for wonder in wonders]
        all_actions += ['construct ' + card for card in cards]
        all_actions += ['discard ' + card for card in cards]
        all_actions += ['construct ' + card_type + ' ' + wonder for wonder in wonders for card_type in unique_types]
        # all_actions += ['construct ' + card + '-' + wonder for wonder in wonders for card in cards]
        all_actions += ['construct ' + token for token in tokens]
        all_actions += ['destroy ' + card for i, card in enumerate(cards) if card_types[i] in ['Brown', 'Grey']]
        all_actions += ['r' + str(i) for i in range(6)]
        all_actions.append('q')
        all_actions.append('turn')
        return all_actions

    def convertActionName(self, action):
        player = self.state_variables.turn_player
        age_board = self.age_boards[self.state_variables.current_age].card_positions
        if self.mode == 'wonders':
            shift = 0 if any(self.wonders_selectable[:4]) else 4
            actionName = 'choose ' + self.wonders[0+shift:4+shift][int(action[1])].wonder_name
        elif self.mode == 'main':
            if action[0] == 'c': actionName = 'construct ' + age_board[int(action[1:])].card_in_slot.card_name
            elif action[0] == 'd': actionName = 'discard ' + age_board[int(action[1:])].card_in_slot.card_name
            elif action[0] == 'w':
                card_type = age_board[int(action.split()[0][1:])].card_in_slot.card_type
                # card_name = age_board[int(action.split()[0][1:])].card_in_slot.card_name
                actionName = 'construct ' + card_type + ' ' + self.players[player].wonders_in_hand[int(action[-1])].wonder_name
                # actionName = 'construct ' + card_name + '-' + self.players[player].wonders_in_hand[int(action[-1])].wonder_name
            else: actionName = action
        elif self.mode == 'token':
            actionName = 'construct ' + self.progress_board.tokens[int(action[1])].token_name
        elif self.mode in ['Circus Maximus', 'The Statue of Zeus']:
            color = 'Grey' if self.mode == 'Circus Maximus' else 'Brown'
            opponent_cards = [card.card_name for card in self.players[player^1].cards_in_play if card.card_type == color]
            actionName = 'destroy ' + opponent_cards[int(action[1:])]
        elif self.mode == 'The Mausoleum':
            actionName = 'construct ' + self.state_variables.discarded_cards[int(action[1:])].card_name
        elif self.mode == 'The Great Library':
            actionName = 'construct ' + self.progress_board.discarded_tokens[int(action[1])].token_name
        else:
            actionName = action
        return actionName

    def convertNameAction(self, actionName):
        first_part = actionName.split()[0]
        player = self.state_variables.turn_player
        age_board = self.age_boards[self.state_variables.current_age].card_positions
        cards = [cardSlot.card_in_slot.card_name if cardSlot.card_in_slot is not None else 'None' for cardSlot in age_board]
        if first_part == 'choose':
            shift = 0 if any(self.wonders_selectable[:4]) else 4
            wonders = [wonder.wonder_name for wonder in self.wonders[0 + shift:4 + shift]]
            action = 'w' + str(wonders.index(actionName.split('choose ')[1]))
        elif first_part == 'construct':
            second_part = actionName.split('construct ')[1]
            if self.mode == 'main':
                colors = ['Brown', 'Grey', 'Red', 'Blue', 'Green', 'Purple', 'Yellow']
                if not second_part.split()[0] in colors:
                # if not '-' in second_part:
                    action = 'c' + str(cards.index(second_part))
                else:
                    color = colors[colors.index(second_part.split()[0])]
                    wonders_in_hand = [wonder.wonder_name for wonder in self.players[player].wonders_in_hand]
                    card_types = [cardSlot.card_in_slot.card_type if cardSlot.card_selectable == 1 and cardSlot.card_in_slot is not None else 'None' for cardSlot in age_board]
                    # card_names = [cardSlot.card_in_slot.card_name for cardSlot in age_board if cardSlot.card_selectable == 1 and cardSlot.card_in_slot is not None]
                    action = 'w' + str(card_types.index(color)) + ' ' + str(wonders_in_hand.index(second_part.split(color + ' ')[1]))
                    # action = 'w' + str(card_names.index(second_part.split('-')[0])) + ' ' + str(wonders_in_hand.index(second_part.split('-')[1]))
            elif self.mode == 'token':
                tokens = [token.token_name for token in self.progress_board.tokens]
                action = 'c' + str(tokens.index(second_part))
            elif self.mode == 'The Mausoleum':
                discarded_cards = [card.card_name for card in self.state_variables.discarded_cards]
                action = 'c' + str(discarded_cards.index(second_part))
            elif self.mode == 'The Great Library':
                discarded_tokens = [token.token_name for token in self.progress_board.discarded_tokens]
                action = 'c' + str(discarded_tokens.index(second_part))
        elif first_part == 'discard':
            action = 'd' + str(cards.index(actionName.split('discard ')[1]))
        elif first_part == 'destroy':
            color = 'Grey' if self.mode == 'Circus Maximus' else 'Brown'
            opponent_cards = [card.card_name for card in self.players[player ^ 1].cards_in_play if card.card_type == color]
            action = 'd' + str(opponent_cards.index(actionName.split('destroy ')[1]))
        else:
            action = actionName
        return action

    def is_done(self):
        if self.display:
            print(self.outcome)
        self.done = True

    def select_action(self, choice):
        """Function to begin requesting player input"""
        player = self.state_variables.turn_player
        action, position, position_wonder = choice[0], choice[1:], "0"

        # If the player owns the law token, allow redeeming it in exchange for a scientific symbol
        if self.players[player].law and action == 'r':
            self.token_law(player, position)
            # Check for scientific victory
            if all([symbol >= 1 for symbol in self.players[player].science]):
                self.outcome = 'Player ' + str(player + 1) + ' has won the Game through Scientific Victory!'
                self.is_done()
                return self.outcome
            return

        if choice == 'turn' and self.state_variables.turn_choice:
            self.state_variables.turn_choice = False
            self.state_variables.change_turn_player()
            return

        if action == 'q':
            self.outcome = "Game has been quit"
            self.is_done()
            return self.outcome

        if choice == 'clear': # has been implemented for debugging
            age = self.state_variables.current_age
            slots_in_age = self.age_boards[age].card_positions
            for slot in range(len(slots_in_age)):
                slots_in_age[slot].card_in_slot = None
            self.state_variables.progress_age()
            self.display_game_state()
            return

        if action == 's': #Display a visual representation of the game
            self.show_board()
            return

        if action == 'w':
            position_wonder = position.split(" ")[1]
            position = position.split(" ")[0]

        self.select_card(int(position), action, int(position_wonder))

    # Main gameplay loop - players alternate choosing cards from the board and performing actions with them.
    def select_card(self, position, action='c', position_wonder=0):
        '''Function to select card on board and perform the appropriate action'''
        self.update_constructable()
        # Turn player variables
        player = self.state_variables.turn_player
        player_state = self.players[player]
        player_board = player_state.cards_in_play

        # Opponent player variables
        opponent = player ^ 1  # XOR operator (changes 1 to 0 and 0 to 1)
        opponent_state = self.players[opponent]
        opponent_board = opponent_state.cards_in_play

        # Current age variables
        age = self.state_variables.current_age
        slots_in_age = self.age_boards[age].card_positions

        chosen_position = slots_in_age[position]

        # Discard or construct chosen card and remove card from board
        if action == 'c':
            # Add card to board.
            if self.card_constructable(player_state, opponent_state, chosen_position.card_in_slot, False) is True:
                player_state.construct_card(chosen_position.card_in_slot, player_board, opponent_board, False)
        elif action == 'd':
            # Gain coins based on yellow building owned.
            yellow_card_count = len([card for card in player_board if card.card_type == 'Yellow'])
            player_state.coins += 2 + yellow_card_count
            self.state_variables.discarded_cards.append(chosen_position.card_in_slot)
        elif action == 'w':
            if self.wonder_constructable(player_state, opponent_state, position_wonder, False):
                player_state.construct_wonder(position_wonder, opponent_state, player, self.state_variables.discarded_cards,
                                              player_board, opponent_board, self.display)
                if player_state.law:
                    self.mode = 'law'
                elif any(player_state.wonder_effects.values()):
                    index = list(player_state.wonder_effects.values()).index(True)
                    self.mode = list(player_state.wonder_effects.keys())[index]
                if len(self.players[0].wonders_in_play + self.players[1].wonders_in_play) == 7:
                    for i in range(len(self.players[0].wonders_in_hand)):
                        player_state.wonders_in_hand[i].wonder_in_play = True
                        opponent_state.wonders_in_hand[i].wonder_in_play = True
                    if self.display: print("\nOnly 7 wonders can be constructed. The 8th wonder is discarded.\n")

        self.state_variables.turn_choice = False
        chosen_position.card_in_slot = None
        player_state.update()

        # Update military conflict and check for military victory
        self.state_variables.update_military_track(self.players[0].military_points, self.players[1].military_points)
        if self.state_variables.military_track >= 9:
            self.display_game_state()
            self.outcome = 'Player 1 has won the Game through Military Supremacy!'
            self.is_done()
            return self.outcome
        elif self.state_variables.military_track <= -9:
            self.display_game_state()
            self.outcome = 'Player 2 has won the Game through Military Supremacy!'
            self.is_done()
            return self.outcome

        # Award victory points based on conflict pawn location
        self.update_conflict_points()

        # Grant military tokens
        self.grant_military_token()

        # If 2 matching scientific symbols are collected, allow progress token selection
        self.check_progress_tokens(player)
        if self.mode == 'token' or self.mode == 'law' or any(player_state.wonder_effects.values()):
            self.perform_check = True
            return

        self.perform_checks()
        return

    def perform_checks(self):
        player = self.state_variables.turn_player
        age = self.state_variables.current_age
        slots_in_age = self.age_boards[age].card_positions

        # Check for scientific victory
        if all([symbol >= 1 for symbol in self.players[player].science]):
            self.display_game_state()
            self.outcome = 'Player ' + str(player + 1) + ' has won the Game through Scientific Victory!'
            self.is_done()
            return self.outcome

        # Award victory points based on purple cards
        if self.state_variables.current_age == 2: #only check in Age 3 to reduce computations
            card_effects = [card.card_effect_passive for card in self.players[0].cards_in_play if card.card_type == 'Purple']
            if len(card_effects) > 0:
                self.update_guild_points(card_effects, 0)
            card_effects = [card.card_effect_passive for card in self.players[1].cards_in_play if card.card_type == 'Purple']
            if len(card_effects) > 0:
                self.update_guild_points(card_effects, 1)

        # Check for end of age (all cards drafted)
        if all(slots_in_age[slot].card_in_slot is None for slot in range(len(slots_in_age))):
            self.players[player].replay = False
            self.state_variables.progress_age()
        else:  # Otherwise, update all cards in current age and change turn turn_player
            self.age_boards[age].update_all()
            if not self.players[player].replay:
                self.state_variables.change_turn_player()
            else:
                self.players[player].replay = False
                if self.display: print("\nPlayer " + str(player +1) + " has the Replay effect active and is allowed to play again.\n")

        if self.state_variables.game_end:
            # Civilian victory: 1 victory point for every 3 coins
            self.players[0].victory_points += self.players[0].coins // 3
            self.players[1].victory_points += self.players[1].coins // 3
            self.display_game_state()

            # Handle Civilian Victory
            if self.display:
                print('Victory Points Player 1: ', self.players[0].victory_points)
                print('Victory Points Player 2: ', self.players[1].victory_points)
            if self.players[0].victory_points > self.players[1].victory_points:
                self.outcome = 'Player 1 has won the Game through Civilian Victory!'
            elif self.players[0].victory_points < self.players[1].victory_points:
                self.outcome = 'Player 2 has won the Game through Civilian Victory!'
            else:
                p1_blue_vp = sum([int(card.card_effect_passive[0]) for card in self.players[0].cards_in_play if card.card_type == 'Blue'])
                p2_blue_vp = sum([int(card.card_effect_passive[0]) for card in self.players[1].cards_in_play if card.card_type == 'Blue'])
                if self.display:
                    print('Both players have the same number of victory points.')
                    print('Victory Points Civilian Buildings Player 1: ', p1_blue_vp)
                    print('Victory Points Civilian Buildings Player 2: ', p2_blue_vp)
                if p1_blue_vp > p2_blue_vp:
                    self.outcome = 'Player 1 has won the Game with the most victory points from Civilian Buildings!'
                elif p1_blue_vp < p2_blue_vp:
                    self.outcome = 'Player 2 has won the Game with the most victory points from Civilian Buildings!'
                else:
                    self.outcome = 'Both players have the same number of victory points from Civilian Buildings. The game ends in a draw!'
            self.is_done()
            return self.outcome
        self.display_game_state()

    # Takes 2 Player objects and 1 Card object and checks whether card is constructable given state and cost.
    def card_constructable(self, player, opponent, card, check):
        '''Checks whether a card is constructable given current player states'''
        symbol_counts = Counter(list(card.card_cost))
        cost, counts = list(symbol_counts.keys()), list(symbol_counts.values())
        trade_cost, coins_needed, constructable, net_cost = 0, 0, True, ''

        if card.card_prerequisite in self.constructable_dict['cards']: #free construction condition
            if 'Urbanism' in self.constructable_dict['owned_tokens'] and not check:
                player.coins += 4
            return constructable
        # check if player has insufficient resources to construct the card
        for i, j in zip(['C', 'W', 'S', 'P', 'G'], [player.clay, player.wood, player.stone, player.paper, player.glass]):
            if i in card.card_cost:
                resources_needed = counts[cost.index(i)]
                if resources_needed > j:
                    constructable = False
                    net_cost += i*(resources_needed - j)
        net_cost = self.variable_production(net_cost, self.constructable_dict['cards'], opponent, self.constructable_dict['wonders']) #Handle variable production
        if card.card_type == 'Blue' and 'Masonry' in self.constructable_dict['owned_tokens']:
            net_cost = self.token_masonry_architecture(net_cost, self.constructable_dict['cards'], opponent)
        for i in list(net_cost): # calculates cost to trade for the resource
            trade_cost += self.calculate_rate(i, self.constructable_dict['cards'], opponent)
        if '$' in card.card_cost: #check if player has enough coins to construct the card
            coins_needed = counts[cost.index('$')]
            if coins_needed > player.coins:
                constructable = False
        if player.coins >= trade_cost + coins_needed: #trade for necessary resources to construct the card
            constructable = True
            if not check:
                player.coins -= trade_cost
                if 'Economy' in self.constructable_dict['opponent_tokens']:
                    self.players[self.state_variables.turn_player ^ 1].coins += trade_cost
        return constructable #False if cost or materials > players coins or materials

    # Checks whether the wonder is constructable given state and cost.
    def wonder_constructable(self, player, opponent, position_wonder, check):
        wonder = player.wonders_in_hand[position_wonder]
        symbol_counts = Counter(list(wonder.wonder_cost))
        cost, counts = list(symbol_counts.keys()), list(symbol_counts.values())
        trade_cost, constructable, net_cost = 0, True, ''

        # check if player has insufficient resources to construct the wonder
        for i, j in zip(['C', 'W', 'S', 'P', 'G'],[player.clay, player.wood, player.stone, player.paper, player.glass]):
            if i in wonder.wonder_cost:
                resources_needed = counts[cost.index(i)]
                if resources_needed > j:
                    constructable = False
                    net_cost += i * (resources_needed - j)
        net_cost = self.variable_production(net_cost, self.constructable_dict['cards'], opponent, self.constructable_dict['wonders'])  # Handle variable production
        if 'Architecture' in self.constructable_dict['owned_tokens']:
            net_cost = self.token_masonry_architecture(net_cost, self.constructable_dict['cards'], opponent)
        for i in list(net_cost): # calculates cost to trade for the resource
            trade_cost += self.calculate_rate(i, self.constructable_dict['cards'], opponent)
        if player.coins >= trade_cost: #trade for necessary resources to construct the card
            constructable = True
            if not check:
                player.coins -= trade_cost
                if 'Economy' in self.constructable_dict['opponent_tokens']:
                    self.players[self.state_variables.turn_player ^ 1].coins += trade_cost
        return constructable

    # Chooses the resource with the highest trading cost and uses variable production for it, if available
    def variable_production(self, net_cost, cards, opponent, wonders):
        if 'Forum' in cards:
            net_cost = self.variable_production_PG(net_cost, cards, opponent)
        if 'Caravansery' in cards:
            net_cost = self.variable_production_WCS(net_cost, cards, opponent)
        if 'Piraeus' in wonders:
            net_cost = self.variable_production_PG(net_cost, cards, opponent)
        if 'The Great Lighthouse' in wonders:
            net_cost = self.variable_production_WCS(net_cost, cards, opponent)
        return net_cost

    def variable_production_PG(self, net_cost, cards, opponent):
        if 'P' in net_cost and 'G' in net_cost:
            p_rate = self.calculate_rate('P', cards, opponent)
            g_rate = self.calculate_rate('G', cards, opponent)
            if p_rate > g_rate:
                net_cost = net_cost.replace('P', '', 1)
            else:
                net_cost = net_cost.replace('G', '', 1)
        elif 'P' in net_cost:
            net_cost = net_cost.replace('P', '', 1)
        elif 'G' in net_cost:
            net_cost = net_cost.replace('G', '', 1)
        return net_cost

    def variable_production_WCS(self, net_cost, cards, opponent):
        w_rate = self.calculate_rate('W', cards, opponent)
        c_rate = self.calculate_rate('C', cards, opponent)
        s_rate = self.calculate_rate('S', cards, opponent)
        if 'W' in net_cost:
            if 'C' in net_cost and 'S' in net_cost:
                if w_rate >= c_rate and w_rate >= s_rate:
                    net_cost = net_cost.replace('W', '', 1)
                elif c_rate >= s_rate:
                    net_cost = net_cost.replace('C', '', 1)
                else:
                    net_cost = net_cost.replace('S', '', 1)
            elif 'C' in net_cost:
                if w_rate >= c_rate:
                    net_cost = net_cost.replace('W', '', 1)
                else:
                    net_cost = net_cost.replace('C', '', 1)
            elif 'S' in net_cost:
                if w_rate >= s_rate:
                    net_cost = net_cost.replace('W', '', 1)
                else:
                    net_cost = net_cost.replace('S', '', 1)
            else:
                net_cost = net_cost.replace('W', '', 1)
        elif 'C' in net_cost:
            if 'S' in net_cost:
                if c_rate >= s_rate:
                    net_cost = net_cost.replace('C', '', 1)
                else:
                    net_cost = net_cost.replace('S', '', 1)
            else:
                net_cost = net_cost.replace('C', '', 1)
        elif 'S' in net_cost:
            net_cost = net_cost.replace('S', '', 1)
        return net_cost


    # If the token Masonry/Architecture is in posession, blue cards/wonders will cost 2 fewer resources
    def token_masonry_architecture(self, net_cost, cards, opponent):
        if len(net_cost) <= 2:
            net_cost = ''
        else:
            rates = np.zeros(len(net_cost), dtype=int)
            for i in range(len(net_cost)):
                rates[i] = self.calculate_rate(net_cost[i], cards, opponent)
            net_cost = list(net_cost)
            for i in np.sort(np.argsort(rates)[-2:])[::-1]:
                del net_cost[i]
            net_cost = ''.join(net_cost)
        return net_cost

    # If the token Law is in posession, allow redeeming it for a scientific symbol
    def token_law(self, player, position):
        self.players[player].science[int(position)] += 1
        self.players[player].law = False
        if self.display: print("Token has been redeemed!")
        self.check_progress_tokens(player)
        self.display_game_state()

    # If 2 matching scientific symbols are collected, allow progress token selection
    def check_progress_tokens(self, player):
        tokens_awarded = self.state_variables.progress_tokens_awarded
        match_science = [True if self.players[player].science[i] >= 2 and not tokens_awarded[i] else False for i in
                         range(len(self.players[player].science))]
        if any(match_science) and any([token.token_in_slot for token in self.progress_board.tokens]):
            self.state_variables.progress_tokens_awarded[match_science.index(True)] = True
            self.mode = 'token'

    # Requests player input to select one of the tokens still available where token_in_slot == True
    def select_token(self, choice):
        player = self.state_variables.turn_player
        if self.display: print("Player " + str(player + 1) + " gathered 2 matching scientific symbols.")
        action, position = choice[0], choice[1:]
        if action == 's': #Display a visual representation of the game
            return self.show_board()
        elif action == 'c':
            self.mode = 'main'
            self.players[player].construct_token(self.progress_board.tokens[int(position)], self.display)
            self.progress_board.tokens[int(position)].token_in_slot = False
        if self.players[player].law:
            self.mode = 'law'

    # Calculates the rate at which a resource can be bought
    def calculate_rate(self, resource, cards, opponent):
        resource_counts = [opponent.clay, opponent.wood, opponent.stone, opponent.paper, opponent.glass]
        rate = 2 + resource_counts[['C', 'W', 'S', 'P', 'G'].index(resource)]
        #handle yellow cards fixing trading rates
        for name, res in zip(['Stone Reserve', 'Clay Reserve', 'Wood Reserve'], ['S', 'C', 'W']):
            if name in cards and resource == res:
                rate = 1
        if 'Customs House' in cards and resource in ['P', 'G']:
            rate = 1
        return rate

    def show_board(self):
        age = self.state_variables.current_age
        slots_in_age = self.age_boards[age].card_positions
        image_dict, selectable_dict = {}, {}
        row_list, counts = np.unique([int(slot.row) for slot in slots_in_age], return_counts=True)
        max_row = row_list[np.argmax(counts)] # get the row with max card number
        for i in row_list: # create an empty dict with the number of rows
            image_dict[i] = []
            selectable_dict[i] = []
        for j in range(len(slots_in_age)): # assign path if card is visible and 1 if selectable
            if slots_in_age[j].card_in_slot is not None:
                if slots_in_age[j].card_visible == 1:  # if the card is visible
                    path = slots_in_age[j].card_in_slot.card_name.replace(" ", "").lower()
                    selectable = 1 if slots_in_age[j].card_selectable == 1 else 0
                else:  # if the card is hidden
                    path = 'age' + str(age + 1) + 'back'
                    selectable = 0
            else:  # fill empty slots with black
                path = 'black'
                selectable = 2
            row = int(slots_in_age[j].row)
            image_dict[row].append(path)  # fill the dictionary with each path per row
            selectable_dict[row].append(selectable)
        if age == 2: #Change middle row display of Age 3
            image_dict[3].insert(1, 'black')
            selectable_dict[3].insert(1, 0)
        image_dict[-1] = [card.card_name.replace(" ", "").lower() for card in self.players[0].cards_in_play]
        selectable_dict[-1] = [card.card_type for card in self.players[0].cards_in_play]
        image_dict[-2] = [card.card_name.replace(" ", "").lower() for card in self.players[1].cards_in_play]
        selectable_dict[-2] = [card.card_type for card in self.players[1].cards_in_play]
        image = ImageDisplay(220, 350)
        age, military = self.state_variables.current_age, self.state_variables.military_track
        m_tokens, p_tokens = self.state_variables.military_tokens, self.progress_board.tokens
        coins = {-1: self.players[0].coins, -2: self.players[1].coins}
        p_tokens_in_play = {-1: self.players[0].progress_tokens_in_play, -2: self.players[1].progress_tokens_in_play}
        wonders = {-1:[self.players[0].wonders_in_hand, self.players[0].wonders_in_play], -2:[self.players[1].wonders_in_hand, self.players[1].wonders_in_play]}
        image.display_board(image_dict, selectable_dict, max_row, age, military, m_tokens, coins, p_tokens, p_tokens_in_play, wonders)

    # Displays the game state in a nice enough way.
    def display_game_state(self):
        '''Print a visual representation of the current game state'''
        if self.display:
            player = self.state_variables.turn_player
            age = self.state_variables.current_age

            print("Progress Tokens :", self.progress_board)
            print("Military Track : " + self.display_military_board())
            self.age_boards[age].display_board()
            print("Player 1 >", self.players[0])
            print("Player 2 >", self.players[1])
            print("")
            print("Current turn player is Player ", str(player + 1))

    # Displays the military conflict in the command line
    def display_military_board(self):
        military = self.state_variables.military_track
        board = (max(0, min(18, military+9)))*'0' + '1' + (max(0, min(18, 9-military)))*'0'
        board = '[' + board[0] + '|' + board[1:4] + '|' + board[4:7] + '|' + board[7:9] + '|' + board[9] + '|' + \
            board[10:12] + '|' + board[12:15] + '|' + board[15:18] + '|' + board[18] + ']'
        return board

    # Grants victory points based on conflict pawn location
    def update_conflict_points(self):
        military = self.state_variables.military_track
        # keep track of old victory points (points_awarded)
        points_awarded = self.state_variables.victory_points_awarded
        # calculate new victory points (points)
        if abs(military) in [0]: points = 0
        elif abs(military) in [1, 2]: points = 2
        elif abs(military) in [3, 4, 5]: points = 5
        elif abs(military) >= 6: points = 10

        if military >= 0:
            if points_awarded >= 0:
                points_change = points - points_awarded
                self.players[0].victory_points += points_change
                #player 2 points unaffected
            else: #points_awarded < 0
                self.players[0].victory_points += points
                self.players[1].victory_points += points_awarded #points_awarded<0
        else: #military < 0
            if points_awarded > 0:
                self.players[0].victory_points -= points_awarded
                self.players[1].victory_points += points
            else: #points_awarded <= 0
                points_change = points - abs(points_awarded)
                #player 1 points unaffected
                self.players[1].victory_points += points_change
        if military < 0:
            points = points * (-1)
        self.state_variables.victory_points_awarded = points

    # Grants military tokens based on military track (opposing player loses coins)
    def grant_military_token(self):
        tokens = self.state_variables.military_tokens
        military_track = self.state_variables.military_track
        if tokens[0] == 0 and military_track <= -6:
            self.players[0].coins = max(0, self.players[0].coins - 5)
            self.state_variables.military_tokens[0] = 1
        elif tokens[1] == 0 and military_track <= -3:
            self.players[0].coins = max(0, self.players[0].coins - 2)
            self.state_variables.military_tokens[1] = 1
        elif tokens[2] == 0 and military_track >= 3:
            self.players[1].coins = max(0, self.players[1].coins - 2)
            self.state_variables.military_tokens[2] = 1
        elif tokens[3] == 0 and military_track >= 6:
            self.players[1].coins = max(0, self.players[1].coins - 5)
            self.state_variables.military_tokens[3] = 1

    # Grants victory points based on purple (guild) cards
    def update_guild_points(self, card_effects, player):
        cards_player_1 = self.players[0].cards_in_play
        cards_player_2 = self.players[1].cards_in_play
        colors = ['Yellow', 'Blue', 'Green', 'Red']
        card_counts = self.state_variables.max_card_counts.copy()
        for effect in card_effects:
            color = effect.split()[2]
            if 'Grey' in effect.split() and 'Brown' in effect.split():
                type_count = len([1 for card in cards_player_1 if card.card_type in ['Grey', 'Brown']])
                type_count = max(type_count, len([1 for card in cards_player_2 if card.card_type in ['Grey', 'Brown']]))
                self.state_variables.max_card_counts[0] = type_count
                type_count -= card_counts[0]
            elif 'Wonder' in effect.split():
                type_count = len(self.players[0].wonders_in_play)
                type_count = max(type_count, len(self.players[1].wonders_in_play))
                type_count *= 2 #wonders are worth 2 victory points instead of 1
                self.state_variables.max_card_counts[1] = type_count
                type_count -= card_counts[1]
            elif '$$$' in effect.split():
                type_count = self.players[0].coins // 3
                type_count = max(type_count, self.players[1].coins // 3)
                self.state_variables.max_card_counts[2] = type_count
                type_count -= card_counts[2]
            else: #handle 'Yellow', 'Blue', 'Green', 'Red'
                type_count = len([1 for card in cards_player_1 if card.card_type == color])
                type_count = max(type_count, len([1 for card in cards_player_2 if card.card_type == color]))
                self.state_variables.max_card_counts[colors.index(color)+3] = type_count
                type_count -= card_counts[colors.index(color)+3]
            self.players[player].victory_points += type_count

class Wonder:
    '''Define a single wonder.'''

    def __init__(self, wonder_name, wonder_cost, wonder_effect_passive, wonder_effect_when_played, wonder_in_play):
        self.wonder_name = wonder_name
        self.wonder_cost = wonder_cost
        self.wonder_effect_passive = wonder_effect_passive
        self.wonder_effect_when_played = wonder_effect_when_played
        self.wonder_in_play = wonder_in_play

    def __repr__(self):
        return str(bg(249, 242, 73) + fg.black
                   + self.wonder_name
                   + rs.all)

    def __deepcopy__(self, memo):
        if self in memo: #check if already copied
            return memo[self]
        memo[self] = Wonder(wonder_name = self.wonder_name,
                            wonder_cost = self.wonder_cost,
                            wonder_effect_passive = self.wonder_effect_passive,
                            wonder_effect_when_played = self.wonder_effect_when_played,
                            wonder_in_play = self.wonder_in_play)
        return memo[self]

class Card:
    '''Define a single card. Attributes match the .csv headers'''
    colour_key = {
        "Brown": bg(100, 50, 0) + fg.white,
        "Grey": bg.grey + fg.black,
        "Red": bg.red + fg.white,
        "Green": bg(0, 128, 0) + fg.white,
        "Yellow": bg.yellow + fg.black,
        "Blue": bg.blue + fg.white,
        "Purple": bg(128, 0, 128) + fg.white,
    }

    def __init__(self, card_name=0, card_set=0, card_type=0, card_cost=0, card_age=0, card_effect_passive=0,
                 card_effect_when_played=0, card_prerequisite=0):
        self.card_name = card_name
        self.card_set = card_set
        self.card_type = card_type
        self.card_cost = card_cost
        self.card_effect_passive = card_effect_passive
        self.card_effect_when_played = card_effect_when_played
        self.card_age = card_age
        self.card_prerequisite = card_prerequisite

    def __repr__(self):
        return str(self.colour_key[self.card_type]
                   + self.card_name
                   + rs.all)

    def __deepcopy__(self, memo):
        if self in memo: #check if already copied
            return memo[self]
        memo[self] = Card(card_name = self.card_name,
                          card_set = self.card_set,
                          card_type = self.card_type,
                          card_cost = self.card_cost,
                          card_effect_passive = self.card_effect_passive,
                          card_effect_when_played = self.card_effect_when_played,
                          card_age = self.card_age,
                          card_prerequisite = self.card_prerequisite)
        return memo[self]

class CardSlot:
    '''Define a card slot on board to represent selectability, visibility, etc.'''

    def __init__(self, card_in_slot=None, card_board_position=None, game_age=None,
                 card_visible=1, card_selectable=0, covered_by=None, row=None):
        self.card_board_position = int(card_board_position)
        self.game_age = int(game_age)
        self.card_in_slot = card_in_slot
        self.card_visible = int(card_visible)
        self.card_selectable = int(card_selectable)
        if covered_by:
        #if isinstance(covered_by, str):
            self.covered_by = [int(card) for card in str(covered_by).split(" ")]
        else:
            self.covered_by = []
        self.row = row

    def __repr__(self):  # How the cards are displayed to the players.
        if self.card_in_slot is None:
            return str("")
        
        if self.card_visible == 0:
            return str("#" + repr(self.card_board_position)
                       + " Hidden " + repr(self.covered_by)
                       )

        return str("#" + repr(self.card_board_position) + " "
                   + repr(self.card_in_slot)
                   )

    def __deepcopy__(self, memo):
        if self in memo: #check if already copied
            return memo[self]
        new_instance = CardSlot(card_in_slot = copy.deepcopy(self.card_in_slot, memo),
                                card_board_position = self.card_board_position,
                                game_age = self.game_age,
                                card_visible = self.card_visible,
                                card_selectable = self.card_selectable,
                                covered_by = None,
                                row = self.row)
        new_instance.covered_by = copy.deepcopy(self.covered_by, memo)

        memo[self] = new_instance
        return new_instance

class ProgressToken:
    '''Define a single progress token'''

    def __init__(self, token_name=0, token_effect_passive=0, token_effect_when_played=0, token_in_slot = False):
        self.token_name = token_name
        self.token_effect_passive = token_effect_passive
        self.token_effect_when_played = token_effect_when_played
        self.token_in_slot = token_in_slot

    def __repr__(self):
        return str(bg(0, 70, 0) + fg.white
                   + self.token_name
                   + rs.all)

    def __deepcopy__(self, memo):
        if self in memo: #check if already copied
            return memo[self]
        memo[self] = ProgressToken(token_name = self.token_name,
                                   token_effect_passive = self.token_effect_passive,
                                   token_effect_when_played = self.token_effect_when_played,
                                   token_in_slot = self.token_in_slot)
        return memo[self]

class ProgressBoard:
    '''Define the progress board in which the progress tokens are slotted into'''

    def __init__(self, csv_dict):
        self.discarded_tokens = []
        self.tokens = self.prepare_progress_board(csv_dict)

    def __repr__(self):
        board = '['
        for token in self.tokens:
            if token.token_in_slot:
                board += '#' + str(self.tokens.index(token)) + ' ' + str(token)
            board += ', '
        board = board[:-2]
        board += ']'
        return board
        # return str([token if token.token_in_slot else '' for token in self.tokens])

    def __deepcopy__(self, memo):
        if self in memo: #check if already copied
            return memo[self]
        new_instance = ProgressBoard({})
        new_instance.tokens = copy.deepcopy(self.tokens, memo)
        new_instance.discarded_tokens = copy.deepcopy(self.discarded_tokens, memo)

        memo[self] = new_instance
        return new_instance

    # read tokens, randomly select 5, and slot them into the board
    def prepare_progress_board(self, csv_dict):
        if not csv_dict: return []
        token_count = 5 + 3
        chosen_tokens = csv_dict['token_list'][np.random.choice(csv_dict['token_list'].shape[0], token_count, replace=False)]
        tokens = []
        for token in chosen_tokens:
            tokens.append(ProgressToken(token[0], token[1], token[2], True))
        self.discarded_tokens = tokens[5:]
        tokens = tokens[:5]
        return tokens

class Player:
    '''Define a class for play to track tableau cards, money, etc.'''

    def __init__(self, player_number=0, player_type='human', agent=None):
        # Private:
        self.player_number = player_number
        self.player_type = player_type
        self.agent = agent

        # Update as card is chosen through Game.construct_card method:
        self.coins = 7
        self.cards_in_play = []
        self.wonders_in_hand = []
        self.wonders_in_play = []
        self.progress_tokens_in_play = []

        # Passive variables can be updated anytime based on cards_in_play via self.update() method.
        self.victory_points = 0
        self.military_points = 0
        self.clay = 0
        self.wood = 0
        self.stone = 0
        self.paper = 0
        self.glass = 0
        self.science = [0,0,0,0,0,0]
        self.law = False
        self.replay = False
        self.wonder_effects = {'Circus Maximus': False, 'The Statue of Zeus': False,
                               'The Mausoleum': False, 'The Great Library': False}

    def __deepcopy__(self, memo):
        if self in memo: #check if already copied
            return memo[self]
        new_instance = Player(player_number = self.player_number,
                              player_type = self.player_type,
                              agent = self.agent)
        new_instance.coins = self.coins
        new_instance.cards_in_play = copy.deepcopy(self.cards_in_play, memo)
        new_instance.wonders_in_hand = copy.deepcopy(self.wonders_in_hand, memo)
        new_instance.wonders_in_play = copy.deepcopy(self.wonders_in_play, memo)
        new_instance.progress_tokens_in_play = copy.deepcopy(self.progress_tokens_in_play, memo)
        new_instance.victory_points = self.victory_points
        new_instance.military_points = self.military_points
        new_instance.clay = self.clay
        new_instance.wood = self.wood
        new_instance.stone = self.stone
        new_instance.paper = self.paper
        new_instance.glass = self.glass
        new_instance.science = self.science[:]
        new_instance.law = self.law
        new_instance.replay = self.replay
        new_instance.wonder_effects = copy.deepcopy(self.wonder_effects, memo={})

        memo[self] = new_instance
        return new_instance

    def __repr__(self):
        in_hand, in_play = '[', '['
        for i in range(len(self.wonders_in_hand)):
            if not self.wonders_in_hand[i].wonder_in_play:
                in_hand += '#' + str(i) + ' ' + str(self.wonders_in_hand[i])
            elif self.wonders_in_hand[i] in self.wonders_in_play:
                in_play += '#' + str(i) + ' ' + str(self.wonders_in_hand[i])
            in_hand += ', '
            in_play += ', '
        in_hand = in_hand[:-2]
        in_play = in_play[:-2]
        in_hand += ']'
        in_play += ']'

        return str(" Coins: " + repr(self.coins)
                   + ", Victory: " + repr(self.victory_points)
                   + ", Military: " + repr(self.military_points)
                   + ", C" + repr(self.clay)
                   + " W" + repr(self.wood)
                   + " S" + repr(self.stone)
                   + " P" + repr(self.paper)
                   + " G" + repr(self.glass)
                   + ", Science: " + repr(self.science[0]) + ' ' + repr(self.science[1]) + ' ' + repr(self.science[2])
                   + ' ' + repr(self.science[3]) + ' ' + repr(self.science[4]) + ' ' + repr(self.science[5])
                   + ",\n Board: " + repr(self.cards_in_play)
                   + ", Tokens: " + repr(self.progress_tokens_in_play)
                   + ",\n Wonders Hand: " + in_hand
                   + ", Wonders Play: " + in_play
                   )

    # removal of card from game board is done elsewhere! (in Game.select_card method).
    def construct_card(self, card, player_board, opponent_board, free):
        '''Function to construct a card in a players tableau'''
        # decrease coins of player by card cost
        symbol_counts = Counter(list(card.card_cost))
        cost, counts = list(symbol_counts.keys()), list(symbol_counts.values())
        cards = [card.card_name for card in player_board]
        if '$' in card.card_cost and card.card_prerequisite not in cards and not free: #free construction condition
            self.coins -= counts[cost.index('$')] # decrease coins by card cost
        owned_tokens = [token.token_name for token in self.progress_tokens_in_play]

        # increase player variables by resource card effect
        if card.card_type == 'Yellow': # handle Yellow cards
            effect = list(card.card_effect_passive)
            if 'V' in effect: # Handle Age 3 Yellow Cards
                self.victory_points += int(effect[0])
                effect_active = card.card_effect_when_played.split(' per ')
                for i in ['Grey', 'Brown', 'Red', 'Yellow']:
                    if i in effect_active:
                        type_count = len([1 for card in player_board if card.card_type == i])
                        if card.card_type == 'Yellow':
                            type_count += 1 #includes itself
                        self.coins += type_count * int(list(effect_active[0])[0])
                if 'Wonder' in effect_active:
                    self.coins += len(self.wonders_in_play) * int(list(effect_active[0])[0])
            elif '$' in card.card_effect_when_played: # Handle coin effect
                effect_active = list(card.card_effect_when_played)
                self.coins += int(effect_active[0])
            # Variable production handled in variable_production function
            # Fixed trading rates handled in calculate_rate function
        elif card.card_type == 'Green': # handle Green cards
            effect = card.card_effect_passive.split('S')
            if 'V' in effect[0]:
                self.victory_points += int(list(effect[0])[0])
            self.science[int(effect[1])-1] += 1
        elif card.card_type == 'Purple': # handle Purple cards
            # 1 coin for each card of type in city with most cards
            if 'Grey' in card.card_effect_when_played.split() and 'Brown' in card.card_effect_when_played.split():
                type_count = len([1 for card in player_board if card.card_type in ['Grey', 'Brown']])
                type_count = max(type_count, len([1 for card in opponent_board if card.card_type in ['Grey', 'Brown']]))
                self.coins += type_count
            for i in ['Yellow', 'Blue', 'Green', 'Red']:
                if i in card.card_effect_when_played.split():
                    type_count = len([1 for card in player_board if card.card_type == i])
                    type_count = max(type_count, len([1 for card in opponent_board if card.card_type == i]))
                    self.coins += type_count
        else: # handle Blue, Brown, Grey, Red cards
            effect = list(card.card_effect_passive)
            resource = ['C', 'W', 'S', 'P', 'G', 'V', 'M']
            resource_names = ['clay', 'wood', 'stone', 'paper', 'glass', 'victory_points', 'military_points']
            if effect[1] in resource: # increase resources of player by card effect
                resource_name = resource_names[resource.index(effect[1])]
                setattr(self, resource_name, getattr(self, resource_name) + int(effect[0]))
            if 'Strategy' in owned_tokens and effect[1] == 'M':
                self.military_points += 1
        self.cards_in_play.append(card)
        return

    # Construct the selected wonder by applying their respective effect
    def construct_wonder(self, position_wonder, opponent, player_turn, discarded_cards, player_board, opponent_board, display):
        wonder = self.wonders_in_hand[position_wonder]
        effect = wonder.wonder_effect_when_played
        effect_passive = wonder.wonder_effect_passive
        if 'Theology' in [token.token_name for token in self.progress_tokens_in_play]:
            self.replay = True

        if 'V' in effect:
            self.victory_points += int(effect[0])
        if '$' in effect:
            if 'V' in effect:
                self.coins += int(effect[2])
            else:
                self.coins += int(effect[:2])
        if 'M' in effect:
            self.military_points += int(effect[2])
        if '-' in effect:
            opponent.coins = max(0, opponent.coins - int(effect[-2]))

        if 'Replay' in effect_passive:
            self.replay = True
        elif 'Grey' in effect_passive or 'Brown' in effect_passive:
            color = 'Grey' if 'Grey' in effect_passive else 'Brown'
            wonder_name = 'Circus Maximus' if 'Grey' in effect_passive else 'The Statue of Zeus'
            opponent_cards = [card for card in opponent.cards_in_play if card.card_type == color]
            if len(opponent_cards) == 1:
                if display: print("\n" + str(opponent_cards[0]) + " of Player " + str(player_turn^1 + 1) + " is discarded.")
                self.discard_card(opponent_cards[0], opponent, discarded_cards)
            elif len(opponent_cards) >= 2:
                self.wonder_effects[wonder_name] = True
        elif wonder.wonder_name == 'The Mausoleum':
            if len(discarded_cards) == 1:
                if display: print("\nDiscarded card " + str(discarded_cards[0]) + " is constructed for free.")
                self.construct_card(discarded_cards[0], player_board, opponent_board, True)
                discarded_cards.remove(discarded_cards[0])
            elif len(discarded_cards) >= 2:
                self.wonder_effects['The Mausoleum'] = True
        elif wonder.wonder_name == 'The Great Library':
            self.wonder_effects['The Great Library'] = True

        wonder.wonder_in_play = True
        self.wonders_in_hand[position_wonder].wonder_in_play = True
        self.wonders_in_play.append(wonder)
        return

    # Enables the player to discard one card from his opponent in the specified color
    def wonder_destory_card(self, choice, opponent, color, player_turn, discarded_cards, name, display):
        opponent_cards = [card for card in opponent.cards_in_play if card.card_type == color]
        opponent_turn = player_turn ^ 1
        cards = self.print_string(opponent_cards)
        if display: print('\n' + color + " cards of Player " + str(opponent_turn + 1) + ": " + cards)
        action, position = choice[0], choice[1:]
        if action == 's':
            return self.wonder_show_effect('Card', opponent_cards)
        card = opponent_cards[int(position)]
        self.discard_card(card, opponent, discarded_cards)
        self.wonder_effects[name] = False

    # Sub-function which actually removes the card from the board and reduces resources
    def discard_card(self, card, opponent, discarded_cards):
        opponent.cards_in_play.remove(card)
        resource = ['C', 'W', 'S', 'P', 'G']
        resource_names = ['clay', 'wood', 'stone', 'paper', 'glass']
        if card.card_effect_passive[1] in resource:
            resource_name = resource_names[resource.index(card.card_effect_passive[1])]
            setattr(opponent, resource_name, getattr(opponent, resource_name) - int(card.card_effect_passive[0]))
        discarded_cards.append(card)

    # Enables the player to pick a discarded card and construct it for free
    def wonder_mausoleum(self, choice, discarded_cards, player_board, opponent_board, display):
        cards = self.print_string(discarded_cards)
        if display: print("\nDiscarded cards since the beginning of the game: " + cards)
        action, position = choice[0], choice[1:]
        if action == 's':
            return self.wonder_show_effect('Card', discarded_cards)
        card = discarded_cards[int(position)]
        self.construct_card(card, player_board, opponent_board, True)
        discarded_cards.remove(card)
        self.wonder_effects['The Mausoleum'] = False

    # Enables the player to pick 1 from 3 discarded Progress Tokens
    def wonder_great_library(self, choice, discarded_tokens, display):
        tokens = self.print_string(discarded_tokens)
        if display: print("\n3 random discarded tokens from the beginning of the game: " + tokens)
        action, position = choice[0], choice[1:]
        if action == 's':
            return self.wonder_show_effect('Token', discarded_tokens)
        token = discarded_tokens[int(position)]
        discarded_tokens.remove(token)
        self.construct_token(token, display)
        self.wonder_effects['The Great Library'] = False

    def wonder_show_effect(self, print_object, card_list):
        width, height = 220, 350
        if print_object == 'Token':
            width, height = 140, 140
        image = ImageDisplay(width, height)
        image.display_cards(card_list, print_object)

    # Creates a string which can be used to print in the command line
    def print_string(self, print_cards):
        cards = '['
        for i in range(len(print_cards)):
            cards += '#' + str(i) + ' ' + str(print_cards[i])
            cards += ', '
        cards = cards[:-2]
        cards += ']'
        return cards

    def update(self):
        '''Updates player passive variables based on players tableau'''
        return

    # construct the selected token by applying their respective effect
    def construct_token(self, token, display):
        effect = token.token_effect_when_played
        name = token.token_name
        owned_tokens = [own_token.token_name for own_token in self.progress_tokens_in_play]
        self.progress_tokens_in_play.append(token)
        if 'Mathematics' in owned_tokens:
            self.victory_points += 3
        if 'V' in effect: # Agriculture & Philosophy token
            self.victory_points += int(effect[0])
        if '$' in effect: # Agriculture & Urbanism token
            self.coins += int(effect[-2])
        elif 'S' in effect: # Law token
            self.law = True
            if display: print("\nPlayer " + str(self.player_number + 1) + " >", self.__repr__())
        elif name == 'Mathematics':
            self.victory_points += 3*len(owned_tokens) + 3

    # If the token Law is in posession, allow redeeming it for a scientific symbol
    def token_law(self, choice, progress_board, display):
        if display: print("Player " + str(self.player_number + 1) +
                          " owns the law progress token and may [r]edeem it once in exchange for any scientific symbol.")
        action, position = choice[0], choice[1:]
        if action == 's':
            tokens = progress_board.tokens.copy()
            token_names = [token.token_name for token in tokens]
            if 'Law' in token_names:
                tokens.remove(tokens[token_names.index('Law')])
            image = ImageDisplay(140, 140)
            image.display_cards(tokens, 'Token')
        elif action == 'r':
            self.science[int(position)] += 1
            self.law = False
            if display: print("Token has been redeemed!")
        else:
            if display: print("Law token was not redeemed.")

class StateVariables:
    '''Class to represent all state variables shared between players (military, turn player, etc.)'''

    def __init__(self, turn_player=None, current_age=0, military_track=0):
        self.rng = default_rng()
        if turn_player is None:
            self.turn_player = self.rng.integers(low=0, high=2)  # Randomly select first player if none specified.
        self.current_age = current_age  # Start in first age.
        self.military_track = military_track  # Start military track at 0.
        self.game_end = False
        self.victory_points_awarded = 0
        self.military_tokens = [0,0,0,0]
        self.turn_choice = False
        self.max_card_counts = [0,0,0,0,0,0,0]
        self.progress_tokens_awarded = [False for i in range(6)]
        self.discarded_cards = []

    def __repr__(self):
        return str(" Age: " + repr(self.current_age)
                   + ", Discarded Cards: " + repr(self.discarded_cards)
                   )

    def __deepcopy__(self, memo):
        if self in memo: #check if already copied
            return memo[self]
        new_instance = StateVariables(turn_player = None,
                                      current_age = self.current_age,
                                      military_track = self.military_track)
        new_instance.turn_player = self.turn_player
        new_instance.rng = self.rng
        new_instance.game_end = self.game_end
        new_instance.victory_points_awarded = self.victory_points_awarded
        new_instance.military_tokens = self.military_tokens[:]
        new_instance.turn_choice = self.turn_choice
        new_instance.max_card_counts = self.max_card_counts[:]
        new_instance.progress_tokens_awarded = self.progress_tokens_awarded[:]
        new_instance.discarded_cards = copy.deepcopy(self.discarded_cards, memo)

        memo[self] = new_instance
        return new_instance

    def change_turn_player(self):
        '''Function to change current turn player'''
        self.turn_player = self.turn_player ^ 1  # XOR operation to change 0 to 1 and 1 to 0

    def progress_age(self):
        '''Function to progress age and end game if required'''
        if self.current_age < 2:
            self.current_age = self.current_age + 1
            if self.military_track > 0 and self.turn_player == 0:
                self.change_turn_player() #if player 1 has stronger military, change to player 2
            elif self.military_track < 0 and self.turn_player == 1:
                self.change_turn_player() #if player 2 has stronger military, change to player 1
            #in case military is balanced, last active player remains
            self.turn_choice = True #Allow the player to choose who begins the next Age
        else:
            self.game_end = True

    def update_military_track(self, military_points_1, military_points_2):
        '''Function to update military track'''
        self.military_track = military_points_1 - military_points_2

class Age:
    '''Class to define a game age and represent the unique board layouts'''

    age_1_card_count = 20
    age_2_card_count = 20
    age_3_card_count = 17
    age_guild_card_count = 3

    def __init__(self, age, csv_dict):
        self.age = age
        self.card_positions = self.prepare_age_board(age, csv_dict)
        self.number_of_rows = int(max(self.card_positions[slot].row for slot in range(len(self.card_positions)))) if self.card_positions else 0

    def __repr__(self):
        return str('Age ' + str(self.age))

    def __deepcopy__(self, memo):
        if self in memo:
            return memo[self]
        new_instance = Age(self.age, None)
        new_instance.number_of_rows = self.number_of_rows
        new_instance.card_positions = copy.deepcopy(self.card_positions, memo)

        memo[self] = new_instance
        return new_instance

    # Init functions:

    def prepare_age_board(self, age, csv_dict):
        '''Takes dataframe of all cards and creates list of card objects representing the board for a given age.'''
        if not csv_dict: return []
        age = str(age)  # Convert to int if required
        age_layout = csv_dict['age_layouts'][np.where(csv_dict['age_layouts'][:,4] == age)]  # Filter for age
        age_cards = csv_dict['card_list'][np.where(csv_dict['card_list'][:,6] == age)]  # Filter for age

        if age == "1":
            age_cards = age_cards[np.random.choice(age_cards.shape[0], self.age_1_card_count, replace=False)]
        elif age == "2":
            age_cards = age_cards[np.random.choice(age_cards.shape[0], self.age_2_card_count, replace=False)]
        elif age == "3":
            guilds_chosen = csv_dict['card_list'][np.where(csv_dict['card_list'][:,6] == "Guild")]
            guilds_chosen = guilds_chosen[np.random.choice(guilds_chosen.shape[0], self.age_guild_card_count, replace=False)]
            age_cards = age_cards[np.random.choice(age_cards.shape[0], self.age_3_card_count, replace=False)]
            age_cards = np.vstack((age_cards, guilds_chosen)) # Add guild cards and normal cards together
            np.random.shuffle(age_cards) # Shuffle cards together
        else:
            return

        # Unpack age layout np.array in card slot objects
        card_positions = [CardSlot(**dict(zip(csv_dict['age_layouts_labels'], row)))
                          for row in age_layout]
        
        # Place card objects into card slots
        for slot, _ in enumerate(card_positions):
            card_positions[slot].card_in_slot = Card(**dict(zip(csv_dict['card_list_labels'], age_cards[slot])))

        return card_positions

    def update_all(self):
        '''Updates all slots on board as per update_slot method'''
        for slot in range(len(self.card_positions)):
            self.update_slot(slot)  # Update each slot for visibility and selectability.

    def update_slot(self, slot):
        '''Updates card in a single slot for visibility, selectability, etc.'''
        if self.card_positions[slot].covered_by:  # Checks whether there are still cards covering this card.
            # Apparently the pythonic way to check a list is not empty is to see if the list is true... ¯\_(ツ)_/¯
            for covering_card in self.card_positions[slot].covered_by:  # Loops through list of
                # covering cards. Does it backwards to avoid index errors.
                if self.card_positions[covering_card].card_in_slot is None:  # Checks if covering card has been taken.
                    self.card_positions[slot].covered_by.remove(covering_card)  # If covering card has been taken,
                    # remove it from list of covering cards.

        if not self.card_positions[slot].covered_by:  # If no more covering cards, make card visible and selectable.
            self.card_positions[slot].card_selectable = 1
            self.card_positions[slot].card_visible = 1

    def display_board(self):
        '''Prints visual representation of cards remaining on the board for this age'''
        cards = self.card_positions
        rows = self.number_of_rows
        for row in reversed(range(rows + 1)):
            print("Row", str(row + 1), ":", [card for card in cards if card.row == str(row)])
