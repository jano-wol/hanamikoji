#ifndef HANAMIKOJI_DEEP_AGENT_H_INCLUDED
#define HANAMIKOJI_DEEP_AGENT_H_INCLUDED

#include "IPlayers.h"

class DeepAgent : public IPlayer
{
public:
  int act(const GameState& gameState, const PrivateInfoSet& privateInfoSet) override { return 42; }
};

#endif