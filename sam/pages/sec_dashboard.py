from sam.pages.base import Headed


class Dashboard(Headed):
    def __init__(self):
        super(Dashboard, self).__init__(True, True)
        self.set_title(self.page.strings.dashboard_title)
        self.styles = ['/static/css/general.css',
                       '/static/nouislider/nouislider.css',
                       '/static/nouislider/nouislider.pips.css',
                       '/static/css/security.css']
        self.scripts = ['/static/nouislider/nouislider.min.js',
                        '/static/js/security.js']

    def GET(self):
        return self.render("dashboard")
