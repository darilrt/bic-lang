from bic import Parser, Lexer
import sys
import argparse

# helper function to get the options from the command line
def get_options():
    parser = argparse.ArgumentParser(description='Bic compiler')
    parser.add_argument('filename', help='the file to compile')
    parser.add_argument('-o', '--output', help='the file to output to')
    parser.add_argument('-t', '--tokens', action='store_true', help='print tokens')
    parser.add_argument('-a', '--ast', action='store_true', help='print AST')
    parser.add_argument('-c', '--code', action='store_true', help='print code')
    return parser.parse_args()

def main():
    # get the options from the command line
    options = get_options()

    # create lexer and parser
    lexer = Lexer(options.filename)

    if options.tokens:
        lexer.print_token = True

    parser = Parser(lexer)

    # parse and print AST
    tree = parser.parse()

    if options.ast:
        print(tree)

    # transpile and print code
    code = tree.transpile()
    
    if options.code:
        print(code)
    
    # write code to file
    if options.output:
        with open(options.output, 'w') as file:
            file.truncate(0)
            file.write(code)
        
        print('Successfully compiled to ' + options.output)

if __name__ == '__main__':
    main()