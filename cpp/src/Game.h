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

#include "IPlayer.h"
#include "Movegen.h"
#include "WebSocketServer.h"

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

std::vector<int32_t> card_list_to_inner(const std::vector<int32_t>& l)
{
  std::vector<int32_t> result(7, 0);
  for (auto c : l) {
    result[c] += 1;
  }
  return result;
}

class GameEnv
{
public:
  GameEnv(std::vector<std::unique_ptr<IPlayer>> players_, int port)
      : server(port), players(std::move(players_)), round(1), winner(-1)
  {
    private_info_sets.push_back(PrivateInfoSet());
    private_info_sets.push_back(PrivateInfoSet());
    state = GameState();
    json msg;
    msg["type"] = "init_player_id";
    server.send_message(msg);
    auto resp = server.receive_message();
    std::string resp_str = resp["ans"];
    if (resp_str == "second") {
      std::swap(players[0], players[1]);
    }
    if (players[0]->toString() == "Human") {
      human = 0;
      agent = 1;
    } else {
      human = 1;
      agent = 0;
    }
  }

  int get_opp() { return 1 - state.acting_player_id; }

  std::vector<std::pair<int, std::vector<int32_t>>> get_moves()
  {
    MovesGener mg(private_info_sets[state.acting_player_id].hand_cards, state.action_cards[state.acting_player_id],
                  state.decision_cards_1_2, state.decision_cards_2_2);
    return mg.getMoves();
  }

  void card_play_init()
  {
    int expected_length = ((agent == 0 && round % 2 == 1) || (agent == 1 && round % 2 == 0)) ? 7 : 6;
    json msg;
    msg["type"] = "init_hand";
    msg["desc"] = expected_length;
    server.send_message(msg);
    auto resp = server.receive_message();
    std::string hand_str = resp["ans"];
    std::vector<int32_t> ret(7, 0);
    for (char c : hand_str) {
      int val = c - '0';
      ++ret[val];
    }
    private_info_sets[agent].hand_cards = ret;
    if (state.acting_player_id == agent) {
      private_info_sets[state.acting_player_id].moves = get_moves();
    }
  }

  int draw_card()
  {
    json msg;
    msg["type"] = "draw_card";
    server.send_message(msg);
    auto resp = server.receive_message();
    std::string card_str = resp["ans"];
    return card_str[0] - '0';
  }

  std::vector<int32_t> reveal_human_stash()
  {
    json msg;
    msg["type"] = "stash_req";
    msg["desc"] = private_info_sets[agent].stashed_card;
    server.send_message(msg);
    auto resp = server.receive_message();
    std::vector<int32_t> stash = resp["ans"];
    return stash;
  }

  void update_geisha_preferences()
  {
    auto human_stash = reveal_human_stash();
    private_info_sets[human].stashed_card = human_stash;
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
    auto move = players[curr]->act(state, info);
    if (curr == agent) {
      json msg;
      msg["type"] = "move_desc";
      if (move.second.size() == 7) {
        msg["desc"] = move;
      } else {
        std::vector<int> v1(move.second.begin(), move.second.begin() + 7);
        std::vector<int> v2(move.second.begin() + 7, move.second.end());
        msg["desc"] = {move.first, {v1, v2}};
      }
      server.send_message(msg);
    }
    if (curr == human) {
      json msg;
      msg["type"] = "move_req";
      server.send_message(msg);
      auto resp = server.receive_message();
      int first = resp["ans"][0];
      std::vector<int32_t> second;
      if (resp["ans"][1][0].is_array()) {
        for (const auto& row : resp["ans"][1]) {
          for (const auto& val : row) {
            second.push_back(val.get<int32_t>());
          }
        }
      } else {
        second = resp["ans"][1].get<std::vector<int32_t>>();
      }
      move = {first, second};
    }

    bool is_draw_card = true;

    switch (move.first) {
    case TYPE_0_STASH:
      state.round_moves[curr].emplace_back(TYPE_0_STASH, std::vector<int32_t>(7, 0));  // TODO FIX?
      state.action_cards[curr][0] = 0;
      if (curr == agent) {
        info.hand_cards = sub_cards(info.hand_cards, move.second);
        info.stashed_card = move.second;
      }
      state.num_cards[curr] -= 1;
      state.acting_player_id = opp;
      break;
    case TYPE_1_TRASH:
      state.round_moves[curr].emplace_back(TYPE_1_TRASH, std::vector<int32_t>(7, 0));  // TODO FIX?
      state.action_cards[curr][1] = 0;
      if (curr == agent) {
        info.hand_cards = sub_cards(info.hand_cards, move.second);
        info.trashed_cards = move.second;
      }
      state.num_cards[curr] -= 2;
      state.acting_player_id = opp;
      break;
    case TYPE_2_CHOOSE_1_2:
      state.round_moves[curr].emplace_back(move);
      state.action_cards[curr][2] = 0;
      if (curr == agent) {
        info.hand_cards = sub_cards(info.hand_cards, move.second);
      }
      state.decision_cards_1_2 = move.second;
      state.num_cards[curr] -= 3;
      state.acting_player_id = opp;
      is_draw_card = false;
      break;
    case TYPE_3_CHOOSE_2_2:
      state.round_moves[curr].emplace_back(move);
      state.action_cards[curr][3] = 0;
      state.decision_cards_2_2 = {std::vector<int32_t>(move.second.begin(), move.second.begin() + 7),
                                  std::vector<int32_t>(move.second.begin() + 7, move.second.end())};
      if (curr == agent) {
        info.hand_cards = sub_cards(info.hand_cards, state.decision_cards_2_2.first);
        info.hand_cards = sub_cards(info.hand_cards, state.decision_cards_2_2.second);
      }
      state.num_cards[curr] -= 4;
      state.acting_player_id = opp;
      is_draw_card = false;
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
        card_play_init();
      } else {
        json msg;
        msg["type"] = "winner";
        msg["desc"] = players[winner]->toString();
        server.send_message(msg);
      }
    } else {
      auto& new_info = private_info_sets[state.acting_player_id];
      if (is_draw_card) {
        state.num_cards[state.acting_player_id]++;
        if (state.acting_player_id == agent) {
          auto card = draw_card();
          info.hand_cards[card] += 1;
        }
      }
      if (state.acting_player_id == agent) {
        new_info.moves = get_moves();
      }
    }
  }

  void reset()
  {
    winner = -1;
    round = 1;
    state = GameState();
    private_info_sets[0] = PrivateInfoSet();
    private_info_sets[1] = PrivateInfoSet();
    card_play_init();
  }

  GameState state;
  WebSocketServer server;
  std::vector<PrivateInfoSet> private_info_sets;
  std::vector<std::unique_ptr<IPlayer>> players;
  int round = 1;
  int winner = -1;
  int human = -1;
  int agent = -1;
  std::vector<int32_t> num_wins = {0, 0};
};

#endif
