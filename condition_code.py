condition_dict = {
    "eq",                   #Equal Z = 1
    "ne",                   #Not equal Z = 0
    "cs", "hs"              #Carry set, Unsigned higher or same C = 1
    "cc", "lo"              #Carry clear, Unsigned lower C = 0
    "mi",                   #Minus, Negative N = 1
    "pl",                   #Plus, Positive or zero N = 0
    "vs",                   #Overflow V = 1
    "vc",                   #No overflow V = 0
    "hi",                   #Unsigned higher C = 1 / Z = 0
    "ls",                   #Unsigned lower or same C = 0 0 Z = 1
    "ge",                   #Signed greater or equal N = V
    "lt",                   #Signed less N ! V
    "gt",                   #Signed greater Z = 0 / N = V
    "le",                   #Signed less or equal Z = 1 0 N ! V
    "al", "<omit>"          #Always any
}

#Giải thích