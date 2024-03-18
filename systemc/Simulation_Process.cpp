#include "sysc/communication/sc_clock.h"
#include "sysc/kernel/sc_externs.h"
#include "sysc/kernel/sc_module.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/kernel/sc_time.h"
#include <iostream>
#include <systemc>
using namespace sc_core;
using namespace std;

SC_MODULE(Process) {
    sc_clock clk;
    SC_CTOR(Process) : clk("clk", 1, SC_SEC) {
        SC_METHOD(method);
        SC_THREAD(thread);
        SC_CTHREAD(cthread, clk);
    }

    void method(void) {
        cout << "method triggered @ " << sc_time_stamp() << endl;
        next_trigger(sc_time(1, SC_SEC));
    }

    void thread() {
        while (true) {
            cout << "thread triggered @ " << sc_time_stamp() << endl;
            wait(1, sc_core::SC_SEC);
        }
    }

    void cthread() {
        while (true) {
            cout << "cthread triggered @ " << sc_time_stamp() << endl;
            wait();
        }
    }
};

int sc_main(int argc, char **argv){
    Process process("process");
    cout << "execution phase begins @ " << sc_time_stamp() << endl;
    sc_start(2, sc_core::SC_SEC);
    cout << "execution phase ends @ " << sc_time_stamp() << endl;
    return 0;
}
