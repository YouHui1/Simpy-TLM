###################################################################

# Created by write_sdc on Thu Apr  4 20:17:18 2024

###################################################################
set sdc_version 2.0

set_units -time ns -resistance kOhm -capacitance pF -voltage V -current uA
set_max_delay 4  -through [list [get_ports {f[1]}] [get_ports {f[0]}] [get_ports a] [get_ports \
b] [get_ports c] [get_ports d] [get_ports e]]
