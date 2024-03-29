from simpy import Environment
from multi_socket_example.utilities import *
from utils import *


class Bus(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.targ_socket = MultiSocket(self, 'targ_socket')
        self.init_socket = MultiSocket(self, 'init_socket')
        self.m_id_map = {}

        self.targ_socket.register_nb_transport_fw(self.nb_transport_fw)
        self.targ_socket.register_b_transport(self.b_transport)
        self.targ_socket.register_get_direct_mem_ptr(self.get_direct_mem_ptr)
        self.targ_socket.register_transport_dbg(self.transport_dbg)

        self.init_socket.register_nb_transport_bw(self.nb_transport_bw)
        self.init_socket.register_invalidate_direct_mem_ptr(self.invalidate_direct_mem_ptr)


    def nb_transport_fw(self,
                        trans: Generic_Payload,
                        phase: tlm_phase,
                        delay: int,
                        id: int):
        # yield self.env.timeout(0)
        assert id < len(self.targ_socket.m_sockets), "nb_transport_fw: invalid id"
        self.m_id_map[trans] = id
        address = trans.get_address()
        masked_address = [0]
        target_nr = self.decode_address(address, masked_address)
        masked_address = masked_address[0]
        if target_nr < len(self.init_socket.m_sockets):
            trans.set_address(masked_address)
            status = self.init_socket.nb_transport_fw(trans, phase, delay, target_nr)
            if status == tlm_sync_enum.TLM_COMPLETED:
                trans.set_address(address)
            return status
        else:
            return status

    def nb_transport_bw(self,
                        trans: Generic_Payload,
                        phase: tlm_phase,
                        delay: int,
                        id: int):
        # yield self.env.timeout(0)
        assert id < len(self.init_socket.m_sockets), "nb_transport_bw: invalid id"
        address = trans.get_address()
        trans.set_address(self.compose_address(id, address))
        return self.targ_socket.nb_transport_bw(trans, phase, delay, self.m_id_map[trans])

    def b_transport(self,
                    trans: Generic_Payload,
                    delay: int,
                    id: int):
        yield self.env.timeout(delay)
        assert id < len(self.targ_socket.m_sockets), "b_transport: invalid id"
        address = trans.get_address()
        masked_address = [0]
        target_nr = self.decode_address(address, masked_address)

        if target_nr < len(self.init_socket.m_sockets):
            trans.set_address(masked_address)
            self.init_socket.b_transport(trans, delay, target_nr)
            trans.set_address(address)


    def get_direct_mem_ptr(self,
                           trans: Generic_Payload,
                           dmi_data: TLM_DMI,
                           id: int):
        masked_address = [0]
        target_nr = self.decode_address(trans.get_address(), masked_address)
        if target_nr >= len(self.init_socket.m_sockets):
            return False
        trans.set_address(masked_address)
        status = self.init_socket.get_direct_mem_ptr(trans, dmi_data, target_nr)

        dmi_data.set_start_address(self.compose_address(target_nr, dmi_data.get_start_address()))
        dmi_data.set_end_address(self.compose_address(target_nr, dmi_data.get_end_address()))
        return status


    def transport_dbg(self,
                      trans: Generic_Payload,
                      id: int):
        masked_address = 0
        target_nr = self.decode_address(trans.get_address(), masked_address)
        if target_nr >= len(self.init_socket.m_sockets):
            return 0

        trans.set_address(masked_address)

        return self.init_socket.transport_dbg(trans, target_nr)


    def invalidate_direct_mem_ptr(self,
                                  start_range,
                                  end_range,
                                  id):
        bw_start_range = self.compose_address(id, start_range)
        bw_end_range = self.compose_address(id, end_range)

        for i in range(len(self.targ_socket.m_sockets)):
            self.targ_socket.invalidate_direct_mem_ptr(bw_start_range, bw_end_range, i)

    def decode_address(self, address, masked_address):
        target_nr = address & 0x3
        masked_address[0] = address
        return target_nr

    def compose_address(self, target_nr, address):
        return address
