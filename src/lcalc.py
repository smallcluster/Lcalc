import sys
import os
from parser import FileReader, Parser, StringReader


if __name__ == "__main__":

    version = "Lcalc v1.0, JAFFUER Pierre"


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
        print(version)
        print("Type 'exit;' to quit, 'help;' for help.")
        line = ""
        buffer = ""
        new_input = True
        while True:
            if new_input:
                print()
                line = input("> ")
            else:
                line = input("... ")

            if line.endswith(";"):
                buffer += line
                try:
                    P.parse(StringReader(buffer))
                except ValueError as err:
                    print(f"Bad expression: {err}")
                buffer = ""
                new_input = True
            else:
                buffer += line
                new_input = False


        
