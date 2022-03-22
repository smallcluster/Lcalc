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

    def reduce_LO(self, verbose=False):
        t = self
        while t.can_reduce_LO():
            t = t.one_step_reduce_LO()
            if verbose:
                print(f"-> {t}")
        return t

    def __str__(self) -> str:
        vars = self.get_abstracted_vars()
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

    # Abstract functions
    def copy(self):
        pass
    def get_abstracted_vars(self):
        pass
    def to_string(self):
        pass
    def can_reduce_LO(self) -> bool:
        pass
    def replace(self, var, term):
        pass
    
    def get_abstracted_vars(self, set=set()):
        return set
    
class Abstract(Term):
    def __init__(self, var, term):
        super().__init__(None, term, TermType.ABSTRACT)
        self.var = var

    def copy(self):
        var = Variable(self.var.name)
        return Abstract(var, self.right.replace(self.var, var))

    def to_string(self) -> str:
        txt = f"${self.var}"
        next = self.right
        while next.type == TermType.ABSTRACT:
            txt += f" {next.var}"
            next = next.right
        return f"{txt}.{next.to_string()}"

    def can_reduce_LO(self) -> bool:
        return self.right.can_reduce_LO()

    def replace(self, var, term):
        if self.var == var:
            return self.right.replace(var, term)
        t = self.copy()
        return Abstract(t.var, t.right.replace(var, term))


    def one_step_reduce_LO(self):
        t = self.copy()
        return Abstract(t.var, t.right.one_step_reduce_LO())

    def get_abstracted_vars(self):
        return self.right.get_abstracted_vars()+[self.var]

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


    def can_reduce_LO(self) -> bool:
        if self.left.type == TermType.ABSTRACT:
            return True
        elif self.left.type == TermType.APPLY:
            LR = self.left.can_reduce_LO()
            if not LR:
                return self.right.can_reduce_LO()
            else:
                return LR
        else:
            return self.right.can_reduce_LO()

    def replace(self, var, term):
        return Apply(self.left.replace(var, term), self.right.replace(var, term))

    def one_step_reduce_LO(self):
        if self.left.type == TermType.ABSTRACT:
            return self.left.replace(self.left.var, self.right)
        elif self.left.type == TermType.APPLY:
            if self.left.can_reduce_LO():
                return Apply(self.left.one_step_reduce_LO(), self.right)
            else:
                return Apply(self.left, self.right.one_step_reduce_LO())
        else:
            return Apply(self.left, self.right.one_step_reduce_LO())

    def get_abstracted_vars(self):
        return self.left.get_abstracted_vars() + self.right.get_abstracted_vars()

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
    
    def can_reduce_LO(self) -> bool:
        return False

    def replace(self, var, term):
        if self == var:
            return term.copy()
        return self

    def one_step_reduce_LO(self):
        return self

    def get_abstracted_vars(self):
        return []