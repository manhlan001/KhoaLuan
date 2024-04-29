import re
import sys
from dict import line_edit_dict, conditon_dict, and_32, or_32, xor_32, complement
import dict
from encoder import Encoder
from decoder import Decoder

VALID_COMMAND_REGEX = re.compile(r"(MOV|LSR|LSL|ASR|ROR|RRX|AND|BIC|ORR|ORN|EOR)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE)", re.IGNORECASE)
SHIFT_REGEX = re.compile(r"(LSL|LSR|ASR|ROR|RRX)", re.IGNORECASE)
FLAG_REGEX = re.compile(r"S", re.IGNORECASE)

def split_parts(line):
    # Tách chuỗi dựa trên nhiều ký tự phân cách như khoảng trắng, dấu phẩy, dấu hai chấm
    parts = re.split(r'\s+|,|:', line)

    # Bỏ qua các phần tử rỗng sau khi tách
    parts = [part for part in parts if part.strip()]

    return parts
        
def check_assembly_line(self, line):
    parts = split_parts(line)

    # Biểu thức chính quy để kiểm tra định dạng dòng lệnh
    # ^         : bắt đầu dòng
    # \w+       : ít nhất một ký tự từ (word character)
    # \s+       : ít nhất một khoảng trắng
    # r\d+      : "r" tiếp theo là ít nhất một số (rd hoặc rx)
    # |         : hoặc
    # #[\d]+    : "#" tiếp theo là một số (hằng số)
    # $         : kết thúc dòng
    # Đảm bảo có ít nhất ba phần (lệnh và ít nhất hai đối số)
    if len(parts) < 3:
        return None  # Trả về None nếu không đủ đối số

    # Kiểm tra lệnh (phần đầu tiên)
    instruction = parts[0]
    reg = parts[1]
    mem = parts[2:]
    arguments = []
    
    regex_register = re.compile(r"r\d+$")
    regex_const = re.compile(r"#-?\d+$")
    
    flag_N = flag_Z = flag_C = flag_V = "0"
    
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
                        for mem in mem:
                            if regex_const.match(mem):
                                clean_num = mem.lstrip('#')
                                num = int(clean_num)
                                num_string = Encoder(num)
                                temporary.append(num_string)
                            elif regex_register.match(mem):
                                line_edit = line_edit_dict.get(mem)
                                binary_str = line_edit.text()
                                binary_str = Decoder(binary_str)
                                binary_str = Encoder(binary_str)
                                temporary.append(binary_str)
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
                        for mem in mem:
                            if regex_const.match(mem):
                                clean_num = mem.lstrip('#')
                                num = int(clean_num)
                                num_string = Encoder(num)
                                temporary.append(num_string)
                            elif regex_register.match(mem):
                                line_edit = line_edit_dict.get(mem)
                                binary_str = line_edit.text()
                                binary_str = Decoder(binary_str)
                                binary_str = Encoder(binary_str)
                                temporary.append(binary_str)
                        arguments = Check_Command(temporary, instruction_clean)
                    else:
                        return None, None, flag_N, flag_Z, flag_C, flag_V
                        
                return reg, arguments, flag_N, flag_Z, flag_C, flag_V
        else:
            return None, None, flag_N, flag_Z, flag_C, flag_V
    else:
        return None, None, flag_N, flag_Z, flag_C, flag_V
    
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
    #elif (instruction.lower() == "and"):
    #    arguments = AND(mem, arguments)
    #elif (instruction.lower() == "bic"):
    #    arguments = BIC(mem, arguments)
    #elif (instruction.lower() == "orr"):
    #    arguments = ORR(mem, arguments)
    #elif (instruction.lower() == "orn"):
    #    arguments = ORN(mem, arguments)
    #elif (instruction.lower() == "eor"):
    #    arguments = EOR(mem, arguments)
    return arguments

def Check_Command_With_Flag(temporary, instruction):
    arguments = []
    if (instruction.lower() == "lsr"):
        arguments = LSR_C(temporary)
    elif (instruction.lower() == "lsl"):
        arguments = LSL_C(temporary)
    elif (instruction.lower() == "asr"):
        arguments = ASR_C(temporary)
    elif (instruction.lower() == "ror"):
        arguments = ROR_C(temporary)
    elif (instruction.lower() == "rrx"):
        arguments = RRX_C(temporary)
    return arguments

def MOV(temporary):
    result = temporary
    return result

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
        print(result)
        return result
    else:
        return None
    
