import web
import common
import base

"""
Relative URL tests for use with these pages:
    '/home', 'pages.debug.Debug_h',
    '/home/joe', 'pages.debug.Debug_h_j',
    '/home/joe/demo', 'pages.debug.Debug_h_j_d',
    '/home/joe/demo2', 'pages.debug.Debug_h_j_d2',
    '/home/sam', 'pages.debug.Debug_h_s',
    '/home/sam/demo', 'pages.debug.Debug_h_s_d',
"""


class Debug_h(base.Headed):
    def __init__(self):
        super(Debug_h, self).__init__("Debug Info", True, True)

    def GET(self):
        html = ('<h2>/home/</h2>'
                '\n<h4>With dot</h4>\n'
                '<p><a href="./home">Here</a></p>'
                '<p><a href="./home/joe">/home/joe</a></p>'
                '<p><a href="./home/joe/demo">/home/joe/demo</a></p>'
                '<p><a href="./home/joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="./home/sam">/home/sam</a></p>'
                '<p><a href="./home/sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without dot</h4>\n'
                '<p><a href="/home">/home</a></p>'
                '<p><a href="/home/joe">/home/joe</a></p>'
                '<p><a href="/home/joe/demo">/home/joe/demo</a></p>'
                '<p><a href="/home/joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="/home/sam">/home/sam</a></p>'
                '<p><a href="/home/sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without slash</h4>\n'
                '<p><a href="home">Here</a></p>'
                '<p><a href="home/joe">/home/joe</a></p>'
                '<p><a href="home/joe/demo">/home/joe/demo</a></p>'
                '<p><a href="home/joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="home/sam">/home/sam</a></p>'
                '<p><a href="home/sam/demo">/home/sam/demo</a></p>'
                 )
        return html

class Debug_h_j(base.Headed):
    def __init__(self):
        super(Debug_h_j, self).__init__("Debug Info", True, True)

    def GET(self):
        html = ('<h2>/home/joe</h2>'
                '\n<h4>With dot</h4>\n'
                '<p><a href="../home">/home</a></p>'
                '<p><a href="./joe">/home/joe</a></p>'
                '<p><a href="./joe/demo">/home/joe/demo</a></p>'
                '<p><a href="./joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="./sam">/home/sam</a></p>'
                '<p><a href="./sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without dot</h4>\n'
                '<p><a href="/home">/home</a></p>'
                '<p><a href="/home/joe">/home/joe</a></p>'
                '<p><a href="/home/joe/demo">/home/joe/demo</a></p>'
                '<p><a href="/home/joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="/home/sam">/home/sam</a></p>'
                '<p><a href="/home/sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without slash</h4>\n'
                '<p><a href="joe">/home/joe</a></p>'
                '<p><a href="joe/demo">/home/joe/demo</a></p>'
                '<p><a href="joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="sam">/home/sam</a></p>'
                '<p><a href="sam/demo">/home/sam/demo</a></p>'
                 )
        return html

class Debug_h_s(base.Headed):
    def __init__(self):
        super(Debug_h_s, self).__init__("Debug Info", True, True)

    def GET(self):

        return "<h2>/home/sam</h2>"

class Debug_h_j_d(base.Headed):
    def __init__(self):
        super(Debug_h_j_d, self).__init__("Debug Info", True, True)

    def GET(self):
        html = ('<h2>/home/joe/demo</h2>'
                '\n<h4>With dot</h4>\n'
                '<p><a href="../../home">/home</a></p>'
                '<p><a href="../joe">/home/joe</a></p>'
                '<p><a href="./demo">/home/joe/demo</a></p>'
                '<p><a href="./demo2">/home/joe/demo2</a></p>'
                '<p><a href="../sam">/home/sam</a></p>'
                '<p><a href="../sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without dot</h4>\n'
                '<p><a href="/home">/home</a></p>'
                '<p><a href="/home/joe">/home/joe</a></p>'
                '<p><a href="/home/joe/demo">/home/joe/demo</a></p>'
                '<p><a href="/home/joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="/home/sam">/home/sam</a></p>'
                '<p><a href="/home/sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without slash</h4>\n'
                '<p><a href="demo">/home/joe/demo</a></p>'
                '<p><a href="demo2">/home/joe/demo2</a></p>'
                 )
        return html

class Debug_h_j_d2(base.Headed):
    def __init__(self):
        super(Debug_h_j_d2, self).__init__("Debug Info", True, True)

    def GET(self):
        html = ('<h2>/home/joe/demo2</h2>'
                '\n<h4>With dot</h4>\n'
                '<p><a href="../../home">/home</a></p>'
                '<p><a href="../joe">/home/joe</a></p>'
                '<p><a href="./demo">/home/joe/demo</a></p>'
                '<p><a href="./demo2">/home/joe/demo2</a></p>'
                '<p><a href="../sam">/home/sam</a></p>'
                '<p><a href="../sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without dot</h4>\n'
                '<p><a href="/home">/home</a></p>'
                '<p><a href="/home/joe">/home/joe</a></p>'
                '<p><a href="/home/joe/demo">/home/joe/demo</a></p>'
                '<p><a href="/home/joe/demo2">/home/joe/demo2</a></p>'
                '<p><a href="/home/sam">/home/sam</a></p>'
                '<p><a href="/home/sam/demo">/home/sam/demo</a></p>'
                '\n<h4>Without slash</h4>\n'
                '<p><a href="demo">/home/joe/demo</a></p>'
                '<p><a href="demo2">/home/joe/demo2</a></p>'
                 )
        return html


class Debug_h_s_d(base.Headed):
    def __init__(self):
        super(Debug_h_s_d, self).__init__("Debug Info", True, True)

    def GET(self):
        return "<h2>/home/sam/demo</h2>"
