from simpy import Environment
from multi_socket_example.utilities import *
from utils import *

class Initiator(Module):
    def __init__(self, env: Environment, name: str):
        super().__init__(env, name)
        self.socket = Socket(self)
        # self.m_mm = mm()
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
                dprint(f"{self.name} wait for event. now: {self.env.now}")
                yield self.end_request_event
                dprint(f"{self.name} free. now: {self.env.now}")

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
            dprint(f'{self.name} trans: {trans} epoch: {i} phase: {phase} now: {self.env.now} delay: {delay}')
            status = self.socket.nb_transport_fw(trans, phase, delay)
            if status[0] == tlm_sync_enum.TLM_UPDATED:
                self.env.process(self.trigger_event(trans, phase, delay))
            elif status[0] == tlm_sync_enum.TLM_COMPLETED:
                self.request_in_progress = None
                self.check_transaction(trans)
            w = SC_PS(rand_ps())
            dprint(f"{self.name} wait epoch {i} for {w}")
            yield self.env.timeout(w)

        yield self.env.timeout(SC_NS(100))

        trans = Generic_Payload()
        trans.set_command(tlm_command.TLM_WRITE_COMMAND)
        trans.set_address(0)
        trans.set_data_ptr(self.data[0])
        trans.set_data_length(4)
        trans.set_streaming_width(4)
        trans.set_byte_enable_ptr(0)
        trans.set_dmi_allowed(False)
        trans.set_response_status(tlm_response_status.TLM_INCOMPLETE_RESPONSE, self.socket)

        delay = SC_PS(rand_ps())
        print("Calling b_transport at {} with delay = {}"
                .format(self.env.now,
                        delay),
                file=fout)
        yield self.env.process(self.socket.b_transport(trans, delay))
        self.check_transaction(trans)

    def nb_transport_bw(self,
                        trans: Generic_Payload,
                        phase: tlm_phase,
                        delay: int,
                        ret):
        yield self.env.timeout(0)
        dprint(f'{self.name} recv: {trans} phase: {phase} now: {self.env.now} delay: {delay}')
        self.env.process(self.trigger_event(trans, phase, delay))
        ret[0] = tlm_sync_enum.TLM_ACCEPTED

    def peq_cb(self, trans, phase):
        # yield self.env.timeout(0)
        dprint(f'{self.name} callback: {trans} phase: {phase} now: {self.env.now}')
        if phase == tlm_phase.END_REQ or (trans == self.request_in_progress and phase == tlm_phase.BEGIN_RESP):
            self.request_in_progress = None
            dprint(f"{self.name} unlock the event. now: {self.env.now}")
            self.end_request_event.succeed()
            self.end_request_event = self.env.event()
        elif phase == tlm_phase.BEGIN_REQ or phase == tlm_phase.END_RESP:
            assert False, "Illegal transaction phase received by initiator"

        if phase == tlm_phase.BEGIN_RESP:
            self.check_transaction(trans)
            # print(">>>", phase)
            fw_phase = tlm_phase.END_RESP
            delay = SC_PS(rand_ps())
            dprint(f'{self.name} trans: {trans} phase: {fw_phase} now: {self.env.now} delay: {delay}')
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
