import re
import sys
from dict import plain_edit_dict, line_edit_dict, conditon_dict
import dict
import GiaoDien
from encoder import Encoder
from decoder import Decoder

VALID_COMMAND_BRANCH = re.compile(r"(B|BL|BX)", re.IGNORECASE)
CONDITIONAL_MODIFIER_REGEX = re.compile(r"(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE|AL)", re.IGNORECASE)
regex_register = re.compile(r"r\d+$|lr", re.IGNORECASE)

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
                bit_int = int(bit_str, 16)
                hex_string = '0x' + format(bit_int, '08x')
                label = mapping.get(hex_string)
                return label, flag_B
            else:
                return None, flag_B
        if instruction.lower() == "bl":
            address_branch_link = mappping_address.get(line)
            int_address_branch_link = int(address_branch_link, 16)
            int_address_branch_link = int_address_branch_link + 4
            str_address_branch_link = '0x' + format(int_address_branch_link, '08x')
            lr = line_edit_dict.get("lr")
            lr.setText(str_address_branch_link)
        if not c:
            return None, flag_B
        return parts[1], flag_B
    else:
        return None, flag_B
    
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
        current_int = int(current, 16)
        target_int = int(target, 16)
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