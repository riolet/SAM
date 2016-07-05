import web
# tell renderer where to look for templates
render = web.template.render('templates/')
db = web.database(dbn='mysql', user='root', pw='Zervos', db='samapper')

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
