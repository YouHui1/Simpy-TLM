#include "sysc/datatypes/int/sc_nbdefs.h"
#include "sysc/kernel/sc_externs.h"
#include "sysc/kernel/sc_module.h"
#include "sysc/kernel/sc_module_name.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/kernel/sc_time.h"
#include "sysc/kernel/sc_wait.h"
#include "sysc/utils/sc_report.h"
#include "tlm_core/tlm_2/tlm_2_interfaces/tlm_dmi.h"
#include "tlm_core/tlm_2/tlm_generic_payload/tlm_gp.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#define SC_INCLUDE_DYNAMIC_PROCESS

#include <systemc>
using namespace sc_core;
using namespace sc_dt;
using namespace std;

#include "tlm.h"
#include "tlm_utils/simple_initiator_socket.h"
#include "tlm_utils/simple_target_socket.h"

class Initiator : public sc_module {
public:
    SC_HAS_PROCESS(Initiator);
    tlm_utils::simple_initiator_socket<Initiator> socket;

    Initiator(const sc_module_name& name) : socket("socket"){
        socket.register_invalidate_direct_mem_ptr(this, &Initiator::invalidate_direct_mem_ptr);

        SC_THREAD(thread_process);
    }

    void thread_process() {
        tlm::tlm_generic_payload* trans = new tlm::tlm_generic_payload;
        sc_time delay = sc_time(10, SC_NS);

        for (int i = 0; i < 128 ; i += 4) {
            ///...
            tlm::tlm_command cmd = static_cast<tlm::tlm_command>(rand() % 2);
            if (cmd == tlm::TLM_WRITE_COMMAND) {
                data = 0xFF000000 | i;
            }

            if (dmi_ptr_valid) {
                if (cmd == tlm::TLM_READ_COMMAND) {
                    assert(dmi_data.is_read_allowed());
                    memcpy(&data, dmi_data.get_dmi_ptr(), 4);
                    wait(dmi_data.get_read_latency());
                } else if (cmd == tlm::TLM_WRITE_COMMAND) {
                    assert(dmi_data.is_write_allowed());
                    memcpy(dmi_data.get_dmi_ptr(), &data, 4);
                    wait(dmi_data.get_write_latency());
                }
                //...
                cout << "trans = { " << (cmd ? 'W' : 'R') << ", " << hex << i
                    << " } , data = " << hex << data << " at time " << sc_time_stamp() << endl;

            } else {
                trans->set_command(cmd);
                trans->set_address(i);
                trans->set_data_ptr(reinterpret_cast<unsigned char*>(&data));
                trans->set_data_length(4);
                trans->set_streaming_width(4);
                trans->set_byte_enable_ptr(0);
                trans->set_dmi_allowed(false);
                trans->set_response_status(tlm::TLM_INCOMPLETE_RESPONSE);
                // ...
                socket->b_transport(*trans, delay);

                if (trans->is_response_error()) {
                    // SC_REPORT_ERROR("TLM 2.0", "Response error from b_transport");
                    char txt[100];
                    sprintf(txt, "Error from b_transport, response status = %s", trans->get_response_string().c_str());
                    SC_REPORT_ERROR("TLM 2.0", txt);
                }

                if (trans->is_dmi_allowed()) {
                    // ...
                    dmi_data.init();
                    dmi_ptr_valid = socket->get_direct_mem_ptr(*trans, dmi_data);
                    //...
                }
                cout << "trans = { " << (cmd ? 'W' : 'R') << ", " << hex << i
                    << " } , data = " << hex << data << " at time " << sc_time_stamp()
                    << " delay = " << delay << endl;
            }

        }
        trans->set_address(0);
        trans->set_read();
        trans->set_data_length(128);

        unsigned char *   data = new unsigned char[128];
        trans->set_data_ptr(data);

        unsigned int n_bytes = socket->transport_dbg(*trans);

        for (unsigned int i = 0; i < n_bytes; i += 4) {
            cout << "mem[" << i << "] = "
            << *(reinterpret_cast<unsigned int*>( &data[i] )) << endl;
        }

        // wait(delay);
    }

    virtual void invalidate_direct_mem_ptr(sc_dt::uint64 start_range, sc_dt::uint64 end_range) {
        dmi_ptr_valid = false;
    }

private:
    int           data;
    bool          dmi_ptr_valid;
    tlm::tlm_dmi  dmi_data;
};

