class Instruction:
    def __init__(self, opcode, rs=0, rt=0, rd=0, imm=0):
        self.opcode = opcode
        self.rs = rs
        self.rt = rt
        self.rd = rd
        self.imm = imm

    def __repr__(self):
        return f"Instruction(opcode='{self.opcode}', rs={self.rs}, rt={self.rt}, rd={self.rd}, imm={self.imm})"

class Memory:
    def __init__(self):
        self.combined_memory = [
            # Instructions for loading matrix A and B elements into registers
            Instruction('LOAD', rs=0, rt=1, imm=0),  # Load a11 to R1
            Instruction('LOAD', rs=0, rt=2, imm=1),  # Load a12 to R2
            Instruction('LOAD', rs=0, rt=3, imm=2),  # Load a21 to R3
            Instruction('LOAD', rs=0, rt=4, imm=3),  # Load a22 to R4
            Instruction('LOAD', rs=0, rt=5, imm=4),  # Load b11 to R5
            Instruction('LOAD', rs=0, rt=6, imm=5),  # Load b12 to R6
            Instruction('LOAD', rs=0, rt=7, imm=6),  # Load b21 to R7
            Instruction('LOAD', rs=0, rt=8, imm=7),  # Load b22 to R8

            # Instructions for matrix multiplication
            # C[0][0] = a11*b11 + a12*b21
            Instruction('MUL', rs=1, rt=5, rd=9),  # R9 = R1 * R5 (a11 * b11)
            Instruction('MUL', rs=2, rt=7, rd=10), # R10 = R2 * R7 (a12 * b21)
            Instruction('ADD', rs=9, rt=10, rd=11),# R11 = R9 + R10 (C[0][0])

            # C[0][1] = a11*b12 + a12*b22
            Instruction('MUL', rs=1, rt=6, rd=12), # R12 = R1 * R6 (a11 * b12)
            Instruction('MUL', rs=2, rt=8, rd=13), # R13 = R2 * R8 (a12 * b22)
            Instruction('ADD', rs=12, rt=13, rd=14),# R14 = R12 + R13 (C[0][1])

            # C[1][0] = a21*b11 + a22*b21
            Instruction('MUL', rs=3, rt=5, rd=15), # R15 = R3 * R5 (a21 * b11)
            Instruction('MUL', rs=4, rt=7, rd=16), # R16 = R4 * R7 (a22 * b21)
            Instruction('ADD', rs=15, rt=16, rd=17),# R17 = R15 + R16 (C[1][0])

            # C[1][1] = a21*b12 + a22*b22
            Instruction('MUL', rs=3, rt=6, rd=18), # R18 = R3 * R6 (a21 * b12)
            Instruction('MUL', rs=4, rt=8, rd=19), # R19 = R4 * R8 (a22 * b22)
            Instruction('ADD', rs=18, rt=19, rd=20),# R20 = R18 + R19 (C[1][1])

            # Store results back to memory
            Instruction('STORE', rs=0, rt=11, imm=8), # Store C[0][0] in memory[8]
            Instruction('STORE', rs=0, rt=14, imm=9), # Store C[0][1] in memory[9]
            Instruction('STORE', rs=0, rt=17, imm=10),# Store C[1][0] in memory[10]
            Instruction('STORE', rs=0, rt=20, imm=11),# Store C[1][1] in memory[11]

            # Data for matrices A and B
            1, 2, # Matrix A
            3, 4, # Matrix A
            5, 6, # Matrix B
            7, 8  # Matrix B
        ]

# Example of how to use the Memory class
memory = Memory()
for instruction in memory.combined_memory:
    print(instruction)