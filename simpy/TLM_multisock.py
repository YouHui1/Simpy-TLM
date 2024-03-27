from simpy import Environment
from multi_socket_example.initiator import *
from multi_socket_example.bus import *
from multi_socket_example.target import *

class Top(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.bus = Bus(self.env, 'bus')
        self.init = []
        self.target = []
        for i in range(4):
            init = Initiator(self.env, 'init_{}'.format(i))
            init.socket.bind(self.bus.targ_socket)
            self.init.append(init)

            targ = Target(self.env, 'target_{}'.format(i))
            self.bus.init_socket.bind(targ.socket)
            self.target.append(targ)

            dprint(init, init.name)
            dprint(targ, targ.name)


if __name__ == '__main__':
    env = simpy.Environment()
    top = Top(env, 'top')
    env.run()

    print("\n***** Messages have been written to file output.txt                    *****")
