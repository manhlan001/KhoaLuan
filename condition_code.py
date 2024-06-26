def split_hex(hex_str):
    bytes_list = [f"{hex_str[i:i+2]}" for i in range(0, len(hex_str), 2)]
    bytes_list.reverse()
    memory = " ".join(bytes_list)
    return memory

def combine_hex(memory):
    bytes_list = memory.split()
    bytes_list.reverse()
    hex_str = "".join(byte for byte in bytes_list)
    return hex_str

str = "abcdefgh"
str_re = split_hex(str)
print(combine_hex(str_re))