from .Token import Token

INDENT = '    '

def get_protection(type):
    if type == 'PUB':
        return 'public: '
    elif type == 'PRIV':
        return 'private: '
    elif type == 'protected':
        return 'protected: '
    return ''

# AST
class AST:
    def transpile(self, depth=0) -> str:
        return ""

# AST_node
class AST_token(AST):
    def __init__(self, token):
        self.token = token
    
    def __str__(self) -> str:
        return f'{type(self).__name__}({self.token})'

    def transpile(self, depth=0) -> str:
        return str(self.token.transpile())

# AST_token_value
class AST_token_value(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
    
    def __str__(self) -> str:
        return f'{type(self).__name__}({self.value})'
    
    def transpile(self, depth=0) -> str:
        return str(self.value)

# AST_left_right
class AST_left_right(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f'{type(self).__name__}({self.left}, {self.right})'
    
    def transpile(self, depth=0):
        return super().transpile(depth=depth)

# CppLit: C++ Literal
class CppLit(AST):
    def __init__(self, value):
        self.value = value
    
    def __str__(self) -> str:
        return f'{type(self).__name__}({self.value})'
    
    def transpile(self, depth=0) -> str:
        return str(self.value)

# Values
# Identifier: variable name
class Identifier(AST_token_value):
    pass

# String: string
class String(AST_token_value):
    def transpile(self, depth=0) -> str:
        return f'"{self.value}"'

# Char: char
class Char(AST_token_value):
    def transpile(self, depth=0) -> str:
        return f"'{self.value}'"

# Float: float
class Float(AST_token_value):
    pass

# Integer: integer
class Integer(AST_token_value):
    pass

# Boolean: boolean
class Boolean(AST_token_value):
    pass

# Null: null
class Null(AST_token_value):
    def transpile(	self, depth=0) -> str:
        return '0'

# Array: array
class Array(AST_token):
    def transpile(self, depth=0) -> str:
        return f'{{{", ".join([item.transpile() for item in self.token])}}}'

# Var: variable
class Var(AST_token_value):
    pass

# NamespaceAccess: namespace access
class NamespaceAccess(AST_left_right):
    def transpile(self, depth=0):
        left = self.left.transpile(depth=depth) if isinstance(self.left, AST) else self.left.value
        right = self.right.transpile(depth=depth) if isinstance(self.right, AST) else self.right.value
        return f'{left}::{right}'

# ObjectAccess: object access
class ObjectAccess(AST):
    def __init__(self, left, right, is_arrow=False):
        self.left = left
        self.right = right
        self.op = '->' if is_arrow else '.'

    def transpile(self, depth=0):
        right = self.right.transpile(depth=depth) if isinstance(self.right, AST) else self.right.value
        if self.left == 'this':
            return f'this->{right}'
        left = self.left.transpile(depth=depth) if isinstance(self.left, AST) else self.left.value
        return f'{left}{self.op}{right}'

# Index: Index
class Index(AST_left_right):
    def transpile(self, depth=0):
        left = self.left.transpile(depth=depth) if isinstance(self.left, AST) else self.left.value
        right = self.right.transpile(depth=depth) if isinstance(self.right, AST) else self.right.value
        return f'{left}[{right}]'

# Dot: Dot
class Dot(AST_left_right):
    def transpile(self, depth=0):
        left = self.left.transpile(depth=depth) if isinstance(self.left, AST) else self.left.value
        right = self.right.transpile(depth=depth) if isinstance(self.right, AST) else self.right.value
        return f'{left}.{right}'

# Types
# Type: type
class Type(AST):
    def __init__(self, token, is_const=False, template=None, variadic=False):
        self.token = token
        self.is_const = is_const
        self.template = template
        self.variadic = variadic

    def __str__(self) -> str:
        return f'Type({self.token})'

    def transpile(self, depth=0) -> str:
        variadic = '...' if self.variadic else ''
        const = 'const ' if self.is_const else ''
        type = self.token.value if isinstance(self.token, Token) else self.token.transpile()
        tmp = f'{self.template.transpile()}' if self.template else ''
        return f'{const}{type}{tmp}{variadic}'

# TypeRef: type reference
class TypeRef(AST_token):
    def transpile(self, depth=0) -> str:
        if isinstance(self.token, Token):
            return self.token.value + '&'

        return self.token.transpile() + '&'

# TypePtr: type pointer
class TypePtr(AST_token):
    def transpile(self, depth=0) -> str:
        if isinstance(self.token, Token):
            return self.token.value + '*'

        return self.token.transpile() + '*'

# TypeDecl: type declaration
class TypeDecl(AST_left_right):
    def transpile(self, depth=0):
        left = self.left.transpile(depth=depth) if isinstance(self.left, AST) else self.left.value
        right = self.right.transpile(depth=depth) if isinstance(self.right, AST) else self.right.value
        return f'typedef {right} {left}'

# Bracket: bracket
class Bracket(AST_token):
    def __init__(self, token):
        super().__init__(token)
    
    def __str__(self) -> str:
        return f'Bracket({self.token})'
    
    def transpile(self, depth=0) -> str:
        return f'[{self.token.transpile() if self.token else ""}]'

# TemplateDecl: template declaration
class TemplateDecl(AST):
    def __init__(self, types):
        self.types = types
    
    def __str__(self) -> str:
        return f'TemplateDecl({self.types})'

    def transpile(self, depth=0) -> str:
        return f'{", ".join([param.transpile() for param in self.types])}'

# TemplateType: template type
class TemplateType(AST_left_right):
    def __init__(self, left, right, variadic=False):
        super().__init__(left, right)
        self.variadic = variadic

    def transpile(self, depth=0):
        left = self.left.transpile(depth=depth) if isinstance(self.left, AST) else self.left.value
        right = self.right.transpile(depth=depth) if isinstance(self.right, AST) else self.right.value
        variadic = '...' if self.variadic else ''
        if right == 'type':
            right = 'typename'

        return f'{right}{variadic} {left}'

# TemplateParams: template parameters
class TemplateParams(AST):
    def __init__(self, params):
        self.params = params

    def __str__(self) -> str:
        return f'TemplateParams({self.params})'

    def transpile(self, depth=0) -> str:
        params = ''
        for p in self.params:
            params += p.transpile(depth=depth) + ', '

        return f'<{params[:-2]}>' if params else ''

# expressions
# Expr: expression
class Expr(AST_token):
    def transpile(self, depth=0) -> str:
        if isinstance(self.token, Token):
            return self.token.value

        return self.token.transpile()

# BinOp: binary operator
class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = op
        self.op = op.value
        self.right = right

    def __str__(self) -> str:
        return 'BinOp({left}, {op}, {right})'.format(
            left=self.left,
            op=self.op,
            right=self.right
        )
    
    def transpile(self, depth=0) -> str:
        left = self.left.transpile(depth=depth) if isinstance(self.left, AST) else self.left.value
        right = self.right.transpile(depth=depth) if isinstance(self.right, AST) else self.right.value
        return f'{left} {self.op} {right}'

# UnaryOp: unary operator
class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = op
        self.op = op.value
        self.expr = expr

    def __str__(self) -> str:
        return 'UnaryOp({op}, {expr})'.format(
            op=self.op,
            expr=self.expr
        )
    
    def transpile(self, depth=0) -> str:
        expr = self.expr.transpile(depth=depth) if isinstance(self.expr, AST) else self.expr.value
        return f'{self.op}{expr}'

# Parenthesis: parenthesis
class Parenthesis(AST):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self) -> str:
        return 'Parenthesis({expr})'.format(
            expr=self.expr
        )
    
    def transpile(self, depth=0) -> str:
        expr = self.expr.transpile(depth=depth) if isinstance(self.expr, AST) else self.expr.value
        return f'({expr})'

# Post-Op: post operator
class PostOp(AST):
    def __init__(self, expr, op):
        self.expr = expr
        self.token = op
        self.op = op.value

    def __str__(self) -> str:
        return 'PostOp({expr}, {op})'.format(
            expr=self.expr,
            op=self.op
        )
    
    def transpile(self, depth=0) -> str:
        expr = self.expr.transpile(depth=depth) if isinstance(self.expr, AST) else self.expr.value
        return f'{expr}{self.op}'

# Pre-Op: pre operator
class PreOp(AST):
    def __init__(self, op, expr):
        self.token = op
        self.op = op.value
        self.expr = expr

    def __str__(self) -> str:
        return 'PreOp({op}, {expr})'.format(
            op=self.op,
            expr=self.expr
        )

    def transpile(self, depth=0) -> str:
        expr = self.expr.transpile(depth=depth) if isinstance(self.expr, AST) else self.expr.value
        return f'{self.op}{expr}'

# Statements
# Block: block of statements
class Block(AST):
    def __init__(self, statements):
        self.statements = statements

    def __str__(self) -> str:
        return 'Block({statements})'.format(
            statements=self.statements
        )

    def transpile(self, depth=0) -> str:
        ind = INDENT * (depth + 1)
        base = INDENT * (depth)
        filtered = filter(lambda s: s != None, map(lambda s: s.transpile(depth + 1) if s is not None else None, self.statements))
        trlist = map(lambda s: '\n' + ind + s, filtered)
        return '{' + ''.join(filter(lambda s: s != None, trlist)) + '\n' + base + '}'

# Statement: statement
class Statement(AST_token):
    def transpile(self, depth=0) -> str:
        if self.token is None:
            return None

        stmt = self.token.transpile(depth).strip()

        if not isinstance(self.token, (CppLit, Import)):
            stmt += ';' if stmt and stmt[-1] != '}' else ''
        
        if stmt == "":
            return None
        
        return stmt

# Overload
# Call: call
class Call(AST):
    def __init__(self, func, args, template=None):
        self.func = func
        self.args = args
        self.template = template

    def __str__(self) -> str:
        return 'Call({func}, {args})'.format(
            func=self.func,
            args=self.args
        )
    
    def transpile(self, depth=0) -> str:
        func = self.func.transpile(depth) if isinstance(self.func, AST) else self.func.value
        args = self.args.transpile(depth)
        template = self.template.transpile(depth) if self.template is not None else ''

        return f'{func}{template}({args})'

# Misc
# NoOp: no operation
class NoOp(AST):
    def __str__(self) -> str:
        return 'NoOp()'

# Program: program
class Program(AST):
    def __init__(self):
        self.statements = []

    def __str__(self) -> str:
        return 'Program(' + ', '.join(map(lambda s: str(s), self.statements)) +  ')'

    def transpile(self, depth=0) -> str:
        indent = depth * INDENT
        filtered = filter(lambda s: s != None, map(lambda s: s.transpile(depth), self.statements))
        return f'\n'.join(filtered)

# Args: arguments
class Args(AST_token):
    def transpile(self, depth=0) -> str:
        args = ', '.join(map(lambda a: a.transpile(depth), self.token))
        return args

# variable 
# VarDecl: variable declaration
class VarDecl(AST):
    def __init__(self, name, type=None, value=None, is_mut=False, bracket=[], is_static=False):
        self.name = name
        self.type = type
        self.value = value
        self.is_mut = is_mut
        self.bracket = bracket
        self.protection = None
        self.is_static = is_static

    def __str__(self) -> str:
        return 'VarDecl({name}, {type}, {value})'.format(
            name=self.name,
            type=self.type,
            value=self.value
        )

    def transpile(self, depth=0) -> str:
        name = self.name.value
        type = self.type.transpile() if self.type else 'auto'
        mut = '' if self.is_mut else 'const '
        bracket = ''
        for b in self.bracket:
            bracket += b.value if isinstance(b, Token) else b.transpile()
        
        protection = get_protection(self.protection)
        static = 'static ' if self.is_static else ''
        
        def_part = f'{protection}{static}{type} {mut}{name}{bracket}'

        if self.value is None:
            return def_part
        value = self.value.transpile()
        return f'{def_part} = {value}'

# function
# FuncDecl: function declaration
class FuncDecl(AST):
    def __init__(self, name, args, type=Type([]), template=None, body=None, is_const=False, is_static=False, is_virtual=False, is_override=False):
        self.name = name
        self.args = args
        self.type = type
        self.body = body
        self.is_const = is_const
        self.protection = None
        self.is_static = is_static
        self.is_virtual = is_virtual
        self.is_override = is_override
        self.template = template

        self.method_type = None

    def __str__(self) -> str:
        return 'FuncDecl({name}, {args}, {type}, {body})'.format(
            name=self.name,
            args=self.args,
            type=self.type,
            body=self.body
        )

    def transpile(self, depth=0, parent : str='', is_header=False, all_data=False) -> str:
        name = self.name.value
        template = f'template <{self.template.transpile()}> ' if self.template else ''
        if self.method_type == 'destructor': name = '~' + name
        args = ", ".join(map(lambda a: a.transpile(), self.args))
        type = ((self.type.transpile() + ' ') if self.type else 'auto ' ) if not self.method_type == 'constructor' and not self.method_type == 'destructor' else ''
        body = self.body.transpile(depth=depth) if self.body else '= 0'
        const = ' const ' if self.is_const else ''
        protection = get_protection(self.protection)
        static = 'static ' if self.is_static else ''
        virtual = 'virtual ' if self.is_virtual else ''
        nodiscard = '[[nodiscard]] ' if type != 'auto ' and type != 'void ' else ''
        if self.method_type in ['constructor', 'destructor']: nodiscard = ''
        parent_name = parent + '::' if parent else ''

        if all_data:
            return f'{protection}{template}{nodiscard}{static}{virtual}{type}{name}({args}){const}{body}'

        if parent_name == '' and name == 'main':
            if is_header: return ''
            return f'{type}{parent_name}{name}({args}) {const}{body}'

        if is_header: return f'{protection}{template}{nodiscard}{static}{virtual}{type}{name}({args}){const};'
        return f'{type}{parent_name}{name}({args}) {const}{body}'


# return: return statement
class Return(AST):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self) -> str:
        return 'Return({expr})'.format(
            expr=self.expr
        )

    def transpile(self, depth=0) -> str:
        return f'return {self.expr.transpile()}'

