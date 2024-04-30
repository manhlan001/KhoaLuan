import re
import sys
from dict import line_edit_dict, conditon_dict, and_32, or_32, xor_32, complement
import dict
from encoder import Encoder
from decoder import Decoder

VALID_COMMAND_REGEX = re.compile(r"(MOV|LSR|LSL|ASR|ROR|RRX|AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
VALID_COMMAND_REGEX_BIT_OP = re.compile(r"(AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE)", re.IGNORECASE)
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
        
def check_assembly_line(self, line):
    flag_N = flag_Z = flag_C = flag_V = "0"
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
         return None, None, flag_N, flag_Z, flag_C, flag_V
    if len(parts) < 3:
        return None, None, flag_N, flag_Z, flag_C, flag_V

    instruction = parts[0]
    reg = parts[1]
    mem = parts[2:]
    arguments = []
    
    regex_register = re.compile(r"r\d+$")
    regex_const = re.compile(r"#-?\d+$")
    
    if regex_register.match(reg):
        match_instruction = re.search(VALID_COMMAND_REGEX, instruction)
        if match_instruction:
            instruction_clean = match_instruction.group(0)
            instruction = re.sub(match_instruction.group(0), "", instruction)
            match_condition = re.search(CONDITIONAL_MODIFIER_REGEX, instruction)
            if match_condition:
                return None, None, flag_N, flag_Z, flag_C, flag_V
            else:
                match_flag = re.search(FLAG_REGEX, instruction)
                if match_flag:
                    instruction = instruction.lstrip(match_flag.group(0))
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
                                if i + 1 < len(mem) and i + 2 < len(mem) and SHIFT_REGEX.match(mem[i + 1]) and VALID_COMMAND_REGEX_BIT_OP.match(instruction_clean):
                                    if regex_const.match(mem[i + 2]):
                                        clean_num = mem[i + 2].lstrip('#')
                                        num = int(clean_num)
                                        binary_str, flag_C = Check_Shift(binary_str, num, mem[i + 1])
                                        temporary.append(binary_str[0])
                                        break
                                    else:
                                        return None, None, flag_N, flag_Z, flag_C, flag_V
                                binary_str = Decoder(binary_str)
                                binary_str = Encoder(binary_str)
                                temporary.append(binary_str)
                            else:
                                return None, None, flag_N, flag_Z, flag_C, flag_V
                        if SHIFT_REGEX.match(instruction_clean):
                            arguments, flag_C = Check_Command_With_Flag(temporary, instruction_clean)
                        else:
                            arguments = Check_Command(temporary, instruction_clean)
                            
                        result = arguments[0]
                        flag_N = result[0]
                        if Decoder(result) == 0: flag_Z = '1'
                    else:
                        return None, None, flag_N, flag_Z, flag_C, flag_V
                else:
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
                                if i + 1 < len(mem) and i + 2 < len(mem) and SHIFT_REGEX.match(mem[i + 1]) and VALID_COMMAND_REGEX_BIT_OP.match(instruction_clean):
                                    if regex_const.match(mem[i + 2]):
                                        clean_num = mem[i + 2].lstrip('#')
                                        num = int(clean_num)
                                        binary_str, _ = Check_Shift(binary_str, num, mem[i + 1])
                                        temporary.append(binary_str[0])
                                        break
                                    else:
                                        return None, None, flag_N, flag_Z, flag_C, flag_V
                                binary_str = Decoder(binary_str)
                                binary_str = Encoder(binary_str)
                                temporary.append(binary_str)
                            else:
                                return None, None, flag_N, flag_Z, flag_C, flag_V
                        arguments = Check_Command(temporary, instruction_clean)
                    else:
                        return None, None, flag_N, flag_Z, flag_C, flag_V
                        
                return reg, arguments, flag_N, flag_Z, flag_C, flag_V
        else:
            return None, None, flag_N, flag_Z, flag_C, flag_V
    else:
        return None, None, flag_N, flag_Z, flag_C, flag_V
    
def Check_Shift(string, num, instruction):
    if (instruction.lower() == "lsr"):
        results, carry = dict.r_shift_32_c(string, num)
    elif (instruction.lower() == "lsl"):
        results, carry = dict.l_shift_32_c(string, num)
    elif (instruction.lower() == "asr"):
        results, carry = dict.asr_shift_32_c(string, num)
    elif (instruction.lower() == "ror"):
        results, carry = dict.ror_shift_32_c(string, num)
    elif (instruction.lower() == "rrx"):
        results, carry = dict.rrx_shift_32_c(string, num)
    return results, carry
    
def Check_Command(temporary, instruction):
    arguments = []
    if(instruction.lower() == "mov"):
        arguments = MOV(temporary)
    elif (instruction.lower() == "lsr"):
        arguments = LSR(temporary)
    elif (instruction.lower() == "lsl"):
        arguments = LSL(temporary)
    elif (instruction.lower() == "asr"):
        arguments = ASR(temporary)
    elif (instruction.lower() == "ror"):
        arguments = ROR(temporary)
    elif (instruction.lower() == "rrx"):
        arguments = RRX(temporary)
    elif (instruction.lower() == "and"):
        arguments = AND(temporary)
    elif (instruction.lower() == "bic"):
        arguments = BIC(temporary)
    elif (instruction.lower() == "orr"):
        arguments = ORR(temporary)
    elif (instruction.lower() == "orn"):
        arguments = ORN(temporary)
    elif (instruction.lower() == "eor"):
        arguments = EOR(temporary)
    return arguments

def Check_Command_With_Flag(temporary, instruction):
    arguments = []
    if (instruction.lower() == "lsr"):
        arguments, carry = LSR_C(temporary)
    elif (instruction.lower() == "lsl"):
        arguments, carry = LSL_C(temporary)
    elif (instruction.lower() == "asr"):
        arguments, carry = ASR_C(temporary)
    elif (instruction.lower() == "ror"):
        arguments, carry = ROR_C(temporary)
    elif (instruction.lower() == "rrx"):
        arguments, carry = RRX_C(temporary)
    return arguments, carry

def MOV(temporary):
    if len(temporary) == 1:
        result = temporary
        return result
    else:
        return None

def LSR(temporary):
    if len(temporary) < 2:
        return None
    else:
        num = Decoder(temporary[1])
        result, _ = dict.r_shift_32_c(temporary[0], num)
        return result
        
def LSR_C(temporary):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.r_shift_32_c(temporary[0], num)
        return result, carry
        
def LSL(temporary):
    if len(temporary) < 2:
        return None
    else:
        num = Decoder(temporary[1])
        result, _ = dict.l_shift_32_c(temporary[0], num)
        return result

def LSL_C(temporary):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.l_shift_32_c(temporary[0], num)
        return result, carry
        
def ASR(temporary):
    if len(temporary) < 2:
        return None
    else:
        num = Decoder(temporary[1])
        result, _ = dict.asr_shift_32_c(temporary[0], num)
        return result
    
def ASR_C(temporary):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.asr_shift_32_c(temporary[0], num)
        return result, carry
    
def ROR(temporary):
    if len(temporary) < 2:
        return None
    else:
        num = Decoder(temporary[1])
        result, _ = dict.ror_shift_32_c(temporary[0], num)
        return result
    
def ROR_C(temporary):
    if len(temporary) < 2:
        carry = '0'
        return None, carry
    else:
        num = Decoder(temporary[1])
        result, carry = dict.ror_shift_32_c(temporary[0], num)
        return result, carry
    
def RRX(temporary):
    if len(temporary) == 1:
        carry_in = conditon_dict.get("c")
        carry_in = carry_in.text()
        result, _ = dict.rrx_shift_32_c(temporary[0], carry_in)
        return result
    else:
        return None
    
def RRX_C(temporary):
    if len(temporary) == 1:
        carry_in = conditon_dict.get("c")
        carry_in = carry_in.text()
        result, carry = dict.rrx_shift_32_c(temporary[0], carry_in)
        return result, carry
    else:
        carry = '0'
        return None, carry
    
def AND(temporary):
    if len(temporary) < 2:
        return None
    else:
        result = dict.and_32(temporary[0], temporary[1])
        return result
    
def BIC(temporary):
    if len(temporary) < 2:
        return None
    else:
        binary_str = dict.complement(temporary[1])
        result = dict.and_32(temporary[0], binary_str)
        return result
    
def ORR(temporary):
    if len(temporary) < 2:
        return None
    else:
        result = dict.or_32(temporary[0], temporary[1])
        return result
    
def ORN(temporary):
    if len(temporary) < 2:
        return None
    else:
        binary_str = dict.complement(temporary[1])
        result = dict.or_32(temporary[0], binary_str)
        return result
    
def EOR(temporary):
    if len(temporary) < 2:
        return None
    else:
        result = dict.xor_32(temporary[0], temporary[1])
        return result
    