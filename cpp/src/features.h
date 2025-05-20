#ifndef HANAMIKOJI_FEATURES_H_INCLUDED
#define HANAMIKOJI_FEATURES_H_INCLUDED

#include <algorithm>
#include <array>
#include <cstring>  // for memset
#include <map>
#include <numeric>
#include <vector>
#include "game.h"
#include "movegen.h"

constexpr int ROUND_MOVES = 12;
constexpr int MOVE_VECTOR_SIZE = 63;
constexpr int X_FEATURE_SIZE = 169;
constexpr int X_NO_MOVE_FEATURE_SIZE = X_FEATURE_SIZE - MOVE_VECTOR_SIZE;

using Move = std::pair<int, std::vector<int>>;

std::vector<int> my_move2array(const Move& move)
{
  std::vector<int> ret = {};
  int type = move.first;
  const auto& data = move.second;

  switch (type) {
  case TYPE_0_STASH:
    std::copy(data[0].begin(), data[0].end(), ret.begin());
    break;
  case TYPE_1_TRASH:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 7);
    break;
  case TYPE_2_CHOOSE_1_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 14);
    break;
  case TYPE_3_CHOOSE_2_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 21);
    std::copy(data[1].begin(), data[1].end(), ret.begin() + 28);
    break;
  case TYPE_4_RESOLVE_1_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 35);
    std::copy(data[1].begin(), data[1].end(), ret.begin() + 42);
    break;
  case TYPE_5_RESOLVE_2_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 49);
    std::copy(data[1].begin(), data[1].end(), ret.begin() + 56);
    break;
  }
  return ret;
}

std::vector<int> opp_move2array(const Move& move)
{
  std::vector<int> ret = {};
  int type = move.first;
  const auto& data = move.second;

  switch (type) {
  case TYPE_0_STASH:
    std::fill(ret.begin(), ret.begin() + 7, 1);
    break;
  case TYPE_1_TRASH:
    std::fill(ret.begin() + 7, ret.begin() + 14, 1);
    break;
  case TYPE_2_CHOOSE_1_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 14);
    break;
  case TYPE_3_CHOOSE_2_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 21);
    std::copy(data[1].begin(), data[1].end(), ret.begin() + 28);
    break;
  case TYPE_4_RESOLVE_1_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 35);
    std::copy(data[1].begin(), data[1].end(), ret.begin() + 42);
    break;
  case TYPE_5_RESOLVE_2_2:
    std::copy(data[0].begin(), data[0].end(), ret.begin() + 49);
    std::copy(data[1].begin(), data[1].end(), ret.begin() + 56);
    break;
  }
  return ret;
}

std::vector<int> one_hot(int num_cards)
{
  std::vector<int> one_hot = {};
  if (num_cards > 0 && num_cards <= 7) {
    one_hot[num_cards - 1] = 1;
  }
  return one_hot;
}

std::vector<std::vector<int>> encode_round_moves(const std::vector<Move>& curr_moves,
                                                                     const std::vector<Move>& opp_moves)
{
  std::vector<std::vector<int>> z(ROUND_MOVES);
  int l_curr = curr_moves.size();
  for (int i = 6 - l_curr; i < 6; ++i) {
    z[i] = my_move2array(curr_moves[i - (6 - l_curr)]);
  }
  int l_opp = opp_moves.size();
  for (int i = ROUND_MOVES - l_opp; i < ROUND_MOVES; ++i) {
    z[i] = opp_move2array(opp_moves[i - (ROUND_MOVES - l_opp)]);
  }
  return z;
}

using Vec7 = std::vector<int>;
using Vec4 = std::vector<int>;
using Vec63 = std::vector<int>;
using FeatureVec = std::vector<int8_t>;                  // 169-length vector
using FeatureMatrix = std::vector<FeatureVec>;           // shape = (num_moves, 169)
using HistoryMatrix = std::vector<std::vector<int8_t>>;  // shape = (12, 63)
using HistoryBatch = std::vector<HistoryMatrix>;         // shape = (num_moves, 12, 63)

struct Obs
{
  std::string id;
  std::string round_id;
  std::vector<std::pair<int, std::vector<int>>> moves;
  FeatureMatrix x_batch;
  FeatureVec x_no_move;
  HistoryMatrix z;
  HistoryBatch z_batch;
};

