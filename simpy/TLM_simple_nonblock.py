from utils import *
import random

class ResponseError(Exception):
    pass


class Initiator(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.m_initiator_port = Socket(self)
        self.m_test_peq = peq_with_get(self.env, "m_test_peq")
        self.m_slv_end_req_evt = self.env.event()

        self.m_initiator_port.register_nb_transport_bw(self.nb_transport_bw_func)

        self.env.process(self.SendReqThread())
        self.env.process(self.SendEndRespThread())

    def SendReqThread(self):
        t_cycle_cnt = 0
        t_phase = tlm_phase(tlm_phase.BEGIN_REQ)
        t_delay = 0
        while True:
            t_cycle_cnt += 1
            t_delay = t_cycle_cnt
            t_payload = Generic_Payload()
            t_payload.set_address(0x10000 + t_cycle_cnt)
            print("{} \033[34m [{}] call nb_transport_fw, BEGIN_REQ phase, addr = {}, delay cycle {} \033[0m"
                  .format(self.name,
                          self.env.now,
                          hex(t_payload.get_address()),
                          t_cycle_cnt))
            self.m_initiator_port.nb_transport_fw(t_payload, t_phase, t_delay)

            yield self.m_slv_end_req_evt

            yield self.env.timeout(1)

    def nb_transport_bw_func(self,
                             payload: Generic_Payload,
                             phase: tlm_phase,
                             delay: int,
                             return_value: tlm_sync_enum):
        yield self.env.timeout(0)
        if phase.m_id == tlm_phase.END_REQ:
            print("{} \033[35m [{}] nb_transport_bw_func recv END_REQ phase, addr = {}\033[0m"
                  .format(self.name,
                          self.env.now,
                          hex(payload.get_address())))
            self.m_slv_end_req_evt.succeed()
            self.m_slv_end_req_evt = self.env.event()
        elif phase.m_id == tlm_phase.BEGIN_RESP:
            print("{} \033[35m [{}] nb_transport_bw_func recv BEGIN_RESP phase, addr = {}\033[0m"
                  .format(self.name,
                          self.env.now,
                          hex(payload.get_address())))
            self.m_test_peq.notify(payload)
        else:
            assert False, f"{self.name} Invalid phase"

        return_value = tlm_sync_enum.TLM_ACCEPTED

    def SendEndRespThread(self):
        t_get = -1
        t_phase = tlm_phase(tlm_phase.END_RESP)
        t_delay = 0
        while True:
            yield self.m_test_peq.get_event()
            yield from self.m_test_peq.get_next_transaction()
            t_get = self.m_test_peq.out
            while t_get != 0:

                print("{} \033[34m [{}] call nb_transport_fw, END_RESP phase, addr = {}\033[0m"
                        .format(self.name,
                                self.env.now,
                                hex(t_get.get_address())))
                self.m_initiator_port.nb_transport_fw(t_get, t_phase, t_delay)
                t_get = 0
                yield from self.m_test_peq.get_next_transaction()
                t_get = self.m_test_peq.out

class Target(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.m_target_port = Socket(self)
        self.m_target_port.register_nb_transport_fw(self.nb_transport_fw_func)

        self.m_req_fifo = fifo(self.env)
        self.m_resp_fifo = fifo(self.env)

        self.env.process(self.MainThread())
        self.env.process(self.BeginRespThread())

    def nb_transport_fw_func(self,
                             payload: Generic_Payload,
                             phase: tlm_phase,
                             delay: int,
                             return_value: tlm_sync_enum):
        yield self.env.timeout(delay)
        if phase.m_id == tlm_phase.BEGIN_REQ:
            # yield self.m_req_fifo.write_event
            self.m_req_fifo.write(payload)
            print("{} \033[35m [{}] nb_transport_fw_func recv BEGIN_REQ phase, addr = {}\033[0m"
                  .format(self.name,
                          self.env.now,
                          hex(payload.get_address())))

        elif phase.m_id == tlm_phase.END_RESP:
            print("{} \033[35m [{}] nb_transport_fw_func recv END_RESP phase, addr = {}\033[0m"
                  .format(self.name,
                          self.env.now,
                          hex(payload.get_address())))
        else:
            assert False, f"{self.name} Invalid phase"

        return_value = tlm_sync_enum.TLM_ACCEPTED

    def MainThread(self):
        t_phase = tlm_phase(tlm_phase.END_REQ)
        t_delay = 0
        while True:
            yield self.m_req_fifo.read_event
            t_payload = self.m_req_fifo.read()
            # print(t_payload)

            print("{} \033[38m [{}] call nb_transport_bw, END_REQ phase, addr = {}\033[0m"
                  .format(self.name,
                          self.env.now,
                          hex(t_payload.get_address())))

            self.m_target_port.nb_transport_bw(t_payload, t_phase, t_delay)
            # yield self.m_resp_fifo.read_event
            self.m_resp_fifo.write(t_payload)
            yield self.env.timeout(1)

    def BeginRespThread(self):
        t_phase = tlm_phase(tlm_phase.BEGIN_RESP)
        t_delay = 1
        while True:
            yield self.m_resp_fifo.read_event
            t_payload = self.m_resp_fifo.read()
            print("{} \033[38m [{}] call nb_transport_bw, BEGIN_RESP phase, addr = {}\033[0m"
                  .format(self.name,
                          self.env.now,
                          hex(t_payload.get_address())))

            self.m_target_port.nb_transport_bw(t_payload, t_phase, t_delay)
            yield self.env.timeout(1)


class Top(Module):
    def __init__(self, env, name):
        super().__init__(env, name)
        self.initiator = Initiator(self.env, "init")
        self.target = Target(self.env, "targ")
        self.initiator.m_initiator_port.bind(self.target.m_target_port)

if __name__ == '__main__':
    env = simpy.Environment()
    top = Top(env, 'top')
    env.run(until=20)
