from myhdl import *


@block
def dut(a, b, c, d, e, f):
    @instance
    def assignment():
        while True:
            yield a, b
            yield delay(305)
            c.next = a & b
            d.next = a | b
            e.next = a ^ b
            f.next = concat(a, b)
    return instances()

@block
def logic_gate():
    a = Signal(modbv(0)[1:])
    b = Signal(modbv(0)[1:])
    c = Signal(modbv(0)[1:])
    d = Signal(modbv(0)[1:])
    e = Signal(modbv(0)[1:])
    f = Signal(modbv(0)[2:])
    d = dut(a, b, c, d, e, f)

    cnt = Signal(modbv(0)[4:])

    @instance
    def drive():
        while True:
            b.next = cnt // 2
            a.next = cnt % 2
            cnt.next = cnt + 1
            yield delay(100000)


    return instances()


tb = logic_gate()
tb.config_sim(True, timescale="1ps")
tb.run_sim(1500000)
tb.config_sim(False)
