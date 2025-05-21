#include <torch/script.h>
#include <filesystem>
#include <iostream>
#include "DeepAgent.h"
#include "Game.h"
#include "RandomAgent.h"

int main(int /*argc*/, char* argv[])
{
  std::filesystem::path exe_path = argv[0];
  std::filesystem::path exe_dir = exe_path.parent_path();
  if (exe_dir.empty()) {
    exe_dir = std::filesystem::current_path();
  }

  auto deep_agent_1 = std::make_unique<DeepAgent>(exe_dir);
  // auto deep_agent_2 = std::make_unique<DeepAgent>(exe_dir);
  auto random_agent = std::make_unique<RandomAgent>();
  std::vector<std::unique_ptr<IPlayer>> players;
  players.emplace_back(std::move(random_agent));
  players.emplace_back(std::move(deep_agent_1));

  GameEnv env(std::move(players));
  env.init_card_play();
  while (env.winner == -1) {
    env.step();
  }
  std::cout << "winner=" << env.winner << "\n";
}
