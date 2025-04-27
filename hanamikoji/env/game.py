from copy import deepcopy
from .move_generator import MovesGener


class GameEnv(object):

    def __init__(self, players):
        self.players = players
        self.deck = None
        self.winner = None

        self.acting_player_id = 'first'
        self.id_to_round_position = {'first': 'first', 'second': 'second'}
        self.round = 1
        self.num_wins = {'first': 0, 'second': 0}
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
        # The number of cards left for each player.
        self.num_cards_left = {'first': 7, 'second': 6}
        # Contains two lists. First list is the round starter moves, the other list is for round second moves
        self.round_actions = {'first': [], 'second': []}

        # TODO clarify what are these
        self.info_sets = {'first': InfoSet('first', 'first'), 'second': InfoSet('second', 'second')}
        self.game_infoset = None

    def card_play_init(self, card_play_data):
        self.info_sets['first'].player_hand_cards = card_play_data['first']
        self.info_sets['second'].player_hand_cards = card_play_data['second']
        self.deck = card_play_data['deck']
        self.game_infoset = self.get_infoset()

    def game_done(self):
        if self.num_cards_left['first'] == 0 and self.num_cards_left['second'] == 0:
            winner_player = self.is_game_ended()
            if winner_player:
                self.winner = winner_player
                self.num_wins[self.winner] += 1

    def get_winner(self):
        return self.winner

    def update_geisha_preferences(self):
        first_gifts = [a + b for a, b in zip(self.gift_cards['first'], self.info_sets['first'].player_stashed_card)]
        second_gifts = [a + b for a, b in zip(self.gift_cards['second'], self.info_sets['second'].player_stashed_card)]
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

    # def update_acting_player_hand_cards(self, action):
    #    if action != []:
    #        for card in action:
    #            self.info_sets[
    #                self.acting_player_position].player_hand_cards.remove(card)
    #        self.info_sets[self.acting_player_position].player_hand_cards.sort()

    def get_legal_actions(self):
        mg = MovesGener(self.info_sets[self.acting_player_position].player_hand_cards,
                        self.info_sets[self.acting_player_position].legal_actions, )
        moves = mg.gen_moves()
        return moves

    def reset(self):
        self.move_history = {'first': [], 'second': []}
        self.winner = None
        self.acting_player_id = 'first'
        self.info_sets = {'first': InfoSet('first', 'first'), 'second': InfoSet('second', 'second')}

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
    The game state is described as infoset, which contains the private data of the players.
    """

    def __init__(self, player_id, player_round_position):
        # The hand cards of the current player. A list.
        self.player_hand_cards = None
        # The stashed card of the current player
        self.player_stashed_card = None
        # The two trashed cards of the current player
        self.player_trashed_cards = None
        # The legal actions. It is a list of list
        self.legal_actions = None
