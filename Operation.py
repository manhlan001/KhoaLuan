from encoder import Encoder
# Hàm SignedSatQ kiểm tra saturation cho số nguyên có dấu
def signed_sat_q(i, n):
    # Tính giá trị cực đại và cực tiểu cho số nguyên có dấu
    max_val = (2 ** (n - 1)) - 1
    min_val = -(2 ** (n - 1))

    if i > max_val:
        result = max_val
        saturated = True
    elif i < min_val:
        result = min_val
        saturated = True
    else:
        result = i
        saturated = False

    return (result, saturated)

# Hàm UnsignedSatQ kiểm tra saturation cho số nguyên không dấu
def unsigned_sat_q(i, n):
    # Tính giá trị cực đại cho số nguyên không dấu
    max_val = (2 ** n) - 1

    if i > max_val:
        result = max_val
        saturated = True
    elif i < 0:
        result = 0
        saturated = True
    else:
        result = i
        saturated = False

    return (result, saturated)

# Hàm SignedSat chỉ trả về kết quả giá trị số nguyên có dấu
def signed_sat(i, n):
    result, _ = signed_sat_q(i, n)
    return result

# Hàm UnsignedSat chỉ trả về kết quả giá trị số nguyên không dấu
def unsigned_sat(i, n):
    result, _ = unsigned_sat_q(i, n)
    return result

# Hàm SatQ cho phép xác định saturation có dấu hoặc không dấu
def sat_q(i, n, unsigned):
    if unsigned:
        result, sat = unsigned_sat_q(i, n)  # Sử dụng UnsignedSatQ nếu unsigned là True
    else:
        result, sat = signed_sat_q(i, n)  # Sử dụng SignedSatQ nếu unsigned là False
    return (result, sat)  # Trả về kết quả và trạng thái saturation

# Hàm Sat chỉ trả về kết quả của số nguyên sau khi kiểm tra saturation
def sat(i, n, unsigned):
    if unsigned:
        result = unsigned_sat(i, n)  # Sử dụng UnsignedSat nếu unsigned là True
    else:
        result = signed_sat(i, n)  # Sử dụng SignedSat nếu unsigned là False
    return result  # Trả về kết quả sau khi saturation

# Hàm LSL_C
def lsl_c(x, shift, n):
    assert shift > 0, "Shift phải lớn hơn 0"
    # Mở rộng số nguyên bằng cách thêm các số 0 ở cuối, tương đương với dịch trái
    extended_x = x << shift
    # Lấy kết quả dịch trái giới hạn trong n bit
    result = extended_x & ((1 << n) - 1)
    # Lấy bit "carry" sau khi dịch trái
    carry_out = (extended_x >> n) & 1
    return (result, carry_out)

# Hàm LSL
def lsl(x, shift, n):
    assert shift >= 0, "Shift phải lớn hơn hoặc bằng 0"
    if shift == 0:
        return x
    else:
        # Gọi hàm LSL_C để dịch trái
        result, _ = lsl_c(x, shift, n)
        return result
    
# Hàm LSR_C
def lsr_c(x, shift, n):
    assert shift > 0, "Shift phải lớn hơn 0"
    # Mở rộng số nguyên bằng cách thêm các số 0 ở trước
    extended_x = x << n  # Tạo thành chuỗi số nguyên với n bit và dịch trái
    # Sau đó dịch phải số lượng vị trí cần thiết
    extended_x = extended_x >> (n - shift)
    # Lấy phần cần thiết của kết quả
    result = extended_x & ((1 << n) - 1)  # Giới hạn trong n bit
    # Lấy bit "carry"
    carry_out = (x >> (shift - 1)) & 1
    return (result, carry_out)

# Hàm LSR
def lsr(x, shift, n):
    assert shift >= 0, "Shift phải lớn hơn hoặc bằng 0"
    if shift == 0:
        return x
    else:
        # Gọi hàm LSR_C để dịch phải
        result, _ = lsr_c(x, shift, n)
        return result
    
# Hàm ASR_C
def asr_c(x, shift, n):
    assert shift > 0, "Shift phải lớn hơn 0"
    # Lấy bit dấu để mở rộng
    sign_bit = (x >> (n - 1)) & 1
    # Mở rộng số nguyên bằng cách thêm các bit dấu ở trước
    extended_x = x | ((sign_bit * ((1 << (shift + n)) - 1)) << n)
    # Dịch phải số lượng vị trí cần thiết
    result = extended_x >> shift
    # Giới hạn kết quả trong n bit
    result = result & ((1 << n) - 1)
    # Lấy bit "carry"
    carry_out = (x >> (shift - 1)) & 1
    return (result, carry_out)

