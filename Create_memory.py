import re
import sys
import os
from dict import line_edit_dict, conditon_dict
import dict
from encoder import Encoder, Encoder_12bit
from decoder import Decoder
from PyQt6 import QtCore, QtGui, QtWidgets 

VALID_COMMAND_REGEX = re.compile(r"(MOV|MVN|LSR|LSL|ASR|ROR|RRX|AND|BIC|ORR|ORN|EOR|ADD|ADC|SUB|SBC|RSB)", re.IGNORECASE)
VALID_COMMAND_REGEX_BIT_OP_SPECIAL = re.compile(r"(AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_ARITHMETIC_ADD_SUB = re.compile(r"(ADD|ADC|SUB|SBC|RSB)", re.IGNORECASE)
VALID_COMMAND_REGEX_BIT_OP = re.compile(r"(AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_TEST = re.compile(r"(CMP|CMN|TST|TEQ)", re.IGNORECASE)
VALID_COMMAND_SINGLE_DATA_TRANFER = re.compile(r"(LDR|STR|LDRB|STRB)", re.IGNORECASE)
VALID_COMMAND_REGEX_MULTI = re.compile(r"(MUL|MLA|MLS|DIV)", re.IGNORECASE)
VALID_COMMAND_BRANCH = re.compile(r"(B|BL|BX)", re.IGNORECASE)
VALID_COMMAND_STACKED = re.compile(r"(POP|PUSH)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE|AL)", re.IGNORECASE)
SHIFT_REGEX = re.compile(r"(LSL|LSR|ASR|ROR|RRX)", re.IGNORECASE)
FLAG_REGEX = re.compile(r"S", re.IGNORECASE)
regex_register = re.compile(r"r\d+$|lr")
regex_const = re.compile(r"#-?\d+$")
regex_const_hex = re.compile(r"^#0x[0-9a-fA-F]+$")

def split_and_filter(line):
    parts = re.split(r',', line)
    if any(part.strip() == '' for part in parts):
        return None
    final_parts = []
    for part in parts:
        sub_parts = part.split()
        final_parts.extend([sub_part for sub_part in sub_parts if sub_part.strip() != ''])
    return final_parts
        
def check_memory(self, line, address, lines, data_labels):
    condition = "al"
    memory = ""
    
    parts = split_and_filter(line)
    # Biểu thức chính quy để kiểm tra định dạng dòng lệnh
    # ^         : bắt đầu dòng
    # \w+       : ít nhất một ký tự từ (word character)
    # \s+       : ít nhất một khoảng trắng
    # r\d+      : "r" tiếp theo là ít nhất một số (rd hoặc rx)
    # |         : hoặc
    # #[\d]+    : "#" tiếp theo là một số (hằng số)
    # $         : kết thúc dòng
    # Đảm bảo có ít nhất ba phần (lệnh và ít nhất hai đối số)
    if parts == None:
         return memory
    if len(parts) < 3:
        return memory

    instruction = parts[0]
    reg = parts[1]
    mem = parts[2:]
    num_memory = ""
    reg_memory = []
    
    if not regex_register.match(reg):
        return memory
    
    if regex_register.match(reg) and reg.lower() == "r13" or reg.lower() == "r15":
        return memory
    
    if len(mem) > 4:
        return memory

    match_instruction = re.search(VALID_COMMAND_REGEX, instruction)
    match_instruction_test = re.search(VALID_COMMAND_REGEX_TEST, instruction)
    match_instruction_single_data_tranfer = re.search(VALID_COMMAND_SINGLE_DATA_TRANFER, instruction)
    match_instruction_multi = re.search(VALID_COMMAND_REGEX_MULTI, instruction)
    if match_instruction:
        instruction_clean = match_instruction.group(0)
        instruction = re.sub(match_instruction.group(0), "", instruction)
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        if match_condition:
            condition = match_condition.group(0)
            instruction = re.sub(condition, "", instruction)
        match_flag = re.search(FLAG_REGEX, instruction)
        flag = "0"
        if match_flag:
            instruction = instruction.lstrip(match_flag.group(0))
            flag = "1"
        if not instruction:
            if SHIFT_REGEX.match(instruction_clean):
                shift = "00000000"
                if len(mem) == 2:
                    if regex_register.match(mem[0]):
                        Rm = mem[0]
                    else:
                        return memory
                    if instruction_clean.lower() == "rrx":
                        shift = f"{0:05b}" + dict.shift_memory_dict.get(instruction_clean) + '0'
                    elif not instruction_clean.lower() == "rrx":
                        if regex_const.match(mem[1]):
                            clean_num = mem[1].lstrip('#')
                            num = int(clean_num)
                            shift = f"{num:05b}" + dict.shift_memory_dict.get(instruction_clean) + '0'
                        elif regex_const_hex.match(mem[1]):
                            clean_num = mem[1].lstrip('#')
                            num = dict.twos_complement_to_signed(clean_num)
                            shift = f"{num:05b}" + dict.shift_memory_dict.get(instruction_clean) + '0'
                        elif regex_register.match(mem[1]):
                            shift = dict.register_memory_dict.get(mem[1]) + '0' + dict.shift_memory_dict.get(instruction_clean) + '1'
                        else:
                            return memory
                else:
                    return memory
                Rd = dict.register_memory_dict.get(reg)    
                Rn = "0000"
                condition_memory = dict.condition_memory_dict.get(condition)
                opcode_memory = "1101"
                Immediate_Operand = "0"
                memory = condition_memory + '00' + Immediate_Operand + opcode_memory + flag + Rn + Rd + shift + dict.register_memory_dict.get(Rm)
            else:
                shift = "00000000"
                if len(mem) == 1 and (VALID_COMMAND_REGEX_BIT_OP_SPECIAL.match(instruction_clean) or VALID_COMMAND_REGEX_ARITHMETIC_ADD_SUB.match(instruction_clean)):
                    mem.append(reg)
                    mem.reverse()
                for i in range(len(mem)):
                    item = mem[i]
                    if regex_const.match(item):
                        clean_num = item.lstrip('#')
                        num = int(clean_num)
                        num_memory = dict.process_binary(num)
                        Immediate_Operand = "1"
                    elif regex_const_hex.match(item):
                        clean_num = item.lstrip('#')
                        num = dict.twos_complement_to_signed(clean_num)
                        num_memory = dict.process_binary(num)
                        Immediate_Operand = "1"
                    elif regex_register.match(item):
                        reg_memory.append(item)
                        Immediate_Operand = "0"
                        if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]) and VALID_COMMAND_REGEX_BIT_OP.match(instruction_clean):
                            if mem[i + 1].lower() == "rrx":
                                shift = f"{0:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                break
                            elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                                if regex_const.match(mem[i + 2]):
                                    clean_num = mem[i + 2].lstrip('#')
                                    num = int(clean_num)
                                    shift = f"{num:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                    break
                                elif regex_register.match(mem[i + 2]):
                                    shift = dict.register_memory_dict.get(mem[i + 2]) + '0' + dict.shift_memory_dict.get(mem[i + 1]) + '1'
                                    break
                            else:
                                return memory
                    else:
                        return memory
                Rd = dict.register_memory_dict.get(reg)    
                Rn = "0000"
                Rm = "0000"  
                if len(reg_memory) == 1:
                    Rn = dict.register_memory_dict.get(reg_memory[0])
                elif len(reg_memory) == 2:
                    Rn = dict.register_memory_dict.get(reg_memory[0])
                    Rm = dict.register_memory_dict.get(reg_memory[1])
                condition_memory = dict.condition_memory_dict.get(condition)
                opcode_memory = dict.DataProcessing_opcode_memory_dict.get(instruction_clean)
                if Immediate_Operand == "0":
                    memory = condition_memory + '00' + Immediate_Operand + opcode_memory + flag + Rn + Rd + shift + Rm
                elif Immediate_Operand == "1":
                    if num_memory:
                        memory = condition_memory + '00' + Immediate_Operand + opcode_memory + flag + Rn + Rd + num_memory
                    else:
                        QtWidgets.QMessageBox.critical(None, "Lỗi", "invalid constant (" + str(num) + ") after fixup")
                        return memory
        else:
            return memory
        return memory
    
    elif match_instruction_test:
        instruction_clean = match_instruction_test.group(0)
        instruction = re.sub(match_instruction_test.group(0), "", instruction)
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        if match_condition:
            condition = match_condition.group(0)
            instruction = re.sub(condition, "", instruction)
        if not instruction:
            shift = "00000000"
            for i in range(len(mem)):
                item = mem[i]
                if regex_const.match(item):
                    clean_num = item.lstrip('#')
                    num = int(clean_num)
                    num_memory = dict.process_binary(num)
                    Immediate_Operand = "1"
                elif regex_const_hex.match(item):
                    clean_num = item.lstrip('#')
                    num = dict.twos_complement_to_signed(clean_num)
                    num_memory = dict.process_binary(num)
                    Immediate_Operand = "1"
                elif regex_register.match(item):
                    reg_memory.append(item)
                    Immediate_Operand = "0"
                    if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]):
                        if mem[i + 1].lower() == "rrx":
                            shift = f"{0:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                            break
                        elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                            if regex_const.match(mem[i + 2]):
                                clean_num = mem[i + 2].lstrip('#')
                                num = int(clean_num)
                                shift = f"{num:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                break
                            elif regex_register.match(mem[i + 2]):
                                shift = dict.register_memory_dict.get(mem[i + 2]) + '0' + dict.shift_memory_dict.get(mem[i + 1]) + '1'
                                break
                        else:
                            return memory
                else:
                    return memory
            Rd = dict.register_memory_dict.get(reg)    
            Rn = "0000"    
            if len(reg_memory) == 1:
                Rm = reg_memory[0]
            elif len(reg_memory) == 2:
                Rn = dict.register_memory_dict.get(reg_memory[0])
                Rm = reg_memory[1]
            condition_memory = dict.condition_memory_dict.get(condition)
            opcode_memory = dict.DataProcessing_opcode_memory_dict.get(instruction_clean)
            if Immediate_Operand == "0":
                memory = condition_memory + '00' + Immediate_Operand + opcode_memory + "1" + Rn + Rd + shift + dict.register_memory_dict.get(Rm)
            elif Immediate_Operand == "1":
                if num_memory:
                    memory = condition_memory + '00' + Immediate_Operand + opcode_memory + "1" + Rn + Rd + num_memory
                else:
                    QtWidgets.QMessageBox.critical(None, "Lỗi", "invalid constant (" + str(num) + ") after fixup")
                    return memory
        else:
            return memory
        return memory
    
    elif match_instruction_single_data_tranfer:
        P = U = B = W = L = "0"
        Immediate_Operand = "0"
        Rn = "0000"
        condition_memory = dict.condition_memory_dict.get(condition)
        shift = "00000000"
        num_memory = "000000000000"
        instruction_clean = match_instruction_single_data_tranfer.group(0)
        instruction = re.sub(match_instruction_single_data_tranfer.group(0), "", instruction)
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        if match_condition:
            condition = match_condition.group(0)
            instruction = re.sub(condition, "", instruction)
        if instruction.lower() == "b":
            instruction_clean = instruction_clean + "b"
        regex_bracket_1 = re.compile(r"\[", re.IGNORECASE)
        regex_bracket_2 = re.compile(r"\]", re.IGNORECASE)
        if len(mem) == 1:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            regex_equal = re.compile(r"\=")
            if bracket_1 and bracket_2:
                mem[0] = mem[0].strip("[]")
                if regex_register.match(mem[0]):
                    reg_memory.append(mem[0])
                    Rn = dict.register_memory_dict.get(reg_memory[0])
            else:
                mapping = {key: value for key, value in zip(lines, address)}
                have_label = re.search(regex_equal, mem[0])
                if have_label and data_labels:
                    label = mem[0].strip('=')
                    Rn = "1111"
                    if label in data_labels:
                        index = data_labels.index(label)
                        hex_str = data_labels[index + 1]
                        num_1 = int(hex_str, 16)
                        num_2_str = mapping.get(line)
                        num_2 = int(num_2_str, 16)
                        num_memory = Encoder_12bit(num_1 - num_2)
                else:
                    return memory
            
            if instruction_clean.lower() == "ldr":
                L = "1"
                B = "0"
            if instruction_clean.lower() == "str":
                L = "0"
                B = "0"
            if instruction_clean.lower() == "ldrb":
                L = "1"
                B = "1"
            if instruction_clean.lower() == "strb":
                L = "0"
                B = "1"
            Rd = dict.register_memory_dict.get(reg)
            Rm = "0000"
            P = U = "1"
            W = "0"
            if Immediate_Operand == "0":
                memory = condition_memory + "01" + Immediate_Operand + P + U + B + W + L + Rn + Rd + num_memory
            elif Immediate_Operand == "1":
                memory = condition_memory + "01" + Immediate_Operand + P + U + B + W + L + Rn + Rd + shift + Rm
                
        if len(mem) == 2:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            if bracket_1 and bracket_2:
                mem[0] = mem[0].strip("[]")
                W = "1"
                P = "0"
                if regex_register.match(mem[0]):
                    reg_memory.append(mem[0])
                    if regex_const.match(mem[1]):
                        Immediate_Operand == "0"
                        clean_num = mem[1].lstrip('#')
                        num = int(clean_num)
                        if num >= 0:
                            U = "1"
                        elif num < 0:
                            U = "0"
                        num_memory = Encoder_12bit(num)
                    elif regex_const_hex.match(mem[1]):
                        Immediate_Operand == "0"
                        clean_num = mem[1].lstrip('#')
                        num = dict.twos_complement_to_signed(clean_num)
                        if num >= 0:
                            U = "1"
                        elif num < 0:
                            U = "0"
                        num_memory = Encoder_12bit(num)
                    elif regex_register.match(mem[1]):
                        Immediate_Operand == "1"
                        U = "1"
                        Rm = dict.register_memory_dict.get(mem[1])
                elif not regex_register.match(mem[0]):
                    return memory
                
            elif bracket_1 and not bracket_2:
                mem[0] = mem[0].strip("[")
                P = "1"
                if regex_register.match(mem[0]):
                    reg_memory.append(mem[0])
                elif not regex_register.match(mem[0]):
                    return memory
                bracket_mem = re.search(regex_bracket_2, mem[1])
                if bracket_mem:
                    mem[1] = mem[1].replace("]", '')
                    exclamation = re.compile(r"\!")
                    exclamation_check = re.search(exclamation, mem[1])
                    if exclamation_check:
                        W = "1"
                        mem[1] = mem[1].strip('!')
                        if regex_const.match(mem[1]):
                            Immediate_Operand == "0"
                            clean_num = mem[1].lstrip('#')
                            num = int(clean_num)
                            if num >= 0:
                                U = "1"
                            elif num < 0:
                                U = "0"
                            num_memory = Encoder_12bit(num)
                        elif regex_const_hex.match(mem[1]):
                            Immediate_Operand == "0"
                            clean_num = mem[1].lstrip('#')
                            num = dict.twos_complement_to_signed(clean_num)
                            if num >= 0:
                                U = "1"
                            elif num < 0:
                                U = "0"
                            num_memory = Encoder_12bit(num)
                        elif regex_register.match(mem[1]):
                            Immediate_Operand == "1"
                            Rm = dict.register_memory_dict.get(mem[1])
                        else:
                            return memory
                    elif not exclamation_check:
                        W = "0"
                        mem[1] = mem[1].strip('!')
                        if regex_const.match(mem[1]):
                            Immediate_Operand == "0"
                            clean_num = mem[1].lstrip('#')
                            num = int(clean_num)
                            if num >= 0:
                                U = "1"
                            elif num < 0:
                                U = "0"
                            num_memory = Encoder_12bit(num)
                        elif regex_const_hex.match(mem[1]):
                            Immediate_Operand == "0"
                            clean_num = mem[1].lstrip('#')
                            num = dict.twos_complement_to_signed(clean_num)
                            if num >= 0:
                                U = "1"
                            elif num < 0:
                                U = "0"
                            num_memory = Encoder_12bit(num)
                        elif regex_register.match(mem[1]):
                            Immediate_Operand == "1"
                            U = "1"
                            Rm = dict.register_memory_dict.get(mem[1])
                        else:
                            return memory
                elif not bracket_mem:
                    return memory
                
            elif not bracket_1:
                return memory
            
            if instruction_clean.lower() == "ldr":
                L = "1"
                B = "0"
            if instruction_clean.lower() == "str":
                L = "0"
                B = "0"
            if instruction_clean.lower() == "ldrb":
                L = "1"
                B = "1"
            if instruction_clean.lower() == "strb":
                L = "0"
                B = "1"
            Rd = dict.register_memory_dict.get(reg)
            Rn = dict.register_memory_dict.get(reg_memory[0])
            if Immediate_Operand == "0":
                if num_memory:
                    memory = condition_memory + "01" + Immediate_Operand + P + U + B + W + L + Rn + Rd + num_memory
                else:
                    QtWidgets.QMessageBox.critical(None, "Lỗi", "invalid constant (" + num + ") after fixup")
                    return memory
            elif Immediate_Operand == "1":
                memory = condition_memory + "01" + Immediate_Operand + P + U + B + W + L + Rn + Rd + shift + Rm
                
        elif len(mem) > 2 and len(mem) < 5:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            if bracket_1 and bracket_2:
                mem[0] = mem[0].strip("[]")
                P = "0"
                reg.append(mem[0])
                if regex_register.match(mem[0]):
                    reg_memory.append(mem[0])
                    for i in range(1, len(mem)):
                        item = mem[i]
                        if regex_register.match(item):
                            Immediate_Operand == "1"
                            Rm = dict.register_memory_dict.get(item)
                            if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]):
                                if mem[i + 1].lower() == "rrx":
                                    shift = f"{0:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                    break
                                elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                                    if regex_const.match(mem[i + 2]):
                                        clean_num = mem[i + 2].lstrip('#')
                                        num = int(clean_num)
                                        shift = f"{num:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                        break
                                    elif regex_const_hex.match(mem[i + 2]):
                                        clean_num = mem[i + 2].lstrip('#')
                                        num = dict.twos_complement_to_signed(clean_num)
                                        shift = f"{num:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                        break    
                                    elif regex_register.match(mem[i + 2]):
                                        shift = dict.register_memory_dict.get(mem[i + 2]) + '0' + dict.shift_memory_dict.get(mem[i + 1]) + '1'
                                        break
                        else:
                            return memory
                elif not regex_register.match(mem[0]):
                    return memory
            
            elif bracket_1 and not bracket_2:
                mem[0] = mem[0].strip("[")
                P = "1"
                if regex_register.match(mem[0]):
                    reg_memory.append(mem[0])
                elif not regex_register.match(mem[0]):
                    return memory
                if len(mem) == 3:
                    exclamation = re.compile(r"\!")
                    exclamation_check = re.search(exclamation, mem[2])
                    if exclamation_check:
                        W = "1"
                        reg.append(mem[0])
                        mem[2] = mem[2].strip("!")
                    search = re.search(regex_bracket_2, mem[2])
                    if search:
                        mem[2] = mem[2].strip("]")
                    else:
                        return memory
                if len(mem) == 4:
                    exclamation = re.compile(r"\!")
                    exclamation_check = re.search(exclamation, mem[3])
                    if exclamation_check:
                        W = "1"
                        reg.append(mem[0])
                        mem[3] = mem[3].strip("!")
                    search = re.search(regex_bracket_2, mem[3])
                    if search:
                        mem[3] = mem[3].strip("]")
                    else:
                        return memory
                for i in range(1, len(mem)):
                    item = mem[i]
                    if regex_register.match(item):
                        Immediate_Operand == "1"
                        Rm = dict.register_memory_dict.get(item)
                        if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]):
                            if mem[i + 1].lower() == "rrx":
                                shift = f"{0:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                break
                            elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                                if regex_const.match(mem[i + 2]):
                                    clean_num = mem[i + 2].lstrip('#')
                                    num = int(clean_num)
                                    shift = f"{num:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                    break
                                elif regex_const_hex.match(mem[i + 2]):
                                    clean_num = mem[i + 2].lstrip('#')
                                    num = dict.twos_complement_to_signed(clean_num)
                                    shift = f"{num:05b}" + dict.shift_memory_dict.get(mem[i + 1]) + '0'
                                    break
                                elif regex_register.match(mem[i + 2]):
                                    shift = dict.register_memory_dict.get(mem[i + 2]) + '0' + dict.shift_memory_dict.get(mem[i + 1]) + '1'
                                    break
                    else:
                        return memory     
            elif not bracket_1:
                return memory
            if instruction_clean.lower() == "ldr":
                L = "1"
                B = "0"
            if instruction_clean.lower() == "str":
                L = "0"
                B = "0"
            if instruction_clean.lower() == "ldrb":
                L = "1"
                B = "1"
            if instruction_clean.lower() == "strb":
                L = "0"
                B = "1"
            U = "1"
            Rd = dict.register_memory_dict.get(reg)
            Rn = dict.register_memory_dict.get(reg_memory[0])
            memory = condition_memory + "01" + Immediate_Operand + P + U + B + W + L + Rn + Rd + shift + Rm  
        elif len(mem) > 4:
            return memory
        return memory
    
    elif match_instruction_multi:
        u = None
        if instruction and instruction[0] == "u":
            u = "0"
            instruction = instruction[1:]
        if instruction and instruction[0] == "s":
            u = "1"
            instruction = instruction[1:]
        instruction_clean = match_instruction_multi.group(0)
        instruction = re.sub(match_instruction_multi.group(0), "", instruction)
        LONG_REGEX = re.compile(r"L", re.IGNORECASE)
        l = None
        long_flag = re.search(LONG_REGEX, instruction)
        if long_flag:
            instruction = instruction.lstrip(long_flag.group(0))
            l = 1
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        if match_condition:
            condition = match_condition.group(0)
            instruction = re.sub(condition, "", instruction)
        match_flag = re.search(FLAG_REGEX, instruction)
        flag = "0"
        if match_flag:
            instruction = instruction.lstrip(match_flag.group(0))
            flag = "1"
        if not instruction:
            if len(mem) == 1:
                mem.append(reg)
                mem.reverse()
            if l == 1 and len(mem) == 3:
                reg_memory.append(mem[0])
                mem = mem[1:]
            for i in range(len(mem)):
                item = mem[i]
                if regex_register.match(item):
                    reg_memory.append(item)
                else:
                    return memory
            reg_memory.reverse()
            condition_memory = dict.condition_memory_dict.get(condition)    
            if u != None and (l == 1 or instruction_clean.lower() == "div"):
                if instruction_clean.lower() == "div":
                    A = "0"
                    Rd = dict.register_memory_dict.get(reg)    
                    Rn = "0000"
                    Rm = dict.register_memory_dict.get(reg_memory[0])
                    Rs = dict.register_memory_dict.get(reg_memory[1])
                    memory = condition_memory + "00001" + u + A + flag + Rd + Rn + Rs + "1001" + Rm
                else:
                    RdLo = dict.register_memory_dict.get(reg)  
                    RdHi = dict.register_memory_dict.get(reg_memory[0])
                    Rm = dict.register_memory_dict.get(reg_memory[1])
                    Rs = dict.register_memory_dict.get(reg_memory[2])
                    if instruction_clean.lower() == "mla" or instruction_clean.lower() == "mls":
                        A = "1"
                    else:
                        A = "0"
                    memory = condition_memory + "00001" + u + A + flag + RdLo + RdHi + Rs + "1001" + Rm
            else:
                Rd = dict.register_memory_dict.get(reg)    
                Rn = "0000"
                if instruction_clean.lower() == "mla" or instruction_clean.lower() == "mls":
                    A = "1"
                    Rm = dict.register_memory_dict.get(reg_memory[0])
                    Rs = dict.register_memory_dict.get(reg_memory[1])
                    Rn = dict.register_memory_dict.get(reg_memory[2])
                else:
                    A = "0"
                    Rm = dict.register_memory_dict.get(reg_memory[0])
                    Rs = dict.register_memory_dict.get(reg_memory[1])
                memory = condition_memory + "000000" + A + flag + Rd + Rn + Rs + "1001" + Rm
        else:
            return memory
        return memory
    else:
        return memory
    
