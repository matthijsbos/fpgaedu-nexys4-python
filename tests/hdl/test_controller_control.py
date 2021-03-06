from myhdl import (Signal, ResetSignal, intbv, always, instance, Simulation, 
        StopSimulation, delay)
from unittest import TestCase

from fpgaedu import ControllerSpec
from fpgaedu.hdl._controller_control import ControllerControl

class ControllerControlTestCase(TestCase):

    WIDTH_ADDR = 32
    WIDTH_DATA = 8
    EXP_RESET_ACTIVE = False

    def setUp(self):
        self.spec = ControllerSpec(self.WIDTH_ADDR, self.WIDTH_DATA)
        # input signals
        self.opcode_cmd = Signal(intbv(0)[self.spec.width_opcode:0])
        self.rx_ready = Signal(False)
        self.tx_ready = Signal(False)
        self.cycle_autonomous = Signal(False)
        self.reset = ResetSignal(True, active=False, async=False)
        # output signals
        self.rx_next = Signal(False)
        self.opcode_res = Signal(intbv(0)[self.spec.width_message:0])
        self.nop = Signal(False)
        self.exp_wen = Signal(False)
        self.exp_reset = ResetSignal(True, active=self.EXP_RESET_ACTIVE, 
                async=False)
        self.cycle_start = Signal(False)
        self.cycle_pause = Signal(False)
        self.cycle_step = Signal(False)

        self.control = ControllerControl(spec=self.spec, reset=self.reset,
                opcode_cmd=self.opcode_cmd, opcode_res=self.opcode_res,
                rx_ready=self.rx_ready, 
                rx_next=self.rx_next,
                tx_ready=self.tx_ready, nop=self.nop, 
                exp_wen=self.exp_wen, exp_reset=self.exp_reset,
                cycle_autonomous=self.cycle_autonomous,
                cycle_start=self.cycle_start, cycle_pause=self.cycle_pause,
                cycle_step=self.cycle_step, 
                exp_reset_active=self.EXP_RESET_ACTIVE)
        
    def simulate(self, test_logic, duration=None):
        sim = Simulation(self.control, test_logic)
        sim.run(duration, quiet=False)

    def stop_simulation(self):
        raise StopSimulation()

    def test_exp_wen(self):

        @instance
        def test():
            self.opcode_cmd.next = self.spec.opcode_cmd_read
            self.rx_ready.next = False
            self.tx_ready.next = False
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.opcode_cmd.next = self.spec.opcode_cmd_write
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.rx_ready.next = True
            self.tx_ready.next = False
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.rx_ready.next = False
            self.tx_ready.next = True
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.rx_ready.next = True
            self.tx_ready.next = True
            yield delay(10)
            self.assertTrue(self.exp_wen)

            self.cycle_autonomous.next = True
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.stop_simulation()

        self.simulate(test) 

    def test_exp_reset(self):

        @instance
        def test():
            yield delay(10)
    
            self.opcode_cmd.next = self.spec.opcode_cmd_reset
            self.rx_ready.next = False
            self.tx_ready.next = False
            yield delay(10)
            self.assertEquals(self.exp_reset, not self.EXP_RESET_ACTIVE)

            self.opcode_cmd.next = self.spec.opcode_cmd_reset
            self.rx_ready.next = True
            self.tx_ready.next = False
            yield delay(10)
            self.assertEquals(self.exp_reset, not self.EXP_RESET_ACTIVE)

            self.opcode_cmd.next = self.spec.opcode_cmd_reset
            self.rx_ready.next = False
            self.tx_ready.next = True
            yield delay(10)
            self.assertEquals(self.exp_reset, not self.EXP_RESET_ACTIVE)

            self.opcode_cmd.next = self.spec.opcode_cmd_reset
            self.rx_ready.next = True
            self.tx_ready.next = True
            yield delay(10)
            self.assertEquals(self.exp_reset, self.EXP_RESET_ACTIVE)

            # assert that the exp_reset signal is activated when the controller 
            # reset signal is activated
            self.reset.next = self.reset.active
            yield delay(10)
            self.assertEquals(self.exp_reset, self.EXP_RESET_ACTIVE)

            self.stop_simulation()

        self.simulate(test)

    def test_nop_dequeue(self):

        @instance
        def test():

            self.rx_ready.next = False
            self.tx_ready.next = False
            yield delay(10)
            self.assertTrue(self.nop)
            self.assertFalse(self.rx_next)

            self.rx_ready.next = True
            self.tx_ready.next = True
            yield delay(10)
            self.assertFalse(self.nop)
            self.assertTrue(self.rx_next)

            self.rx_ready.next = True
            self.tx_ready.next = False
            yield delay(10)
            self.assertTrue(self.nop)
            self.assertFalse(self.rx_next)

            self.rx_ready.next = True
            self.tx_ready.next = True
            yield delay(10)
            self.assertFalse(self.nop)
            self.assertTrue(self.rx_next)

            self.rx_ready.next = False
            self.tx_ready.next = True
            yield delay(10)
            self.assertTrue(self.nop)
            self.assertFalse(self.rx_next)

            self.stop_simulation()

        self.simulate(test) 

    def test_opcode_res(self):

        @instance
        def test():
            self.rx_ready.next = True
            self.tx_ready.next = True
            self.cycle_autonomous.next = False

            def test_opcode(cmd, res_expected):
                self.opcode_cmd.next = cmd
                yield delay(10)
                self.assertEquals(self.opcode_res, res_expected)

            yield test_opcode(self.spec.opcode_cmd_read, 
                    self.spec.opcode_res_read_success)
            yield test_opcode(self.spec.opcode_cmd_write,
                    self.spec.opcode_res_write_success)
            yield test_opcode(self.spec.opcode_cmd_reset,
                    self.spec.opcode_res_reset_success)
            yield test_opcode(self.spec.opcode_cmd_step,
                    self.spec.opcode_res_step_success)
            yield test_opcode(self.spec.opcode_cmd_start,
                    self.spec.opcode_res_start_success)
            yield test_opcode(self.spec.opcode_cmd_pause,
                    self.spec.opcode_res_pause_error_mode)
            yield test_opcode(self.spec.opcode_cmd_status,
                    self.spec.opcode_res_status)

            self.cycle_autonomous.next = True
            yield delay(10)

            yield test_opcode(self.spec.opcode_cmd_read, 
                    self.spec.opcode_res_read_error_mode)
            yield test_opcode(self.spec.opcode_cmd_write,
                    self.spec.opcode_res_write_error_mode)
            yield test_opcode(self.spec.opcode_cmd_reset,
                    self.spec.opcode_res_reset_success)
            yield test_opcode(self.spec.opcode_cmd_step,
                    self.spec.opcode_res_step_error_mode)
            yield test_opcode(self.spec.opcode_cmd_start,
                    self.spec.opcode_res_start_error_mode)
            yield test_opcode(self.spec.opcode_cmd_pause,
                    self.spec.opcode_res_pause_success)
            yield test_opcode(self.spec.opcode_cmd_status,
                    self.spec.opcode_res_status)

            self.stop_simulation()

        self.simulate(test) 

    def test_cycle_start(self):
        @instance
        def test():
            yield delay(10)
            
            # rx empty, tx full, no start
            self.opcode_cmd.next = self.spec.opcode_cmd_start
            self.rx_ready.next = False
            self.tx_ready.next = False
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_start)

            # tx full, no start
            self.opcode_cmd.next = self.spec.opcode_cmd_start
            self.rx_ready.next = True
            self.tx_ready.next = False
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_start)

            # rx empty, no start
            self.opcode_cmd.next = self.spec.opcode_cmd_start
            self.rx_ready.next = False
            self.tx_ready.next = True
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_start)

            # should signal start now
            self.opcode_cmd.next = self.spec.opcode_cmd_start
            self.rx_ready.next = True
            self.tx_ready.next = True
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertTrue(self.cycle_start)

            # cycle controller in autonomous mode, should no longer signal 
            # start 
            self.cycle_autonomous.next = True
            yield delay(10)
            self.assertFalse(self.cycle_start)

            self.reset.next = self.reset.active
            yield delay(10)
            self.assertFalse(self.cycle_start)

            self.stop_simulation()

        self.simulate(test) 


    def test_cycle_pause(self):
        @instance
        def test():
            yield delay(10)

            # rx empty, tx full, no pause
            self.opcode_cmd.next = self.spec.opcode_cmd_pause
            self.rx_ready.next = False
            self.tx_ready.next = False
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_pause)

            # rx empty, no pause
            self.opcode_cmd.next = self.spec.opcode_cmd_pause
            self.rx_ready.next = False
            self.tx_ready.next = True
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_pause)

            # tx full, no pause
            self.opcode_cmd.next = self.spec.opcode_cmd_pause
            self.rx_ready.next = True
            self.tx_ready.next = False
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_pause)

            # cycle controller not in autonomous mode, no pause
            self.opcode_cmd.next = self.spec.opcode_cmd_pause
            self.rx_ready.next = True
            self.tx_ready.next = True
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_pause)

            # cycle controller in autonomous mode, pause signal
            self.opcode_cmd.next = self.spec.opcode_cmd_pause
            self.rx_ready.next = True
            self.tx_ready.next = True
            self.cycle_autonomous.next = True
            yield delay(10)
            self.assertTrue(self.cycle_pause)

            # cycle controller switches to manual mode, no longer a pause 
            # signal emitted
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_pause)

            self.stop_simulation()

        self.simulate(test) 

    def test_cycle_step(self):
        @instance
        def test():
            yield delay(10)

            # rx empty, tx full, no step
            self.opcode_cmd.next = self.spec.opcode_cmd_step
            self.rx_ready.next = False
            self.tx_ready.next = False
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_step)
            
            # tx full, no step
            self.opcode_cmd.next = self.spec.opcode_cmd_step
            self.rx_ready.next = True
            self.tx_ready.next = False
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_step)

            # rx empty, no step
            self.opcode_cmd.next = self.spec.opcode_cmd_step
            self.rx_ready.next = False
            self.tx_ready.next = True
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.cycle_step)

            # in autonomous mode, no step
            self.opcode_cmd.next = self.spec.opcode_cmd_step
            self.rx_ready.next = True
            self.tx_ready.next = True
            self.cycle_autonomous.next = True
            yield delay(10)
            self.assertFalse(self.cycle_step)

            # not in autonomous mode, no step
            self.opcode_cmd.next = self.spec.opcode_cmd_step
            self.rx_ready.next = True
            self.tx_ready.next = True
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertTrue(self.cycle_step)

            self.stop_simulation()

        self.simulate(test) 

