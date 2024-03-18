#include "sysc/kernel/sc_externs.h"
#include "sysc/kernel/sc_module.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/kernel/sc_time.h"
#include <systemc>

using namespace sc_core;
using namespace std;

SC_MODULE(Concurrency) {
    SC_CTOR(Concurrency) {
        SC_THREAD(thread1);
        SC_THREAD(thread2);
    }

    void thread1() {
        while (true) {
            cout << sc_time_stamp() << " : thread1" << endl;
            wait(2, sc_core::SC_SEC);
        }
    }

    void thread2() {
        while (true) {
            cout << "\t" << sc_time_stamp() << " : thread2" << endl;
            wait(3, sc_core::SC_SEC);
        }
    }
};

int sc_main(int argc, char **argv){
    Concurrency concurrency("concurrency");
    sc_start(10, sc_core::SC_SEC);
    return 0;
}
