from pprint import pprint
from sam import common
import re
import web.db


class RuleParseError(Exception): pass


class RuleSQL(object):
    def __init__(self, subject, wheres, havings):
        self.subject = subject
        self._wheres = wheres
        self._havings = havings
        self._groupbys = set()
        self._whats = []

        self._where_columns = self._build_where_columns(self._wheres)
        # self._having_columns = self._build_having_columns

        self.where = ""
        self.when = ""
        self.having = ""
        self.groupby = ""
        self.what = ""

        self.where = self.process_clauses(self._wheres)
        self.having = self.process_clauses(self._havings)
        self._groupbys = self._build_groupbys()
        self.groupby = ", ".join(self._groupbys)
        self._whats = self._build_whats()
        self.what = ", ".join(self._whats)

    def process_clauses(self, clauses):
        parts = []
        for item in clauses:
            if item[0] == 'JOIN':
                parts.append(item[1])
            elif item[0] == 'MODIFIER':
                parts.append(item[1])
            elif item[0] == 'CLAUSE':
                clause = item[1]
                if clause['type'] == 'port':
                    clause_sql = 'port {} {}'.format(clause['comp'], web.sqlquote(clause['value']))
                    parts.append(clause_sql)
                elif clause['type'] == 'host':
                    if isinstance(clause['value'], (str, unicode)):
                        ips = web.sqlquote(common.IPStringtoInt(clause['value']))
                    else:
                        ips = web.sqlquote(map(common.IPStringtoInt, clause['value']))
                    if clause['dir'] == 'src':
                        clause_sql = 'src {} {}'.format(clause['comp'], ips)
                    elif clause['dir'] == 'dst':
                        clause_sql = 'dst {} {}'.format(clause['comp'], ips)
                    else:
                        clause_sql = '(dst {c} {val} or src {c} {val})'.format(c=clause['comp'], val=ips)
                    parts.append(clause_sql)
                elif clause['type'] == 'protocol':
                    val = web.sqlquote(clause['value'].upper())
                    clause_sql = 'protocol {} {}'.format(clause['comp'], val)
                    parts.append(clause_sql)
                elif clause['type'] == 'aggregate':
                    val = web.sqlquote(clause['value'])
                    clause_sql = '`{0}[{1}]` {2} {3}'.format(clause['dir'], clause['agg'],
                                                             clause['comp'], val)
                    parts.append(clause_sql)
                else:
                    raise RuleParseError('Cannot convert to sql: type "{}" is unhandled.'.format(clause['type']))
        return " ".join(parts)

    def set_timerange(self, tstart, tend):
        self.when = "timerange BETWEEN {} AND {}".format(web.sqlquote(tstart), web.sqlquote(tend))

    def _build_where_columns(self, wheres):
        columns = set()
        for item in wheres:
            if item[0] == 'CLAUSE':
                clause = item[1]
                if clause['type'] == 'host':
                    dir_ = clause['dir']
                    # dir_ should be one of 'src' 'dst' 'either'
                    if dir_ == 'either':
                        columns.add('src')
                        columns.add('dst')
                    elif dir_ in ('src', 'dst'):
                        columns.add(dir_)
                elif clause['type'] == 'port':
                    columns.add('port')
                elif clause['type'] == 'protocol':
                    columns.add('protocol')
        return columns

    def _build_whats(self):
        if not self._havings:
            return "*"

        whats = ['timestamp']
        if self.subject == 'either':
            whats.extend(['src', 'dst'])
        elif self.subject in ('src', 'dst'):
            whats.append(self.subject)
        whats.extend(self._where_columns)

        #
        if 'dst' not in whats:
            whats.append("COUNT(DISTINCT dst) AS 'dst[hosts]'")
        if 'src' not in whats:
            whats.append("COUNT(DISTINCT dst) AS 'src[hosts]'")
        if 'port' not in whats:
            whats.append("COUNT(DISTINCT port) AS 'conn[ports]'")
        if 'protocol' not in whats:
            whats.append("COUNT(DISTINCT protocol) AS 'conn[protocol]'")
        if 'links' not in whats:
            whats.append("SUM(links) AS 'conn[links]'")

        return whats

    def _build_groupbys(self):
        if not self._havings:
            return ''

        column_names = {'timestamp'}
        if self.subject == 'either':
            column_names |= {'src', 'dst'}
        elif self.subject in ('src', 'dst'):
            column_names.add(self.subject)
        column_names |= self._where_columns
        return column_names

    def get_where(self):
        if self.where:
            if self.when:
                query = "WHERE {} AND ({})".format(self.when, self.where)
            else:
                query = "WHERE {}".format(self.where)
        elif self.when:
            query = "WHERE {}".format(self.when)
        else:
            query = ""
        return query

    def get_query(self, table, orderby='', limit=''):
        query = "SELECT {}\nFROM {}\n{}".format(self.what, table, self.get_where())

        if self.groupby:
            query = "{}\nGROUP BY {}".format(query, self.groupby)
        if self.having:
            query = "{}\nHAVING {}".format(query, self.having)
        if orderby:
            query = "{}\nORDER BY {}".format(query, orderby)
        if limit:
            query = "{}\nLIMIT {}".format(query, limit)
        return query