def memory_branch(self, line, lines, address, labels):
    condition = "al"
    memory = ""
    parts = split_and_filter(line)
    if parts == None or (not len(parts) == 2):
        return memory
    instruction = parts[0]
    match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
    if match_condition:
        condition = match_condition.group(0)
        instruction = re.sub(condition, "", instruction)
    if VALID_COMMAND_BRANCH.match(instruction):
        condition_memory = dict.condition_memory_dict.get(condition)
        if instruction.lower() == "bx":
            if regex_register.match(parts[1]):
                Rn = dict.register_memory_dict.get(parts[1])
            else:
                return memory
            memory = condition_memory + "0001" + "0010" + "1111" + "1111" + "1111" + "0001" + Rn
        else:
            offset = get_memory_offset(line, parts[1], lines, address, labels)  
            if instruction.lower() == "b":
                L = "0"
                memory = condition_memory + "101" + L + offset
            elif instruction.lower() == "bl":
                L = "1"
                memory = condition_memory + "101" + L + offset
        return memory
    else:
        return memory
    
def get_memory_offset(current_line, current_label, lines, address, labels):
    mapping = {key: value for key, value in zip(lines, address)}
    if current_label in labels:
        target = mapping.get(labels[current_label][0])
    current = mapping.get(current_line)
    if current != None and target != None:
        current_int = dict.twos_complement_to_signed(current)
        target_int = dict.twos_complement_to_signed(target)
        result = int((target_int - current_int - 8) / 4)
        result_str = Encoder_24bit(result)
    return result_str

