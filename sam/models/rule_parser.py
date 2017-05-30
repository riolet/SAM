from pprint import pprint
from sam import common
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
        (r'\[\S+(?:\s*,\s*\S+)*\]|\(\S+(?:\s*,\s*\S+)*\)',
                       lambda scanner, token: ('LIT_LIST', token)),  # to match "[a,b,c]" and "(d , e , f)"
        (r'\(',        lambda scanner, token: ('P_OPEN', token)),
        (r'\)',        lambda scanner, token: ('P_CLOSE', token)),
        (r'[\w.-]+',   lambda scanner, token: ('LITERAL', token)),
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
        self.sql = ""

        self.tokens = self.tokenize()
        self.decode_tokens()
        self.clauses = self.clause_builder()
        self.sql = self.sql_encoder()

    def tokenize(self):
        tokens, remainder = RuleParser.SCANNER.scan(self.original)
        if remainder:
            raise RuleParseError('Unable to parse rule. Cannot interpret "{}"'.format(remainder))
        if not self.has_balanced_parens(tokens):
            raise RuleParseError('Unable to parse rule. Parentheses are unbalanced.')
        return tokens

    def has_balanced_parens(self, tokenlist):
        p_level = 0
        for token in tokenlist:
            print(token)
            if token[1] == '(':
                p_level += 1
            elif token[1] == ')':
                p_level -= 1
            if p_level < 0:
                return False
        return p_level == 0

    def decode_tokens(self):
        for i in range(len(self.tokens)):
            token = self.tokens[i]
            if token[0] == 'REPLACEMENT':
                if token[1] in self.replacements:
                    replacement = self.replacements[token[1]]
                    if isinstance(replacement, (list, tuple)):
                        self.tokens[i] = ('LIT_LIST', map(str, replacement))
                    else:
                        if re.match(r'\[\S+(?:\s*,\s*\S+)*\]|\(\S+(?:\s*,\s*\S+)*\)', str(replacement)):
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
            if token[0] in ('DIRECTION', 'TYPE', 'COMPARATOR', 'LITERAL', 'LIT_LIST') and mode != 'clause':
                next_mode = 'clause'
                clause = self.default_clause()
            elif token[0] in ('AND', 'OR'):
                next_mode = 'join'
            elif token[0] in ('NOT', 'P_OPEN', 'P_CLOSE'):
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
        return objects

    def sql_encoder(self):
        sql = ""
        for item in self.clauses:
            if item[0] == 'JOIN':
                sql += ' {} '.format(item[1])
            elif item[0] == 'MODIFIER':
                sql += ' {} '.format(item[1])
            elif item[0] == 'CLAUSE':
                clause = item[1]
                if clause['type'] == 'port':
                    if type(clause['value']) is list:
                        ports = "({})".format(",".join(map(str, map(int, clause['value']))))
                    else:
                        ports = int(clause['value'])

                    clause_sql = 'port {} {}'.format(clause['comp'], ports)
                elif clause['type'] == 'host':
                    if type(clause['value']) is list:
                        ips = "({})".format(",".join(map(str, map(common.IPStringtoInt, clause['value']))))
                    else:
                        ips = common.IPStringtoInt(clause['value'])
                    if clause['dir_'] == 'src':
                        clause_sql = 'src {} {}'.format(clause['comp'], ips)
                    elif clause['dir_'] == 'dst':
                        clause_sql = 'dst {} {}'.format(clause['comp'], ips)
                    else:
                        clause_sql = '(dst {c} {val} or src {c} {val})'.format(c=clause['comp'], val=ips)
                else:
                    raise RuleParseError('Cannot convert to sql: type "{}" is unhandled.'.format(clause['type']))
                sql += clause_sql
        return sql
