cmake_minimum_required(VERSION 3.15)
project(algos)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)
add_compile_options(-Wall -Wcast-qual -Wextra -Wshadow)
add_link_options(-Wall -Wcast-qual -Wextra -Wshadow)
if (CMAKE_CXX_COMPILER STREQUAL "clang++")
add_compile_options(-stdlib=libc++)
add_link_options(-stdlib=libc++)
endif()
if (${CMAKE_BUILD_TYPE} STREQUAL "release")
add_compile_options(-flto=auto)
add_link_options(-flto=auto)
else()
add_compile_options(-g -fsanitize=address)
add_link_options(-fsanitize=address)
endif()
enable_testing()
add_subdirectory(src)
