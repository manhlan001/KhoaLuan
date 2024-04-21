def Encoder(number):
    if(number >= 0):
        # Chuyển đổi thành nhị phân
        binary_str = bin(number)  # Trả về dạng '0b101010'
        # Loại bỏ '0b' và đảm bảo rằng chuỗi có đúng 32 bit
        binary_32 = binary_str[2:].zfill(32)  # Sử dụng zfill để điền số 0 cho đủ 32 bit
        return binary_32
    
    else:
        # Số âm cần chuyển đổi
        negative_number = -42
        # Chuyển đổi thành nhị phân
        negative_binary_str = bin(negative_number & 0xFFFFFFFF)  # Sử dụng mask để đảm bảo 32 bit
        # Loại bỏ '0b' và điền đủ 32 bit
        negative_binary_32 = negative_binary_str[2:].zfill(32)
        return negative_binary_32
