import re

def extract_cells(sdf_content):
    cells = []
    stack = []
    cell_start = None
    for i, char in enumerate(sdf_content):
        if char == '(':
            if sdf_content[i+1:i+5] == 'CELL':
                if cell_start is None:
                    cell_start = i  # Mark the start of a CELL block
                stack.append(i)
            elif len(stack) > 0:
                stack.append(i)
        elif char == ')' and stack:
            start = stack.pop()
            if not stack and cell_start is not None:
                # When the stack is empty, we found a complete CELL block
                cell_end = i
                cells.append(sdf_content[cell_start:cell_end+1])
                cell_start = None  # Reset for the next CELL block
    return cells

def parse_sdf_to_dict(sdf_content):
    cell_pattern = re.compile(r'\(CELL(.*?)\)\s*\)', re.DOTALL)
    cell_blocks = extract_cells(sdf_content)

    cells = []

    for block in cell_blocks:
        cell_info = {}
        cell_info['CELLTYPE'] = re.search(r'\(CELLTYPE\s+"(.*?)"\)', block).group(1)

        instance_match = re.search(r'\(INSTANCE\s+(.*?)\)', block)
        if instance_match:
            cell_info['INSTANCE'] = instance_match.group(1)
        else:
            cell_info['INSTANCE'] = None

        # Parsing DELAY section
        delay_info = {}
        interconnects = re.findall(r'\(INTERCONNECT\s+(.*?)\s+\((.*?)\)', block)
        if interconnects:
            delay_info['INTERCONNECT'] = [{'from_to': ic[0], 'delays': ic[1]} for ic in interconnects]

        iopaths = re.findall(r'\(IOPATH\s+(.*?)\s+(.*?)\s+\((.*?)\)\s+\((.*?)\)', block)
        if iopaths:
            delay_info['IOPATH'] = [{'input_output': [ip[0], ip[1]], 'rise_delays': [float(num) for num in ip[2].split(':')], 'fall_delays': [float(num) for num in ip[3].split(':')]} for ip in iopaths]

        cell_info['DELAY'] = delay_info

        cells.append(cell_info)

    return cells
