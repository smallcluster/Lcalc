# TODO : use this in the parser AND in term.py to expend user defined terms during Beta reduction (left side only)
from tokenize import Token


class Symbtable:
    def __init__(self) -> None:
        self.tokens = []

    def add(self, token: Token) -> int:
        if token in self.tokens:
            return self.tokens.index(token)
        self.tokens.append(token)
        return len(self.tokens)-1

    def is_token_in(self, token):
        return token in self.tokens

    def get(self, i):
        return self.tokens[i]