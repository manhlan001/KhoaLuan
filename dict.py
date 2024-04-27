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

common_dict = {
    "mov": None,
}

def l_shift_32(a, shift_val):
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32 
    assert shift_val <= 32
    shifted_str = a[shift_val:] + '0' * shift_val
    assert len(shifted_str) == 32
    return shifted_str
    
def r_shift_32(a, shift_val):
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32 
    shifted_str = '0' * shift_val + a[:-shift_val]
    assert len(shifted_str) == 32
    return shifted_str

def asr_shift_32(a, shift_val):
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32 
    sign_bit = a[0]
    shifted_str = sign_bit * shift_val + a[:-shift_val]
    assert len(shifted_str) == 32
    
    return shifted_str

def ror_shift_32(a, shift_val):
    assert isinstance(a, str) and isinstance(shift_val, int)
    assert len(a) == 32
    assert 0 <= shift_val <= 32
    shifted_str = a[-shift_val:] + a[:-shift_val] 
    assert len(shifted_str) == 32
    return shifted_str

def and_32(str1, str2):
    assert isinstance(str1, str) and isinstance(str2, str)
    assert len(str1) == 32 and len(str2) == 32
    num1 = int(str1, 2)
    num2 = int(str2, 2)
    result = num1 & num2
    result_str = f"{result:032b}"
    return result_str

    
