from copy import deepcopy
from . import move_detector as md, move_selector as ms
from .move_generator import MovesGener

class GameEnv(object):

    def __init__(self, players):
        self.players = players
        self.deck = None
        self.winner = None
        self.acting_player_position = 'first'
        self.section = 1
        self.move_history = {'first': [], 'second': []}
        self.num_wins = {'first': 0, 'second': 0}
        self.info_sets = {'first': InfoSet('first'), 'second': InfoSet('second')}
        self.game_infoset = None

    def card_play_init(self, card_play_data):
        self.info_sets['first'].player_hand_cards = card_play_data['first']
        self.info_sets['second'].player_hand_cards = card_play_data['second']
        self.deck = card_play_data['deck']
        self.game_infoset = self.get_infoset()

    def game_done(self):
        if len(self.info_sets['first'].move_history[1]) == 6:
            self.winner = 'first' # TODO
            self.update_num_wins()

    def update_num_wins(self):
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
        if not self.winner:
            # TODO fix
            self.game_infoset = self.get_infoset()

    #def update_acting_player_hand_cards(self, action):
    #    if action != []:
    #        for card in action:
    #            self.info_sets[
    #                self.acting_player_position].player_hand_cards.remove(card)
    #        self.info_sets[self.acting_player_position].player_hand_cards.sort()

    def get_legal_actions(self):
        mg = MovesGener(
            self.info_sets[self.acting_player_position].player_hand_cards)

        moves = list()
        for m in moves:
            m.sort()

        return moves

    def reset(self):
        self.move_history = {'first': [], 'second': []}
        self.winner = None
        self.acting_player_position = None
        self.info_sets = {'first': InfoSet('first'), 'second': InfoSet('second')}

    def get_infoset(self):
        self.info_sets[self.acting_player_position].legal_actions = self.get_legal_actions()

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
        # The legal actions. It is a list of list
        self.legal_actions = None

        # Opp info
        # The hand cards of the opp player. A list.
        self.opp_hand_cards = None
        # The stashed card of the current player
        self.opp_stashed_card = None
        # The two trashed cards of the current player
        self.opp_trash_cards = None
        # The unknown cards of the deck for the current player
        self.opp_unknown_cards = None
