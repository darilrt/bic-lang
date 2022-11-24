from .AST import *
from .Token import *
from .Lexer import *

import sys

# custom exception 
class ParserError(Exception):
    def __init__(self, message, token):
        self.message = message
        self.token = token

    def __str__(self):
        return f'ParserError: {self.message} at {self.token}'

# Parser: parse the tokens into an AST (abstract syntax tree)
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.last_token = None
        self.current_token = self.lexer.get_next_token()

        self.is_capture_error = False
        self.error_count = False

        self.state_stack = []
        self.state_id = ''

        self.class_nodes = [VarDecl, FuncDecl, ClassDecl, EnumDecl, OperatorDecl]

    def set_capture_error(self):
        self.is_capture_error = True
        self.error_count = 0

        # return state
        return {
            'token': self.current_token,
            'last_token': self.last_token,
            'lexer': self.lexer.get_state()
        }

    def set_state(self, state):
        self.current_token = state['token']
        self.last_token = state['last_token']
        self.lexer.set_state(state['lexer'])

    def unset_capture_error(self):
        self.is_capture_error = False
        return self.error_count

    def push_state(self, id):
        self.state_id = id
        self.state_stack.append({
            'id': id,
            'token': self.current_token,
            'last_token': self.last_token,
            'lexer': self.lexer.get_state()
        })
    
    def pop_state(self, return_state=False):
        state = self.state_stack.pop()

        if self.state_stack == []:
            self.state_id = ''
            return

        self.state_id = state['id']

        if return_state:
            self.current_token = state['token']
            self.last_token = state['last_token']
            self.lexer.set_state(state['lexer'])

    def error(self, token_type=None):
        def print_line_error():
            print(f'{self.lexer.get_line(self.last_token.line)}')
            print(f'{(self.last_token.column - 1) * " "}^')
        
        if token_type:
            if self.is_capture_error:
                self.error_count += 1
                raise ParserError(f'Capturable error', self.current_token)
            else:
                print('File %s: line %d, column %d' % (self.lexer.filename, self.last_token.line, self.last_token.column))
                print_line_error()
                print(f'Expected {token_type}, but got {self.current_token.type} "{self.current_token.value}"')
                sys.exit(1)
        else:
            if self.is_capture_error:
                self.error_count += 1
                raise ParserError(f'Capturable error', self.current_token)
            else:
                print('File %s: line %d, column %d' % (self.lexer.filename, self.last_token.line, self.last_token.column))
                print_line_error()
                print(f'Unexpected {self.current_token.type} "{self.current_token.value}"')
                sys.exit(1)
    
    def eat(self, token_type):
        self.last_token = self.current_token

        if self.state_id == 'template':
            if self.current_token.type == 'RSHIFT':
                self.current_token = Token('GT', '>', self.current_token.line, self.current_token.column)
                self.lexer.pos += 1
                self.lexer.column += 1
                self.lexer.current_char = '>'
                return

        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(token_type)

    # name: ID
    def name(self):
        node = self.current_token
        self.eat('ID')
        return node
    
    # namespace_access: name (COLONCOLON name)*
    def namespace_access(self, node):
        while self.current_token.type == 'COLONCOLON':
            self.eat('COLONCOLON')
            node = NamespaceAccess(left=node, right=self.name())
        return node
    
    # object_access: expr ((DOT | ARROW) name)+
    def object_access(self, node):
        while self.current_token.type == 'DOT' or self.current_token.type == 'ARROW':
            if self.current_token.type == 'DOT':
                self.eat('DOT')
                node = ObjectAccess(node, self.name())
            elif self.current_token.type == 'ARROW':
                self.eat('ARROW')
                node = ObjectAccess(node, self.name(), is_arrow=True)
        return node
    
    # args: expr (COMMA expr)*
    def args(self):
        node = Args([self.expr()])
        while self.current_token.type == 'COMMA':
            self.eat('COMMA')
            node.token.append(self.expr())
        return node
    
    # call: expr LPAREN args+ RPAREN
    def call(self, node):
        template = None
        if self.current_token.type == 'LT':
            template = self.template_params()
        
        self.eat('LPAREN')
        if self.current_token.type == 'RPAREN':
            self.eat('RPAREN')
            return Call(node, Args([]))
        
        args = self.args()
        self.eat('RPAREN')
        return Call(node, args, template=template)

    # array: LBRACKET expr (COMMA expr)* RBRACKET
    def array(self):
        self.eat('LBRACKET')
        node = Array([self.expr()])
        while self.current_token.type == 'COMMA':
            self.eat('COMMA')
            node.token.append(self.expr())
        self.eat('RBRACKET')
        return node

    # value: INTEGER | FLOAT | STRING | BOOLEAN | NULL
    def value(self):
        token = self.current_token
        if token.type == 'INTEGER':
            self.eat('INTEGER')
            return Integer(token)
        elif token.type == 'FLOAT':
            self.eat('FLOAT')
            return Float(token)
        elif token.type == 'BOOLEAN':
            self.eat('BOOLEAN')
            return Boolean(token)
        elif token.type == 'NULL':
            self.eat('NULL')
            return Null(token)
        elif token.type == 'STRING':
            self.eat('STRING')
            return String(token)
        elif token.type == 'CHAR':
            self.eat('CHAR')
            return Char(token)
        else:
            self.error()

    # primary: value | LPAREN expr RPAREN | object_access | call | array
    def primary(self):
        token = self.current_token
        if token.type in ('INTEGER', 'FLOAT', 'BOOLEAN', 'NULL', 'STRING', 'CHAR'):
            return self.value()
        
        elif token.type == 'TYPE':
            self.eat('TYPE')
            return Type(token)

        elif token.type == 'DOT':
            self.eat('DOT')
            return ObjectAccess('this', self.name())

        elif token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            
            if self.current_token.type == 'LBRACKET':
                return self.index(Parenthesis(node))

            return Parenthesis(node)
        
        elif token.type in ['INC', 'DEC']:
            self.eat(token.type)
            return PreOp(token, self.primary())

        elif token.type == 'ID':
            node = self.name()

            # if the next token is a COLONCOLON, then this is a namespace access
            if self.current_token.type == 'COLONCOLON':
                node = self.namespace_access(node)
            
            # if the next token is ++ or --, then this is a post-increment or post-decrement
            if self.current_token.type in ('INC', 'DEC'):
                tok = self.current_token
                self.eat(self.current_token.type)
                return PostOp(node, tok)
            
            elif self.current_token.type == 'LBRACKET':
                return self.index(node)
            
            elif self.current_token.type in ['LPAREN', 'LT']:
                return self.call(node)
            
            elif self.current_token.type == 'ELLIPSIS':
                self.eat('ELLIPSIS')
                return PostOp(node, Token('ELLIPSIS', '...', token.line, token.column))
            
            return node
        
        self.error()
    
    # dot_expr: primary (DOT ID)+
    def dot_expr(self):
        node = self.primary()
        return self.object_access(node)

    # unary: (PLUS | MINUS | AMP | STAR) dot_expr
    def unary(self):
        token = self.current_token
        if self.current_token.type == 'NEW':
            self.eat('NEW')
            return New(self.expr())
        elif token.type == 'PLUS':
            self.eat('PLUS')
            return UnaryOp(token, self.dot_expr())
        elif token.type == 'BANG':
            self.eat('BANG')
            return UnaryOp(token, self.dot_expr())
        elif token.type == 'MINUS':
            self.eat('MINUS')
            return UnaryOp(token, self.dot_expr())
        elif token.type == 'AMP':
            self.eat('AMP')
            return UnaryOp(token, self.dot_expr())
        elif token.type == 'MUL':
            self.eat('MUL')
            return UnaryOp(token, self.dot_expr())
        elif token.type == 'BANG':
            self.eat('BANG')
            return UnaryOp(token, self.dot_expr())
        
        return self.dot_expr()
    
    # term: unary ((MUL | DIV) unary)* 
    def term(self):
        node = self.unary()
        
        while self.current_token.type in ('DOT', 'MUL', 'FORWARDSLASH', 'MOD'):
            token = self.current_token
            if token.type == 'DOT':
                self.eat('DOT')
                node = Dot(node, self.unary())
            elif token.type == 'MUL':
                self.eat('MUL')
            elif token.type == 'FORWARDSLASH':
                self.eat('FORWARDSLASH')
            elif token.type == 'MOD':
                self.eat('MOD')
                
            node = BinOp(left=node, op=token, right=self.unary())
        
        if self.current_token.type == 'LBRACKET':
            return self.index(node)
            
        return node
    
    # add: term ((PLUS | MINUS) term)*
    def add(self):
        node = self.term()
        
        while self.current_token.type in ('PLUS', 'MINUS'):
            token = self.current_token
            if token.type == 'PLUS':
                self.eat('PLUS')
            elif token.type == 'MINUS':
                self.eat('MINUS')
                
            node = BinOp(left=node, op=token, right=self.term())
            
        return node
    
    # bitop: add ((BITAND | BITOR | BITXOR | LSHIFT | RSHIFT) add)*
    def bitop(self):
        node = self.add()

        while self.current_token.type in ('BITAND', 'BITOR', 'BITXOR', 'LSHIFT', 'RSHIFT'):
            token = self.current_token
            if token.type == 'BITAND':
                self.eat('BITAND')
            elif token.type == 'BITOR':
                self.eat('BITOR')
            elif token.type == 'BITXOR':
                self.eat('BITXOR')
            elif token.type == 'LSHIFT':
                self.eat('LSHIFT')
            elif token.type == 'RSHIFT':
                if self.state_id == 'template':
                    self.current_token = Token('GT', '>', self.current_token.line, self.current_token.column - 1)
                    self.lexer.pos -= 1
                    self.lexer.current_char = '>'
                    return node
                self.eat('RSHIFT')
                
            node = BinOp(left=node, op=token, right=self.expr())
            
        return node

    # comp: bitop ((EQ | NEQ | LT | GT | LTE | GTE | AND | OR) bitop)*
    def comp(self):
        node = self.bitop()
        while self.current_token.type in ('EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE', 'AND', 'OR'):
            token = self.current_token
            if token.type == 'EQ':
                self.eat('EQ')
            elif token.type == 'NEQ':
                self.eat('NEQ')
            elif token.type == 'LT':
                self.eat('LT')
            elif token.type == 'GT':
                if self.state_id == 'template':
                    return node
                self.eat('GT')
            elif token.type == 'LTE':
                self.eat('LTE')
            elif token.type == 'GTE':
                self.eat('GTE')
            if token.type == 'AND':
                self.eat('AND')
            elif token.type == 'OR':
                self.eat('OR')
                
            node = BinOp(left=node, op=token, right=self.bitop())
            
        return node

    # assign_op: ASSIGN | PLUSEQ | MINUSEQ | MULEQ | DIVEQ | MODEQ | ANDEQ | OREQ | XOREQ
    def assign_op(self):
        token = self.current_token
        if token.type == 'ASSIGN':
            self.eat('ASSIGN')
        elif token.type == 'ADDEQ':
            self.eat('ADDEQ')
        elif token.type == 'SUBEQ':
            self.eat('SUBEQ')
        elif token.type == 'MULEQ':
            self.eat('MULEQ')
        elif token.type == 'DIVEQ':
            self.eat('DIVEQ')
        elif token.type == 'MODEQ':
            self.eat('MODEQ')
        elif token.type == 'ANDEQ':
            self.eat('ANDEQ')
        elif token.type == 'OREQ':
            self.eat('OREQ')
        elif token.type == 'XOREQ':
            self.eat('XOREQ')
        return token

    # assign: node assign_op expr
    # if no expression is found show an error
    def assign(self, node):
        token = self.assign_op()
        expr = self.expr()

        if expr is None:
            self.error()
        
        return BinOp(left=node, op=token, right=expr)

    # expr: comp | call | assign
    def expr(self):
        node = self.comp()
        if self.current_token.type in ['LPAREN', 'LT']:
            node = self.call(node)
        
        if self.current_token.type in ('ASSIGN', 'ADDEQ', 'SUBEQ', 'MULEQ', 'DIVEQ', 'MODEQ', 'ANDEQ', 'OREQ', 'XOREQ'):
            node = self.assign(node)
        
        return Expr(node)
    
    # block: LBRACE (statement)* RBRACE
    def block(self):
        self.eat('LBRACE')
        self.unset_capture_error()
        statements = []
        while self.current_token.type != 'RBRACE':
            statements.append(self.statement())
        self.eat('RBRACE')
        return Block(statements)

    # param: ID (LBRACKET expr RBRACKET)* COLON type_spec
    def param(self):
        node = self.name()
        bracket = []
        while self.current_token.type == 'LBRACKET':
            bracket.append(self.bracket())
        self.eat('COLON')
        node = Param(name=node, type=self.type_spec(), bracket=bracket)
        return node

    # params: param (COMMA param)*
    def params(self):
        params = []
        params.append(self.param())
        while self.current_token.type == 'COMMA':
            self.eat('COMMA')
            params.append(self.param())
        return params

    # index: expr (LBRACKET expr RBRACKET)*
    def index(self, node):
        while self.current_token.type == 'LBRACKET':
            self.eat('LBRACKET')
            node = Index(node, self.expr())
            self.eat('RBRACKET')
        return node
    
    # type: ID (COLONCOLON ID)* | TYPE
    def type_name(self):
        if self.current_token.type == 'ID':
            node = self.name()
            while self.current_token.type == 'COLONCOLON':
                self.unset_capture_error()
                self.eat('COLONCOLON')
                node = NamespaceAccess(left=node, right=self.name())
        elif self.current_token.type == 'TYPE':
            node = self.current_token
            self.unset_capture_error()
            self.eat('TYPE')
        else:
            self.error()

        return node

    # type_ptr: type (MUL)*
    def type_ptr(self):
        node = self.type_name()

        while self.current_token.type == 'MUL':
            self.eat('MUL')
            node = TypePtr(node)
        
        return node
    
    # type_ref: type_ptr (AMP)*
    def type_ref(self):
        node = self.type_ptr()
        while self.current_token.type == 'AMP':
            self.eat('AMP')
            node = TypeRef(node)
        return node

    # bracket: LBRACKET expr? RBRACKET
    def bracket(self):
        self.eat('LBRACKET')
        if self.current_token.type != 'RBRACKET':
            node = self.expr()
        else:
            node = None
        self.eat('RBRACKET')

        return Bracket(node)
    
    # template_param_list_val: type_spec | expr
    def template_param_list_val(self):
        state = self.set_capture_error()
        node = None

        try:
            node = self.type_spec()
        except ParserError as e:
            self.set_state(state)
            self.unset_capture_error()
            node = self.expr()

        return node
    
    # template_params: LT (template_param_list_val (COMMA template_param_list_val)*)? GT
    def template_params(self):
        self.push_state('template')
        self.eat('LT')
        params = []
        if self.current_token.type != 'GT':
            params.append(self.template_param_list_val())
            while self.current_token.type == 'COMMA':
                self.eat('COMMA')
                params.append(self.template_param_list_val())
        self.eat('GT')
        self.pop_state()
        
        return TemplateParams(params)

    # template_type: ID COLON (TYPE_KEY | CLASS | type_decl)
    def template_type(self):
        name = self.name()
        self.eat('COLON')
        if self.current_token.type == 'TYPE_KEY':
            node = self.current_token
            self.eat('TYPE_KEY')
        elif self.current_token.type == 'CLASS':
            node = self.current_token
            self.eat('CLASS')
        else:
            node = self.type_spec()
        
        # variadic template
        if self.current_token.type == 'ELLIPSIS':
            self.eat('ELLIPSIS')
            return TemplateType(name, node, True)
        return TemplateType(name, node, False)

    # template_decl:  LT template_type (COMMA template_type)* GT
    def template_decl(self):
        self.push_state('template')
        self.eat('LT')
        types = []
        types.append(self.template_type())
        while self.current_token.type == 'COMMA':
            self.eat('COMMA')
            types.append(self.template_type())
        self.eat('GT')
        self.pop_state()
        return TemplateDecl(types)

    # type_spec: const? type_ref template_params? (bracket)*
    def type_spec(self):
        is_const = False
        if self.current_token.type == 'CONST':
            self.eat('CONST')
            is_const = True
        
        node = self.type_ref()

        template = None
        if self.current_token.type == 'LT':
            template = self.template_params()
        
        variadic = False
        if self.current_token.type == 'ELLIPSIS':
            self.eat('ELLIPSIS')
            variadic = True

        return Type(node, is_const=is_const, template=template, variadic=variadic)

    # var_decl: (LET | MUT) ID (LBRACKET expr RBRACKET)* COLON type_spec (ASSIGN expr)? 
    def var_decl(self):
        token = self.current_token
        if token.type == 'LET':
            self.eat('LET')
        elif token.type == 'MUT':
            self.eat('MUT')
        else:
            self.error()
        node = VarDecl(self.name(), is_mut=token.type == 'MUT')

        bracket = []
        while self.current_token.type == 'LBRACKET':
            bracket.append(self.bracket())
        node.bracket = bracket
        
        self.eat('COLON')
        node.type = self.type_spec()
        if self.current_token.type == 'ASSIGN':
            self.eat('ASSIGN')
            node.value = self.expr()
        return node
    
    # simple_var_decl: ID (COLON type_spec)?
    def simple_var_decl(self):
        node = VarDecl(self.name(), is_mut=True)
        if self.current_token.type == 'COLON':
            self.eat('COLON')
            node.type = self.type_spec()
        return node

    # func_decl: ID LPAREN params? RPAREN CONST? (ARROW type_spec)? block
    def func_decl(self, is_virtual=False):
        name = self.name()
        template = None
        if self.current_token.type == 'LT':
            template = self.template_decl()
            self.unset_capture_error()
        self.eat('LPAREN')
        params = []
        if self.current_token.type != 'RPAREN':
            params = self.params()
        self.eat('RPAREN')
        is_const = False
        if self.current_token.type == 'CONST':
            self.eat('CONST')
            is_const = True
        type = None
        if self.current_token.type == 'ARROW':
            self.eat('ARROW')
            self.unset_capture_error()
            type = self.type_spec()
        block = None
        if self.current_token.type == 'SEMI' and is_virtual:
            self.eat('SEMI')
        else:
            block = self.block()
        fn = FuncDecl(name, params, type, body=block, is_const=is_const)
        fn.template = template
        return fn

    # return_stmt: RETURN expr?
    def return_stmt(self):
        self.eat('RET')
        if self.current_token.type != 'SEMI':
            return Return(self.expr())
        return Return(None)

    # elif_stmt: ELIF LPARENT expr RPARENT block
    def elif_stmt(self):
        self.eat('ELIF')
        self.eat('LPAREN')
        expr = self.expr()
        self.eat('RPAREN')
        block = self.block()
        return Elif(expr, block)

    # if_stmt: IF LPARENT expr RPARENT block (elif_stmt)* (ELSE block)?
    def if_stmt(self):
        self.eat('IF')
        self.eat('LPAREN')
        cond = self.expr()
        self.eat('RPAREN')
        block = self.block()
        elifs = []
        while self.current_token.type == 'ELIF':
            elifs.append(self.elif_stmt())
        else_block = None
        if self.current_token.type == 'ELSE':
            self.eat('ELSE')
            else_block = self.block()
        return If(cond, block, elifs, else_block)

    # while_stmt: WHILE LPARENT expr RPARENT block
    def while_stmt(self):
        self.eat('WHILE')
        self.eat('LPAREN')
        cond = self.expr()
        self.eat('RPAREN')
        block = self.block()
        return While(cond, block)

    # for_stmt: FOR LPARENT simple_var_decl IN expr RPARENT block
    def for_stmt(self):
        self.eat('FOR')
        self.eat('LPAREN')
        var_decl = self.simple_var_decl()
        self.eat('IN')
        expr = self.expr()
        self.eat('RPAREN')
        block = self.block()
        return For(var_decl, expr, block)

    # type_decl: TYPE ID = type_spec;
    def type_decl(self):
        self.eat('TYPE_KEY')
        name = self.name()
        self.eat('ASSIGN')
        type = self.type_spec()
        return TypeDecl(name, type)

    # inherit_decl: LPARENT (PUB|PRIV) type_spec (COMMA (PUB|PRIV) type_spec)* RPARENT
    def inherit_decl(self):
        self.eat('LPAREN')
        inherits = []
        while self.current_token.type != 'RPAREN':
            if self.current_token.type == 'PUB':
                self.eat('PUB')
                inherits.append(('PUB', self.type_spec()))
            elif self.current_token.type == 'PRIV':
                self.eat('PRIV')
                inherits.append(('PRIV', self.type_spec()))
            else:
                inherits.append(('protected', self.type_spec()))
            
            if self.current_token.type == 'COMMA':
                self.eat('COMMA')
            else:
                break
        self.eat('RPAREN')
        return inherits

    # class_decl: CLASS ID template_params? inherit_decl? block
    def class_decl(self):
        self.eat('CLASS')
        name = self.name()
        template = None
        if self.current_token.type == 'LT':
            template = self.template_decl()
        inherits = []
        if self.current_token.type == 'LPAREN':
            inherits = self.inherit_decl()
        block = self.block()
        return ClassDecl(name, block, template=template, inherits=inherits)

    # protection_decl: PUB | PRIV
    def protection_decl(self):
        token = self.current_token
        if token.type == 'PUB':
            self.eat('PUB')
        elif token.type == 'PRIV':
            self.eat('PRIV')
        else:
            self.error()
        return token.type

    # del_stmt: DEL expr
    def del_stmt(self):
        self.eat('DEL')
        return Del(self.expr())

    # enum_key: ID (ASSIGN expr)?
    def enum_key(self):
        name = self.name()
        if self.current_token.type == 'ASSIGN':
            self.eat('ASSIGN')
            return EnumType(name, self.expr())
        return EnumType(name, None)
    
    # enum_decl: ENUM ID (COLON type_spec)? LBRACE enum_key (COMMA enum_key)* RBRACE
    def enum_decl(self):
        self.eat('ENUM')
        name = self.name()
        type = None
        if self.current_token.type == 'COLON':
            self.eat('COLON')
            type = self.type_spec()
        self.eat('LBRACE')
        keys = []
        while self.current_token.type != 'RBRACE':
            keys.append(self.enum_key())
            if self.current_token.type == 'COMMA':
                self.eat('COMMA')
            else:
                break
        self.eat('RBRACE')
        return EnumDecl(name, type, keys)

    # op_id: PLUS | MINUS | MUL | FORWARDSLASH | PERCENT
    def op_id(self):
        ops = ['PLUS', 'MINUS', 'MUL', 'FORWARDSLASH']
        if self.current_token.type in ops:
            token = self.current_token
            self.eat(self.current_token.type)
            return token

    # operator_decl: OPERATOR op_id LPARENT params RPARENT CONST? (ARROW type_spec)? block
    def operator_decl(self):
        self.eat('OPERATOR')
        op = self.op_id()
        self.eat('LPAREN')
        params = self.params()
        self.eat('RPAREN')
        const = False
        if self.current_token.type == 'CONST':
            self.eat('CONST')
            const = True
        ret_type = None
        if self.current_token.type == 'ARROW':
            self.eat('ARROW')
            ret_type = self.type_spec()
        block = self.block()
        return OperatorDecl(op, params, block, ret_type, is_const=const)

    # statement:
    # EOF |
    # SEMI | 
    # expr SEMI | 
    # block | 
    # var_decl SEMI |
    # type_decl SEMI |
    # break SEMI |
    # continue SEMI |
    # return_stmt SEMI |
    # if_stmt |
    # for_stmt |
    # while_stmt |
    # class_decl |
    # func_decl SEMI 
    # func_decl
    def statement(self, is_virtual=False):
        token = self.current_token
        if token.type == 'EOF':
            self.eat('EOF')
        elif token.type == 'CPPLIT':
            self.eat('CPPLIT')
            return Statement(CppLit(token.value))
        elif token.type == 'IMPORT':
            self.eat('IMPORT')
            node = None
            if self.current_token.type == 'STRING':
                node = Import(self.current_token)
                self.eat('STRING')
            self.eat('SEMI')
            return Statement(node)
        elif token.type == 'SEMI':
            self.eat('SEMI')
        elif token.type == 'TYPE_KEY':
            node = self.type_decl()
            self.eat('SEMI')
            return Statement(node)
        elif token.type == 'RET':
            node = self.return_stmt()
            self.eat('SEMI')
            return Statement(node)
        elif token.type == 'DEL':
            node = self.del_stmt()
            self.eat('SEMI')
            return Statement(node)
        elif token.type == 'LBRACE':
            return Statement(self.block())
        elif token.type == 'IF':
            return Statement(self.if_stmt())
        elif token.type == 'WHILE':
            return Statement(self.while_stmt())
        elif token.type == 'FOR':
            return Statement(self.for_stmt())
        elif token.type == 'BREAK':
            self.eat('BREAK')
            return Statement(Break())
        elif token.type == 'CONTINUE':
            self.eat('CONTINUE')
            self.eat('SEMI')
            return Statement(Continue())
        elif self.current_token.type in ['PUB', 'PRIV']:
            protection = self.protection_decl()
            node = self.statement().token
            if type(node) in self.class_nodes:
                node.protection = protection
                return Statement(node)
            self.error()
        elif token.type == 'STATIC':
            self.eat('STATIC')
            node = self.statement().token
            if type(node) in self.class_nodes:
                node.is_static = True
                return Statement(node)
            self.error()
        elif token.type == 'VIRTUAL':
            self.eat('VIRTUAL')
            node = self.statement(True).token
            if type(node) in [FuncDecl]:
                node.is_virtual = True
                return Statement(node)
            self.error()
        elif token.type in ['LET', 'MUT']:
            node = self.var_decl()
            self.eat('SEMI')
            return Statement(node)
        elif token.type == 'CLASS':
            return Statement(self.class_decl())
        elif token.type == 'ENUM':
            return Statement(self.enum_decl())
        elif token.type == 'TILDE':
            self.eat('TILDE')
            node = self.func_decl()
            node.method_type = 'destructor'
            return Statement(node)
        elif token.type == 'OPERATOR':
            node = self.operator_decl()
            return Statement(node)
        elif token.type == 'ID':
            state = self.set_capture_error()
            node = None
            try:
                node = self.func_decl(is_virtual)
            except ParserError as e:
                self.set_state(state)
                self.unset_capture_error()
                node = self.expr()
                self.eat('SEMI')
            return Statement(node)
        else:
            node = self.expr()
            self.eat('SEMI')
            return Statement(node)
        return None

    def parse(self):
        root = Program()

        while self.current_token.type != 'EOF':
            stmt = self.statement()

            if stmt is not None:
                root.statements.append(stmt)

        return root
