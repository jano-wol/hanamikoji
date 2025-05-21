#include <torch/script.h>
#include "Features.h"
#include "Game.h"
#include "IPlayer.h"

class DeepAgent : public IPlayer
{
public:
  DeepAgent(const std::string& ckpt_dir_path)
  {
    model_first = torch::jit::load(ckpt_dir_path + "/first.pt");
    model_second = torch::jit::load(ckpt_dir_path + "/second.pt");
    model_first.eval();
    model_second.eval();

    if (torch::cuda::is_available()) {
      model_first.to(torch::kCUDA);
      model_second.to(torch::kCUDA);
    }
  }

  int act(const GameState& gameState, const PrivateInfoSet& infoset) override
  {
    const auto& moves = infoset.moves;
    if (moves.size() == 1) {
      return 0;
    }

    TorchObs obs = get_obs(gameState, infoset);  // assume implemented
    torch::Tensor x = obs.x_batch.to(torch::kFloat32);
    torch::Tensor z = obs.z_batch.to(torch::kFloat32);

    if (torch::cuda::is_available()) {
      x = x.to(torch::kCUDA);
      z = z.to(torch::kCUDA);
    }

    torch::jit::Module& model =
        infoset.id_to_round_id.at(infoset.acting_player_id) == "first" ? model_first : model_second;

    auto output = model.forward({z, x}).toGenericDict();
    torch::Tensor y_pred = output.at("values").toTensor();

    int best_idx = y_pred.argmax(0).item<int>();
    return moves[best_idx];
  }

private:
  torch::jit::Module model_first;
  torch::jit::Module model_second;
};
