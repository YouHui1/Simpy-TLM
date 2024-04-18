import simpy

# file = open('debug.txt', 'w')
def dprint(*args, **kwargs):
#     global file
#     # 指定输出文件路径，可以根据需要修改

#     # 将sep、end、file和flush参数设置默认值，与print函数保持一致
#     sep = kwargs.pop('sep', ' ')
#     end = kwargs.pop('end', '\n')
#     # file = kwargs.pop('file', None)  # 这里的file参数实际上不会被使用，因为我们会将内容输出到指定的文件
#     flush = kwargs.pop('flush', False)

#     # 将所有位置参数转换为字符串，并使用sep参数连接
#     output_str = sep.join(map(str, args)) + end

#     # 打开指定的文件，并将内容写入文件

#     file.write(output_str)

#     # 如果flush为True，则刷新输出流，确保内容立即写入文件
#     if flush:
#         file.flush()
    pass

def SC_PS(num):
    return num * 1
def SC_NS(num):
    return num * 1e3
def SC_US(num):
    return num * 1e6
def SC_MS(num):
    return num * 1e9
def SC_S(num):
    return num * 1e12

class ResponseError(Exception):
    pass

class tlm_command:
    TLM_READ_COMMAND = 0
    TLM_WRITE_COMMAND = 1
    TLM_IGNORE_COMMAND = 2

class tlm_response_status:
    TLM_OK_RESPONSE = 1
    TLM_INCOMPLETE_RESPONSE = 0
    TLM_GENERIC_ERROR_RESPONSE = -1
    TLM_ADDRESS_ERROR_RESPONSE = -2
    TLM_COMMAND_ERROR_RESPONSE = -3
    TLM_BURST_ERROR_RESPONSE = -4
    TLM_BYTE_ENABLE_ERROR_RESPONSE = -5

class tlm_phase:
    """TLM Phase

    """
    UNINITIALIZED_PHASE = 0
    BEGIN_REQ = 1
    END_REQ = 2
    BEGIN_RESP = 3
    END_RESP = 4
    m_ex_ph = {}

    def __init__(self, id=UNINITIALIZED_PHASE) -> None:
        self.m_id = id

    @staticmethod
    def DECLARE_EXTENDED_PHASE(name: str):
        tlm_phase.m_ex_ph[name] = len(tlm_phase.m_ex_ph.items()) + 5

class tlm_sync_enum:
    TLM_ACCEPTED = 0
    TLM_UPDATED = 1
    TLM_COMPLETED = 2


class fifo:
    def __init__(self, env: simpy.Environment, capacity=16) -> None:
        self.env = env
        self.buf = simpy.Store(self.env, capacity)

        self.read_event = self.env.event()
        self.write_event = self.env.event()

    def write(self, value):
        self.buf.put(value)
        if not self.read_event.triggered:
            self.read_event.succeed()
        # self.read_event = self.env.event()
        # self.nb_write(value)
        return True

    def read(self):
        return self.nb_read()

    def nb_write(self, value):
        if self.is_full():
            self.write_event.succeed()
            return False
        self.buf.put(value)
        self.read_event.succeed()
        # self.read_event = self.env.event()
        return True

    def nb_read(self):
        if self.is_empty():
            # self.read_event = self.env.event()
            return None
        value = self.buf.get().value
        if self.write_event.triggered:
            self.write_event.succeed()
        if self.is_empty():
            self.read_event = self.env.event()
        # self.write_event = self.env.event()
        return value

    def is_empty(self):
        """检查FIFO是否为空。"""
        return len(self.buf.items) == 0

    def is_full(self):
        """检查FIFO是否已满。"""
        return len(self.buf.items) == self.buf.capacity

