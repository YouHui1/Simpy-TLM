from utils import *

class Concurrency(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.env.process(self.trigger())
        self.env.process(self.catcher())

    def trigger(self):
        while True:
            print("{} : thread1".format(self.env.now))
            yield self.env.timeout(2)
    def catcher(self):
        while True:
            print("\t{} : thread1".format(self.env.now))
            yield self.env.timeout(3)

if __name__ == '__main__':
    env = simpy.Environment()
    concurrency = Concurrency(env, "concurrency")
    env.run(until=10)
