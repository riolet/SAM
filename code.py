import sys
import web
# tell renderer where to look for templates
render = web.template.render('templates/')


try:
    sys.dont_write_bytecode = True
    import dbconfig_local as dbconfig
    sys.dont_write_bytecode = False
except Exception as e:
    print e
    import dbconfig

db = web.database(dbn='mysql', user=dbconfig.params['user'], pw=dbconfig.params['passwd'], db=dbconfig.params['db'], port=dbconfig.params['port'])

# Manage routing from here. Regex matches URL and chooses class by name
urls = (
    '/(.*)', 'index'  # matched groups (in parens) are sent as arguments
)

class index:
    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self, name):
        rows = db.select('Syslog')
        # index is name of template.
        return render.index(name, rows)


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
