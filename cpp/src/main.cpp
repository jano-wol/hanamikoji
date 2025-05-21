#include <torch/script.h>
#include <filesystem>
#include <iostream>
#include "DeepAgent.h"
#include "Game.h"
#include "RandomAgent.h"

torch::Tensor run_model(torch::jit::script::Module& model, torch::Tensor z, torch::Tensor x)
{
  std::vector<torch::jit::IValue> inputs;
  inputs.push_back(z);
  inputs.push_back(x);
  return model.forward(inputs).toTensor();
}

int main(int argc, char* argv[]) { return 0; }
