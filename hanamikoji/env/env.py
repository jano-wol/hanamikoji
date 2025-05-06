import numpy as np

from hanamikoji.env.game import GameEnv, get_card_play_data
from hanamikoji.env.move_generator import *

ROUND_MOVES = 12
MOVE_VECTOR_SIZE = 63
HIST_MOVE_VECTOR_SIZE = 64
X_FEATURE_SIZE = 169
X_NO_MOVE_FEATURE_SIZE = (X_FEATURE_SIZE - MOVE_VECTOR_SIZE)

def my_move2array(move):
    ret = np.zeros(MOVE_VECTOR_SIZE, dtype=np.int8)
    if move[0] == TYPE_0_STASH:
        ret[:7] = move[1]
    if move[0] == TYPE_1_TRASH:
        ret[7:14] = move[1]
    if move[0] == TYPE_2_CHOOSE_1_2:
        ret[14:21] = move[1]
    if move[0] == TYPE_3_CHOOSE_2_2:
        ret[21:28] = move[1][0]
        ret[28:35] = move[1][1]
    if move[0] == TYPE_4_RESOLVE_1_2:
        ret[35:42] = move[1][0]
        ret[42:49] = move[1][1]
    if move[0] == TYPE_5_RESOLVE_2_2:
        ret[49:56] = move[1][0]
        ret[56:] = move[1][1]
    return ret

class Env:
    """
    Hanamikoji multi-agent wrapper
    """

    def __init__(self, objective):
        """
        Objective is wp/adp/logadp. Here, we use dummy agents.
        This is because, in the original game, the players
        are `in` the game. Here, we want to isolate
        players and environments to have a more gym style
        interface. To achieve this, we use dummy players
        to play. For each move, we tell the corresponding
        dummy player which action to play, then the player
        will perform the actual action in the game engine.
        """
        self.objective = objective

        # Initialize players
        # We use two dummy players
        self.players = {}
        for player_id in ['first', 'second']:
            self.players[player_id] = DummyAgent(player_id)

        # Initialize the internal environment
        self._env = GameEnv(self.players)

        self.infoset = None

    def reset(self):
        """
        Every time reset is called, the environment
        will be re-initialized with a new deck of cards.
        This function is usually called when a game is over.
        """
        self._env.reset()
        card_play_data = get_card_play_data()
        self._env.card_play_init(card_play_data)
        # First element is GameState, second element is PrivateInfo.
        self.infoset = self._active_player_info_set()
        return get_obs(self.infoset)

    def step(self, move):
        """
        Step function takes as input the move, which
        is a list of integers, and output the next observation,
        reward, and a Boolean variable indicating whether the
        current game is finished. It also returns an empty
        dictionary that is reserved to pass useful information.
        """
        assert move in self.infoset[1].moves
        self.players[self._acting_player_id()].set_move(move)
        self._env.step()
        self.infoset = self._active_player_info_set()
        done = False
        reward = 0.0
        if self._game_over():
            done = True
            reward = self._get_reward()
            obs = None
        else:
            obs = get_obs(self.infoset)
        return obs, reward, done, {}

    def _get_reward(self):
        """
        This function is called in the end of each
        game. It returns either 1/-1 for win/loss,
        or ADP, i.e., every bomb will double the score.
        """
        winner = self._game_winner()
        if winner == 'first':
            return 1.0
        else:
            return -1.0


    def _active_player_info_set(self):
        """
        Here, active_player_info_set is defined as all the information available for the active player
        """
        return self._env.active_player_info_set

    def _game_winner(self):
        """
        A string of landlord/peasants
        """
        return self._env.get_winner()


    def _acting_player_id(self):
        """
        The player that is active. It can be 'first' or 'second'
        """
        return self._env.state.acting_player_id


    def _game_over(self):
        """
        Returns a Boolean
        """
        return self._env.winner is not None


class DummyAgent(object):
    """
    Dummy agent is designed to easily interact with the
    game engine. The agent will first be told what move
    to perform. Then the environment will call this agent
    to perform the actual move. This can help us to
    isolate environment and agents towards a gym like
    interface.
    """

    def __init__(self, player_id):
        self.player_id = player_id
        self.move = None

    def act(self, infoset):
        """
        Simply return the move that is set previously.
        """
        assert self.move in infoset[1].moves
        return self.move

    def set_move(self, move):
        """
        The environment uses this function to tell the dummy agent what to do.
        """
        self.move = move


def _get_one_hot_array(num_left_cards):
    one_hot = np.zeros(7, dtype=np.int8)
    if num_left_cards > 0:
        one_hot[num_left_cards - 1] = 1
    return one_hot


def _cards2array(list_cards):
    return np.array(list_cards, dtype=np.int8)

