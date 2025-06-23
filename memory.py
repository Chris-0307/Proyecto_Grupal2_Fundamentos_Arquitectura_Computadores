from instruction import Instruction
from riscv_parser import parse_riscv_code

class Memory:
    def __init__(self):
        instructions = parse_riscv_code('program.txt')
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        self.combined_memory = instructions + data
