import sys
from language.lang_parser import parse

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("usage: python parse.py <file-name>")
    else:
        filename = sys.argv[1]
        data = None
        with open(filename, "r") as f:
            data = f.read()
        if data is None:
            print("file missing")
        else:
            print(parse(data))
