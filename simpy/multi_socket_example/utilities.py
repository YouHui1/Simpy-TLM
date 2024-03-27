from utils import *
import random

seed = random.randint(0, 100000)
print(seed)
random.seed(69915)

fout = open("output.txt", "w")

def rand_ps() -> int:
    n = random.randint(0, 99)
    n = n**3
    return n // 100