Obs get_obs(const GameState& gameState, const PrivateInfoSet& privateInfoSet)
{
  Obs obs;
  const int num_moves = privateInfoSet.moves.size();
  const std::string& curr = gameState.acting_player_id;
  const std::string& opp = (curr == "first" ? "second" : "first");

  obs.id = curr;
  obs.round_id = gameState.id_to_round_id.at(curr);
  obs.moves = privateInfoSet.moves;

  // --- FEATURE VECTORS ---
  Vec7 geisha_points = {2, 2, 2, 3, 3, 4, 5};
  Vec7 geisha_preferences;
  for (int i = 0; i < 7; ++i) {
    geisha_preferences[i] = gameState.geisha_preferences.at(curr)[i] - gameState.geisha_preferences.at(opp)[i];
  }

  Vec7 hand_cards = privateInfoSet.hand_cards;
  Vec7 stashed_card = privateInfoSet.stashed_card;
  Vec7 trashed_cards = privateInfoSet.trashed_cards;
  Vec7 decision_1_2 = gameState.decision_cards_1_2;
  Vec7 decision_2_2_1 =
      (gameState.decision_cards_2_2.has_value() ? gameState.decision_cards_2_2.value()[0] : Vec7{0, 0, 0, 0, 0, 0, 0});
  Vec7 decision_2_2_2 =
      (gameState.decision_cards_2_2.has_value() ? gameState.decision_cards_2_2.value()[1] : Vec7{0, 0, 0, 0, 0, 0, 0});
  Vec4 action_cards = gameState.action_cards.at(curr);
  Vec4 action_cards_opp = gameState.action_cards.at(opp);
  Vec7 gift_cards = gameState.gift_cards.at(curr);
  Vec7 gift_cards_opp = gameState.gift_cards.at(opp);

  Vec7 all_gift_cards;
  for (int i = 0; i < 7; ++i) all_gift_cards[i] = gift_cards[i] + stashed_card[i];

  Vec7 num_cards = one_hot(gameState.num_cards.at(curr));
  Vec7 num_cards_opp = one_hot(gameState.num_cards.at(opp));

  Vec7 unknown_cards;
  for (int i = 0; i < 7; ++i)
    unknown_cards[i] = geisha_points[i] - hand_cards[i] - all_gift_cards[i] - trashed_cards[i] - gift_cards_opp[i] -
                       decision_1_2[i] - decision_2_2_1[i] - decision_2_2_2[i];

  // --- x_batch ---
  obs.x_batch.resize(num_moves, FeatureVec(X_FEATURE_SIZE));
  for (int j = 0; j < num_moves; ++j) {
    auto& x = obs.x_batch[j];
    int idx = 0;

    auto append7 = [&](const Vec7& v) {
      for (int i = 0; i < 7; ++i) x[idx++] = v[i];
    };
    auto append4 = [&](const Vec4& v) {
      for (int i = 0; i < 4; ++i) x[idx++] = v[i];
    };

    append7(geisha_points);
    append7(geisha_preferences);
    append7(hand_cards);
    append7(stashed_card);
    append7(trashed_cards);
    append7(decision_1_2);
    append7(decision_2_2_1);
    append7(decision_2_2_2);
    append4(action_cards);
    append4(action_cards_opp);
    append7(gift_cards);
    append7(gift_cards_opp);
    append7(all_gift_cards);
    append7(num_cards);
    append7(num_cards_opp);
    append7(unknown_cards);

    // Move vector
    Vec63 move_vec = my_move2array(privateInfoSet.moves[j]);
    for (int i = 0; i < 63; ++i) x[idx++] = move_vec[i];
  }

  // --- x_no_move ---
  obs.x_no_move.resize(X_NO_MOVE_FEATURE_SIZE);
  {
    int idx = 0;
    auto append7 = [&](const Vec7& v) {
      for (int i = 0; i < 7; ++i) obs.x_no_move[idx++] = v[i];
    };
    auto append4 = [&](const Vec4& v) {
      for (int i = 0; i < 4; ++i) obs.x_no_move[idx++] = v[i];
    };

    append7(geisha_points);
    append7(geisha_preferences);
    append7(hand_cards);
    append7(stashed_card);
    append7(trashed_cards);
    append7(decision_1_2);
    append7(decision_2_2_1);
    append7(decision_2_2_2);
    append4(action_cards);
    append4(action_cards_opp);
    append7(gift_cards);
    append7(gift_cards_opp);
    append7(all_gift_cards);
    append7(num_cards);
    append7(num_cards_opp);
    append7(unknown_cards);
  }

  // --- z ---
  obs.z = encode_round_moves(gameState.round_moves.at(curr), gameState.round_moves.at(opp));

  // --- z_batch ---
  obs.z_batch.resize(num_moves, obs.z);

  return obs;
}

#endif