# Param: parameter
class Param(AST):
    def __init__(self, name, type=None, bracket=[]):
        self.name = name
        self.type = type
        self.bracket = bracket

    def __str__(self) -> str:
        return 'Param({name}, {type})'.format(
            name=self.name,
            type=self.type
        )
    
    def transpile(self, depth=0) -> str:
        name = self.name.value
        type = self.type.transpile() if self.type else None
        bracket = ''
        for b in self.bracket:
            bracket += b.value if isinstance(b, Token) else b.transpile()

        return f'{type} {name}{bracket}'

# Control flow
# If: if statement
class If(AST):
    def __init__(self, cond, body, elif_stmt=None, else_stmt=None):
        self.cond = cond
        self.body = body
        self.else_stmt = else_stmt
        self.elif_stmt = elif_stmt

    def __str__(self) -> str:
        return 'If({cond}, {body}, {elif_stmt}, {else_stmt})'.format(
            cond=self.cond,
            body=self.body,
            elif_stmt=self.elif_stmt,
            else_stmt=self.else_stmt
        )

    def transpile(self, depth=0) -> str:
        cond = self.cond.transpile()
        body = self.body.transpile(depth=depth)
        else_stmt = f'else {self.else_stmt.transpile(depth=depth)}' if self.else_stmt else ''
        elif_stmt_ = " "
        for elif_stmt in self.elif_stmt:
            elif_stmt_ += f'{elif_stmt.transpile(depth=depth)}'

        return f'if ({cond}) {body}{elif_stmt_}{else_stmt}'

