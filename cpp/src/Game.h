#ifndef HANAMIKOJI_GAME_H_INCLUDED
#define HANAMIKOJI_GAME_H_INCLUDED

#include <algorithm>
#include <array>
#include <cassert>
#include <memory>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "Movegen.h"

std::vector<int32_t> add_cards(const std::vector<int32_t>& a, const std::vector<int32_t>& b)
{
  std::vector<int32_t> result(7);
  for (int i = 0; i < 7; ++i) result[i] = a[i] + b[i];
  return result;
}

std::vector<int32_t> sub_cards(const std::vector<int32_t>& a, const std::vector<int32_t>& b)
{
  std::vector<int32_t> result(7);
  for (int i = 0; i < 7; ++i) result[i] = a[i] - b[i];
  return result;
}

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

class Player
{
public:
  virtual int act(const GameState& gameState, const PrivateInfoSet& privateInfoSet) = 0;
};

class GameEnv
{
public:
  GameEnv(std::vector<std::shared_ptr<Player>> players_) : players(std::move(players_)), round(1), winner(-1)
  {
    private_info_sets.push_back(PrivateInfoSet());
    private_info_sets.push_back(PrivateInfoSet());
    state = GameState();
  }

  void init_card_play()
  {
    deck = {0, 0, 1, 1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6};
    shuffle(deck.begin(), deck.end(), random_engine);

    std::vector<int32_t> f(7, 0), s(7, 0);
    for (int i = 0; i < 7; ++i) f[deck[i]]++;
    for (int i = 7; i < 13; ++i) s[deck[i]]++;

    private_info_sets[state.acting_player_id].hand_cards = f;
    private_info_sets[get_opp()].hand_cards = s;

    deck.erase(deck.begin(), deck.begin() + 13);

    private_info_sets[state.acting_player_id].moves = get_moves();
  }

  void update_geisha_preferences()
  {
    std::vector<int32_t> first_gifts = add_cards(state.gift_cards[0], private_info_sets[0].stashed_card);
    std::vector<int32_t> second_gifts = add_cards(state.gift_cards[1], private_info_sets[1].stashed_card);

    for (int i = 0; i < 7; ++i) {
      if (first_gifts[i] > second_gifts[i] ||
          (first_gifts[i] == second_gifts[i] && state.geisha_preferences[0][i] == 1)) {
        state.geisha_preferences[0][i] = 1;
      } else {
        state.geisha_preferences[0][i] = 0;
      }

      if (first_gifts[i] < second_gifts[i] ||
          (first_gifts[i] == second_gifts[i] && state.geisha_preferences[1][i] == 1)) {
        state.geisha_preferences[1][i] = 1;
      } else {
        state.geisha_preferences[1][i] = 0;
      }
    }
  }

  int is_game_ended()
  {
    int first_geisha_win = 0;
    int first_geisha_points = 0;
    int second_geisha_win = 0;
    int second_geisha_points = 0;

    for (int i = 0; i < 7; ++i) {
      if (state.geisha_preferences[0][i] == 1) {
        first_geisha_win++;
        first_geisha_points += state.points[i];
      }
      if (state.geisha_preferences[1][i] == 1) {
        second_geisha_win++;
        second_geisha_points += state.points[i];
      }
    }

    if (first_geisha_points >= 11)
      return 0;
    if (second_geisha_points >= 11)
      return 1;
    if (first_geisha_win >= 4)
      return 0;
    if (second_geisha_win >= 4)
      return 1;
    return -1;
  }

  void set_winner()
  {
    int winner_player = is_game_ended();
    if (winner_player != -1) {
      winner = winner_player;
      num_wins[winner]++;
    }
  }

  void step()
  {
    int curr = state.acting_player_id;
    int opp = get_opp();
    auto& info = private_info_sets[curr];
    int move_index = players[curr]->act(state, info);
    auto move = info.moves[move_index];

    bool draw_card = true;

    switch (move.first) {
    case TYPE_0_STASH:
      state.round_moves[curr].emplace_back(TYPE_0_STASH, std::vector<int32_t>(7, 0));  // TODO FIX?
      state.action_cards[curr][0] = 0;
      info.hand_cards = sub_cards(info.hand_cards, move.second);
      info.stashed_card = move.second;
      state.num_cards[curr] -= 1;
      state.acting_player_id = opp;
      break;
    case TYPE_1_TRASH:
      state.round_moves[curr].emplace_back(TYPE_1_TRASH, std::vector<int32_t>(7, 0));  // TODO FIX?
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
      state.decision_cards_2_2 = {std::vector<int32_t>(move.second.begin(), move.second.begin() + 7),
                                  std::vector<int32_t>(move.second.begin() + 7, move.second.end())};
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
          add_cards(state.gift_cards[curr], std::vector<int32_t>(move.second.begin(), move.second.begin() + 7));
      state.gift_cards[opp] =
          add_cards(state.gift_cards[opp], std::vector<int32_t>(move.second.begin() + 7, move.second.end()));
      break;
    case TYPE_5_RESOLVE_2_2:
      state.round_moves[curr].emplace_back(move);
      state.decision_cards_2_2 = {};
      state.gift_cards[curr] =
          add_cards(state.gift_cards[curr], std::vector<int32_t>(move.second.begin(), move.second.begin() + 7));
      state.gift_cards[opp] =
          add_cards(state.gift_cards[opp], std::vector<int32_t>(move.second.begin() + 7, move.second.end()));
      break;
    }

    if (state.round_moves[0].size() + state.round_moves[1].size() == 12) {
      assert(state.num_cards[0] == 0 && state.num_cards[1] == 0);

      update_geisha_preferences();
      set_winner();

      if (winner == -1) {
        auto next_geisha_preferences = state.geisha_preferences;
        round += 1;
        state = GameState();
        state.geisha_preferences = next_geisha_preferences;

        if (round % 2 == 0) {
          state.acting_player_id = 1;
          state.id_to_round_id = {1, 0};
          state.num_cards = {6, 7};
        }
        private_info_sets[0] = PrivateInfoSet();
        private_info_sets[1] = PrivateInfoSet();
        init_card_play();
      }
    } else {
      auto& new_info = private_info_sets[state.acting_player_id];
      if (draw_card && !deck.empty()) {
        new_info.hand_cards[deck[0]]++;
        state.num_cards[state.acting_player_id]++;
        deck.erase(deck.begin());
      }
      new_info.moves = get_moves();
    }
  }

private:
  GameState state;
  std::vector<PrivateInfoSet> private_info_sets;
  std::vector<std::shared_ptr<Player>> players;
  std::vector<int32_t> deck;
  int round = 1;
  int winner = -1;
  std::vector<int32_t> num_wins = {0, 0};
  std::default_random_engine random_engine;

  int get_opp() { return 1 - state.acting_player_id; }

  std::vector<std::pair<int, std::vector<int32_t>>> get_moves()
  {
    MovesGener mg(private_info_sets[state.acting_player_id].hand_cards, state.action_cards[state.acting_player_id],
                  state.decision_cards_1_2, state.decision_cards_2_2);
    return mg.getMoves();
  }
};

#endif
