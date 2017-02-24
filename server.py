import sys
import os
sys.path.append(os.path.dirname(__file__))
import web
import constants
import integrity

# web.config.debug = False

# Manage routing from here. Regex matches URL and chooses class by name


# Validate the database format
integrity.check_and_fix_integrity()

if __name__ == "__main__":
    app = web.application(constants.urls, globals())
    app.run()
