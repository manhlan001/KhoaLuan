import re
import sys
from dict import line_edit_dict, common_dict, l_shift_32, r_shift_32, asr_shift_32, ror_shift_32, and_32
from encoder import Encoder
from decoder import Decoder

VALID_COMMAND_REGEX = re.compile(r"\b(MOV|TEQ|BX|PUSH|CMP|NEG|CLZ|LSL|RSB|UDIV|POP|MLS|B|SUB|ADD)(\w*)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"\b(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE)(\_W|\_L)?\b", re.IGNORECASE)

def is_int_str(val):
    """returns whether a value is an integer string or not"""
    try: 
        to_int(val)
        return True
    except Exception:
        return False

def to_int(val):
    """changes val to an integer, where val is a decimal, binary, or hex string"""
    assert val[0] == "#"
    val = val[1:]
    if val.isdigit():
        return int(val)
    if val[:2] == '0b':
        return int(val,2)
    if val[:2] == '0x':
        return int(val,16)
    raise Exception
    
def detect_overflow(a,b,res):
    """detects overflow, returns '0b0' or '0b1' depending on whether overflow occurred"""
    a_sign = a[2]
    b_sign = b[2]
    res_sign = res[2]
    if a_sign == b_sign and b_sign != res_sign:
        return '0b1'
    return '0b0'

def invert(bin_str):
    """inverts binary string of any length. expects it in the format of '0b...'. This particularly nifty list comprehension found on http://stackoverflow.com/questions/3920494/python-flipping-binary-1s-and-0s-in-a-string"""
    assert isinstance(bin_str,str)
    raw_num = bin_str[2:]
    return '0b'+''.join('1' if x == '0' else '0' for x in raw_num)

def split_parts(line):
    # Tách chuỗi dựa trên nhiều ký tự phân cách như khoảng trắng, dấu phẩy, dấu hai chấm
    parts = re.split(r'\s+|,|:', line)

    # Bỏ qua các phần tử rỗng sau khi tách
    parts = [part for part in parts if part.strip()]

    return parts
#thêm phần check #2 mới chấp nhận còn 2 không thì lỗi
        
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
        
    if(instruction.lower() == "mov"):
        arguments = MOV(mem, arguments)
    elif (instruction.lower() == "lsr"):
        arguments = LSR(mem, arguments)
    elif (instruction.lower() == "lsl"):
        arguments = LSL(mem, arguments)
    elif (instruction.lower() == "asr"):
        arguments = ASR(mem, arguments)
    elif (instruction.lower() == "ror"):
        arguments = ROR(mem, arguments)
    elif (instruction.lower() == "and"):
        arguments = AND(mem, arguments)
    
    return reg, arguments
    
def MOV(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    if pattern_const.match(mem[0]):
        clean_mem = mem[0].lstrip('#')
        num = int(clean_mem)
        num = Encoder(num)
        arguments.append(num)
        return arguments
    elif pattern_register.match(mem[0]):
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        binary_str = Decoder(binary_str)
        binary_str = Encoder(binary_str)
        arguments.append(binary_str)
        return arguments
    else:
        return None
#sửa lại kiểm tra const có dấu # phía trước số không, có thì tách dấu # ra
        
def LSR(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        result = r_shift_32(binary_str, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        num = Decoder(binary_str_2)
        result = r_shift_32(binary_str_1, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    else:
        return None
        
def LSL(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        result = l_shift_32(binary_str, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        num = Decoder(binary_str_2)
        result = l_shift_32(binary_str_1, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    else:
        return None
        
def ASR(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        result = asr_shift_32(binary_str, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        num = Decoder(binary_str_2)
        result = asr_shift_32(binary_str_1, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    else:
        return None
    
def ROR(mem, arguments):
    pattern_const = re.compile(r"^#-?\d+$")
    pattern_register = re.compile(r"^r\d+$")
    if pattern_const.match(mem[1]):
        clean_mem = mem[1].lstrip('#')
        line_edit = line_edit_dict.get(mem[0])
        binary_str = line_edit.text()
        num = int(clean_mem)
        result = ror_shift_32(binary_str, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    elif pattern_register.match(mem[1]):
        line_edit_1 = line_edit_dict.get(mem[0])
        binary_str_1 = line_edit_1.text()
        line_edit_2 = line_edit_dict.get(mem[1])
        binary_str_2 = line_edit_2.text()
        num = Decoder(binary_str_2)
        result = ror_shift_32(binary_str_1, num)
        result = Decoder(result)
        result = Encoder(result)
        arguments.append(result)
        return arguments
    else:
        return None
    
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
        if pattern_command.match(mem[2]):
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
                
            result = and_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
        else:
            result = and_32(binary_str_1, binary_str_2)
            result = Decoder(result)
            result = Encoder(result)
            arguments.append(result)
            
        return arguments
    else:
        return None
    