import dict
def split_hex(hex_str):
    bytes_list = [f"{hex_str[i:i+2]}" for i in range(0, len(hex_str), 2)]
    bytes_list.reverse()
    memory = " ".join(bytes_list)
    return memory

num = 5
surplus = num % 4
print(surplus)
