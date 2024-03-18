from utils import *
import random

class ResponseError(Exception):
    pass


class Initiator(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.socket = Socket(self.env)
        self.data = [None]

        self.env.process(self.thread_process())

    def thread_process(self):
        trans = Genetic_Payload()
        delay = 10

        for i in range(32, 96, 4):
            cmd = random.randint(0, 1)
            if cmd == tlm_command.TLM_WRITE_COMMAND:
                self.data = [0xff000000 | i]

            trans.set_command(cmd)
            trans.set_address(i)
            trans.set_data_ptr(self.data)
            trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.socket)

            yield self.env.process(self.socket.b_transport(trans, delay))
            if trans.is_response_error():
                raise ResponseError("Response error from b_transport")

            print("trans = ( {}, {} ), data = {} at time {} delay = {}"
                  .format('W' if cmd == 1 else 'R',
                          hex(i),
                          hex(self.data[0]),
                          self.env.now,
                          delay))

            yield self.env.timeout(delay)

class Memory(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.mem = [0] * 256
        for i in range(256):
            self.mem[i] = 0xaa000000 | random.randint(0, 256)
        self.socket = Socket(self.env)
        self.socket.register_b_transport(self.b_transport)

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

        trans.set_response_status(tlm_response_status.TLM_OK_RESPONSE, self.socket.other_socket)
        yield self.env.timeout(0)

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
