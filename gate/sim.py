from digsim.circuit import Circuit
from digsim.circuit.components import YosysComponent
import digsim
import os
import random
from sdf import *

def set_cell_delay(circuit: Circuit,
                   component_name: str,
                   delay_ns: float):
    assert delay_ns >= 0, "Invalid number"
    match_name = component_name + '_'
    # component_class = getattr(digsim.circuit.components._yosys_atoms, component_name)
    for name, component in circuit._components.items():
        # if isinstance(component, component_class):
        if (name.find(match_name) == 0):
            component.ports[-1]._delay_ns = delay_ns
            print(f"{component_name} set delay: {delay_ns} ns")
            break


if __name__ == '__main__':
    with open('output/logic_gate/logic_gate.sdf', 'r') as file:
        sdf_content = file.read()

    parsed_cells = parse_sdf_to_dict(sdf_content)

    circuit = Circuit()
    yosys_logic = YosysComponent(circuit, path='logic_gate_yosys.json')

    circuit.vcd('logic_delay.vcd')

    for cell in parsed_cells:
        if cell['INSTANCE'] is None:
            continue
        iopath = cell['DELAY']['IOPATH'][0]
        rise_delays = iopath['rise_delays']
        fall_delays = iopath['fall_delays']
        mx_delay = max(rise_delays[-1], fall_delays[-1])
        name = cell['INSTANCE']
        set_cell_delay(circuit, name, mx_delay)

    yosys_logic.a.value = 0
    yosys_logic.b.value = 0
    for i in range(16):
        io1 = i % 2
        io2 = i // 2

        yosys_logic.a.value = io1
        yosys_logic.b.value = io2
        circuit.run(ns=100)

    circuit.vcd_close()
