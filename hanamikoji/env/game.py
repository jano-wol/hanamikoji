from copy import deepcopy
from .move_generator import *


def _add_cards(a, b):
    return [a + b for a, b in zip(a, b)]


def _sub_cards(a, b):
    return [a - b for a, b in zip(a, b)]


def card_list_to_inner(l):
    ret = [0] * 7
    for c in l:
        ret[c - 1] += 1
    return ret


class GameState(object):
    """
    GameState contains the public data of the game.
    """

    def __init__(self):
        # 'first' and 'second' mean global first and second player unless otherwise stated
        self.acting_player_id = 'first'
        # Here keys mean global 'first' and 'second', values mean round local first and second (indicating eval model)
        self.id_to_round_id = {'first': 'first', 'second': 'second'}
        # Constant rule list storing the geisha card numbers which coincide with their point reward
        self.points = [2, 2, 2, 3, 3, 4, 5]
        # The already played and public geisha gift cards
        self.gift_cards = {'first': [0, 0, 0, 0, 0, 0, 0], 'second': [0, 0, 0, 0, 0, 0, 0]}
        # The possible action cards
        self.action_cards = {'first': [1, 1, 1, 1], 'second': [1, 1, 1, 1]}
        # decision cards 1 - 2
        self.decision_cards_1_2 = None
        # decision cards 2 - 2
        self.decision_cards_2_2 = None
        # +1 if player is preferred
        self.geisha_preferences = {'first': [0, 0, 0, 0, 0, 0, 0], 'second': [0, 0, 0, 0, 0, 0, 0]}
        # The number of cards in hand
        self.num_cards = {'first': 7, 'second': 6}
        # Contains the moves of the first and second players
        self.round_moves = {'first': [], 'second': []}

    def to_dict(self):
        return deepcopy({
            "acting_player_id": self.acting_player_id,
            "id_to_round_id": self.id_to_round_id,
            "points": self.points,
            "gift_cards": self.gift_cards,
            "action_cards": self.action_cards,
            "decision_cards_1_2": self.decision_cards_1_2,
            "decision_cards_2_2": self.decision_cards_2_2,
            "geisha_preferences": self.geisha_preferences,
            "num_cards": self.num_cards,
            "round_moves": self.round_moves
        })


