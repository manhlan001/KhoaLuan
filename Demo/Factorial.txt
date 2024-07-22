.data
num: .word 5
result: .word 0

.text
start:
    push {r0, r1, r2, r3, r4, r5, r6, r7}
    mov r0, #1
    mov r1, #1
    ldr r2, =num
    ldr r2, [r2]
    ldr r3, =result
    mov r4, #0

calculate_factorial:
    cmp r1, r2
    bgt store_result

    mov r5, r1
    mov r6, #1
factorial_loop:
    cmp r5, #0
    beq add_to_sum
    mul r6, r6, r5
    sub r5, r5, #1
    b factorial_loop

add_to_sum:
    add r4, r4, r6
    add r1, r1, #1
    b calculate_factorial

store_result:
    str r4, [r3]
    pop {r0, r1, r2, r3, r4, r5, r6, r7}