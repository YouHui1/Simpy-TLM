from simpy import Environment
from utils import *
import random

random.seed(0)

class ICache(Module):
    def __init__(self, env: Environment, name: str, num:int=10):
        self.num = num
        super().__init__(env, name)
        self.sock = Socket(self)

        self.env.process(self.thread())

    def thread(self):
        for i in range(self.num):
            inst = random.randint(0, 2**23)
            payload = Generic_Payload()
            payload.set_data_ptr(inst)
            payload.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.sock)
            yield self.env.timeout(10)
            print("\033[1;31m"+ f"{self.name:<8} time: {self.env.now:<5}create instruction: {hex(inst)}" +"\033[0m")
            yield self.env.process(self.sock.b_transport(payload, 0))

class Decoder(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.ic_sock = Socket(self)
        self.alu_sock = Socket(self)
        self.register = None
        self.data = None
        self.register_ready = self.env.event()
        self.finished = self.env.event()

        self.ic_sock.register_b_transport(self.b_transport_pipeline)
        # self.ic_sock.register_b_transport(self.b_transport)

        self.env.process(self.thread())

    def thread(self):
        while True:
            yield self.register_ready
            self.data = {}
            self.data['op'] = self.register >> 20 & 0x7
            self.data['i1'] = self.register >> 10 & 0x3ff
            self.data['i2'] = self.register & 0x3ff

            yield self.env.timeout(25)
            msg = f"{self.name:<8} time: {self.env.now:<5}"
            print("\033[1;33m"+ msg +f"read instruction: {hex(self.register)}\n" +
                  f"{' ' * len(msg)}decode: op: {self.data['op']}, i1: {self.data['i1']}, i2: {self.data['i2']}" +"\033[0m")
            self.finished.succeed()
            self.finished = self.env.event()
            pass

    def b_transport(self, payload: Generic_Payload, delay):
        yield self.env.timeout(delay)
        self.register = payload.get_data_ptr()
        self.register_ready.succeed()
        self.register_ready = self.env.event()
        yield self.finished

        trans = Generic_Payload()
        trans.set_data_ptr(self.data)
        trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.alu_sock)
        yield self.env.process(self.alu_sock.b_transport(trans, 0))

        payload.set_response_status(tlm_response_status.TLM_OK_RESPONSE, self.ic_sock.other_socket)

    def b_transport_pipeline(self, payload: Generic_Payload, delay):
        yield self.env.timeout(delay)
        self.register = payload.get_data_ptr()
        self.register_ready.succeed()
        self.register_ready = self.env.event()
        yield self.finished

        trans = Generic_Payload()
        trans.set_data_ptr(self.data)
        trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.alu_sock)
        payload.set_response_status(tlm_response_status.TLM_OK_RESPONSE, self.ic_sock.other_socket)
        yield self.env.process(self.alu_sock.b_transport(trans, 0))


class ALU(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.sock = Socket(self)
        self.mem = [0] * 1024
        for i in range(1024):
            self.mem[i] = random.randint(0, 2**32 - 1)
        self.register = None
        self.register_ready = self.env.event()
        self.finished = self.env.event()

        self.sock.register_b_transport(self.b_transport)

        self.env.process(self.thread())

    def thread(self):
        while True:
            yield self.register_ready
            i1 = self.register['i1']
            i2 = self.register['i2']
            if self.register['op'] == 0:
                res = self.mem[i1] + self.mem[i2]
            elif self.register['op'] == 1:
                res = (self.mem[i1] - self.mem[i2]) & (2**32 - 1)
            elif self.register['op'] == 2:
                res = int(self.mem[i1] < self.mem[i2])
            elif self.register['op'] == 3:
                res = int(self.mem[i1] == self.mem[i2])
            elif self.register['op'] == 4:
                res = self.mem[i1] & self.mem[i2]
            elif self.register['op'] == 5:
                res = self.mem[i1] | self.mem[i2]
            elif self.register['op'] == 6:
                res = self.mem[i1] ^ self.mem[i2]
            elif self.register['op'] == 7:
                res = int(self.mem[i1] > self.mem[i2])
            else:
                assert False, 'Invalid Operation'
            yield self.env.timeout(35)
            msg = f"{self.name:<8} time: {self.env.now:<5}"
            print("\033[1;32m"+ msg +f"read data: {self.register}\n" +
                  f"{' ' * len(msg)}calculate: dat1: {hex(self.mem[i1])}, dat2: {hex(self.mem[i2])}, op: {self.register['op']} result: {hex(res)}" +"\033[0m")

            self.finished.succeed()
            self.finished = self.env.event()

    def b_transport(self, payload: Generic_Payload, delay):
        yield self.env.timeout(delay)
        self.register = payload.get_data_ptr()
        self.register_ready.succeed()
        self.register_ready = self.env.event()
        yield self.finished

        payload.set_response_status(tlm_response_status.TLM_OK_RESPONSE, self.sock.other_socket)


class Top(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.icache = ICache(env, 'icache', 10)
        self.decoder = Decoder(env, 'decoder')
        self.alu = ALU(env, 'alu')
        self.icache.sock.bind(self.decoder.ic_sock)
        self.decoder.alu_sock.bind(self.alu.sock)

if __name__ == '__main__':
    env = simpy.Environment()
    top = Top(env, 'top')
    env.run()
