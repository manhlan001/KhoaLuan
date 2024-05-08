from decoder import Decoder
from encoder import Encoder
line_edit_dict = {
    "r0": None,
    "r1": None,
    "r2": None,
    "r3": None,
    "r4": None,
    "r5": None,
    "r6": None,
    "r7": None,
    "r8": None,
    "r9": None,
    "r10": None,
    "r11": None,
    "r12": None,
    "sp": None,
    "lr": None,
    "pc": None,
}

conditon_dict = {
    "n": None,
    "z": None,
    "c": None,
    "v": None
}

DataProcessing_opcode_memory_dict = {
    "and": '0000',
    "eor": '0001',
    "sub": '0010',
    "rsb": '0011',
    "add": '0100',
    "adc": '0101',
    "sbc": '0110',
    "rsc": '0111',
    "tst": '1000',
    "teq": '1001',
    "cmp": '1010',
    "cmn": '1011',
    "orr": '1100',
    "mov": '1101',
    "bic": '1110',
    "mvn": '1111'
}

register_memory_dict = {
    "r0": '0000',
    "r1": '0001',
    "r2": '0010',
    "r3": '0011',
    "r4": '0100',
    "r5": '0101',
    "r6": '0110',
    "r7": '0111',
    "r8": '1000',
    "r9": '1001',
    "r10": '1010',
    "r11": '1011',
    "r12": '1100'
}

condition_memory_dict = {
    "eq": '0000',
    "ne": '0001',
    "cs" or "hs": '0010',
    "cc" or "lo": '0011',
    "mi": '0100',
    "pl": '0101',
    "vs": '0110',
    "vc": '0111',
    "hi": '1000',
    "ls": '1001',
    "ge": '1010',
    "lt": '1011',
    "gt": '1100',
    "le": '1101',
    "al": '1110',
}

shift_memory_dict = {
    "lsl": '00',
    "lsr": '01',
    "asr": '10',
    "ror": '11'
}

def check_condition(condition):
    n_edit = conditon_dict.get("n")
    n = n_edit.text()
    z_edit = conditon_dict.get("z")
    z = z_edit.text()
    c_edit = conditon_dict.get("c")
    c = c_edit.text()
    v_edit = conditon_dict.get("v")
    v = v_edit.text()
    if (condition.lower() == "eq"):
        if z == '1':
            return True
        else: 
            return False
    if (condition.lower() == "ne"):
        if z == '0':
            return True
        else: 
            return False
    if (condition.lower() == "cs") or (condition.lower() == "hs"):
        if c == '1':
            return True
        else: 
            return False
    if (condition.lower() == "cc") or (condition.lower() == "lo"):
        if c == '0':
            return True
        else: 
            return False
    if (condition.lower() == "mi"):
        if n == '1':
            return True
        else: 
            return False
    if (condition.lower() == "pl"):
        if n == '0':
            return True
        else: 
            return False
    if (condition.lower() == "vs"):
        if v == '1':
            return True
        else: 
            return False
    if (condition.lower() == "vc"):
        if v == '0':
            return True
        else: 
            return False
    if (condition.lower() == "hi"):
        if c == '1' and z == '0':
            return True
        else: 
            return False
    if (condition.lower() == "ls"):
        if c == '0' or z == '1':
            return True
        else: 
            return False
    if (condition.lower() == "ge"):
        if n == v:
            return True
        else: 
            return False
    if (condition.lower() == "lt"):
        if n != v:
            return True
        else: 
            return False
    if (condition.lower() == "gt"):
        if z == '0' and n == v:
            return True
        else: 
            return False
    if (condition.lower() == "le"):
        if z == '1' or n != v:
            return True
        else: 
            return False
    if (condition.lower() == "al"):
        return True
    if (condition.lower() == ""):
        return True

def l_shift_32_c(a, shift_val):
    result = []
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32
    carry = None
    if shift_val == 0:
        carry = '0'
    else:
        for i in range(shift_val):
            carry = a[0]
            a = a[1:] + '0'
    result.append(a)
    return result, carry

def r_shift_32_c(a, shift_val):
    result = []
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32
    carry = None
    if shift_val == 0:
        carry = '0'
    else:
        for i in range(shift_val):
            carry = a[-1]
            a = '0' + a[:-1]
    result.append(a)
    return result, carry

def asr_shift_32_c(a, shift_val):
    result = []
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32
    sign_bit = a[0]
    carry = None
    if shift_val == 0:
        carry = '0'
    else:
        for i in range(shift_val):
            carry = a[-1]
            a = sign_bit + a[:-1]
    result.append(a)
    return result, carry