def hist_move2array(hist_move, round_start):
    move_id = hist_move[0]
    move = hist_move[1]
    ret = np.zeros(HIST_MOVE_VECTOR_SIZE, dtype=np.int8)
    if move[0] == TYPE_0_STASH:
        # Not public info, in lstm we do not encode it
        ret[:7] = [1] * 7
    if move[0] == TYPE_1_TRASH:
        # Not public info, in lstm we do not encode it
        ret[7:14] = [1] * 7
    if move[0] == TYPE_2_CHOOSE_1_2:
        ret[14:21] = move[1]
    if move[0] == TYPE_3_CHOOSE_2_2:
        ret[21:28] = move[1][0]
        ret[28:35] = move[1][1]
    if move[0] == TYPE_4_RESOLVE_1_2:
        ret[35:42] = move[1][0]
        ret[42:49] = move[1][1]
    if move[0] == TYPE_5_RESOLVE_2_2:
        ret[49:56] = move[1][0]
        ret[56:63] = move[1][1]
    id_bit = 1 if round_start == move_id else 0
    ret[63] = id_bit
    return ret


def _encode_round_moves(round_moves):
    z = np.zeros((ROUND_MOVES, HIST_MOVE_VECTOR_SIZE))
    l = len(round_moves)
    for i in range(l):
        z[i, :] = hist_move2array(round_moves[i], round_moves[0][0])
    return z


def _create_batch(a_list, num):
    return np.broadcast_to(a_list, (num, len(a_list)))


