import web
import pages.overview
import pages.map
import pages.stats

# Manage routing from here. Regex matches URL and chooses class by name
urls = (
    '/', 'pages.overview.Overview',  # matched groups (in parens) are sent as arguments
    '/map', 'pages.map.Map',
    '/stats', 'pages.stats.Stats',
    '/query', 'pages.query.Query'
)


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
