#include <torch/script.h>
#include <iostream>

torch::Tensor run_model(torch::jit::script::Module& model, torch::Tensor z, torch::Tensor x) {
    std::vector<torch::jit::IValue> inputs;
    inputs.push_back(z);
    inputs.push_back(x);
    return model.forward(inputs).toTensor();
}

int main() {
    try {
        torch::jit::script::Module model_first = torch::jit::load("./first.pt");
        torch::jit::script::Module model_second = torch::jit::load("./second.pt");

        // Create dummy input (same shape as during tracing)
        int a = 43;
        torch::Tensor z = torch::randn({a, 12, 63});  // Replace with actual value
        torch::Tensor x = torch::randn({43, 169});        // Replace with actual value

        // Choose model based on player ID
        std::string player_id = "first";  // or "second"

        torch::Tensor result;
        if (player_id == "first")
            result = run_model(model_first, z, x);
        else
            result = run_model(model_second, z, x);

        std::cout << "Model output: " << result << std::endl;

    } catch (const c10::Error& e) {
        std::cerr << "Error loading or running model: " << e.what() << std::endl;
        return -1;
    }

    return 0;
}

