import re
import sys
from dict import line_edit_dict, conditon_dict
import dict
from encoder import Encoder
from decoder import Decoder

VALID_COMMAND_REGEX = re.compile(r"(MOV|MVN|LSR|LSL|ASR|ROR|RRX|AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_BIT_OP = re.compile(r"(AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_TEST = re.compile(r"(CMP|CMN|TST|TEQ)", re.IGNORECASE)
VALID_COMMAND_SINGLE_DATA_TRANFER = re.compile(r"(LDR|STR)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE|AL)", re.IGNORECASE)
SHIFT_REGEX = re.compile(r"(LSL|LSR|ASR|ROR|RRX)", re.IGNORECASE)
FLAG_REGEX = re.compile(r"S", re.IGNORECASE)

def split_and_filter(line):
    parts = re.split(r',', line)
    if any(part.strip() == '' for part in parts):
        return None
    final_parts = []
    for part in parts:
        sub_parts = part.split()
        final_parts.extend([sub_part for sub_part in sub_parts if sub_part.strip() != ''])
    return final_parts
        
def check_memory(self, line):
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
    
    regex_register = re.compile(r"r\d+$")
    regex_const = re.compile(r"#-?\d+$")
    
    if not regex_register.match(reg):
        return memory
    
    if regex_register.match(reg) and reg.lower() == "r13" or reg.lower() == "r15":
        return memory
    
    if len(mem) > 4:
        return memory

    match_instruction = re.search(VALID_COMMAND_REGEX, instruction)
    match_instruction_test = re.search(VALID_COMMAND_REGEX_TEST, instruction)
    match_instruction_single_data_tranfer = re.search(VALID_COMMAND_SINGLE_DATA_TRANFER, instruction)
    if match_instruction:
        instruction_clean = match_instruction.group(0)
        instruction = re.sub(match_instruction.group(0), "", instruction)
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        
        if match_condition:
            condition = match_condition.group(0)
            instruction = re.sub(condition, "", instruction)

        match_flag = re.search(FLAG_REGEX, instruction)
        if match_flag:
            instruction = instruction.lstrip(match_flag.group(0))
            if not instruction:
                shift = "00000000"
                for i in range(len(mem)):
                    item = mem[i]
                    if regex_const.match(item):
                        clean_num = item.lstrip('#')
                        num = int(clean_num)
                        num_memory = dict.process_binary(num)
                        Immediate_Operand = "1"
                    elif regex_register.match(item):
                        reg_memory.append(item)
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
                        Immediate_Operand = "0"
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
                    memory = condition_memory + '00' + Immediate_Operand + opcode_memory + "1" + Rn + Rd + num_memory
            else:
                return memory
        else:
            if not instruction:
                shift = "00000000"
                for i in range(len(mem)):
                    item = mem[i]
                    if regex_const.match(item):
                        clean_num = item.lstrip('#')
                        num = int(clean_num)
                        num_memory = dict.process_binary(num)
                        Immediate_Operand = "1"
                    elif regex_register.match(item):
                        reg_memory.append(item)
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
                        Immediate_Operand = "0"
                    else:
                        return memory
                    
                if num_memory == None:
                    return memory
                    
                Rd = dict.register_memory_dict.get(reg)    
                Rn = "0000"
                Rm = "0000"
                if len(reg_memory) == 1:
                    Rm = reg_memory[0]
                elif len(reg_memory) == 2:
                    Rn = dict.register_memory_dict.get(reg_memory[0])
                    Rm = reg_memory[1]
                condition_memory = dict.condition_memory_dict.get(condition)
                opcode_memory = dict.DataProcessing_opcode_memory_dict.get(instruction_clean)
                if Immediate_Operand == "0":
                    memory = condition_memory + '00' + Immediate_Operand + opcode_memory + "0" + Rn + Rd + shift + dict.register_memory_dict.get(Rm)
                elif Immediate_Operand == "1":
                    memory = condition_memory + '00' + Immediate_Operand + opcode_memory + "0" + Rn + Rd + num_memory
            else:
                return memory
        return memory
    elif match_instruction_test:
        instruction_clean = match_instruction_test.group(0)
        instruction = re.sub(match_instruction_test.group(0), "", instruction)
        if not instruction:
            shift = "00000000"
            for i in range(len(mem)):
                item = mem[i]
                if regex_const.match(item):
                    clean_num = item.lstrip('#')
                    num = int(clean_num)
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
            
            if num_memory == None:
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
                memory = condition_memory + '00' + Immediate_Operand + opcode_memory + "1" + Rn + Rd + num_memory
        else:
            return memory
            
        return memory
    else:
        return memory