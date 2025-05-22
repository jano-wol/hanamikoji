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
  GameEnv(std::vector<std::unique_ptr<IPlayer>> players_, int /*port*/)
      : private_info_sets{PrivateInfoSet(), PrivateInfoSet()}, players(std::move(players_)), round(1), winner(-1)
  {}

  int get_opp() { return 1 - state.acting_player_id; }

  std::vector<std::pair<int, std::vector<int32_t>>> get_moves()
  {
    MovesGener mg(private_info_sets[state.acting_player_id].hand_cards, state.action_cards[state.acting_player_id],
                  state.decision_cards_1_2, state.decision_cards_2_2);
    return mg.getMoves();
  }

  void card_play_init(std::vector<int32_t> startHand)
  {
    private_info_sets[agent].hand_cards = startHand;
    private_info_sets[state.acting_player_id].moves = get_moves();
  }

  int draw_card() { return {}; }

  std::vector<int32_t> reveal_human_stash() { return {}; }

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

  std::pair<std::pair<int, std::vector<int32_t>>, double> eval()
  {
    int curr = state.acting_player_id;
    auto& info = private_info_sets[curr];
    auto move = players[curr]->act(state, info);
    return move;
  }

  void reset(std::vector<int32_t> geishaPreferences, std::vector<int32_t> startHand)
  {
    winner = -1;
    round = 1;
    state = GameState();
    private_info_sets[0] = PrivateInfoSet();
    private_info_sets[1] = PrivateInfoSet();
    for (int i = 0; i < 7; ++i) {
      if (geishaPreferences[i] == 1) {
        state.geisha_preferences[0][i] = 1;
      }
      if (geishaPreferences[i] == -1) {
        state.geisha_preferences[1][i] = 1;
      }
    }

    int agentPlace = 0;
    if (players[agentPlace]->toString() != "DeepAgent") {
      std::swap(players[0], players[1]);
    }
    if (players[0]->toString() == "Human") {
      human = 0;
      agent = 1;
    } else {
      human = 1;
      agent = 0;
    }
    card_play_init(startHand);
  }

  GameState state;
  // WebSocketServer server;
  std::vector<PrivateInfoSet> private_info_sets;
  std::vector<std::unique_ptr<IPlayer>> players;
  int round = 1;
  int winner = -1;
  int human = -1;
  int agent = -1;
  std::vector<int32_t> num_wins = {0, 0};
};

#endif
