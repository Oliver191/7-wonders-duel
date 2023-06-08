'''Module to play a game of Seven Wonders Duel'''
import numpy as np
from numpy.random import default_rng
from sty import fg, bg, rs
from seven_wonders_visual import ImageDisplay

class Game:
    '''Define a single instance of a game'''

    def __init__(self, game_count=1):
        # Create a list of lists, one list per age containing the card objects for that age:
        self.age_boards = [Age(age) for age in range(1, 4)]
        self.game_count = game_count
        self.players = [Player(0, 'human'), Player(1, 'human')]
        self.state_variables = StateVariables()
        self.progress_board = PorgressBoard()
        print("Welcome to 7 Wonders Duel - Select a Card to Play")
        self.display_game_state()

    def __repr__(self):
        return repr('Game Instance: ' + str(self.game_count))

        # TODO: Draft wonders function

    def request_player_input(self):  # TODO When using AI, no need for player input, just needs to print AI choice.
        """Function to begin requesting player input

        Returns:
            void: [description]
        """
        if self.state_variables.turn_choice:
            print("")
            print("As the player with the weaker military, you are allowed to choose who begins the next Age.")
            print("Enter [turn] to allow your opponent to begin.")
            print("Otherwise continue playing:")

        choice = input("PLAYER " + str(self.state_variables.turn_player + 1) + ": "
                       + "Select a card to [c]onstruct or [d]iscard for coins. ")
                       #+ "(Format is 'X#' where X is c/d and # is card position)")  # TODO Select by name or number?

        if choice == '':
            print("Select a valid action! (construct or discard)")
            return self.request_player_input()
        action, position = choice[0], choice[1:]

        if choice == 'turn' and self.state_variables.turn_choice:
            print("Opponent is chosen to begin.")
            self.state_variables.turn_choice = False
            self.state_variables.change_turn_player()
            return self.request_player_input()

        if action == 'q':
            return print("Game has been quit")

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
            image_dict, selectable_dict, max_row = self.show_board()
            image = ImageDisplay(220, 350)
            # TODO Add display of available progress tokens on military board
            # TODO Add display of owned progress tokens on player board
            age = self.state_variables.current_age
            military = self.state_variables.military_track
            tokens = self.state_variables.military_tokens
            coins = {-1 : self.players[0].coins, -2 : self.players[1].coins}
            image.display_board(image_dict, selectable_dict, max_row, age, military, tokens, coins)
            print("Please choose a card!")
            return self.request_player_input()

        if action != 'c' and action != 'd':
            print("Select a valid action! (construct or discard)")
            return self.request_player_input()

        if not position.isdigit():
            print("Card choice must be an integer!")
            return self.request_player_input()

        self.select_card(int(position), action)

    # Main gameplay loop - players alternate choosing cards from the board and performing actions with them.
    def select_card(self, position, action='c'):
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
            if self.card_constructable(player_state, opponent_state, chosen_position.card_in_slot) is True:
                player_state.construct_card(chosen_position.card_in_slot, player_board, opponent_board)
            else:
                print('You do not have the resources required to construct this card!')
                return self.request_player_input()
        elif action == 'd':
            # Gain coins based on yellow building owned.
            yellow_card_count = len([card for card in player_board if card.card_type == 'Yellow'])
            player_state.coins += 2 + yellow_card_count
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
            return print('Player 1 has won the Game through Military Supremacy!')
        elif self.state_variables.military_track <= -9:
            self.display_game_state()
            return print('Player 2 has won the Game through Military Supremacy!')

        # Award victory points based on conflict pawn location
        self.update_conflict_points()

        # Grant military tokens
        self.grant_military_token()

        # Check for scientific victory
        if all([symbol >= 1 for symbol in self.players[0].science]):
            self.display_game_state()
            return print('Player 1 has won the Game through Scientific Victory!')
        elif all([symbol >= 1 for symbol in self.players[1].science]):
            self.display_game_state()
            return print('Player 2 has won the Game through Scientific Victory!')

        # Award victory points based on purple cards
        if self.state_variables.current_age == 2: #only check in Age 3 to reduce computations
            card_effects = [card.card_effect_passive for card in self.players[0].cards_in_play if card.card_type == 'Purple']
            if len(card_effects) > 0:
                self.update_guild_points(card_effects, 0)
            card_effects = [card.card_effect_passive for card in self.players[1].cards_in_play if card.card_type == 'Purple']
            if len(card_effects) > 0:
                self.update_guild_points(card_effects, 1)

        # If 2 matching scientific symbols are collected, allow progress token selection
        tokens_awarded = self.state_variables.progress_tokens_awarded
        match_science = [True if self.players[player].science[i] >= 2 and not tokens_awarded[i] else False for i in range(len(self.players[player].science))]
        if any(match_science):
            self.state_variables.progress_tokens_awarded[match_science.index(True)] = True
            token = self.select_token()
            self.players[player].construct_token(token, self.progress_board)
            self.progress_board.tokens[token].token_in_slot = False

            # Check for end of age (all cards drafted)
        if all(slots_in_age[slot].card_in_slot is None for slot in range(len(slots_in_age))):
            self.state_variables.progress_age()
        else:  # Otherwise, update all cards in current age and change turn turn_player
            self.age_boards[age].update_all()
            self.state_variables.change_turn_player()  # TODO This might not always be true if go again wonders chosen

        if self.state_variables.game_end:
            # Civilian victory: 1 victory point for every 3 coins
            self.players[0].victory_points += self.players[0].coins // 3
            self.players[1].victory_points += self.players[1].coins // 3
            self.display_game_state()

            # Handle Civilian Victory
            print('Victory Points Player 1: ', self.players[0].victory_points)
            print('Victory Points Player 2: ', self.players[1].victory_points)
            if self.players[0].victory_points > self.players[1].victory_points:
                print('Player 1 has won the Game through Civilian Victory!')
            elif self.players[0].victory_points < self.players[1].victory_points:
                print('Player 2 has won the Game through Civilian Victory!')
            else:
                print('Both players have the same number of victory points.')
                p1_blue_vp = sum([int(card.card_effect_passive[0]) for card in self.players[0].cards_in_play if card.card_type == 'Blue'])
                p2_blue_vp = sum([int(card.card_effect_passive[0]) for card in self.players[1].cards_in_play if card.card_type == 'Blue'])
                print('Victory Points Civilian Buildings Player 1: ', p1_blue_vp)
                print('Victory Points Civilian Buildings Player 2: ', p2_blue_vp)
                if p1_blue_vp > p2_blue_vp:
                    print('Player 1 has won the Game with the most victory points from Civilian Buildings!')
                elif p1_blue_vp < p2_blue_vp:
                    print('Player 2 has won the Game with the most victory points from Civilian Buildings!')
                else:
                    print('Both players have the same number of victory points from Civilian Buildings.')
                    print('The game ends in a draw!')
            return

        # Continue game loop.
        self.display_game_state()
        return self.request_player_input()

    # Takes 2 Player objects and 1 Card object and checks whether card is constructable given state and cost.
    def card_constructable(self, player, opponent, card):
        '''Checks whether a card is constructable given current player states'''
        cost, counts = np.unique(list(card.card_cost), return_counts=True) #split string and return unique values and their counts
        trade_cost = 0
        coins_needed = 0
        constructable = True
        cards = [card.card_name for card in player.cards_in_play]
        net_cost = ''
        if card.card_prerequisite in cards: #free construction condition
            return constructable
        # check if player has insufficient resources to construct the card
        for i, j in zip(['C', 'W', 'S', 'P', 'G'], [player.clay, player.wood, player.stone, player.paper, player.glass]):
            if i in card.card_cost:
                resources_needed = counts[np.where(cost == i)[0]][0]
                if resources_needed > j:
                    constructable = False
                    net_cost += i*(resources_needed - j)
        net_cost = self.variable_production(net_cost, cards, opponent) #Handle variable production
        for i in list(net_cost): # calculates cost to trade for the resource
            trade_cost += self.calculate_rate(i, cards, opponent)
        if '$' in card.card_cost: #check if player has enough coins to construct the card
            coins_needed = counts[np.where(cost == '$')[0]][0]
            if coins_needed > player.coins:
                constructable = False
        if player.coins >= trade_cost + coins_needed: #trade for necessary resources to construct the card
            constructable = True
            player.coins -= trade_cost
        return constructable #False if cost or materials > players coins or materials

    # Chooses the resource with the highest trading cost and uses variable production for it, if available
    def variable_production(self, net_cost, cards, opponent):
        if 'Forum' in cards:
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
        if 'Caravansery' in cards:
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

    # Requests player input to select one of the tokens still available where token_in_slot == True
    def select_token(self):
        print("")
        print("Player " + str(self.state_variables.turn_player + 1) +
              " gathered 2 matching scientific symbols.")
        choice = input("PLAYER " + str(self.state_variables.turn_player + 1) + ": "
                       + "Please [c]onstruct a progress token from the Board. ")
        if choice == '':
            print('This is not a valid action!')
            return self.select_token()
        action, position = choice[0], choice[1:]
        if action == 's': #Display a visual representation of the game
            image_dict, selectable_dict, max_row = self.show_board()
            image = ImageDisplay(220, 350)
            # TODO Copy adjusted function from above
            age = self.state_variables.current_age
            military = self.state_variables.military_track
            tokens = self.state_variables.military_tokens
            coins = {-1 : self.players[0].coins, -2 : self.players[1].coins}
            image.display_board(image_dict, selectable_dict, max_row, age, military, tokens, coins)
            print("Please choose a token!")
            return self.select_token()
        elif action == 'c':
            if position == '':
                print('This is not a valid action!')
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

    # Calculates the rate at which a resource can be bought
    def calculate_rate(self, resource, cards, opponent):
        resource_counts = [opponent.clay, opponent.wood, opponent.stone, opponent.paper, opponent.glass]
        rate = 2 + resource_counts[np.where(np.array(['C', 'W', 'S', 'P', 'G']) == resource)[0][0]]
        #handle yellow cards fixing trading rates
        for name, res in zip(['Stone Reserve', 'Clay Reserve', 'Wood Reserve'], ['S', 'C', 'W']):
            if name in cards and resource == res:
                rate = 1
        if 'Customs House' in cards and resource in ['P', 'G']:
            rate = 1
        return rate

    # Takes 2 Player objects and 1 Card object and constructs the card if possible. If it cannot, returns False.
    def valid_moves(self, player, opponent, age):  # TODO Return list of valid moves for current player.
        '''Returns list of valid moves for given board state and player states'''
        return

    def show_board(self):
        age = self.state_variables.current_age
        slots_in_age = self.age_boards[age].card_positions
        image_dict = {}
        selectable_dict = {}
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
        image_dict[-1] = [card.card_name.replace(" ", "").lower() for card in self.players[0].cards_in_play]
        selectable_dict[-1] = [1] * len(image_dict[-1])
        image_dict[-2] = [card.card_name.replace(" ", "").lower() for card in self.players[1].cards_in_play]
        selectable_dict[-2] = [1] * len(image_dict[-2])
        return image_dict, selectable_dict, max_row

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
        if abs(military) in [0]:
            points = 0
        elif abs(military) in [1, 2]:
            points = 2
        elif abs(military) in [3, 4, 5]:
            points = 5
        elif abs(military) >= 6:
            points = 10

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

