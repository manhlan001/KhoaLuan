from PyQt6 import QtWidgets
import re
from dict import line_edit_dict, conditon_dict
import dict
from encoder import Encoder
from decoder import Decoder

VALID_COMMAND_REGEX = re.compile(r"(MOV|MVN|LSR|LSL|ASR|ROR|RRX|AND|BIC|ORR|EOR|ADD|ADC|SUB|SBC|RSB)", re.IGNORECASE)
VALID_COMMAND_REGEX_BIT_OP = re.compile(r"(MOV|MVN|AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_TEST = re.compile(r"(CMP|CMN|TST|TEQ)", re.IGNORECASE)
VALID_COMMAND_REGEX_BIT_OP_SPECIAL = re.compile(r"(AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_ARITHMETIC_ADD_SUB = re.compile(r"(ADD|ADC|SUB|SBC|RSB)", re.IGNORECASE)
VALID_COMMAND_REGEX_MULTI = re.compile(r"(MUL|MLA|MLS|DIV)", re.IGNORECASE)
VALID_COMMAND_SINGLE_DATA_TRANFER = re.compile(r"(LDR|STR|LDRB|STRB)", re.IGNORECASE)
VALID_COMMAND_BRANCH = re.compile(r"(B|BL|BX)", re.IGNORECASE)
VALID_COMMAND_STACKED = re.compile(r"(POP|PUSH)", re.IGNORECASE)
VALID_COMMAND_SATURATE = re.compile(r"(SSAT|USAT)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE|AL)", re.IGNORECASE)
SHIFT_REGEX = re.compile(r"(LSL|LSR|ASR|ROR|RRX)", re.IGNORECASE)
FLAG_REGEX = re.compile(r"S", re.IGNORECASE)
COLON_REGEX = re.compile(r"\:")
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

def check_branch(self, line, address, lines):
    flag_B = None
    mapping = {key: value for key, value in zip(address, lines)}
    mappping_address = {key: value for key, value in zip(lines, address)}
    condition = "al"
    parts = split_and_filter(line)
    if parts == None or (not len(parts) == 2):
        return None, flag_B
    instruction = parts[0]
    match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
    if match_condition:
        condition = match_condition.group(0)
        c = dict.check_condition(condition)
        instruction = re.sub(condition, "", instruction)
    elif not match_condition:
        c = dict.check_condition(condition)
    if VALID_COMMAND_BRANCH.match(instruction):
        flag_B = 1
        if instruction.lower() == "bx":
            if regex_register.match(parts[1]):
                line_str = line_edit_dict.get(parts[1])
                bit_str = line_str.text()
                bit_int = dict.twos_complement_to_signed(bit_str)
                hex_string = format(bit_int, '08x')
                label = mapping.get(hex_string)
                return label, flag_B
            else:
                return None, None
        if instruction.lower() == "bl":
            address_branch_link = mappping_address.get(line)
            int_address_branch_link = dict.twos_complement_to_signed(address_branch_link)
            int_address_branch_link = int_address_branch_link + 4
            str_address_branch_link = format(int_address_branch_link, '08x')
            lr = line_edit_dict.get("lr")
            lr.setText(str_address_branch_link)
        if not c:
            return None, flag_B
        return parts[1], flag_B
    else:
        return None, flag_B
    
def check_stacked(self, line, address, lines, stacked):
    mappping_address = {key: value for key, value in zip(address, lines)}
    label_stacked = None
    flag_stacked = None
    reg_stacked = []
    arguments_stacked = []
    condition = "al"
    parts = split_and_filter(line)
    instruction = parts[0]
    mems = parts[1:]
    match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
    if match_condition:
        condition = match_condition.group(0)
        c = dict.check_condition(condition)
        instruction = re.sub(condition, "", instruction)
    elif not match_condition:
        c = dict.check_condition(condition)
    if VALID_COMMAND_STACKED.match(instruction):
        sp_line = line_edit_dict.get("sp")
        sp_hex_str = sp_line.text()
        sp = dict.twos_complement_to_signed(sp_hex_str)
        if instruction.lower() == "push":
            flag_stacked = 1
            if mems[0].startswith("{") and mems[-1].endswith("}"):
                mems[0] = mems[0].strip('{')
                mems[-1] = mems[-1].strip('}')
                for mem in mems:
                    if regex_register.match(mem):
                        line_str = line_edit_dict.get(mem)
                        bit_str = line_str.text()
                        bit_int = dict.twos_complement_to_signed(bit_str)
                        hex_string = format(bit_int, '08x')
                        stacked.append(hex_string)
                        sp -= 4
                    else:
                        return None, None, None, None
            else:
                return None, None, None, None
        if instruction.lower() == "pop":
            flag_stacked = 2
            pop_list = []
            if mems[0].startswith("{") and mems[-1].endswith("}"):
                mems[0] = mems[0].strip('{')
                mems[-1] = mems[-1].strip('}')
                for mem in mems:
                    if regex_register.match(mem) or mem.lower() == "pc":
                        pop_list.append(mem)
                    else:
                        return None, None, None, None
            else:
                return None, None, None, None
            if len(pop_list) <= len(stacked):
                mapping = {key: value for key, value in zip(pop_list, stacked)}
                if "pc" in pop_list:
                    label_stacked = mappping_address.get(mapping.get("pc"))
                    pop_list.remove("pc")
                    sp += 4
                for i in range(len(pop_list)):
                    reg_stacked.append(pop_list[i])
                    hex_str = mapping.get(pop_list[i])
                    int_str = dict.twos_complement_to_signed(hex_str)
                    bin_str = Encoder(int_str)
                    arguments_stacked.append(bin_str)
                    sp += 4
            else:
                flag_stacked = 3
                return None, None, None, flag_stacked
        if not c:
            return None, None, None, None
        sp_bin_str = Encoder(sp)
        sp_dec = Decoder(sp_bin_str)
        sp_hex_str = format(sp_dec, '08x')
        sp_line = line_edit_dict.get('sp')
        sp_line.setText(sp_hex_str)
        sp_line.setStyleSheet("background-color: yellow; font-family: 'Open Sans', Verdana, Arial, sans-serif; font-size: 16px;")
        return reg_stacked, arguments_stacked, label_stacked, flag_stacked
    else:
        return None, None, None, None
        
def check_assembly_line(self, lines, line, address, memory, data_labels, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte, stacked):
    reg = []
    c = True
    flag_N = flag_Z = flag_C = flag_V = "0"
    flag_T = None
    condition = "al"
    label, flag_B = check_branch(self, line, address, lines)
    reg_stacked, arguments_stacked, label_stacked, flag_stacked = check_stacked(self, line, address, lines, stacked)
    if flag_stacked:
        return reg_stacked, arguments_stacked, label_stacked, flag_stacked, flag_N, flag_Z, flag_C, flag_V, flag_T
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
         return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    if len(parts) < 3:
        return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T

    instruction = parts[0]
    reg.append(parts[1])
    mem = parts[2:]
    arguments = []
    
    if not regex_register.match(reg[0]):
        return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    if regex_register.match(reg[0]) and reg[0].lower() == "sp" or reg[0].lower() == "pc":
        return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    if len(mem) > 4:
        return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T

    match_instruction = re.search(VALID_COMMAND_REGEX, instruction)
    match_instruction_test = re.search(VALID_COMMAND_REGEX_TEST, instruction)
    match_instruction_single_data_tranfer = re.search(VALID_COMMAND_SINGLE_DATA_TRANFER, instruction)
    match_instruction_multi = re.search(VALID_COMMAND_REGEX_MULTI, instruction)
    match_instruction_saturate = re.search(VALID_COMMAND_SATURATE, instruction)
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
            if len(mem) == 1 and (VALID_COMMAND_REGEX_BIT_OP_SPECIAL.match(instruction_clean) or VALID_COMMAND_REGEX_ARITHMETIC_ADD_SUB.match(instruction_clean)):
                mem.insert(0, reg[0])
            for i in range(len(mem)):
                item = mem[i]
                if i == 0 and (regex_const.match(item) or regex_const_hex.match(item)) and not VALID_COMMAND_REGEX_BIT_OP.match(instruction_clean):
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                if regex_const.match(item):
                    clean_num = item.lstrip('#')
                    num = int(clean_num)
                    num_string = Encoder(num)
                    temporary.append(num_string)
                elif regex_const_hex.match(item):
                    clean_num = item.lstrip('#')
                    num = dict.twos_complement_to_signed(clean_num)
                    num_string = Encoder(num)
                    temporary.append(num_string)
                elif regex_register.match(item):
                    line_edit = line_edit_dict.get(item)
                    binary_str = line_edit.text()
                    hex_int = dict.twos_complement_to_signed(binary_str)
                    binary_str = Encoder(hex_int)
                    if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]) and not SHIFT_REGEX.match(instruction_clean):
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
                                num = dict.twos_complement_to_signed(num_str)
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
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            
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
                return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            if arguments == None:
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        else:
            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    
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
                elif regex_const_hex.match(item):
                    clean_num = item.lstrip('#')
                    num = dict.twos_complement_to_signed(clean_num)
                    num_string = Encoder(num)
                    binary_str_2 = num_string
                elif regex_register.match(item):
                    line_edit = line_edit_dict.get(item)
                    binary_str_2 = line_edit.text()
                    hex_int_2 = dict.twos_complement_to_signed(binary_str_2)
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
                                num = dict.twos_complement_to_signed(num_str)
                                num_str = Encoder(num)
                                t.append(binary_str_2)
                                t.append(num_str)
                                binary_str, _ = Check_Shift(t, mem[i + 1], line)
                                binary_str_2 = binary_str[0]
                                break
                        else:
                            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                    binary_str_2 = Decoder(binary_str_2)
                    binary_str_2 = Encoder(binary_str_2)
                else:
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            temporary.append(binary_str_1)
            temporary.append(binary_str_2)
            regex = re.compile(r"(CMP|CMN)", re.IGNORECASE)
            if regex.match(instruction_clean):
                arguments, flag_C, flag_V = Check_Command_With_Flag(temporary, instruction_clean, line)
            else:
                arguments = Check_Command_With_Flag(temporary, instruction_clean, line)
            if not c:
                arguments.append(f"{0:032b}")
                return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            flag_T = 1    
            result = arguments[0]
            flag_N = result[0]
            if Decoder(result) == 0: flag_Z = '1'
        else:
            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    elif match_instruction_single_data_tranfer:
        equ = None
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
        if instruction.lower() == "b":
            instruction_clean = instruction_clean + "b"
        if instruction.lower() == "h":
            instruction_clean = instruction_clean + "h"
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
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            else:
                have_label = re.search(regex_equal, mem[0])
                if have_label and data_labels:
                    label = mem[0].strip('=')
                    if label in data_labels:
                        index = data_labels.index(label)
                        hex_str = data_labels[index + 1]
                        if index + 2 < len(data_labels) and data_labels[index + 2] == "equ":
                            equ = True
                    label = None
                else:
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
               
            if instruction_clean.lower() == "ldr":
                if equ:
                    int_str = int(hex_str, 16)
                    result = Encoder(int_str)
                else:
                    result = LDR(hex_str, model)
                arguments.append(result)
            if instruction_clean.lower() == "ldrb":
                if equ:
                    int_str = int(hex_str, 16)
                    result = Encoder(int_str)
                else:
                    result = LDR_B(hex_str, model_byte)
                arguments.append(result)
            if instruction_clean.lower() == "ldrh":
                if equ:
                    int_str = int(hex_str, 16)
                    result = Encoder(int_str)
                else:
                    result = LDR_H(hex_str, model_byte)
                arguments.append(result)
            if instruction_clean.lower() == "str":
                STR(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                flag_T = 1
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            if instruction_clean.lower() == "strb":
                STR_B(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                flag_T = 1
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            if instruction_clean.lower() == "strh":
                STR_H(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                flag_T = 1
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            
        elif len(mem) == 2:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            if bracket_1 and bracket_2:
                mem[0] = mem[0].strip("[]")
                reg.append(mem[0])
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                    num_1 = dict.twos_complement_to_signed(hex_str)
                    temporary.append(num_1)
                    if regex_const.match(mem[1]):
                        clean_num = mem[1].lstrip('#')
                        num_2 = int(clean_num)
                        temporary.append(num_2)
                    else:
                        return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                elif not regex_register.match(mem[0]):
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                num_result = num_1 + num_2
                num_result_str = Encoder(num_result)
                
            elif bracket_1 and not bracket_2:
                mem[0] = mem[0].strip("[")
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                    num_1 = dict.twos_complement_to_signed(hex_str)
                    temporary.append(num_1)
                elif not regex_register.match(mem[0]):
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
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
                            num_2 = dict.twos_complement_to_signed(hex_str_reg)
                            temporary.append(num_2)
                        else:
                            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                        num_result = num_1 + num_2
                        num_result_str = Encoder(num_result)
                        hex_str = format(num_result, '08x')
                    elif not exclamation_check:
                        if regex_const.match(mem[1]):
                            clean_num = mem[1].lstrip('#')
                            num_2 = int(clean_num)
                            temporary.append(num_2)
                        elif regex_register.match(mem[1]):
                            line_edit = line_edit_dict.get(mem[1])
                            hex_str_reg = line_edit.text()
                            num_2 = dict.twos_complement_to_signed(hex_str_reg)
                            temporary.append(num_2)
                        else:
                            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                    num_result = num_1 + num_2
                    hex_str = format(num_result, '08x')
                elif not bracket_mem:
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                
            elif not bracket_1:
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            
            if instruction_clean.lower() == "ldr":
                result = LDR(hex_str, model)
                arguments.append(result)
                if num_result_str:
                    arguments.append(num_result_str)
            if instruction_clean.lower() == "ldrb":
                result = LDR_B(hex_str, model_byte)
                arguments.append(result)
                if num_result_str:
                    arguments.append(num_result_str)
            if instruction_clean.lower() == "ldrh":
                result = LDR_H(hex_str, model_byte)
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
            if instruction_clean.lower() == "strb":
                STR_B(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
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
            if instruction_clean.lower() == "strh":
                STR_H(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
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
     
        elif len(mem) == 4:
            bracket_1 = re.search(regex_bracket_1, mem[0])
            bracket_2 = re.search(regex_bracket_2, mem[0])
            if bracket_1 and not bracket_2:
                t = None
                mem[0] = mem[0].strip("[")
                if regex_register.match(mem[0]):
                    line_edit = line_edit_dict.get(mem[0])
                    hex_str = line_edit.text()
                    num_1 = dict.twos_complement_to_signed(hex_str)
                    temporary.append(num_1)
                elif not regex_register.match(mem[0]):
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                search = re.search(regex_bracket_2, mem[3])
                if search:
                    mem[3] = mem[3].strip("]")
                else:
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                for i in range(1, len(mem)):
                    item = mem[i]
                    if regex_register.match(item):
                        line_edit = line_edit_dict.get(item)
                        hex_str_in = line_edit.text()
                        hex_int_in = dict.twos_complement_to_signed(hex_str_in)
                        hex_str_in = Encoder(hex_int_in)
                        if i + 1 < len(mem) and SHIFT_REGEX.match(mem[i + 1]):
                            temp = []
                            if mem[i + 1].lower() == "lsl" and i + 2 < len(mem):
                                if regex_const.match(mem[i + 2]):
                                    clean_num = mem[i + 2].lstrip('#')
                                    num = int(clean_num)
                                    num_str = Encoder(num)
                                    temp.append(hex_str_in)
                                    temp.append(num_str)
                                    binary_str_reg, _ = Check_Shift(temp, mem[i + 1], line)
                                    break
                    else:
                        return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
                num_2 = Decoder(binary_str_reg[0])
                num_result = num_1 + num_2
                hex_str = format(num_result, '08x')
            elif not bracket_1:
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        
            if instruction_clean.lower() == "ldr":
                result = LDR(hex_str, model)
                arguments.append(result)
            if instruction_clean.lower() == "ldrb":
                result = LDR_B(hex_str, model_byte)
                arguments.append(result)
            if instruction_clean.lower() == "ldrh":
                result = LDR_H(hex_str, model_byte)
                arguments.append(result)
            if instruction_clean.lower() == "str":
                STR(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                arguments = None
                flag_T = 1
                if(len(reg) == 1):
                    reg = None
                elif(len(reg) == 2):
                    reg[0] = reg[1]
                    reg.pop(1)
            if instruction_clean.lower() == "strb":
                STR_B(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                arguments = None
                flag_T = 1
                if(len(reg) == 1):
                    reg = None
                elif(len(reg) == 2):
                    reg[0] = reg[1]
                    reg.pop(1)
            if instruction_clean.lower() == "strh":
                STR_H(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte)
                arguments = None
                flag_T = 1
                if(len(reg) == 1):
                    reg = None
                elif(len(reg) == 2):
                    reg[0] = reg[1]
                    reg.pop(1)
        elif len(mem) > 4:
            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        
        return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    elif match_instruction_multi:
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
            if len(mem) == 1:
                mem.insert(0, reg[0])
            if l == 1 and len(mem) == 3:
                reg.append(mem[0])
                mem = mem[1:]
            for i in range(len(mem)):
                item = mem[i]
                if regex_register.match(item):
                    line_edit = line_edit_dict.get(item)
                    binary_str = line_edit.text()
                    num = dict.twos_complement_to_signed(binary_str)
                    binary_str = Encoder(num)
                    temporary.append(binary_str)
                else:
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            if flag == 1:
                result = arguments[0]
                flag_N = result[0]
                if Decoder(result) == 0: flag_Z = '1'
            if u != None and (l == 1 or instruction_clean.lower() == "div"):    
                arguments = Check_Command_Long(temporary, instruction_clean, u, reg, line)
            elif u == None and l == None:
                arguments = Check_Command(temporary, instruction_clean, line)
            else:
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            if not c:
                arguments.append(f"{0:032b}")
                return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            if arguments == None:
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        else:
            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    
    elif match_instruction_saturate:
        instruction_clean = match_instruction_saturate.group(0)
        instruction = re.sub(match_instruction_saturate.group(0), "", instruction)
        match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
        if match_condition:
            condition = match_condition.group(0)
            c = dict.check_condition(condition)
            instruction = re.sub(condition, "", instruction)
        elif not match_condition:
            c = dict.check_condition(condition)
        if not instruction:
            temporary = []
            if len(mem) == 2:
                const = mem[0]
                reg_const = mem[1]
                if regex_const.match(const) and regex_register.match(reg_const):
                    const = const.lstrip('#')
                    const = int(const)
                    sat = int(pow(2, const) / 2)
                    line_edit = line_edit_dict.get(reg_const)
                    binary_str = line_edit.text()
                    num = dict.twos_complement_to_signed(binary_str)
                    arguments = SAT(sat, num, instruction_clean)
                else:
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            elif len(mem) == 3 or len(mem) == 4:
                const = mem[0]
                reg_const = mem[1]
                shift = mem[2]
                if regex_const.match(const) and regex_register.match(reg_const):
                    const = const.lstrip('#')
                    const = int(const)
                    sat = int(pow(2, const) / 2)
                    line_edit = line_edit_dict.get(reg_const)
                    binary_str = line_edit.text()
                    hex_int_in = dict.twos_complement_to_signed(binary_str)
                    hex_str_in = Encoder(hex_int_in)
                    if SHIFT_REGEX.match(shift):
                        temp = []
                        if shift.lower() == "rrx":
                            num_rrx = conditon_dict.get("c")
                            num_str = num_rrx.text()
                            temp.append(hex_str_in)
                            temp.append(num_str)
                            binary_str_shift, _ = Check_Shift(temp, shift, line)
                        else:
                            if regex_const.match(mem[3]):
                                clean_num = mem[3].lstrip('#')
                                num = int(clean_num)
                                num_str = Encoder(num)
                                temp.append(hex_str_in)
                                temp.append(num_str)
                                binary_str_shift, _ = Check_Shift(temp, shift, line)
                            elif regex_register.match(mem[3]):
                                num_edit = line_edit_dict.get(mem[3])
                                num_str = num_edit.text()
                                num = int(num_str, 16)
                                num_str = Encoder(num)
                                temp.append(hex_str_in)
                                temp.append(num_str)
                                binary_str_shift, _ = Check_Shift(temp, shift, line)
                    num = dict.twos_complement_to_signed(binary_str_shift)
                    arguments = SAT(sat, num, instruction_clean)
                else:
                    return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
            else:
                return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        else:
            return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
        return reg, arguments, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    else:
        return None, None, label, flag_B, flag_N, flag_Z, flag_C, flag_V, flag_T
    
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

def SAT(sat, num, instruction):
    arguments = []
    if instruction.lower() == "ssat":
        if num < -sat:
            result = -sat
            result = Encoder(result)
            arguments.append(result)
        elif num > sat - 1:
            result = sat - 1
            result = Encoder(result)
            arguments.append(result)
        else:
            result = Encoder(num)
            arguments.append(result)
        return arguments
    elif instruction.lower() == "usat":
        if num < 0:
            result = 0
            result = Encoder(result)
            arguments.append(result)
        elif num > 2 * sat - 1:
            result = 2 * sat - 1
            result = Encoder(result)
            arguments.append(result)
        else:
            result = Encoder(num)
            arguments.append(result)
        return arguments
    else:
        return None

def LDR(hex_str, model):
    result = dict.find_one_memory(model, hex_str)
    result_int = dict.twos_complement_to_signed(result)
    result = Encoder(result_int)
    if result == None:
        result = f"{0:032b}"
    return result

def LDR_B(hex_str, model_byte):
    result = dict.find_one_memory_in_byte(model_byte, hex_str)
    result_int = dict.twos_complement_to_signed(result)
    result = Encoder(result_int)
    if result == None:
        result = f"{0:032b}"
    return result

def LDR_H(hex_str, model_byte):
    result = dict.find_one_memory_in_halfword(model_byte, hex_str)
    result_int = dict.twos_complement_to_signed(result)
    result = Encoder(result_int)
    if result == None:
        result = f"{0:032b}"
    return result
    
def STR(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte):
    line_edit = line_edit_dict.get(reg[0])
    mem_replace = line_edit.text()
    mapping = {key: value for key, value in zip(address, memory)}
    try:
        result = mapping.get(hex_str)
        position = memory.index(result)
        memory[position] = mem_replace
    except ValueError:
        pass
    dict.replace_one_memory(model, hex_str, mem_replace)
    dict.replace_one_memory(model_2, hex_str, mem_replace)
    dict.replace_one_memory(model_4, hex_str, mem_replace)
    dict.replace_one_memory(model_8, hex_str, mem_replace)
    dict.replace_one_memory_byte(model_byte, hex_str, mem_replace)
    dict.replace_one_memory_byte(model_2_byte, hex_str, mem_replace)
    dict.replace_one_memory_byte(model_4_byte, hex_str, mem_replace)
    dict.replace_one_memory_byte(model_8_byte, hex_str, mem_replace)
    
def STR_B(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte):
    line_edit = line_edit_dict.get(reg[0])
    mem_replace = line_edit.text()
    mapping = {key: value for key, value in zip(address, memory)}
    try:
        result = mapping.get(hex_str)
        position = memory.index(result)
        memory[position] = mem_replace
    except ValueError:
        pass
    dict.replace_one_memory_in_byte(model, hex_str, mem_replace)
    dict.replace_one_memory_in_byte(model_2, hex_str, mem_replace)
    dict.replace_one_memory_in_byte(model_4, hex_str, mem_replace)
    dict.replace_one_memory_in_byte(model_8, hex_str, mem_replace)
    dict.replace_one_memory_byte_in_byte(model_byte, hex_str, mem_replace)
    dict.replace_one_memory_byte_in_byte(model_2_byte, hex_str, mem_replace)
    dict.replace_one_memory_byte_in_byte(model_4_byte, hex_str, mem_replace)
    dict.replace_one_memory_byte_in_byte(model_8_byte, hex_str, mem_replace)

def STR_H(reg, hex_str, address, memory, model, model_2, model_4, model_8, model_byte, model_2_byte, model_4_byte, model_8_byte):
    line_edit = line_edit_dict.get(reg[0])
    mem_replace = line_edit.text()
    mapping = {key: value for key, value in zip(address, memory)}
    try:
        result = mapping.get(hex_str)
        position = memory.index(result)
        memory[position] = mem_replace
    except ValueError:
        pass
    dict.replace_one_memory_in_halfword(model, hex_str, mem_replace)
    dict.replace_one_memory_in_halfword(model_2, hex_str, mem_replace)
    dict.replace_one_memory_in_halfword(model_4, hex_str, mem_replace)
    dict.replace_one_memory_in_halfword(model_8, hex_str, mem_replace)
    dict.replace_one_memory_halfword_in_byte(model_byte, hex_str, mem_replace)
    dict.replace_one_memory_halfword_in_byte(model_2_byte, hex_str, mem_replace)
    dict.replace_one_memory_halfword_in_byte(model_4_byte, hex_str, mem_replace)
    dict.replace_one_memory_halfword_in_byte(model_8_byte, hex_str, mem_replace)