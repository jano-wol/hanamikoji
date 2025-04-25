from copy import deepcopy
from . import move_detector as md, move_selector as ms
from .move_generator import MovesGener

EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
                    8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q',
                    13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}

RealCard2EnvCard = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                    '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12,
                    'K': 13, 'A': 14, '2': 17, 'X': 20, 'D': 30}

class GameEnv(object):

    def __init__(self, players):
        self.players = players
        self.deck = None
        self.winner = None
        self.acting_player_position = 'first'
        self.section = 1
        self.move_history = {'first': [], 'second': []}
        self.num_wins = {'first': 0, 'second': 0}
        self.num_scores = {'first': 0, 'second': 0}
        self.info_sets = {'first': InfoSet('first'), 'second': InfoSet('second')}
        self.game_infoset = None

    def card_play_init(self, card_play_data):
        self.info_sets['first'].player_hand_cards = card_play_data['first']
        self.info_sets['second'].player_hand_cards = card_play_data['second']
        self.game_infoset = self.get_infoset()

    def game_done(self):
        if len(self.info_sets['first'].move_history[1]) == 6:
            self.winner = 'first' # TODO
            self.update_num_wins_scores()

    def update_num_wins_scores(self):
        self.num_wins[self.winner] += 1

    def get_winner(self):
        return self.winner

    def step(self):
        action = self.players[self.acting_player_position].act(self.game_infoset)
        assert action in self.game_infoset.legal_actions
        self.move_history[self.acting_player_position].append(action)
        # TODO update
        # self.update_acting_player_hand_cards(action)
        # self.played_cards[self.acting_player_position] += action
        self.game_done()
        if not self.game_over:
            self.get_acting_player_position()
            self.game_infoset = self.get_infoset()

    def get_last_move(self):
        last_move = []
        if len(self.card_play_action_seq) != 0:
            if len(self.card_play_action_seq[-1]) == 0:
                last_move = self.card_play_action_seq[-2]
            else:
                last_move = self.card_play_action_seq[-1]

        return last_move

    def update_acting_player_hand_cards(self, action):
        if action != []:
            for card in action:
                self.info_sets[
                    self.acting_player_position].player_hand_cards.remove(card)
            self.info_sets[self.acting_player_position].player_hand_cards.sort()

    def get_legal_card_play_actions(self):
        mg = MovesGener(
            self.info_sets[self.acting_player_position].player_hand_cards)

        action_sequence = self.card_play_action_seq

        rival_move = []
        if len(action_sequence) != 0:
            if len(action_sequence[-1]) == 0:
                rival_move = action_sequence[-2]
            else:
                rival_move = action_sequence[-1]

        rival_type = md.get_move_type(rival_move)
        rival_move_type = rival_type['type']
        rival_move_len = rival_type.get('len', 1)
        moves = list()

        if rival_move_type == md.TYPE_0_PASS:
            moves = mg.gen_moves()

        elif rival_move_type == md.TYPE_1_SINGLE:
            all_moves = mg.gen_type_1_single()
            moves = ms.filter_type_1_single(all_moves, rival_move)

        elif rival_move_type == md.TYPE_2_PAIR:
            all_moves = mg.gen_type_2_pair()
            moves = ms.filter_type_2_pair(all_moves, rival_move)

        elif rival_move_type == md.TYPE_3_TRIPLE:
            all_moves = mg.gen_type_3_triple()
            moves = ms.filter_type_3_triple(all_moves, rival_move)

        elif rival_move_type == md.TYPE_4_BOMB:
            all_moves = mg.gen_type_4_bomb() + mg.gen_type_5_king_bomb()
            moves = ms.filter_type_4_bomb(all_moves, rival_move)

        elif rival_move_type == md.TYPE_5_KING_BOMB:
            moves = []

        elif rival_move_type == md.TYPE_6_3_1:
            all_moves = mg.gen_type_6_3_1()
            moves = ms.filter_type_6_3_1(all_moves, rival_move)

        elif rival_move_type == md.TYPE_7_3_2:
            all_moves = mg.gen_type_7_3_2()
            moves = ms.filter_type_7_3_2(all_moves, rival_move)

        elif rival_move_type == md.TYPE_8_SERIAL_SINGLE:
            all_moves = mg.gen_type_8_serial_single(repeat_num=rival_move_len)
            moves = ms.filter_type_8_serial_single(all_moves, rival_move)

        elif rival_move_type == md.TYPE_9_SERIAL_PAIR:
            all_moves = mg.gen_type_9_serial_pair(repeat_num=rival_move_len)
            moves = ms.filter_type_9_serial_pair(all_moves, rival_move)

        elif rival_move_type == md.TYPE_10_SERIAL_TRIPLE:
            all_moves = mg.gen_type_10_serial_triple(repeat_num=rival_move_len)
            moves = ms.filter_type_10_serial_triple(all_moves, rival_move)

        elif rival_move_type == md.TYPE_11_SERIAL_3_1:
            all_moves = mg.gen_type_11_serial_3_1(repeat_num=rival_move_len)
            moves = ms.filter_type_11_serial_3_1(all_moves, rival_move)

        elif rival_move_type == md.TYPE_12_SERIAL_3_2:
            all_moves = mg.gen_type_12_serial_3_2(repeat_num=rival_move_len)
            moves = ms.filter_type_12_serial_3_2(all_moves, rival_move)

        elif rival_move_type == md.TYPE_13_4_2:
            all_moves = mg.gen_type_13_4_2()
            moves = ms.filter_type_13_4_2(all_moves, rival_move)

        elif rival_move_type == md.TYPE_14_4_22:
            all_moves = mg.gen_type_14_4_22()
            moves = ms.filter_type_14_4_22(all_moves, rival_move)

        if rival_move_type not in [md.TYPE_0_PASS,
                                   md.TYPE_4_BOMB, md.TYPE_5_KING_BOMB]:
            moves = moves + mg.gen_type_4_bomb() + mg.gen_type_5_king_bomb()

        if len(rival_move) != 0:  # rival_move is not 'pass'
            moves = moves + [[]]

        for m in moves:
            m.sort()

        return moves

    def reset(self):
        self.move_history = []
        self.game_over = False
        self.acting_player_position = None
        self.player_utility_dict = None
        self.info_sets = {'first': InfoSet('first'),
                         'second': InfoSet('second')}

    def get_infoset(self):
        self.info_sets[
            self.acting_player_position].last_pid = self.last_pid

        self.info_sets[
            self.acting_player_position].legal_actions = \
            self.get_legal_card_play_actions()

        self.info_sets[
            self.acting_player_position].bomb_num = self.bomb_num

        self.info_sets[
            self.acting_player_position].last_move = self.get_last_move()

        self.info_sets[
            self.acting_player_position].last_two_moves = self.get_last_two_moves()

        self.info_sets[
            self.acting_player_position].last_move_dict = self.last_move_dict

        self.info_sets[self.acting_player_position].num_cards_left_dict = \
            {pos: len(self.info_sets[pos].player_hand_cards)
             for pos in ['landlord', 'landlord_up', 'landlord_down']}

        self.info_sets[self.acting_player_position].other_hand_cards = []
        for pos in ['landlord', 'landlord_up', 'landlord_down']:
            if pos != self.acting_player_position:
                self.info_sets[
                    self.acting_player_position].other_hand_cards += \
                    self.info_sets[pos].player_hand_cards

        self.info_sets[self.acting_player_position].played_cards = \
            self.played_cards
        self.info_sets[self.acting_player_position].three_landlord_cards = \
            self.three_landlord_cards
        self.info_sets[self.acting_player_position].card_play_action_seq = \
            self.card_play_action_seq

        self.info_sets[
            self.acting_player_position].all_handcards = \
            {pos: self.info_sets[pos].player_hand_cards
             for pos in ['first', 'second']}

        return deepcopy(self.info_sets[self.acting_player_position])