class TLM_DMI:
    DMI_ACCESS_NONE = 0x0
    DMI_ACCESS_READ = 0x1
    DMI_ACCESS_WRITE = 0x2
    DMI_ACCESS_READ_WRITE = DMI_ACCESS_READ | DMI_ACCESS_WRITE

    def __init__(self) -> None:
        self.m_dmi_ptr = 0x0
        self.m_dmi_start_address = 0x0
        self.m_dmi_end_address = 0xffffffffffffffff
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_NONE
        self.m_dmi_read_latency = 0
        self.m_dmi_write_latency = 0
        pass
    def init(self):
        self.m_dmi_ptr = 0x0
        self.m_dmi_start_address = 0x0
        self.m_dmi_end_address = 0xffffffffffffffff
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_NONE
        self.m_dmi_read_latency = 0
        self.m_dmi_write_latency = 0
    def get_start_address(self):
        return self.m_dmi_start_address
    def get_end_address(self):
        return self.m_dmi_end_address
    def get_read_latency(self):
        return self.m_dmi_read_latency
    def get_write_latency(self):
        return self.m_dmi_write_latency
    def get_dmi_ptr(self):
        return self.m_dmi_ptr
    def get_granted_access(self):
        return self.m_dmi_access
    def is_none_allowed(self):
        return self.m_dmi_access == TLM_DMI.DMI_ACCESS_NONE
    def is_read_allowed(self):
        return (self.m_dmi_access & TLM_DMI.DMI_ACCESS_READ) == TLM_DMI.DMI_ACCESS_READ
    def is_write_allowed(self):
        return (self.m_dmi_access & TLM_DMI.DMI_ACCESS_WRITE) == TLM_DMI.DMI_ACCESS_WRITE
    def is_read_write_allowed(self):
        return (self.m_dmi_access & TLM_DMI.DMI_ACCESS_READ_WRITE) == TLM_DMI.DMI_ACCESS_READ_WRITE

    def set_dmi_ptr(self, p):
        self.m_dmi_ptr = p
    def set_start_address(self, addr):
        self.m_dmi_start_address = addr
    def set_end_address(self, addr):
        self.m_dmi_end_address = addr
    def set_read_latency(self, t):
        self.m_dmi_read_latency = t
    def set_write_latency(self, t):
        self.m_dmi_write_latency = t
    def set_granted_access(self, a):
        self.m_dmi_access = a
    def allow_none(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_NONE
    def allow_read(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_READ
    def allow_write(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_WRITE
    def allow_read_write(self):
        self.m_dmi_access = TLM_DMI.DMI_ACCESS_READ_WRITE

class Generic_Payload:
    def __init__(self) -> None:
        self.m_address = None
        self.m_command = None
        self.m_data = None
        self.m_dmi = False
        self.m_response_status = None
        self.m_length = 0
        self.m_streaming_width = 0
        self.m_byte_enable = 0

    def set_command(self, cmd):
        self.m_command = cmd
    def set_data_length(self, length):
        self.m_length = length
    def set_address(self, addr):
        self.m_address = addr
    def set_data_ptr(self, data_ptr):
        self.m_data = data_ptr
    def set_response_status(self, response, sock):
        self.m_response_status = response
        if self.m_response_status == tlm_response_status.TLM_INCOMPLETE_RESPONSE:
            sock.block_event = simpy.Event(sock.env)
            pass
        elif self.m_response_status == tlm_response_status.TLM_OK_RESPONSE:
            if not sock.block_event.triggered:
                sock.block_event.succeed()
    def set_dmi_allowed(self, dmi_allowed):
        self.m_dmi = dmi_allowed
    def set_streaming_width(self, streaming_width):
        self.m_streaming_width = streaming_width
    def set_byte_enable_ptr(self, byte_enable):
        self.m_byte_enable = byte_enable

    def is_dmi_allowed(self):
        return self.m_dmi
    def is_response_error(self) -> bool:
        return self.m_response_status <= 0

    def get_command(self):
        return self.m_command
    def get_address(self):
        return self.m_address
    def get_data_ptr(self):
        return self.m_data
    def get_data_length(self):
        return self.m_length
    def get_byte_enable_ptr(self):
        return self.m_byte_enable
    def get_streaming_width(self):
        return self.m_streaming_width


class Module:
    def __init__(self, env: simpy.Environment, name: str):
        self.env = env
        self.name = name
        pass
    def before_end_of_elaboration(self):
        pass
    def end_of_elaboration(self):
        pass
    def start_of_simulation(self):
        pass
    def end_of_simulation(self):
        pass

class Socket:
    def __init__(self, module: Module, name: str="socket"):
        self.env = module.env
        self.name = module.name + '_{}'.format(name)
        self.other_socket = None
        self.nb_transport_fw_func = None
        self.nb_transport_bw_func = None
        self.b_transport_func = None
        self.transport_dbg_func = None
        self.get_direct_mem_ptr_func = None
        self.invalidate_direct_mem_ptr_func = None
        self.block_event = self.env.event()

    def bind(self, other):
        if isinstance(other, Socket):
            assert self.other_socket is None and other.other_socket is None, "Bind Error: the socket is bound"
            self.other_socket = other
            other.other_socket = self
        elif isinstance(other, MultiSocket):
            self.other_socket = other
            other.m_sockets.append(self)
            # other.other_socket = self
            pass
        else:
            assert False, "Bind Error: the other is not a socket"
    def register_b_transport(self, func):
        self.b_transport_func = func
    def register_get_direct_mem_ptr(self, func):
        self.get_direct_mem_ptr_func = func
    def register_invalidate_direct_mem_ptr(self, func):
        self.invalidate_direct_mem_ptr_func = func
    def register_transport_dbg(self, func):
        self.transport_dbg_func = func
    def register_nb_transport_bw(self, func):
        self.nb_transport_bw_func = func
    def register_nb_transport_fw(self, func):
        self.nb_transport_fw_func = func

    def b_transport(self, payload, delay):
        assert self.other_socket.b_transport_func is not None, "Socket is None"
        if isinstance(self.other_socket, Socket):
            self.env.process(self.other_socket.b_transport_func(payload, delay))
        elif isinstance(self.other_socket, MultiSocket):
            self.env.process(self.other_socket.b_transport_func(payload, delay, self.other_socket.m_sockets.index(self)))
        else:
            assert False, "b_transport: Invalid Type"
        yield self.block_event
        # self.block_event = simpy.Event(self.env)

    def nb_transport_bw(self, trans, phase, t):
        assert self.other_socket.nb_transport_bw_func is not None, f"{self.other_socket.name} nb_transport_bw_func is None"
        if isinstance(self.other_socket, Socket):
            return self.other_socket.nb_transport_bw_func(trans, phase, t)
        elif isinstance(self.other_socket, MultiSocket):
            return self.other_socket.nb_transport_bw_func(trans, phase, t, self.other_socket.m_sockets.index(self))
        else:
            assert False, "nb_transport_bw: Invalid Type"

    def nb_transport_fw(self, trans, phase, t):
        assert self.other_socket.nb_transport_fw_func is not None, f"{self.other_socket.name} nb_transport_fw_func is None"
        if isinstance(self.other_socket, Socket):
            return self.other_socket.nb_transport_fw_func(trans, phase, t)
        elif isinstance(self.other_socket, MultiSocket):
            return self.other_socket.nb_transport_fw_func(trans, phase, t, self.other_socket.m_sockets.index(self))
        else:
            assert False, "nb_transport_fw: Invalid Type"

    def transport_dbg(self, trans):
        if isinstance(self.other_socket, Socket):
            return self.other_socket.transport_dbg_func(trans)
        elif isinstance(self.other_socket, MultiSocket):
            return self.other_socket.transport_dbg_func(trans, self.other_socket.m_sockets.index(self))
        else:
            assert False, "transport_dbg: Invalid Type"

    def get_direct_mem_ptr(self, trans, dmi_data):
        if isinstance(self.other_socket, Socket):
            return self.other_socket.get_direct_mem_ptr_func(trans, dmi_data)
        elif isinstance(self.other_socket, MultiSocket):
            return self.other_socket.get_direct_mem_ptr_func(trans, dmi_data, self.other_socket.m_sockets.index(self))
        else:
            assert False, "get_direct_mem_ptr: Invalid Type"

    def invalidate_direct_mem_ptr(self, start_range, end_range):
        if isinstance(self.other_socket, Socket):
            self.other_socket.invalidate_direct_mem_ptr_func(start_range, end_range)
        elif isinstance(self.other_socket, MultiSocket):
            self.other_socket.invalidate_direct_mem_ptr_func(start_range, end_range, self.other_socket.m_sockets.index(self))
        else:
            assert False, "invalidate_direct_mem_ptr: Invalid Type"


class Socket_Tagged:
    def __init__(self, module: Module, name: str="socket"):
        self.env = module.env
        self.name = module.name + '_{}'.format(name)
        self.other_socket = None
        self.nb_transport_fw_func = None
        self.nb_transport_bw_func = None
        self.b_transport_func = None
        self.transport_dbg_func = None
        self.get_direct_mem_ptr_func = None
        self.invalidate_direct_mem_ptr_func = None
        self.m_transport_user_id = None
        self.block_event = self.env.event()

    def bind(self, other):
        assert self.other_socket is None and other.other_socket is None, "Bind Error"
        self.other_socket = other
        other.other_socket = self
    def register_b_transport(self, func, id):
        self.b_transport_func = func
        self.m_transport_user_id = id

    def register_get_direct_mem_ptr(self, func):
        self.get_direct_mem_ptr_func = func

    def register_invalidate_direct_mem_ptr(self, func, id):
        self.invalidate_direct_mem_ptr_func = func
        self.m_transport_user_id = id

    def register_transport_dbg(self, func):
        self.transport_dbg_func = func

    def register_nb_transport_bw(self, func, id):
        self.nb_transport_bw_func = func
        self.m_transport_user_id = id

    def register_nb_transport_fw(self, func, id):
        self.nb_transport_fw_func = func
        self.m_transport_user_id = id

    def b_transport(self, payload, delay):
        assert self.other_socket.b_transport_func is not None, "Socket is None"
        self.env.process(self.other_socket.b_transport_func(payload, delay))
        yield self.block_event
        # self.block_event = simpy.Event(self.env)

    def nb_transport_bw(self, trans, phase, t):
        assert self.other_socket.nb_transport_bw_func is not None, f"{self.other_socket.name} nb_transport_bw_func is None"
        if isinstance(self.other_socket, Socket):
            return self.other_socket.nb_transport_bw_func(trans, phase, t)
        elif isinstance(self.other_socket, MultiSocket):
            return self.other_socket.nb_transport_bw_func(trans, phase, t, self.other_socket.m_sockets.index(self))
        else:
            assert False, "nb_transport_bw: Invalid Type"

    def nb_transport_fw(self, trans, phase, t):
        assert self.other_socket.nb_transport_fw_func is not None, f"{self.other_socket.name} nb_transport_fw_func is None"
        if isinstance(self.other_socket, Socket):
            return self.other_socket.nb_transport_fw_func(trans, phase, t)
        elif isinstance(self.other_socket, MultiSocket):
            return self.other_socket.nb_transport_fw_func(trans, phase, t, self.other_socket.m_sockets.index(self))
        else:
            assert False, "nb_transport_fw: Invalid Type"

    def transport_dbg(self, trans):
        return self.other_socket.transport_dbg_func(trans)

    def get_direct_mem_ptr(self, trans, dmi_data):
        return self.other_socket.get_direct_mem_ptr_func(trans, dmi_data)

    def invalidate_direct_mem_ptr(self, start_range, end_range):
        self.other_socket.invalidate_direct_mem_ptr_func(start_range, end_range)

class MultiSocket:
    def __init__(self, module: Module, name: str="socket"):
        self.env = module.env
        self.name = module.name + "_{}".format(name)
        self.other_socket = None
        self.m_sockets = []
        self.nb_transport_fw_func = None
        self.nb_transport_bw_func = None
        self.b_transport_func = None
        self.transport_dbg_func = None
        self.get_direct_mem_ptr_func = None
        self.invalidate_direct_mem_ptr_func = None
        self.block_event = self.env.event()
    def bind(self, other):
        if isinstance(other, Socket):
            assert other.other_socket is None, "Bind Error: the socket is bound"
            self.m_sockets.append(other)
            other.other_socket = self
        elif isinstance(other, MultiSocket):
            self.other_socket = other
            other.other_socket = self
        else:
            assert False, "Bind Error: the other is not a socket"
    def register_b_transport(self, func):
        self.b_transport_func = func

    def register_get_direct_mem_ptr(self, func):
        self.get_direct_mem_ptr_func = func

    def register_invalidate_direct_mem_ptr(self, func):
        self.invalidate_direct_mem_ptr_func = func

    def register_transport_dbg(self, func):
        self.transport_dbg_func = func

    def register_nb_transport_bw(self, func):
        self.nb_transport_bw_func = func

    def register_nb_transport_fw(self, func):
        self.nb_transport_fw_func = func

    def b_transport(self, payload, delay, id):
        assert self.m_sockets[id].b_transport_func is not None, "Socket is None"
        self.env.process(self.m_sockets[id].b_transport_func(payload, delay))
        yield self.block_event
        # self.block_event = simpy.Event(self.env)

    def nb_transport_bw(self, trans, phase, t, id):
        assert self.m_sockets[id].nb_transport_bw_func is not None, f"{self.other_socket.name} nb_transport_bw_func is None"
        return self.m_sockets[id].nb_transport_bw_func(trans, phase, t)

    def nb_transport_fw(self, trans, phase, t, id):
        assert self.m_sockets[id].nb_transport_fw_func is not None, f"{self.other_socket.name} nb_transport_fw_func is None"
        return self.m_sockets[id].nb_transport_fw_func(trans, phase, t)

    def transport_dbg(self, trans, id):
        return self.m_sockets[id].transport_dbg_func(trans)

    def get_direct_mem_ptr(self, trans, dmi_data, id):
        return self.m_sockets[id].get_direct_mem_ptr_func(trans, dmi_data)

    def invalidate_direct_mem_ptr(self, start_range, end_range, id):
        self.m_sockets[id].invalidate_direct_mem_ptr_func(start_range, end_range)

class peq_with_get(Module):
    """payload event queue

    """
    def __init__(self, env: simpy.Environment, name: str):
        super().__init__(env, name)
        self.m_scheduled_events = []
        self.m_event = self.env.event()
        self.out = -1
        pass

    def notify(self, trans, t=0):
        self.m_scheduled_events.append([self.env.now + t, trans])
        self.m_scheduled_events.sort(key=lambda x: x[0])
        # yield self.env.timeout(t)
        self.m_event.succeed()
        self.m_event = self.env.event()

    def get_next_transaction(self):
        if len(self.m_scheduled_events) == 0:
            self.out = 0
            return
        now = self.env.now
        dict_ = self.m_scheduled_events[0]
        if dict_[0] <= now:
            trans = dict_[1]
            self.m_scheduled_events.pop(0)
            self.out = trans
            return
            # return trans

        yield self.env.timeout(dict_[0] - now)
        self.m_event.succeed()
        self.m_event = self.env.event()

        self.out = 0

    def cancel_all(self):
        self.m_scheduled_events.clear()
        self.m_event.succeed()

    def get_event(self):
        return self.m_event
