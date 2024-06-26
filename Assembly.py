from PyQt6 import QtCore, QtGui, QtWidgets
import re
import sys
from dict import line_edit_dict, conditon_dict
import dict
import GiaoDien
import ctypes
from encoder import Encoder
from decoder import Decoder

VALID_COMMAND_REGEX = re.compile(r"(MOV|MVN|LSR|LSL|ASR|ROR|RRX|AND|BIC|ORR|EOR|ADD|ADC|SUB|SBC|RSB|RSC)", re.IGNORECASE)
VALID_COMMAND_REGEX_BIT_OP = re.compile(r"(MOV|MVN|AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_TEST = re.compile(r"(CMP|CMN|TST|TEQ)", re.IGNORECASE)
VALID_COMMAND_REGEX_ARITHMETIC_ADD_SUB = re.compile(r"(ADD|ADC|SUB|SBC|RSB)", re.IGNORECASE)
VALID_COMMAND_REGEX_MULTI = re.compile(r"(MUL|MLA|MLS|DIV)", re.IGNORECASE)
VALID_COMMAND_SINGLE_DATA_TRANFER = re.compile(r"(LDR|STR)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE|AL)", re.IGNORECASE)
SHIFT_REGEX = re.compile(r"(LSL|LSR|ASR|ROR|RRX)", re.IGNORECASE)
FLAG_REGEX = re.compile(r"S", re.IGNORECASE)
COLON_REGEX = re.compile(r"\:")

def split_and_filter(line):
    parts = re.split(r',', line)
    if any(part.strip() == '' for part in parts):
        return None
    final_parts = []
    for part in parts:
        sub_parts = part.split()
        final_parts.extend([sub_part for sub_part in sub_parts if sub_part.strip() != ''])
    return final_parts
        
def check_assembly_line(self, line, address, memory, data_labels, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte):
    reg = []
    c = True
    flag_N = flag_Z = flag_C = flag_V = "0"
    flag_T = None
    condition = "al"
    
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
         return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
    if len(parts) < 3:
        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T

    instruction = parts[0]
    reg.append(parts[1])
    mem = parts[2:]
    arguments = []
    
    regex_register = re.compile(r"r\d+$|lr")
    regex_const = re.compile(r"#-?\d+$")
    
    if not regex_register.match(reg[0]):
        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    if regex_register.match(reg[0]) and reg[0].lower() == "sp" or reg[0].lower() == "pc":
        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    if len(mem) > 4:
        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T

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
            c = dict.check_condition(condition)
            instruction = re.sub(condition, "", instruction)
        elif not match_condition:
            c = dict.check_condition(condition)
            
        match_flag = re.search(FLAG_REGEX, instruction)
        flag = None
        if match_flag:
            instruction = instruction.lstrip(match_flag.group(0))
            flag = 1
        if not instruction:
            temporary = []
            for i in range(len(mem)):
                item = mem[i]
                if regex_const.match(item):
                    clean_num = item.lstrip('#')
                    num = int(clean_num)
                    num_string = Encoder(num)
                    temporary.append(num_string)
                elif regex_register.match(item):
                    line_edit = line_edit_dict.get(item)
                    binary_str = line_edit.text()
                    hex_int = ctypes.c_int32(int(binary_str, 16)).value
                    binary_str = Encoder(hex_int)
                    if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]) and VALID_COMMAND_REGEX_BIT_OP.match(instruction_clean):
                        t = []
                        if mem[i + 1].lower() == "rrx":
                            num_rrx = conditon_dict.get("c")
                            num_str = num_rrx.text()
                            t.append(binary_str)
                            t.append(num_str)
                            binary_str, _ = Check_Shift(t, mem[i + 1], line)
                            temporary.append(binary_str[0])
                            break
                        elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                            if regex_const.match(mem[i + 2]):
                                clean_num = mem[i + 2].lstrip('#')
                                num = int(clean_num)
                                num_str = Encoder(num)
                                t.append(binary_str)
                                t.append(num_str)
                                binary_str, _ = Check_Shift(t, mem[i + 1], line)
                                temporary.append(binary_str[0])
                                break
                            elif regex_register.match(mem[i + 2]):
                                num_edit = line_edit_dict.get(mem[i + 2])
                                num_str = num_edit.text()
                                num = ctypes.c_int32(int(num_str, 16)).value
                                num_str = Encoder(num)
                                t.append(binary_str)
                                t.append(num_str)
                                binary_str, _ = Check_Shift(t, mem[i + 1], line)
                                temporary.append(binary_str[0])
                                break
                    binary_str = Decoder(binary_str)
                    binary_str = Encoder(binary_str)
                    temporary.append(binary_str)
                else:
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            
            if flag == 1 and SHIFT_REGEX.match(instruction_clean):
                arguments, flag_C = Check_Command_With_Flag(temporary, instruction_clean, line)
                result = arguments[0]
                flag_N = result[0]
                if Decoder(result) == 0: flag_Z = '1'
            elif flag == 1 and VALID_COMMAND_REGEX_ARITHMETIC_ADD_SUB.match(instruction_clean):
                arguments, flag_C, flag_V = Check_Command_With_Flag(temporary, instruction_clean, line)
                result = arguments[0]
                flag_N = result[0]
                if Decoder(result) == 0: flag_Z = '1'
            elif flag == 1:
                arguments = Check_Command(temporary, instruction_clean, line)
                result = arguments[0]
                flag_N = result[0]
                if Decoder(result) == 0: flag_Z = '1'
            else:
                arguments = Check_Command(temporary, instruction_clean, line)
            
            if not c:
                arguments.append(f"{0:032b}")
                return reg, arguments, flag_N, flag_Z, flag_C, flag_V, flag_T
            if arguments == None:
                return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
        else:
            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
        return reg, arguments, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    elif match_instruction_test:
        line_edit = line_edit_dict.get(reg[0])
        binary_str_1 = line_edit.text()
        hex_int_1 = int(binary_str_1, 16)
        binary_str_1 = Encoder(hex_int_1)
        instruction_clean = match_instruction_test.group(0)
        instruction = re.sub(match_instruction_test.group(0), "", instruction)
        
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        if match_condition:
            condition = match_condition.group(0)
            c = dict.check_condition(condition)
            instruction = re.sub(condition, "", instruction)
        elif not match_condition:
            c = dict.check_condition(condition)
        
        if not instruction:
            temporary = []
            for i in range(len(mem)):
                item = mem[i]
                if regex_const.match(item):
                    clean_num = item.lstrip('#')
                    num = int(clean_num)
                    num_string = Encoder(num)
                    binary_str_2 = num_string
                elif regex_register.match(item):
                    line_edit = line_edit_dict.get(item)
                    binary_str_2 = line_edit.text()
                    hex_int_2 = ctypes.c_int32(int(binary_str_2, 16)).value
                    binary_str_2 = Encoder(hex_int_2)
                    if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]):
                        t = []
                        if mem[i + 1].lower() == "rrx":
                            num_rrx = conditon_dict.get("c")
                            num_str = num_rrx.text()
                            t.append(binary_str_2)
                            t.append(num_str)
                            binary_str, _ = Check_Shift(t, mem[i + 1], line)
                            binary_str_2 = binary_str[0]
                            break
                        elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                            if regex_const.match(mem[i + 2]):
                                clean_num = mem[i + 2].lstrip('#')
                                num = int(clean_num)
                                num_str = Encoder(num)
                                t.append(binary_str_2)
                                t.append(num_str)
                                binary_str, _ = Check_Shift(t, mem[i + 1], line)
                                binary_str_2 = binary_str[0]
                                break
                            elif regex_register.match(mem[i + 2]):
                                num_edit = line_edit_dict.get(mem[i + 2])
                                num = ctypes.c_int32(int(num_str, 16)).value
                                num_str = Encoder(num)
                                t.append(binary_str_2)
                                t.append(num_str)
                                binary_str, _ = Check_Shift(t, mem[i + 1], line)
                                binary_str_2 = binary_str[0]
                                break
                        else:
                            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                    binary_str_2 = Decoder(binary_str_2)
                    binary_str_2 = Encoder(binary_str_2)
                else:
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            temporary.append(binary_str_1)
            temporary.append(binary_str_2)
            regex = re.compile(r"(CMP|CMN)", re.IGNORECASE)
            if regex.match(instruction_clean):
                arguments, flag_C, flag_V = Check_Command_With_Flag(temporary, instruction_clean, line)
            else:
                arguments = Check_Command_With_Flag(temporary, instruction_clean, line)
            
            if not c:
                arguments.append(f"{0:032b}")
                return reg, arguments, flag_N, flag_Z, flag_C, flag_V, flag_T
                
            flag_T = 1    
            result = arguments[0]
            flag_N = result[0]
            if Decoder(result) == 0: flag_Z = '1'
        else:
            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            
        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
    elif match_instruction_single_data_tranfer:
        num_result_str = None
        binary_str = ""
        instruction_clean = match_instruction_single_data_tranfer.group(0)
        instruction = re.sub(match_instruction_single_data_tranfer.group(0), "", instruction)
        
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        if match_condition:
            condition = match_condition.group(0)
            c = dict.check_condition(condition)
            instruction = re.sub(condition, "", instruction)
        elif not match_condition:
            c = dict.check_condition(condition)
        
        regex_bracket_1 = re.compile(r"\[", re.IGNORECASE)
        regex_bracket_2 = re.compile(r"\]", re.IGNORECASE)
        temporary = []
        if len(mem) == 1:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            regex_equal = re.compile(r"\=")
            if bracket_1 and bracket_2:
                mem[0] = mem[0].strip("[]")
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                else:
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            else:
                have_label = re.search(regex_equal, mem[0])
                if have_label and data_labels:
                    label = mem[0].strip('=')
                    if label in data_labels:
                        index = data_labels.index(label)
                        hex_str = data_labels[index + 1]
                else:
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
               
            if instruction_clean.lower() == "ldr":
                result = LDR(hex_str, address, memory)
                arguments.append(result)
            if instruction_clean.lower() == "str":
                STR(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                flag_T = 1
                return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            
        if len(mem) == 2:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            if bracket_1 and bracket_2:
                mem[0] = mem[0].strip("[]")
                reg.append(mem[0])
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                    num_1 = ctypes.c_int32(int(hex_str, 16)).value
                    temporary.append(num_1)
                    if regex_const.match(mem[1]):
                        clean_num = mem[1].lstrip('#')
                        num_2 = int(clean_num)
                        temporary.append(num_2)
                    elif regex_register.match(mem[1]):
                        line_edit = line_edit_dict.get(mem[1])
                        hex_str_reg = line_edit.text()
                        num_2 = ctypes.c_int32(int(hex_str_reg, 16)).value
                        temporary.append(num_2)
                    else:
                        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                elif not regex_register.match(mem[0]):
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                num_result = num_1 + num_2
                num_result_str = Encoder(num_result)
                
            elif bracket_1 and not bracket_2:
                mem[0] = mem[0].strip("[")
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                    num_1 = ctypes.c_int32(int(hex_str, 16)).value
                    temporary.append(num_1)
                elif not regex_register.match(mem[0]):
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                bracket_mem = re.search(regex_bracket_2, mem[1])
                if bracket_mem:
                    mem[1] = mem[1].replace("]", '')
                    exclamation = re.compile(r"\!")
                    exclamation_check = re.search(exclamation, mem[1])
                    if exclamation_check:
                        reg.append(mem[0])
                        mem[1] = mem[1].strip('!')
                        if regex_const.match(mem[1]):
                            clean_num = mem[1].lstrip('#')
                            num_2 = int(clean_num)
                            temporary.append(num_2)
                        elif regex_register.match(mem[1]):
                            line_edit = line_edit_dict.get(mem[1])
                            hex_str_reg = line_edit.text()
                            num_2 = ctypes.c_int32(int(hex_str_reg, 16)).value
                            temporary.append(num_2)
                        else:
                            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                        num_result = num_1 + num_2
                        num_result_str = Encoder(num_result)
                        hex_str = '0x' + format(num_result, '08x')
                    elif not exclamation_check:
                        if regex_const.match(mem[1]):
                            clean_num = mem[1].lstrip('#')
                            num_2 = int(clean_num)
                            temporary.append(num_2)
                        elif regex_register.match(mem[1]):
                            line_edit = line_edit_dict.get(mem[1])
                            hex_str_reg = line_edit.text()
                            num_2 = ctypes.c_int32(int(hex_str_reg, 16)).value
                            temporary.append(num_2)
                        else:
                            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                    num_result = num_1 + num_2
                    hex_str = '0x' + format(num_result, '08x')
                elif not bracket_mem:
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                
            elif not bracket_1:
                return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            
            if instruction_clean.lower() == "ldr":
                result = LDR(hex_str, address, memory)
                arguments.append(result)
                if num_result_str:
                    arguments.append(num_result_str)
            if instruction_clean.lower() == "str":
                STR(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                flag_T = 1
                if(len(reg) == 1):
                    reg = None
                elif(len(reg) == 2):
                    reg[0] = reg[1]
                    reg.pop(1)
                if num_result_str:
                    arguments.append(num_result_str)
                else:
                    arguments = None
     
        elif len(mem) > 2 and len(mem) < 5:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            if bracket_1 and bracket_2:
                mem[0] = mem[0].strip("[]")
                reg.append(mem[0])
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                    num_1 = ctypes.c_int32(int(hex_str, 16)).value
                    temporary.append(num_1)
                    for i in range(1, len(mem)):
                        item = mem[i]
                        if regex_register.match(item):
                            line_edit = line_edit_dict.get(item)
                            hex_str_in = line_edit.text()
                            hex_int_in = ctypes.c_int32(int(hex_str_in, 16)).value
                            hex_str_in = Encoder(hex_int_in)
                            if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]):
                                temp = []
                                if mem[i + 1].lower() == "rrx":
                                    num_rrx = conditon_dict.get("c")
                                    num_str = num_rrx.text()
                                    temp.append(hex_str_in)
                                    temp.append(num_str)
                                    binary_str_reg, _ = Check_Shift(temp, mem[i + 1], line)
                                    break
                                elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                                    if regex_const.match(mem[i + 2]):
                                        clean_num = mem[i + 2].lstrip('#')
                                        num = int(clean_num)
                                        num_str = Encoder(num)
                                        temp.append(hex_str_in)
                                        temp.append(num_str)
                                        binary_str_reg, _ = Check_Shift(temp, mem[i + 1], line)
                                        break
                                    elif regex_register.match(mem[i + 2]):
                                        num_edit = line_edit_dict.get(mem[i + 2])
                                        num_str = num_edit.text()
                                        num = ctypes.c_int32(int(num_str, 16)).value
                                        num_str = Encoder(num)
                                        temp.append(hex_str_in)
                                        temp.append(num_str)
                                        binary_str_reg, _ = Check_Shift(temp, mem[i + 1], line)
                                        break
                        else:
                            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                        
                    num_2 = Decoder(binary_str_reg[0])
                    
                elif not regex_register.match(mem[0]):
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                
                num_result = num_1 + num_2
                num_result_str = Encoder(num_result)
            
            elif bracket_1 and not bracket_2:
                t = None
                mem[0] = mem[0].strip("[")
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                    num_1 = ctypes.c_int32(int(hex_str, 16)).value
                    temporary.append(num_1)
                elif not regex_register.match(mem[0]):
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                if len(mem) == 3:
                    exclamation = re.compile(r"\!")
                    exclamation_check = re.search(exclamation, mem[2])
                    if exclamation_check:
                        t = 1
                        reg.append(mem[0])
                        mem[2] = mem[2].strip("!")
                    search = re.search(regex_bracket_2, mem[2])
                    if search:
                        mem[2] = mem[2].strip("]")
                    else:
                        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                if len(mem) == 4:
                    exclamation = re.compile(r"\!")
                    exclamation_check = re.search(exclamation, mem[3])
                    if exclamation_check:
                        t = 1
                        reg.append(mem[0])
                        mem[3] = mem[3].strip("!")
                    search = re.search(regex_bracket_2, mem[3])
                    if search:
                        mem[3] = mem[3].strip("]")
                    else:
                        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                for i in range(1, len(mem)):
                    item = mem[i]
                    if regex_register.match(item):
                        line_edit = line_edit_dict.get(item)
                        hex_str_in = line_edit.text()
                        hex_int_in = ctypes.c_int32(int(hex_str_in, 16)).value
                        hex_str_in = Encoder(hex_int_in)
                        if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]):
                            temp = []
                            if mem[i + 1].lower() == "rrx":
                                num_rrx = conditon_dict.get("c")
                                num_str = num_rrx.text()
                                temp.append(hex_str_in)
                                temp.append(num_str)
                                binary_str_reg, _ = Check_Shift(temp, mem[i + 1], line)
                                break
                            elif not mem[i + 1].lower() == "rrx" and i + 2 < len(mem):
                                if regex_const.match(mem[i + 2]):
                                    clean_num = mem[i + 2].lstrip('#')
                                    num = int(clean_num)
                                    num_str = Encoder(num)
                                    temp.append(hex_str_in)
                                    temp.append(num_str)
                                    binary_str_reg, _ = Check_Shift(temp, mem[i + 1], line)
                                    break
                                elif regex_register.match(mem[i + 2]):
                                    num_edit = line_edit_dict.get(mem[i + 2])
                                    num_str = num_edit.text()
                                    num = int(num_str, 16)
                                    num_str = Encoder(num)
                                    temp.append(hex_str_in)
                                    temp.append(num_str)
                                    binary_str_reg, _ = Check_Shift(temp, mem[i + 1], line)
                                    break
                    else:
                        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                num_2 = Decoder(binary_str_reg[0])
                num_result = num_1 + num_2
                num_result_str = Encoder(num_result)
                    
            elif not bracket_1:
                return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            
            if instruction_clean.lower() == "ldr":
                result = LDR(hex_str, address, memory)
                arguments.append(result)
                if num_result_str:
                    arguments.append(num_result_str)
            
            if instruction_clean.lower() == "str":
                hex_str = num_result_str
                STR(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                flag_T = 1
                if(len(reg) == 1):
                    reg = None
                elif(len(reg) == 2):
                    reg[0] = reg[1]
                    reg.pop(1)
                if num_result_str and t == 1:
                    arguments.append(num_result_str)
                else:
                    arguments = None
                
        elif len(mem) > 4:
            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
    
        return reg, arguments, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    if match_instruction_multi:
        u = None
        if instruction and instruction[0] == "u":
            u = 0
            instruction = instruction[1:]
        if instruction and instruction[0] == "s":
            u = 1
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
            c = dict.check_condition(condition)
            instruction = re.sub(condition, "", instruction)
        elif not match_condition:
            c = dict.check_condition(condition)
        match_flag = re.search(FLAG_REGEX, instruction)
        flag = None
        if match_flag:
            instruction = instruction.lstrip(match_flag.group(0))
            flag = 1
        if not instruction:
            temporary = []
            if l == 1 and len(mem) == 3:
                reg.append(mem[0])
                mem = mem[1:]
            for i in range(len(mem)):
                item = mem[i]
                if regex_register.match(item):
                    line_edit = line_edit_dict.get(item)
                    binary_str = line_edit.text()
                    num = ctypes.c_int32(int(binary_str, 16)).value
                    binary_str = Encoder(num)
                    temporary.append(binary_str)
                else:
                    return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
                      
            if flag == 1:
                result = arguments[0]
                flag_N = result[0]
                if Decoder(result) == 0: flag_Z = '1'
            
            if u != None and (l == 1 or instruction_clean.lower() == "div"):    
                arguments = Check_Command_Long(temporary, instruction_clean, u, reg, line)
            elif u == None and l == None:
                arguments = Check_Command(temporary, instruction_clean, line)
            else:
                return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
            
            if not c:
                arguments.append(f"{0:032b}")
                return reg, arguments, flag_N, flag_Z, flag_C, flag_V, flag_T
            if arguments == None:
                return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
        else:
            return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
        return reg, arguments, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    else:
        return None, None, flag_N, flag_Z, flag_C, flag_V, flag_T
    
def Check_Shift(temporary, instruction, line):
    if (instruction.lower() == "lsr"):
        results, carry = LSR_C(temporary, line)
    elif (instruction.lower() == "lsl"):
        results, carry = LSL_C(temporary, line)
    elif (instruction.lower() == "asr"):
        results, carry = ASR_C(temporary, line)
    elif (instruction.lower() == "ror"):
        results, carry = ROR_C(temporary, line)
    elif (instruction.lower() == "rrx"):
        results, carry = RRX_C(temporary, line)
    return results, carry
    
def Check_Command(temporary, instruction, line):
    arguments = []
    if(instruction.lower() == "mov"):
        arguments = MOV(temporary, line)
    elif (instruction.lower() == "lsr"):
        arguments, _ = LSR_C(temporary, line)
    elif (instruction.lower() == "lsl"):
        arguments, _ = LSL_C(temporary, line)
    elif (instruction.lower() == "asr"):
        arguments, _ = ASR_C(temporary, line)
    elif (instruction.lower() == "ror"):
        arguments, _ = ROR_C(temporary, line)
    elif (instruction.lower() == "rrx"):
        arguments, _ = RRX_C(temporary, line)
    elif (instruction.lower() == "and"):
        arguments = AND(temporary, line)
    elif (instruction.lower() == "bic"):
        arguments = BIC(temporary, line)
    elif (instruction.lower() == "orr"):
        arguments = ORR(temporary, line)
    elif (instruction.lower() == "orn"):
        arguments = ORN(temporary, line)
    elif (instruction.lower() == "eor"):
        arguments = EOR(temporary, line)
    elif(instruction.lower() == "mvn"):
        arguments = MVN(temporary, line)
    elif(instruction.lower() == "add"):
        arguments, _, _ = dict.add_32(temporary, line)
    elif(instruction.lower() == "adc"):
        arguments, _, _ = ADC(temporary, line)
    elif(instruction.lower() == "sub"):
        arguments, _, _ = dict.sub_32(temporary, line)
    elif(instruction.lower() == "sbc"):
        arguments, _, _ = SBC(temporary, line)
    elif(instruction.lower() == "rsb"):
        arguments, _, _ = RSB(temporary, line)
    elif(instruction.lower() == "rsc"):
        arguments, _, _ = RSB(temporary, line)
    elif(instruction.lower() == "mul"):
        arguments = dict.mul_32(temporary, line)
    elif(instruction.lower() == "mla"):
        arguments = MLA(temporary, line)
    elif(instruction.lower() == "mls"):
        arguments = MLS(temporary, line)
    return arguments

def Check_Command_With_Flag(temporary, instruction, line):
    arguments = []
    if (instruction.lower() == "lsr"):
        arguments, carry = LSR_C(temporary, line)
    elif (instruction.lower() == "lsl"):
        arguments, carry = LSL_C(temporary, line)
    elif (instruction.lower() == "asr"):
        arguments, carry = ASR_C(temporary, line)
    elif (instruction.lower() == "ror"):
        arguments, carry = ROR_C(temporary, line)
    elif (instruction.lower() == "rrx"):
        arguments, carry = RRX_C(temporary, line)
    elif(instruction.lower() == "add"):
        arguments, carry, overflow = dict.add_32(temporary, line)
        return arguments, carry, overflow
    elif(instruction.lower() == "adc"):
        arguments, carry, overflow = ADC(temporary, line)
        return arguments, carry, overflow
    elif(instruction.lower() == "sub"):
        arguments, carry, overflow = dict.sub_32(temporary, line)
        return arguments, carry, overflow
    elif(instruction.lower() == "sbc"):
        arguments, carry, overflow = SBC(temporary, line)
        return arguments, carry, overflow
    elif(instruction.lower() == "rsb"):
        arguments, carry, overflow = RSB(temporary, line)
        return arguments, carry, overflow
    elif(instruction.lower() == "rsc"):
        arguments, carry, overflow = RSC(temporary, line)
        return arguments, carry, overflow
    elif (instruction.lower() == "cmp"):
        arguments, carry, overflow = dict.sub_32(temporary, line)
        return arguments, carry, overflow
    elif (instruction.lower() == "cmn"):
        arguments, carry, overflow = dict.add_32(temporary, line)
        return arguments, carry, overflow
    elif (instruction.lower() == "tst"):
        arguments = AND(temporary, line)
        return arguments
    elif (instruction.lower() == "teq"):
        arguments = EOR(temporary, line)
        return arguments
    return arguments, carry

def Check_Command_Long(temporary, instruction, u, reg, line):
    arguments = []
    if(instruction.lower() == "mul") and u == 0:
        arguments = dict.mul_64_unsigned(temporary, line)
    elif(instruction.lower() == "mul") and u == 1:
        arguments = dict.mul_64_signed(temporary, line)
    elif(instruction.lower() == "mla") and u == 0:
        arguments = UMLA(temporary, reg, line)
    elif(instruction.lower() == "mla") and u == 1:
        arguments = SMLA(temporary, reg, line)
    elif(instruction.lower() == "mls") and u == 0:
        arguments = UMLS(temporary, reg, line)
    elif(instruction.lower() == "mls") and u == 1:
        arguments = SMLS(temporary, reg, line)
    if(instruction.lower() == "div") and u == 0:
        arguments = dict.divide_32_unsigned(temporary, line)
    elif(instruction.lower() == "div") and u == 1:
        arguments = dict.divide_32_signed(temporary, line)
    return arguments

def MOV(temporary, line):
    if len(temporary) == 1:
        result = temporary
        return result
    else:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    
def MVN(temporary, line):
    result = []
    if len(temporary) == 1:
        result.append(dict.complement(temporary[0]))
        return result
    else:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
       
def LSR_C(temporary, line):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.r_shift_32_c(temporary[0], num, line)
        return result, carry
        
def LSL_C(temporary, line):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.l_shift_32_c(temporary[0], num, line)
        return result, carry
    
def ASR_C(temporary, line):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.asr_shift_32_c(temporary[0], num, line)
        return result, carry

def ROR_C(temporary, line):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.ror_shift_32_c(temporary[0], num, line)
        return result, carry
    
def RRX_C(temporary, line):
    if len(temporary) == 1:
        carry_in = conditon_dict.get("c")
        carry_in = carry_in.text()
        result, carry = dict.rrx_shift_32_c(temporary[0], carry_in, line)
        return result, carry
    else:
        carry = '0'
        return None, carry
    
def AND(temporary, line):
    if len(temporary) < 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    else:
        result = dict.and_32(temporary[0], temporary[1], line)
        return result
    
def BIC(temporary, line):
    if len(temporary) < 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    else:
        binary_str = dict.complement(temporary[1])
        result = dict.and_32(temporary[0], binary_str, line)
        return result
    
def ORR(temporary, line):
    if len(temporary) < 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    else:
        result = dict.or_32(temporary[0], temporary[1], line)
        return result
    
def ORN(temporary, line):
    if len(temporary) < 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    else:
        binary_str = dict.complement(temporary[1])
        result = dict.or_32(temporary[0], binary_str, line)
        return result
    
def EOR(temporary, line):
    if len(temporary) < 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    else:
        result = dict.xor_32(temporary[0], temporary[1], line)
        return result

def ADC(temporary, line):
    t = []
    carry_in = conditon_dict.get("c")
    carry_in = carry_in.text()
    carry_int = int(carry_in)
    c = Encoder(carry_int)
    result, _, _ = dict.add_32(temporary, line)
    t.append(result[0])
    t.append(c)
    arguments, carry, overflow = dict.add_32(t, line)
    return arguments, carry, overflow

def SBC(temporary, line):
    t = []
    carry_in = conditon_dict.get("c")
    carry_in = carry_in.text()
    carry_int = int(carry_in)
    if carry_int == 0:
        carry_int = 1
    elif carry_int == 1:
        carry_int = 0
    c = Encoder(carry_int)
    result, _, _ = dict.sub_32(temporary, line)
    t.append(result[0])
    t.append(c)
    arguments, carry, overflow = dict.sub_32(t, line)
    return arguments, carry, overflow
    
def RSB(temporary, line):
    t = temporary[0]
    temporary[0] = temporary[1]
    temporary[1] = t
    arguments, carry, overflow = dict.sub_32(temporary, line)
    return arguments, carry, overflow

def RSC(temporary, line):
    t = []
    carry_in = conditon_dict.get("c")
    carry_in = carry_in.text()
    carry_int = int(carry_in)
    if carry_int == 0:
        carry_int = 1
    elif carry_int == 1:
        carry_int = 0
    c = Encoder(carry_int)
    temp = temporary[0] 
    temporary[0] = temporary[1]
    temporary[1] = temp
    result, _, _ = dict.sub_32(temporary, line)
    t.append(result[0])
    t.append(c)
    arguments, carry, overflow = dict.sub_32(t, line)
    return arguments, carry, overflow

def MLA(temporary, line):
    if len(temporary) != 3:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    temp_1 = []
    temp_1.append(temporary[0])
    temp_1.append(temporary[1])
    t = dict.mul_32(temp_1, line)
    temp_2 = []
    temp_2.append(temporary[2])
    temp_2.append(t[0])
    result, _, _ = dict.add_32(temp_2, line)
    return result

def MLS(temporary, line):
    if len(temporary) != 3:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    temp_1 = []
    temp_1.append(temporary[0])
    temp_1.append(temporary[1])
    t = dict.mul_32(temp_1, line)
    temp_2 = []
    temp_2.append(temporary[2])
    temp_2.append(t[0])
    result, _, _ = dict.sub_32(temp_2, line)
    return result

def UMLA(temporary, reg, line):
    if len(temporary) != 2 or len(reg) == 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    result = []
    hi = line_edit_dict.get(reg[1])
    num_hi_str = hi.text()
    lo = line_edit_dict.get(reg[0])
    num_lo_str = lo.text()
    num_1_64bit = num_hi_str + num_lo_str
    num_1 = int(num_1_64bit, 2)
    t = dict.mul_64_unsigned(temporary, line)
    num_2_64bit = t[1] + t[0]
    num_2 = int(num_2_64bit, 2)
    num_result = num_1 + num_2
    lower_32 = num_result & ((1 << 32) - 1)
    upper_32 = (num_result >> 32) & ((1 << 32) - 1)
    lower_32_str = f"{lower_32:032b}"
    upper_32_str = f"{upper_32:032b}"
    result.append(lower_32_str)
    result.append(upper_32_str)
    return result

def SMLA(temporary, reg, line):
    if len(temporary) != 2 or len(reg) == 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    result = []
    hi = line_edit_dict.get(reg[1])
    num_hi_str = hi.text()
    lo = line_edit_dict.get(reg[0])
    num_lo_str = lo.text()
    num_1_64bit = num_hi_str + num_lo_str
    num_1 = int(num_1_64bit, 2)
    t = dict.mul_64_signed(temporary, line)
    num_2_64bit = t[1] + t[0]
    num_2 = int(num_2_64bit, 2)
    num_result = num_1 + num_2
    lower_32 = num_result & ((1 << 32) - 1)
    upper_32 = (num_result >> 32) & ((1 << 32) - 1)
    lower_32_str = f"{lower_32:032b}"
    upper_32_str = f"{upper_32:032b}"
    result.append(lower_32_str)
    result.append(upper_32_str)
    return result

def UMLS(temporary, reg, line):
    if len(temporary) != 2 or len(reg) == 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    result = []
    hi = line_edit_dict.get(reg[1])
    num_hi_str = hi.text()
    lo = line_edit_dict.get(reg[0])
    num_lo_str = lo.text()
    num_1_64bit = num_hi_str + num_lo_str
    num_1 = int(num_1_64bit, 2)
    t = dict.mul_64_unsigned(temporary, line)
    num_2_64bit = t[1] + t[0]
    num_2 = int(num_2_64bit, 2)
    num_result = num_1 - num_2
    lower_32 = num_result & ((1 << 32) - 1)
    upper_32 = (num_result >> 32) & ((1 << 32) - 1)
    lower_32_str = f"{lower_32:032b}"
    upper_32_str = f"{upper_32:032b}"
    result.append(lower_32_str)
    result.append(upper_32_str)
    return result

def SMLS(temporary, reg, line):
    if len(temporary) != 2 or len(reg) == 2:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Bad arguments to instruction --" + line)
        return None
    result = []
    hi = line_edit_dict.get(reg[1])
    num_hi_str = hi.text()
    lo = line_edit_dict.get(reg[0])
    num_lo_str = lo.text()
    num_1_64bit = num_hi_str + num_lo_str
    num_1 = int(num_1_64bit, 2)
    t = dict.mul_64_signed(temporary, line)
    num_2_64bit = t[1] + t[0]
    num_2 = int(num_2_64bit, 2)
    num_result = num_1 - num_2
    lower_32 = num_result & ((1 << 32) - 1)
    upper_32 = (num_result >> 32) & ((1 << 32) - 1)
    lower_32_str = f"{lower_32:032b}"
    upper_32_str = f"{upper_32:032b}"
    result.append(lower_32_str)
    result.append(upper_32_str)
    return result

def LDR(hex_str, address, memory):
    mapping = {key: value for key, value in zip(address, memory)}
    result = mapping.get(hex_str)
    result_int = int(result, 16)
    result = Encoder(result_int)
    if result == None:
        result = f"{0:032b}"
    return result
    
def STR(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte):
    mapping = {key: value for key, value in zip(address, memory)}
    result = mapping.get(hex_str)
    if not result:
        QtWidgets.QMessageBox.critical(None, "Lỗi", "Invalid address input for STR")
        return
    position = memory.index(result)
    line_edit = line_edit_dict.get(reg[0])
    binary_str = line_edit.text()
    memory[position] = binary_str
    dict.replace_memory(model, address, memory)
    dict.replace_memory(model_2, address, memory)
    dict.replace_memory(model_4, address, memory)
    dict.replace_memory(model_8, address, memory)
    dict.replace_memory_byte(model_byte, address, memory)
    dict.replace_memory_byte(model_2_byte, address, memory)
    dict.replace_memory_byte(model_4_byte, address, memory)
    dict.replace_memory_byte(model_8_byte, address, memory)
