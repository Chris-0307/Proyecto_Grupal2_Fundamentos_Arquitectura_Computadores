# instruction.py
class Instruction:
    def __init__(self, opcode, rs=0, rt=0, rd=0, imm=0):
        self.opcode = opcode
        self.rs = rs
        self.rt = rt
        self.rd = rd
        self.imm = imm

    def __repr__(self):
        return f"Instruction(opcode='{self.opcode}', rs={self.rs}, rt={self.rt}, rd={self.rd}, imm={self.imm})"
