import numpy as np

import re
import sys
import os

VALID_COMMAND_REGEX = re.compile(r"\b(MOV|TEQ|BX|PUSH|CMP|NEG|CLZ|LSL|RSB|UDIV|POP|MLS|B|SUB|ADD)(\w*)")
CONDITIONAL_MODIFIER_REGEX = re.compile(r"\b(EQ|NE|CS|HS|CC|LO|MI|PL|VS|VC|HI|LS|GE|LT|GT|LE)(\_W|\_L)?\b")

def add_32(a,b,carry_in='0b0'):
    """takes two 32-digit binary strings and returns their sum in the same format, along with overflow and carryout."""
    assert len(a) == 34 and len(b) == 34
    res = None
    msb_carry_out = bin(0)
    temp_sum = bin(int(a,2)+int(b,2)+int(carry_in,2))
    if len(temp_sum) < 34:
        res = s_bin_se_32(int(a,2)+int(b,2)+int(carry_in,2))
    else:
        res = '0b'+temp_sum[-32:]
    if len(temp_sum) > len(a):
        msb_carry_out = bin(1)
    over_flow = detect_overflow(a,b,res)
    return res,msb_carry_out,over_flow

def detect_overflow(a,b,res):
    """detects overflow, returns '0b0' or '0b1' depending on whether overflow occurred"""
    a_sign = a[2]
    b_sign = b[2]
    res_sign = res[2]
    if a_sign == b_sign and b_sign != res_sign:
        return '0b1'
    return '0b0'

def add_64(a,b,carry_in='0b0'):
    """takes two 64-digit binary strings and returns their sum in the same format, along with overflow and carryout."""
    assert len(a) == 66 and len(b) == 66
    res = None
    msb_carry_out = bin(0)
    temp_sum = bin(int(a,2)+int(b,2)+int(carry_in,2))
    if len(temp_sum) < 66:
        res = s_bin_se_64(int(a,2)+int(b,2)+int(carry_in,2))
    else:
        res = '0b'+temp_sum[-64:]
    if len(temp_sum) > len(a):
        msb_carry_out = bin(1)
    over_flow = detect_overflow(a,b,res)
    return res,msb_carry_out,over_flow

def invert(bin_str):
    """inverts binary string of any length. expects it in the format of '0b...'. This particularly nifty list comprehension found on http://stackoverflow.com/questions/3920494/python-flipping-binary-1s-and-0s-in-a-string"""
    assert isinstance(bin_str,str)
    raw_num = bin_str[2:]
    return '0b'+''.join('1' if x == '0' else '0' for x in raw_num)

def subtract_32(a,b):
    """returns a - b, carry out, and overflow. expects two 32-digit binary strings."""
    assert len(a) == 34 and len(b) == 34
    b_inv = invert(b)
    return add_32(a,b_inv,carry_in='0b1')

def subtract_64(a,b):
    """returns a - b, carry out, and overflow. expects two 32-digit binary strings."""
    assert len(a) == 66 and len(b) == 66
    b_inv = invert(b)
    return add_64(a,b_inv,carry_in='0b1')

def str_se_64(bin_str):
    """sign extends binary strings to 64 bit binary strings"""
    assert isinstance(bin_str,str)
    raw_bin = bin(bin_str)[2:]
    orig_len = len(raw_bin)
    if raw_bin[0] == 0:
        return '0b'+'0'*(64-orig_len)+raw_bin
    else:
        return '0b'+'1'*(64-orig_len)+raw_bin

def u_bin_se_32(num):
    """converts an int to a binary number and sign extends it with zeros to be 32 bits. Does not accept negative numbers."""
    assert isinstance(num,int)
    assert num >= 0
    raw_bin = bin(num)[2:]
    orig_len = len(raw_bin)
    return '0b'+'0'*(32-orig_len)+raw_bin

def u_bin_se_64(num):
    """converts an int to a binary number and sign extends it with zeros to be 64 bits. Does not accept negative numbers."""
    assert isinstance(num, int)
    assert num >= 0
    raw_bin = bin(num)[2:]
    orig_len = len(raw_bin)
    return '0b'+'0'*(64-orig_len)+raw_bin

