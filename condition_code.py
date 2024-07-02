import re
import dict

regex_const_hex = re.compile(r"^#0x[0-9a-fA-F]+$")
test_str = "#0xffffff"

if regex_const_hex.match(test_str):
   test_str = test_str.lstrip("#")
   print(dict.twos_complement_to_signed(test_str))
else:
    print(0)