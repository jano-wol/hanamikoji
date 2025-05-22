#ifndef HANAMIKOJI_FEATURES_H_INCLUDED
#define HANAMIKOJI_FEATURES_H_INCLUDED

#include <torch/script.h>
#include <array>
#include <vector>
#include "Game.h"
#include "Movegen.h"

// Constants
constexpr int ROUND_MOVES = 12;
constexpr int MOVE_VECTOR_SIZE = 63;
constexpr int X_FEATURE_SIZE = 169;
constexpr int X_NO_MOVE_FEATURE_SIZE = (X_FEATURE_SIZE - MOVE_VECTOR_SIZE);

// Tensor container for inference
struct TorchObs
{
  torch::Tensor x_batch;    // [num_moves, 169]
  torch::Tensor x_no_move;  // [169]
  torch::Tensor z_batch;    // [num_moves, 12, 63]
};

typedef std::pair<int, std::vector<int>> Move;

torch::Tensor myMoveToTensor(const Move& move)
{
  auto ret = torch::zeros({MOVE_VECTOR_SIZE}, torch::kFloat32);

  switch (move.first) {
  case TYPE_0_STASH:
    ret.slice(0, 0, 7) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_1_TRASH:
    ret.slice(0, 7, 14) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_2_CHOOSE_1_2:
    ret.slice(0, 14, 21) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_3_CHOOSE_2_2:
    ret.slice(0, 21, 35) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_4_RESOLVE_1_2:
    ret.slice(0, 35, 49) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_5_RESOLVE_2_2:
    ret.slice(0, 49, 63) = torch::tensor(move.second, torch::kFloat32);
    break;
  }

  return ret;
}

torch::Tensor oppMoveToTensor(const Move& move)
{
  auto ret = torch::zeros({MOVE_VECTOR_SIZE}, torch::kFloat32);
  std::vector<int32_t> vec(7, 1);
  switch (move.first) {
  case TYPE_0_STASH:
    ret.slice(0, 0, 7) = torch::tensor(vec, torch::kFloat32);
    break;
  case TYPE_1_TRASH:
    ret.slice(0, 7, 14) = torch::tensor(vec, torch::kFloat32);
    break;
  case TYPE_2_CHOOSE_1_2:
    ret.slice(0, 14, 21) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_3_CHOOSE_2_2:
    ret.slice(0, 21, 35) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_4_RESOLVE_1_2:
    ret.slice(0, 35, 49) = torch::tensor(move.second, torch::kFloat32);
    break;
  case TYPE_5_RESOLVE_2_2:
    ret.slice(0, 49, 63) = torch::tensor(move.second, torch::kFloat32);
    break;
  }

  return ret;
}

torch::Tensor getOneHotTensor(int32_t n)
{
  auto one_hot = torch::zeros({7}, torch::kFloat32);
  if (n > 0 && n <= 7)
    one_hot[n - 1] = 1.0f;
  return one_hot;
}

torch::Tensor encodeRoundMoves(const std::vector<Move>& round_moves_curr, const std::vector<Move>& round_moves_opp)
{
  auto z = torch::zeros({ROUND_MOVES, MOVE_VECTOR_SIZE}, torch::kFloat32);

  int l_curr = static_cast<int>(round_moves_curr.size());
  for (int i = 6 - l_curr; i < 6; ++i) z[i] = myMoveToTensor(round_moves_curr[i - (6 - l_curr)]);

  int l_opp = static_cast<int>(round_moves_opp.size());
  for (int i = ROUND_MOVES - l_opp; i < ROUND_MOVES; ++i)
    z[i] = oppMoveToTensor(round_moves_opp[i - (ROUND_MOVES - l_opp)]);

  return z;
}

std::vector<int32_t> add_vec(const std::vector<int32_t>& a, const std::vector<int32_t>& b)
{
  std::vector<int32_t> result(7);
  for (int i = 0; i < 7; ++i) result[i] = a[i] + b[i];
  return result;
}

std::vector<int32_t> sub_vec(const std::vector<int32_t>& a, const std::vector<int32_t>& b)
{
  std::vector<int32_t> result(7);
  for (int i = 0; i < 7; ++i) result[i] = a[i] - b[i];
  return result;
}

std::vector<int32_t> calcUnknowns(const std::vector<int32_t>& a, const std::vector<int32_t>& b,
                                  const std::vector<int32_t>& c, const std::vector<int32_t>& d,
                                  const std::vector<int32_t>& e, const std::vector<int32_t>& f,
                                  const std::vector<int32_t>& g, const std::vector<int32_t>& h)
{
  std::vector<int32_t> ret;
  ret = sub_vec(a, b);
  ret = sub_vec(ret, c);
  ret = sub_vec(ret, d);
  ret = sub_vec(ret, e);
  ret = sub_vec(ret, f);
  ret = sub_vec(ret, g);
  ret = sub_vec(ret, h);
  return ret;
}

