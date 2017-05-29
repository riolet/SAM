from pprint import pprint
import re


class RuleParseError(Exception): pass


class RuleParser(object):
    SCANNER = re.Scanner([
        (r'src|dst',   lambda scanner, token: ('DIRECTION', token)),
        (r'host|port', lambda scanner, token: ('TYPE', token)),
        (r'in|not in', lambda scanner, token: ('LIST', token)),
        (r'and|&&',    lambda scanner, token: ('AND', token)),
        (r'or|\|\|',   lambda scanner, token: ('OR', token)),
        (r'not',       lambda scanner, token: ('NOT', token)),
        (r'<=|<|>|>=|=|!=',
                       lambda scanner, token: ('COMPARATOR', token)),
        (r'\$\S+',     lambda scanner, token: ('REPLACEMENT', token[1:])),  # remove the leading $
        (r'\[\S+(?:[\s,]*\S+)*\]|\(\S+(?:[\s,]*\S+)*\)',
                       lambda scanner, token: ('LIT_LIST', token)),  # to match "[a,b,c]" and "(d e f)"
        (r'\S+',       lambda scanner, token: ('LITERAL', token)),
        (r"\s+",       None),  # None == skip token.
    ])

    # rule:
    # | clauses
    # clauses:
    # | [NOT] clause
    # | clauses AND [NOT] clause
    # | clauses OR [NOT] clause
    # clause:
    # | [DIRECTION=either] [TYPE=host] [LIST] LIT_LIST|REPLACEMENT
    # | [DIRECTION=either] [TYPE=host] [COMPARATOR==] LITERAL|REPLACEMENT

    def __init__(self, replacements, rule_string):
        self.replacements = replacements
        self.original = rule_string
        self.tokens = []
        self.clauses = []

        self.tokenize()
        self.decode_tokens()
        self.clause_builder()

    def tokenize(self):
        tokens, remainder = RuleParser.SCANNER.scan(self.original)
        if remainder:
            raise RuleParseError('Unable to parse rule. Cannot interpret "{}"'.format(remainder))
        self.tokens = tokens

    def decode_tokens(self):
        for i in range(len(self.tokens)):
            token = self.tokens[i]
            if token[0] == 'REPLACEMENT':
                if token[1] in self.replacements:
                    replacement = self.replacements[token[1]]
                    if isinstance(replacement, (list, tuple)):
                        self.tokens[i] = ('LIT_LIST', map(str, replacement))
                    else:
                        if re.match(r'\[\S+(?:[\s,]*\S+)*\]|\(\S+(?:[\s,]*\S+)*\)', str(replacement)):
                            parts = re.split("[, ]+", str(replacement[1:-1]))
                            self.tokens[i] = ('LIT_LIST', parts)
                        else:
                            self.tokens[i] = ('LITERAL', str(replacement))
            elif token[0] == 'LIT_LIST':
                parts = re.split("[, ]+", token[1][1:-1])
                self.tokens[i] = ('LIT_LIST', parts)

    def default_clause(self):
        obj = {
            'dir_': 'either',
            'type': 'host',
            'comp': '=',
            'value': '1.2.3.4',
            'collection': False
        }
        return obj

    def clause_builder(self):
        objects = []
        clause = None
        mode = None
        next_mode = None
        for token in self.tokens:
            next_mode = mode
            if token[0] in ('DIRECTION', 'TYPE', 'COMPARATOR', 'LITERAL', 'LIT_LIST') and mode != 'clause':
                next_mode = 'clause'
                clause = self.default_clause()
            elif token[0] in ('AND', 'OR'):
                next_mode = 'join'
            elif token[0] in ('NOT'):
                next_mode = 'modify'

            if next_mode is None or (mode is None and next_mode == 'join'):
                raise RuleParseError("Unable to parse rule. Clause expected.")
            mode = next_mode

            if next_mode == 'join':
                if clause is not None:
                    clause.pop('collection', None)
                    objects.append(('CLAUSE', clause))
                    clause = None
                objects.append(('JOIN', token[1]))
            elif next_mode == 'modify':
                if clause is not None:
                    clause.pop('collection', None)
                    objects.append(('CLAUSE', clause))
                    clause = None
                objects.append(('MODIFIER', token[1]))
            elif next_mode == 'clause':
                if token[0] == 'DIRECTION':
                    clause['dir_'] = token[1]
                elif token[0] == 'TYPE':
                    clause['type'] = token[1]
                elif token[0] == 'COMPARATOR':
                    clause['comp'] = token[1]
                    clause['collection'] = False
                elif token[0] == 'LIST':
                    clause['comp'] = token[1]
                    clause['collection'] = True
                elif token[0] == 'LIT_LIST':
                    if clause['collection'] == True:
                        clause['value'] = token[1]
                    else:
                        raise RuleParseError("Lists can only be used with the 'in' operator. Example: dst port in (22, 23, 24)")
                elif token[0] == 'LITERAL':
                    if clause['collection'] == False:
                        clause['value'] = token[1]
                    else:
                        raise RuleParseError("The in operator can only be used with lists. Example: dst port in (22, 23, 24)")
        if clause is not None:
            clause.pop('collection', None)
            objects.append(('CLAUSE', clause))
            clause = None
        self.clauses = objects