#ifndef HANAMIKOJI_RANDOM_PLAYER_H_INCLUDED
#define HANAMIKOJI_RANDOM_PLAYER_H_INCLUDED

#include "IPlayers.h"

class RandomPlayer : public IPlayer
{
public:
  int act(const GameState& /*gameState*/, const PrivateInfoSet& /*privateInfoSet*/) override
  {
    static std::mt19937 rng{std::random_device{}()};
    std::uniform_int_distribution<int> dist(0, 9);
    return dist(rng);
  }
};

#endif