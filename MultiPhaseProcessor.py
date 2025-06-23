import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal


class MultiStageProcessor(QThread):
    statusUpdate = pyqtSignal(str)

    def __init__(self, delay = 1):
        super().__init__()
        self.cycle_delay = delay
        self.initialize()

    def initialize(self):
        self.start_time = time.time()
        self.regs = [0] * 32                  #GPRs
        raw_memory = Memory().combined_memory
        self.main_memory = [0] * 1024
        self.instr_mem = [None] * 256
        self.data_mem = [0] * 1024
        self.PC = 0
        self.prev_PC = -1
        self.IR = None
        self.regA = 0
        self.regB = 0
        self.result = 0
        self.MEM_data = 0
        self.phase = 'FETCH'
        self.main_memory[:len(raw_memory)] = raw_memory
        self.total_instructions = self._load_memory()

# Separa el contenido cargado en memoria combinada entre instrucciones y datos,
# y los distribuye en memoria de instrucciones y memoria de datos.
    def _load_memory(self):
        count = 0
        for i, val in enumerate(self.main_memory):
            if isinstance(val, Instruction):
                self.instr_mem[count] = val
                count += 1
            else:
                break
        for i in range(count, len(self.main_memory)):
            self.data_mem[i - count] = self.main_memory[i]
        return count

# Obtiene la siguiente instrucción desde memoria de instrucciones.
    def _fetch(self):
        self.IR = self.instr_mem[self.PC]
        self.PC += 1
        self.statusUpdate.emit(f"Fetch → {self.IR}")

# Extrae los operandos desde los registros.
    def _decode(self):
        self.regA = self.regs[self.IR.rs]
        self.regB = self.regs[self.IR.rt]
        self.statusUpdate.emit(f"Decode → A: {self.regA}, B: {self.regB}")

# Realiza la operación ALU correspondiente según el opcode.
    def _execute(self):
        op = self.IR.opcode  # Instrucción actual
        a = self.regA        # Registro A
        b = self.regB        # Registro B
        imm = self.IR.imm    # Valor inmediato de la instrucción
        pc = self.PC         # Guardar al PC

        alu_operations = {
            'ADD': lambda: a + b,
            'SUB': lambda: a - b,
            'MUL': lambda: a * b,
            'AND': lambda: a & b,
            'OR': lambda: a | b,
            'XOR': lambda: a ^ b,
            'SLT': lambda: 1 if a < b else 0,           # Set if Less Than
            'ADDI': lambda: a + imm,
            'SUBI': lambda: a - imm,
            'LOAD': lambda: a + imm,                    # Dirección de carga (offset + base)
            'STORE': lambda: a + imm,                   # Dirección de almacenamiento (offset + base)
            'JUMP': lambda: pc + imm,                   # Salto absoluto (relativo al PC)
            'BEQ': lambda: pc + imm if a == b else pc,  # Branch si A == B
            'BNE': lambda: pc + imm if a != b else pc   # Branch si A != B
        }

        self.result = alu_operations.get(op, lambda: 0)()            # Ejecutar la operación correspondiente al opcode, o 0 por defecto si no se reconoce
        self.statusUpdate.emit(f"Execute → Result: {self.result}")

# Carga o almacena datos según la instrucción.
    def _mem_access(self):
        addr = self.result
        if self.IR.opcode == 'LOAD':
            self.MEM_data = self.data_mem[addr]
        elif self.IR.opcode == 'STORE':
            self.data_mem[addr] = self.regB
        self.statusUpdate.emit(f"Memory → MDR: {self.MEM_data}")

# Escribe los resultados de vuelta en los registros
# o actualiza el PC si es una instrucción de salto o rama.
    def _write_back(self):
        op = self.IR.opcode
        if op in ['ADD', 'SUB', 'MUL', 'AND', 'OR', 'XOR', 'SLT']:
            self.regs[self.IR.rd] = self.result
        elif op == 'LOAD':
            self.regs[self.IR.rt] = self.MEM_data
        elif op in ['ADDI', 'SUBI']:
            self.regs[self.IR.rt] = self.result
        elif op in ['JUMP', 'BEQ', 'BNE']:
            self.PC = self.result
        self.statusUpdate.emit(f"WriteBack → Registers: {self.regs}")

# Ejecuta un ciclo completo del procesador multiciclo, avanzando entre fases
# de instrucción (FETCH → DECODE → EXECUTE → MEMORY → WRITEBACK).
    def Mcycle(self):
        if self.PC >= self.total_instructions:
            return False

        if self.PC != self.prev_PC:
            self.statusUpdate.emit(f"Cycle Start → PC: {self.PC}")
            self.prev_PC = self.PC

        if self.phase == 'FETCH':
            self._fetch()
            self.phase = 'DECODE'
        elif self.phase == 'DECODE':
            self._decode()
            self.phase = 'EXEC'
        elif self.phase == 'EXEC':
            self._execute()
            self.phase = 'MEM' if self.IR.opcode in ['LOAD', 'STORE'] else 'WB'
        elif self.phase == 'MEM':
            self._mem_access()
            self.phase = 'WB'
        elif self.phase == 'WB':
            self._write_back()
            self.phase = 'FETCH'
        return True