#include <torch/script.h>
#include <filesystem>
#include <iostream>
#include "DeepAgent.h"
#include "Game.h"
#include "Human.h"

int main(int /*argc*/, char* argv[])
{
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
  std::vector<int> results{0, 0};
  while (true) {
    env.reset();
    while (env.winner == -1) {
      env.step();
    }
  }
}
