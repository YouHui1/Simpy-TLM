from utils import *

class Concurrency(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.env.process(self.thread1())
        self.env.process(self.thread2())

    def thread1(self):
        while True:
            print("{} : thread1".format(self.env.now))
            yield self.env.timeout(2)
    def thread2(self):
        while True:
            print("\t{} : thread1".format(self.env.now))
            yield self.env.timeout(3)

if __name__ == '__main__':
    env = simpy.Environment()
    concurrency = Concurrency(env, "concurrency")
    env.run(until=10)