# Elif: elif statement
class Elif(AST):
    def __init__(self, cond, body, else_stmt=None):
        self.cond = cond
        self.body = body
        self.else_stmt = None

    def __str__(self) -> str:
        return 'Elif({cond}, {body}, {else_stmt})'.format(
            cond=self.cond,
            body=self.body,
            else_stmt=self.else_stmt
        )

    def transpile(self, depth=0) -> str:
        cond = self.cond.transpile()
        body = self.body.transpile(depth=depth)
        else_stmt = self.else_stmt.transpile(depth=depth) if self.else_stmt else ''

        return f'else if ({cond}) {body} {else_stmt}'

# Break: break statement
class Break(AST):
    def __str__(self) -> str:
        return 'Break()'

    def transpile(self, depth=0) -> str:
        return 'break'

# Continue: continue statement
class Continue(AST):
    def __str__(self) -> str:
        return 'Continue()'

    def transpile(self, depth=0) -> str:
        return 'continue'

# While: while statement
class While(AST):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def __str__(self) -> str:
        return 'While({cond}, {body})'.format(
            cond=self.cond,
            body=self.body
        )

    def transpile(self, depth=0) -> str:
        cond = self.cond.transpile()
        body = self.body.transpile(depth=depth)

        return f'while ({cond}) {body}'

