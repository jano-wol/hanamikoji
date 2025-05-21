cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project(MyLstmInference)

find_package(Torch REQUIRED)

add_executable(main main.cpp)

message(${PROJECT_SOURCE_DIR}!!!)
target_include_directories(main PRIVATE
    ${PROJECT_SOURCE_DIR}/../ext/websocketpp
    ${PROJECT_SOURCE_DIR}/../ext/asio-1.30.2/include
)

find_package(Threads REQUIRED)

target_link_libraries(main
    "${TORCH_LIBRARIES}"
    Threads::Threads
)