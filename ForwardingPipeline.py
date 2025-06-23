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

        alu_result = {
            'ADD': lambda: A + B,
            'SUB': lambda: A - B,
            'MUL': lambda: A * B,
            'AND': lambda: A & B,
            'OR': lambda: A | B,
            'XOR': lambda: A ^ B,
            'SLT': lambda: 1 if A < B else 0,
            'ADDI': lambda: A + imm,
            'SUBI': lambda: A - imm,
            'LOAD': lambda: A + imm,
            'STORE': lambda: A + imm,
            'JUMP': lambda: pc + imm,
            'BEQ': lambda: pc + imm if A == B else pc,
            'BNE': lambda: pc + imm if A != B else pc
        }.get(ir.opcode, lambda: 0)()

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