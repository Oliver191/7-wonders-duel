'''Module to play a game of Seven Wonders Duel'''
import numpy as np
from numpy.random import default_rng
from sty import fg, bg, rs
from seven_wonders_visual import ImageDisplay
import argparse
import importlib
from collections import Counter
from testAgents import HumanAgent

import time

class Game:
    '''Define a single instance of a game'''

    def __init__(self, game_count, agent_class, agent_type, csv_dict):
        self.csv_dict = csv_dict
        self.agent1, self.player_type1 = self.initialize_agent(agent_class[0], game_count[0])
        self.agent2, self.player_type2 = self.initialize_agent(agent_class[1], game_count[0])
        self.wins_player1, self.wins_player2, self.draws = 0, 0, 0
        self.run_game(game_count[0], game_count[1], agent_type)

    def __repr__(self):
        return repr(self.outcome)

    # initializes the agent if it is specified
    def initialize_agent(self, agent, numTraining):
        if agent is None:
            return HumanAgent(), 'human'
        else:
            return agent(print, numTraining), 'agent'

    # runs the game, the specified number of times
    def run_game(self, numTraining, game_count, agent_type):
        training = True
        for game_number in range(game_count):
            self.game_number = max(0, game_number - numTraining)
            self.set_game_state()
            self.request_player_input()
            self.update_outcome()
            self.final()
            if self.game_number > 0 and training:
                training = False
                original_print("\nTraining completed!\n")
            # if game_number < 100: original_print(self.outcome)
            if (game_number + 1) % 100 == 0:
                self.print_update(self.wins_player1, self.wins_player2, self.draws, game_number + 1, agent_type[0], agent_type[1])

    # Keep track of wins, losses, and draws
    def update_outcome(self):
        if 'Player' in self.outcome:
            if self.outcome.split()[1] == "1":
                self.wins_player1 += 1
            elif self.outcome.split()[1] == "2":
                self.wins_player2 += 1
        else:
            self.draws += 1

    # Execute final function of agent, if it exists
    def final(self):
        if hasattr(self.agent1, 'final') and callable(getattr(self.agent1, 'final')):
            self.agent1.final(self.copy_state(0), self.outcome)
        if hasattr(self.agent2, 'final') and callable(getattr(self.agent2, 'final')):
            self.agent2.final(self.copy_state(1), self.outcome)

    # initializes the game
    def set_game_state(self):
        self.players = [Player(0, self.player_type1, self.agent1), Player(1, self.player_type2, self.agent2)]
        self.age_boards = [Age(age, self.csv_dict) for age in range(1, 4)]
        self.state_variables = StateVariables()
        self.progress_board = ProgressBoard(self.csv_dict)
        self.outcome, self.state, self.constructable_dict = None, None, {}
        self.draft_wonders(self.csv_dict)
        print("Welcome to 7 Wonders Duel - Select a Card to Play")
        self.display_game_state()
        self.elapsed_time = 0.0

    def print_update(self, wins_player1, wins_player2, draws, game_number, agent1, agent2):
        original_print()
        original_print("Wins Player 1: " + str(wins_player1) + "/" + str(game_number) + " (" + agent1 + ")")
        original_print("Wins Player 2: " + str(wins_player2) + "/" + str(game_number) + " (" + agent2 + ")")
        original_print("Draws: " + str(draws) + "/" + str(game_number))

    #Copy all essential information of the current game state
    def copy_state(self, player):
        state = {'age_board': self.age_boards[self.state_variables.current_age].card_positions,
                 'player': self.players[player],
                 'opponent': self.players[player ^ 1],
                 'state_variables': self.state_variables,
                 'progress_board': self.progress_board
                 }
        return state

    #Draft wonders by selecting 8 random ones and letting players choose them in turn
    def draft_wonders(self, csv_dict):
        wonder_count = 8
        chosen_wonders = csv_dict['wonder_list'][np.random.choice(csv_dict['wonder_list'].shape[0], wonder_count, replace=False)]
        wonders = []
        for wonder in chosen_wonders:
            wonders.append(Wonder(wonder[0], wonder[1], wonder[2], wonder[3], False))
        player = self.state_variables.turn_player
        opponent = player ^ 1
        selectable = [True for i in range(8)]
        print("")
        print("Before the game begins, each player selects 4 wonders.")
        print("Player " + str(player+1) + " selects the first, Player " + str(opponent+1) + " chooses the next two, and then Player " + str(player+1) + " gets the remaining wonder.")
        selectable = self.wonder_input(player, wonders[:4], selectable, 0)
        selectable = self.wonder_input(opponent, wonders[:4], selectable, 0)
        selectable = self.wonder_input(opponent, wonders[:4], selectable, 0)
        self.players[player].wonders_in_hand.append(wonders[selectable[:4].index(True)])
        selectable[selectable[:4].index(True)] = False
        print("PLAYER " + str(player+1) + " receives the last remaining wonder.")

        print("")
        print("Now the next four wonders are selected in the same fashion, but Player " + str(opponent+1) + " begins.")
        selectable = self.wonder_input(opponent, wonders[4:], selectable, 4)
        selectable = self.wonder_input(player, wonders[4:], selectable, 4)
        selectable = self.wonder_input(player, wonders[4:], selectable, 4)
        self.players[opponent].wonders_in_hand.append(wonders[selectable[4:].index(True)+4])
        selectable[selectable[4:].index(True)+4] = False
        print("PLAYER " + str(opponent + 1) + " receives the last remaining wonder.")

        print("Player 1 Wonders: ", self.players[0].wonders_in_hand)
        print("Player 2 Wonders: ", self.players[1].wonders_in_hand)
        print("")

    # Generates all valid moves a player can take during wonder drafting
    def valid_moves_wonder(self, remaining_wonders, selectable, shift):
        valid_moves = ['w'+str(i) for i in range(len(remaining_wonders)) if selectable[i + shift]]
        return valid_moves

    #Select a single wonder during wonder drafting
    def wonder_input(self, player, remaining_wonders, selectable, shift):
        count = 0
        selectable_wonders = '['
        for i in range(len(remaining_wonders)):
            if selectable[i+shift]:
                selectable_wonders += '#' + str(i) + ' ' + str(remaining_wonders[i])
                count += 1
            selectable_wonders += ', '
        selectable_wonders = selectable_wonders[:-2]
        selectable_wonders += ']'

        print("Valid moves: " + str(self.valid_moves_wonder(remaining_wonders, selectable, shift)) + "\n")
        print("Wonders available: ", selectable_wonders)
        input_string = "PLAYER " + str(player + 1) + ": "+ "Select a remaining [w]onder of the " + str(count) + " available. "

        if self.players[player].player_type == 'agent':
            self.state = self.copy_state(player)
            wonder_dict = {k: v for k, v in zip(remaining_wonders, selectable[0 + shift:4 + shift])}
            choice = self.players[player].agent.getAction(self.valid_moves_wonder(remaining_wonders, selectable, shift), input_string, self.state, wonder_dict)
        else:
            choice = self.players[player].agent.getAction(input_string)

        if choice == '':
            print("Select a valid action!")
            return self.wonder_input(player, remaining_wonders, selectable, shift)
        action, position = choice[0], choice[1:]

        if action == 's':
            image = ImageDisplay(220, 350)
            p1_wonders, p2_wonders = self.players[0].wonders_in_hand, self.players[1].wonders_in_hand
            image.display_wonder(remaining_wonders, selectable, shift, p1_wonders, p2_wonders)
            return self.wonder_input(player, remaining_wonders, selectable, shift)
        elif action == 'w':
            if not position.isdigit():
                print("Wonder choice must be an integer!")
                return self.wonder_input(player, remaining_wonders, selectable, shift)
            elif int(position) in range(len(remaining_wonders)) and selectable[int(position)+shift]:
                self.players[player].wonders_in_hand.append(remaining_wonders[int(position)])
                selectable[int(position)+shift] = False
                return selectable
            else:
                print('Select a valid wonder!')
                return self.wonder_input(player, remaining_wonders, selectable, shift)
        else:
            print("Select a valid action!")
            return self.wonder_input(player, remaining_wonders, selectable, shift)

    def valid_moves(self):
        '''Returns list of valid moves for given board state and player states'''
        player = self.state_variables.turn_player
        opponent = player ^ 1
        cards = self.age_boards[self.state_variables.current_age].card_positions
        selectable = [cardslot.card_board_position for cardslot in cards if cardslot.card_selectable == 1 and cardslot.card_in_slot is not None]
        valid_moves = ['d' + str(i) for i in selectable]
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
        return valid_moves

    def request_player_input(self):
        """Function to begin requesting player input

        Returns:
            void: [description]
        """
        player = self.state_variables.turn_player
        self.state = self.copy_state(player)
        self.constructable_dict = {'cards': [card.card_name for card in self.players[player].cards_in_play],
                                   'wonders': [wonder.wonder_name for wonder in self.players[player].wonders_in_play],
                                   'owned_tokens': [token.token_name for token in self.players[player].progress_tokens_in_play],
                                   'opponent_tokens': [token.token_name for token in self.players[player ^ 1].progress_tokens_in_play]}
        print("Valid moves: " + str(self.valid_moves()) + "\n")

        if self.state_variables.turn_choice:
            print("")
            print("As the player with the weaker military, you are allowed to choose who begins the next Age.")
            print("Enter [turn] to allow your opponent to begin.")
            print("Otherwise continue playing:")

        if self.players[player].law:
            print("")
            print("Player " + str(player + 1) +
                  " owns the law progress token and may [r]edeem it once in exchange for any scientific symbol.")

        input_string = "PLAYER " + str(player + 1) + ": " + "Select a card to [c]onstruct, [d]iscard for coins, or use for [w]onder. "
        # + "(Format is 'X#' where X is c/d and # is card position)")
        if self.players[player].player_type == 'agent':
            choice = self.players[player].agent.getAction(self.valid_moves(), input_string, self.state, 'main')
        else:
            choice = self.players[player].agent.getAction(input_string)

        if choice == '':
            print("Select a valid action! (construct, discard or wonder)")
            return self.request_player_input()
        action, position, position_wonder = choice[0], choice[1:], "0"

        # If the player owns the law token, allow redeeming it in exchange for a scientific symbol
        if self.players[player].law and action == 'r':
            self.token_law(player, position)
            # Check for scientific victory
            if all([symbol >= 1 for symbol in self.players[player].science]):
                self.outcome = 'Player ' + str(player + 1) + ' has won the Game through Scientific Victory!'
                return self.outcome

        if choice == 'turn' and self.state_variables.turn_choice:
            print("Your opponent is chosen to begin.")
            self.state_variables.turn_choice = False
            self.state_variables.change_turn_player()
            return self.request_player_input()

        if action == 'q':
            self.outcome = "Game has been quit"
            return self.outcome

        if choice == 'clear': # has been implemented for debugging
            # clear board and progress age
            age = self.state_variables.current_age
            slots_in_age = self.age_boards[age].card_positions
            for slot in range(len(slots_in_age)):
                slots_in_age[slot].card_in_slot = None
            self.state_variables.progress_age()
            self.display_game_state()
            print("Board has been cleared!")
            return self.request_player_input()

        if action == 's': #Display a visual representation of the game
            self.show_board()
            print("Please choose a card!")
            return self.request_player_input()

        if action == 'w':
            if len(position.split(" ")) == 2:
                if position.split(" ")[0].isdigit() and position.split(" ")[1].isdigit():
                    position_wonder = position.split(" ")[1]
                    position = position.split(" ")[0]
                else:
                    print("Card and wonder choice must be an integer!")
                    return self.request_player_input()
            else:
                print("Choose a card and a wonder separated by a space.")
                return self.request_player_input()

        if action != 'c' and action != 'd' and action != 'w':
            if not self.players[player].law or not action == 'r':
                print("Select a valid action! (construct, discard or wonder)")
            return self.request_player_input()

        if not position.isdigit():
            print("Card choice must be an integer!")
            return self.request_player_input()

        self.select_card(int(position), action, int(position_wonder))

    # Main gameplay loop - players alternate choosing cards from the board and performing actions with them.
    def select_card(self, position, action='c', position_wonder=0):
        '''Function to select card on board and perform the appropriate action'''
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

        # Checks for valid card choices
        if position >= len(slots_in_age) or position < 0:
            print('Select a card on the board!')
            return self.request_player_input()

        chosen_position = slots_in_age[position]

        if chosen_position.card_in_slot is None:
            print('This card has already been chosen!')
            return self.request_player_input()

        if chosen_position.card_selectable == 0:
            print('Card is covered, you cannot pick this card!')
            return self.request_player_input()

        # Discard or construct chosen card and remove card from board
        if action == 'c':
            # Add card to board.
            if self.card_constructable(player_state, opponent_state, chosen_position.card_in_slot, False) is True:
                player_state.construct_card(chosen_position.card_in_slot, player_board, opponent_board, False)
            else:
                print('You do not have the resources required to construct this card!')
                return self.request_player_input()
        elif action == 'd':
            # Gain coins based on yellow building owned.
            yellow_card_count = len([card for card in player_board if card.card_type == 'Yellow'])
            player_state.coins += 2 + yellow_card_count
            self.state_variables.discarded_cards.append(chosen_position.card_in_slot)
        elif action == 'w':
            if position_wonder in range(len(player_state.wonders_in_hand)):
                if not [wonder.wonder_in_play for wonder in player_state.wonders_in_hand][position_wonder]:
                    if self.wonder_constructable(player_state, opponent_state, position_wonder, False):
                        player_state.construct_wonder(position_wonder, opponent_state, player, self.state_variables.discarded_cards,
                                                      player_board, opponent_board, self.progress_board, self.state)
                        if len(self.players[0].wonders_in_play + self.players[1].wonders_in_play) == 7:
                            for i in range(len(self.players[0].wonders_in_hand)):
                                player_state.wonders_in_hand[i].wonder_in_play = True
                                opponent_state.wonders_in_hand[i].wonder_in_play = True
                            print("")
                            print("Only 7 wonders can be constructed. The 8th wonder is discarded.")
                            print("")
                    else:
                        print('You do not have the resources required to construct this wonder!')
                        return self.request_player_input()
                else:
                    print('Wonder was already constructed!')
                    return self.request_player_input()
            else:
                print('Select a wonder in your hand!')
                return self.request_player_input()
        else:
            print('This is not a valid action!')
            return self.request_player_input()

        self.state_variables.turn_choice = False
        chosen_position.card_in_slot = None
        player_state.update()

        # Update military conflict and check for military victory
        self.state_variables.update_military_track(self.players[0].military_points, self.players[1].military_points)
        if self.state_variables.military_track >= 9:
            self.display_game_state()
            self.outcome = 'Player 1 has won the Game through Military Supremacy!'
            return self.outcome
        elif self.state_variables.military_track <= -9:
            self.display_game_state()
            self.outcome = 'Player 2 has won the Game through Military Supremacy!'
            return self.outcome

        # Award victory points based on conflict pawn location
        self.update_conflict_points()

        # Grant military tokens
        self.grant_military_token()

        # If 2 matching scientific symbols are collected, allow progress token selection
        self.check_progress_tokens(player)
        self.check_progress_tokens(player) #check a second time if law token was redeemed

        # Check for scientific victory
        if all([symbol >= 1 for symbol in self.players[player].science]):
            self.display_game_state()
            self.outcome = 'Player ' + str(player + 1) + ' has won the Game through Scientific Victory!'
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
                print("")
                print("Player " + str(player +1) + " has the Replay effect active and is allowed to play again.")
                print("")

        if self.state_variables.game_end:
            # Civilian victory: 1 victory point for every 3 coins
            self.players[0].victory_points += self.players[0].coins // 3
            self.players[1].victory_points += self.players[1].coins // 3
            self.display_game_state()

            # Handle Civilian Victory
            print('Victory Points Player 1: ', self.players[0].victory_points)
            print('Victory Points Player 2: ', self.players[1].victory_points)
            if self.players[0].victory_points > self.players[1].victory_points:
                self.outcome = 'Player 1 has won the Game through Civilian Victory!'
            elif self.players[0].victory_points < self.players[1].victory_points:
                self.outcome = 'Player 2 has won the Game through Civilian Victory!'
            else:
                print('Both players have the same number of victory points.')
                p1_blue_vp = sum([int(card.card_effect_passive[0]) for card in self.players[0].cards_in_play if card.card_type == 'Blue'])
                p2_blue_vp = sum([int(card.card_effect_passive[0]) for card in self.players[1].cards_in_play if card.card_type == 'Blue'])
                print('Victory Points Civilian Buildings Player 1: ', p1_blue_vp)
                print('Victory Points Civilian Buildings Player 2: ', p2_blue_vp)
                if p1_blue_vp > p2_blue_vp:
                    self.outcome = 'Player 1 has won the Game with the most victory points from Civilian Buildings!'
                elif p1_blue_vp < p2_blue_vp:
                    self.outcome = 'Player 2 has won the Game with the most victory points from Civilian Buildings!'
                else:
                    self.outcome = 'Both players have the same number of victory points from Civilian Buildings. The game ends in a draw!'
            return self.outcome

        # Continue game loop.
        self.display_game_state()
        return self.request_player_input()

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
        if not position.isdigit():
            return print("Symbol choice must be an integer!")
        elif int(position) in range(len(self.players[player].science)):
            self.players[player].science[int(position)] += 1
            self.players[player].law = False
            print("Token has been redeemed!")
            self.check_progress_tokens(player)
            self.display_game_state()
        else:
            return print('Select a valid scientific symbol!')

    # If 2 matching scientific symbols are collected, allow progress token selection
    def check_progress_tokens(self, player):
        tokens_awarded = self.state_variables.progress_tokens_awarded
        match_science = [True if self.players[player].science[i] >= 2 and not tokens_awarded[i] else False for i in
                         range(len(self.players[player].science))]
        if any(match_science) and any([token.token_in_slot for token in self.progress_board.tokens]):
            self.state_variables.progress_tokens_awarded[match_science.index(True)] = True
            token = self.select_token()
            self.players[player].construct_token(self.progress_board.tokens[token], self.progress_board, self.state)
            self.progress_board.tokens[token].token_in_slot = False

    # Requests player input to select one of the tokens still available where token_in_slot == True
    def select_token(self):
        print("Valid moves: " + str(self.valid_moves_token()))
        print("")
        print("Player " + str(self.state_variables.turn_player + 1) +
              " gathered 2 matching scientific symbols.")
        input_string = "PLAYER " + str(self.state_variables.turn_player + 1) + ": " + "Please [c]onstruct a progress token from the Board. "
        if self.players[self.state_variables.turn_player].player_type == 'agent':
            choice = self.players[self.state_variables.turn_player].agent.getAction(self.valid_moves_token(), input_string, self.state, 'token')
        else:
            choice = self.players[self.state_variables.turn_player].agent.getAction(input_string)
        if choice == '':
            print('This is not a valid action!')
            return self.select_token()
        action, position = choice[0], choice[1:]
        if action == 's': #Display a visual representation of the game
            self.show_board()
            print("Please choose a token!")
            return self.select_token()
        elif action == 'c':
            if not position.isdigit():
                print("Token choice must be an integer!")
                return self.select_token()
            elif int(position) in range(len(self.progress_board.tokens)):
                if self.progress_board.tokens[int(position)].token_in_slot:
                    return int(position)
                else:
                    print('This token has already been chosen!')
                    return self.select_token()
            else:
                print('Select a valid token on the board!')
                return self.select_token()
        else:
            print('This is not a valid action!')
            return self.select_token()

    # Generates all valid moves a player can take during token selection
    def valid_moves_token(self):
        valid_moves = ['c' + str(i) for i in range(len(self.progress_board.tokens)) if self.progress_board.tokens[i].token_in_slot]
        return valid_moves

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

    # read tokens, randomly select 5, and slot them into the board
    def prepare_progress_board(self, csv_dict):
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
    def construct_wonder(self, position_wonder, opponent, player_turn, discarded_cards, player_board, opponent_board, progress_board, state):
        wonder = self.wonders_in_hand[position_wonder]
        effect = wonder.wonder_effect_when_played
        effect_passive = wonder.wonder_effect_passive
        discarded_tokens = progress_board.discarded_tokens
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
        elif 'Grey' in effect_passive:
            self.wonder_destory_card(opponent, 'Grey', player_turn, discarded_cards, state)
        elif 'Brown' in effect_passive:
            self.wonder_destory_card(opponent, 'Brown', player_turn, discarded_cards, state)
        elif wonder.wonder_name == 'The Mausoleum':
            self.wonder_mausoleum(discarded_cards, player_turn, player_board, opponent_board, state)
        elif wonder.wonder_name == 'The Great Library':
            self.wonder_great_library(discarded_tokens, player_turn, progress_board, state)

        wonder.wonder_in_play = True
        self.wonders_in_hand[position_wonder].wonder_in_play = True
        self.wonders_in_play.append(wonder)
        return

    # Enables the player to discard one card from his opponent in the specified color
    def wonder_destory_card(self, opponent, color, player_turn, discarded_cards, state):
        opponent_cards = [card for card in opponent.cards_in_play if card.card_type == color]
        opponent_turn = player_turn ^ 1

        if len(opponent_cards) >= 2:
            cards = self.print_string(opponent_cards)
            print("")
            print(color + " cards of Player " + str(opponent_turn + 1) + ": " + cards)
            input_string = "PLAYER " + str(player_turn + 1) + ": " + "Select a " + color + " card of Player " + \
                           str(opponent_turn + 1) + " to discard. "
            result = self.request_input(input_string,self.wonder_destory_card,opponent_cards, 'd', 'Card', state, 'destroy')
            if type(result) is int:
                card = opponent_cards[result]
                self.discard_card(card, opponent, discarded_cards)
            else:
                result(opponent, color, player_turn, discarded_cards, state)
        elif len(opponent_cards) == 1:
            card = opponent_cards[0]
            print("")
            print(str(card) + " of Player " + str(opponent_turn + 1) + " is discarded.")
            self.discard_card(card, opponent, discarded_cards)

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
    def wonder_mausoleum(self, discarded_cards, player_turn, player_board, opponent_board, state):
        if len(discarded_cards) >= 2:
            cards = self.print_string(discarded_cards)
            print("")
            print("Discarded cards since the beginning of the game: " + cards)
            input_string = "PLAYER " + str(player_turn + 1) + ": " + "Select a discarded card and construct it for free. "

            result = self.request_input(input_string, self.wonder_mausoleum, discarded_cards, 'c', 'Card', state, 'mausoleum')
            if type(result) is int:
                card = discarded_cards[result]
                discarded_cards.remove(card)
                self.construct_card(card, player_board, opponent_board, True)
            else:
                result(discarded_cards, player_turn, player_board, opponent_board, state)
        elif len(discarded_cards) == 1:
            card = discarded_cards[0]
            print("")
            print("Discarded card " + str(card) + " is constructed for free.")
            discarded_cards.remove(card)
            self.construct_card(card, player_board, opponent_board, True)

    # Enables the player to pick 1 from 3 discarded Progress Tokens
    def wonder_great_library(self, discarded_tokens, player_turn, progress_board, state):
        tokens = self.print_string(discarded_tokens)
        print("")
        print("3 random discarded tokens from the beginning of the game: " + tokens)
        input_string = "PLAYER " + str(player_turn + 1) + ": " + "Select a discarded token and construct it for free. "
        result = self.request_input(input_string, self.wonder_great_library, discarded_tokens, 'c', 'Token', state, 'library')
        if type(result) is int:
            token = discarded_tokens[result]
            discarded_tokens.remove(token)
            self.construct_token(token, progress_board, state)
        else:
            result(discarded_tokens, player_turn, progress_board, state)

    # Sub-function to request player input
    def request_input(self, input_string, function_false, card_list, key, print_object, state, function):
        print("Valid moves: " + str(self.valid_moves_effect(card_list, key)) + "\n")
        if self.player_type == 'agent':
            choice = self.agent.getAction(self.valid_moves_effect(card_list, key), input_string, state, function)
        else:
            choice = self.agent.getAction(input_string)
        if choice == '':
            print("Select a valid action!")
            return function_false
        action, position = choice[0], choice[1:]
        if action == 's':
            width, height = 220, 350
            if print_object == 'Token':
                width, height = 140, 140
            image = ImageDisplay(width, height)
            image.display_cards(card_list, print_object)
            return function_false
        elif action == key:
            if not position.isdigit():
                print(str(print_object) + " choice must be an integer!")
                return function_false
            elif int(position) in range(len(card_list)):
                return int(position)
            else:
                print("Select a valid " + print_object.lower() + "!")
                return function_false
        else:
            print("Select a valid action!")
            return function_false

    # Generates all valid moves a player can take during wonder effects
    def valid_moves_effect(self, card_list, key):
        valid_moves = [key + str(i) for i in range(len(card_list))]
        return valid_moves

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
    def construct_token(self, token, progress_board, state):
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
            print("")
            print("Player " + str(self.player_number + 1) + " >", self.__repr__())
            self.token_law(progress_board, state)
        elif name == 'Mathematics':
            self.victory_points += 3*len(owned_tokens) + 3

    # If the token Law is in posession, allow redeeming it for a scientific symbol
    def token_law(self, progress_board, state):
        print("Valid moves: " + str(self.valid_moves_token_law()) + "\n")
        print("Player " + str(self.player_number + 1) +
              " owns the law progress token and may [r]edeem it once in exchange for any scientific symbol.")
        input_string = "PLAYER " + str(self.player_number + 1) + ": "
        if self.player_type == 'agent':
            choice = self.agent.getAction(self.valid_moves_token_law(), input_string, state, 'law')
        else:
            choice = self.agent.getAction(input_string)
        if choice == '':
            print("Selected action was not valid. Resume game.")
            return print("")
        action, position = choice[0], choice[1:]
        if action == 's':
            tokens = progress_board.tokens.copy()
            token_names = [token.token_name for token in tokens]
            if 'Law' in token_names:
                tokens.remove(tokens[token_names.index('Law')])
            image = ImageDisplay(140, 140)
            image.display_cards(tokens, 'Token')
            return self.token_law(progress_board)
        elif action == 'r':
            if not position.isdigit():
                print("Symbol choice must be an integer!")
                return self.token_law(progress_board)
            elif int(position) in range(len(self.science)):
                self.science[int(position)] += 1
                self.law = False
                print("Token has been redeemed!")
            else:
                print('Select a valid scientific symbol!')
                return self.token_law(progress_board)
        else:
            print("Selected action was not valid. Resume game.")
            return print("")

    # Generates all valid moves a player can take when redeeming the law token
    def valid_moves_token_law(self):
        valid_moves = ['r' + str(i) for i in range(len(self.science))]
        valid_moves.append('q')
        return valid_moves

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
        self.number_of_rows = int(max(self.card_positions[slot].row for slot in range(len(self.card_positions))))

    def __repr__(self):
        return str('Age ' + str(self.age))

    # Init functions:

    def prepare_age_board(self, age, csv_dict):
        '''Takes dataframe of all cards and creates list of card objects representing the board for a given age.'''
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

