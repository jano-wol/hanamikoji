// hanamikoji_game.hpp (or .cpp depending on split)

#include <algorithm>
#include <array>
#include <cassert>
#include <map>
#include <memory>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "movegen.h"

std::vector<int> add_cards(const std::vector<int>& a, const std::vector<int>& b)
{
  std::vector<int> result(7);
  for (int i = 0; i < 7; ++i) result[i] = a[i] + b[i];
  return result;
}

std::vector<int> sub_cards(const std::vector<int>& a, const std::vector<int>& b)
{
  std::vector<int> result(7);
  for (int i = 0; i < 7; ++i) result[i] = a[i] - b[i];
  return result;
}

struct PrivateInfoSet
{
  std::vector<int> hand_cards;
  std::vector<int> stashed_card = std::vector<int>(7, 0);
  std::vector<int> trashed_cards = std::vector<int>(7, 0);
  std::vector<std::pair<int, std::vector<int>>> moves;
};

struct GameState
{
  std::string acting_player_id = "first";
  std::map<std::string, std::string> id_to_round_id = {{"first", "first"}, {"second", "second"}};
  std::vector<int> points = {2, 2, 2, 3, 3, 4, 5};
  std::map<std::string, std::vector<int>> gift_cards = {{"first", std::vector<int>(7, 0)},
                                                        {"second", std::vector<int>(7, 0)}};
  std::map<std::string, std::vector<int>> action_cards = {{"first", {1, 1, 1, 1}}, {"second", {1, 1, 1, 1}}};
  std::vector<int> decision_cards_1_2;
  std::pair<std::vector<int>, std::vector<int>> decision_cards_2_2;
  std::map<std::string, std::vector<int>> geisha_preferences = {{"first", std::vector<int>(7, 0)},
                                                                {"second", std::vector<int>(7, 0)}};
  std::map<std::string, int> num_cards = {{"first", 7}, {"second", 6}};
  std::map<std::string, std::vector<std::pair<int, std::vector<int>>>> round_moves = {{"first", {}}, {"second", {}}};
};

class Player
{
public:
  virtual int act(const GameState& gameState, const PrivateInfoSet& privateInfoSet) = 0;
};

class GameEnv
{
public:
  GameEnv(std::map<std::string, std::shared_ptr<Player>> players) : players(players), round(1), winner("")
  {
    private_info_sets["first"] = PrivateInfoSet();
    private_info_sets["second"] = PrivateInfoSet();
    state = GameState();
  }

  void init_card_play()
  {
    deck = {0, 0, 1, 1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6};
    shuffle(deck.begin(), deck.end(), random_engine);

    std::vector<int> f(7, 0), s(7, 0);
    for (int i = 0; i < 7; ++i) f[deck[i]]++;
    for (int i = 7; i < 13; ++i) s[deck[i]]++;

    private_info_sets[state.acting_player_id].hand_cards = f;
    private_info_sets[get_opp()].hand_cards = s;

    deck.erase(deck.begin(), deck.begin() + 13);

    private_info_sets[state.acting_player_id].moves = get_moves();
    active_player_info_set = {state, private_info_sets[state.acting_player_id]};
  }

  void update_geisha_preferences()
  {
    std::vector<int> first_gifts = add_cards(state.gift_cards["first"], private_info_sets["first"].stashed_card);
    std::vector<int> second_gifts = add_cards(state.gift_cards["second"], private_info_sets["second"].stashed_card);

    for (int i = 0; i < 7; ++i) {
      if (first_gifts[i] > second_gifts[i] ||
          (first_gifts[i] == second_gifts[i] && state.geisha_preferences["first"][i] == 1)) {
        state.geisha_preferences["first"][i] = 1;
      } else {
        state.geisha_preferences["first"][i] = 0;
      }

      if (first_gifts[i] < second_gifts[i] ||
          (first_gifts[i] == second_gifts[i] && state.geisha_preferences["second"][i] == 1)) {
        state.geisha_preferences["second"][i] = 1;
      } else {
        state.geisha_preferences["second"][i] = 0;
      }
    }
  }

