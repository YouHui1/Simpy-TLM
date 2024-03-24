from simpy import Environment
from utils import *
import random

class Initiator(Module):
    """initiator

    """
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.dmi_ptr_valid = False
        self.socket = Socket(self)
        self.dmi_data = TLM_DMI()

        self.socket.register_invalidate_direct_mem_ptr(self.invalidate_direct_mem_ptr)

        self.env.process(self.thread_process())

    def thread_process(self):
        trans = Generic_Payload()
        delay = [10]
        for i in range(256-64, 256+64, 4):
            cmd = random.randint(0, 1)
            data = [0]
            if cmd == tlm_command.TLM_WRITE_COMMAND:
                data = [0xff000000 | i]

            if self.dmi_ptr_valid and i >= self.dmi_data.get_start_address() \
                and i <= self.dmi_data.get_end_address():

                if cmd == tlm_command.TLM_READ_COMMAND:
                    assert self.dmi_data.is_read_allowed(), "dmi isn't allowed to read"
                    data[0] = self.dmi_data.get_dmi_ptr()[0 + i - self.dmi_data.get_start_address()]
                    yield self.env.timeout(self.dmi_data.get_read_latency())
                elif cmd == tlm_command.TLM_WRITE_COMMAND:
                    assert self.dmi_data.is_write_allowed(), "dmi isn't allowed to write"
                    self.dmi_data.get_dmi_ptr()[0 + i - self.dmi_data.get_start_address()] = data[0]
                    yield self.env.timeout(self.dmi_data.get_write_latency())

                print("DMI = ( {}, {} ), data = {} at time {}"
                      .format('W' if cmd == 1 else 'R',
                              hex(i),
                              hex(data[0]),
                              self.env.now))
            else:
                trans.set_command(cmd)
                trans.set_address(i)
                trans.set_data_ptr(data)
                trans.set_data_length(4)
                trans.set_dmi_allowed(False)
                trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.socket)

                yield self.env.process(self.socket.b_transport(trans, delay))

                if trans.is_response_error():
                    raise ResponseError("Response error from b_transport")
                if trans.is_dmi_allowed():
                    trans.set_address(i)
                    self.dmi_ptr_valid = self.socket.get_direct_mem_ptr(trans, self.dmi_data)

                print("trans = ( {}, {} ), data = {} at time {} delay = {}"
                      .format('W' if cmd == 1 else 'R',
                              hex(i),
                              hex(data[0]),
                              self.env.now,
                              delay[0]))

        A = 128
        trans.set_address(A)
        trans.set_command(tlm_command.TLM_READ_COMMAND)
        trans.set_data_length(256)

        data = [0] * (256)
        trans.set_data_ptr(data)

        n_bytes = self.socket.transport_dbg(trans)

        for i in range(0, n_bytes, 4):
            print("mem[{}] = {}".format(hex(A + i), hex(data[i // 4])))

        A = 256
        trans.set_address(A)
        trans.set_data_length(128)

        n_bytes = self.socket.transport_dbg(trans)

        for i in range(0, n_bytes, 4):
            print("mem[{}] = {}".format(hex(A + i), hex(data[i // 4])))

        A = 512
        trans.set_address(A)
        trans.set_data_length(128)

        n_bytes = self.socket.transport_dbg(trans)

        for i in range(0, n_bytes, 4):
            print("mem[{}] = {}".format(hex(A + i), hex(data[i // 4])))

        A = 512 + 256
        trans.set_address(A)
        trans.set_data_length(128)

        n_bytes = self.socket.transport_dbg(trans)

        for i in range(0, n_bytes, 4):
            print("mem[{}] = {}".format(hex(A + i), hex(data[i // 4])))

    def invalidate_direct_mem_ptr(self, start_range, end_range):
        self.dmi_ptr_valid = False


        pass
