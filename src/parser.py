from symbtable import Symbtable

# READERS
class Reader:
    def __init__(self) -> None:
        self.pos = 0
    def read_char(self) -> chr:
        self.pos += 1
    def get_pos(self) -> int:
        return self.pos
    def set_pos(self, pos) -> None:
        self.pos = pos
    def is_eof(self) -> bool:
        pass
class StringReader(Reader):
    def __init__(self, string) -> None:
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
    def __init__(self, name, value) -> None:
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return f"( \"{self.name}\" , {self.value} )"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Token):
            return self.name == __o.name
        else:
            raise TypeError(f"{self.name}: Token -> __eq__ -> object __o not inst of Token")
    
    def __ne__(self, __o: object) -> bool:
        if isinstance(__o, Token):
            return self.name != __o.name
        else:
            raise TypeError(f"{self.name}: Token -> __eq__ -> object __o not inst of Token")

class Lexer:
    def __init__(self, reader: Reader, symbtable: Symbtable) -> None:
        self.reader: Reader = reader
        self.state = 0
        self.line_no = 1
        self.buffer = ""
        self.symbtable = symbtable

        self.digits = [str(i) for i in range(10)]

    def get_next_token(self) -> Token:
        self.state = 0
        self.buffer = ""
        while True:
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
                        T = Token(self.buffer, int(self.buffer))
                        return T
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
                        T = Token(self.buffer, None)
                        return T
                    else:
                        self.buffer += c
                else:
                    return Token(self.buffer, None)
            # SYNTAX
            elif self.state == 5:
                if c in "()\.;":
                    if c == '\\':
                        return Token("LAMBDA", c)
                    else:
                        return Token(c, None)
                else:
                    # error
                    self.state = -1
                    self.buffer = c
            else:
                raise ValueError(f"Unknown char sequence '{self.buffer}' at {self.line_no}")
class Parser:
    def __init__(self, symbtable: Symbtable) -> None:
        self.symbtable: Symbtable = symbtable
        self.EOF = Token("EOF", None)

    def parse(self, reader: Reader) -> None:
        lexer = Lexer(reader, self.symbtable)
        T = lexer.get_next_token()
        while T != self.EOF :
            print(str(T))
            T = lexer.get_next_token()