import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal

class SegmentedCPU1(QThread):
    messageChanged = pyqtSignal(str)

    def __init__(self, delay_seconds=1):
        super().__init__()
        self.delay = delay_seconds
        self.initialize()

    def initialize(self):
        self.start_clock = time.time()
        self.reg_bank = [0] * 32
        self.main_mem = [0] * 1024
        self.instr_mem = [None] * 256
        preload = Memory().combined_memory
        self.main_mem[:len(preload)] = preload
        self.data_mem = [0] * 1024
        self.pc = 0
        self.stage_regs = {
            "FETCH_DECODE": {},
            "DECODE_EXEC": {},
            "EXEC_MEM": {},
            "MEM_WB": {}
        }
        self.total_instructions = self.extract_instructions()

    def fetch(self):
        if self.pc < self.total_instructions:
            self.stage_regs["FETCH_DECODE"]["IR"] = self.instr_mem[self.pc]
            self.stage_regs["FETCH_DECODE"]["NPC"] = self.pc + 1
            self.pc += 1
            self.messageChanged.emit(f"Fetched: {self.stage_regs['FETCH_DECODE']['IR']}")
        else:
            self.stage_regs["FETCH_DECODE"]["IR"] = None

    def decode(self):
        instr = self.stage_regs["FETCH_DECODE"].get("IR")
        if instr:
            self.stage_regs["DECODE_EXEC"]["A"] = self.reg_bank[instr.rs]
            self.stage_regs["DECODE_EXEC"]["B"] = self.reg_bank[instr.rt]
            self.stage_regs["DECODE_EXEC"]["IR"] = instr
            self.messageChanged.emit(f"Decoded: A = {self.stage_regs['DECODE_EXEC']['A']}, B = {self.stage_regs['DECODE_EXEC']['B']}")
        else:
            self.stage_regs["DECODE_EXEC"]["IR"] = None

    def execute(self):
        instr = self.stage_regs["DECODE_EXEC"].get("IR")
        if instr:
            A = self.stage_regs["DECODE_EXEC"]["A"]
            B = self.stage_regs["DECODE_EXEC"]["B"]
            result = None
            if instr.opcode == 'ADD':
                result = A + B
            elif instr.opcode == 'SUB':
                result = A - B
            elif instr.opcode == 'MUL':
                result = A * B
            elif instr.opcode in ['LOAD', 'STORE']:
                result = A + instr.imm
            elif instr.opcode == 'JUMP':
                result = self.pc + instr.imm
            elif instr.opcode == 'BEQ':
                result = self.pc + instr.imm if A == B else self.pc
            elif instr.opcode == 'BNE':
                result = self.pc + instr.imm if A != B else self.pc
            elif instr.opcode == 'AND':
                result = A & B
            elif instr.opcode == 'OR':
                result = A | B
            elif instr.opcode == 'XOR':
                result = A ^ B
            elif instr.opcode == 'SLT':
                result = 1 if A < B else 0
            elif instr.opcode == 'ADDI':
                result = A + instr.imm
            elif instr.opcode == 'SUBI':
                result = A - instr.imm

            self.stage_regs["EXEC_MEM"]["ALU_RESULT"] = result
            self.stage_regs["EXEC_MEM"]["IR"] = instr
            self.messageChanged.emit(f"Executed: ALUOut = {result}")
        else:
            self.stage_regs["EXEC_MEM"]["IR"] = None

    def memory_stage(self):
        instr = self.stage_regs["EXEC_MEM"].get("IR")
        if instr:
            addr = self.stage_regs["EXEC_MEM"]["ALU_RESULT"]
            if instr.opcode == 'LOAD':
                mdr = self.data_mem[addr]
                self.stage_regs["MEM_WB"]["MDR"] = mdr
            elif instr.opcode == 'STORE':
                self.data_mem[addr] = self.stage_regs["DECODE_EXEC"]["B"]

            self.stage_regs["MEM_WB"]["ALU_RESULT"] = addr
            self.stage_regs["MEM_WB"]["IR"] = instr
            self.messageChanged.emit(f"Memory Access: MDR = {self.stage_regs['MEM_WB'].get('MDR', 'N/A')}")
        else:
            self.stage_regs["MEM_WB"]["IR"] = None

    def write_back(self):
        instr = self.stage_regs["MEM_WB"].get("IR")
        if instr:
            if instr.opcode in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLT', 'MUL']:
                self.reg_bank[instr.rd] = self.stage_regs["MEM_WB"]["ALU_RESULT"]
            elif instr.opcode == 'LOAD':
                self.reg_bank[instr.rt] = self.stage_regs["MEM_WB"]["MDR"]
            elif instr.opcode in ['ADDI', 'SUBI']:
                self.reg_bank[instr.rt] = self.stage_regs["MEM_WB"]["ALU_RESULT"]
            elif instr.opcode in ['JUMP', 'BEQ', 'BNE']:
                self.pc = self.stage_regs["MEM_WB"]["ALU_RESULT"]
            self.messageChanged.emit(f"Write Back: Registers = {self.reg_bank}")

    def run_cycle(self):
        self.write_back()
        self.memory_stage()
        self.execute()
        self.decode()
        self.fetch()

        if self.check_data_hazard():
            self.inject_stall()

        pipeline_empty = all(not reg for reg in self.stage_regs.values())
        return not (self.pc >= self.total_instructions and pipeline_empty)

    def check_data_hazard(self):
        current = self.stage_regs["DECODE_EXEC"].get("IR")
        prev = self.stage_regs["EXEC_MEM"].get("IR")
        if current and prev:
            return current.rs == prev.rd or current.rt == prev.rd
        return False

    def inject_stall(self):
        self.stage_regs["FETCH_DECODE"] = {"IR": None, "NPC": None}
        self.messageChanged.emit("Pipeline stalled due to hazard")

    def extract_instructions(self):
        count = 0
        for i, entry in enumerate(self.main_mem):
            if isinstance(entry, Instruction):
                self.instr_mem[count] = entry
                count += 1
            else:
                break
        for j in range(count, len(self.main_mem)):
            self.data_mem[j - count] = self.main_mem[j]
        return count
