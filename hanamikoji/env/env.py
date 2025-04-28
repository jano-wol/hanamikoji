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

def _get_one_hot_array(num_left_cards, max_num_cards):
    """
    A utility function to obtain one-hot endoding
    """
    one_hot = np.zeros(max_num_cards)
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

def _get_obs_landlord(infoset):
    """
    Obttain the landlord features. See Table 4 in
    https://arxiv.org/pdf/2106.06135.pdf
    """
    num_legal_actions = len(infoset[1].moves)
    my_handcards = _cards2array(infoset.player_hand_cards)
    my_handcards_batch = np.repeat(my_handcards[np.newaxis, :],
                                   num_legal_actions, axis=0)

    other_handcards = _cards2array(infoset.other_hand_cards)
    other_handcards_batch = np.repeat(other_handcards[np.newaxis, :],
                                      num_legal_actions, axis=0)

    last_action = _cards2array(infoset.last_move)
    last_action_batch = np.repeat(last_action[np.newaxis, :],
                                  num_legal_actions, axis=0)

    my_action_batch = np.zeros(my_handcards_batch.shape)
    for j, move in enumerate(infoset[1].moves):
        my_action_batch[j, :] = _my_move2array(move)

    landlord_up_num_cards_left = _get_one_hot_array(
        infoset.num_cards_left_dict['landlord_up'], 17)
    landlord_up_num_cards_left_batch = np.repeat(
        landlord_up_num_cards_left[np.newaxis, :],
        num_legal_actions, axis=0)

    landlord_down_num_cards_left = _get_one_hot_array(
        infoset.num_cards_left_dict['landlord_down'], 17)
    landlord_down_num_cards_left_batch = np.repeat(
        landlord_down_num_cards_left[np.newaxis, :],
        num_legal_actions, axis=0)

    landlord_up_played_cards = _cards2array(
        infoset.played_cards['landlord_up'])
    landlord_up_played_cards_batch = np.repeat(
        landlord_up_played_cards[np.newaxis, :],
        num_legal_actions, axis=0)

    landlord_down_played_cards = _cards2array(
        infoset.played_cards['landlord_down'])
    landlord_down_played_cards_batch = np.repeat(
        landlord_down_played_cards[np.newaxis, :],
        num_legal_actions, axis=0)

    bomb_num = _get_one_hot_bomb(
        infoset.bomb_num)
    bomb_num_batch = np.repeat(
        bomb_num[np.newaxis, :],
        num_legal_actions, axis=0)

    x_batch = np.hstack((my_handcards_batch,
                         other_handcards_batch,
                         last_action_batch,
                         landlord_up_played_cards_batch,
                         landlord_down_played_cards_batch,
                         landlord_up_num_cards_left_batch,
                         landlord_down_num_cards_left_batch,
                         bomb_num_batch,
                         my_action_batch))
    x_no_action = np.hstack((my_handcards,
                             other_handcards,
                             last_action,
                             landlord_up_played_cards,
                             landlord_down_played_cards,
                             landlord_up_num_cards_left,
                             landlord_down_num_cards_left,
                             bomb_num))
    z = _action_seq_list2array(_process_action_seq(
        infoset.card_play_action_seq))
    z_batch = np.repeat(
        z[np.newaxis, :, :],
        num_legal_actions, axis=0)
    obs = {
            'position': 'landlord',
            'x_batch': x_batch.astype(np.float32),
            'z_batch': z_batch.astype(np.float32),
            'legal_actions': infoset[1].moves,
            'x_no_action': x_no_action.astype(np.int8),
            'z': z.astype(np.int8),
          }
    return obs
