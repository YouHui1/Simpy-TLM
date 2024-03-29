from simpy import Environment
from multi_socket_example.utilities import *
from utils import *

class Initiator(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.socket = Socket(self)
        self.data = [[0]] * 16
        self.request_in_progress = None
        self.end_request_event = self.env.event()
        self.m_peq = []

        self.mutex = simpy.Resource(self.env, 1)

        self.socket.register_nb_transport_bw(self.nb_transport_bw)

        self.env.process(self.thread_process())

    def trigger_event(self, trans, phase, delay):
        yield self.env.timeout(delay)
        self.peq_cb(trans, phase)

    def thread_process(self):
        trans = None
        phase = tlm_phase()
        delay = 0
        for i in range(1000):
            adr = random.randint(0, 2**31-1)
            cmd = random.randint(0, 1)
            if cmd == tlm_command.TLM_WRITE_COMMAND:
                self.data[i % 16] = random.randint(0, 2**31-1)

            trans = Generic_Payload()
            trans.set_command(cmd)
            trans.set_address(adr)
            trans.set_data_ptr(self.data[i%16])
            trans.set_data_length(4)
            trans.set_streaming_width(4)
            trans.set_byte_enable_ptr(0)
            trans.set_dmi_allowed(False)
            trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.socket)
            if self.request_in_progress is not None:
                yield self.end_request_event

            self.request_in_progress = trans
            phase = tlm_phase.BEGIN_REQ
            delay = SC_PS(rand_ps())

            print("{} {} new, cmd = {}, data = {} at time {}"
                  .format(hex(adr),
                          self.name,
                          'W' if cmd == 1 else 'R',
                          hex(self.data[i % 16][0]) if isinstance(self.data[i % 16], list) else hex(self.data[i % 16]),
                          self.env.now),
                  file=fout)
            status = self.socket.nb_transport_fw(trans, phase, delay)
            if status == tlm_sync_enum.TLM_UPDATED:
                self.env.process(self.trigger_event(trans, phase, delay))
            elif status == tlm_sync_enum.TLM_COMPLETED:
                self.request_in_progress = None
                self.check_transaction(trans)
            w = SC_PS(rand_ps())
            yield self.env.timeout(w)

        yield self.env.timeout(SC_NS(100))

        # trans = Generic_Payload()
        # trans.set_command(tlm_command.TLM_WRITE_COMMAND)
        # trans.set_address(0)
        # trans.set_data_ptr(self.data[0])
        # trans.set_data_length(4)
        # trans.set_streaming_width(4)
        # trans.set_byte_enable_ptr(0)
        # trans.set_dmi_allowed(False)
        # trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.socket)

        # delay = SC_PS(rand_ps())
        # print("Calling b_transport at {} with delay = {}"
        #         .format(self.env.now,
        #                 delay),
        #         file=fout)
        # yield self.env.process(self.socket.b_transport(trans, delay))
        # self.check_transaction(trans)
    def timeout(self, phase, delay):
        yield self.env.timeout(delay)
        print(f"Timeout: {self.name} throw the payload away, phase: {phase}, time: {self.env.now}", file=fout)

    def nb_transport_bw(self,
                        trans: Generic_Payload,
                        phase: tlm_phase,
                        delay: int):
        # yield self.env.timeout(0)
        if (delay > 5000):
            self.env.process(self.timeout(phase, delay))
            self.request_in_progress = None
            self.end_request_event.succeed()
            self.end_request_event = self.env.event()
            return tlm_sync_enum.TLM_COMPLETED
        self.env.process(self.trigger_event(trans, phase, delay))
        return tlm_sync_enum.TLM_ACCEPTED

    def peq_cb(self, trans, phase):
        if phase == tlm_phase.END_REQ or (trans == self.request_in_progress and phase == tlm_phase.BEGIN_RESP):
            self.request_in_progress = None
            self.end_request_event.succeed()
            self.end_request_event = self.env.event()
        elif phase == tlm_phase.BEGIN_REQ or phase == tlm_phase.END_RESP:
            assert False, "Illegal transaction phase received by initiator"

        if phase == tlm_phase.BEGIN_RESP:
            self.check_transaction(trans)
            fw_phase = tlm_phase.END_RESP
            delay = SC_PS(rand_ps())
            self.socket.nb_transport_fw(trans, fw_phase, delay)

    def check_transaction(self, trans: Generic_Payload):
        if trans.is_response_error():
            assert False, "Transaction returned with error"
        cmd = trans.get_command()
        adr = trans.get_address()
        ptr = trans.get_data_ptr()
        print("{} {} check, cmd = {}, data = {} at time {}"
                .format(hex(adr),
                        self.name,
                        'W' if cmd == 1 else 'R',
                        hex(ptr[0]) if isinstance(ptr, list) else hex(ptr),
                        self.env.now),
                file=fout)
