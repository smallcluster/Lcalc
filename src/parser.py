import sys
import term
import os

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

class FileReader(Reader):
    def __init__(self, file) -> None:
        super().__init__()
        self.file = file
    
    def read_char(self) -> chr:
        c = self.file.read(1)
        super().read_char()
        return c
    
    def set_pos(self, pos: int) -> None:
        self.file.seek(pos)
        super().set_pos(pos)
    
    def is_eof(self) -> bool:
        c = self.file.read(1)
        self.file.seek(self.pos)
        return c == ""

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
                elif c == '"':
                    self.state = 7
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
                if c in "().;<>,":
                    return Token(c, None)
                else:
                    # error
                    self.state = -1
                    self.buffer = c
            # LAMBDA
            elif self.state == 6:
                return Token("LAMBDA", None)
            # PATH
            elif self.state == 7:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c == '"':
                        return Token(self.buffer, self.buffer, "PATH")
                    else:
                        self.buffer += c
                else:
                    raise ValueError(f"Path is malformed : {self.buffer}")
            else:
                raise ValueError(f"Unknown char sequence '{self.buffer}' at {self.line_no}")
class Parser:
    def __init__(self, free_vars: dict = dict()) -> None:
        self.lexer : Lexer = None
        self.EOF = Token("EOF", None)
        self.token = None
        self.free_vars = free_vars  # {name:term}
        self.modules = set() # to do, implement a module system
        self.verbose = False
        self.reduce_beta = True
        self.reduce_eta = False

    def listall(self):
        for k in self.free_vars:
            print(f"{k} -> {self.free_vars[k]}")
            
    def match(self, token : Token) -> None:
        if token == self.token:
            self.token = self.lexer.next_token()
        else:
            raise ValueError(f"Token {token} expected, got {self.token}")
        

    def parse(self, reader: Reader) -> None:
        self.lexer = Lexer(reader)
        self.token = self.lexer.next_token()
        self.L()

    # L -> I; L | EOF
    def L(self) -> None:
        if self.token != self.EOF:
            # instruction
            self.I()
            self.match(Token(";", None))
            self.L()
    # I -> clear| exit | listall | verbose | quiet | reduce {("both"|"beta"|"eta")} | import path | print T | Name := T 
    def I(self) -> None:
        if self.token.type == "NAME":
            # --built in keywords
            # clear
            if self.token == Token("clear", None, "NAME"):
                self.match(self.token)
                os.system('cls' if os.name=='nt' else 'clear')
            # exit
            elif self.token == Token("exit", None, "NAME"):
                self.match(self.token)
                sys.exit()
            # listall
            elif self.token == Token("listall", None, "NAME"):
                self.match(self.token)
                self.listall()
            # verbose
            elif self.token == Token("verbose", None, "NAME"):
                self.match(self.token)
                self.verbose = True
            # quiet
            elif self.token == Token("quiet", None, "NAME"):
                self.match(self.token)
                self.verbose = False
            #reduce
            elif self.token == Token("reduce", None, "NAME"):
                self.match(self.token)
                # reduce beta
                if self.token == Token("beta", None, "NAME"):
                    self.match(self.token)
                    self.reduce_beta = True
                    self.reduce_eta = False
                # reduce eta
                elif self.token == Token("eta", None, "NAME"):
                    self.match(self.token)
                    self.reduce_eta = True
                    self.reduce_beta = False
                # reduce both
                elif self.token == Token("both", None, "NAME"):
                    self.match(self.token)
                    self.reduce_eta = True
                    self.reduce_beta = True
                else:
                    raise ValueError(f"reduce expects 'beta' (default), 'eta' or 'both'. Got {self.token.name}.")
            # print T
            elif self.token == Token("print", None, "NAME"):
                self.match(self.token)
                t = self.T([])
                #eval
                if self.reduce_beta and self.reduce_eta:
                    t, n = t.reduce(self.verbose)
                elif self.reduce_beta:
                    t, n = t.beta_reduce(self.verbose)
                elif self.reduce_eta:
                    t, n = t.eta_reduce(self.verbose)

                if self.is_number(t):
                    print(self.get_number(t))
                # if the term is a free variable already defined, print it's tree
                elif t.type == term.TermType.VARIABLE and t.name in self.free_vars: 
                    print(str(self.free_vars[t.name]))
                else:
                    print(str(t))
            # import "path"
            elif self.token == Token("import", None, "NAME"):
                self.match(self.token)
                if self.token.type != "PATH":
                    raise ValueError(f"Expected a path name, got {self.token}")
                path = self.token.value
                self.match(self.token)
                # check if file exist
                if not os.path.exists(path):
                    raise ValueError(f"File {path} do not exist.")
                # parse file content
                with open(path, "r") as f:
                    Parser(self.free_vars).parse(FileReader(f))
            # variable assignation
            # Name := T
            else:
                var_name = self.token.name
                self.match(self.token)
                self.match(Token("ASSIGN", None))
                t = self.T([])
                #eval
                if self.reduce_beta and self.reduce_eta:
                    t, n = t.reduce(self.verbose)
                elif self.reduce_beta:
                    t, n = t.beta_reduce(self.verbose)
                elif self.reduce_eta:
                    t, n = t.eta_reduce(self.verbose)
                # update variable value
                self.free_vars[var_name] = t
        else:
            raise ValueError(f"Language keyword or variable name expected, got {self.token.name}.")

    # OP Apply 
    # T -> E {("E")*}
    def T(self, context) -> term.Term:
        context = context[:]
        e = self.E(context)
        while self.token == Token("(", None) or self.token == Token("<", None)  or self.token.type == "NAME" or self.token.type == "NUMBER":
            e = term.Apply(e, self.E(context))
        return e


    # E -> (T) | Name | Num | \ {("Name")+} . T | <T {("," "T")+}>
    def E(self, context) -> term.Term:
        context = context[:]
        # tuple
        if self.token == Token("<", None):
            self.match(self.token)
            t = [self.T(context)]
            self.match(Token(",", None))
            t.append(self.T(context))
            while self.token == Token(",", None):
                self.match(self.token)
                t.append(self.T(context))
            self.match(Token(">", None))
            v = term.Variable("p")
            c = v
            for i in t:
                c = term.Apply(c, i)
            return term.Abstract(v, c)

        elif self.token == Token("(", None):
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
            n = self.gen_number(self.token.value)
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

    def get_number(self, t):
        if t.type != term.TermType.ABSTRACT:
            return None
        ab1 = t
        # ARCHIVE ONLY
        # id =eta 1, check this special case
        #if t.right == t.var:
        #    return 1

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

    def is_number(self, t):
        return self.get_number(t) != None

    def gen_number(self, n):
        f = term.Variable("f")
        x = term.Variable("x")
        t = x
        for i in range(n):
            t = term.Apply(f, t)
        return term.Abstract(f, term.Abstract(x, t))

    #TODO : format tuple for display
    def tuple_to_str(self, t: term.Term) -> str:
        if t.type != term.TermType.ABSTRACT:
            return None
        