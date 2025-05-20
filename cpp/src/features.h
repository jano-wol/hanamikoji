#ifndef HANAMIKOJI_FEATURES_H_INCLUDED
#define HANAMIKOJI_FEATURES_H_INCLUDED

#include <torch/script.h>
#include "game.h"
#include "movegen.h"

// Struct to hold model input
struct TorchObs {
    torch::Tensor x_batch;   // [num_moves, 169]
    torch::Tensor x_no_move; // [169]
    torch::Tensor z_batch;   // [num_moves, 12, 63]
};

// Helper: flatten 2D vector to tensor
torch::Tensor toTensor2D(const std::vector<std::vector<float>>& data) {
    const int rows = data.size();
    const int cols = data[0].size();
    torch::Tensor tensor = torch::empty({rows, cols}, torch::kFloat32);
    for (int i = 0; i < rows; ++i)
        std::memcpy(tensor[i].data_ptr<float>(), data[i].data(), cols * sizeof(float));
    return tensor;
}

// Helper: flatten 3D vector to tensor
torch::Tensor toTensor3D(const std::vector<std::vector<std::vector<float>>>& data) {
    const int dim0 = data.size();
    const int dim1 = data[0].size();
    const int dim2 = data[0][0].size();
    torch::Tensor tensor = torch::empty({dim0, dim1, dim2}, torch::kFloat32);
    for (int i = 0; i < dim0; ++i)
        for (int j = 0; j < dim1; ++j)
            std::memcpy(tensor[i][j].data_ptr<float>(), data[i][j].data(), dim2 * sizeof(float));
    return tensor;
}

// Main function: creates input tensors
TorchObs get_obs_torch(const GameState& gameState, const PrivateInfoSet& privateInfoSet) {
    const int num_moves = privateInfoSet.moves.size();

    std::vector<std::vector<float>> x_batch_vec(num_moves, std::vector<float>(169));
    std::vector<float> x_no_move_vec(169);
    std::vector<std::vector<std::vector<float>>> z_batch_vec(num_moves, std::vector<std::vector<float>>(12, std::vector<float>(63)));

    // ... fill x_batch_vec[j], x_no_move_vec, z_batch_vec[j]
    // using logic from your previous feature encoding,
    // but cast all values to float

    // For example:
    // x_batch_vec[j][i] = static_cast<float>(geisha_points[i]);
    // or for move encoding:
    // move_vec = my_move2array(move);
    // for (int k = 0; k < 63; ++k) x_batch_vec[j][106 + k] = static_cast<float>(move_vec[k]);

    // Convert to torch::Tensor
    torch::Tensor x_batch = toTensor2D(x_batch_vec);       // [num_moves, 169]
    torch::Tensor x_no_move = torch::from_blob(x_no_move_vec.data(), {169}, torch::kFloat32).clone(); // clone to own memory
    torch::Tensor z_batch = toTensor3D(z_batch_vec);       // [num_moves, 12, 63]

    return {x_batch, x_no_move, z_batch};
}

#endif
