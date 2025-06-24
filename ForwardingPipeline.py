import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal

class ForwardingPipeline(QThread):
    statusSignal = pyqtSignal(str)

    def __init__(self, delay=1):
        super().__init__()
        self.delay = delay
        self.initialize_pipeline()

    def initialize_pipeline(self):
        self.start_time = time.time()
        self.registers = [0] * 32
        self.memory = [0] * 1024
        self.instructions = [None] * 256
        combined = Memory().combined_memory
        self.memory[:len(combined)] = combined
        self.inactive_cycles = 0
        self.data = [0] * 1024
        self.pc = 0
        self.pipeline_regs = {
            "IF": {}, "ID": {}, "EX": {}, "MEM": {}, "WB": {}
        }
        self.inst_count = self._separate_memory()

    def _separate_memory(self):
        count = 0
        for i, val in enumerate(self.memory):
            if isinstance(val, Instruction):
                self.instructions[count] = val
                count += 1
            else:
                break
        for j in range(count, len(self.memory)):
            self.data[j - count] = self.memory[j]
        return count

    def _fetch(self):
        if self.pc < self.inst_count:
            self.pipeline_regs["IF"] = {"IR": self.instructions[self.pc],"NPC": self.pc + 1}
            self.statusSignal.emit(f"Fetch: {self.instructions[self.pc]}")
            self.pc += 1
        else:
            self.pipeline_regs["IF"]["IR"] = None

    def _decode(self):
        ir = self.pipeline_regs["IF"].get("IR")
        if ir:
            self.pipeline_regs["ID"] = {"A": self._forward(ir.rs),"B": self._forward(ir.rt),"IR": ir}
            a, b = self.pipeline_regs["ID"]["A"], self.pipeline_regs["ID"]["B"]
            self.statusSignal.emit(f"Decode: A = {a}, B = {b}")
        else:
            self.pipeline_regs["ID"]["IR"] = None

    def _execute(self):
        ir = self.pipeline_regs["ID"].get("IR")
        if not ir:
            self.pipeline_regs["EX"]["IR"] = None
            return

        A, B, imm, pc = self.pipeline_regs["ID"]["A"], self.pipeline_regs["ID"]["B"], ir.imm, self.pc
        alu_result = 0

        match ir.opcode:
            case 'SUB': alu_result = A - B
            case 'XOR': alu_result = A ^ B
            case 'SLT': alu_result = 1 if A < B else 0
            case 'LOAD' | 'STORE': alu_result = A + imm
            case 'JUMP':
                alu_result = pc + imm + 1
                self.pc = alu_result
                self.pipeline_regs["IF"] = {"IR": None}
                self.pipeline_regs["ID"] = {"IR": None}
                self.statusSignal.emit(f"Jump taken → PC = {self.pc}")
            case 'BEQ':
                if A == B:
                    alu_result = pc + imm - 1
                    self.pc = alu_result
                    self.pipeline_regs["IF"] = {"IR": None}
                    self.pipeline_regs["ID"] = {"IR": None}
                    self.statusSignal.emit(f"Branch taken (BEQ) → PC = {self.pc}")
                else:
                    alu_result = pc
            case 'BNE':
                if A != B:
                    alu_result = pc + imm + 1
                    self.pc = alu_result
                    self.pipeline_regs["IF"] = {"IR": None}
                    self.pipeline_regs["ID"] = {"IR": None}
                    self.statusSignal.emit(f"Branch taken (BNE) → PC = {self.pc}")
                else:
                    alu_result = pc
            case 'ADD': alu_result = A + B
            case 'MUL': alu_result = A * B
            case 'AND': alu_result = A & B
            case 'OR': alu_result = A | B
            case 'ADDI': alu_result = A + imm
            case 'SUBI': alu_result = A - imm

        self.pipeline_regs["EX"] = {"ALU": alu_result, "IR": ir}
        self.statusSignal.emit(f"Execute: ALU = {alu_result}")

    def _memory(self):
        ir = self.pipeline_regs["EX"].get("IR")
        if not ir:
            self.pipeline_regs["MEM"]["IR"] = None
            return

        addr = self.pipeline_regs["EX"]["ALU"]
        self.pipeline_regs["MEM"] = {"ALU": addr, "IR": ir}

        if ir.opcode == 'LOAD':
            self.pipeline_regs["MEM"]["MDR"] = self.data[addr]
        elif ir.opcode == 'STORE':
            self.data[addr] = self.pipeline_regs["ID"]["B"]

        self.statusSignal.emit(f"Memory: MDR = {self.pipeline_regs['MEM'].get('MDR', 'N/A')}")

    def _writeback(self):
        ir = self.pipeline_regs["MEM"].get("IR")
        if not ir:
            return

        alu = self.pipeline_regs["MEM"].get("ALU")
        mdr = self.pipeline_regs["MEM"].get("MDR")

        if ir.opcode in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLT', 'MUL']:
            self.registers[ir.rd] = alu
        elif ir.opcode == 'LOAD':
            self.registers[ir.rt] = mdr
        elif ir.opcode in ['ADDI', 'SUBI']:
            self.registers[ir.rt] = alu
        elif ir.opcode in ['JUMP', 'BEQ', 'BNE']:
            self.pc = alu

        self.statusSignal.emit(f"WriteBack: Registers = {self.registers}")

    def _forward(self, idx):
        if idx == 0:
            return 0
        for stg in ["MEM", "EX"]:
            ir = self.pipeline_regs[stg].get("IR")
            if ir and getattr(ir, 'rd', -1) == idx:
                return self.pipeline_regs[stg].get("ALU")
        return self.registers[idx]

    def advance_Fpipeline(self):
        self._writeback()
        self._memory()
        self._execute()
        self._decode()
        self._fetch()

        active = any(reg.get("IR") for reg in self.pipeline_regs.values())

        if not active and self.pc >= self.inst_count:
            self.inactive_cycles += 1
        else:
            self.inactive_cycles = 0

        return self.inactive_cycles < 2