from enum import Enum

class TermType(Enum):
    ABSTRACT = 1
    APPLY = 2
    VARIABLE = 3

class Term:
    def __init__(self, left, right, type):
        self.left = left
        self.right = right
        self.type = type

    def beta_reduce(self, verbose=False):
        t, oldt = self, self
        n = 0
        if verbose:
            print(f"{n} -> {t}")
        # do ... while
        t, reduced = t.one_step_beta_reduce()
        if t == None or not reduced:
            if verbose:
                print(f"1 -> {oldt}")
            return (oldt, n)
        while reduced:
            n += 1
            oldt = t
            if verbose:
                print(f"{n} -> {t}")
            t, reduced = t.one_step_beta_reduce()
            
        return (oldt, n)

    def eta_reduce(self, verbose=False):
        t, oldt = self, self
        n = 0
        if verbose:
            print(f"{n} -> {t}")
        # do ... while
        t, reduced = t.one_step_eta_reduce()
        if t == None or not reduced:
            if verbose:
                print(f"1 -> {oldt}")
            return (oldt, n)
        while reduced:
            n += 1
            oldt = t
            if verbose:
                print(f"{n} -> {t}")
            t, reduced = t.one_step_eta_reduce()
        return (oldt, n)
    
    def reduce(self, verbose=False):
        t, nb = self.beta_reduce(verbose)
        t, ne = t.eta_reduce(verbose)
        return (t, nb+ne)

    def __str__(self) -> str:
        vars = self.get_abstracted_vars()
        vars.reverse()
        names = {x.name for x in vars}
        d = {n:[] for n in names}
        for v in vars :
            d[v.name].append(v)
        # rename
        for n in d.keys():
            v = d[n]
            for i in range(1, len(v)):
                v[i].name = n+str(i)
        # get text rep
        txt = self.to_string()

        # rollback renaming
        # prevent variables from accumulating numbers
        for n in d.keys():
            v = d[n]
            for i in range(1, len(v)):
                v[i].name = n

        return txt

    def is_equals(self, term):
        linkvar1 = []
        linkvar2 = []
        queue1 = []
        queue2 = []
        queue1.append(self)
        queue2.append(term)
        while len(queue1) > 0 and len(queue2) > 0:
            t1 = queue1.pop(0)
            t2 = queue2.pop(0)
            # Not the same type
            if t1.type != t2.type:
                return False
            # Variable
            if t1.type == TermType.VARIABLE:
                # 2 linked
                if t1 in linkvar1 and t2 in linkvar2:
                    index1 = linkvar1.index(t1)
                    index2 = linkvar2.index(t2)
                    if index1 != index2:
                        return False
                # 2 free
                elif t1 not in linkvar1 and t2 not in linkvar2:
                    if t1 != t2:
                        return False
                # no match
                else:
                    return False
            # Abstract
            elif t1.type == TermType.ABSTRACT:
                linkvar1.append(t1.var)
                linkvar2.append(t2.var)
                queue1.append(t1.right)
                queue2.append(t2.right)
            # Apply
            elif t1.type == TermType.APPLY:
                queue1.append(t1.left)
                queue1.append(t1.right)
                queue2.append(t2.left)
                queue2.append(t2.right)
        if len(queue1) != len(queue2):
            return False
        return True

    # Abstract functions
    def copy(self):
        pass
    def get_abstracted_vars(self):
        pass
    def to_string(self):
        pass
    def can_beta_reduce(self) -> bool:
        pass
    def one_step_beta_reduce(self):
        pass
    def can_eta_reduce(self) -> bool:
        pass
    def one_step_eta_reduce(self):
        pass
    def replace(self, var, term):
        pass
    def get_abstracted_vars(self):
        pass
    def is_var_in(self, var):
        pass
    