def Encoder_24bit(number):
    if number >= 0:
        binary_str = bin(number)[2:].zfill(24)
    else:
        binary_str = bin((1 << 24) + number)[2:].zfill(24)
    if len(binary_str) > 24:
        binary_str = binary_str[-24:]
    return binary_str

def memory_stacked(self, line, lines, address, labels):
    condition = "al"
    memory = ""
    parts = split_and_filter(line)
    instruction = parts[0]
    mems = parts[1:]
    match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
    if match_condition:
        condition = match_condition.group(0)
        instruction = re.sub(condition, "", instruction)
    if VALID_COMMAND_STACKED.match(instruction):
        condition_memory = dict.condition_memory_dict.get(condition)
        registers = {
                        "r0": "0", "r1": "0", "r2": "0", "r3": "0",
                        "r4": "0", "r5": "0", "r6": "0", "r7": "0",
                        "r8": "0", "r9": "0", "r10": "0", "r11": "0",
                        "r12": "0", "sp": "0", "lr": "0", "pc": "0"
                    }
        pop = "0100010111101"
        push = "0100100101101"
        if instruction.lower() == "push":
            if mems[0].startswith("{") and mems[-1].endswith("}"):
                mems[0] = mems[0].strip('{')
                mems[-1] = mems[-1].strip('}')
                for mem in mems:
                    if regex_register.match(mem):
                        if mem in registers:
                            registers[mem] = "1"
                    else:
                        return memory
            else:
                return None, None, None, None
            memory = condition_memory + push + (registers["pc"] + registers["lr"] + registers["sp"]
                                            + registers["r12"] + registers["r11"] + registers["r10"]
                                            + registers["r9"] + registers["r8"] + registers["r7"]
                                            + registers["r6"] + registers["r5"] + registers["r4"]
                                            + registers["r3"] + registers["r2"] + registers["r1"] + registers["r0"])
        if instruction.lower() == "pop":
            if mems[0].startswith("{") and mems[-1].endswith("}"):
                mems[0] = mems[0].strip('{')
                mems[-1] = mems[-1].strip('}')
                for mem in mems:
                    if regex_register.match(mem):
                        if mem in registers:
                            registers[mem] = "1"
                    else:
                        return memory
            else:
                return None, None, None, None
            memory = condition_memory + pop + (registers["pc"] + registers["lr"] + registers["sp"]
                                            + registers["r12"] + registers["r11"] + registers["r10"]
                                            + registers["r9"] + registers["r8"] + registers["r7"]
                                            + registers["r6"] + registers["r5"] + registers["r4"]
                                            + registers["r3"] + registers["r2"] + registers["r1"] + registers["r0"])
        return memory
    else:
        return memory