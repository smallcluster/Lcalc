import sys
import os
from parser import FileReader, Parser, StringReader


if __name__ == "__main__":
    sys.setrecursionlimit(10**9)
    clear = lambda : os.system('cls' if os.name=='nt' else 'clear')
    P = Parser()

    if len(sys.argv) >= 2:
        #load file
        path = sys.argv[1]
        with open(path, "r") as f:
            P.parse(FileReader(f))
    else:
        # Interactive interpreter
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


        