class Memory : public sc_module {
public:
    SC_HAS_PROCESS(Memory);
    tlm_utils::simple_target_socket<Memory>       socket;

    enum {SIZE = 256};
    const sc_time LATENCY = sc_time(5, SC_NS);

    Memory(const sc_module_name& name) : socket("socket") {
        socket.register_b_transport(this,         &Memory::b_transport);
        socket.register_get_direct_mem_ptr(this,  &Memory::get_direct_mem_ptr);
        socket.register_transport_dbg(this,       &Memory::transport_dbg);

        for (int i = 0; i < SIZE; i++) {
            mem[i] = 0xAA000000 | (rand() % SIZE);
        }

        SC_THREAD(invalidation_process);
    }

    virtual unsigned int transport_dbg(tlm::tlm_generic_payload& trans) {
        tlm::tlm_command  cmd = trans.get_command();
        sc_dt::uint64     adr = trans.get_address() / 4;
        unsigned char *   ptr = trans.get_data_ptr();
        unsigned int      len = trans.get_data_length();

        unsigned int num_bytes = (len < SIZE - adr) ? len : SIZE - adr;

        if (cmd == tlm::TLM_READ_COMMAND) {
            memcpy(ptr, &mem[adr], num_bytes);
        } else if (cmd == tlm::TLM_WRITE_COMMAND) {
            memcpy(&mem[adr], ptr, num_bytes);
        }

        return num_bytes;
    }

    virtual bool get_direct_mem_ptr(tlm::tlm_generic_payload& trans, tlm::tlm_dmi& dmi_data){
        dmi_data.allow_read_write();
        // ...
        dmi_data.set_dmi_ptr(reinterpret_cast<unsigned char*>( &mem[0] ));
        dmi_data.set_start_address(0);
        dmi_data.set_end_address(SIZE * 4 -1);
        dmi_data.set_read_latency(LATENCY);
        dmi_data.set_write_latency(LATENCY);

        return true;
    }

    virtual void b_transport(tlm::tlm_generic_payload& trans, sc_time& delay){
        tlm::tlm_command  cmd = trans.get_command();
        sc_dt::uint64     adr = trans.get_address() / 4;
        unsigned char *   ptr = trans.get_data_ptr();
        unsigned int      len = trans.get_data_length();
        unsigned char *   byt = trans.get_byte_enable_ptr();
        unsigned int      wid = trans.get_streaming_width();

        if (adr >= sc_dt::uint64(SIZE)) {
            trans.set_response_status(tlm::TLM_ADDRESS_ERROR_RESPONSE);
            return;
        }

        if (byt != 0) {
            trans.set_response_status(tlm::TLM_BYTE_ENABLE_ERROR_RESPONSE);
            return;
        }

        if (len > 4 || wid < len) {
            trans.set_response_status(tlm::TLM_BURST_ERROR_RESPONSE);
            return;
        }

        // if (adr >= sc_dt::uint64(SIZE) || byt != 0 || len > 4 || wid < len) {
        //   SC_REPORT_ERROR("TLM 2.0", "Target does not support given generic payload transaction");
        // }

        if (cmd == tlm::TLM_READ_COMMAND) {
            memcpy(ptr, &mem[adr], len);
        } else if (cmd == tlm::TLM_WRITE_COMMAND) {
            memcpy(&mem[adr], ptr, len);
        }
        wait(delay);
        delay = SC_ZERO_TIME;

        trans.set_dmi_allowed(true);
        trans.set_response_status(tlm::TLM_OK_RESPONSE);
    };

    void invalidation_process() {
        for (int i = 0; i < 4; i ++) {
            wait(LATENCY * 8);
            socket->invalidate_direct_mem_ptr(0, SIZE - 1);
        }
    }

private:
    int mem[SIZE];
};

class Top : public sc_module {
public:
    SC_HAS_PROCESS(Top);
    Initiator *initiator;
    Memory    *memory;

    Top(const sc_module_name& name){
        initiator = new Initiator("initiator");
        memory    = new Memory("memory");

        initiator->socket.bind( memory->socket );
    }
};

int sc_main(int argc, char **argv){
    Top top("top");
    sc_start();
    return 0;
}
