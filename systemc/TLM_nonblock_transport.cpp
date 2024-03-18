#include "nonblock_transport/initiator.h"
#include "nonblock_transport/target.h"

SC_MODULE(Top)
{
  Initiator *initiator;
  Target    *target;

  SC_CTOR(Top)
  {
    // Instantiate components
    initiator = new Initiator("initiator");
    target    = new Target   ("target");

    // One initiator is bound directly to one target with no intervening bus

    // Bind initiator socket to target socket
    initiator->socket.bind(target->socket);
  }
};

int sc_main(int argc, char* argv[])
{
  Top top("top");
  sc_start();

  cout << "\n***** Messages have been written to file output.txt                    *****\n";
  cout << "***** Select 'Download files after run' to read file in EDA Playground *****\n\n";

  return 0;
}
