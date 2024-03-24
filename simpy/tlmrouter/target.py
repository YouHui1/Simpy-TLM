from utils import *
import random

mem_nr = 0

class Memory(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.mem = [0] * 256
        self.LATENCY = 10
        global mem_nr
        for i in range(256):
            # self.mem[i] = 0xaa000000 | (mem_nr << 20) | random.randint(0, 256)
            self.mem[i] = 0xaa000000 | (mem_nr << 20) | i

        mem_nr += 1

        self.socket = Socket(self)
        self.socket.register_b_transport(self.b_transport)
        self.socket.register_get_direct_mem_ptr(self.get_direct_mem_ptr)
        self.socket.register_transport_dbg(self.transport_dbg)

        # self.env.process(self.invalidation_process())

    def transport_dbg(self, trans: Generic_Payload):
        cmd = trans.get_command()
        adr = trans.get_address() // 4
        ptr = trans.get_data_ptr()
        len = trans.get_data_length()

        num_bytes = len if len < (256 - adr) * 4 else (256 - adr) * 4
        if cmd == tlm_command.TLM_READ_COMMAND:
            for i in range(num_bytes // 4):
                ptr[i] = self.mem[adr + i]
        elif cmd == tlm_command.TLM_WRITE_COMMAND:
            for i in range(num_bytes // 4):
                self.mem[adr + i] = ptr[i]

        return num_bytes

    def get_direct_mem_ptr(self, trans: Generic_Payload, dmi_data: TLM_DMI):
        dmi_data.allow_read_write()
        dmi_data.set_dmi_ptr(self.mem)
        dmi_data.set_start_address(0)
        dmi_data.set_end_address(256 * 4 - 1)
        dmi_data.set_read_latency(self.LATENCY)
        dmi_data.set_write_latency(self.LATENCY)

        return True

    def b_transport(self, trans: Generic_Payload, delay):
        cmd = trans.get_command()
        adr = trans.get_address() // 4
        ptr = trans.get_data_ptr()
        if adr >= 256:
            trans.set_response_status(tlm_response_status.TLM_ADDRESS_ERROR_RESPONSE);
            # raise ValueError("Target does not support given generic payload transaction")
            return

        if cmd == tlm_command.TLM_READ_COMMAND:
            ptr[0] = self.mem[adr]
        elif cmd == tlm_command.TLM_WRITE_COMMAND:
            self.mem[adr] = ptr[0]

        yield self.env.timeout(delay[0])
        delay[0] = 0

        trans.set_dmi_allowed(True)
        trans.set_response_status(tlm_response_status.TLM_OK_RESPONSE, self.socket.other_socket)

    def invalidation_process(self):
        for i in range(4):
            yield self.env.timeout(self.LATENCY * 8)
            self.socket.invalidate_direct_mem_ptr(0, 255)
