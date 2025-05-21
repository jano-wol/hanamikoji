#ifndef HANAMIKOJI_IPLAYER_H_INCLUDED
#define HANAMIKOJI_IPLAYER_H_INCLUDED

struct PrivateInfoSet
{
  std::vector<int32_t> hand_cards;
  std::vector<int32_t> stashed_card = std::vector<int32_t>(7, 0);
  std::vector<int32_t> trashed_cards = std::vector<int32_t>(7, 0);
  std::vector<std::pair<int, std::vector<int32_t>>> moves;
};

struct GameState
{
  int acting_player_id = 0;
  std::vector<int32_t> id_to_round_id = {0, 1};
  std::vector<int32_t> points = {2, 2, 2, 3, 3, 4, 5};
  std::vector<std::vector<int32_t>> gift_cards = {std::vector<int32_t>(7, 0), std::vector<int32_t>(7, 0)};
  std::vector<std::vector<int32_t>> action_cards = {{1, 1, 1, 1}, {1, 1, 1, 1}};
  std::vector<int32_t> decision_cards_1_2 = {};
  std::pair<std::vector<int32_t>, std::vector<int32_t>> decision_cards_2_2 = {};
  std::vector<std::vector<int32_t>> geisha_preferences = {std::vector<int32_t>(7, 0), std::vector<int32_t>(7, 0)};
  std::vector<int32_t> num_cards = {7, 6};
  std::vector<std::vector<std::pair<int, std::vector<int32_t>>>> round_moves = {{{}}, {{}}};
};

class IPlayer
{
public:
  virtual int act(const GameState& gameState, const PrivateInfoSet& privateInfoSet) = 0;
  virtual ~IPlayer() = default;
};

#endif
