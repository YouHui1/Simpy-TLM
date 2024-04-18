import json

def filter(json_file, top_module):
    json_file['modules'] = {k: v for k, v in json_file['modules'].items() if k == top_module}
    return

def modify(json_file, top_module):
    modules = json_file['modules']
    cells = modules[top_module]['cells']
    for idx, (k, v) in enumerate(cells.items()):
        # print(v['port_directions'])
        v['port_directions']['Y'] = v['port_directions'].pop('Z')
        v['connections']['Y'] = v['connections'].pop('Z')
    return

TYPE = {'INVHDMX': '$_NOT_', 'AND2HDMX': '$_AND_', 'NOR2HDUX': '$_NOR_'}

def change_type(json_file, top_module):
    modules = json_file['modules']
    cells = modules[top_module]['cells']
    for idx, (k, v) in enumerate(cells.items()):
        v['type'] = TYPE[v['type']]
    return

with open('logic_gate_yosys.json', 'r') as file:
    src = json.load(file)
    # print(src['modules']['logic_gate'].keys())
    filter(src, 'logic_gate')
    modify(src, 'logic_gate')
    change_type(src, 'logic_gate')
    # for i in src['modules'].keys():
    #     print(i == 'logic_gate')

with open('logic_gate_yosys.json', 'w') as file:
    dst = json.dumps(src, indent=2)
    file.write(dst)
