from symbtable import Symbtable, Token
import term
import churchnum as church

# READERS
class Reader:
    def __init__(self) -> None:
        self.pos = 0
    def read_char(self) -> chr:
        self.pos += 1
    def get_pos(self) -> int:
        return self.pos
    def set_pos(self, pos:int) -> None:
        self.pos = pos
    def is_eof(self) -> bool:
        pass
class StringReader(Reader):
    def __init__(self, string:str) -> None:
        super().__init__()
        self.string : str = string
    def read_char(self) -> chr:
        c = self.string[self.pos]
        super().read_char()   
        return c
    def is_eof(self) -> bool:
        return self.pos >= len(self.string)

class Lexer:
    def __init__(self, reader: Reader, symbtable: Symbtable) -> None:
        self.reader: Reader = reader
        self.state = 0
        self.line_no = 1
        self.buffer = ""
        self.symbtable = symbtable

        self.digits = [str(i) for i in range(10)]

    def next_token(self) -> int:
        self.state = 0
        self.buffer = ""
        while True :
            # INITIAL STATE
            if self.state == 0:
                # EOF
                if self.reader.is_eof():
                    return self.symbtable.add(Token("EOF", None))
                c = self.reader.read_char()
                if c == ' ':
                    continue
                elif c == '\n':
                    self.line_no +=1
                elif c == '#':
                    self.state = 1
                elif c in self.digits:
                    self.state = 2
                    self.buffer = c
                elif c == ':':
                    self.state = 3
                elif c == "\u03BB" or c == "\\":
                    self.state = 6
                elif c.isalpha() or c == '_':
                    self.state = 4
                    self.buffer = c
                else:
                    self.state = 5
            # COMMENTS
            elif self.state == 1:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                else:
                    return self.symbtable.add(Token("EOF", None))
                if c == '\n':
                    self.line_no += 1
                    self.state = 0
            # NATURAL NUMBERS
            elif self.state == 2:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c not in self.digits:
                        self.reader.set_pos(self.reader.get_pos()-1) # go back one
                        T = self.symbtable.add(Token(self.buffer, int(self.buffer), "NUMBER"))
                        return T
                    else:
                        self.buffer += c
                else:
                    return self.symbtable.add(Token(self.buffer, int(self.buffer)))
            # ASSIGN
            elif self.state == 3:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c == '=':
                        return self.symbtable.add(Token("ASSIGN", ":="))
                    else:
                        # error
                        self.state = -1
                        self.buffer = ":"+c
                else:
                    # error
                    self.state = -1
                    self.buffer = c+"EOF"
            # KEYWORD
            elif self.state == 4:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c not in self.digits and not c.isalpha() and c != '_':
                        self.reader.set_pos(self.reader.get_pos()-1) # go back one
                        T = self.symbtable.add(Token(self.buffer, None, "NAME"))
                        return T
                    else:
                        self.buffer += c
                else:
                    return self.symbtable.add(Token(self.buffer, None))
            # SYNTAX
            elif self.state == 5:
                if c in "().;":
                    return self.symbtable.add(Token(c, None))
                else:
                    # error
                    self.state = -1
                    self.buffer = c
            # LAMBDA
            elif self.state == 6:
                return self.symbtable.add(Token("LAMBDA", None))
            else:
                raise ValueError(f"Unknown char sequence '{self.buffer}' at {self.line_no}")
