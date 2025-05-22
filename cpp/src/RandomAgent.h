#ifndef HANAMIKOJI_RANDOM_AGENT_H_INCLUDED
#define HANAMIKOJI_RANDOM_AGENT_H_INCLUDED

#include <random>

#include "IPlayer.h"

class RandomAgent : public IPlayer
{
public:
  std::pair<std::pair<int, std::vector<int32_t>>, double> act(const GameState& /*gameState*/,
                                                              const PrivateInfoSet& privateInfoSet) override
  {
    return {};
  }

  std::string toString() override { return "RandomAgent"; }
};

#endif