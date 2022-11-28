from .AST import *

class CodeGenerator:
    """ Generates a cpp and header file from the AST Nodes. """

    def __init__(self, tree : Program, filename : str):
        self.tree = tree
        self.header = ''
        self.code = ''

        self.source_filename = filename + '.cpp'
        self.header_filename = filename + '.hpp'

    def generate(self):
        self.header += '#pragma once\n'
        self.code += f'#include "{self.header_filename}"\n'

        self.generate_program(self.tree)
    
    def generate_program(self, program : Program):
        for statement in program.statements:
            self.generate_statement(statement)
    
    def generate_statement(self, statement : Statement, parent : str = ''):
        if isinstance(statement.token, CppLit):
            self.code += statement.transpile() + '\n'

        elif isinstance(statement.token, EnumDecl):
            self.header += statement.token.transpile() + '\n'
        
        elif isinstance(statement.token, ClassDecl):
            self.generate_class(statement.token)
        
        elif isinstance(statement.token, FuncDecl):
            self.generate_func(statement.token, parent)
        
        elif isinstance(statement.token, Import):
            self.code += statement.token.transpile() + '\n'
            self.header += statement.token.transpile() + '\n'
        
    def generate_class(self, class_decl : ClassDecl, parent : str = '', depth : int = 0):
        self.header += class_decl.transpile(depth=depth, is_header=True) + ' {\n'
        name = class_decl.name.value
        name = (parent + '::' + name) if parent else name 

        for statement in class_decl.body.statements:
            if isinstance(statement.token, FuncDecl):
                self.generate_func(statement.token, name, depth)
            elif isinstance(statement.token, ClassDecl):
                self.generate_class(statement.token, name, depth)
            elif isinstance(statement.token, VarDecl):
                self.header += statement.token.transpile(depth=depth) + ';\n'
            elif isinstance(statement.token, EnumDecl):	
                self.header += statement.token.transpile(depth=depth) + ';\n'
            elif isinstance(statement.token, CppLit):
                self.header += statement.token.transpile(depth=depth) + '\n'
            else:
                raise Exception('Invalid statement in class body')

        self.header += '};\n'

    def generate_func(self, func_decl : FuncDecl, parent : str = '', depth : int = 0):
        if func_decl.template:
            self.header += func_decl.transpile(depth=depth, parent=parent, all_data=True) + '\n'
        else:
            self.header += func_decl.transpile(depth=depth, parent=parent, is_header=True) + '\n'
            self.code += func_decl.transpile(depth=depth, parent=parent) + '\n'