import re
import sys
import Assembly
import string
from encoder import Encoder
from decoder import Decoder

VALID_DATA = ".data"
VALID_SIZE = ".word"

regex_const = re.compile(r"-?\d+$")

def split_and_filter(line):
    parts = re.split(r',', line)
    if any(part.strip() == '' for part in parts):
        return None
    final_parts = []
    for part in parts:
        sub_parts = part.split()
        final_parts.extend([sub_part for sub_part in sub_parts if sub_part.strip() != ''])
    return final_parts

def is_special_or_digit(word):
    if not word:
        return False
    first_char = word[0]
    if first_char.isdigit():
        return True
    special_characters = string.punctuation
    if first_char in special_characters:
        return True
    return False

def parse_data(lines):
    if VALID_DATA in lines:
        index = lines.index(VALID_DATA)
        new_list = lines[index:]
        original_list = lines[:index]
        return original_list, new_list
    else:
        return lines, []
    
def process_data(data_lines, address):
    label_data = []
    data_address = []
    data_memory = []
    address_data_base = int(address[-1], 16)
    data_lines = [item for item in data_lines if item not in ["", None]]
    if len(data_lines) >= 2:
        data_lines = data_lines[1:]
        temp = []
        for line in data_lines:
            address_data_base += 4
            address_data_base_str = format(address_data_base, '08x')
            data_address.append(address_data_base_str)
            stripped_line = line.strip()
            result = is_special_or_digit(stripped_line)
            parts = split_and_filter(line)
            if len(parts) > 2:
                if parts[0].endswith(':') and not result and parts[1] == VALID_SIZE:
                    parts[0] = parts[0].strip(':')
                    label_data.append(parts[0])
                    label_data.append(address_data_base_str)
                else:
                    return None, None, None
        for line in data_lines:
            stripped_line = line.strip()
            result = is_special_or_digit(stripped_line)
            parts = split_and_filter(line)
            if len(parts) > 2:
                if parts[0].endswith(':') and not result and parts[1] == VALID_SIZE:
                    parts[0] = parts[0].strip(':')
                    parts = parts[2:]
                    for part in parts:
                        address_data_base += 4
                        address_data_base_str = format(address_data_base, '08x')
                        if part == parts[0]:
                            data_memory.append(address_data_base_str)
                        if regex_const.match(part):
                            num = int(part)
                            num_str = format(num, '08x')
                            temp.append(num_str)
                            data_address.append(address_data_base_str)
                else:
                    return None, None, None
            else:
                return None, None, None
        data_memory.extend(temp)
        return label_data, data_address, data_memory
    else:
        return None, None, None

            