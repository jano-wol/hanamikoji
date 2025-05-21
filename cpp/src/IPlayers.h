#ifndef HANAMIKOJI_IPLAYERS_H_INCLUDED
#define HANAMIKOJI_IPLAYERS_H_INCLUDED

#include "Game.h"

class IPlayer
{
public:
  virtual int act(const GameState& gameState, const PrivateInfoSet& privateInfoSet) = 0;
  virtual ~IPlayer() = default;
};

#endif