def s_bin_se_32(num):
    """converts an int to a 32 bit binary number. Automatically converts negative ints to twos complement representation."""
    assert isinstance(num,int)
    if num > 0:
        return u_bin_se_32(num)
    elif num < 0:
        raw_bin = bin(num)[3:]
        orig_len = len(raw_bin)
        pos_rep = '0b'+'0'*(32-orig_len)+raw_bin
        inv = invert(pos_rep)
        res,msb_carry_out,over_flow = add_32(inv,'0b00000000000000000000000000000001')
        return res
    else:
        return '0b00000000000000000000000000000000'

def s_bin_se_64(num):
    """converts an int to a 64 bit binary number. Automatically converts negative ints to twos complement representation."""
    assert isinstance(num,int)
    if num > 0:
        return u_bin_se_64(num)
    elif num < 0:
        raw_bin = bin(num)[3:]
        orig_len = len(raw_bin)
        pos_rep = '0b'+'0'*(64-orig_len)+raw_bin
        inv = invert(pos_rep)
        res,msb_carry_out,over_flow = add_64(inv,'0b'+'0'*63+'1')
        return res
    else:
        return '0b'+'0'*64

def s_bin_to_int_32(bin_str):
    """converts 32 bit binary strings in twos complement representation into an integer"""
    assert isinstance(bin_str,str)
    assert len(bin_str) == 34
    raw_bin_str = bin_str[2:]
    if raw_bin_str[0] == '0':
        return int(bin_str,2)
    else:
        inv = invert(bin_str)
        pos_rep = add_32(inv,s_bin_se_32(1))[0]
        return -1*int(pos_rep,2)

def s_multiply_32(a,b):
    """multiplies two signed 32 bit strings and returns a 64 bit string"""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    a_int = s_bin_to_int_32(a)
    b_int = s_bin_to_int_32(b)
    res_int = a_int*b_int
    return s_bin_se_64(res_int)

def s_multiply_32_2(a,b):
    """multiplies two signed 32 bit strings and returns two 32 bit bit strings"""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    a_int = s_bin_to_int_32(a)
    b_int = s_bin_to_int_32(b)
    res_int = a_int*b_int
    res_64 = s_bin_se_64(res_int)
    return res_64[:34],'0b'+res_64[34:]

def s_multiply_ls_32(a,b):
    """multiplies two signed 32 bit strings and returns the least significant 32 bits of the result"""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    a_int = s_bin_to_int_32(a)
    b_int = s_bin_to_int_32(b)
    res_int = a_int*b_int
    return '0b'+s_bin_se_64(res_int)[-32:]

def u_multiply_32(a,b):
    """multiplies two unsigned 32 bit strings and returns a 64 bit string"""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    a_int = int(a,2)
    b_int = int(b,2)
    res_int = a_int*b_int
    return u_bin_se_64(res_int)

def u_multiply_32_2(a,b):
    """multiplies two unsigned 32 bit strings and two 32 bit bit strings"""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    a_int = int(a,2)
    b_int = int(b,2)
    res_int = a_int*b_int
    res_64 = u_bin_se_64(res_int)
    return res_64[:34],'0b'+res_64[34:]

def s_divide_32(a,b):
    """returns a/b, signed integer division."""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    a_int = s_bin_to_int_32(a)
    b_int = s_bin_to_int_32(b)
    res_int = a_int/b_int
    return s_bin_se_32(res_int)

def u_divide_32(a,b):
    """returns a/b, unsigned integer division."""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    a_int = int(a,2)
    b_int = int(b,2)
    res_int = a_int/b_int
    return u_bin_se_32(res_int)

def l_shift_32(a, shift_val):
    """returns 32 bit string shifted left by int shift_val"""
    assert isinstance(a,str) and isinstance(shift_val,int)
    assert len(a) == 34
    assert shift_val <= 32
    assert len('0b'+a[2+shift_val:]+'0'*shift_val) == 34
    return '0b'+a[2+shift_val:]+'0'*shift_val

def r_shift_32_log(a,shift_val):
    """returns 32 bit string shifted right by int shift_val"""
    assert isinstance(a,str) and isinstance(shift_val,int)
    assert len(a) == 34
    assert shift_val <= 32
    return '0b'+'0'*shift_val+a[2:-shift_val]
    assert len('0b'+'0'*shift_val+a[2:-shift_val]) == 34