# For: for each statement
class For(AST):
    def __init__(self, var_decl, iterable, body):
        self.var_decl = var_decl
        self.iterable = iterable
        self.body = body

    def __str__(self) -> str:
        return 'For({var_decl}, {iterable}, {body})'.format(
            var_decl=self.var_decl,
            iterable=self.iterable,
            body=self.body
        )
    
    def transpile(self, depth=0) -> str:
        var_decl = self.var_decl.transpile()
        iterable = self.iterable.transpile()
        body = self.body.transpile(depth=depth)

        return f'for ({var_decl} : {iterable}) {body}'

# Data types
# ClassDecl: class declaration
class ClassDecl(AST):
    def __init__(self, name, body, template=None, inherits=[]):
        self.name = name
        self.body = body
        self.template = template
        self.inherits = inherits

    def __str__(self) -> str:
        return 'ClassDecl({name}, {body}, {template}, {inherits})'.format(
            name=self.name,
            body=self.body,
            template=self.template,
            inherits=self.inherits
        )
    
    def transpile(self, depth=0, is_header=False) -> str:
        name = self.name.value
        # for node in body add protect to each node
        for stmt in self.body.statements:
            node = stmt.token

            if isinstance(node, FuncDecl):
                func_name = node.name.value
                if func_name == name:
                    node.method_type = 'constructor'

            if node.protection not in ['PUB', 'PRIV']:
                node.protection = 'protected'

        body = self.body.transpile(depth=depth)
        if is_header:
            body = ''

        template = f'template <{self.template.transpile()}> ' if self.template else ''
        inherits = f' : {", ".join(map(lambda i: f"{get_protection(i[0])[:-2]} {i[1].transpile()}", self.inherits))}' if self.inherits else ''

        return f'{template}class {name}{inherits}'