# Hàm ASR
def asr(x, shift, n):
    assert shift >= 0, "Shift phải lớn hơn hoặc bằng 0"
    if shift == 0:
        return x
    else:
        # Gọi hàm ASR_C để dịch phải có dấu
        result, _ = asr_c(x, shift, n)
        return result
    
# Hàm ROR_C
def ror_c(x, shift, n):
    assert shift != 0, "Shift không thể là 0"
    m = shift % n  # Xác định số lần xoay phải
    # Xoay phải bằng cách kết hợp dịch phải và dịch trái
    lsr_part = (x >> m)  # Phần dịch phải
    lsl_part = (x << (n - m))  # Phần dịch trái
    result = lsr_part | lsl_part  # Kết hợp hai phần
    # Giới hạn kết quả trong n bit
    result = result & ((1 << n) - 1)
    # Lấy bit "carry"
    carry_out = (result >> (n - 1)) & 1
    return (result, carry_out)

# Hàm ROR
def ror(x, shift, n):
    if shift == 0:
        return x  # Nếu shift là 0, không thay đổi
    else:
        # Gọi hàm ROR_C để xoay phải và chỉ lấy kết quả
        result, _ = ror_c(x, shift, n)
        return result
    
# Hàm RRX_C
def rrx_c(x, carry_in, n):
    # Thêm carry_in vào vị trí cao nhất và dịch phải
    result = (carry_in << (n - 1)) | (x >> 1)  # Kết hợp carry_in và x<N-1:1>
    # Lấy bit "carry_out" là bit thấp nhất của x
    carry_out = x & 1  # X<0>
    return (result, carry_out)

# Hàm RRX
def rrx(x, carry_in, n):
    result, _ = rrx_c(x, carry_in, n)
    return result

import re

# Danh sách các chuỗi cần kiểm tra
mem = ["r1"]

# Biểu thức chính quy để tìm mẫu 'r' theo sau bởi một hoặc nhiều chữ số
regex = re.compile(r"r\d+")

# Tìm tất cả các mẫu 'r+1 số' trong danh sách
matches = [re.findall(regex, m) for m in mem]

# Làm phẳng danh sách các chuỗi khớp
flattened_matches = [item for sublist in matches for item in sublist]

# Tách chữ 'r' khỏi đầu của mỗi chuỗi
clean_num = [item.lstrip('r') for item in flattened_matches]
num = int(clean_num[0])
num_string = Encoder(num)
print(num_string)

# In ra các chuỗi đã tách 'r'
print("Các chuỗi dạng 'r+1 số' đã tách 'r':", num_string)

# Kiểm tra xem có ít nhất một mẫu 'r+1 số' trong danh sách
has_match = any(re.search(regex, m) for m in mem)

if has_match:
    print("Có chuỗi dạng 'r+1 số' trong danh sách")
else:
    print("Không có chuỗi dạng 'r+1 số' trong danh sách")
    

# Biểu thức chính quy để tìm các mẫu 'r+số' hoặc '#+số'
regex_r = re.compile(r"^r\d+$")  # Bắt đầu với 'r' và theo sau là một hoặc nhiều chữ số
regex_hash = re.compile(r"^#\d+$")  # Bắt đầu với '#' và theo sau là một hoặc nhiều chữ số

# Danh sách các phần tử cần kiểm tra
items = ["r1", "#2", "r10", "a5", "#25", "xyz"]

# Duyệt qua từng phần tử và kiểm tra
results = {"r+số": [], "#+số": [], "không khớp": []}

for item in items:
    if regex_r.match(item):
        results["r+số"].append(item)
    elif regex_hash.match(item):
        results["#+số"].append(item)
    else:
        results["không khớp"].append(item)

# In ra các kết quả
print("Các phần tử khớp dạng 'r+số':", results["r+số"])
print("Các phần tử khớp dạng '#+số':", results["#+số"])
print("Các phần tử không khớp:", results["không khớp"])

t = "0"
print(t)

import re

# Dãy ban đầu
sequence = "lsrs"

# Biểu thức chính quy để tìm chuỗi "lsr"
pattern = re.compile(r"lsr")

# Kiểm tra xem chuỗi "lsr" có xuất hiện trong dãy không
match = re.search(pattern, sequence)

if match:
    print("Chuỗi 'lsr' được tìm thấy trong dãy.")
    
    # Xóa chuỗi "lsr" từ đầu dãy bằng lstrip()
    sequence = sequence.lstrip("lsr")

    print("Dãy sau khi xóa chuỗi 'lsr':", sequence)
else:
    print("Chuỗi 'lsr' không được tìm thấy trong dãy.")







   



