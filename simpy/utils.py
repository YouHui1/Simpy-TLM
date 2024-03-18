import simpy


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

    def __init__(self, id=UNINITIALIZED_PHASE) -> None:
        self.m_id = id

class tlm_sync_enum:
    TLM_ACCEPTED = 0
    TLM_UPDATED = 1
    TLM_COMPLETED = 2

class peq_with_get:
    """payload event queue

    """
    def __init__(self, env: simpy.Environment) -> None:
        self.env = env
        self.m_scheduled_events = []
        self.m_event = self.env.event()
        self.m_event2 = self.env.event()
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

class fifo:
    def __init__(self, env: simpy.Environment, capacity=16) -> None:
        self.env = env
        self.buf = simpy.Store(self.env, capacity)

        self.read_event = self.env.event()
        self.write_event = self.env.event()

    def write(self, value):
        self.buf.put(value)
        self.read_event.succeed()
        self.read_event = self.env.event()
        # self.nb_write(value)
        return True

    def read(self):
        return self.nb_read()

    def nb_write(self, value):
        if self.is_full():
            return False
        self.buf.put(value)
        self.read_event.succeed()
        self.read_event = self.env.event()
        return True

    def nb_read(self):
        if self.is_empty():
            return None
        value = self.buf.get().value
        self.write_event.succeed()
        self.write_event = self.env.event()
        return value

    def is_empty(self):
        """检查FIFO是否为空。"""
        return len(self.buf.items) == 0

    def is_full(self):
        """检查FIFO是否已满。"""
        return len(self.buf.items) == self.buf.capacity

class Genetic_Payload:
    def __init__(self) -> None:
        self.m_address = None
        self.m_command = None
        self.m_data = None
        self.m_dmi = False
        self.m_response_status = None
        self.m_length = 0
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
        elif self.m_response_status == tlm_response_status.TLM_OK_RESPONSE:
            # if not sock.block_event.triggered:
                sock.block_event.succeed()
    def set_dmi_allowed(self, dmi_allowed):
        self.m_dmi = dmi_allowed

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

class Module:
    def __init__(self, env, name):
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
    def __init__(self, module: Module):
        self.env = module.env
        self.name = module.name
        self.data = None
        self.other_socket = None
        self.nb_transport_fw_func = None
        self.nb_transport_bw_func = None
        self.b_transport_func = None
        self.transport_dbg_func = None
        self.get_direct_mem_ptr_func = None
        self.invalidate_direct_mem_ptr_func = None
        self.block_event = self.env.event()

    def bind(self, other):
        assert self.other_socket is None and other.other_socket is None, "Bind Error"
        self.other_socket = other
        other.other_socket = self
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
        self.env.process(self.other_socket.b_transport_func(payload, delay))
        yield self.block_event
        # self.block_event = simpy.Event(self.env)

    def nb_transport_bw(self, trans, phase, t):
        ret = 0
        assert self.other_socket.nb_transport_bw_func is not None, f"{self.other_socket.name} nb_transport_bw_func is None"
        self.env.process(self.other_socket.nb_transport_bw_func(trans, phase, t, ret))
        return ret

    def nb_transport_fw(self, trans, phase, t):
        ret = 0
        assert self.other_socket.nb_transport_fw_func is not None, f"{self.other_socket.name} nb_transport_fw_func is None"
        self.env.process(self.other_socket.nb_transport_fw_func(trans, phase, t, ret))
        return ret

    def transport_dbg(self, trans):
        return self.other_socket.transport_dbg_func(trans)

    def get_direct_mem_ptr(self, trans, dmi_data):
        return self.other_socket.get_direct_mem_ptr_func(trans, dmi_data)

    def invalidate_direct_mem_ptr(self, start_range, end_range):
        self.other_socket.invalidate_direct_mem_ptr_func(start_range, end_range)