# To supress print statements if required
def supress_print(*args, **kwargs):
    pass

def import_agent(agent_type):
    agent_module = importlib.import_module('testAgents')
    return getattr(agent_module, agent_type) if agent_type is not None else None

def read_data():
    csv_dict = {'age_layouts': np.genfromtxt('age_layout.csv', delimiter=',', skip_header=1, dtype=str),
                'age_layouts_labels': np.genfromtxt('age_layout.csv', delimiter=',', dtype=str, max_rows=1),
                'card_list': np.genfromtxt('card_list.csv', delimiter=',', skip_header=1, dtype=str),
                'card_list_labels': np.genfromtxt('card_list.csv', delimiter=',', dtype=str, max_rows=1),
                'token_list': np.genfromtxt('progress_tokens.csv', delimiter=',', skip_header=1, dtype=str),
                'wonder_list': np.genfromtxt('wonder_list.csv', delimiter=',', skip_header=1, dtype=str)}
    return csv_dict

# To run the game
if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--training_count", type=int, default=0, help="Number of games during training")
    parser.add_argument("-g", "--game_count", type=int, default=1, help="Number of games")
    parser.add_argument("-a1", "--agent1_type", type=str, default=None, help="Type of Agent 1 to import")
    parser.add_argument("-a2", "--agent2_type", type=str, default=None, help="Type of Agent 2 to import")
    parser.add_argument("-s", "--supress", type=str, default='False', help="Game state not printed when True")
    args = parser.parse_args()

    original_print = print
    numTraining = args.training_count
    game_count = args.game_count
    agent1_class = import_agent(args.agent1_type)
    agent2_class = import_agent(args.agent2_type)
    supress = True if args.supress == 'True' else False
    wins_player1, wins_player2, draws = 0, 0, 0
    if supress:
        print()
        print = supress_print
    agent1, agent2 = str(args.agent1_type) if args.agent1_type is not None else 'HumanAgent', str(
        args.agent2_type) if args.agent2_type is not None else 'HumanAgent'
    csv_dict = read_data()
    game1 = Game([numTraining, game_count], [agent1_class, agent2_class], [agent1, agent2], csv_dict)

    elapsed_time = time.time() - start_time
    original_print(f"\nExecution time: {elapsed_time} seconds")
    pass


# Code to measure execution time
# start_time = time.time()
#
# self.elapsed_time += time.time() - start_time
# original_print(f"\nExecution time: {self.elapsed_time} seconds")