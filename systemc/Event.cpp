#include "sysc/kernel/sc_event.h"
#include "sysc/kernel/sc_externs.h"
#include "sysc/kernel/sc_module.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/kernel/sc_time.h"
#include <systemc>

using namespace sc_core;
using namespace std;

SC_MODULE(Event) {
    sc_event e;
    SC_CTOR(Event) {
        SC_THREAD(trigger);
        SC_THREAD(catcher);
    }

    void trigger() {
        while (true) {
            e.notify(1, sc_core::SC_SEC);
            if (sc_time_stamp() == sc_time(4, SC_SEC)) {
                e.cancel();
            }
            wait(2, SC_SEC);
        }
    }

    void catcher() {
        while (true) {
            wait(e);
            cout << "Event cateched at " << sc_time_stamp() << endl;
        }
    }

};

int sc_main(int argc, char **argv){
    Event event("event");
    sc_start(8, sc_core::SC_SEC);
    return 0;
}
