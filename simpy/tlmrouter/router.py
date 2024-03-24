from simpy import Environment
from utils import *
import random


class Router(Module):
    def __init__(self, env: Environment, name: str, N_TARGETS: int):
        super().__init__(env, name)
        self.target_socket = Socket(self)
        self.initiator_socket = [None] * N_TARGETS

        self.target_socket.register_b_transport(self.b_transport)
        self.target_socket.register_get_direct_mem_ptr(self.get_direct_mem_ptr)
        self.target_socket.register_transport_dbg(self.transport_dbg)

        for i in range(N_TARGETS):
            init_sock = Socket_Tagged(self)
            init_sock.register_invalidate_direct_mem_ptr(self.invalidate_direct_mem_ptr, i)
            self.initiator_socket[i] = init_sock

    def b_transport(self, trans: Generic_Payload, delay):
        yield self.env.timeout(0)
        address = trans.get_address()
        masked_address = [None]
        target_nr = self.decode_address(address, masked_address)

        trans.set_address(masked_address[0])

        yield self.env.process(self.initiator_socket[target_nr].b_transport(trans, delay))

        trans.set_response_status(tlm_response_status.TLM_OK_RESPONSE, self.target_socket.other_socket)


    def get_direct_mem_ptr(self, trans: Generic_Payload, dmi_data: TLM_DMI):
        masked_address = [None]
        target_nr = self.decode_address(trans.get_address(), masked_address)

        status = self.initiator_socket[target_nr].get_direct_mem_ptr(trans, dmi_data)

        dmi_data.set_start_address(self.compose_address(target_nr, dmi_data.get_start_address()))
        dmi_data.set_end_address(self.compose_address(target_nr, dmi_data.get_end_address()))

        return status

    def transport_dbg(self, trans: Generic_Payload):
        masked_address = [None]
        target_nr = self.decode_address(trans.get_address(), masked_address)
        trans.set_address(masked_address[0])

        return self.initiator_socket[target_nr].transport_dbg(trans)

    def invalidate_direct_mem_ptr(self, id, start_range, end_range):
        bw_start_range = self.compose_address(id, start_range)
        bw_end_range = self.compose_address(id, end_range)
        self.target_socket.invalidate_direct_mem_ptr(bw_start_range, bw_end_range)


    def decode_address(self, address, masked_address):
        target_nr = (address >> 8) & 0x3
        masked_address[0] = address & 0xff
        return target_nr

    def compose_address(self, target_nr, address):
        return (target_nr << 8) | (address & 0xff)
