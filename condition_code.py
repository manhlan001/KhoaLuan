# Khởi tạo giá trị các thanh ghi trong một từ điển
registers = {
    "r0": "0", "r1": "0", "r2": "0", "r3": "0",
    "r4": "0", "r5": "0", "r6": "0", "r7": "0",
    "r8": "0", "r9": "0", "r10": "0", "r11": "0",
    "r12": "0", "sp": "0", "lr": "0", "pc": "0"
}

# Danh sách các thanh ghi cần cập nhật
registers_to_update = ["r1", "r5", "sp"]

# Cập nhật giá trị các thanh ghi trong danh sách
for reg in registers_to_update:
    if reg in registers:
        registers[reg] = "1"

# In kết quả để kiểm tra
for reg, value in registers.items():
    print(f"{reg} = {value}")
