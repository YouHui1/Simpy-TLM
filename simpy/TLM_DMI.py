from utils import *
import random

class ResponseError(Exception):
    pass

class TLM_DMI:
    DMI_ACCESS_NONE = 0x0
    DMI_ACCESS_READ = 0x1
    DMI_ACCESS_WRITE = 0x2
    DMI_ACCESS_READ_WRITE = DMI_ACCESS_READ | DMI_ACCESS_WRITE

    def __init__(self) -> None:
        pass
    def init(self):
        self.m_dmi_ptr = 0x0
        self.m_dmi_start_address = 0x0
        self.m_dmi_end_address = 0xffffffffffffffff
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_NONE
        self.m_dmi_read_latency = 0
        self.m_dmi_write_latency = 0
    def get_start_address(self):
        return self.m_start_address
    def get_end_address(self):
        return self.m_dmi_end_address
    def get_read_latency(self):
        return self.m_dmi_read_latency
    def get_write_latency(self):
        return self.m_dmi_write_latency
    def get_dmi_ptr(self):
        return self.m_dmi_ptr
    def get_granted_access(self):
        return self.m_dmi_access
    def is_none_allowed(self):
        return self.m_dmi_access == TLM_DMI.DMI_ACCESS_NONE
    def is_read_allowed(self):
        return (self.m_dmi_access & TLM_DMI.DMI_ACCESS_READ) == TLM_DMI.DMI_ACCESS_READ
    def is_write_allowed(self):
        return (self.m_dmi_access & TLM_DMI.DMI_ACCESS_WRITE) == TLM_DMI.DMI_ACCESS_WRITE
    def is_read_write_allowed(self):
        return (self.m_dmi_access & TLM_DMI.DMI_ACCESS_READ_WRITE) == TLM_DMI.DMI_ACCESS_READ_WRITE

    def set_dmi_ptr(self, p):
        self.m_dmi_ptr = p
    def set_start_address(self, addr):
        self.m_dmi_start_address = addr
    def set_end_address(self, addr):
        self.m_dmi_end_address = addr
    def set_read_latency(self, t):
        self.m_dmi_read_latency = t
    def set_write_latency(self, t):
        self.m_dmi_write_latency = t
    def set_granted_access(self, a):
        self.m_dmi_access = a
    def allow_none(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_NONE
    def allow_read(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_READ
    def allow_write(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_WRITE
    def allow_read_write(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_READ_WRITE

class Initiator(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.socket = Socket(self.env)
        self.data = [None]
        self.dmi_ptr_valid = False
        self.dmi_data = TLM_DMI()
        self.socket.register_invalidate_direct_mem_ptr(self.invalidate_direct_mem_ptr)

        self.env.process(self.thread_process())

    def thread_process(self):
        trans = Genetic_Payload()
        delay = [10]

        for i in range(0, 128, 4):
            cmd = random.randint(0, 1)
            if cmd == tlm_command.TLM_WRITE_COMMAND:
                self.data = [0xff000000 | i]

            if self.dmi_ptr_valid:
                if cmd == tlm_command.TLM_READ_COMMAND:
                    assert self.dmi_data.is_read_allowed(), "It isn't allowed to read dmi_data"
                    self.data[0] = self.dmi_data.get_dmi_ptr()[0]
                    yield self.env.timeout(self.dmi_data.get_read_latency())
                elif cmd == tlm_command.TLM_WRITE_COMMAND:
                    assert self.dmi_data.is_write_allowed(), "It isn't allowed to write dmi_data"
                    self.dmi_data.get_dmi_ptr()[0] = self.data[0]
                    yield self.env.timeout(self.dmi_data.get_write_latency())

                print("trans = ( {}, {} ), data = {} at time {}"
                      .format('W' if cmd == 1 else 'R',
                              hex(i),
                              hex(self.data[0]),
                              self.env.now))
            else:
                trans.set_command(cmd)
                trans.set_address(i)
                trans.set_data_ptr(self.data)
                trans.set_data_length(4)
                trans.set_dmi_allowed(False)
                trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.socket)

                yield self.env.process(self.socket.b_transport(trans, delay))

                if trans.is_response_error():
                    raise ResponseError("Response error from b_transport")
                if trans.is_dmi_allowed():
                    self.dmi_data.init()
                    self.dmi_ptr_valid = self.socket.get_direct_mem_ptr(trans, self.dmi_data)
                print("trans = ( {}, {} ), data = {} at time {} delay = {}"
                    .format('W' if cmd == 1 else 'R',
                            hex(i),
                            hex(self.data[0]),
                            self.env.now,
                            delay[0]))

            # yield self.env.timeout(delay)

        trans.set_address(0)
        trans.set_command(tlm_command.TLM_READ_COMMAND)
        trans.set_data_length(128)
        data = [0] * (128)
        trans.set_data_ptr(data)

        n_bytes = self.socket.transport_dbg(trans)

        for i in range(0, n_bytes, 4):
            print("mem[{}] = {}".format(hex(i), hex(data[i])))

    def invalidate_direct_mem_ptr(self, start_range, end_range):
        self.dmi_ptr_valid = False

class Memory(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.mem = [0] * 256
        self.LATENCY = 5
        for i in range(256):
            self.mem[i] = 0xaa000000 | random.randint(0, 256)
        self.socket = Socket(self.env)
        self.socket.register_b_transport(self.b_transport)
        self.socket.register_get_direct_mem_ptr(self.get_direct_mem_ptr)
        self.socket.register_transport_dbg(self.transport_dbg)

        self.env.process(self.invalidation_process())

    def transport_dbg(self, trans: Genetic_Payload):
        cmd = trans.get_command()
        adr = trans.get_address() // 4
        ptr = trans.get_data_ptr()
        len = trans.get_data_length()

        num_bytes = len if len < 256 - adr else 256 - adr

        if cmd == tlm_command.TLM_READ_COMMAND:
            for i in range(num_bytes):
                ptr[i] = self.mem[adr + i]
        elif cmd == tlm_command.TLM_WRITE_COMMAND:
            for i in range(num_bytes):
                self.mem[adr + i] = ptr[i]

        return num_bytes

    def get_direct_mem_ptr(self, trans: Genetic_Payload, dmi_data: TLM_DMI):
        dmi_data.allow_read_write()
        dmi_data.set_dmi_ptr(self.mem)
        dmi_data.set_start_address(0)
        dmi_data.set_end_address(256 * 4 - 1)
        dmi_data.set_read_latency(self.LATENCY)
        dmi_data.set_write_latency(self.LATENCY)

        return True

    def b_transport(self, trans: Genetic_Payload, delay):
        cmd = trans.get_command()
        adr = trans.get_address()
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

class Top(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.initiator = Initiator(self.env, "initiator")
        self.memory = Memory(self.env, "memory")
        self.initiator.socket.bind(self.memory.socket)

if __name__ == '__main__':
    env = simpy.Environment()
    top = Top(env, 'top')
    env.run()
