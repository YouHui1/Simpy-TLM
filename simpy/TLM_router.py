from simpy import Environment
from tlmrouter.initiator import *
from tlmrouter.target import *
from tlmrouter.router import *
from utils import *

class Top(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.initiator = Initiator(self.env, "init")
        self.memory = [None] * 4
        self.router = Router(self.env, "router", 4)
        for i in range(4):
            s = f"mem_{i}"
            self.memory[i] = Memory(self.env, s)
        self.initiator.socket.bind(self.router.target_socket)
        for i in range(4):
            self.router.initiator_socket[i].bind(self.memory[i].socket)


if __name__ == "__main__":
    env = simpy.Environment()
    top = Top(env, "top")
    env.run()
