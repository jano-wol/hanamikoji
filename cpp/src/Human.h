#ifndef HANAMIKOJI_HUMAN_H_INCLUDED
#define HANAMIKOJI_HUMAN_H_INCLUDED

#include "IPlayer.h"

class Human : public IPlayer
{
public:
  Human() {}

  std::pair<int, std::vector<int32_t>> act(const GameState& /*gameState*/,
                                           const PrivateInfoSet& /*privateInfoSet*/) override
  {
    return {};
  }

  std::string toString() override { return "Human"; }
};

#endif
