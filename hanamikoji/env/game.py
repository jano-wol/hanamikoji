from copy import deepcopy
from .move_generator import *

def _add_cards(a, b):
    return [a + b for a, b in zip(a, b)]

def _sub_cards(a, b):
    return [a - b for a, b in zip(a, b)]

class GameEnv(object):

    def __init__(self, players):
        self.players = players
        self.deck = None
        self.winner = None
        self.num_wins = {'first': 0, 'second': 0}
        self.round = 1

        # 'first' and 'second' mean global first and second player unless otherwise stated
        self.acting_player_id = 'first'
        # Here keys mean global 'first' and 'second', values mean round local first and second (indicating eval model)
        self.id_to_round_position = {'first': 'first', 'second': 'second'}
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
        self.num_cards = {'first': 6, 'second': 6}
        # Contains the moves of the first and second players
        self.round_moves = {'first': [], 'second': []}

        # TODO clarify what are these
        self.info_sets = {'first': InfoSet(), 'second': InfoSet()}
        self.game_infoset = None

    def card_play_init(self, card_play_data):
        self.info_sets['first'].hand_cards = card_play_data['first']
        self.info_sets['second'].hand_cards = card_play_data['second']
        self.deck = card_play_data['deck']
        self.game_infoset = self.get_infoset()

    def get_winner(self):
        return self.winner

    def update_geisha_preferences(self):
        first_gifts = _add_cards(self.gift_cards['first'], self.info_sets['first'].stashed_card)
        second_gifts = _add_cards(self.gift_cards['second'], self.info_sets['second'].stashed_card)
        self.geisha_preferences = {'first': [0, 0, 0, 0, 0, 0, 0], 'second': [0, 0, 0, 0, 0, 0, 0]}
        for i in range(7):
            if first_gifts[i] > second_gifts[i] or (
                    first_gifts[i] == second_gifts[i] and self.geisha_preferences['first'] == 1):
                self.geisha_preferences['first'][i] = 1
            if first_gifts[i] < second_gifts[i] or (
                    first_gifts[i] == second_gifts[i] and self.geisha_preferences['second'] == 1):
                self.geisha_preferences['second'][i] = 1

    def is_game_ended(self):
        first_geisha_win = 0
        first_geisha_points = 0
        second_geisha_win = 0
        second_geisha_points = 0
        for i in range(7):
            if self.geisha_preferences['first'][i] == 1:
                first_geisha_win += 1
                first_geisha_points += self.points[i]
            if self.geisha_preferences['second'][i] == 1:
                second_geisha_win += 1
                second_geisha_points += self.points[i]
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
        mg = MovesGener(self.info_sets[self.acting_player_id].hand_cards,
                        self.action_cards[self.acting_player_id], self.decision_cards_1_2, self.decision_cards_2_2)
        moves = mg.gen_moves()
        return moves

    def step(self):
        info = self.info_sets[self.acting_player_id]
        opp = 'first' if self.acting_player_id == 'second' else 'second'
        if self.decision_cards_1_2 is None and self.decision_cards_2_2 is None:
            info.hand_cards[self.deck[0]] += 1
            self.num_cards[self.acting_player_id] += 1
            self.deck.pop(0)

        move = self.players[self.acting_player_id].act(self.game_infoset)
        assert move in self.game_infoset.moves

        self.round_moves[self.acting_player_id].append(move)
        if move[0] == TYPE_0_STASH:
            self.action_cards[self.acting_player_id][0] = 0
            info.hand_cards = _sub_cards(info.hand_cards, move[1])
            info.stashed_cards = move[1]
            self.num_cards[self.acting_player_id] -= 1
        if move[1] == TYPE_1_TRASH:
            self.action_cards[self.acting_player_id][1] = 0
            info.hand_cards = _sub_cards(info.hand_cards, move[1])
            info.trashed_cards = move[1]
            self.num_cards[self.acting_player_id] -= 2
        if move[2] == TYPE_2_CHOOSE_1_2:
            self.action_cards[self.acting_player_id][2] = 0
            info.hand_cards = _sub_cards(info.hand_cards, move[1])
            self.decision_cards_1_2 = move[1]
            self.num_cards[self.acting_player_id] -= 3
        if move[3] == TYPE_3_CHOOSE_2_2:
            self.action_cards[self.acting_player_id][3] = 0
            info.hand_cards = _sub_cards(info.hand_cards, move[1][0])
            info.hand_cards = _sub_cards(info.hand_cards, move[1][1])
            self.decision_cards_2_2 = move[1]
            self.num_cards[self.acting_player_id] -= 4
        if move[4] == TYPE_4_RESOLVE_1_2:
            self.decision_cards_1_2 = None
            self.gift_cards[self.acting_player_id] = _add_cards(self.gift_cards[self.acting_player_id], move[1][0])
            self.gift_cards[opp] = _add_cards(self.gift_cards[opp], move[1][1])
        if move[5] == TYPE_5_RESOLVE_2_2:
            self.decision_cards_2_2 = None
            self.gift_cards[self.acting_player_id] = _add_cards(self.gift_cards[self.acting_player_id], move[1][0])
            self.gift_cards[opp] = _add_cards(self.gift_cards[opp], move[1][1])
        self.acting_player_id = opp

        if len(self.round_moves['first']) + len(self.round_moves['second']) == 12:
            self.update_geisha_preferences()
            self.set_winner()

    def reset(self):
        self.move_history = {'first': [], 'second': []}
        self.winner = None
        self.acting_player_id = 'first'
        self.info_sets = {'first': InfoSet('first', 'first'), 'second': InfoSet('second', 'second')}

    def get_infoset(self):
        self.info_sets[self.acting_player_position].legal_actions = self.get_moves()

        self.info_sets[self.acting_player_position].num_cards_left_dict = \
            {pos: len(self.info_sets[pos].player_hand_cards)
             for pos in ['first', 'second']}

        self.info_sets[self.acting_player_position].other_hand_cards = []
        for pos in ['landlord', 'landlord_up', 'landlord_down']:
            if pos != self.acting_player_position:
                self.info_sets[
                    self.acting_player_position].other_hand_cards += \
                    self.info_sets[pos].player_hand_cards

        self.info_sets[self.acting_player_position].played_cards = \
            self.played_cards
        self.info_sets[
            self.acting_player_position].all_handcards = \
            {pos: self.info_sets[pos].player_hand_cards
             for pos in ['first', 'second']}

        return deepcopy(self.info_sets[self.acting_player_position])


class InfoSet(object):
    """
    The game state is described as infoset, which contains the private data of the players.
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
