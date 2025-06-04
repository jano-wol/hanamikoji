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
std::map<std::vector<int32_t>, double> startHandDist;

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
  std::sort(sorted_entries.begin(), sorted_entries.end(), [](const auto& a, const auto& b) {
    if (a.second != b.second)
      return a.second > b.second;
    return a.first > b.first;  // Tie-breaker: lexicographic vector comparison
  });
  // Open output file
  std::ofstream out(filename);
  if (!out) {
    std::cerr << "Error: Cannot open file " << filename << " for writing.\n";
    return;
  }

  // Write to file
  for (const auto& [vec, val] : sorted_entries) {
    out << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
      out << vec[i];
      if (i < vec.size() - 1)
        out << ", ";
    }
    out << "] : " << val << "\n";
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

int64_t C(int n, int k)
{
  if (k < 0 || k > n)
    return 0;
  k = std::min(k, n - k);  // Take advantage of symmetry
  int64_t result = 1;
  for (int i = 1; i <= k; ++i) {
    result *= (n - i + 1);
    result /= i;
  }
  return result;
}

void initStartHandDist()
{
  double all = 116280.0;
  for (const auto& startHand : allStartHands) {
    int64_t val = 1;
    for (int i = 0; i < 7; ++i) {
      val *= C(cardCounts[i], startHand[i]);
    }
    startHandDist[startHand] = double(val) / all;
  }
}

int main(int /*argc*/, char* argv[])
{
  std::vector<int> current(cardTypes.size(), 0);
  backtrack(current, 0, 7);
  initStartHandDist();

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

  std::vector<int32_t> geishaPreference;
  for (int i = 0; i < 7; ++i)
  {
    geishaPreference.push_back(0);
  }
  for (const auto& startHand : allStartHands) {
      env.reset(geishaPreference, startHand);
      auto res = env.eval();
      ret[startHand] = res.second;
    }
  std::cout << "totalCall=" << env.call << "\n";
  dumpSortedByValue(ret, "jano.txt");
}