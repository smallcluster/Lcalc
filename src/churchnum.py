import term

def gen_number(n):
    f = term.Variable("f")
    x = term.Variable("x")
    t = x
    for i in range(n):
        t = term.Apply(f, t)
    return term.Abstract(f, term.Abstract(x, t))

def get_succ():
    n = term.Variable("n")
    f = term.Variable("f")
    x = term.Variable("x")
    return term.Abstract(n, term.Abstract(f, term.Abstract(x, term.Apply(f, term.Apply(term.Apply(n, f), x)))))

def get_pred():
    n = term.Variable("n")
    f = term.Variable("f")
    x = term.Variable("x")

    u = term.Variable("u")
    z = term.Variable("z")
    g = term.Variable("g")
    h = term.Variable("h")
    w = term.Variable("w")
    return term.Abstract(n, term.Abstract(f, term.Abstract(x, term.Apply( term.Apply(term.Apply(n, term.Abstract(g, term.Abstract(h, term.Apply(h, term.Apply(g, f))))), term.Abstract(z, x)) , term.Abstract(u, u)))))

def get_number(t):
    if t.type != term.TermType.ABSTRACT:
        return None
    ab1 = t

    # id =eta 1, check this special case
    if t.right == t.var:
        return 1

    # second abstract
    if t.right.type != term.TermType.ABSTRACT:
        return None
    ab2 = t.right
    # 0 or n :
    if ab2.right.type == term.TermType.ABSTRACT:
        return None
    t = ab2.right
    n = 0
    while t.type == term.TermType.APPLY:
        if t.left != ab1.var:
            return None
        n += 1
        t = t.right
    if t == ab2.var:
            return n
    return None

def is_number(t):
    return get_number(t) != None

    