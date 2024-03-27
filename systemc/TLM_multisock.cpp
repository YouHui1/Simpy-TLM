#include "multi-socket-example/initiator.h"
#include "multi-socket-example/bus.h"
#include "multi-socket-example/target.h"

// *****************************************************************************************
// Top-level module instantiates 4 initiators, a bus, and 4 targets
// *****************************************************************************************
const int n = 4;

SC_MODULE(Top)
{
  Initiator* init[n];
  Bus*       bus;
  Target*    target[n];

  SC_CTOR(Top)
  {
    bus   = new Bus("bus");

    // ***************************************************************************
    // bus->init_socket and bus->targ_socket are multi-sockets, each bound 4 times
    // ***************************************************************************

    for (int i = 0; i < n; i++)
    {
      char txt[20];
      sprintf(txt, "init_%d", i);
      init[i] = new Initiator(txt);
      init[i]->socket.bind( bus->targ_socket );
    }

    for (int i = 0; i < n; i++)
    {
      char txt[20];
      sprintf(txt, "target_%d", i);
      target[i] = new Target(txt);

      bus->init_socket.bind( target[i]->socket );
    }
  }
};

int sc_main(int argc, char* argv[])
{
  Top top("top");
  srand(120);
  sc_start();

  cout << "\n***** Messages have been written to file output.txt                    *****\n";
  cout << "***** Select 'Download files after run' to read file in EDA Playground *****\n\n";

  return 0;
}
