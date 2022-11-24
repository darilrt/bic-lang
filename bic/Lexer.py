from .Token import *

# Lexer class
class Lexer:
    def __init__(self, filename):
        self.text = ""
        self.pos = 0
        self.column = 0
        self.line = 1
        self.filename = filename
        self.print_token = False

        with open(self.filename, 'r') as file:
            self.text = file.read()

        if len(self.text) > 0:
            self.current_char = self.text[self.pos]
        
        else:
            self.current_char = None
        
        self.keywords = [
            'type', 'const', # Type
            'let', 'mut', # vars
            'ret', # functions
            'if', 'elif', 'else', 'while', 'for', 'in', 'break', 'continue', # control flow
            'class', 'pub', 'priv', 'static', 'virtual', 'new', 'del', 'null', 'operator',  # classes
            'enum',
            'import',
        ]
        
    def get_state(self):
        return {
            'pos': self.pos,
            'column': self.column,
            'line': self.line,
            'current_char': self.current_char
        }
    
    def set_state(self, state):
        self.pos = state['pos']
        self.column = state['column']
        self.line = state['line']
        self.current_char = state['current_char']

    def get_line(self, index):
        text = self.text.split('\n')
        return text[index - 1]

    def peek(self):
        pos = self.pos
        column = self.column
        line = self.line
        token = self.get_next_token()
        self.pos = pos
        self.column = column
        self.line = line
        return token

    def error(self):
        raise Exception('Invalid character')
        
    def advance(self):
        self.pos += 1
        self.column += 1

        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]
            
    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            if self.current_char == '\n':
                self.line += 1
                self.column = 0

            self.advance()
            
    def integer(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return result
    
    def string(self):
        result = ''
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
            if self.current_char == '\\':
                result += self.current_char
                self.advance()
                result += self.current_char
                self.advance()
        self.advance()
        return result

    def get_next_token(self):
        tok = self._get_next_token()
        if self.print_token:
            print(tok)
        return tok

    def _get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char.isdigit():
                num = self.integer()

                if self.current_char == '.': # float
                    self.advance()
                    num += '.' + self.integer()
                    return Token('FLOAT', float(num), self.line, self.column)
                
                return Token('INTEGER', int(num), self.line, self.column)
                
            elif self.current_char.isalpha() or self.current_char == '_':
                identifier = self.identifier()

                if identifier in ['true', 'false']: 
                    value = 'true' if identifier == 'true' else 'false'
                    return Token('BOOLEAN', value, self.line, self.column)

                elif identifier in ['int', 'float', 'bool', 'char', 'void', 'double']:
                    return Token('TYPE', identifier, self.line, self.column)

                elif identifier in self.keywords:
                    if identifier == 'type':
                        return Token('TYPE_KEY', identifier, self.line, self.column)
                    return Token(identifier.upper(), identifier, self.line, self.column)

                return Token('ID', identifier, self.line, self.column)

            elif self.is_symbol(self.current_char):
                if self.current_char == '.':
                    if self.text[self.pos:self.pos+3] == '...':
                        self.advance()
                        self.advance()
                        self.advance()
                        return Token('ELLIPSIS', '...', self.line, self.column)

                if self.is_multi_char_symbol(self.text[self.pos:self.pos+2]):
                    if self.text[self.pos:self.pos+2] == '//':
                        comment = ''
                        while self.current_char is not None and self.current_char != '\n':
                            comment += self.current_char
                            self.advance()
                        
                        if comment[:3] == '//:':
                            return Token('CPPLIT', comment[3:], self.line, self.column)

                        continue

                    token = Token(self.get_multi_char_symbol(self.text[self.pos:self.pos+2]), self.text[self.pos:self.pos+2], self.line, self.column)
                    self.advance()
                    self.advance()
                    return token

                token = Token(self.char_to_type(self.current_char), self.current_char, self.line, self.column)
                self.advance()
                return token
                
            elif self.current_char == '"':
                self.advance()
                return Token('STRING', self.string(), self.line, self.column)
            
            elif self.current_char == "'": 
                self.advance()
                char = ""
                while self.current_char is not None and self.current_char != "'":
                    char += self.current_char
                    self.advance()
                    if self.current_char == '\\':
                        char += self.current_char
                        self.advance()
                        char += self.current_char
                        self.advance()
                self.advance()
                return Token('CHAR', char, self.line, self.column)

            self.error()
            
        return Token('EOF', None, self.line, self.column)
    
    def is_multi_char_symbol(self, chars):
        return chars in [
            '==', '!=', '<=', '>=', '+=', '-=', '*=', '/=',
            '++', '--', '&&', '||', '<<', '>>', '->', '::',
            '//', '/*', '*/', '%=', '&=', '|=', '^=',
        ]

    def get_multi_char_symbol(self, chars):
        return {
            '==': 'EQ',     '!=': 'NEQ',    '<=': 'LTE',    '>=': 'GTE',
            '+=': 'ADDEQ',  '-=': 'SUBEQ',  '*=': 'MULEQ',  '/=': 'DIVEQ',
            '++': 'INC',    '--': 'DEC',    '&&': 'AND',    '||': 'OR',
            '<<': 'LSHIFT', '>>': 'RSHIFT', '->': 'ARROW',  '::': 'COLONCOLON',
            '//': 'COMMENT', '/*': 'COMMENT_START', '*/': 'COMMENT_END',
            '%=': 'MODEQ',   '&=': 'ANDEQ',  '|=': 'OREQ',   '^=': 'XOREQ',
        }[chars]

    def is_symbol(self, char):
        return char in [
            '+', '-', '*', '/', '(', ')', '{', '}', '[', ']', 
            ',', '.', ':', ';', '=', '<', '>', '&', '|', '!',
            '?', '~', '^', '%', '#', '@', '$', '`', '\\', '/'
        ]

    def char_to_type(self, char):
        return {
            '+': 'PLUS',        '-': 'MINUS',       '*': 'MUL',     '/': 'DIV',
            '(': 'LPAREN',      ')': 'RPAREN',      '{': 'LBRACE',  '}': 'RBRACE',
            '[': 'LBRACKET',    ']': 'RBRACKET',    ',': 'COMMA',   '.': 'DOT',
            ':': 'COLON',       ';': 'SEMI',        '=': 'ASSIGN',  '<': 'LT',
            '>': 'GT',         '&': 'AMP',          '|': 'PIPE',    '!': 'BANG',
            '?': 'QUESTION',    '~': 'TILDE',       '^': 'CARET',   '%': 'MOD',
            '#': 'HASH',        '@': 'AT',          '$': 'DOLLAR',  '`': 'BACKTICK',
            '\\': 'BACKSLASH',  '/': 'FORWARDSLASH'
        }[char]

    def identifier(self):
        result = ''
        while self.current_char is not None and self.current_char.isalnum() or self.current_char == '_':
            result += self.current_char
            self.advance()
        return result    