def r_shift_32_ari(a,shift_val):
    """returns 32 bit string shifted right by int shift_val"""
    assert isinstance(a,str) and isinstance(shift_val,int)
    assert len(a) == 34
    assert shift_val <= 32
    if a[2] == '0':
        assert len('0b'+'0'*shift_val+a[2:-shift_val]) == 34
        return '0b'+'0'*shift_val+a[2:-shift_val]
    else:
        assert len('0b'+'1'*shift_val+a[2:-shift_val]) == 34
        return '0b'+'1'*shift_val+a[2:-shift_val]

def clz_32(a):
    """counts leading zeros of a 32 bit binary str, returns unsigned 32 bit str. Ignores the signed MSB"""
    raw_str = a[2:]
    counter = 0
    index = 1
    str_len = len(raw_str)
    while index != str_len and raw_str[index] != '1':
        counter += 1
        index += 1
    return s_bin_se_32(counter)

def abs_32(a):
    """returns positive twos complement representation of binary str"""
    assert len(a) == 34
    if a[2] == '1':
        return s_multiply_ls_32(a,s_bin_32(-1))
    else:
        return a

def iq30_to_float(a):
    """converts a iq30 number to a float"""
    assert isinstance(a,str)
    assert len(a) == 34
    sign_bit = a[2]
    if sign_bit == '1':
        a = s_multiply_ls_32(a,s_bin_se_32(-1))
    raw_num = a[4:]
    float_res = 0
    for i, bit in enumerate(raw_num):
        float_res += 2**-(i+1)*int(bit,2)
    if sign_bit == '0':
        return float_res
    else:
        return float_res*-1

def float_to_iq30(a):
    """converts a float to an iq30 number"""
    abs_a = abs(a)
    assert abs_a <= 1
    iq30 = '0b'+'0'+31*'0'
    iq30_l = list(iq30)
    remainder = abs_a
    for i in range(30):
        if 2**-(i+1) <= remainder:
            iq30_l[i+4] = '1'
            exp = -(i+1)
            remainder -= 2**-(i+1)
    pos_rep = ''.join(iq30_l)
    if a >= 0:
        return pos_rep
    else:
        return s_multiply_ls_32(pos_rep,s_bin_se_32(-1))

def iq29_to_float(a):
    """converts a iq29 number to a float"""
    assert isinstance(a,str)
    assert len(a) == 34
    sign_bit = a[2]
    raw_num = a[5:]
    float_res = 0
    if sign_bit == '0':
        for i, bit in enumerate(raw_num):
            float_res += 2**-(i+1)*int(bit,2)
    else:
        for i, bit in enumerate(raw_num):
            float_res -= 2**-(i+1)*int(bit,2)
    return float_res

def float_to_iq29(a):
    """converts a float to an iq29 number"""
    abs_a = abs(a)
    assert abs_a <= 1
    if a >= 0:
        iq29 = '0b'+'0'+31*'0'
    else:
        iq29 = '0b'+'1'+31*'0'
    iq29_l = list(iq29)
    remainder = abs_a
    for i in range(29):
        if 2**-(i+1) <= remainder:
            iq29_l[i+5] = '1'
            exp = -(i+1)
            remainder -= 2**-(i+1)
    return ''.join(iq29_l)

def and_32(a,b):
    """returns 32 bit and of two bit strings"""
    assert isinstance(a,str) and isinstance(b,str)
    assert len(a) == 34 and len(b) == 34
    res = ''
    for a_char,b_char in zip(a[2:],b[2:]):
        if a_char == b_char and a_char == '1':
            res += '1'
        else:
            res += '0'
    assert len('0b'+res) == 34
    return '0b'+res

def rotate_r_ext(a,shift_in_val):
    """returns 32 bit string shifted right by one place. The value shifted in on the left is specified as an integer, 0 or 1."""
    assert isinstance(a,str) and isinstance(shift_in_val,int)
    assert len(a) == 34
    assert len('0b'+str(shift_in_val)+a[2:-1]) == 34
    return '0b'+str(shift_in_val)+a[2:-1]

def is_int_str(val):
    """returns whether a value is an integer string or not"""
    try: 
        to_int(val)
        return True
    except Exception:
        return False

def to_int(val):
    """changes val to an integer, where val is a decimal, binary, or hex string"""
    assert val[0] == "#"
    val = val[1:]
    if val.isdigit():
        return int(val)
    if val[:2] == '0b':
        return int(val,2)
    if val[:2] == '0x':
        return int(val,16)
    raise Exception

