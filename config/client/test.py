def pfh(*numbers):
    s=0
    for i in numbers:
        s = s+i*i
    return s
print(pfh(4))
print(pfh(4,5))
list1 = [2,3,4,5]
print(pfh(*list1))