class GameEnvExternal(object):

    def __init__(self, players):
        self.players = players
        if str(players['first']) == 'Human':
            self.human = 'first'
            self.agent = 'second'
        else:
            self.human = 'second'
            self.agent = 'first'
        self.winner = None
        self.num_wins = {'first': 0, 'second': 0}
        self.round = 1

        # Public game info
        self.state = GameState()
        # Private player info
        self.private_info_sets = {'first': PrivateInfoSet(), 'second': PrivateInfoSet()}
        # Storing all the info of the active player. It is an object pair.
        # First element is GameState, second element is PrivateInfo.
        self.active_player_info_set = None

    def get_opp(self):
        return 'first' if self.state.acting_player_id == 'second' else 'second'

    def get_active_player_info_set(self):
        return deepcopy([self.state, self.private_info_sets[self.state.acting_player_id]])

    def parse_starting_hand(self):
        expected_length = 7 if (self.agent == 'first' and self.round % 2 == 1) or (self.agent == 'second' and self.round % 2 == 0) else 6
        while True:
            hand_str = input(f"Enter the agent's starting hand ({expected_length} digits, each 1–7): ").strip()
            if len(hand_str) != expected_length or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly {expected_length} digits.")
                continue
            hand = [int(c) for c in hand_str]
            if all(1 <= card <= 7 for card in hand):
                return hand
            print("Invalid card values. All digits must be between 1 and 7.")

    def draw_card(self):
        while True:
            hand_str = input(f"Draw a card and enter it here. Possible values 1–7: ").strip()
            if len(hand_str) != 1 or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly 1 digits.")
                continue
            if 1 <= int(hand_str) <= 7:
                return int(hand_str)
            print("Invalid card value. PLease enter a digit between 1 and 7.")

    def reveal_human_stash(self):
        while True:
            hand_str = input(f"PLease let me know human cash. Possible values 1–7: ").strip()
            if len(hand_str) != 1 or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly 1 digits.")
                continue
            if 1 <= int(hand_str) <= 7:
                return int(hand_str)
            print("Invalid card value. PLease enter a digit between 1 and 7.")

    def card_play_init(self):
        self.private_info_sets[self.agent].hand_cards = card_list_to_inner(self.parse_starting_hand())
        if self.state.acting_player_id == self.agent:
            self.private_info_sets[self.state.acting_player_id].moves = self.get_moves()
            self.active_player_info_set = self.get_active_player_info_set()

    def get_winner(self):
        return self.winner

    def update_geisha_preferences(self):
        human_stash = self.reveal_human_stash()
        self.private_info_sets[self.human].stashed_card = [0, 0, 0, 0, 0, 0, 0]
        self.private_info_sets[self.human].stashed_card[human_stash - 1] += 1
        first_gifts = _add_cards(self.state.gift_cards['first'], self.private_info_sets['first'].stashed_card)
        second_gifts = _add_cards(self.state.gift_cards['second'], self.private_info_sets['second'].stashed_card)
        for i in range(7):
            if first_gifts[i] > second_gifts[i] or (
                    first_gifts[i] == second_gifts[i] and self.state.geisha_preferences['first'][i] == 1):
                self.state.geisha_preferences['first'][i] = 1
            else:
                self.state.geisha_preferences['first'][i] = 0
            if first_gifts[i] < second_gifts[i] or (
                    first_gifts[i] == second_gifts[i] and self.state.geisha_preferences['second'][i] == 1):
                self.state.geisha_preferences['second'][i] = 1
            else:
                self.state.geisha_preferences['second'][i] = 0

    def is_game_ended(self):
        first_geisha_win = 0
        first_geisha_points = 0
        second_geisha_win = 0
        second_geisha_points = 0
        for i in range(7):
            if self.state.geisha_preferences['first'][i] == 1:
                first_geisha_win += 1
                first_geisha_points += self.state.points[i]
            if self.state.geisha_preferences['second'][i] == 1:
                second_geisha_win += 1
                second_geisha_points += self.state.points[i]
        if 11 <= first_geisha_points:
            return 'first'
        if 11 <= second_geisha_points:
            return 'second'
        if 4 <= first_geisha_win:
            return 'first'
        if 4 <= second_geisha_win:
            return 'second'
        return None

    def set_winner(self):
        winner_player = self.is_game_ended()
        if winner_player:
            self.winner = winner_player
            self.num_wins[self.winner] += 1

    def get_moves(self):
        mg = MovesGener(self.private_info_sets[self.state.acting_player_id].hand_cards,
                        self.state.action_cards[self.state.acting_player_id],
                        self.state.decision_cards_1_2,
                        self.state.decision_cards_2_2)
        moves = mg.gen_moves()
        return moves

    def step(self):
        curr = self.state.acting_player_id
        opp = self.get_opp()
        info = self.private_info_sets[curr]
        self.active_player_info_set = self.get_active_player_info_set()
        move = self.players[curr].act(self.active_player_info_set)
        if curr == self.agent:
            assert move in self.active_player_info_set[1].moves
        draw_card = True
        if move[0] == TYPE_0_STASH:
            self.state.round_moves[curr].append([move[0], [0] * 7])
            self.state.action_cards[curr][0] = 0
            if curr == self.agent:
                info.hand_cards = _sub_cards(info.hand_cards, move[1])
                info.stashed_card = move[1]
            self.state.num_cards[curr] -= 1
            self.state.acting_player_id = opp
        if move[0] == TYPE_1_TRASH:
            self.state.round_moves[curr].append([move[0], [0] * 7])
            self.state.action_cards[curr][1] = 0
            if curr == self.agent:
                info.hand_cards = _sub_cards(info.hand_cards, move[1])
                info.trashed_cards = move[1]
            self.state.num_cards[curr] -= 2
            self.state.acting_player_id = opp
        if move[0] == TYPE_2_CHOOSE_1_2:
            self.state.round_moves[curr].append(move)
            self.state.action_cards[curr][2] = 0
            if curr == self.agent:
                info.hand_cards = _sub_cards(info.hand_cards, move[1])
            self.state.decision_cards_1_2 = move[1]
            self.state.num_cards[curr] -= 3
            self.state.acting_player_id = opp
            draw_card = False
        if move[0] == TYPE_3_CHOOSE_2_2:
            self.state.round_moves[curr].append(move)
            self.state.action_cards[curr][3] = 0
            if curr == self.agent:
                info.hand_cards = _sub_cards(info.hand_cards, move[1][0])
                info.hand_cards = _sub_cards(info.hand_cards, move[1][1])
            self.state.decision_cards_2_2 = move[1]
            self.state.num_cards[curr] -= 4
            self.state.acting_player_id = opp
            draw_card = False
        if move[0] == TYPE_4_RESOLVE_1_2:
            self.state.round_moves[curr].append(move)
            self.state.decision_cards_1_2 = None
            self.state.gift_cards[curr] = _add_cards(self.state.gift_cards[curr], move[1][0])
            self.state.gift_cards[opp] = _add_cards(self.state.gift_cards[opp], move[1][1])
        if move[0] == TYPE_5_RESOLVE_2_2:
            self.state.round_moves[curr].append(move)
            self.state.decision_cards_2_2 = None
            self.state.gift_cards[curr] = _add_cards(self.state.gift_cards[curr], move[1][0])
            self.state.gift_cards[opp] = _add_cards(self.state.gift_cards[opp], move[1][1])

        if len(self.state.round_moves['first']) + len(self.state.round_moves['second']) == 12:
            assert self.state.num_cards['first'] == 0 and self.state.num_cards['second'] == 0
            self.update_geisha_preferences()
            self.set_winner()
            if self.winner is None:
                next_geisha_preferences = deepcopy(self.state.geisha_preferences)
                self.round += 1
                self.state = GameState()
                self.state.geisha_preferences = next_geisha_preferences
                if self.round % 2 == 0:
                    self.state.acting_player_id = 'second'
                    self.state.id_to_round_id = {'first': 'second', 'second': 'first'}
                    self.state.num_cards = {'first': 6, 'second': 7}
                self.private_info_sets = {'first': PrivateInfoSet(), 'second': PrivateInfoSet()}
                self.card_play_init()
        else:
            info = self.private_info_sets[self.state.acting_player_id]
            if draw_card:
                self.state.num_cards[self.state.acting_player_id] += 1
                if self.state.acting_player_id == self.agent:
                    card = self.draw_card()
                    info.hand_cards[card - 1] += 1
            if self.state.acting_player_id == self.agent:
                info.moves = self.get_moves()
                self.active_player_info_set = self.get_active_player_info_set()


class PrivateInfoSet(object):
    """
    PrivateInfoSet contains the private data of the players.
    """

    def __init__(self):
        # The hand cards of the current player. A list.
        self.hand_cards = None
        # The stashed card of the current player
        self.stashed_card = None
        # The two trashed cards of the current player
        self.trashed_cards = None
        # The legal moves. It is a list of list
        self.moves = None

    def to_dict(self):
        return deepcopy({
            "hand_cards": self.hand_cards,
            "stashed_card": self.stashed_card,
            "trashed_cards": self.trashed_cards
        })
