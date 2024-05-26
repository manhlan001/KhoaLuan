import ctypes

# Chuỗi hex biểu diễn số âm
hex_str_reg = "FFFFFFFF"

# Chuyển đổi chuỗi hex thành số nguyên có dấu
num_2 = ctypes.c_int32(int(hex_str_reg, 16)).value
print(num_2)  # Output: -1
