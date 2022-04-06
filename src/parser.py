import term
import churchnum as church

class Token:
    def __init__(self, name: str, value, type: str = None) -> None:
        self.name = name
        self.value = value
        self.type = type

    def __str__(self) -> str:
        return f"( \"{self.name}\" , {self.value} )"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Token):
            return self.name == __o.name
        return False
    
    def __ne__(self, __o: object) -> bool:
        if isinstance(__o, Token):
            return self.name != __o.name
        return False

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
    def __init__(self, reader: Reader) -> None:
        self.reader: Reader = reader
        self.state = 0
        self.line_no = 1
        self.buffer = ""
        self.digits = [str(i) for i in range(10)]

    def next_token(self) -> Token:
        self.state = 0
        self.buffer = ""
        while True :
            # INITIAL STATE
            if self.state == 0:
                # EOF
                if self.reader.is_eof():
                    return Token("EOF", None)
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
                    return Token("EOF", None)
                if c == '\n':
                    self.line_no += 1
                    self.state = 0
            # NATURAL NUMBERS
            elif self.state == 2:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c not in self.digits:
                        self.reader.set_pos(self.reader.get_pos()-1) # go back one
                        return Token(self.buffer, int(self.buffer), "NUMBER")
                    else:
                        self.buffer += c
                else:
                    return Token(self.buffer, int(self.buffer))
            # ASSIGN
            elif self.state == 3:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c == '=':
                        return Token("ASSIGN", ":=")
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
                        return Token(self.buffer, None, "NAME")
                    else:
                        self.buffer += c
                else:
                    return Token(self.buffer, None)
            # SYNTAX
            elif self.state == 5:
                if c in "().;":
                    return Token(c, None)
                else:
                    # error
                    self.state = -1
                    self.buffer = c
            # LAMBDA
            elif self.state == 6:
                return Token("LAMBDA", None)
            else:
                raise ValueError(f"Unknown char sequence '{self.buffer}' at {self.line_no}")
class Parser:
    def __init__(self) -> None:
        self.lexer : Lexer = None
        self.EOF = Token("EOF", None)
        self.token = None
        self.free_vars = dict()  # {name:term}
    def match(self, token : Token) -> None:
        if token == self.token:
            self.token = self.lexer.next_token()
        else:
            raise ValueError(f"Token {token} expected, got {self.token}")

    def parse(self, reader: Reader) -> None:
        self.lexer = Lexer(reader)
        self.L()

    # L -> I;L | EOF
    def L(self) -> None:
        self.token = self.lexer.next_token()
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
                if church.is_number(t):
                    print(church.get_number(t))
                # if the term is a free variable already defined, print it's tree
                elif t.type == term.TermType.VARIABLE and t.name in self.free_vars: 
                    print(str(self.free_vars[t.name]))
                else:
                    print(str(t))
            # variable assignation
            # Name := R
            else:
                var_name = self.token.name
                self.match(self.token)
                self.match(Token("ASSIGN", None))
                t = self.R()
                # update variable value
                self.free_vars[var_name] = t
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
            # if var is a declared free variable -> capture value
            if self.token.name in self.free_vars:
                t = self.free_vars[self.token.name].copy()
                self.match(self.token)
                return t
            else:
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
                context = context+vars
                # keep only the last occurence of duplicate variables
                context = list({v.name:v for v in context}.values())
                t = self.T(context) # get abstracted body
                # construct abstraction chain
                vars.reverse()
                for v in vars:
                    t = term.Abstract(v, t)
                return t
        else:
            raise ValueError(f"Unknown term structure, got {self.token}")