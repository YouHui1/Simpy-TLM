#include "tlm_router/initiator.h"
#include "tlm_router/target.h"
#include "tlm_router/router.h"

SC_MODULE(Top)
{
  Initiator* initiator;
  Router<4>* router;
  Memory*    memory[4];

  SC_CTOR(Top)
  {
    // Instantiate components
    initiator = new Initiator("initiator");
    router    = new Router<4>("router");
    for (int i = 0; i < 4; i++)
    {
      char txt[20];
      sprintf(txt, "memory_%d", i);
      memory[i]   = new Memory(txt);
    }

    // Bind sockets
    initiator->socket.bind( router->target_socket );
    for (int i = 0; i < 4; i++)
      router->initiator_socket[i]->bind( memory[i]->socket );
  }
};

int sc_main(int argc, char* argv[])
{
  Top top("top");
  sc_start();
  return 0;
}