class PorgressBoard:
    '''Define the progress board in which the progress tokens are slotted into'''

    def __init__(self):
        self.tokens = self.prepare_progress_board()

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
    def prepare_progress_board(self):
        token_count = 5
        token_list = np.genfromtxt('progress_tokens.csv', delimiter=',', skip_header=1, dtype=str)
        chosen_tokens = token_list[np.random.choice(token_list.shape[0], token_count, replace=False)]
        tokens = []
        for token in chosen_tokens:
            tokens.append(ProgressToken(token[0], token[1], token[2], True))
        return tokens

class Player:
    '''Define a class for play to track tableau cards, money, etc.'''

    def __init__(self, player_number=0, player_type='human'):
        # Private:
        self.player_number = player_number
        self.player_type = player_type

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
        self.victory_tokens = []
        self.science = [0,0,0,0,0,0]

    def __repr__(self):
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
                   + ", Tokens: " + repr(self.progress_tokens_in_play))

    # removal of card from game board is done elsewhere! (in Game.select_card method).
    def construct_card(self, card, player_board, opponent_board):
        '''Function to construct a card in a players tableau'''
        # decrease coins of player by card cost
        cost, counts = np.unique(list(card.card_cost), return_counts=True)  # split string and return unique values and their counts
        cards = [card.card_name for card in player_board]
        if '$' in card.card_cost and card.card_prerequisite not in cards: #free construction condition
            self.coins -= counts[np.where(cost == '$')[0]][0] # decrease coins by card cost

        # increase player variables by resource card effect
        if card.card_type == 'Yellow': # handle Yellow cards
            effect = list(card.card_effect_passive)
            if 'V' in effect: # Handle Age 3 Yellow Cards
                self.victory_points += int(effect[0])
                effect_active = card.card_effect_when_played.split(' per ')
                for i in ['Grey', 'Brown', 'Red', 'Yellow']:
                    if i in effect_active:
                        type_count = len([1 for card in player_board if card.card_type == i])
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
        self.cards_in_play.append(card)
        return

    def update(self):
        '''Updates player passive variables based on players tableau'''
        return

    # construct the selected token by applying their respective effect
    def construct_token(self, token, progress_board):
        # TODO Apply token effect
        self.progress_tokens_in_play.append(progress_board.tokens[token])

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
    
    # Import card layout and labels for each age:
    age_layouts = np.genfromtxt('age_layout.csv', delimiter=',', skip_header=1, dtype=str)
    age_layouts_labels = np.genfromtxt('age_layout.csv', delimiter=',', dtype=str, max_rows=1)
    
    # Import full card list:
    card_list = np.genfromtxt('card_list.csv', delimiter=',', skip_header=1, dtype=str)
    card_list_labels = np.genfromtxt('card_list.csv', delimiter=',', dtype=str, max_rows=1)

    age_1_card_count = 20
    age_2_card_count = 20
    age_3_card_count = 17
    age_guild_card_count = 3

    def __init__(self, age):
        self.age = age
        self.card_positions = self.prepare_age_board(age)
        self.number_of_rows = int(max(self.card_positions[slot].row for slot in range(len(self.card_positions))))

    def __repr__(self):
        return str('Age ' + str(self.age))

    # Init functions:

    def prepare_age_board(self, age):   
        '''Takes dataframe of all cards and creates list of card objects representing the board for a given age.'''
        age = str(age)  # Convert to int if required
        age_layout = self.age_layouts[np.where(self.age_layouts[:,4] == age)]  # Filter for age
        age_cards = self.card_list[np.where(self.card_list[:,6] == age)]  # Filter for age

        if age == "1":
            age_cards = age_cards[np.random.choice(age_cards.shape[0], self.age_1_card_count, replace=False)]
        elif age == "2":
            age_cards = age_cards[np.random.choice(age_cards.shape[0], self.age_2_card_count, replace=False)]
        elif age == "3":
            guilds_chosen = self.card_list[np.where(self.card_list[:,6] == "Guild")]
            guilds_chosen = guilds_chosen[np.random.choice(guilds_chosen.shape[0], self.age_guild_card_count, replace=False)]
            age_cards = age_cards[np.random.choice(age_cards.shape[0], self.age_3_card_count, replace=False)]
            age_cards = np.vstack((age_cards, guilds_chosen)) # Add guild cards and normal cards together
            np.random.shuffle(age_cards) # Shuffle cards together
        else:
            return
        
        # Unpack age layout np.array in card slot objects
        card_positions = [CardSlot(**dict(zip(self.age_layouts_labels, row)))
                          for row in age_layout]
        
        # Place card objects into card slots
        for slot, _ in enumerate(card_positions):
            card_positions[slot].card_in_slot = Card(**dict(zip(self.card_list_labels, age_cards[slot])))
        
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


# To run the game
if __name__ == "__main__":
    game1 = Game(1)
    pass
    game1.request_player_input()
