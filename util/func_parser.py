import argparse

class FuncArgumentParserError(Exception): pass

class FuncArgumentParserHelp(Exception): pass

class FuncArgumentParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if message:
            print(message)
        raise FuncArgumentParserHelp()

    def error(self, message):
        raise FuncArgumentParserError(message)
