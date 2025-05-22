#!/bin/bash
set -ex
source "$(dirname "${0}")/build/init.sh"
rm -rf "${BUILD_FOLDER}"
mkdir -p "${BUILD_FOLDER}"
cd "${BUILD_FOLDER}"
cmake "${WORKSPACE_FOLDER}/cpp" "-DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}" "-DCMAKE_MAKE_PROGRAM=${CMAKE_MAKE_PROGRAM}" -G "Ninja" "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}" "-DCMAKE_PREFIX_PATH=${LIB_TORCH_FOLDER}/libtorch"
BIN_FOLDER="${BUILD_FOLDER}/bin"
mkdir -p "${BIN_FOLDER}"
cp "${WORKSPACE_FOLDER}/baselines/first.pt" "${BIN_FOLDER}/first.pt"
cp "${WORKSPACE_FOLDER}/baselines/second.pt" "${BIN_FOLDER}/second.pt"
