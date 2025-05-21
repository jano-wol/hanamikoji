#ifndef HANAMIKOJI_RANDOM_AGENT_H_INCLUDED
#define HANAMIKOJI_RANDOM_AGENT_H_INCLUDED

#include <random>

#include "IPlayer.h"

class RandomAgent : public IPlayer
{
public:
  int act(const GameState& /*gameState*/, const PrivateInfoSet& privateInfoSet) override
  {
    static std::mt19937 rng{std::random_device{}()};
    std::uniform_int_distribution<size_t> dist(0, privateInfoSet.moves.size() - 1);
    return dist(rng);
  }
};

#endif