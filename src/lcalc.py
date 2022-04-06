import sys
import os

from symbtable import Symbtable
from parser import Parser, StringReader



if __name__ == "__main__":
    sys.setrecursionlimit(10**9)
    clear = lambda : os.system('cls' if os.name=='nt' else 'clear')

    S = Symbtable()
    P = Parser(S)
    print("Lcalc v0.1, JAFFUER Pierre")
    print("Type 'exit' to quit, 'clear' to clear console.")
    line = ""
    buffer = ""
    new_input = True
    while True:
        if new_input:
            print()
            line = input("> ")
            if line != "clear":
                new_input = False
        else:
            line = input("... ")
        if line.replace(" ", "") == "exit":
            break
        if line.replace(" ", "") == "clear":
            clear()
        elif line.endswith(";"):
            buffer += line
            try:
                P.parse(StringReader(buffer))
            except ValueError as err:
                print(f"Bad expression: {err}")
            buffer = ""
            new_input = True
        else:
            buffer += line


        