def get_obs(infoset):
    """
    This function obtains observations with imperfect information
    from the infoset.
    
    This function will return dictionary named `obs`. It contains
    several fields. These fields will be used to train the model.
    One can play with those features to improve the performance.

    `id` is a string defining the global role of player encoding the infoset ('first' or 'second')

    'round_id' is a string defining the round local role of the player encoding the infoset ('first' or 'second')

    'moves' is the legal moves

    `x_batch` is a batch of features (excluding opponent historical moves). It also encodes the available move features.
    shape = (num_moves, X_FEATURE_SIZE)

    `x_no_move`: the features (excluding the historical moves and the action features). It is not a batch.
    shape = (X_NO_MOVE_FEATURE_SIZE)

    `z_batch` is a batch of features encoding the historical moves of the round.
    shape = (num_moves, ROUND_MOVES, HIST_MOVE_VECTOR_SIZE)

    `z`: same as z_batch but not a batch.
    shape = (ROUND_MOVES, HIST_MOVE_VECTOR_SIZE)

    """
    num_moves = len(infoset[1].moves)
    curr = infoset[0].acting_player_id
    opp = 'second' if curr == 'first' else 'first'

    # FEATURE 1 -- Geisha points. SIZE=7
    geisha_points = np.array([2, 2, 2, 3, 3, 4, 5], dtype=np.int8)
    geisha_points_batch = _create_batch(geisha_points, num_moves)

    # FEATURE 2 -- Geisha preferences. SIZE=7
    geisha_preferences = _cards2array(infoset[0].geisha_preferences[curr]) - _cards2array(infoset[0].geisha_preferences[opp])
    geisha_preferences_batch = _create_batch(geisha_preferences, num_moves)

    # FEATURE 3 -- Hand cards. SIZE=7
    hand_cards = _cards2array(infoset[1].hand_cards)
    hand_cards_batch = _create_batch(hand_cards, num_moves)

    # FEATURE 4 -- Stashed card. SIZE=7
    stashed_card = _cards2array(infoset[1].stashed_card or [0] * 7)
    stashed_card_batch = _create_batch(stashed_card, num_moves)

    # FEATURE 5 -- Trashed cards. SIZE=7
    trashed_cards = _cards2array(infoset[1].trashed_cards or [0] * 7)
    trashed_cards_batch = _create_batch(trashed_cards, num_moves)

    # FEATURE 6 -- Decision cards 1_2. SIZE=7
    decision_cards_1_2 = _cards2array(infoset[0].decision_cards_1_2 or [0] * 7)
    decision_cards_1_2_batch = _create_batch(decision_cards_1_2, num_moves)

    # FEATURE 7 -- Decision cards 2_2 first. SIZE=7
    decision_cards_2_2_1 = _cards2array(
        (infoset[0].decision_cards_2_2[0] if infoset[0].decision_cards_2_2 else [0] * 7))
    decision_cards_2_2_1_batch = _create_batch(decision_cards_2_2_1, num_moves)

    # FEATURE 8 -- Decision cards 2_2 second. SIZE=7
    decision_cards_2_2_2 = _cards2array(
        (infoset[0].decision_cards_2_2[1] if infoset[0].decision_cards_2_2 else [0] * 7))
    decision_cards_2_2_2_batch = _create_batch(decision_cards_2_2_2, num_moves)

    # FEATURE 9 -- Action cards. SIZE=4
    action_cards = np.array(infoset[0].action_cards[curr], dtype=np.int8)
    action_cards_batch = _create_batch(action_cards, num_moves)

    # FEATURE 10 -- Action cards opp. SIZE=4
    action_cards_opp = np.array(infoset[0].action_cards[opp], dtype=np.int8)
    action_cards_opp_batch = _create_batch(action_cards_opp, num_moves)

    # FEATURE 11 -- Gift cards. SIZE=7
    gift_cards = _cards2array(infoset[0].gift_cards[curr])
    gift_cards_batch = _create_batch(gift_cards, num_moves)

    # FEATURE 12 -- Gift cards opp. SIZE=7
    gift_cards_opp = _cards2array(infoset[0].gift_cards[opp])
    gift_cards_opp_batch = _create_batch(gift_cards_opp, num_moves)

    # FEATURE 13 -- All gift cards. SIZE=7
    all_gift_cards = gift_cards + stashed_card
    all_gift_cards_batch = _create_batch(all_gift_cards, num_moves)

    # FEATURE 14 -- Number of cards (one-hot). SIZE=7
    num_cards = _get_one_hot_array(infoset[0].num_cards[curr])
    num_cards_batch = _create_batch(num_cards, num_moves)

    # FEATURE 15 -- Number of cards opp (one-hot). SIZE=7
    num_cards_opp = _get_one_hot_array(infoset[0].num_cards[opp])
    num_cards_opp_batch = _create_batch(num_cards_opp, num_moves)

    # FEATURE 16 -- Unknown cards. (Calc uses that geisha points == number of geisha cards in the deck.) SIZE=7
    unknown_cards = geisha_points - hand_cards - all_gift_cards - trashed_cards - gift_cards_opp - decision_cards_1_2 - decision_cards_2_2_1 - decision_cards_2_2_2
    unknown_cards_batch = _create_batch(unknown_cards, num_moves)

    move_batch = np.zeros((num_moves, MOVE_VECTOR_SIZE))
    for j, move in enumerate(infoset[1].moves):
        move_batch[j, :] = my_move2array(move)

    x_batch = np.empty((num_moves, X_FEATURE_SIZE), dtype=np.int8)
    x_batch[:, 0:7] = geisha_points_batch
    x_batch[:, 7:14] = geisha_preferences_batch
    x_batch[:, 14:21] = hand_cards_batch
    x_batch[:, 21:28] = stashed_card_batch
    x_batch[:, 28:35] = trashed_cards_batch
    x_batch[:, 35:42] = decision_cards_1_2_batch
    x_batch[:, 42:49] = decision_cards_2_2_1_batch
    x_batch[:, 49:56] = decision_cards_2_2_2_batch
    x_batch[:, 56:60] = action_cards_batch
    x_batch[:, 60:64] = action_cards_opp_batch
    x_batch[:, 64:71] = gift_cards_batch
    x_batch[:, 71:78] = gift_cards_opp_batch
    x_batch[:, 78:85] = all_gift_cards_batch
    x_batch[:, 85:92] = num_cards_batch
    x_batch[:, 92:99] = num_cards_opp_batch
    x_batch[:, 99:106] = unknown_cards_batch
    x_batch[:, 106:] = move_batch

    x_no_move = np.empty(X_NO_MOVE_FEATURE_SIZE, dtype=np.int8)
    x_no_move[0:7] = geisha_points
    x_no_move[7:14] = geisha_preferences
    x_no_move[14:21] = hand_cards
    x_no_move[21:28] = stashed_card
    x_no_move[28:35] = trashed_cards
    x_no_move[35:42] = decision_cards_1_2
    x_no_move[42:49] = decision_cards_2_2_1
    x_no_move[49:56] = decision_cards_2_2_2
    x_no_move[56:60] = action_cards
    x_no_move[60:64] = action_cards_opp
    x_no_move[64:71] = gift_cards
    x_no_move[71:78] = gift_cards_opp
    x_no_move[78:85] = all_gift_cards
    x_no_move[85:92] = num_cards
    x_no_move[92:99] = num_cards_opp
    x_no_move[99:106] = unknown_cards

    z = _encode_round_moves(infoset[0].round_moves)
    z_batch = np.broadcast_to(z, (num_moves, *z.shape))
    obs = {
        'id': infoset[0].acting_player_id,
        'round_id': infoset[0].id_to_round_id[infoset[0].acting_player_id],
        'moves': infoset[1].moves,
        'x_batch': x_batch.astype(np.float32),
        'x_no_move': x_no_move.astype(np.int8),
        'z': z.astype(np.int8),
        'z_batch': z_batch.astype(np.float32)
    }
    return obs
