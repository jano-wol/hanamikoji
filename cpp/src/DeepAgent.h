#ifndef HANAMIKOJI_DEEP_AGENT_H_INCLUDED
#define HANAMIKOJI_DEEP_AGENT_H_INCLUDED

#include <torch/script.h>
#include <iostream>
#include "Features.h"
#include "Game.h"
#include "IPlayer.h"

torch::Tensor run_model(torch::jit::script::Module& model, torch::Tensor z, torch::Tensor x)
{
  std::vector<torch::jit::IValue> inputs;
  inputs.push_back(z);
  inputs.push_back(x);
  return model.forward(inputs).toTensor();
}

class DeepAgent : public IPlayer
{
public:
  DeepAgent(const std::string& exe_dir)
  {
    model_first = torch::jit::load(exe_dir + "/first.pt");
    model_second = torch::jit::load(exe_dir + "/second.pt");
    model_first.eval();
    model_second.eval();
  }

  int act(const GameState& gameState, const PrivateInfoSet& privateInfoSet) override
  {
    if (privateInfoSet.moves.size() == 1) {
      return 0;
    }

    TorchObs obs = get_obs(gameState, privateInfoSet);
    torch::Tensor values;
    if (gameState.id_to_round_id[gameState.acting_player_id] == 0) {
      values = run_model(model_first, obs.z_batch, obs.x_batch);
    } else {
      values = run_model(model_second, obs.z_batch, obs.x_batch);
    }
    int64_t best_move_index = values.argmax(0).item<int64_t>();
    return static_cast<int>(best_move_index);
  }

  std::string toString() override { return "DeepAgent"; }

  torch::jit::script::Module model_first;
  torch::jit::script::Module model_second;
};

#endif
