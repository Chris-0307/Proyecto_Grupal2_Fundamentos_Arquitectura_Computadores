import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal


class MultiCycleCPU(QThread):
    messageChanged = pyqtSignal(str)

    def __init__(self, cycleTime=1):
        super().__init__()
        self.cycleTime = cycleTime  # Time taken by each cycle in seconds
        self.reset()

    def reset(self):
        self.start_time = time.time()
        self.registers = [0] * 32  # General purpose registers
        self.memory = [0] * 1024  # Single unified memory for both instructions and data
        self.instruction_memory = [None] * 256  # Instruction memory
        combined_memory = Memory().combined_memory
        self.memory[:len(combined_memory)] = combined_memory  # Load combined memory into the CPU memory
        self.data_memory = [0] * 1024  # Data memory
        self.prevPC = 0
        self.PC = 0  # Program counter
        self.IR = None  # Instruction register
        self.A = 0  # Register A
        self.B = 0  # Register B
        self.ALUOut = 0  # ALU output
        self.MDR = 0  # Memory data register
        self.state = 'FETCH'  # Initial FSM state
        self.instruction_count = self.separate_memory()  # Separate memory and get instruction count

    def fetch_instruction(self):
        self.IR = self.instruction_memory[self.PC]
        self.PC += 1
        self.messageChanged.emit(f"Fetched: {self.IR}")

    def decode_instruction(self):
        self.A = self.registers[self.IR.rs]
        self.B = self.registers[self.IR.rt]
        self.messageChanged.emit(f"Decoded: A = {self.A}, B = {self.B}")

    def execute_instruction(self):
        if self.IR.opcode == 'ADD':
            self.ALUOut = self.A + self.B
        elif self.IR.opcode == 'SUB':
            self.ALUOut = self.A - self.B
        elif self.IR.opcode == 'MUL':
            self.ALUOut = self.A * self.B
        elif self.IR.opcode == 'LOAD':
            self.ALUOut = self.A + self.IR.imm
        elif self.IR.opcode == 'STORE':
            self.ALUOut = self.A + self.IR.imm
        elif self.IR.opcode == 'JUMP':
            self.ALUOut = self.PC + self.IR.imm
        elif self.IR.opcode == 'BEQ':
            self.ALUOut = self.PC + self.IR.imm if self.A == self.B else self.PC
        elif self.IR.opcode == 'AND':
            self.ALUOut = self.A & self.B
        elif self.IR.opcode == 'OR':
            self.ALUOut = self.A | self.B
        elif self.IR.opcode == 'XOR':
            self.ALUOut = self.A ^ self.B
        elif self.IR.opcode == 'SLT':
            self.ALUOut = 1 if self.A < self.B else 0
        elif self.IR.opcode == 'ADDI':
            self.ALUOut = self.A + self.IR.imm
        elif self.IR.opcode == 'SUBI':
            self.ALUOut = self.A - self.IR.imm
        elif self.IR.opcode == 'BNE':
            self.ALUOut = self.PC + self.IR.imm if self.A != self.B else self.PC
        self.messageChanged.emit(f"Executed: ALUOut = {self.ALUOut}")

    def memory_access(self):
        if self.IR.opcode == 'LOAD':
            self.MDR = self.data_memory[self.ALUOut]
        elif self.IR.opcode == 'STORE':
            self.data_memory[self.ALUOut] = self.B
        self.messageChanged.emit(f"Memory Access: MDR = {self.MDR}")

    def write_back(self):
        if self.IR.opcode in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLT', 'MUL']:
            self.registers[self.IR.rd] = self.ALUOut
        elif self.IR.opcode == 'LOAD':
            self.registers[self.IR.rt] = self.MDR
        elif self.IR.opcode in ['JUMP', 'BEQ', 'BNE']:
            self.PC = self.ALUOut
        elif self.IR.opcode in ['ADDI', 'SUBI']:
            self.registers[self.IR.rt] = self.ALUOut
        self.messageChanged.emit(f"Write Back: Registers = {self.registers}")

    def run_cycle(self):
        if self.PC - 1 >= self.instruction_count:
            return False
        if self.prevPC != self.PC:
            self.messageChanged.emit(f"Cycle: PC = {self.PC}, Registers = {self.registers}")
            self.messageChanged.emit(f"Executed Instruction: {self.IR}")
            self.prevPC = self.PC
        if self.state == 'FETCH':
            self.fetch_instruction()
            self.state = 'DECODE'
        elif self.state == 'DECODE':
            self.decode_instruction()
            self.state = 'EXECUTE'
        elif self.state == 'EXECUTE':
            self.execute_instruction()
            self.state = 'MEMORY_ACCESS' if self.IR.opcode in ['LOAD', 'STORE'] else 'WRITE_BACK'
        elif self.state == 'MEMORY_ACCESS':
            self.memory_access()
            self.state = 'WRITE_BACK'
        elif self.state == 'WRITE_BACK':
            self.write_back()
            self.state = 'FETCH'
        return True

    def separate_memory(self):
        instruction_count = 0
        for i, entry in enumerate(self.memory):
            if isinstance(entry, Instruction):
                self.instruction_memory[instruction_count] = entry
                instruction_count += 1
            else:
                break
        for j in range(instruction_count, len(self.memory)):
            self.data_memory[j - instruction_count] = self.memory[j]
        return instruction_count

