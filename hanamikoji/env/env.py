from collections import Counter
import numpy as np

from hanamikoji.env.game import GameEnv, get_card_play_data
from hanamikoji.env.move_generator import *


class Env:
    """
    Hanamikoji multi-agent wrapper
    """

    def __init__(self, objective):
        """
        Objective is wp/adp/logadp. Here, we use dummy agents.
        This is because, in the orignial game, the players
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

    @property
    def _active_player_info_set(self):
        """
        Here, active_player_info_set is defined as all the information available for the active player
        """
        return self._env.active_player_info_set

    @property
    def _game_winner(self):
        """
        A string of landlord/peasants
        """
        return self._env.get_winner()

    @property
    def _acting_player_id(self):
        """
        The player that is active. It can be 'first' or 'second'
        """
        return self._env.state.acting_player_id

    @property
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


def get_obs(infoset):
    """
    This function obtains observations with imperfect information
    from the infoset. It has three branches since we encode
    different features for different positions.
    
    This function will return dictionary named `obs`. It contains
    several fields. These fields will be used to train the model.
    One can play with those features to improve the performance.

    `position` is a string that can be landlord/landlord_down/landlord_up

    `x_batch` is a batch of features (excluding the hisorical moves).
    It also encodes the action feature

    `z_batch` is a batch of features with hisorical moves only.

    `legal_actions` is the legal moves

    `x_no_action`: the features (exluding the hitorical moves and
    the action features). It does not have the batch dim.

    `z`: same as z_batch but not a batch.
    """
    if infoset.player_position == 'landlord':
        return _get_obs_landlord(infoset)
    elif infoset.player_position == 'landlord_up':
        return _get_obs_landlord_up(infoset)
    elif infoset.player_position == 'landlord_down':
        return _get_obs_landlord_down(infoset)
    else:
        raise ValueError('')


def _get_one_hot_array(num_left_cards):
    one_hot = np.zeros(7, dtype=np.int8)
    one_hot[num_left_cards - 1] = 1
    return one_hot


def _cards2array(list_cards):
    return np.array(list_cards, dtype=np.int8)


def _my_move2array(move):
    ret = np.zeros(63, dtype=np.int8)
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


def _opp_move2array(move):
    ret = np.zeros(63, dtype=np.int8)
    if move[0] == TYPE_0_STASH:
        ret[:7] = [1] * 7
    if move[0] == TYPE_1_TRASH:
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
        ret[56:] = move[1][1]
    return ret


def _action_seq_list2array(action_seq_list):
    """
    A utility function to encode the historical moves.
    We encode the historical 15 actions. If there is
    no 15 actions, we pad the features with 0. Since
    three moves is a round in DouDizhu, we concatenate
    the representations for each consecutive three moves.
    Finally, we obtain a 5x162 matrix, which will be fed
    into LSTM for encoding.
    """
    action_seq_array = np.zeros((len(action_seq_list), 54))
    for row, list_cards in enumerate(action_seq_list):
        action_seq_array[row, :] = _cards2array(list_cards)
    action_seq_array = action_seq_array.reshape(5, 162)
    return action_seq_array


def _process_action_seq(sequence, length=15):
    """
    A utility function encoding historical moves. We
    encode 15 moves. If there is no 15 moves, we pad
    with zeros.
    """
    sequence = sequence[-length:].copy()
    if len(sequence) < length:
        empty_sequence = [[] for _ in range(length - len(sequence))]
        empty_sequence.extend(sequence)
        sequence = empty_sequence
    return sequence


def create_batch(arr, num):
    return np.repeat(arr[np.newaxis, :], num, axis=0)


def _get_obs_landlord(infoset):
    """
    Obttain the landlord features. See Table 4 in
    https://arxiv.org/pdf/2106.06135.pdf
    """
    num_moves = len(infoset[1].moves)
    curr = infoset[0].state.acting_player_id
    opp = 'second' if curr == 'first' else 'first'

    # FEATURE 1 -- Geisha points
    geisha_points = np.array([2, 2, 2, 3, 3, 4, 5], dtype=np.int8)
    geisha_points_batch = create_batch(geisha_points, num_moves)

    # FEATURE 2 -- Geisha preferences
    geisha_preferences = _cards2array(infoset[0].state.geisha_preferences[curr]) - _cards2array(
        infoset[0].state.geisha_preferences[opp])
    geisha_preferences_batch = create_batch(geisha_preferences, num_moves)

    # FEATURE 3 -- Hand cards
    hand_cards = _cards2array(infoset[1].hand_cards)
    hand_cards_batch = create_batch(hand_cards, num_moves)

    # FEATURE 4 -- Stashed card
    stashed_card = _cards2array(infoset[1].stashed_card or [0] * 7)
    stashed_card_batch = create_batch(stashed_card, num_moves)

    # FEATURE 5 -- Trashed cards
    trashed_cards = _cards2array(infoset[1].trashed_cards or [0] * 7)
    trashed_cards_batch = create_batch(trashed_cards, num_moves)

    # FEATURE 6 -- Decision cards 1_2
    decision_cards_1_2 = _cards2array(infoset[0].state.decision_cards_1_2 or [0] * 7)
    decision_cards_1_2_batch = create_batch(decision_cards_1_2, num_moves)

    # FEATURE 7 -- Decision cards 2_2 first
    decision_cards_2_2_1 = _cards2array(
        (infoset[0].state.decision_cards_2_2[0] if infoset[0].state.decision_cards_2_2 else [0] * 7))
    decision_cards_2_2_1_batch = create_batch(decision_cards_2_2_1, num_moves)

    # FEATURE 8 -- Decision cards 2_2 second
    decision_cards_2_2_2 = _cards2array(
        (infoset[0].state.decision_cards_2_2[1] if infoset[0].state.decision_cards_2_2 else [0] * 7))
    decision_cards_2_2_2_batch = create_batch(decision_cards_2_2_2, num_moves)

    # FEATURE 9 -- Action cards
    action_cards = np.array(infoset[0].state.action_cards[curr], dtype=np.int8)
    action_cards_batch = create_batch(action_cards, num_moves)

    # FEATURE 10 -- Action cards opp
    action_cards_opp = np.array(infoset[0].state.action_cards[opp], dtype=np.int8)
    action_cards_opp_batch = create_batch(action_cards_opp, num_moves)

    # FEATURE 11 -- Gift cards
    gift_cards = _cards2array(infoset[0].state.gift_cards[curr])
    gift_cards_batch = create_batch(gift_cards, num_moves)

    # FEATURE 12 -- Gift cards opp
    gift_cards_opp = _cards2array(infoset[0].state.gift_cards[opp])
    gift_cards_opp_batch = create_batch(gift_cards_opp, num_moves)

    # FEATURE 13 -- All gift cards
    all_gift_cards = gift_cards + stashed_card
    all_gift_cards_batch = create_batch(all_gift_cards, num_moves)

    # FEATURE 14 -- Number of cards (one-hot)
    num_cards = _get_one_hot_array(infoset[0].state.num_cards[curr])
    num_cards_batch = create_batch(num_cards, num_moves)

    # FEATURE 15 -- Number of cards opp (one-hot)
    num_cards_opp = _get_one_hot_array(infoset[0].state.num_cards[opp])
    num_cards_opp_batch = create_batch(num_cards_opp, num_moves)

    # FEATURE 16 -- Unknown cards
    unknown_cards = geisha_points - all_gift_cards - trashed_cards - gift_cards_opp - decision_cards_1_2 - decision_cards_2_2_1 - decision_cards_2_2_2
    unknown_cards_batch = create_batch(unknown_cards, num_moves)

    move_batch = np.zeros((num_moves, 63))
    for j, move in enumerate(infoset[1].moves):
        move_batch[j, :] = _my_move2array(move)

    x_batch = np.hstack((geisha_points_batch,
                         geisha_preferences_batch,
                         hand_cards_batch,
                         stashed_card_batch,
                         trashed_cards_batch,
                         decision_cards_1_2_batch,
                         decision_cards_2_2_1_batch,
                         decision_cards_2_2_2_batch,
                         action_cards_batch,
                         action_cards_opp_batch,
                         gift_cards_batch,
                         gift_cards_opp_batch,
                         all_gift_cards_batch,
                         num_cards_batch,
                         num_cards_opp_batch,
                         unknown_cards_batch,
                         move_batch))
    # TODO
    z = _action_seq_list2array(_process_action_seq(
        infoset.card_play_action_seq))
    z_batch = np.repeat(
        z[np.newaxis, :, :],
        num_moves, axis=0)
    obs = {
        'id' : infoset[0].state.acting_player_id,
        'round_id' : infoset[0].state.id_to_round_position[infoset[0].state.acting_player_id],
        'x_batch': x_batch.astype(np.float32),
        'z_batch': z_batch.astype(np.float32),
        'moves': infoset[1].moves,
        'z': z.astype(np.int8),
    }
    return obs