class InfoSet(object):
    """
    The game state is described as infoset, which
    includes all the information in the current situation,
    such as the hand cards of the three players, the
    historical moves, etc.
    """
    def __init__(self, player_position):
        # Common info
        # Global player position, first, second
        self.player_position = player_position
        # Player round position meaning that in the current round was started by player or not
        self.player_round_position = None
        # The public geisha gift cards of the current player.
        self.player_gift_cards = [0, 0, 0, 0, 0, 0, 0]
        # The public geisha gift cards of the opp player.
        self.opp_gift_cards = [0, 0, 0, 0, 0, 0, 0]
        # The possible action cards of the current player
        self.player_action_cards = [1, 1, 1, 1]
        # The possible action cards of the opp player
        self.opp_action_cards = [1, 1, 1, 1]
        # decision cards 1 - 2
        self.decision_cards_1_2 = [0, 0, 0, 0, 0, 0, 0]
        # decision cards 2 - 2
        self.decision_cards_2_2 = [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]
        # + 1 if current player is preferred, -1 if opp, otherwise 0
        self.geisha_preferences = [0, 0, 0, 0, 0, 0, 0]
        # The number of cards left for each player. It is a dict with str-->int
        self.num_cards_left_dict = [7, 6]
        # Contains two lists. First list is the round starter moves, the other list is for round second moves
        self.move_history = [[], []]

        # Curr player info
        # The hand cards of the current player. A list.
        self.player_hand_cards = None
        # The stashed card of the current player
        self.player_stashed_card = None
        # The two trashed cards of the current player
        self.player_trash_cards = None
        # The unknown cards of the deck for the current player
        self.player_unknown_cards = None

        # Opp info
        # The hand cards of the opp player. A list.
        self.opp_hand_cards = None
        # The stashed card of the current player
        self.opp_stashed_card = None
        # The two trashed cards of the current player
        self.opp_trash_cards = None
        # The unknown cards of the deck for the current player
        self.opp_unknown_cards = None
