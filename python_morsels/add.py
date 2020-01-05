def add (matrix1, matrix2):
    solution = []
    i = 0
    for m1 in matrix1:
        j = 0
        m2 = matrix2[i]
        sum = []
        for a in m1:
            b = m2[j]
            sum.append(a+b)
            j += 1
        i += 1
        solution.append(sum)
    return solution
