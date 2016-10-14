import sys
import os


class Node(object):
    INDENT_STEP = 2

    def __init__(self):
        self.before = ''
        self.after = ''
        self.contents = []
        self.leading_newlines = 0
        self.trailing_newlines = 0

    def insert(self, node):
        self.contents.append(node)

    def dumps(self):
        javascript = ''
        javascript += "\n" * self.leading_newlines
        javascript += "{0}\n".format(self.before)
        for item in self.contents:
            javascript += item.dumps_indent(self.INDENT_STEP)
        javascript += "{0}\n".format(self.after)
        javascript += "\n" * self.trailing_newlines
        return javascript

    def dumps_indent(self, indent):
        javascript = ''
        javascript += "\n" * self.leading_newlines
        javascript += "{0}{1}\n".format(" " * indent, self.before)
        for item in self.contents:
            javascript += item.dumps_indent(indent + self.INDENT_STEP)
        javascript += "{0}{1}\n".format(" " * indent, self.after)
        javascript += "\n" * self.trailing_newlines
        return javascript


class Text(Node):
    def __init__(self, content):
        Node.__init__(self)
        self.contents.append(content)

    def dumps(self):
        return "\n".join(self.contents) + '\n'

    def dumps_indent(self, indent):
        return "\n".join(self.contents) + '\n'



class It(Node):
    def __init__(self, string, content=Text("      expect(1).toEqual(1);")):
        Node.__init__(self)
        self.before = 'it("{0}", function () {{'.format(string)
        self.contents.append(content)
        self.after = "});"


class Describe(Node):
    def __init__(self, string):
        Node.__init__(self)
        self.before = 'describe("{0}", function () {{'.format(string)
        self.after = '});'
        self.leading_newlines = 2


class TestMaker:
    def __init__(self):
        self.instructions =  "\nThis program retrieves simple function names from .js files and"
        self.instructions += "\nwrites them all out in a _spec file to be filled in as tests"
        self.instructions += "\n"
        self.instructions += "\nUsage:"
        self.instructions += "\n\tpython {0} <input-file>".format(sys.argv[0])
        self.instructions += "\n"

    def validate_file(self, path):
        """
        Check whether a given path is a file.
        Args:
            path: The path to verify is a file

        Returns:
            True or False
        """
        if os.path.isfile(path):
            return True
        else:
            print "File not found:", path
            return False

    def main(self, argv):
        if len(argv) != 2 or not self.validate_file(argv[1]):
            print(self.instructions)
            return
        js_file_path = argv[1]

        # get function names from source js
        file_name = self.read_file_name(js_file_path)  # without extension
        function_names = self.read_function_names(js_file_path)
        print"Function names in {0}:\n\t".format(file_name), "\n\t".join(function_names)

        # determine spec file name and strings
        out_path = self.out_path(file_name)

        # build the describes
        suite = self.build_tree(file_name, function_names)

        # write out the final spec file.
        self.write(out_path, suite.dumps())

        print "done."
        return

    def write(self, path, data):
        with open(path, 'wb') as f:
            f.write(data)

    def build_tree(self, filename, functions):
        suite = Describe(filename + ".js file")
        for func in functions:
            group = Describe(func)
            group.insert(It(" "))
            suite.insert(group)
        suite.contents[0].leading_newlines = 0
        suite.leading_newlines = 0
        return suite

    def out_path(self, name):
        project_folder = "SAM"
        spec_folder = "spec"
        js_folder = "javascripts"

        current_path = os.getcwd()
        proj_pos = current_path.rfind(project_folder)
        if proj_pos == -1:
            print("Could not find project folder. Aborting.")
            exit(-1)
        proj_path = current_path[:proj_pos + len(project_folder)]
        out_path = os.path.join(proj_path, spec_folder, js_folder, name + "_spec.js")
        return out_path

    def read_file_name(self, path):
        filename = path[path.rfind(os.sep) + 1:-3]
        return filename

    def read_function_names(self, path):
        with open(path, 'rb') as f:
            javascript = f.readlines()
        # text is a list of lines from the file now, each ending in \n (except the last)
        function_names = [i[9:i.find("(")] for i in javascript if i.startswith("function ")]
        return function_names


if __name__ == "__main__":
    maker = TestMaker()
    maker.main(sys.argv)
