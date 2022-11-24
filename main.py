from bic import Parser, Lexer, CodeGenerator
import sys
import argparse
import os

# helper function to get the options from the command line
# -o <folder> to specify the output folder
def get_options():
    parser = argparse.ArgumentParser(description='Bic compiler')
    parser.add_argument('filename', help='the file to compile')
    parser.add_argument('-o', '--output', help='the output folder', default='./')
    return parser.parse_args()

def main():
    options = get_options()

    lexer = Lexer(options.filename)
    parser = Parser(lexer)
    tree = parser.parse()

    cg = CodeGenerator(tree, options.filename.replace('.bic', '').split('/')[-1])
    cg.generate()

    # write code to file
    if options.output:
        output_filename = options.output + options.filename.replace('.bic', '')
        
        if not os.path.exists(output_filename):
            os.makedirs(output_filename)
        
        with open(output_filename + '.cpp', 'w+') as file:
            file.truncate(0)
            file.write(cg.code)
        
        with open(output_filename + '.hpp', 'w+') as file:
            file.truncate(0)
            file.write(cg.header)
        
        print(u'\u2713', options.filename, u'\u2192', output_filename + '.cpp', output_filename + '.hpp')

if __name__ == '__main__':
    main()