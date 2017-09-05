from sam.pages.base import Headed


class TestUrl(Headed):
    def __init__(self):
        super(TestUrl, self).__init__(True, True)
        self.set_title("TestUrl Page Title")
        self.styles = ['/static/css/general.css']
        self.scripts = []

    def GET(self):
        return self.render("test_template")