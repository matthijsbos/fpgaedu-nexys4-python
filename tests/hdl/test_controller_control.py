from myhdl import (Signal, intbv, always, instance, Simulation, 
        StopSimulation, delay)
from unittest import TestCase

from fpgaedu import ControllerSpec
from fpgaedu.hdl._controller_control import ControllerControl

class ControllerControlTestCase(TestCase):

    WIDTH_ADDR = 32
    WIDTH_DATA = 8

    def setUp(self):
        self.spec = ControllerSpec(self.WIDTH_ADDR, self.WIDTH_DATA)
        # input signals
        self.opcode_cmd = Signal(intbv(0)[self.spec.width_opcode:0])
        self.rx_fifo_empty = Signal(True)
        self.tx_fifo_full = Signal(False)
        self.cycle_autonomous = Signal(False)
        # output signals
        self.rx_fifo_dequeue = Signal(False)
        self.opcode_res = Signal(intbv(0)[self.spec.width_message:0])
        self.nop = Signal(False)
        self.exp_wen = Signal(False)

        self.control = ControllerControl(spec=self.spec, 
                opcode_cmd=self.opcode_cmd, opcode_res=self.opcode_res,
                rx_fifo_empty=self.rx_fifo_empty, 
                rx_fifo_dequeue=self.rx_fifo_dequeue,
                tx_fifo_full=self.tx_fifo_full, nop=self.nop, 
                exp_wen=self.exp_wen, cycle_autonomous=self.cycle_autonomous)
        
    def simulate(self, test_logic, duration=None):
        sim = Simulation(self.control, test_logic)
        sim.run(duration, quiet=False)

    def stop_simulation(self):
        raise StopSimulation()

    def test_control_exp_wen(self):

        @instance
        def test():
            self.opcode_cmd.next = self.spec.opcode_cmd_read
            self.rx_fifo_empty.next = True
            self.tx_fifo_full.next = True
            self.cycle_autonomous.next = False
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.opcode_cmd.next = self.spec.opcode_cmd_write
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.rx_fifo_empty.next = False
            self.tx_fifo_full.next = True
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.rx_fifo_empty.next = True
            self.tx_fifo_full.next = False
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.rx_fifo_empty.next = False
            self.tx_fifo_full.next = False
            yield delay(10)
            self.assertTrue(self.exp_wen)

            self.cycle_autonomous.next = True
            yield delay(10)
            self.assertFalse(self.exp_wen)

            self.stop_simulation()

        self.simulate(test) 

    def test_control_nop_dequeue(self):

        @instance
        def test():

            self.rx_fifo_empty.next = True
            self.tx_fifo_full.next = True
            yield delay(10)
            self.assertTrue(self.nop)
            self.assertFalse(self.rx_fifo_dequeue)

            self.rx_fifo_empty.next = False
            self.tx_fifo_full.next = False
            yield delay(10)
            self.assertFalse(self.nop)
            self.assertTrue(self.rx_fifo_dequeue)

            self.rx_fifo_empty.next = False
            self.tx_fifo_full.next = True
            yield delay(10)
            self.assertTrue(self.nop)
            self.assertFalse(self.rx_fifo_dequeue)

            self.rx_fifo_empty.next = False
            self.tx_fifo_full.next = False
            yield delay(10)
            self.assertFalse(self.nop)
            self.assertTrue(self.rx_fifo_dequeue)

            self.rx_fifo_empty.next = True
            self.tx_fifo_full.next = False
            yield delay(10)
            self.assertTrue(self.nop)
            self.assertFalse(self.rx_fifo_dequeue)

            self.stop_simulation()

        self.simulate(test) 

    def test_control_opcode_res(self):

        @instance
        def test():
            self.rx_fifo_empty.next = False
            self.tx_fifo_full.next = False
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

