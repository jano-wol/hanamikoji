#include <torch/script.h>
#include <filesystem>
#include <iostream>
#include "DeepAgent.h"
#include "Game.h"
#include "Human.h"

const std::vector<char> cardTypes = {'A', 'B', 'C', 'D', 'E', 'F', 'G'};
const std::vector<int> cardCounts = {2, 2, 2, 3, 3, 4, 5};

std::vector<std::vector<int32_t>> allGeishaPreferences;
std::vector<std::vector<int32_t>> allStartHands;

void generateAllGeishaPreferences()
{
  const int length = 7;
  const int total = 2187;  // 3^7

  for (int i = 0; i < total; ++i) {
    int n = i;
    std::vector<int32_t> vec(length);

    for (int j = length - 1; j >= 0; --j) {
      vec[j] = (n % 3) - 1;
      n /= 3;
    }

    allGeishaPreferences.push_back(vec);
  }
}

void backtrack(std::vector<int>& current, int index, int remaining)
{
  if (remaining == 0) {
    allStartHands.push_back(current);
    return;
  }
  if (index >= int(cardTypes.size()))
    return;

  for (int count = 0; count <= std::min(remaining, cardCounts[index]); ++count) {
    current[index] = count;
    backtrack(current, index + 1, remaining - count);
  }
  current[index] = 0;  // Backtrack
}

void dumpSortedByValue(const std::map<std::vector<int32_t>, double>& ret, const std::string& filename)
{
  // Create a vector of pairs to sort by value
  std::vector<std::pair<std::vector<int32_t>, double>> sorted_entries(ret.begin(), ret.end());

  // Sort by the double value (ascending)
  std::sort(sorted_entries.begin(), sorted_entries.end(),
            [](const auto& a, const auto& b) { return a.second < b.second; });

  // Open output file
  std::ofstream out(filename);
  if (!out) {
    std::cerr << "Error: Cannot open file " << filename << " for writing.\n";
    return;
  }

  // Write to file
  for (const auto& [vec, val] : sorted_entries) {
    out << val << " : [";
    for (size_t i = 0; i < vec.size(); ++i) {
      out << vec[i];
      if (i < vec.size() - 1)
        out << ", ";
    }
    out << "]\n";
  }

  out.close();
  std::cout << "Dumped to file: " << filename << std::endl;
}

int is_ended(std::vector<int32_t> geishaPreferences)
{
  int first_geisha_win = 0;
  int first_geisha_points = 0;
  int second_geisha_win = 0;
  int second_geisha_points = 0;

  for (int i = 0; i < 7; ++i) {
    if (geishaPreferences[i] == 1) {
      first_geisha_win++;
      first_geisha_points += cardCounts[i];
    }
    if (geishaPreferences[i] == -1) {
      second_geisha_win++;
      second_geisha_points += cardCounts[i];
    }
  }

  if (first_geisha_points >= 11)
    return 1;
  if (second_geisha_points >= 11)
    return -1;
  if (first_geisha_win >= 4)
    return 1;
  if (second_geisha_win >= 4)
    return -1;
  return 0;
}

int main(int /*argc*/, char* argv[])
{
  generateAllGeishaPreferences();
  std::vector<int> current(cardTypes.size(), 0);
  backtrack(current, 0, 7);

  std::filesystem::path exe_path = argv[0];
  std::filesystem::path exe_dir = exe_path.parent_path();
  if (exe_dir.empty()) {
    exe_dir = std::filesystem::current_path();
  }

  auto deep_agent_1 = std::make_unique<DeepAgent>(exe_dir);
  auto human = std::make_unique<Human>();
  std::vector<std::unique_ptr<IPlayer>> players;
  players.emplace_back(std::move(deep_agent_1));
  players.emplace_back(std::move(human));

  GameEnv env(std::move(players), 8768);

  std::map<std::vector<int32_t>, double> ret;

  int r = 0;
  for (const auto& geishaPreference : allGeishaPreferences) {
    auto win = is_ended(geishaPreference);
    if (win != 0) {
      ret[geishaPreference] = win;
      continue;
    }
    ++r;
    if (r == 5)
    {
      break;
    }
    double p = 0;
    for (const auto& startHand : allStartHands) {
      env.reset(geishaPreference, startHand);
      auto res = env.eval();
      double p_ = res.second;
      if (p_ > 1.0) {
        p_ = 1.0;
      }
      if (p_ < -1.0) {
        p_ = -1.0;
      }
      p += p_;
    }
    ret[geishaPreference] = p / double(allStartHands.size());
  }
  dumpSortedByValue(ret, "jano.txt");
}