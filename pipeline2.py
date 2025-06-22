import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal

class SegmentedCPU2(QThread):
    messageChanged = pyqtSignal(str)

    def __init__(self, delay_seconds=1):
        super().__init__()
        self.delay = delay_seconds
        self.initialize()

    def initialize(self):
        self.clock_start = time.time()
        self.reg_file = [0] * 32
        self.full_mem = [0] * 1024
        self.code_mem = [None] * 256
        preload_mem = Memory().combined_memory
        self.full_mem[:len(preload_mem)] = preload_mem
        self.data_mem = [0] * 1024
        self.pc = 0
        self.stage_regs = {
            "FETCH_DEC": {},
            "DEC_EXEC": {},
            "EXEC_MEM": {},
            "MEM_WB": {}
        }
        self.total_instr = self.load_instruction_segment()

    def fetch(self):
        if self.pc < self.total_instr:
            self.stage_regs["FETCH_DEC"]["IR"] = self.code_mem[self.pc]
            self.stage_regs["FETCH_DEC"]["NPC"] = self.pc + 1
            self.pc += 1
            self.messageChanged.emit(f"Fetched: {self.stage_regs['FETCH_DEC']['IR']}")
        else:
            self.stage_regs["FETCH_DEC"]["IR"] = None

    def decode(self):
        instr = self.stage_regs["FETCH_DEC"].get("IR")
        if instr:
            self.stage_regs["DEC_EXEC"]["A"] = self.resolve_forwarding(instr.rs)
            self.stage_regs["DEC_EXEC"]["B"] = self.resolve_forwarding(instr.rt)
            self.stage_regs["DEC_EXEC"]["IR"] = instr
            self.messageChanged.emit(f"Decoded: A = {self.stage_regs['DEC_EXEC']['A']}, B = {self.stage_regs['DEC_EXEC']['B']}")
        else:
            self.stage_regs["DEC_EXEC"]["IR"] = None

    def execute(self):
        instr = self.stage_regs["DEC_EXEC"].get("IR")
        if instr:
            op1 = self.stage_regs["DEC_EXEC"]["A"]
            op2 = self.stage_regs["DEC_EXEC"]["B"]
            result = None

            if instr.opcode == 'ADD':
                result = op1 + op2
            elif instr.opcode == 'SUB':
                result = op1 - op2
            elif instr.opcode == 'MUL':
                result = op1 * op2
            elif instr.opcode in ['LOAD', 'STORE']:
                result = op1 + instr.imm
            elif instr.opcode == 'JUMP':
                result = self.pc + instr.imm
            elif instr.opcode == 'BEQ':
                result = self.pc + instr.imm if op1 == op2 else self.pc
            elif instr.opcode == 'BNE':
                result = self.pc + instr.imm if op1 != op2 else self.pc
            elif instr.opcode == 'AND':
                result = op1 & op2
            elif instr.opcode == 'OR':
                result = op1 | op2
            elif instr.opcode == 'XOR':
                result = op1 ^ op2
            elif instr.opcode == 'SLT':
                result = 1 if op1 < op2 else 0
            elif instr.opcode == 'ADDI':
                result = op1 + instr.imm
            elif instr.opcode == 'SUBI':
                result = op1 - instr.imm

            self.stage_regs["EXEC_MEM"]["RESULT"] = result
            self.stage_regs["EXEC_MEM"]["IR"] = instr
            self.messageChanged.emit(f"Executed: RESULT = {result}")
        else:
            self.stage_regs["EXEC_MEM"]["IR"] = None

    def memory_stage(self):
        instr = self.stage_regs["EXEC_MEM"].get("IR")
        if instr:
            addr = self.stage_regs["EXEC_MEM"]["RESULT"]
            if instr.opcode == 'LOAD':
                mem_data = self.data_mem[addr]
                self.stage_regs["MEM_WB"]["MDR"] = mem_data
            elif instr.opcode == 'STORE':
                self.data_mem[addr] = self.stage_regs["DEC_EXEC"]["B"]
            self.stage_regs["MEM_WB"]["RESULT"] = addr
            self.stage_regs["MEM_WB"]["IR"] = instr
            self.messageChanged.emit(f"Memory Access: MDR = {self.stage_regs['MEM_WB'].get('MDR', 'N/A')}")
        else:
            self.stage_regs["MEM_WB"]["IR"] = None

    def write_back(self):
        instr = self.stage_regs["MEM_WB"].get("IR")
        if instr:
            if instr.opcode in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLT', 'MUL']:
                self.reg_file[instr.rd] = self.stage_regs["MEM_WB"]["RESULT"]
            elif instr.opcode == 'LOAD':
                self.reg_file[instr.rt] = self.stage_regs["MEM_WB"]["MDR"]
            elif instr.opcode in ['ADDI', 'SUBI']:
                self.reg_file[instr.rt] = self.stage_regs["MEM_WB"]["RESULT"]
            elif instr.opcode in ['JUMP', 'BEQ', 'BNE']:
                self.pc = self.stage_regs["MEM_WB"]["RESULT"]
            self.messageChanged.emit(f"Write Back: Registers = {self.reg_file}")

    def run_cycle(self):
        self.write_back()
        self.memory_stage()
        self.execute()
        self.decode()
        self.fetch()

        pipeline_done = not any(self.stage_regs.values())
        return not (self.pc >= self.total_instr and pipeline_done)

    def resolve_forwarding(self, reg_idx):
        if reg_idx == 0:
            return 0
        for stage in ["MEM_WB", "EXEC_MEM"]:
            instr = self.stage_regs[stage].get("IR")
            if instr and instr.rd == reg_idx:
                return self.stage_regs[stage]["RESULT"]
        return self.reg_file[reg_idx]

    def load_instruction_segment(self):
        count = 0
        for i, value in enumerate(self.full_mem):
            if isinstance(value, Instruction):
                self.code_mem[count] = value
                count += 1
            else:
                break
        for j in range(count, len(self.full_mem)):
            self.data_mem[j - count] = self.full_mem[j]
        return count
