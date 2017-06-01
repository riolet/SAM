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
        (r'\(',        lambda scanner, token: ('P_OPEN', token)),  # must come after LIT_LIST (both capture parens)
        (r'\)',        lambda scanner, token: ('P_CLOSE', token)),  # must come after LIT_LIST (both capture parens)
        (r'[\w.-]+',   lambda scanner, token: ('LITERAL', token)),
        (r"\s+",       None),  # None == skip token.
    ])
    LIST_DECODER = re.compile(r'\[\S+(?:\s*,\s*\S+)*\]|'  # lists in brackets: [1, 2, 3]
                              r'\(\S+(?:\s*,\s*\S+)*\)|'  # lists in parens: (1, 2, 3) 
                              r'[^\r\n\t\f ,]+(?:\s*,\s*[^\r\n\t\f ,]+)+')  # bare lists: 22, 44

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

        # import pprint
        # print("=" * 80)
        # print("Rule_Parser: Replacements are:")
        # pprint.pprint(replacements)
        # print("=" * 80)

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

    @staticmethod
    def has_balanced_parens(tokenlist):
        p_level = 0
        for token in tokenlist:
            if token[1] == '(':
                p_level += 1
            elif token[1] == ')':
                p_level -= 1
            if p_level < 0:
                return False
        return p_level == 0

    def decode_tokens(self):
        """
        If a REPLACEMENT token was found, replace it from the translation table.
           If the replacement is a list, format it as a string like: "(1,2,3)"
        If a LIT_LIST (literal list) was found, also format it like: "(1,2,3)"
        :return:
        """
        for i in range(len(self.tokens)):
            token = self.tokens[i]
            if token[0] == 'REPLACEMENT':
                if token[1] in self.replacements:
                    replacement = self.replacements[token[1]]
                    if isinstance(replacement, (list, tuple)):
                        self.tokens[i] = ('LIT_LIST', map(str, replacement))
                    else:
                        match = RuleParser.LIST_DECODER.match(str(replacement))
                        if match:
                            s = match.group(0)  # whole match
                            parts = re.split("['\", ]+", s.strip("'\"[]()"))
                            self.tokens[i] = ('LIT_LIST', parts)
                        else:
                            self.tokens[i] = ('LITERAL', str(replacement))
            elif token[0] == 'LIT_LIST':
                parts = re.split("['\", ]+", token[1][1:-1].strip("'\""))
                self.tokens[i] = ('LIT_LIST', parts)

    @staticmethod
    def default_clause():
        obj = {
            'dir_': 'either',
            'type': 'host',
            'comp': '=',
            'value': '1.2.3.4',
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
                    objects.append(('CLAUSE', clause))
                    clause = None
                objects.append(('JOIN', token[1]))
            elif next_mode == 'modify':
                if clause is not None:
                    objects.append(('CLAUSE', clause))
                    clause = None
                objects.append(('MODIFIER', token[1]))
            elif next_mode == 'clause':
                if token[0] == 'DIRECTION':
                    clause['dir_'] = token[1]
                elif token[0] == 'TYPE':
                    clause['type'] = token[1]
                elif token[0] in ('COMPARATOR', 'LIST'):
                    clause['comp'] = token[1]
                elif token[0] == 'LIT_LIST':
                    if clause['comp'].lower() not in ('in', 'not in'):
                        # comparator must be 'in' or 'not in' for lists.
                        if clause['comp'] == '!=':
                            clause['comp'] = 'not in'
                        else:
                            clause['comp'] = 'in'
                    clause['value'] = token[1]
                elif token[0] == 'LITERAL':
                    clause['value'] = token[1]
                    if clause['comp'].lower() == 'in':
                        clause['comp'] = '='  # comparator 'in' only works with lists, but we have a literal.
                    if clause['comp'].lower() == 'not in':
                        clause['comp'] = '!='  # comparator 'not in' only works with lists, but we have a literal.
        if clause is not None:
            objects.append(('CLAUSE', clause))
        return objects

    def sql_encoder(self):
        parts = []
        for item in self.clauses:

            if item[0] == 'JOIN':
                parts.append(item[1])
            elif item[0] == 'MODIFIER':
                parts.append(item[1])
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
                parts.append(clause_sql)
        sql = " ".join(parts)
        return sql


class RuleSQL(object):
    def __init__(self, what, where, groupby, having):
        self.what = what
        self.where = where
        self.groupby = groupby
        self.having = having


class PeriodicRuleParser(object):
    SCANNER = re.Scanner([
        (r'(?:src|dst|conn)\[\S+\]',
                       lambda scanner, token: ('AGGREGATE', token)),
        (r'src|dst',   lambda scanner, token: ('DIRECTION', token)),
        (r'host|port|protocol',
                       lambda scanner, token: ('TYPE', token)),
        (r'in|not in', lambda scanner, token: ('LIST', token)),
        (r'and|&&',    lambda scanner, token: ('AND', token)),
        (r'or|\|\|',   lambda scanner, token: ('OR', token)),
        (r'not',       lambda scanner, token: ('NOT', token)),
        (r'<=|<|>|>=|==?|!=',
                       lambda scanner, token: ('COMPARATOR', token)),
        (r'\$\S+',     lambda scanner, token: ('REPLACEMENT', token[1:])),  # remove the leading $
        (r'\[\S+(?:\s*,\s*\S+)*\]|\(\S+(?:\s*,\s*\S+)*\)',
                       lambda scanner, token: ('LIT_LIST', token)),  # to match "[a,b,c]" and "(d , e , f)"
        (r'\(',        lambda scanner, token: ('P_OPEN', token)),  # must come after LIT_LIST (both capture parens)
        (r'\)',        lambda scanner, token: ('P_CLOSE', token)),  # must come after LIT_LIST (both capture parens)
        (r'[\w.-]+',   lambda scanner, token: ('LITERAL', token)),
        (r"\s+",       None),  # None == skip token.
    ])
    LIST_DECODER = re.compile(r'\[\S+(?:\s*,\s*\S+)*\]|'  # lists in brackets: [1, 2, 3]
                              r'\(\S+(?:\s*,\s*\S+)*\)|'  # lists in parens: (1, 2, 3) 
                              r'[^\r\n\t\f ,]+(?:\s*,\s*[^\r\n\t\f ,]+)+')  # bare lists: 22, 44

    def __init__(self, replacements, subject, rule_string):
        self.replacements = replacements

        # import pprint
        # print("=" * 80)
        # print("Rule_Parser: Replacements are:")
        # pprint.pprint(replacements)
        # print("=" * 80)

        self.original = rule_string
        self.tokens = []
        self.clauses = []
        self.sql = ""

        self.tokens = self.tokenize(self.original)

        PeriodicRuleParser.conform_to_syntax(self.tokens)

        self.decode_tokens(self.replacements, self.tokens)
        self.clauses = self.clause_builder()
        self.sql = self.sql_encoder()

    @staticmethod
    def tokenize(s):
        tokens, remainder = PeriodicRuleParser.SCANNER.scan(s)
        if remainder:
            raise RuleParseError('Unable to parse rule. Cannot interpret "{}"'.format(remainder))
        if not PeriodicRuleParser.has_balanced_parens(tokens):
            raise RuleParseError('Unable to parse rule. Parentheses are unbalanced.')
        return tokens

    @staticmethod
    def has_balanced_parens(tokenlist):
        p_level = 0
        for token in tokenlist:
            if token[1] == '(':
                p_level += 1
            elif token[1] == ')':
                p_level -= 1
            if p_level < 0:
                return False
        return p_level == 0

    @staticmethod
    def decode_tokens(replacements, tokens):
        """
        If a REPLACEMENT token was found, replace it from the translation table.
           If the replacement is a list, format it as a string like: "(1,2,3)"
        If a LIT_LIST (literal list) was found, also format it like: "(1,2,3)"
        :return:
        """
        for i in range(len(tokens)):
            token = tokens[i]
            if token[0] == 'REPLACEMENT':
                if token[1] in replacements:
                    replacement = replacements[token[1]]
                    if isinstance(replacement, (list, tuple)):
                        tokens[i] = ('LIT_LIST', map(str, replacement))
                    else:
                        match = PeriodicRuleParser.LIST_DECODER.match(str(replacement))
                        if match:
                            s = match.group(0)  # whole match
                            parts = re.split("['\", ]+", s.strip("'\"[]()"))
                            tokens[i] = ('LIT_LIST', parts)
                        else:
                            tokens[i] = ('LITERAL', str(replacement))
            elif token[0] == 'LIT_LIST':
                parts = re.split("['\", ]+", token[1][1:-1].strip("'\""))
                tokens[i] = ('LIT_LIST', parts)
            elif token[0] == 'AGGREGATE':
                tokens[i] = ('AGGREGATE', re.match(r'(\S+)\[(\S+)\]', token[1]).groups())

    # AGGREGATE, DIRECTION, TYPE, LIST, AND, OR, NOT, COMPARATOR, REPLACEMENT, LIT_LIST, P_OPEN, P_CLOSE, LITERAL
    # rule:
    # | clauses
    # clauses:
    # | [NOT] clause
    # | clauses AND [NOT] clause
    # | clauses OR [NOT] clause
    # clause:
    # | AGGREGATE [COMPARATOR==] LITERAL|REPLACEMENT
    # | [DIRECTION=either] [TYPE=host] [LIST] LIT_LIST|REPLACEMENT
    # | [DIRECTION=either] [TYPE=host] [COMPARATOR==] LITERAL|REPLACEMENT
    # | P_OPEN [NOT] clauses P_CLOSE

    @staticmethod
    def get_next_token_options(token):
        """
        :param token:
         :type token: str or None
        :return:
         :rtype: list[ str ]
        """
        options = []
        if token is None:
            # Start condition
            options = ['P_OPEN', 'NOT', 'AGGREGATE', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST',
                       'REPLACEMENT']
        if token == 'AGGREGATE':
            options = ['COMPARATOR', 'LITERAL', 'REPLACEMENT']
        elif token == 'DIRECTION':
            options = ['TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST', 'REPLACEMENT']
        elif token == 'TYPE':
            options = ['LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST', 'REPLACEMENT']
        elif token == 'LIST':
            options = ['LIST', 'LIT_LIST', 'REPLACEMENT']
        elif token in ('AND', 'OR'):
            options = ['NOT', 'P_OPEN', 'AGGREGATE', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST',
                       'REPLACEMENT']
        elif token == 'NOT':
            options = ['P_OPEN', 'AGGREGATE', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST',
                       'REPLACEMENT']
        elif token == 'P_OPEN':
            options = ['P_OPEN', 'NOT', 'AGGREGATE', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST',
                       'REPLACEMENT']
        elif token == 'COMPARATOR':
            options = ['LITERAL', 'REPLACEMENT']
        elif token in ('REPLACEMENT', 'LITERAL', 'LIT_LIST', 'P_CLOSE'):
            options = ['P_CLOSE', 'OR', 'AND']

        return options

    @staticmethod
    def conform_to_syntax(tokens):
        prev_token = None
        for token in tokens:
            options = PeriodicRuleParser.get_next_token_options(prev_token)
            if token[0] not in options:
                raise RuleParseError("Invalid rule syntax: unexpected token {}: {}".format(token[0], token[1]))
            prev_token = token[0]

    @staticmethod
    def finalize_clause(clause):
        if not clause.get('dir_'):
            clause['dir'] = 'either'
        if not clause.get('type'):
            clause['type'] = 'host'
        if not clause.get('comp'):
            if clause['value'][0] == '(':
                clause['comp'] = 'in'
            else:
                clause['comp'] = '='

    def clause_builder(self):
        objects = []
        clause = {}
        mode = None
        next_mode = None
        for token in self.tokens:
            if token[0] in ('AGGREGATE', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST') and mode != 'clause':
                next_mode = 'clause'
            elif token[0] in ('AND', 'OR'):
                next_mode = 'join'
            elif token[0] in ('NOT', 'P_OPEN', 'P_CLOSE'):
                next_mode = 'modify'

            mode = next_mode

            if next_mode == 'join':
                objects.append(('JOIN', token[1]))
            elif next_mode == 'modify':
                objects.append(('MODIFIER', token[1]))
            elif next_mode == 'clause':
                if token[0] == 'AGGREGATE':
                    clause['dir_'] = token[1][0]
                    clause['agg'] = token[1][1]
                    clause['type'] = 'aggregate'
                elif token[0] == 'TYPE':
                    clause['type'] = token[1]
                elif token[0] in ('COMPARATOR', 'LIST'):
                    clause['comp'] = token[1]
                elif token[0] == 'LIT_LIST':
                    clause['value'] = token[1]
                    PeriodicRuleParser.finalize_clause(clause)
                    objects.append(('CLAUSE', clause))
                    clause = {}
                elif token[0] == 'LITERAL':
                    clause['value'] = token[1]
                    PeriodicRuleParser.finalize_clause(clause)
                    objects.append(('CLAUSE', clause))
                    clause = {}
        return objects

    def sql_encoder(self):
        parts = []
        sql = " ".join(parts)
        return sql
