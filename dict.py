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

def condition_passed(cond, APSR):
    """
    Kiểm tra xem điều kiện có được thỏa mãn hay không dựa trên giá trị cờ APSR và điều kiện hiện tại.
    """
    # Xác định kết quả dựa trên ba bit cao của 'cond'
    result = False
    cond_key = cond[:3]  # Lấy ba bit đầu tiên
    condition_map = {
        '000': APSR['Z'] == 1,  # EQ
        '001': APSR['C'] == 1,  # CS
        '002': APSR['N'] == 1,  # MI
        '003': APSR['V'] == 1,  # VS
        '100': APSR['C'] == 1 and APSR['Z'] == 0,  # HI
        '101': APSR['N'] == APSR['V'],  # GE
        '102': APSR['N'] == APSR['V'] and APSR['Z'] == 0,  # GT
        '111': True  # AL (Always)
    }
    if cond_key in condition_map:
        result = condition_map[cond_key]
    # Nếu cần phải đảo ngược điều kiện
    if cond[-1] == '1' and cond != '1111':
        result = not result

    return result

def l_shift_32_c(a, shift_val):
    result = []
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32
    carry = None
    if shift_val == 0:
        carry = '0'
    else:
        carry = a[0] 
    shifted_str = a[shift_val:] + '0' * shift_val
    assert len(shifted_str) == 32
    result.append(shifted_str)
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
        carry = a[31] 
    shifted_str = '0' * shift_val + a[:-shift_val]
    assert len(shifted_str) == 32
    result.append(shifted_str)
    return result, carry

def asr_shift_32_c(a, shift_val):
    result = []
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32
    carry = None
    if shift_val == 0:
        carry = '0'
    else:
        carry = a[31]
    sign_bit = a[0]
    shifted_str = sign_bit * shift_val + a[:-shift_val]
    assert len(shifted_str) == 32
    result.append(shifted_str)
    return result, carry

def rrx_shift_32_c(a, carry_in):
    result = []
    assert isinstance(a, str) and len(a) == 32
    assert isinstance(carry_in, str) and len(carry_in) == 1
    shifted_str = carry_in + a[:-1]
    carry_out = a[-1]
    assert len(shifted_str) == 32
    result.append(shifted_str)
    return result, carry_out

def and_32(str1, str2):
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)
    num2 = int(str2, 2)
    result = num1 & num2
    result_str = f"{result:032b}"
    return result_str

def or_32(str1, str2):
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)  
    num2 = int(str2, 2)  
    result = num1 | num2  
    result_str = f"{result:032b}" 
    return result_str

def xor_32(str1, str2):
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)  
    num2 = int(str2, 2)  
    result = num1 ^ num2
    result_str = f"{result:032b}" 
    return result_str

def complement(binary_str):
    assert isinstance(binary_str, str)
    assert all(bit in '01' for bit in binary_str)
    complement_str = ''.join('1' if bit == '0' else '0' for bit in binary_str)
    return complement_str

def detect_overflow(a,b,res):
    """detects overflow, returns '0b0' or '0b1' depending on whether overflow occurred"""
    a_sign = a[2]
    b_sign = b[2]
    res_sign = res[2]
    if a_sign == b_sign and b_sign != res_sign:
        return '0b1'
    return '0b0'

    
