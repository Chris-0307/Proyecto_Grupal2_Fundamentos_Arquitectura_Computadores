import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal

class PipelineCPU(QThread):
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
        self.PC = 0  # Program counter
        self.pipeline_registers = {
            "IF/ID": {},
            "ID/EX": {},
            "EX/MEM": {},
            "MEM/WB": {}
        }
        self.instruction_count = self.separate_memory()  # Separate memory and get instruction count

    def fetch(self):
        if self.PC < self.instruction_count:
            self.pipeline_registers["IF/ID"]["IR"] = self.instruction_memory[self.PC]
            self.pipeline_registers["IF/ID"]["NPC"] = self.PC + 1
            self.PC += 1
            self.messageChanged.emit(f"Fetched: {self.pipeline_registers['IF/ID']['IR']}")
        else:
            self.pipeline_registers["IF/ID"]["IR"] = None

    def decode(self):
        ir = self.pipeline_registers["IF/ID"].get("IR")
        if ir:
            self.pipeline_registers["ID/EX"]["A"] = self.registers[ir.rs]
            self.pipeline_registers["ID/EX"]["B"] = self.registers[ir.rt]
            self.pipeline_registers["ID/EX"]["IR"] = ir
            self.messageChanged.emit(f"Decoded: A = {self.pipeline_registers['ID/EX']['A']}, B = {self.pipeline_registers['ID/EX']['B']}")
        else:
            self.pipeline_registers["ID/EX"]["IR"] = None

    def execute(self):
        ir = self.pipeline_registers["ID/EX"].get("IR")
        if ir:
            A = self.pipeline_registers["ID/EX"]["A"]
            B = self.pipeline_registers["ID/EX"]["B"]
            if ir.opcode == 'ADD':
                ALUOut = A + B
            elif ir.opcode == 'SUB':
                ALUOut = A - B
            elif ir.opcode == 'MUL':
                ALUOut = A * B
            elif ir.opcode == 'LOAD':
                ALUOut = A + ir.imm
            elif ir.opcode == 'STORE':
                ALUOut = A + ir.imm
            elif ir.opcode == 'JUMP':
                ALUOut = self.PC + ir.imm
            elif ir.opcode == 'BEQ':
                ALUOut = self.PC + ir.imm if A == B else self.PC
            elif ir.opcode == 'AND':
                ALUOut = A & B
            elif ir.opcode == 'OR':
                ALUOut = A | B
            elif ir.opcode == 'XOR':
                ALUOut = A ^ B
            elif ir.opcode == 'SLT':
                ALUOut = 1 if A < B else 0
            elif ir.opcode == 'ADDI':
                ALUOut = A + ir.imm
            elif ir.opcode == 'SUBI':
                ALUOut = A - ir.imm
            elif ir.opcode == 'BNE':
                ALUOut = self.PC + ir.imm if A != B else self.PC
            self.pipeline_registers["EX/MEM"]["ALUOut"] = ALUOut
            self.pipeline_registers["EX/MEM"]["IR"] = ir
            self.messageChanged.emit(f"Executed: ALUOut = {ALUOut}")
        else:
            self.pipeline_registers["EX/MEM"]["IR"] = None

    def memory_access(self):
        ir = self.pipeline_registers["EX/MEM"].get("IR")
        if ir:
            ALUOut = self.pipeline_registers["EX/MEM"]["ALUOut"]
            if ir.opcode == 'LOAD':
                MDR = self.data_memory[ALUOut]
                self.pipeline_registers["MEM/WB"]["MDR"] = MDR
            elif ir.opcode == 'STORE':
                self.data_memory[ALUOut] = self.pipeline_registers["ID/EX"]["B"]
            self.pipeline_registers["MEM/WB"]["ALUOut"] = ALUOut
            self.pipeline_registers["MEM/WB"]["IR"] = ir
            self.messageChanged.emit(f"Memory Access: MDR = {self.pipeline_registers.get('MEM/WB', {}).get('MDR', 'N/A')}")
        else:
            self.pipeline_registers["MEM/WB"]["IR"] = None

    def write_back(self):
        ir = self.pipeline_registers["MEM/WB"].get("IR")
        if ir:
            if ir.opcode in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLT', 'MUL']:
                self.registers[ir.rd] = self.pipeline_registers["MEM/WB"]["ALUOut"]
            elif ir.opcode == 'LOAD':
                self.registers[ir.rt] = self.pipeline_registers["MEM/WB"]["MDR"]
            elif ir.opcode in ['JUMP', 'BEQ', 'BNE']:
                self.PC = self.pipeline_registers["MEM/WB"]["ALUOut"]
            elif ir.opcode in ['ADDI', 'SUBI']:
                self.registers[ir.rt] = self.pipeline_registers["MEM/WB"]["ALUOut"]
            self.messageChanged.emit(f"Write Back: Registers = {self.registers}")

    def run_cycle(self):
        # Run pipeline stages in reverse order to simulate parallel execution
        self.write_back()
        self.memory_access()
        self.execute()
        self.decode()
        self.fetch()

        # Check for stalls
        if self.detect_hazard():
            self.stall_pipeline()

        # Check for end of program
        if self.PC >= self.instruction_count and not any(self.pipeline_registers.values()):
            return False
        return True

    def detect_hazard(self):
        ir_ex = self.pipeline_registers["ID/EX"].get("IR")
        ir_mem = self.pipeline_registers["EX/MEM"].get("IR")
        if ir_ex and ir_mem:
            if ir_ex.rs == ir_mem.rd or ir_ex.rt == ir_mem.rd:
                return True
        return False

    def stall_pipeline(self):
        self.pipeline_registers["IF/ID"] = {"IR": None, "NPC": None}
        self.messageChanged.emit("Pipeline stalled due to data hazard")

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
