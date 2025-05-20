#ifndef HANAMIKOJI_MOVE_GEN_H_INCLUDED
#define HANAMIKOJI_MOVE_GEN_H_INCLUDED

#include <utility>
#include <vector>

const int TYPE_0_STASH = 0;
const int TYPE_1_TRASH = 1;
const int TYPE_2_CHOOSE_1_2 = 2;
const int TYPE_3_CHOOSE_2_2 = 3;
const int TYPE_4_RESOLVE_1_2 = 4;
const int TYPE_5_RESOLVE_2_2 = 5;

class MovesGener {
public:
  std::vector<std::pair<int, std::vector<int>>> moves;

  MovesGener(const std::vector<int> &cards_list,
             const std::vector<int> &action_cards,
             const std::vector<int> &choose_1_2,
             const std::pair<std::vector<int>, std::vector<int>> &choose_2_2) {

    if (!choose_1_2.empty()) {
      for (int i = 0; i < 7; ++i) {
        if (choose_1_2[i] != 0) {
          std::vector<int> a(7, 0);
          std::vector<int> b = choose_1_2;
          a[i] = 1;
          b[i] -= 1;
          std::vector<int> combined(14);
          std::copy(a.begin(), a.end(), combined.begin());
          std::copy(b.begin(), b.end(), combined.begin() + 7);
          moves.emplace_back(TYPE_4_RESOLVE_1_2, combined);
        }
      }
      return;
    }

    if (!choose_2_2.first.empty()) {
      std::vector<int> combined(14);
      std::copy(choose_2_2.first.begin(), choose_2_2.first.end(),
                combined.begin());
      std::copy(choose_2_2.second.begin(), choose_2_2.second.end(),
                combined.begin() + 7);
      moves.emplace_back(TYPE_5_RESOLVE_2_2, combined);

      if (choose_2_2.first != choose_2_2.second) {
        std::vector<int> combined(14);
        std::copy(choose_2_2.second.begin(), choose_2_2.second.end(),
                  combined.begin());
        std::copy(choose_2_2.first.begin(), choose_2_2.first.end(),
                  combined.begin() + 7);
        moves.emplace_back(TYPE_5_RESOLVE_2_2, combined);
      }
      return;
    }

    if (action_cards[0] == 1) {
      for (int i = 0; i < 7; ++i) {
        if (cards_list[i] == 0)
          continue;
        std::vector<int> vec(7, 0);
        vec[i] = 1;
        moves.emplace_back(TYPE_0_STASH, vec);
      }
    }

    if (action_cards[1] == 1) {
      for (int i = 0; i < 7; ++i) {
        if (cards_list[i] == 0)
          continue;
        for (int j = i; j < 7; ++j) {
          if ((i == j && cards_list[i] < 2) || (i != j && cards_list[j] == 0))
            continue;
          std::vector<int> vec(7, 0);
          vec[i]++;
          vec[j]++;
          moves.emplace_back(TYPE_1_TRASH, vec);
        }
      }
    }

    if (action_cards[2] == 1) {
      for (int i = 0; i < 7; ++i) {
        if (cards_list[i] == 0)
          continue;
        int hand_i = cards_list[i] - 1;
        for (int j = i; j < 7; ++j) {
          if ((i == j && hand_i == 0) || (i != j && cards_list[j] == 0))
            continue;
          int hand_j = (i == j) ? hand_i - 1 : cards_list[j] - 1;
          for (int k = j; k < 7; ++k) {
            if ((j == k && hand_j == 0) || (j != k && cards_list[k] == 0))
              continue;
            std::vector<int> vec(7, 0);
            vec[i]++;
            vec[j]++;
            vec[k]++;
            moves.emplace_back(TYPE_2_CHOOSE_1_2, vec);
          }
        }
      }
    }

    if (action_cards[3] == 1) {
      for (int p = 0; p < 7; ++p) {
        if (cards_list[p] == 0)
          continue;
        for (int q = p; q < 7; ++q) {
          if ((p == q && cards_list[p] < 2) || (p != q && cards_list[q] == 0))
            continue;

          std::vector<int> temp_hand = cards_list;
          temp_hand[p]--;
          temp_hand[q]--;

          if (temp_hand[p] < 0 || temp_hand[q] < 0)
            continue; // TODO this is needed??

          for (int r = p; r < 7; ++r) {
            if (temp_hand[r] == 0)
              continue;
            for (int s = r; s < 7; ++s) {
              if ((r == s && temp_hand[r] < 2) || (r != s && temp_hand[s] == 0))
                continue;
              if (p == r && q > s)
                continue;

              std::vector<int> pair1(7, 0), pair2(7, 0);
              pair1[p]++;
              pair1[q]++;
              pair2[r]++;
              pair2[s]++;

              std::vector<int> combined(14);
              std::copy(pair1.begin(), pair1.end(), combined.begin());
              std::copy(pair2.begin(), pair2.end(), combined.begin() + 7);
              moves.emplace_back(TYPE_3_CHOOSE_2_2, combined);
            }
          }
        }
      }
    }
  }

  const std::vector<std::pair<int, std::vector<int>>> &getMoves() const {
    return moves;
  }
};

#endif
