def Encoder(number):
    if(number >= 0):
        binary_str = bin(number)
        binary_32 = binary_str[2:].zfill(32)
        return binary_32
    
    else:
        negative_binary_str = bin(number & 0xFFFFFFFF)
        negative_binary_32 = negative_binary_str[2:].zfill(32)
        return negative_binary_32
    
def Encoder_12bit(number):
    if(number >= 0):
        binary_str = bin(number)
        binary_12 = binary_str[2:].zfill(12)
        return binary_12
    
    else:
        negative_binary_str = bin(number & 0xFFFFFFFF)
        negative_binary_12 = negative_binary_str[2:].zfill(12)
        return negative_binary_12
    
def Encoder_5bit(number):
    if(number >= 0):
        binary_str = bin(number)
        binary_5 = binary_str[2:].zfill(5)
        return binary_5
    
    else:
        negative_binary_str = bin(number & 0xFFFFFFFF)
        negative_binary_5 = negative_binary_str[2:].zfill(5)
        return negative_binary_5