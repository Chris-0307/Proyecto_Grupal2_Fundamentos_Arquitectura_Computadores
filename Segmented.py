import time
from memory import *
from PyQt5.QtCore import QThread, pyqtSignal

class SegmentedProcessor(QThread):
    statusSignal = pyqtSignal(str)

    def __init__(self, delay=1):
        super().__init__()
        self.delay = delay
        self.initialize()

# Inicializa todos los registros, memoria e instrucciones
    def initialize(self):
        self.start_time = time.time()
        self.regs = [0] * 32
        self.ram = [0] * 1024
        self.instr_mem = [None] * 256
        combined = Memory().combined_memory
        self.ram[:len(combined)] = combined
        self.inactive_cycles = 0
        self.data_mem = [0] * 1024
        self.pc = 0
        self.stages = {
            "IF_ID": {},        # Instruction Fetch - Instruction Decode
            "ID_EX": {},        # Instruction Decode - Execute
            "EX_MEM": {},       # Instruction Execute - Memory
            "MEM_WB": {}        # Memory - WriteBack
        }
        self.total_instructions = self._load_mem()
        self.total_cycles = 0

# Separa instrucciones y datos en memoria; retorna el total de instrucciones cargadas
    def _load_mem(self):
        count = 0
        for i, val in enumerate(self.ram):
            if isinstance(val, Instruction):
                self.instr_mem[count] = val
                count += 1
            else:
                break
        for i in range(count, len(self.ram)):
            self.data_mem[i - count] = self.ram[i]
        return count

# Obtiene la siguiente instrucción y actualiza el PC
    def stage_fetch(self):
        if self.pc < self.total_instructions:
            self.stages["IF_ID"]["IR"] = self.instr_mem[self.pc]
            self.stages["IF_ID"]["NPC"] = self.pc + 1
            self.pc += 1
            self.statusSignal.emit(f"Fetch: {self.stages['IF_ID']['IR']}")
        else:
            self.stages["IF_ID"]["IR"] = None

# Decodifica la instrucción y lee los operandos
    def stage_decode(self):
        ir = self.stages["IF_ID"].get("IR")
        if ir:
            self.stages["ID_EX"] = {"A": self.regs[ir.rs],"B": self.regs[ir.rt],"IR": ir}
            self.statusSignal.emit(f"Decode: A = {self.stages['ID_EX']['A']}, B = {self.stages['ID_EX']['B']}")
        else:
            self.stages["ID_EX"]["IR"] = None

# Realiza la operación ALU correspondiente
    def stage_execute(self):
        ir = self.stages["ID_EX"].get("IR")
        if not ir:
            self.stages["EX_MEM"]["IR"] = None
            return

        a, b, imm = self.stages["ID_EX"]["A"], self.stages["ID_EX"]["B"], ir.imm
        result = 0

        match ir.opcode:
            case'SUB': result = a - b
            case'MUL': result = a * b
            case'SUBI': result = a - imm
            case 'LW' | 'SW': result = a + imm
            case 'JUMP':
                result = self.pc + imm + 1
                self.pc = result
                self.stages["IF_ID"] = {"IR": None}
                self.stages["ID_EX"] = {"IR": None}
                self.statusSignal.emit(f"Jump taken: PC = {self.pc}, flushed IF/ID and ID/EX")
            case 'BEQ':
                if a == b:
                    result = self.pc + imm - 1
                    self.pc = result
                    self.stages["IF_ID"] = {"IR": None}
                    self.stages["ID_EX"] = {"IR": None}
            case 'BNE':
                if a != b:
                    result = self.pc + imm + 1
                    self.pc = result
                    self.stages["IF_ID"] = {"IR": None}
                    self.stages["ID_EX"] = {"IR": None}
                    self.statusSignal.emit(f"Branch taken (BNE): PC = {self.pc}, flushed IF/ID and ID/EX")
                else:
                    result = self.pc
            case 'AND': result = a & b
            case 'OR': result = a | b
            case 'XOR': result = a ^ b
            case 'SLT': result = 1 if a < b else 0
            case 'ADDI': result = a + imm
            case 'ADD': result = a + b


        self.stages["EX_MEM"] = {"ALU": result,"IR": ir}
        self.statusSignal.emit(f"Execute: ALU = {result}")

