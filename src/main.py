import term
import churchnum as cn

succ = cn.get_succ()
pred = cn.get_pred()

n2 = cn.gen_number(2)
n3 = term.Apply(succ, n2)

print(f"2 = {n2}")
print(f"succ = {succ}")
print(f"succ 2 = {n3}")
n3.reduce_LO(True)
print("= 3")

n = 3
a = term.Apply(pred, cn.gen_number(n))
print(f"pred = {pred}")
print(f"pred {n} = {a}")
a = a.reduce_LO(True)
print(f"= {cn.get_number(a)}")


n2 = cn.gen_number(2)
nn2 = term.Apply(pred, cn.gen_number(3)).reduce_LO()

if n2.is_equals(nn2):
    print(f"{cn.get_number(n2)} == pred 3 == {cn.get_number(nn2)}")
else:
    print(f"{cn.get_number(n2)} != pred 3 != {cn.get_number(nn2)}")