TorchObs get_obs(const GameState& gameState, const PrivateInfoSet& privateInfoSet)
{
  const int num_moves = static_cast<int>(privateInfoSet.moves.size());
  int curr = gameState.acting_player_id;
  int opp = 1 - curr;

  auto x_batch = torch::empty({num_moves, X_FEATURE_SIZE}, torch::kFloat32);
  auto x_no_move = torch::empty({X_NO_MOVE_FEATURE_SIZE}, torch::kFloat32);

  auto z = encodeRoundMoves(gameState.round_moves[curr], gameState.round_moves[opp]);
  auto z_batch = z.unsqueeze(0).expand({num_moves, ROUND_MOVES, MOVE_VECTOR_SIZE}).clone();

  torch::Tensor move_batch = torch::empty({num_moves, MOVE_VECTOR_SIZE}, torch::kFloat32);
  for (int i = 0; i < num_moves; ++i) {
    move_batch[i] = myMoveToTensor(privateInfoSet.moves[i]);
  }

  // Fill in x_batch with all feature slices (placeholder: fill with dummy data)
  // You will replace below with actual tensors from game state
  auto dummy_7 = torch::zeros({7}, torch::kFloat32);
  auto dummy_4 = torch::zeros({4}, torch::kFloat32);

  std::vector<int32_t> geisha_points_vec{2, 2, 2, 3, 3, 4, 5};
  std::vector<int32_t> preferences_vec = sub_vec(gameState.geisha_preferences[curr], gameState.geisha_preferences[opp]);
  std::vector<int32_t> decision_1_2_vec =
      gameState.decision_cards_1_2.empty() ? std::vector<int32_t>(7, 0) : gameState.decision_cards_1_2;
  std::vector<int32_t> decision_2_2_1_vec =
      gameState.decision_cards_2_2.first.empty() ? std::vector<int32_t>(7, 0) : gameState.decision_cards_2_2.first;
  std::vector<int32_t> decision_2_2_2_vec =
      gameState.decision_cards_2_2.second.empty() ? std::vector<int32_t>(7, 0) : gameState.decision_cards_2_2.second;
  std::vector<int32_t> all_gift_cards_vec = add_vec(gameState.gift_cards[curr], privateInfoSet.stashed_card);
  std::vector<int32_t> unknown_cards =
      calcUnknowns(geisha_points_vec, privateInfoSet.hand_cards, all_gift_cards_vec, privateInfoSet.trashed_cards,
                   gameState.gift_cards[opp], decision_1_2_vec, decision_2_2_1_vec, decision_2_2_2_vec);

  auto feature_1 = torch::tensor(geisha_points_vec, torch::kFloat32);
  auto feature_2 = torch::tensor(preferences_vec, torch::kFloat32);
  auto feature_3 = torch::tensor(privateInfoSet.hand_cards, torch::kFloat32);
  auto feature_4 = torch::tensor(privateInfoSet.stashed_card, torch::kFloat32);
  auto feature_5 = torch::tensor(privateInfoSet.trashed_cards, torch::kFloat32);
  auto feature_6 = torch::tensor(decision_1_2_vec, torch::kFloat32);
  auto feature_7 = torch::tensor(decision_2_2_1_vec, torch::kFloat32);
  auto feature_8 = torch::tensor(decision_2_2_2_vec, torch::kFloat32);
  auto feature_9 = torch::tensor(gameState.action_cards[curr], torch::kFloat32);
  auto feature_10 = torch::tensor(gameState.action_cards[opp], torch::kFloat32);
  auto feature_11 = torch::tensor(gameState.gift_cards[curr], torch::kFloat32);
  auto feature_12 = torch::tensor(gameState.gift_cards[opp], torch::kFloat32);
  auto feature_13 = torch::tensor(all_gift_cards_vec, torch::kFloat32);
  auto feature_14 = getOneHotTensor(gameState.num_cards[curr]);
  auto feature_15 = getOneHotTensor(gameState.num_cards[opp]);
  auto feature_16 = torch::tensor(unknown_cards, torch::kFloat32);

  for (int i = 0; i < num_moves; ++i) {
    x_batch[i].slice(0, 0, 7) = feature_1;      // geisha_points
    x_batch[i].slice(0, 7, 14) = feature_2;     // preferences
    x_batch[i].slice(0, 14, 21) = feature_3;    // hand
    x_batch[i].slice(0, 21, 28) = feature_4;    // stash
    x_batch[i].slice(0, 28, 35) = feature_5;    // trash
    x_batch[i].slice(0, 35, 42) = feature_6;    // decision 1_2
    x_batch[i].slice(0, 42, 49) = feature_7;    // decision 2_2-1
    x_batch[i].slice(0, 49, 56) = feature_8;    // decision 2_2-2
    x_batch[i].slice(0, 56, 60) = feature_9;    // actions
    x_batch[i].slice(0, 60, 64) = feature_10;   // opp actions
    x_batch[i].slice(0, 64, 71) = feature_11;   // gift
    x_batch[i].slice(0, 71, 78) = feature_12;   // gift opp
    x_batch[i].slice(0, 78, 85) = feature_13;   // all gift
    x_batch[i].slice(0, 85, 92) = feature_14;   // card count
    x_batch[i].slice(0, 92, 99) = feature_15;   // opp card count
    x_batch[i].slice(0, 99, 106) = feature_16;  // unknown
    x_batch[i].slice(0, 106, 169) = move_batch[i];
  }

  x_no_move.slice(0, 0, 7) = feature_1;
  x_no_move.slice(0, 7, 14) = feature_2;
  x_no_move.slice(0, 14, 21) = feature_3;
  x_no_move.slice(0, 21, 28) = feature_4;
  x_no_move.slice(0, 28, 35) = feature_5;
  x_no_move.slice(0, 35, 42) = feature_6;
  x_no_move.slice(0, 42, 49) = feature_7;
  x_no_move.slice(0, 49, 56) = feature_8;
  x_no_move.slice(0, 56, 60) = feature_9;
  x_no_move.slice(0, 60, 64) = feature_10;
  x_no_move.slice(0, 64, 71) = feature_11;
  x_no_move.slice(0, 71, 78) = feature_12;
  x_no_move.slice(0, 78, 85) = feature_13;
  x_no_move.slice(0, 85, 92) = feature_14;
  x_no_move.slice(0, 92, 99) = feature_15;
  x_no_move.slice(0, 99, 106) = feature_16;

  return TorchObs{x_batch, x_no_move, z_batch};
}

#endif  // HANAMIKOJI_FEATURES_H_INCLUDED