class simulator():
    """simulates an arm program given to it as a text file"""
    def __init__(self,txt):
        self.txt = txt
        self.prog = self.convert_txt(self.txt)
        #prog is a list of strings that will be executed, with the exception that it is an integer if we are meant to jump at that point in execution
        self.run_prog(self.prog)
        self.LR = None
        self.n_flag = None
        self.z_flag = None
        self.c_flag = None
        self.v_flag = None

    def convert_txt(self,txt_file):
        """converts arm assembly text file to list of python instructions"""
        content = []
        with open(txt_file) as f:
            content = f.readlines()
        #strip leading and trailing whitespaces
        for i, line in enumerate(content):
            content[i] = line.strip()
        #remove commented lines and unneeded IT lines that tell ARM processor that conditional statements are about to be executed
        no_comments = []
        for i, line in enumerate(content):
            try:
                if line[0] != '"' and line[:2] != 'IT':
                    no_comments.append(line)
            except IndexError:
                print ("Could not parse line "+str(i))
        content = no_comments
        #deal with jump labels
        no_labels = []
        labels = []
        for i, line in enumerate(content):
            if re.search(r"\s", line) is None:
                #matches only match at beginning of string!
                if re.match(r'\A[\w-]+\Z', line) is None:
                    raise Exception("Jump labels can only have alphanumeric chars and underscores!")
                labels.append((line,i))
            else:
                no_labels.append(line)
        for i, (label, index) in enumerate(labels):
            for j, line in enumerate(no_labels):
                no_labels[j] = line.replace(label,str(index-i-1))
        content = no_labels
        #remove curly braces and replace periods w/ underscores
        for i, line in enumerate(content):
            content[i] = re.sub(r'[{}]','',line).replace(".","_")
        #turn assembly commands into function calls, dealing with conditional commands as well
        for i, line in enumerate(content):
            command = line.split()[0]
            if VALID_COMMAND_REGEX.match(command) is None:
                raise Exception("Command %s is not a valid command or is not implemented!"%command)
            stripped_command,modifiers = VALID_COMMAND_REGEX.findall(command)[0]
            if modifiers == "" or modifiers == "_L" or modifiers == "_W":
                    content[i] = 'self.'+command+'("'+line.replace(command,"").lstrip()+'")'
            else:
                if CONDITIONAL_MODIFIER_REGEX.match(modifiers) is not None:
                    conditional,text_after = CONDITIONAL_MODIFIER_REGEX.findall(modifiers)[0]
                    content[i] = 'self.handle_conditionals("'+stripped_command+text_after+'","'+conditional+'","'+line.replace(command,"").lstrip()+'")'
                else:
                    print (modifiers)
                    print (line)
                    raise Exception("Conditional %s is not valid or not implemented!"%conditional)
        #replace LR and SP with appropriate registers
        for i, line in enumerate(content):
            content[i] = line.replace("LR","R14").replace("SP","R13")
        return content

    def ADD(self,args):
        """sets reg_a = reg_b + reg_c with 3 args, or reg_a = reg_a + reg_b with two arguments"""
        args_split = self.split_args(args)
        if len(args_split) < 3:
            reg_or_num_c =  None
            reg_a,reg_b = args_split
        else:
            reg_a,reg_b,reg_or_num_c = args_split
        if reg_or_num_c is not None:
            if is_int_str(reg_or_num_c):
                c = u_bin_se_32(to_int(reg_or_num_c))
            else:
                c = self.regs[int(reg_or_num_c[1:])]
            b = self.regs[int(reg_b[1:])]
            print (b)
            print (c)
            self.regs[int(reg_a[1:])],o,c = add_32(b,c)
        else:
            a = self.regs[int(reg_a[1:])]
            b = self.regs[int(reg_b[1:])]
            self.regs[int(reg_a[1:])],o,c = add_32(a,b)

    def B(self, branch_index):
        """jumps PC to branch_index"""
        self.PC = int(branch_index)

    def BX(self, reg):
        """jumps PC to val stored in input reg, if there's no value stored in input, then PC jumps to exit program"""
        if self.regs[int(reg[1:])] is None:
            self.PC = len(self.prog)
            #Exits program
        else:
            self.PC = self.regs[int(reg[1:])]

    def CLZ_W(self,args):
        """stores number of leading zeros of val at register b into register a"""
        reg_a, reg_b = self.split_args(args)
        self.regs[int(reg_a[1:])] = clz_32(self.regs[int(reg_b[1:])])

    def CMP(self,args):
        """sets equality (z) flag based on whether or not reg == num_or_reg. sets sign flag (n) by XORing the MSBs of the binary representations of the two operands. Interprets arguments as unsigned integers"""
        reg, num_or_reg = self.split_args(args)
        if is_int_str(num_or_reg): #if second arg is a number
            a = self.regs[int(reg[1:])]
            b = u_bin_se_32(to_int(num_or_reg))
            res,msb_carry_out,over_flow = subtract_32(a,b)
            print (over_flow)
        else: #second argument is a register
            a = self.regs[int(reg[1:])]
            b = self.regs[int(num_or_reg[1:])]
            res,msb_carry_out,over_flow = subtract_32(a,b)
        self.c_flag = int(msb_carry_out,2)
        self.v_flag = int(over_flow,2)
        if res[2] == '1': #a-b is negative
            self.n_flag = 1
        else:
            self.n_flag = 0
        if s_bin_to_int_32(res) == 0: #a-b is zero
            self.z_flag = 1
        else:
            self.z_flag = 0

    def handle_conditionals(self,command,conditional,args):
        """executes statements conditionally depending on how flags are set"""
        if conditional == "EQ":
            if self.z_flag == 1:
                print ("self."+command+"('"+args+"')")
                exec("self."+command+"('"+args+"')")

        elif conditional == "GE":
            if self.n_flag == self.z_flag:
                print ("self."+command+"('"+args+"')")
                exec("self."+command+"('"+args+"')")

        elif conditional == "LE":
            if self.z_flag == 1 or self.n_flag != self.z_flag:
                print ("self."+command+"('"+args+"')")
                exec("self."+command+"('"+args+"')")

        elif conditional == "MI":
            if self.n_flag == 1:
                print ("self."+command+"('"+args+"')")
                exec("self."+command+"('"+args+"')")

        elif conditional == "NE":
            if self.z_flag == 0:
                print ("self."+command+"('"+args+"')")
                exec("self."+command+"('"+args+"')")

        else:
            raise Exception("This conditional statement not implemented yet!")

    def LSL_W(self,args):
        """shifts reg_b by amount stored in reg_c (logical shift left), and stores result into reg_a"""
        reg_a,reg_b,reg_c = self.split_args(args)
        b = self.regs[int(reg_b[1:])]
        c = self.regs[int(reg_c[1:])]
        self.regs[int(reg_a[1:])] = l_shift_32(b,int(c,2))

    def MLS_W(self,args):
        """takes last 32 bits of reg_b*reg_c, subtracts it from reg_d, stores result into reg_a"""
        reg_a,reg_b,reg_c,reg_d = self.split_args(args)
        b = self.regs[int(reg_b[1:])]
        c = self.regs[int(reg_c[1:])]
        d = self.regs[int(reg_d[1:])]
        self.regs[int(reg_a[1:])],c,o = subtract_32(d,s_multiply_ls_32(b,c))   

    def MOV(self,args):
        """moves number to register. Not sure if there's a difference between MOV and MOV_W in arm assembly, so the functions were left separate."""
        args_split = self.split_args(args)
        reg = args_split[0]
        num = args_split[1]
        self.regs[int(reg[1:])] = u_bin_se_32(to_int(num))

    def MOV_W(self,args):
        """moves number to register"""
        args_split = self.split_args(args)
        reg = args_split[0]
        num = args_split[1]
        self.regs[int(reg[1:])] = u_bin_se_32(to_int(num))

    def NEG(self,args):
        """multiples value in reg_b by negative 1 and places result into reg_a"""
        reg_a,reg_b = self.split_args(args)
        b = self.regs[int(reg_b[1:])]
        res = s_multiply_ls_32(b,s_bin_se_32(-1))
        self.regs[int(reg_a[1:])] = res
        #if self.n_flag == 1:
        #    if b[2] == "0": #value to be inverted is positive
        #        inv = invert(b)
        #        res,msb_carry_out,over_flow = add_32(inv,u_bin_se_32(1))
        #        self.regs[int(reg_a[1:])] = res
        #    if b[2] == "1": #value to be inverted is negative
        #        res,msb_carry_out,over_flow = subtract_32(b,u_bin_se_32(1))
        #        inv = invert(res)
        #        self.regs[int(reg_a[1:])] = inv

    def POP(self,registers):
        """takes any number of register arguments in a string and pops stack into those registers, but only if the last comparison of a,b set flags indicating that a >= b"""
        reg_list = registers.split(',')
        for i in range(len(reg_list)):
            if reg_list[-i] != 'PC':
                self.regs[int(reg_list[-i][1:])] = self.stack[-i]
            else:
                self.PC = self.stack[-i]

    def PUSH(self,registers):
        """takes any number of register arguments in a string and pushes those register values to the stack"""
        reg_list = registers.split(',')
        for reg in reg_list:
            self.stack.append(self.regs[int(reg[1:])])

    def RSB_W(self,args):
        """sets reg_a = reg_c - reg_b"""
        reg_a,reg_b,reg_or_num_c = self.split_args(args)
        if is_int_str(reg_or_num_c):
            c = u_bin_se_32(to_int(reg_or_num_c))
        else:
            c = self.regs[int(reg_or_num_c[1:])]
        b = self.regs[int(reg_b[1:])]
        self.regs[int(reg_a[1:])],o,c = subtract_32(c,b)

    def split_args(self,args):
        split_list =  re.split(r'\s*,|,\s*|\s',args)
        return filter(None,split_list)

    def SUB_W(self,args):
        """sets reg_a = reg_b - reg_c"""
        reg_a,reg_b,reg_or_num_c = self.split_args(args)
        if is_int_str(reg_or_num_c):
            c = u_bin_se_32(to_int(reg_or_num_c))
        else:
            c = self.regs[int(reg_or_num_c[1:])]
        b = self.regs[int(reg_b[1:])]
        self.regs[int(reg_a[1:])],o,c = subtract_32(b,c)

    def TEQ_W(self,args):
        """sets equality (z) flag based on whether or not reg == num_or_reg. sets sign flag (n) by XORing the MSBs of the binary representations of the two operands. Interprets value in register and the second argument as unsigned integers"""
        reg,num_or_reg = self.split_args(args)
        if is_int_str(num_or_reg): #if second arg is a number
            if int(self.regs[int(reg[1:])],2) == to_int(num_or_reg):
                self.z_flag = 1
            else:
                self.z_flag = 0

            if self.regs[int(reg[1:])][2] == u_bin_se_32(to_int(num_or_reg))[2]:
                self.n_flag = 0
            else:
                self.n_flag = 1
        else: #second argument is a register
            if int(self.regs[int(reg[1:])],2) == int(self.regs[int(num_or_reg[1:])],2):
                self.z_flag = 1
            else:
                self.z_flag = 0
                    
            if self.regs[int(reg[1:])][2] == self.regs[int(num_or_reg[1:])][2]:
                self.n_flag = 0
            else:
                self.n_flag = 1

    def UDIV_W(self,args):
        """does a unsigned divide of reg_b/reg_c and stores result in reg_a"""
        reg_a,reg_b,reg_c = self.split_args(args)
        b = self.regs[int(reg_b[1:])]
        c = self.regs[int(reg_c[1:])]
        self.regs[int(reg_a[1:])] = u_divide_32(b,c)

    def UMULL(self,registers):
        """takes 4 arguments in one string seperated by commas, saves unsigned multiply in the first two args"""
        args = registers.split(',')
        assert len(args) == 4
        c = self.regs[int(args[2][1:])]
        d = self.regs[int(args[3][1:])]
        self.regs[int(args[1][1:])],self.regs[int(args[0][1:])] = u_multiply_32_2(c,d)

    def run_prog(self,prog):
        """takes a list of strings that python executes"""
        self.regs = [None]*32 #register list
        self.PC = 0
        self.stack = []
        prog_len = len(prog)
        while self.PC < prog_len and self.PC is not None:
            print (prog[self.PC])
            exec (prog[self.PC])
            print (self.regs[0])
            if self.PC is not None:
                self.PC+=1
        print ("Simulation finished!")

if __name__ == "__main__":
    for arg in sys.argv:
        assert os.path.isfile(arg)
    s = simulator(sys.argv[1])
    print (s.regs[0])
    print (iq30_to_float(s.regs[0]))