def RRX_C(temporary):
    if len(temporary) == 1:
        carry_in = conditon_dict.get("c")
        carry_in = carry_in.text()
        result, carry = dict.rrx_shift_32_c(temporary[0], carry_in)
        print(result)
        return result, carry
    else:
        carry = '0'
        return None, carry
    
def AND(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    pattern_command = re.compile(r"^\s*(LSL|LSR|ASR|ROR)$", re.IGNORECASE)
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        num_str = Encoder(num)
        result = and_32(binary_str, num_str)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        if(len(mem) < 3):
            result = and_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
        elif pattern_command.match(mem[2]):
            if pattern_const.match(mem[3]):
                clean_mem = mem[3].lstrip('#')
                num = int(clean_mem)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            elif pattern_register.match(mem[3]):
                line_edit_3 = line_edit_dict.get(mem[3])
                binary_str_3 = line_edit_3.text()
                num = Decoder(binary_str_3)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
                
            result = and_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
            
        return arguments
    else:
        return None
    
def BIC(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    pattern_command = re.compile(r"^\s*(LSL|LSR|ASR|ROR)$", re.IGNORECASE)
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        num_str = Encoder(num)
        num_str = complement(num_str)
        result = and_32(binary_str, num_str)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        if(len(mem) < 3):
            binary_str_2 = complement(binary_str_2)  
            result = and_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
        elif pattern_command.match(mem[2]):
            if pattern_const.match(mem[3]):
                clean_mem = mem[3].lstrip('#')
                num = int(clean_mem)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            elif pattern_register.match(mem[3]):
                line_edit_3 = line_edit_dict.get(mem[3])
                binary_str_3 = line_edit_3.text()
                num = Decoder(binary_str_3)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            
            binary_str_2 = complement(binary_str_2)    
            result = and_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
            
        return arguments
    else:
        return None
    
def ORR(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    pattern_command = re.compile(r"^\s*(LSL|LSR|ASR|ROR)$", re.IGNORECASE)
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        num_str = Encoder(num)
        result = or_32(binary_str, num_str)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        if pattern_command.match(mem[2]):
            if pattern_const.match(mem[3]):
                clean_mem = mem[3].lstrip('#')
                num = int(clean_mem)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            elif pattern_register.match(mem[3]):
                line_edit_3 = line_edit_dict.get(mem[3])
                binary_str_3 = line_edit_3.text()
                num = Decoder(binary_str_3)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
                
            result = or_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
        else:
            result = or_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
            
        return arguments
    else:
        return None
    
def ORN(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    pattern_command = re.compile(r"^\s*(LSL|LSR|ASR|ROR)$", re.IGNORECASE)
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        num_str = Encoder(num)
        num_str = complement(num_str)
        result = or_32(binary_str, num_str)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        if pattern_command.match(mem[2]):
            if pattern_const.match(mem[3]):
                clean_mem = mem[3].lstrip('#')
                num = int(clean_mem)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            elif pattern_register.match(mem[3]):
                line_edit_3 = line_edit_dict.get(mem[3])
                binary_str_3 = line_edit_3.text()
                num = Decoder(binary_str_3)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            
            binary_str_2 = complement(binary_str_2)    
            result = or_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
        else:
            binary_str_2 = complement(binary_str_2)    
            result = or_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
            
        return arguments
    else:
        return None
    
def EOR(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    pattern_command = re.compile(r"^\s*(LSL|LSR|ASR|ROR)$", re.IGNORECASE)
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        num_str = Encoder(num)
        num_str = complement(num_str)
        result = xor_32(binary_str, num_str)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        if pattern_command.match(mem[2]):
            if pattern_const.match(mem[3]):
                clean_mem = mem[3].lstrip('#')
                num = int(clean_mem)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            elif pattern_register.match(mem[3]):
                line_edit_3 = line_edit_dict.get(mem[3])
                binary_str_3 = line_edit_3.text()
                num = Decoder(binary_str_3)
                if (mem[2].lower() == "lsr"):
                    binary_str_2 = r_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "lsl"):
                    binary_str_2 = l_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "asr"):
                    binary_str_2 = asr_shift_32(binary_str_2, num)
                elif (mem[2].lower() == "ror"):
                    binary_str_2 = ror_shift_32(binary_str_2, num)
            
            binary_str_2 = complement(binary_str_2)    
            result = xor_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
        else:
            binary_str_2 = complement(binary_str_2)    
            result = xor_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
            
        return arguments
    else:
        return None
    