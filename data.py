import re
import sys
import Assembly
import string
from encoder import Encoder
from decoder import Decoder
import dict
from PyQt6 import QtCore, QtGui, QtWidgets

VALID_DATA = ".data"
VALID_SIZE = ".word"
VALID_ASCII = ".asciz"
VALID_SPACE_MEMORY = re.compile(r"(.space|.skip|.zero)", re.IGNORECASE)

regex_const = re.compile(r"-?\d+$")
regex_const_hex = re.compile(r"^0x[0-9a-fA-F]+$")

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
    address_data_base = int(address[-1], 16) + 4
    data_lines = [item for item in data_lines if item not in ["", None]]
    if len(data_lines) >= 2:
        data_lines = data_lines[1:]
        temp = []
        for line in data_lines:
            stripped_line = line.strip()
            result = is_special_or_digit(stripped_line)
            parts = split_and_filter(line)
            if len(parts) > 2:
                if parts[0].endswith(':') and not result and (parts[1] == VALID_SIZE or VALID_SPACE_MEMORY.match(parts[1]) or parts[1] == VALID_ASCII):
                    address_data_base_str = format(address_data_base, '08x')
                    data_address.append(address_data_base_str)
                    parts[0] = parts[0].strip(':')
                    label_data.append(parts[0])
                    label_data.append(address_data_base_str)
                    address_data_base += 4
                else:
                    return None, None, None
        for line in data_lines:
            stripped_line = line.strip()
            result = is_special_or_digit(stripped_line)
            parts = split_and_filter(line)
            if len(parts) > 2:
                if parts[0].endswith(':') and not result and parts[1] == VALID_SIZE:
                    parts = parts[2:]
                    for part in parts:
                        address_data_base_str = format(address_data_base, '08x')
                        if part == parts[0]:
                           data_memory.append(address_data_base_str)
                        if regex_const.match(part):
                            num = int(part)
                            num_bin_str = Encoder(num)
                            num = Decoder(num_bin_str)
                            num_str = format(num, '08x')
                            temp.append(num_str)
                            data_address.append(address_data_base_str)
                        elif regex_const_hex.match(part):
                            num = int(part, 16)
                            num_str = format(num, '08x')
                            temp.append(num_str)
                            data_address.append(address_data_base_str)
                        address_data_base += 4
                elif parts[0].endswith(':') and not result and VALID_SPACE_MEMORY.match(parts[1]):
                    parts = parts[2:]
                    address_data_base_str = format(address_data_base, '08x')
                    data_memory.append(address_data_base_str)
                    if len(parts) == 1:
                        try:
                            size_in_bytes = int(parts[0])
                        except ValueError:
                            QtWidgets.QMessageBox.critical(None, "Lỗi", ".space specifies non-absolute value")
                            return None, None, None
                        if size_in_bytes % 4 == 0:
                            num_addr = size_in_bytes // 4
                        else:
                            num_addr = size_in_bytes // 4 + 1
                        for i in range(num_addr):
                            num_str = format(0, '08x')
                            temp.append(num_str)
                            data_address.append(address_data_base_str)
                            if (i < num_addr - 1) or (num_addr == 1):
                                address_data_base += 4
                                address_data_base_str = format(address_data_base, '08x')
                    elif len(parts) == 2:
                        try:
                            if regex_const.match(parts[0]):
                                size_in_bytes = int(parts[0])
                                fill_value = int(parts[1])
                            elif regex_const_hex.match(parts[0]):
                                size_in_bytes = dict.twos_complement_to_signed(parts[0])
                                fill_value = dict.twos_complement_to_signed(parts[1])
                        except ValueError:
                            QtWidgets.QMessageBox.critical(None, "Lỗi", ".space specifies non-absolute value")
                            return None, None, None
                        if size_in_bytes % 4 == 0:
                            num_addr = size_in_bytes // 4
                        else:
                            num_addr = size_in_bytes // 4 + 1
                        for i in range(num_addr):
                            if fill_value >= -256 and fill_value <= 255:
                                num_str = format(fill_value, '02x')
                                fill_value_str = num_str + num_str + num_str + num_str
                                temp.append(fill_value_str)
                            else:
                                fill_value_str = format(0, '08x')
                                temp.append(fill_value_str)
                            data_address.append(address_data_base_str)
                            if i < num_addr - 1 or num_addr == 1:
                                address_data_base += 4
                                address_data_base_str = format(address_data_base, '08x')
                    else:
                        return None, None, None
                elif parts[0].endswith(':') and not result and parts[1] == VALID_ASCII:
                    parts = re.findall(r'"(.*?)"', line)
                    address_data_base_str = format(address_data_base, '08x')
                    data_memory.append(address_data_base_str)
                    if len(parts) > 0:
                        for i in range(len(parts)):
                            string = parts[i]
                            ascii_mem = dict.ascii_memory(string)
                            for j in range(len(ascii_mem)):
                                temp.append(ascii_mem[j])
                                data_address.append(address_data_base_str)
                                if j < len(ascii_mem) - 1 or len(ascii_mem) == 1:
                                    address_data_base += 4
                                    address_data_base_str = format(address_data_base, '08x')
                    else:
                        return None, None, None    
                else:
                    return None, None, None
            else:
                return None, None, None
        data_memory.extend(temp)
        return label_data, data_address, data_memory
    else:
        return None, None, None