class Abstract(Term):
    def __init__(self, var, term):
        super().__init__(None, term, TermType.ABSTRACT)
        self.var = var

    def copy(self):
        var = Variable(self.var.name)
        return Abstract(var, self.right.replace(self.var, var))

    def to_string(self) -> str:
        txt = '\u03BB'+str(self.var)
        next = self.right
        while next.type == TermType.ABSTRACT:
            txt += f" {next.var}"
            next = next.right
        return f"{txt}.{next.to_string()}"

    # def can_beta_reduce(self) -> bool:
    #     return self.right.can_beta_reduce()

    def replace(self, var, term):
        if self.var == var:
            return self.right.replace(var, term)
        t = self.copy()
        return Abstract(t.var, t.right.replace(var, term))


    def one_step_beta_reduce(self):
        t = self.copy()
        r = t.right.one_step_beta_reduce()
        return (Abstract(t.var, r[0]), True) if r[1] else (None, False)

    def get_abstracted_vars(self):
        return self.right.get_abstracted_vars()+[self.var]

    # def can_eta_reduce(self) -> bool:
    #     if self.right.type == TermType.APPLY and self.right.right == self.var and not self.right.left.is_var_in(self.var):
    #         return True
    #     return self.right.can_eta_reduce()
    
    def one_step_eta_reduce(self):
        if self.right.type == TermType.APPLY and self.right.right == self.var and not self.right.left.is_var_in(self.var):
            return (self.right.left, True)
        t = self.copy()
        r = t.right.one_step_eta_reduce()
        return (Abstract(t.var, r[0]), True) if r[1] else (None, False)

    def is_var_in(self, var):
        return self.right.is_var_in(var)

class Apply(Term):
    def __init__(self, left, right):
        super().__init__(left, right, TermType.APPLY)

    def copy(self):
        return Apply(self.left.copy(), self.right.copy())
    
    def to_string(self) -> str:
        if (self.left.type == TermType.VARIABLE or self.left.type == TermType.APPLY ) and self.right.type == TermType.VARIABLE:
            return f"{self.left.to_string()} {self.right.to_string()}"
        elif self.left.type == TermType.VARIABLE and (self.right.type == TermType.ABSTRACT or  self.right.type == TermType.APPLY):
            return f"{self.left.to_string()} ({self.right.to_string()})"
        if self.left.type == TermType.ABSTRACT and self.right.type == TermType.VARIABLE:
            return f"({self.left.to_string()}) {self.right.to_string()}"
        elif self.left.type == TermType.ABSTRACT and (self.right.type == TermType.ABSTRACT or  self.right.type == TermType.APPLY):
            return f"({self.left.to_string()}) ({self.right.to_string()})"
        elif self.left.type == TermType.APPLY and (self.right.type == TermType.ABSTRACT or  self.right.type == TermType.APPLY):
            return f"{self.left.to_string()} ({self.right.to_string()})"


    # def can_beta_reduce(self) -> bool:
    #     if self.left.type == TermType.ABSTRACT:
    #         return True
    #     elif self.left.can_beta_reduce():
    #         return True
    #     return self.right.can_beta_reduce()

    # def can_eta_reduce(self) -> bool:
    #     if self.left.can_eta_reduce():
    #         return True
    #     return self.right.can_eta_reduce()

    def one_step_eta_reduce(self):
        r = self.left.one_step_eta_reduce()
        if r[1]:
            return (Apply(r[0], self.right), True)
        else:
            rr = self.right.one_step_eta_reduce()
            return (Apply(self.left, rr[0]), rr[1])

    def replace(self, var, term):
        return Apply(self.left.replace(var, term), self.right.replace(var, term))

    def one_step_beta_reduce(self):
        if self.left.type == TermType.ABSTRACT:
            return (self.left.replace(self.left.var, self.right), True)
        r = self.left.one_step_beta_reduce()
        if r[1]:
            return (Apply(r[0], self.right), True)
        else:
            rr = self.right.one_step_beta_reduce()
            return  (Apply(self.left, rr[0]), rr[1])

    def get_abstracted_vars(self):
        return self.left.get_abstracted_vars() + self.right.get_abstracted_vars()

    def is_var_in(self, var):
        return self.left.is_var_in(var) or self.right.is_var_in(var)

class Variable(Term):
    def __init__(self, name):
        super().__init__(None, None, TermType.VARIABLE)
        self.name = name

    def copy(self):
        return self
    
    def __str__(self) -> str:
        return self.name

    def to_string(self):
        return self.name
    
    # def can_beta_reduce(self) -> bool:
    #     return False

    # def can_eta_reduce(self) -> bool:
    #     return False

    def replace(self, var, term):
        if self == var:
            return term.copy()
        return self

    def one_step_beta_reduce(self):
        return (self, False)

    def one_step_eta_reduce(self):
        return (self, False)

    def get_abstracted_vars(self):
        return []

    def is_var_in(self, var):
        return self == var
    
