from instruction import Instruction


def parse_riscv_code(filename):
    instructions = []
    with open(filename, 'r') as file:
        for line in file:
            # Eliminar comentarios y espacios
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '#' in line:
                line = line.split('#')[0].strip()

            parts = line.replace(',', '').split()
            if len(parts) == 0:
                continue

            opcode = parts[0].upper()

            if opcode == 'LW':
                rt = int(parts[1][1:])  # x1 -> 1
                offset, base = parts[2].split('(')
                imm = int(offset)
                rs = int(base.strip('x)'))
                instructions.append(Instruction('LOAD', rs=rs, rt=rt, imm=imm))

            elif opcode == 'SW':
                rt = int(parts[1][1:])
                offset, base = parts[2].split('(')
                imm = int(offset)
                rs = int(base.strip('x)'))
                instructions.append(Instruction('STORE', rs=rs, rt=rt, imm=imm))

            elif opcode == 'ADD':
                rd = int(parts[1][1:])
                rs = int(parts[2][1:])
                rt = int(parts[3][1:])
                instructions.append(Instruction('ADD', rs=rs, rt=rt, rd=rd))

            elif opcode == 'SUB':
                rd = int(parts[1][1:])
                rs = int(parts[2][1:])
                rt = int(parts[3][1:])
                instructions.append(Instruction('SUB', rs=rs, rt=rt, rd=rd))

            elif opcode == 'MUL':
                rd = int(parts[1][1:])
                rs = int(parts[2][1:])
                rt = int(parts[3][1:])
                instructions.append(Instruction('MUL', rs=rs, rt=rt, rd=rd))

            elif opcode == 'ADDI':
                rt = int(parts[1][1:])
                rs = int(parts[2][1:])
                imm = int(parts[3])
                instructions.append(Instruction('ADDI', rs=rs, rt=rt, imm=imm))

            elif opcode == 'SUBI':
                rt = int(parts[1][1:])
                rs = int(parts[2][1:])
                imm = int(parts[3])
                instructions.append(Instruction('SUBI', rs=rs, rt=rt, imm=imm))

            elif opcode == 'BEQ':
                rs = int(parts[1][1:])
                rt = int(parts[2][1:])
                imm = int(parts[3])
                instructions.append(Instruction('BEQ', rs=rs, rt=rt, imm=imm))

            elif opcode == 'BNE':
                rs = int(parts[1][1:])
                rt = int(parts[2][1:])
                imm = int(parts[3])
                instructions.append(Instruction('BNE', rs=rs, rt=rt, imm=imm))

            elif opcode == 'JUMP':
                imm = int(parts[1])
                instructions.append(Instruction('JUMP', imm=imm))

            elif opcode == 'AND':
                rd = int(parts[1][1:])
                rs = int(parts[2][1:])
                rt = int(parts[3][1:])
                instructions.append(Instruction('AND', rs=rs, rt=rt, rd=rd))

            elif opcode == 'OR':
                rd = int(parts[1][1:])
                rs = int(parts[2][1:])
                rt = int(parts[3][1:])
                instructions.append(Instruction('OR', rs=rs, rt=rt, rd=rd))

            elif opcode == 'XOR':
                rd = int(parts[1][1:])
                rs = int(parts[2][1:])
                rt = int(parts[3][1:])
                instructions.append(Instruction('XOR', rs=rs, rt=rt, rd=rd))

            elif opcode == 'SLT':
                rd = int(parts[1][1:])
                rs = int(parts[2][1:])
                rt = int(parts[3][1:])
                instructions.append(Instruction('SLT', rs=rs, rt=rt, rd=rd))

            else:
                print(f"Instrucción no reconocida: {opcode}")

    return instructions
