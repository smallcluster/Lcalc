# TOKENS
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

# TODO : use this in the parser AND in term.py to expend user defined terms during Beta reduction (left side only)
class Symbtable:
    def __init__(self) -> None:
        self.tokens = []

    def add(self, token: Token) -> int:
        if token in self.tokens:
            return self.tokens.index(token)
        self.tokens.append(token)
        return len(self.tokens)-1

    def is_token_in(self, token: Token) -> bool:
        return token in self.tokens

    def get(self, i: int) -> Token:
        return self.tokens[i]

    def index(self, token : Token) -> int:
        return self.tokens.index(token)

    def remove(self, token: Token):
        self.tokens.remove(token)