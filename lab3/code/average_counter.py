from fractions import Fraction

import ss_function as ss_f


# 设置模数p
p = 1000000007

# 随机选取两个参与方，例如student2和student3，获得d2,d3，从而恢复出d=a+b+c
# 读取d2,d3
d_23 = []
for i in range(2, 4):
    with open(f"d_{i}.txt", "r") as f:
        d_23.append(int(f.read()))

# 加法重构获得d
d = ss_f.restructure_polynomial([2, 3], d_23, 2, p)

# 计算平均值average=d/3
average = Fraction(d, 3)
print(f"三个数据的和为：{d}")
if average.denominator == 1:
    print(f"三个数据的平均值为：{average.numerator}")
else:
    print(f"三个数据的平均值为：{average}，约为：{float(average)}")
