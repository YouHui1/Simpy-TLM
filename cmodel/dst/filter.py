from cppyy import gbl as cpp
import cppyy
import sys
import os
import re

cppyy.add_include_path('/home/shiying/systemc/systemc/include')
cppyy.add_library_path('/home/shiying/systemc/systemc/lib')
cppyy.load_library('systemc')
# print(os.getcwd())
os.chdir('../src/2D-Median-Filter')
cppyy.add_include_path('EasyBMP')
code_lst = ['EasyBMP_DataStructures.h', 'EasyBMP_BMP.h', 'EasyBMP_VariousBMPutilities.h', 'EasyBMP.h', 'EasyBMP.cpp']
for name in code_lst:
    with open(os.path.join('EasyBMP', name), 'r') as file:
        s = file.read()
        cppyy.cppdef(s)

cppyy.add_include_path('include')
code_lst = os.listdir(os.path.join(os.getcwd(), 'include'))
for name in code_lst:
    with open(os.path.join('include', name), 'r') as file:
        s = file.read()
        cppyy.cppdef(s)
cpp_format = r'^(?!main).*\.cpp$'
filtered_list = []
code_lst = [s for s in os.listdir(os.path.join(os.getcwd(), 'src')) if re.match(cpp_format, s)]
for name in code_lst:
    with open(os.path.join('src', name), 'r') as file:
        s = file.read()
        cppyy.cppdef(s)


median_filter = cpp.median_filter_module('median_filter')
memory = cpp.memory_module("memory")
testbench = cpp.median_filter_tb("median_filter_testbench")

median_filter.initiator_socket.bind(memory.target_socket)

testbench.initiator_socket.bind(memory.target_socket_tb)

# The system clock
Clk = cpp.sc_core.sc_clock("Clock", 10, cpp.SC_NS, 0.5, 10, cpp.SC_NS)

cppyy.cppdef('''
// The system reset signal
sc_signal<bool> Rst;

// Start and Finish signals
sc_signal<bool> Start;
sc_signal<bool> Finish;
''')
# # // The system reset signal
# Rst = cpp.sc_core.sc_signal[bool]

# # // Start and Finish signals
# Start = cpp.sc_core.sc_signal[bool]
# Finish = cpp.sc_core.sc_signal[bool]

median_filter.clk(Clk)
median_filter.rst(cpp.Rst)
median_filter.start(cpp.Start)
median_filter.finish(cpp.Finish)

memory.clk(Clk)
memory.rst(cpp.Rst)

testbench.clk(Clk)
testbench.rst(cpp.Rst)
testbench.start(cpp.Start)
testbench.finish(cpp.Finish)

cpp.sc_core.sc_start()
