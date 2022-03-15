class Abstract:
    def __init__(self, name, term):
        super().__init__()
        self.name = name
        self.childs = [term.copy()]

    def __str__(self):
        txt = f"${self.name}"
        c = self.childs[0]
        while isinstance(c, Abstract):
            txt += f" {c.name}"
            c = c.childs[0]
        return f"{txt}.{c}"

    def copy(self):
        return Abstract(self.name, self.childs[0].copy())

class Apply:
    def __init__(self, L_term, R_term):
        super().__init__()
        self.childs = [L_term.copy(), R_term.copy()]
    
    def __str__(self):
        L , R = self.childs[0], self.childs[1]
        if isinstance(L, Variable) and isinstance(R, Variable):
            return f"{L} {R}"
        elif isinstance(L, Variable) and isinstance(R, Apply):
            return f"{L} ({R})"
        elif isinstance(L, Variable) and isinstance(R, Abstract):
            return f"{L} ({R})"
        elif isinstance(L, Apply) and isinstance(R, Variable):
            return f"{L} {R}"
        elif isinstance(L, Apply) and isinstance(R, Apply):
            return f"{L} ({R})"
        elif isinstance(L, Apply) and isinstance(R, Abstract):
            return f"{L} ({R})"
        elif isinstance(L, Abstract) and isinstance(R, Variable):
            return f"({L}) {R}"
        elif isinstance(L, Abstract) and isinstance(R, Apply):
            return f"({L}) ({R})"
        elif isinstance(L, Abstract) and isinstance(R, Abstract):
            return f"({L}) ({R})"
        
    def copy(self):
        return Apply(self.childs[0].copy(), self.childs[1].copy())

class Variable:
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __str__(self):
        return self.name

    def copy(self):
        return Variable(self.name)

def replace(node, term, name):
    if isinstance(node, Variable):
        if node.name == name:
            return term.copy()
        return node.copy()
    elif isinstance(node, Apply):
        L = replace(node.childs[0], term, name)
        R = replace(node.childs[1], term, name)
        return Apply(L, R)
    elif isinstance(node, Abstract):
        if node.name == name:
            return node.copy()
        return Abstract(node.name, replace(node.childs[0], term, name))

def can_reduce(term):
    if isinstance(term, Apply):
        L = term.childs[0]
        R = term.childs[1]
        if isinstance(L, Apply):
            return can_reduce(L)
        elif isinstance(L, Abstract):
            return True
        elif isinstance(R, Apply):
            return can_reduce(R)
        else:
            return False
    elif isinstance(term, Abstract):
        return can_reduce(term.childs[0])
    else:
        False

# TODO : handle variable rename
def one_step_reduce_LL(term):
    if isinstance(term, Apply):
        L = term.childs[0]
        R = term.childs[1]
        if isinstance(L, Apply):
            return Apply(one_step_reduce_LL(L), R)
        elif isinstance(L, Abstract):
            return replace(L.childs[0], R, L.name)
        elif isinstance(R, Apply):
            return Apply(L, one_step_reduce_LL(R))
        else:
            return term
    elif isinstance(term, Abstract):
        return Abstract(term.name, one_step_reduce_LL(term.childs[0]))
    else:
        return term

def reduce_LL(term):
    t = term.copy()
    while can_reduce(t):
        t = one_step_reduce_LL(t)
    return t

def reduce_LL_verbose(term):
    t = term.copy()
    print(f"{t}")
    while can_reduce(t):
        t = one_step_reduce_LL(t)
        print(f"-> {t}")
    return t

def create_number(n):
    T = Variable("x")
    for i in range(n):
        T = Apply(Variable("f"), T.copy())
    return Abstract("f", Abstract("x", T))


pred = Abstract("n", Abstract("f", Abstract("x", Apply(Apply(Apply(Variable("n"), Abstract("g", Abstract("h", Apply(Variable("h"), Apply(Variable("g"), Variable("f")))))), Abstract("u", Variable("x"))), Abstract("z", Variable("z"))))))
succ = Abstract("n", Abstract("f", Abstract("x", Apply(Variable("f"), Apply(Apply(Variable("n"), Variable("f")), Variable("x"))))))
true = Abstract("x", Abstract("y", Variable("x")))
false = Abstract("x", Abstract("y", Variable("y")))
ifelse = Abstract("x", Variable("x"))
turing = Apply( Abstract("x", Abstract("y", Apply(Variable("y"),Apply(Apply(Variable("x"), Variable("x")),Variable("y"))))),  Abstract("x", Abstract("y", Apply(Variable("y"),Apply(Apply(Variable("x"), Variable("x")),Variable("y"))))))

if __name__ == "__main__":
    print(f"pred := {pred}")
    print(f"5 := {create_number(5)}")
    n = 5
    predn = Apply(pred, create_number(n))
    print(f"pred {n} := {predn}")
    reduce_LL_verbose(predn)

