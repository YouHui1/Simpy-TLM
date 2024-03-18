from utils import *

class Process(Module):
    def __init__(self, env: simpy.Environment(), name):
        super().__init__(env, name)
        self.method_env = simpy.Timeout(env, 0)
        self.method_env.callbacks.append(self.method)
        self.env.process(self.thread())
        self.env.process(self.cthread())

    def method(self, event):
        print("method triggered @ {}".format(self.env.now))
        event = simpy.Timeout(env, 1)
        event.callbacks.append(self.method)


    def thread(self):
        while True:
            print("thread triggered @ {}".format(self.env.now))
            yield self.env.timeout(1)

    def cthread(self):
        while True:
            print("cthread triggered @ {}".format(self.env.now))
            yield self.env.timeout(1)

if __name__ == '__main__':
    env = simpy.Environment()
    process = Process(env, "Process")
    print("execution phase begins @ {}".format(env.now))
    env.run(2)
    print("execution phase ends @ {}".format(env.now))
