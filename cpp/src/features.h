#ifndef HANAMIKOJI_FEATURES_H_INCLUDED
#define HANAMIKOJI_FEATURES_H_INCLUDED

#include <torch/script.h>
#include <array>
#include <vector>
#include "game.h"
#include "movegen.h"

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

torch::Tensor getOneHotTensor(int n)
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

TorchObs get_obs(const Infoset& infoset)
{
  const int num_moves = static_cast<int>(infoset.legal_moves.size());

  auto x_batch = torch::empty({num_moves, X_FEATURE_SIZE}, torch::kFloat32);
  auto x_no_move = torch::empty({X_NO_MOVE_FEATURE_SIZE}, torch::kFloat32);

  auto z =
      encodeRoundMoves(infoset.round_moves.at(infoset.acting_player), infoset.round_moves.at(infoset.opponent_player));
  auto z_batch = z.unsqueeze(0).expand({num_moves, ROUND_MOVES, MOVE_VECTOR_SIZE}).clone();

  torch::Tensor move_batch = torch::empty({num_moves, MOVE_VECTOR_SIZE}, torch::kFloat32);
  for (int i = 0; i < num_moves; ++i) {
    move_batch[i] = moveToTensor(infoset.legal_moves[i]);
  }

  // Fill in x_batch with all feature slices (placeholder: fill with dummy data)
  // You will replace below with actual tensors from game state
  auto dummy_7 = torch::zeros({7}, torch::kFloat32);
  auto dummy_4 = torch::zeros({4}, torch::kFloat32);

  for (int i = 0; i < num_moves; ++i) {
    x_batch[i].slice(0, 0, 7) = dummy_7;     // geisha_points
    x_batch[i].slice(0, 7, 14) = dummy_7;    // preferences
    x_batch[i].slice(0, 14, 21) = dummy_7;   // hand
    x_batch[i].slice(0, 21, 28) = dummy_7;   // stash
    x_batch[i].slice(0, 28, 35) = dummy_7;   // trash
    x_batch[i].slice(0, 35, 42) = dummy_7;   // decision 1_2
    x_batch[i].slice(0, 42, 49) = dummy_7;   // decision 2_2-1
    x_batch[i].slice(0, 49, 56) = dummy_7;   // decision 2_2-2
    x_batch[i].slice(0, 56, 60) = dummy_4;   // actions
    x_batch[i].slice(0, 60, 64) = dummy_4;   // opp actions
    x_batch[i].slice(0, 64, 71) = dummy_7;   // gift
    x_batch[i].slice(0, 71, 78) = dummy_7;   // gift opp
    x_batch[i].slice(0, 78, 85) = dummy_7;   // all gift
    x_batch[i].slice(0, 85, 92) = dummy_7;   // card count
    x_batch[i].slice(0, 92, 99) = dummy_7;   // opp card count
    x_batch[i].slice(0, 99, 106) = dummy_7;  // unknown
    x_batch[i].slice(0, 106, 169) = move_batch[i];
  }

  // Fill x_no_move similarly (excluding move features)
  x_no_move.slice(0, 0, 7) = dummy_7;
  x_no_move.slice(0, 7, 14) = dummy_7;
  x_no_move.slice(0, 14, 21) = dummy_7;
  x_no_move.slice(0, 21, 28) = dummy_7;
  x_no_move.slice(0, 28, 35) = dummy_7;
  x_no_move.slice(0, 35, 42) = dummy_7;
  x_no_move.slice(0, 42, 49) = dummy_7;
  x_no_move.slice(0, 49, 56) = dummy_7;
  x_no_move.slice(0, 56, 60) = dummy_4;
  x_no_move.slice(0, 60, 64) = dummy_4;
  x_no_move.slice(0, 64, 71) = dummy_7;
  x_no_move.slice(0, 71, 78) = dummy_7;
  x_no_move.slice(0, 78, 85) = dummy_7;
  x_no_move.slice(0, 85, 92) = dummy_7;
  x_no_move.slice(0, 92, 99) = dummy_7;
  x_no_move.slice(0, 99, 106) = dummy_7;

  return TorchObs{x_batch, x_no_move, z_batch};
}

#endif  // HANAMIKOJI_FEATURES_H_INCLUDED
