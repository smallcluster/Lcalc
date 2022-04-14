import sys
import term
import os
import time

class Token:
    def __init__(self, name: str, value = None, type: str = None) -> None:
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
                elif c == "<":
                    self.state = 8
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
            # ASSIGN or list pile
            elif self.state == 3:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c == '=':
                        return Token("ASSIGN", ":=")
                    elif c == ':':
                        return Token("::")
                    else:
                        # error
                        self.state = -1
                        self.buffer = ":"+c
                else:
                    # error
                    self.state = -1
                    self.buffer = c+"EOF"
            # ASSIGN no eval
            elif self.state == 8:
                if not self.reader.is_eof():
                    c = self.reader.read_char()
                    if c == '-':
                        return Token("ASSIGN_NO_EVAL", "<-")
                    else:
                        # backtrace and return "<"
                        self.reader.set_pos(self.reader.get_pos()-1) # go back one
                        return Token("<")
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
                if c in "().;>,[]":
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
    def __init__(self, free_vars: dict = dict(), modules=set(), combinator = None) -> None:
        self.lexer : Lexer = None
        self.EOF = Token("EOF", None)
        self.token = None
        self.free_vars = free_vars  # {name:(term, recursive ?)}
        self.modules = modules
        self.verbose = False
        self.reduce_beta = True
        self.reduce_eta = False
        self.combinator = combinator if combinator != None else self.turing_combinator()

        # last infos
        self.last_eval_time:float = 0.0
        self.last_reduction_number:int = 0


    def listall(self):
        for k in self.free_vars:
            t, recursive = self.free_vars[k]
            if recursive:
                print(f"{k} (recursive) -> {t}")
            else:
                print(f"{k} -> {t}")
            
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
    # I -> help | clear | exit | listall |showlastinfos | verbose {("true"|"false")} | reduce {("both"|"beta"|"eta")} | import path | 
    # print T | Name := T | Name <- T | defaultcombinator T;
    def I(self) -> None:
        if self.token.type == "NAME":
            # --built in keywords
            # help
            if self.token == Token("help", None, "NAME"):
                self.match(self.token)
                print("----------- BASICS -----------")
                print("print TERM; -> display evaluated term, ex : print (\\x.x) 1;")
                print("printnoeval TERM; -> display term without evaluating it")
                print("NAME := TERM; -> assign evaluated term to a variable, ex : id := (\\x.x) 2;")
                print("NAME <- TERM; -> assign a term to a variable without evaluating it")
                print("Free variables must be defined and are captured by value.")
                print("Built in Support for church numerals and tuples ex: print <1,2,3>;")
                print("-------- COMMAND LIST --------")
                print("help; -> display this help")
                print("clear; -> clear console output")
                print("exit; -> quit interpreter")
                print("listall; -> display all defined lambda terms")
                print("showlastinfos; -> display last evaluation time and number of reductions")
                print("verbose true/false; -> show/hide evaluation steps")
                print("reduce beta(default)/eta/both; -> evaluation strategy : leftmost outermost beta/eta reduction or both")
                print("defaultcombinator T; -> specify the default fixed point combinator (Turing by default)")
                print("import \"path\"; -> load terms from file")
                print("------------------------------")
            # clear
            elif self.token == Token("clear", None, "NAME"):
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
            # showlastinfos
            elif self.token == Token("showlastinfos"):
                self.match(self.token)
                self.show_last_infos()
            # verbose
            elif self.token == Token("verbose", None, "NAME"):
                self.match(self.token)
                if self.token == Token("true"):
                    self.match(self.token)
                    self.verbose = True
                elif self.token == Token("false"):
                    self.match(self.token)
                    self.verbose = False
                else:
                    raise ValueError(f"verbose expects 'false' (default) or 'true'. Got {self.token.name}.")
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
                t, recursive = self.T([])
                start_time = time.time()
                if self.reduce_beta and self.reduce_eta:
                    t, n = t.reduce(self.verbose)
                elif self.reduce_beta:
                    t, n = t.beta_reduce(self.verbose)
                elif self.reduce_eta:
                    t, n = t.eta_reduce(self.verbose)
                self.last_eval_time = time.time() - start_time
                self.last_reduction_number = n
                if self.verbose:
                    self.show_last_infos()
                print(self.format_term(t))
            # printnoeval T
            elif self.token == Token("printnoeval", None, "NAME"):
                self.match(self.token)
                t, recursive = self.T([])
                print(self.format_term(t))
            # import "path"
            elif self.token == Token("import", None, "NAME"):
                self.match(self.token)
                if self.token.type != "PATH":
                    raise ValueError(f"Expected a path name, got {self.token}")
                path = self.token.value
                self.match(self.token)

                path = os.path.abspath(path) # convert to absolute
                # check if file exist
                if not os.path.exists(path):
                    raise ValueError(f"File {path} do not exist.")
                # check if not already imported and parse
                if path not in self.modules:
                    self.modules.add(path)
                    # parse file content
                    with open(path, "r") as f:
                        Parser(self.free_vars, self.modules, self.combinator).parse(FileReader(f))
                    
            # defaultcombinator T
            elif self.token == Token("defaultcombinator"):
                self.match(self.token)
                t, recursive = self.T([])
                self.combinator = t
            # variable assignation
            # Name := T | Name <- T
            else:
                var_name = self.token.name
                self.match(self.token)

                no_eval = False
                if self.token == Token("ASSIGN"):
                    self.match(self.token)
                elif self.token == Token("ASSIGN_NO_EVAL"):
                    self.match(self.token)
                    no_eval = True
                else:
                    raise ValueError(f"Expected ':=' or '<-', got '{self.token.name}'")

                vrecurse = term.Variable("v")
                t, recursive = self.T([], var_name, vrecurse)

                if recursive:
                    t = term.Abstract(vrecurse, t)
                    t = term.Apply(self.combinator.copy(), t)
                    self.free_vars[var_name] = (t, True)
                elif no_eval:
                    self.free_vars[var_name] = (t, False)
                else:
                    #eval
                    start_time = time.time()
                    if self.reduce_beta and self.reduce_eta:
                        t, n = t.reduce(self.verbose)
                    elif self.reduce_beta:
                        t, n = t.beta_reduce(self.verbose)
                    elif self.reduce_eta:
                        t, n = t.eta_reduce(self.verbose)
                    self.last_eval_time = time.time() - start_time
                    self.last_reduction_number = n
                    if self.verbose:
                        self.show_last_infos()
                    self.free_vars[var_name] = (t, False)
        else:
            raise ValueError(f"Language keyword or variable name expected, got {self.token.name}.")

    # OP Apply 
    # T -> R {("R")*}
    def T(self, context, recurse_name : str = None, recurse_var:term.Variable = None):
        context = context[:]
        e, recurse = self.R(context, recurse_name, recurse_var)
        while self.token == Token("(", None) or self.token == Token("<", None) or self.token == Token("[", None)  or self.token.type == "NAME" or self.token.type == "NUMBER":
            etmp, recursetmp = self.R(context, recurse_name, recurse_var)
            recurse = recurse or recursetmp
            e = term.Apply(e, etmp)
        return e, recurse

    # R -> E | E :: R
    def R(self, context, recurse_name : str = None, recurse_var:term.Variable = None):
        context = context[:]
        e, recurse = self.E(context, recurse_name, recurse_var)
        if self.token == Token("::"):
            self.match(self.token)
            r, recursetmp = self.R(context, recurse_name, recurse_var)
            recurse = recurse or recursetmp
            e = self.list_pile(e, r)
        return (e, recurse)

    # E -> (T) | Name | Num | \ {("Name")+} . T | <T {("," "T")+}> | [{("T")? ("," "T")+}]
    def E(self, context, recurse_name : str = None, recurse_var:term.Variable = None):
        context = context[:]
        # tuple
        if self.token == Token("<", None):
            self.match(self.token)
            tmp, recurse = self.T(context, recurse_name, recurse_var)
            t = [tmp]
            while self.token == Token(",", None):
                self.match(self.token)
                tmp, recursetmp = self.T(context, recurse_name, recurse_var)
                recurse = recurse or recursetmp
                t.append(tmp)
            self.match(Token(">", None))
            return self.gen_tuple(t), recurse
        elif self.token == Token("["):
            self.match(self.token)
            # empty list
            if self.token == Token("]"):
                self.match(self.token)
                return self.gen_list([]), False
            # read list
            tmp, recurse = self.T(context, recurse_name, recurse_var)
            t = [tmp]
            while self.token == Token(",", None):
                self.match(self.token)
                tmp, recursetmp = self.T(context, recurse_name, recurse_var)
                recurse = recurse or recursetmp
                t.append(tmp)
            self.match(Token("]", None))
            return self.gen_list(t), recurse
        elif self.token == Token("(", None):
            self.match(self.token)
            t, recurse = self.T(context, recurse_name, recurse_var)
            self.match(Token(")", None))
            return t, recurse
        elif self.token.type == "NAME":
            # if var is in the context
            for v in context:
                if v.name == self.token.name:
                    self.match(self.token)
                    return v, False
            # if var is the assignation -> recursuve function
            if self.token.name == recurse_name:
                self.match(self.token)
                return recurse_var, True
            # if var is a declared free variable -> capture value
            if self.token.name in self.free_vars:
                t, recurse = self.free_vars[self.token.name]
                self.match(self.token)
                return t.copy(), False
            else:
                raise ValueError(f"Free variable {self.token.name} is not defined.")
        elif self.token.type == "NUMBER":
            n = self.gen_number(self.token.value)
            self.match(self.token)
            return n, False
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
                t, recurse = self.T(context, recurse_name, recurse_var) # get abstracted body
                # construct abstraction chain
                vars.reverse()
                for v in vars:
                    t = term.Abstract(v, t)
                return t, recurse
        else:
            raise ValueError(f"Unknown term structure, got {self.token}")

    def get_number(self, t):
        if t.type != term.TermType.ABSTRACT:
            return None
        ab1 = t
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

    def gen_number(self, n):
        f = term.Variable("f")
        x = term.Variable("x")
        t = x
        for i in range(n):
            t = term.Apply(f, t)
        return term.Abstract(f, term.Abstract(x, t))

    def turing_combinator(self):
        a = term.Variable("a")
        b = term.Variable("b")
        A = term.Abstract(a, term.Abstract(b, term.Apply(b, term.Apply(term.Apply(a,a),b))))
        return term.Apply(A, A.copy())

    def curry_combinator(self):
        # λf.(λx.f (xx))(λx.f (xx))
        f = term.Variable("f")
        x1 = term.Variable("x")
        x2 = term.Variable("x")
        return term.Abstract(f, term.Apply(term.Abstract(x1, term.Apply(f, term.Apply(x1,x1))), term.Abstract(x1,term.Apply(f, term.Apply(x1,x1)))))

    def strict_combinator(self):
        f = term.Variable("f")
        x1 = term.Variable("x")
        x2 = term.Variable("x")
        v1 = term.Variable("v")
        v2 = term.Variable("v")
        return term.Abstract(f, term.Apply(term.term.Abstract(x1, term.term.Apply(f, term.term.Abstract(v1, term.term.Apply(term.term.Apply(x1,x1),v1)))), term.term.Abstract(x2, term.term.Apply(f, term.term.Abstract(v2, term.term.Apply(term.term.Apply(x2,x2),v2))))))

    def show_last_infos(self):
        print(f"Last evaluation took {self.last_eval_time}s for {self.last_reduction_number} reductions.")

    def gen_tuple(self, L):
        x = term.Variable("x")
        t = x
        for e in L:
            t = term.Apply(t, e)
        return term.Abstract(x, t)

    def get_tuple(self, t:term.Term):
        if t.type != term.TermType.ABSTRACT:
            return None
        v = t.var
        next = t.right
        L = []
        while next.type == term.TermType.APPLY:
            L.append(next.right)
            next = next.left
        if next == v:
            L.reverse()
            return tuple(L) if len(L) > 0 else None
        return None

    def list_pile(self, h, t):
        x = term.Variable("x")
        y = term.Variable("y")
        return term.Abstract(x, term.Abstract(y, term.Apply( term.Apply(x, h), t)))

    def gen_list(self, L):
        x = term.Variable("x")
        y = term.Variable("y")
        t = term.Abstract(x, term.Abstract(y, y)) # empty list
        for e in reversed(L):
            t = self.list_pile(e, t)
        return t

    def get_list(self, t:term.Term):
        L = []
        while True:
            # \x y .
            if t.type != term.TermType.ABSTRACT:
                return None
            var1 = t.var
            t = t.right
            if t.type != term.TermType.ABSTRACT:
                return None
            var2 = t.var
            t = t.right
            # \x y . y
            if t == var2:
                return L
            elif t.type != term.TermType.APPLY:
                return None
            elif t.left.type != term.TermType.APPLY:
                return None
            elif t.left.left != var1:
                return None
            # \x y . x H T
            else:
                L.append(t.left.right)
                t = t.right

    def get_free_var(self, t:term.Term) -> str:
        for v in self.free_vars:
            if t.is_equals(self.free_vars[v][0]):
                return v
        return None
        
    def format_term(self, t:term.Term) -> str:
        # check if exist
        f = self.get_free_var(t)
        if f != None:
            return f
        # check if number
        n = self.get_number(t)
        if n != None:
            return str(n)
        # check tuple
        tp = self.get_tuple(t)
        if tp != None:
            if len(tp) == 0:
                return "<>"
            buffer = "<"
            for i in tp:
                buffer += self.format_term(i)+","
            return buffer[:-1]+">"
        # check list
        li = self.get_list(t)
        if li != None:
            buffer = "["
            for i in li:
                buffer += self.format_term(i)+","
            return buffer[:-1]+"]"
        # unknown
        return str(t)