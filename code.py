import web
# tell renderer where to look for templates
render = web.template.render('templates/')

# Manage routing from here. Regex matches URL and chooses class by name
urls = (
    '/(.*)', 'index'  # matched groups (in parens) are sent as arguments
)

class index:
    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self, name):
        # index is name of template.
        return render.index(name)


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
