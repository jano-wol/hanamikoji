#include <torch/script.h>
#include <filesystem>
#include <iostream>

torch::Tensor run_model(torch::jit::script::Module& model, torch::Tensor z, torch::Tensor x)
{
  std::vector<torch::jit::IValue> inputs;
  inputs.push_back(z);
  inputs.push_back(x);
  return model.forward(inputs).toTensor();
}

int main(int argc, char* argv[])
{
  if (argc < 1) {
    std::cerr << "No argv[0] found!" << std::endl;
    return -1;
  }

  // Get path of executable
  std::filesystem::path exe_path = argv[0];
  std::filesystem::path exe_dir = exe_path.parent_path();

  // If no parent path, fallback to current directory
  if (exe_dir.empty()) {
    exe_dir = std::filesystem::current_path();
  }

  // Compose model paths
  std::filesystem::path model_first_path = exe_dir / "first.pt";
  std::filesystem::path model_second_path = exe_dir / "second.pt";
  torch::jit::script::Module model_first = torch::jit::load(model_first_path);
  torch::jit::script::Module model_second = torch::jit::load(model_second_path);

  // Create dummy input (same shape as during tracing)
  int a = 43;
  torch::Tensor z = torch::randn({a, 12, 63});  // Replace with actual value
  torch::Tensor x = torch::randn({43, 169});    // Replace with actual value

  // Choose model based on player ID
  std::string player_id = "first";  // or "second"

  torch::Tensor result;
  if (player_id == "first")
    result = run_model(model_first, z, x);
  else
    result = run_model(model_second, z, x);

  std::cout << "Model output: " << result << std::endl;

  return 0;
}
