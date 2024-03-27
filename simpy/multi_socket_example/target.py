from simpy import Environment
from multi_socket_example.utilities import *
from utils import *

tlm_phase.DECLARE_EXTENDED_PHASE("internal_ph")

class Target(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.socket = Socket(self)
        self.socket.register_nb_transport_fw(self.nb_transport_fw)
        # self.m_peq = []

        self.mutex = simpy.Resource(self.env, 1)
        self.request = None

        self.n_trans = 0
        self.response_in_progress = False
        self.next_response_pending: Generic_Payload | None = None
        self.end_req_pending = []

    def trigger_event(self, trans, phase, delay):
        yield self.env.timeout(delay)
        self.peq_cb(trans, phase)

    def nb_transport_fw(self,
                        trans: Generic_Payload,
                        phase: tlm_phase,
                        delay: int,
                        ret):
        yield self.env.timeout(0)
        adr = trans.get_address()
        len_ = trans.get_data_length()
        byt = trans.get_byte_enable_ptr()
        wid = trans.get_streaming_width()

        if byt != 0:
            trans.set_response_status(tlm_response_status.TLM_BYTE_ENABLE_ERROR_RESPONSE)
            ret[0] = tlm_sync_enum.TLM_COMPLETED
            return
        if len_ > 4 or wid < len_:
            trans.set_response_status(tlm_response_status.TLM_BURST_ERROR_RESPONSE)
            ret[0] = tlm_sync_enum.TLM_COMPLETED
            return
        # print("????4")
        dprint(f'{self.name} recv: {trans} phase: {phase} now: {self.env.now} delay: {delay} ??: {self.n_trans} ')
        self.env.process(self.trigger_event(trans, phase, delay))
        # yield from self.m_peq.notify(trans, phase, delay)
        # print("????5")
        ret[0] = tlm_sync_enum.TLM_ACCEPTED

    def peq_cb(self, trans: Generic_Payload, phase: tlm_phase):
        status = [0]
        delay = [0]
        dprint(f'{self.name} callback: {trans} phase: {phase} now: {self.env.now} delay: {delay} ??: {self.n_trans}')
        # print(f'{self.name} callback: {trans} phase: {phase} now: {self.env.now} delay: {delay} ??: {self.n_trans}')
        if phase == tlm_phase.BEGIN_REQ:
            if self.n_trans == 2:
                self.end_req_pending.append(trans)
            else:
                self.send_end_req(trans, status)
                if status[0] == tlm_sync_enum.TLM_COMPLETED:
                    return
        elif phase == tlm_phase.END_RESP:
            if not self.response_in_progress:
                assert False, "Illegal transaction phase END_RESP received by target"

            self.n_trans -= 1
            # dprint(f"{self.env.now} {self} '-' {self.n_trans}")

            self.response_in_progress = False
            if self.next_response_pending is not None:
                self.send_response(self.next_response_pending)
                self.next_response_pending = None
                self.mutex.release(self.request)


            if len(self.end_req_pending) != 0:
                self.send_end_req(self.end_req_pending[0], status)
                self.end_req_pending.pop(0)
        elif phase == tlm_phase.END_REQ or phase == tlm_phase.BEGIN_RESP:
            assert False, "Illegal transaction phase received by target"
        else:
            if phase == tlm_phase.m_ex_ph['internal_ph']:
                cmd = trans.get_command()
                adr = trans.get_address()
                ptr = trans.get_data_ptr()
                len_ = trans.get_data_length()

                if cmd == tlm_command.TLM_READ_COMMAND:
                    ptr = random.randint(0, 2**31-1)
                    print("{} {} Execute READ, target = {}, data = {}"
                            .format(hex(adr),
                                    self.name,
                                    self.name,
                                    hex(ptr[0]) if isinstance(ptr, list) else hex(ptr)),
                            file=fout)
                elif cmd == tlm_command.TLM_WRITE_COMMAND:
                    print("{} {} Execute READ, target = {}, data = {}"
                            .format(hex(adr),
                                    self.name,
                                    self.name,
                                    hex(ptr[0]) if isinstance(ptr, list) else hex(ptr)),
                            file=fout)
                trans.set_response_status(tlm_response_status.TLM_OK_RESPONSE, self.socket)
                if self.response_in_progress:
                    # while self.next_response_pending is not None:
                    #     yield self.env.timeout(1000)
                    if self.next_response_pending is not None:
                        # print(self.next_response_pending)
                        assert False, f"{self}: Attempt to have two pending responses in target"
                    self.next_response_pending = trans
                    self.request = self.mutex.request()
                else:
                    self.send_response(trans)

    def send_end_req(self, trans: Generic_Payload, status):
        bw_phase = tlm_phase.END_REQ
        int_phase = tlm_phase.m_ex_ph['internal_ph']
        delay = SC_PS(rand_ps())

        dprint(f'{self.name} trans: {trans} phase: {bw_phase} now: {self.env.now} delay: {delay} ??: {self.n_trans}')
        status = self.socket.nb_transport_bw(trans, bw_phase, delay)

        if status[0] == tlm_sync_enum.TLM_COMPLETED:
            return

        delay = delay + SC_PS(rand_ps())
        dprint(f'{self.name} selfcallback: {trans} phase: {bw_phase} now: {self.env.now} delay: {delay} ??: {self.n_trans}')
        self.env.process(self.trigger_event(trans, int_phase, delay))
        self.n_trans += 1
        # dprint(f"{self.env.now} {self} '+' {self.n_trans}")
        return

    def send_response(self, trans: Generic_Payload):
        self.response_in_progress = True
        bw_phase = tlm_phase.BEGIN_RESP
        delay = 0
        dprint(f'{self.name} trans: {trans} phase: {bw_phase} now: {self.env.now} delay: {delay} ??: {self.n_trans}')
        status = self.socket.nb_transport_bw(trans, bw_phase, delay)
        if status[0] == tlm_sync_enum.TLM_UPDATED:
            self.env.process(self.trigger_event(trans, bw_phase, delay))
            # yield from self.m_peq.notify(trans, bw_phase, delay)
        elif status[0] == tlm_sync_enum.TLM_COMPLETED:
            self.n_trans -= 1
            self.response_in_progress = False