class RuleParser(object):
    SCANNER = re.Scanner([
        (r'having',      lambda scanner, token: ('CONTEXT', token)),
        (r'(?:src|dst|conn)\[\S+\]',
                        lambda scanner, token: ('AGGREGATE', token)),
        (r'src|dst',    lambda scanner, token: ('DIRECTION', token)),
        (r'host|port|protocol',
                        lambda scanner, token: ('TYPE', token)),
        (r'in|not in',  lambda scanner, token: ('LIST', token)),
        (r'and|&&',     lambda scanner, token: ('AND', token)),
        (r'or|\|\|',    lambda scanner, token: ('OR', token)),
        (r'not',        lambda scanner, token: ('NOT', token)),
        (r'<=|<|>|>=|==?|!=',
                        lambda scanner, token: ('COMPARATOR', token)),
        (r'\$\S+',      lambda scanner, token: ('REPLACEMENT', token[1:])),  # slicing to remove the leading $
        (r'\[\S+(?:\s*,\s*\S+)*\]|\(\S+(?:\s*,\s*\S+)*\)',
                        lambda scanner, token: ('LIT_LIST', token)),  # to match "[a,b,c]" and "(d , e , f)"
        (r'\(',         lambda scanner, token: ('P_OPEN', token)),  # must come after LIT_LIST (both capture parens)
        (r'\)',         lambda scanner, token: ('P_CLOSE', token)),  # must come after LIT_LIST (both capture parens)
        (r'[\w.-]+',    lambda scanner, token: ('LITERAL', token)),
        (r"\s+",        None),  # None == skip token.
    ])
    LIST_DECODER = re.compile(r'\[\S+(?:\s*,\s*\S+)*\]|'  # lists in brackets: [1, 2, 3]
                              r'\(\S+(?:\s*,\s*\S+)*\)|'  # lists in parens: (1, 2, 3) 
                              r'[^\r\n\t\f ,]+(?:\s*,\s*[^\r\n\t\f ,]+)+')  # bare lists: 22, 44

    # rule:
    # | clauses
    # | CONTEXT aggs
    # | clauses CONTEXT aggs
    # clauses:
    # | [NOT] clause
    # | clauses AND [NOT] clause
    # | clauses OR [NOT] clause
    # clause:
    # | [DIRECTION=either] [TYPE=host] [LIST] LIT_LIST|REPLACEMENT
    # | [DIRECTION=either] [TYPE=host] [COMPARATOR==] LITERAL|REPLACEMENT
    # | P_OPEN [NOT] clauses P_CLOSE
    # aggs:
    # | [NOT] agg
    # | aggs AND [NOT] agg
    # | aggs OR [NOT] agg
    # agg:
    # | AGGREGATE [COMPARATOR==] LITERAL|REPLACEMENT
    # | P_OPEN [NOT] aggs P_CLOSE

    # TODO: remove the token CONTEXT ("having") so that you write horrible rules like:
    #   "dst protocol UDP and (dst[ports] >500 or dst host 1.2.3.4)"

    def __init__(self, replacements, subject, rule_string):
        self.replacements = replacements
        self.subject = subject

        # import pprint
        # print("=" * 80)
        # print("Rule_Parser: Replacements are:")
        # pprint.pprint(replacements)
        # print("=" * 80)

        self.original = rule_string
        self.tokens = []
        self.where_clauses = []
        self.having_clauses = []
        self.sql = ""

        self.tokens = self.tokenize(self.original)
        #print(" Tokens ".center(80, '='))
        #pprint(self.tokens)

        self.decode_tokens(self.replacements, self.tokens)
        RuleParser.conform_to_syntax(self.tokens)
        #print(" Decoded Tokens ".center(80, '='))
        #pprint(self.tokens)

        self.where_clauses, self.having_clauses = self.clause_builder()
        #print(" WHERE Clauses ".center(80, '='))
        #pprint(self.where_clauses)
        #print(" HAVING Clauses ".center(80, '='))
        #pprint(self.having_clauses)

        self.sql = self.sql_encoder()
        #print(" ".center(80, '='))

    @staticmethod
    def tokenize(s):
        tokens, remainder = RuleParser.SCANNER.scan(s)
        if remainder:
            raise RuleParseError('Unable to parse rule. Cannot interpret "{}"'.format(remainder))
        if not RuleParser.has_balanced_parens(tokens):
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
    def get_next_token_options(passed_having, token):
        """
        Note: this function assumes all replacements have been made and no replacement tokens remain.
        They all should have become "LITERAL" or "LIT_LIST".

        TODO: add a stream_start and stream_end tokens to make sure we reach an exit point
           (Exit points are only after a LIT_LIST or LITERAL)
        :param token:
         :type token: str or None
        :return:
         :rtype: list[ str ]
        """
        options = []
        if token is None:
            # Start condition
            options = ['CONTEXT', 'NOT', 'P_OPEN', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST']
        if token == 'AGGREGATE':
            options = ['COMPARATOR', 'LITERAL']
        elif token == 'DIRECTION':
            options = ['TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST']
        elif token == 'TYPE':
            options = ['LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST']
        elif token == 'LIST':
            options = ['LIT_LIST']
        elif token in ('AND', 'OR'):
            if passed_having:
                options = ['NOT', 'P_OPEN', 'AGGREGATE']
            else:
                options = ['NOT', 'P_OPEN', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST']
        elif token == 'NOT':
            if passed_having:
                options = ['P_OPEN', 'AGGREGATE']
            else:
                options = ['P_OPEN', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST']
        elif token == 'P_OPEN':
            if passed_having:
                options = ['NOT', 'AGGREGATE']
            else:
                options = ['NOT', 'P_OPEN', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST']
        elif token == 'COMPARATOR':
            options = ['LITERAL']
        elif token in ('LITERAL', 'LIT_LIST', 'P_CLOSE'):
            if passed_having:
                options = ['P_CLOSE', 'OR', 'AND']
            else:
                options = ['P_CLOSE', 'OR', 'AND', 'CONTEXT']
        elif token == 'CONTEXT':
            options = ['NOT', 'P_OPEN', 'AGGREGATE']


        return options

    @staticmethod
    def conform_to_syntax(tokens):
        prev_token = None
        having = 0
        for token in tokens:
            options = RuleParser.get_next_token_options(having == 1, prev_token)
            if token[0] not in options:
                raise RuleParseError("Invalid rule syntax: unexpected token {}: {}".format(token[0], token[1]))
            if token[0] == 'CONTEXT':
                having += 1
                if having > 1:
                    raise RuleParseError('Invalid rule syntax: "{}" may only appear once.'.format(token[1]))
            prev_token = token[0]

    @staticmethod
    def finalize_clause(clause):
        if not clause.get('dir'):
            clause['dir'] = 'either'
        if not clause.get('type'):
            clause['type'] = 'host'
        if not clause.get('comp'):
            if isinstance(clause['value'], (list, tuple)):
                clause['comp'] = 'in'
            else:
                clause['comp'] = '='

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
                        match = RuleParser.LIST_DECODER.match(str(replacement))
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

    @staticmethod
    def default_clause():
        obj = {
            'dir': 'either',
            'type': 'host',
            'comp': '=',
            'value': '1.2.3.4',
        }
        return obj

    def clause_builder(self):
        where_objects = []
        having_objects = []
        objects = where_objects
        clause = {}
        mode = None
        next_mode = None
        for token in self.tokens:
            switch = token[0]
            if switch in ('AGGREGATE', 'DIRECTION', 'TYPE', 'LIST', 'COMPARATOR', 'LITERAL', 'LIT_LIST') and mode != 'clause':
                next_mode = 'clause'
            elif switch in ('AND', 'OR'):
                next_mode = 'join'
            elif switch in ('NOT', 'P_OPEN', 'P_CLOSE'):
                next_mode = 'modify'
            elif switch == "CONTEXT":
                objects = having_objects
                continue

            mode = next_mode

            if next_mode == 'join':
                objects.append(('JOIN', token[1]))
            elif next_mode == 'modify':
                objects.append(('MODIFIER', token[1]))
            elif next_mode == 'clause':
                if switch == 'AGGREGATE':
                    clause['dir'] = token[1][0]
                    clause['agg'] = token[1][1]
                    clause['type'] = 'aggregate'
                elif switch == 'DIRECTION':
                    clause['dir'] = token[1]
                elif switch == 'TYPE':
                    clause['type'] = token[1]
                elif switch in ('COMPARATOR', 'LIST'):
                    clause['comp'] = token[1]
                elif switch == 'LIT_LIST':
                    clause['value'] = token[1]
                    RuleParser.finalize_clause(clause)
                    objects.append(('CLAUSE', clause))
                    clause = {}
                elif switch == 'LITERAL':
                    clause['value'] = token[1]
                    RuleParser.finalize_clause(clause)
                    objects.append(('CLAUSE', clause))
                    clause = {}
        return where_objects, having_objects

    def sql_encoder(self):
        """
        :return:
         :rtype: RuleSQL
        """
        sql = RuleSQL(self.subject, self.where_clauses, self.having_clauses)
        return sql
