.text
push {r0, r1, r2, r3, r4, r5, r6, r7}
ldr r0, =array
ldr r1, =length
ldr r1, [r1]
sub r2, r1, #1
mov r3, #0
outer: 
    mov r4, r2
inner:  
    sub r5, r4, #1
    lsl r4, r4, #2
    lsl r5, r5, #2
    ldr r6, [r0, r4]
    ldr r7, [r0, r5]

    cmp r6, r7
    bge no_swap

    str r7, [r0, r4]
    str r6, [r0, r5]

no_swap:
    lsr r4, r4, #2
    lsr r5, r5, #2
    sub r4, r4, #1
    cmp r4, r3
    bgt inner

    add r3, r3, #1
    cmp r3, r2
    blt outer

done_sort:
   pop {r0, r1, r2, r3, r4, r5, r6, r7}

.data
array:  .word 5, 1, 4, 2, 8, -7
length: .word 6