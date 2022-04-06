from symbtable import Symbtable
import term

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

# TOKENS
class Token:
    def __init__(self, name: str, value) -> None:
        self.name = name
        self.value = value

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
                        T = self.symbtable.add(Token(self.buffer, int(self.buffer)))
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
                        T = self.symbtable.add(Token(self.buffer, "NAME"))
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
    def __init__(self, lexer: Lexer, symbtable: Symbtable) -> None:
        self.symbtable: Symbtable = symbtable
        self.lexer = lexer
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

    def parse(self) -> None:
        self.L()

    # L -> I;L | EOF
    def L(self) -> None:
        self.next_token()
        if self.token != self.EOF:
            # instruction
            self.I()
            self.match(Token(";", None))
            self.L()
    # I -> Name := T | print T
    def I(self) -> None:
        if self.token.value == "NAME":
            # --built in keywords
            # print T
            if self.token == Token("print", "NAME"):
                self.match(self.token)
                t = self.T()
                print(str(t))
            # variable assignation
            # Name := T
            else:
                var_id = self.token_id
                self.next_token()
                self.match(Token(":=", None))
                t = self.T()
                # update variable value
                self.symbtable.get(self.token_id).value = t
        else:
            raise ValueError(f"Language keyword or variable name expected, got {self.token}.")

    # OP Apply 
    # T -> E {("E")*}
    def T(self) -> term.Term:
        e = self.E()
        while self.token == Token("(", None) or self.token.value == "NAME":
            e = term.Apply(e, self.E())
        return e


    # E -> (T) | Name | \ {("Name")+} . T
    def E(self) -> term.Term:
        if self.token == Token("(", None):
            self.match(self.token)
            t = self.T()
            self.match(Token(")", None))
            return t
        elif self.token.value == "NAME":
            var = term.Variable(self.token.name)
            self.match(self.token)
            return var
        elif self.token == Token("LAMBDA", None):
            self.match(self.token)
            if self.token.value == "NAME":
                # get list of vars
                vars = [term.Variable(self.token.name)]
                self.match(self.token)
                while self.token.value == "NAME":
                    vars.append(term.Variable(self.token.name))
                    self.match(self.token)
                self.match(Token(".", None))
                # get abstracted term
                t = self.T() # TODO: handle linked variable context
                # construct abstraction chain
                for v in vars.reverse():
                    t = term.Abstract(v, t)
                return t
        else:
            raise ValueError(f"Unknown term structure, got {self.token}")



            

