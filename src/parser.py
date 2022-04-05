from unicodedata import digit
from pyparsing import Regex

# READERS
class Reader:
    def __init__(self) -> None:
        self.pos = 0
    def read_char(self) -> chr:
        self.pos += 1
    def get_pos(self):
        return self.pos
    def set_pos(self, pos):
        self.pos = pos

    def is_eof(self):
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

# Tokens
class Token:
    def __init__(self, name, value) -> None:
        self.name = name
        self.value = value

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Token):
            return self.name == __o.name
        else:
            raise TypeError(f"{self.name}: Token -> __eq__ -> object __o not inst of Token")
class Symtable:
    def __init__(self) -> None:
        self.tokens = []
class Lexer:
    def __init__(self, reader: Reader, symtable: Symtable) -> None:
        self.reader: Reader = reader
        self.state = 0
        self.line_no = 1
        self.buffer = ""
        self.symtable = symtable

        self.digits = [str(i) for i in range(10)]

    def get_next_token(self):
        self.state = 0
        self.buffer = ""
        while True:
            # end of file
            if self.reader.is_eof():
                return Token("EOF", None)
            # init state
            if self.state == 0:
                c = self.reader.read_char()
                if c == '\n':
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
            # comments
            elif self.state == 1:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                else:
                    return Token("EOF", None)
                if c == '\n':
                    self.line_no += 1
                    self.state = 0
            # Natural number
            elif self.state == 2:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c not in self.digits:
                        self.reader.set_pos(self.reader.get_pos()-1) # go back one
                        T = Token(self.buffer, int(self.buffer))
                        return T
                    self.buffer += c
                else:
                    return Token(self.buffer, int(self.buffer))
            # ASSIGN
            elif self.state == 3:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c == '=':
                        return Token("ASSIGN", ":=")
                    # error
                    self.state = -1
                    self.buffer = ":"+c
                # error
                self.state = -1
                self.buffer = c+"EOF"
            # KEYWORD
            elif self.state == 4:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c not in digit and not c.isalpha() and c != '_':
                        self.reader.set_pos(self.reader.get_pos()-1) # go back one
                        T = Token(self.buffer, None)
                        return T
                else:
                    return Token(self.buffer, None)
            # SYNTAX
            elif self.state == 5:
                if c in "()\.;":
                    return Token(c, None)
                # error
                self.state = -1
                self.buffer = c
            else:
                raise ValueError(f"Unknown char sequence '{self.buffer}' at {self.line_no}")
class Parser:
    def __init__(self, symtable: Symtable) -> None:
        self.symtable = symtable

    def parse(self, reader: Reader):
        lexer = Lexer(reader, self.symtable)