class Parser:
    def __init__(self, symbtable: Symbtable) -> None:
        self.symbtable: Symbtable = symbtable
        self.lexer : Lexer = None
        self.EOF = Token("EOF", None)
        self.token, self.token_id = None, None

    def next_token(self) -> None:
        self.token_id = self.lexer.next_token()
        self.token = self.symbtable.get(self.token_id)

    def match(self, token : Token) -> None:
        if token == self.token:
            self.next_token()
        else:
            raise ValueError(f"Token {token} expected, got {self.token}")

    def parse(self, reader: Reader) -> None:
        self.lexer = Lexer(reader, self.symbtable)
        self.L()

    # L -> I;L | EOF
    def L(self) -> None:
        self.next_token()
        if self.token != self.EOF:
            # instruction
            self.I()
            self.match(Token(";", None))
            self.L()
    # I -> Name := R | print R | R
    def I(self) -> None:
        if self.token.type == "NAME":
            # --built in keywords
            # print R
            if self.token == Token("print", None, "Name"):
                self.match(self.token)
                t = self.R()

                # if the term is a free variable already defined, print it's tree
                if t.type == term.TermType.VARIABLE:
                    tok = Token(t.name, None, "NAME")
                    if self.symbtable.is_token_in(tok):
                        index = self.symbtable.index(tok)
                        print(str(self.symbtable.get(index).value))
                    else:
                        print(str(t))
                else:
                    print(str(t))
            # variable assignation
            # Name := R
            else:
                var_id = self.token_id
                self.match(self.token)
                self.match(Token("ASSIGN", None))
                t = self.R()
                # update variable value
                self.symbtable.get(var_id).value = t
        else:
            raise ValueError(f"Language keyword or variable name expected, got {self.token}.")

    # reductions
    # breduce T | ereduce T | breducev T | ereducev T | T
    def R(self) -> Token:
        context = []
        if self.token == Token("breduce", None, "NAME"):
            self.match(self.token)
            t = self.T(context)
            t,n = t.beta_reduce()
            return t
        elif self.token == Token("breducev", None, "NAME"):
            self.match(self.token)
            t = self.T(context)
            t,n = t.beta_reduce(True)
            return t
        elif self.token == Token("ereduce", None, "NAME"):
            self.match(self.token)
            t = self.T(context)
            t,n = t.eta_reduce()
            return t
        elif self.token == Token("ereducev", None, "NAME"):
            self.match(self.token)
            t = self.T(context)
            t,n = t.eta_reduce(True)
            return t
        else:
            return self.T(context)

    # OP Apply 
    # T -> E {("E")*}
    def T(self, context) -> term.Term:
        context = context[:]
        e = self.E(context)
        while self.token == Token("(", None) or self.token.type == "NAME" or self.token.type == "NUMBER":
            e = term.Apply(e, self.E(context))
        return e


    # E -> (T) | Name | Num | \ {("Name")+} . T
    def E(self, context) -> term.Term:
        context = context[:]
        if self.token == Token("(", None):
            self.match(self.token)
            t = self.T(context)
            self.match(Token(")", None))
            return t
        elif self.token.type == "NAME":
            # if var is in the context
            for v in context:
                if v.name == self.token.name:
                    self.match(self.token)
                    return v
            # if var is a declared free variable -> replace graph
            if self.symbtable.is_token_in(self.token):
                t = self.symbtable.get(self.symbtable.index(self.token)).value
                if t != None:
                    self.match(self.token)
                    return t
                else:
                    # var isn't defined -> error
                    raise ValueError(f"Free variable {self.token.name} is not defined.")
            # var isn't defined -> error
            raise ValueError(f"Free variable {self.token.name} is not defined.")
        elif self.token.type == "NUMBER":
            n = church.gen_number(self.token.value)
            self.match(self.token)
            return n
        elif self.token == Token("LAMBDA", None):
            self.match(self.token)
            if self.token.type == "NAME":
                # get list of vars
                vars = [term.Variable(self.token.name)]
                self.match(self.token)
                while self.token.type == "NAME":
                    vars.append(term.Variable(self.token.name))
                    self.match(self.token)
                self.match(Token(".", None))
                # get abstracted term
                t = self.T(context+vars)
                # construct abstraction chain
                vars.reverse()
                for v in vars:
                    t = term.Abstract(v, t)
                return t
        else:
            raise ValueError(f"Unknown term structure, got {self.token}")



            