def ror_shift_32_c(a, shift_val):
    result = []
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32
    if shift_val == 0:
        carry = '0'
    else:
        for i in range(shift_val):
            carry = a[-1]
            a = a[-1:] + a[:-1]
    result.append(a)
    return result, carry


def rrx_shift_32_c(a, carry_in):
    result = []
    assert isinstance(a, str) and len(a) == 32
    assert isinstance(carry_in, str) and len(carry_in) == 1
    carry_out = a[-1]
    shifted_str = carry_in + a[:-1]
    assert len(shifted_str) == 32
    result.append(shifted_str)
    return result, carry_out

def and_32(str1, str2):
    result = []
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)
    num2 = int(str2, 2)
    result_int = num1 & num2
    result_str = f"{result_int:032b}"
    result_str = Decoder(result_str)
    result_str = Encoder(result_str)
    result.append(result_str)
    return result

def or_32(str1, str2):
    result = []
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)  
    num2 = int(str2, 2)  
    result_int = num1 | num2  
    result_str = f"{result_int:032b}" 
    result_str = Decoder(result_str)
    result_str = Encoder(result_str)
    result.append(result_str)
    return result

def xor_32(str1, str2):
    result = []
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)  
    num2 = int(str2, 2)  
    result_int = num1 ^ num2
    result_str = f"{result_int:032b}" 
    result_str = Decoder(result_str)
    result_str = Encoder(result_str)
    result.append(result_str)
    return result

def cmp_32(temporary):
    result = []
    assert len(temporary) == 2
    str1 = temporary[0]
    str2 = temporary[1]
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)  
    num2 = int(str2, 2)  
    result_int = num1 - num2
    carry = '1' if result_int >= 0 else '0'
    result_str = f"{result_int:032b}"
    overflow = detect_overflow_sub(str1, str2, result_str)
    result_str = Decoder(result_str)
    result_str = Encoder(result_str)
    result.append(result_str)
    return result, carry, overflow

def detect_overflow_sub(a, b, res):
    a_sign = a[0]
    b_sign = b[0]
    res_sign = res[0]
    if a_sign != b_sign and a_sign != res_sign:
        return '1'
    return '0'

def cmn_32(temporary):
    result = []
    assert len(temporary) == 2
    str1 = temporary[0]
    str2 = temporary[1]
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)  
    num2 = int(str2, 2)  
    result_int = num1 + num2
    carry = '1' if (result_int >> 32) & 1 else '0'
    result_str = f"{result_int & ((1 << 32) - 1):032b}"
    overflow = detect_overflow_add(str1, str2, result_str)
    result_str = Decoder(result_str)
    result_str = Encoder(result_str)
    result.append(result_str)
    return result, carry, overflow

def detect_overflow_add(a, b, res):
    a_sign = a[0]
    b_sign = b[0]
    res_sign = res[0]
    if a_sign == b_sign and a_sign != res_sign:
        return '1'
    return '0'

def complement(binary_str):
    assert isinstance(binary_str, str)
    assert all(bit in '01' for bit in binary_str)
    complement_str = ''.join('1' if bit == '0' else '0' for bit in binary_str)
    return complement_str

def find_bit_positions(binary_str):
    return [i for i, bit in enumerate(binary_str) if bit == '1']

def determine_rotation_for_single_bit(position):
    return ((31 - position[0]) // 2) * 2

def determine_rotation_for_multiple_bits(positions):
    first_position = positions[0]
    last_position = positions[-1]
    if last_position - first_position > 8:
        return None
    return  ((31 - last_position) // 2) * 2

def process_binary(num):
    if num < 0:
        num = abs(num) - 1
    binary_str = Encoder(num)
    if len(binary_str) != 32:
        return None
    
    positions = find_bit_positions(binary_str)
    num_ones = len(positions)
    
    if int(binary_str, 2) > 255 and (31 in positions or 30 in positions):
        return None
    
    if num_ones == 1:
        rotation = determine_rotation_for_single_bit(positions)
    elif num_ones > 1:
        rotation = determine_rotation_for_multiple_bits(positions)
        
    if rotation == None:
        return None

    rotated_str = binary_str[-rotation:] + binary_str[:-rotation]
    last_8_bits = rotated_str[-8:]
    rotation_bits = format(15 - (rotation // 2), '04b')
    
    if int(binary_str, 2) < 256:
        result = "0000" + last_8_bits
        return result
    
    result = rotation_bits + last_8_bits
    return result







    
    