# Accede a memoria de datos si corresponde (LOAD o STORE)
    def stage_memory(self):
        ir = self.stages["EX_MEM"].get("IR")
        if ir:
            address = self.stages["EX_MEM"]["ALU"]
            self.stages["MEM_WB"] = {"IR": ir, "ALU": address}

            if ir.opcode == 'LW':
                self.stages["MEM_WB"]["MDR"] = self.data_mem[address]
            elif ir.opcode == 'SW':
                self.data_mem[address] = self.stages["ID_EX"]["B"]


            mdr = self.stages["MEM_WB"].get("MDR", "N/A")
            self.statusSignal.emit(f"Memory: MDR = {mdr}")
        else:
            self.stages["MEM_WB"]["IR"] = None

# Escribe resultados de vuelta en registros
    def stage_writeback(self):
        ir = self.stages["MEM_WB"].get("IR")
        if ir:
            alu = self.stages["MEM_WB"].get("ALU")
            mdr = self.stages["MEM_WB"].get("MDR")

            if ir.opcode in ['ADD', 'SUB', 'MUL', 'AND', 'OR', 'XOR', 'SLT']:
                self.regs[ir.rd] = alu
            elif ir.opcode == 'LW':
                self.regs[ir.rt] = mdr
            elif ir.opcode in ['JUMP', 'BEQ', 'BNE']:
                self.pc = alu
            elif ir.opcode in ['ADDI', 'SUBI']:
                self.regs[ir.rt] = alu

            self.statusSignal.emit(f"WriteBack: Registers = {self.regs}")

# Avanza el pipeline ejecutando cada etapa en orden inverso
    def advance_pipeline(self):
        self.stage_writeback()
        self.stage_memory()
        self.stage_execute()

        if self.data_conflict():
            self.insert_stall()

        else:
            self.stage_decode()
            self.stage_fetch()

        self.total_cycles += 1

        active = any(stage.get("IR") for stage in self.stages.values())

        if not active and self.pc >= self.total_instructions:
            self.inactive_cycles += 1
        else:
            self.inactive_cycles = 0

        return self.inactive_cycles < 2  # Detener tras 2 ciclos completamente inactivos

# Verifica si hay conflicto de datos entre instrucciones en EX y MEM
    def data_conflict(self):
        decode_ir = self.stages["IF_ID"].get("IR")
        if not decode_ir:
            return False

        src_regs = {decode_ir.rs, decode_ir.rt} - {0}

        # Instrucciones en etapas que aún no escriben
        for stage_name in ["ID_EX", "EX_MEM", "MEM_WB"]:
            ir = self.stages[stage_name].get("IR")
            if not ir:
                continue

            # Determinar el destino de esa instrucción
            dest = None
            if ir.opcode in ['ADD', 'SUB', 'MUL', 'AND', 'OR', 'XOR', 'SLT']:
                dest = ir.rd
            elif ir.opcode in ['ADDI', 'SUBI', 'LW']:
                dest = ir.rt
            # STORE y ramas no escriben en registro

            if dest and dest in src_regs:
                print(f"⛔ DATA HAZARD: {decode_ir.opcode} necesita R{dest} aún no escrito")
                return True  # ¡hazard detectado!

        return False

    # Inserta un ciclo de burbuja (stall) debido a dependencia de datos
    def insert_stall(self):
        ir = self.stages["IF_ID"].get("IR")
        msg = f"⚠ STALL: Instrucción {ir} necesita datos aún no escritos."
        self.stages["ID_EX"] = {"IR": None}
        self.statusSignal.emit(msg)