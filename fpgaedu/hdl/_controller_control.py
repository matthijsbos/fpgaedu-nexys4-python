from myhdl import (always_comb, Signal)

def ControllerControl(spec, reset, opcode_cmd, opcode_res, rx_ready, 
        cycle_autonomous, rx_next, tx_ready, nop, exp_wen,
        exp_reset, cycle_start, cycle_pause, cycle_step, exp_reset_active=False):
    '''
    Input signals:
        opcode_cmd
        rx_ready
        cycle_autonomous
        tx_ready
    Output signals:
        opcode_res
        rx_next
        nop
        exp_wen
        exp_reset
        cycle_start
        cycle_pause
        cycle_step
    '''

    nop_int = Signal(True) 
   
    @always_comb
    def internal_logic():
        nop_int.next = (not rx_ready or not tx_ready or reset == reset.active)

    @always_comb
    def output_logic():

        rx_next.next = not nop_int
        nop.next = nop_int

        exp_wen.next = (opcode_cmd == spec.opcode_cmd_write and
                not cycle_autonomous and not nop_int and reset != reset.active)

        if ((reset == reset.active) or 
                (opcode_cmd == spec.opcode_cmd_reset and not nop_int)):
            exp_reset.next = exp_reset_active
        else:
            exp_reset.next = not exp_reset_active

        # Set opcode_res
        opcode_res.next = 0
        if reset == reset.active:
            opcode_res.next = 0
        if opcode_cmd == spec.opcode_cmd_read and not cycle_autonomous:
            opcode_res.next = spec.opcode_res_read_success
        elif opcode_cmd == spec.opcode_cmd_read and cycle_autonomous:
            opcode_res.next = spec.opcode_res_read_error_mode
        elif opcode_cmd == spec.opcode_cmd_write and not cycle_autonomous:
            opcode_res.next = spec.opcode_res_write_success
        elif opcode_cmd == spec.opcode_cmd_write and cycle_autonomous:
            opcode_res.next = spec.opcode_res_write_error_mode
        elif opcode_cmd == spec.opcode_cmd_reset:
            opcode_res.next = spec.opcode_res_reset_success
        elif opcode_cmd == spec.opcode_cmd_step and not cycle_autonomous:
            opcode_res.next = spec.opcode_res_step_success
        elif opcode_cmd == spec.opcode_cmd_step and cycle_autonomous:
            opcode_res.next = spec.opcode_res_step_error_mode
        elif opcode_cmd == spec.opcode_cmd_start and not cycle_autonomous:
            opcode_res.next = spec.opcode_res_start_success
        elif opcode_cmd == spec.opcode_cmd_start and cycle_autonomous:
            opcode_res.next = spec.opcode_res_start_error_mode
        elif opcode_cmd == spec.opcode_cmd_pause and cycle_autonomous:
            opcode_res.next = spec.opcode_res_pause_success
        elif opcode_cmd == spec.opcode_cmd_pause and not cycle_autonomous:
            opcode_res.next = spec.opcode_res_pause_error_mode
        elif opcode_cmd == spec.opcode_cmd_status:
            opcode_res.next = spec.opcode_res_status

        cycle_start.next = (opcode_cmd == spec.opcode_cmd_start and 
                not cycle_autonomous and not nop_int and reset != reset.active)
        cycle_pause.next = (opcode_cmd == spec.opcode_cmd_pause and 
                cycle_autonomous and not nop_int and reset != reset.active)
        cycle_step.next = (opcode_cmd == spec.opcode_cmd_step and 
                not cycle_autonomous and not nop_int and reset != reset.active)


    return internal_logic, output_logic