  void step()
  {
    std::string curr = state.acting_player_id;
    std::string opp = get_opp();
    auto info = private_info_sets[curr];
    int move_index = players[curr]->act(state, info);
    auto move = active_player_info_set.second.moves[move_index];

    bool draw_card = true;

    switch (move.first) {
    case TYPE_0_STASH:
      state.round_moves[curr].emplace_back(TYPE_0_STASH, std::vector<int>(7, 0));
      state.action_cards[curr][0] = 0;
      info.hand_cards = sub_cards(info.hand_cards, move.second);
      info.stashed_card = move.second;
      state.num_cards[curr] -= 1;
      state.acting_player_id = opp;
      break;
    case TYPE_1_TRASH:
      state.round_moves[curr].emplace_back(TYPE_1_TRASH, std::vector<int>(7, 0));
      state.action_cards[curr][1] = 0;
      info.hand_cards = sub_cards(info.hand_cards, move.second);
      info.trashed_cards = move.second;
      state.num_cards[curr] -= 2;
      state.acting_player_id = opp;
      break;
    case TYPE_2_CHOOSE_1_2:
      state.round_moves[curr].emplace_back(move);
      state.action_cards[curr][2] = 0;
      info.hand_cards = sub_cards(info.hand_cards, move.second);
      state.decision_cards_1_2 = move.second;
      state.num_cards[curr] -= 3;
      state.acting_player_id = opp;
      draw_card = false;
      break;
    case TYPE_3_CHOOSE_2_2:
      state.round_moves[curr].emplace_back(move);
      state.action_cards[curr][3] = 0;
      state.decision_cards_2_2 = {std::vector<int>(move.second.begin(), move.second.begin() + 7),
                                  std::vector<int>(move.second.begin() + 7, move.second.end())};
      info.hand_cards = sub_cards(info.hand_cards, state.decision_cards_2_2.first);
      info.hand_cards = sub_cards(info.hand_cards, state.decision_cards_2_2.second);
      state.num_cards[curr] -= 4;
      state.acting_player_id = opp;
      draw_card = false;
      break;
    case TYPE_4_RESOLVE_1_2:
      state.round_moves[curr].emplace_back(move);
      state.decision_cards_1_2.clear();
      state.gift_cards[curr] =
          add_cards(state.gift_cards[curr], std::vector<int>(move.second.begin(), move.second.begin() + 7));
      state.gift_cards[opp] =
          add_cards(state.gift_cards[opp], std::vector<int>(move.second.begin() + 7, move.second.end()));
      break;
    case TYPE_5_RESOLVE_2_2:
      state.round_moves[curr].emplace_back(move);
      state.decision_cards_2_2 = {};
      state.gift_cards[curr] =
          add_cards(state.gift_cards[curr], std::vector<int>(move.second.begin(), move.second.begin() + 7));
      state.gift_cards[opp] =
          add_cards(state.gift_cards[opp], std::vector<int>(move.second.begin() + 7, move.second.end()));
      break;
    }

    if (state.round_moves["first"].size() + state.round_moves["second"].size() == 12) {
      // TODO: Round end logic (geisha resolution, winner check, round reset)
    } else {
      auto& new_info = private_info_sets[state.acting_player_id];
      if (draw_card && !deck.empty()) {
        new_info.hand_cards[deck[0]]++;
        state.num_cards[state.acting_player_id]++;
        deck.erase(deck.begin());
      }
      new_info.moves = get_moves();
      active_player_info_set = {state, new_info};
    }
  }

private:
  GameState state;
  std::map<std::string, PrivateInfoSet> private_info_sets;
  std::map<std::string, std::shared_ptr<Player>> players;
  std::vector<int> deck;
  std::string winner;
  int round;
  std::map<std::string, int> num_wins = {{"first", 0}, {"second", 0}};
  std::pair<GameState, PrivateInfoSet> active_player_info_set;
  std::default_random_engine random_engine;

  std::string get_opp() { return state.acting_player_id == "first" ? "second" : "first"; }

  std::vector<std::pair<int, std::vector<int>>> get_moves()
  {
    MovesGener mg(private_info_sets[state.acting_player_id].hand_cards, state.action_cards[state.acting_player_id],
                  state.decision_cards_1_2, state.decision_cards_2_2);
    return mg.getMoves();
  }
};
