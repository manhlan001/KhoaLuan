def split_hex(hex_str):
    if not hex_str.startswith("0x") or len(hex_str) % 2 != 0:
        raise ValueError("Invalid hexadecimal input")
    hex_str = hex_str[2:]
    bytes_list = [f"0x{hex_str[i:i+2]}" for i in range(0, len(hex_str), 2)]
    bytes_list.reverse()
    memory = " ".join(bytes_list)
    return memory

def combine_hex(memory):
    bytes_list = memory.split()
    bytes_list.reverse()
    hex_str = "".join(byte[2:] for byte in bytes_list)
    combined_hex = "0x" + hex_str
    return combined_hex

hex_str = '0x12345678'
memory = split_hex(hex_str)
print("Memory:", memory)
combined_hex = combine_hex(memory)
print("Combined Hex:", combined_hex)