# OperatorDecl: operator declaration
class OperatorDecl(AST):
    def __init__(self, op, args, body, type, is_const=False):
        self.op = op
        self.args = args
        self.type = type
        self.body = body
        self.is_static = False
        self.is_virtual = False
        self.protection = None
        self.is_const = is_const

    def transpile(self, depth=0):
        op = self.op.value
        type = self.type.transpile() if self.type else 'auto'
        args = ", ".join(map(lambda a: a.transpile(), self.args))
        body = self.body.transpile(depth)
        nodiscard = '[[nodiscard]] ' if type != 'auto' and type != 'void' else ''
        static = 'static ' if self.is_static else ''
        virtual = 'virtual ' if self.is_virtual else ''
        const = 'const ' if self.is_const else ''
        protection = get_protection(self.protection)
        return f'{protection}{nodiscard}{static}{virtual}{type} operator{op}({args}) {const}{body}'

# New: new object
class New(AST):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self) -> str:
        return 'New({expr})'.format(
            expr=self.expr
        )
    
    def transpile(self, depth=0) -> str:
        expr = self.expr.transpile()

        return f'new {expr}'

# Del: delete object
class Del(AST):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self) -> str:
        return 'Del({expr})'.format(
            expr=self.expr
        )
    
    def transpile(self, depth=0) -> str:
        expr = self.expr.transpile()

        return f'delete {expr}'

# EnumType: enum type
class EnumType(AST):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr
    
    def __str__(self) -> str:
        return 'EnumType({name}, {expr})'.format(
            name=self.name,
            expr=self.expr
        )
    
    def transpile(self, depth=0) -> str:
        name = self.name.value
        expr = (' = ' + self.expr.transpile()) if self.expr else ''

        return f'{name}{expr}'

# EnumDecl: enum declaration
class EnumDecl(AST):
    def __init__(self, name, type, keys):
        self.name = name
        self.type = type
        self.keys = keys
        self.protection = None
    
    def __str__(self) -> str:
        return 'EnumDecl({name}, {type}, {keys})'.format(
            name=self.name,
            type=self.type,
            keys=self.keys
        )
    
    def transpile(self, depth=0) -> str:
        name = self.name.value
        type = (' : ' + self.type.transpile()) if self.type else ''
        indent = INDENT * (depth + 1)
        base = INDENT * depth
        body = '{'
        for e in self.keys:
            body += f'\n{indent}{e.transpile()},'
        body += f'\n{base}}}'
        protection = get_protection(self.protection)
        return f'{protection}enum class {name}{type} {body};'

# import: import statement
class Import(AST):
    def __init__(self, path):
        self.path = path

    def __str__(self) -> str:
        return 'Import({path})'.format(
            path=self.path
        )
    
    def transpile(self, depth=0) -> str:
        path = self.path.value

        # change path extension to .hpp
        path = path.replace('.bic', '.hpp')

        return f'#include "{path}"'