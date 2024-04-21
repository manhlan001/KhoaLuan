import re
import sys
from dict import line_edit_dict
from encoder import Encoder
from decoder import Decoder

def split_parts(line):
    # Tách chuỗi dựa trên nhiều ký tự phân cách như khoảng trắng, dấu phẩy, dấu hai chấm
    parts = re.split(r'\s+|,|:|#', line)

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
    mem = parts[2]

    # Kiểm tra đối số
    pattern_const = re.compile(r"^\d+$")
    pattern_register = re.compile(r"^r\d+$")
    arguments = []

    if pattern_const.match(mem):
        num = int(mem)
        num = Encoder(num)
        arguments.append(num)
    else: 
        if pattern_register.match(mem):
            line_edit = line_edit_dict.get(mem)
            binary_str = line_edit.text()
            binary_str = Decoder(binary_str)
            binary_str = Encoder(binary_str)
            arguments.append(binary_str)
        else:
            return reg, None  # Nếu có đối số không hợp lệ, trả về None
        
    if(instruction == "mov" or instruction == "Mov"):
        return reg, arguments
    else:
        return reg, None