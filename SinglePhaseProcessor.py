import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal


class SinglePhaseProcessor(QThread):
    statusSignal = pyqtSignal(str)

    def __init__(self, delay=1):
        super().__init__()
        self.delay = delay
        self._setup()

    def _setup(self):
        """
        Inicializa registros, memoria, contadores y variables de control.
        """
        self.start_time = time.time()
        self.reg_file = [0] * 32                 # Registros de propósito general
        full_memory = Memory().combined_memory
        self.memory_block = [0] * 1024
        self.instr_set = [None] * 256
        self.data_block = [0] * 1024
        self.pc = 0
        self.ir = None
        self.srcA = 0
        self.srcB = 0
        self.alu_result = 0
        self.data_buffer = 0
        self.memory_block[:len(full_memory)] = full_memory
        self.total_instructions = self._split_memory()

# Separa las instrucciones y datos de la memoria combinada
    def _split_memory(self):
        count = 0
        for i, val in enumerate(self.memory_block):
            if isinstance(val, Instruction):
                self.instr_set[count] = val
                count += 1
            else:
                break
        for i in range(count, len(self.memory_block)):
            self.data_block[i - count] = self.memory_block[i]
        return count

# Ejecuta el ciclo completo del procesador uniciclo:
# Fetch → Decode → Execute → Memory → WriteBack.
    def FullCycle(self):
        """
        Ejecuta el ciclo completo del procesador uniciclo:
        Fetch → Decode → Execute → Memory → WriteBack.
        """
        # Fetch
        self.ir = self.instr_set[self.pc]
        self.pc += 1
        self.statusSignal.emit(f"Fetch: {self.ir}")

        # Decode
        self.srcA = self.reg_file[self.ir.rs]
        self.srcB = self.reg_file[self.ir.rt]
        self.statusSignal.emit(f"Decode: A = {self.srcA}, B = {self.srcB}")

        # Execute
        op, imm = self.ir.opcode, self.ir.imm
        a, b, pc = self.srcA, self.srcB, self.pc

        alu_ops = {
            'ADD': lambda: a + b,
            'SUB': lambda: a - b,
            'MUL': lambda: a * b,
            'AND': lambda: a & b,
            'OR':  lambda: a | b,
            'XOR': lambda: a ^ b,
            'SLT': lambda: 1 if a < b else 0,
            'ADDI': lambda: a + imm,
            'SUBI': lambda: a - imm,
            'LOAD': lambda: a + imm,
            'STORE': lambda: a + imm,
            'JUMP': lambda: pc + imm,
            'BEQ': lambda: pc + imm if a == b else pc,
            'BNE': lambda: pc + imm if a != b else pc
        }

        self.alu_result = alu_ops.get(op, lambda: 0)()
        self.statusSignal.emit(f"Execute: Result = {self.alu_result}")

        # Memory
        if op == 'LOAD':
            self.data_buffer = self.data_block[self.alu_result]
        elif op == 'STORE':
            self.data_block[self.alu_result] = b
        self.statusSignal.emit(f"Memory: Buffer = {self.data_buffer}")

        # Write Back
        if op in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLT', 'MUL']:
            self.reg_file[self.ir.rd] = self.alu_result
        elif op == 'LOAD':
            self.reg_file[self.ir.rt] = self.data_buffer
        elif op in ['JUMP', 'BEQ', 'BNE']:
            self.pc = self.alu_result
        elif op in ['ADDI', 'SUBI']:
            self.reg_file[self.ir.rt] = self.alu_result

        self.statusSignal.emit(f"WriteBack: Registers = {self.reg_file}")


# Ejecuta una instrucción completa (uniciclo).
    def Scycle(self):

        if self.pc >= self.total_instructions:
            return False
        self.FullCycle()
        return True
