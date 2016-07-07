import sys
import web
import MySQLdb
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
    def create_database(self):
        saved_db = dbconfig.params.pop('db')
        with MySQLdb.connect(**dbconfig.params) as connection:
            connection.execute("CREATE DATABASE IF NOT EXISTS samapper;")
            connection.execute("USE samapper;")
            connection.execute("DROP TABLE IF EXISTS Links;")
            connection.execute("DROP TABLE IF EXISTS Nodes;")
            connection.execute("DROP TABLE IF EXISTS Syslog;")
            connection.execute("CREATE TABLE Syslog (entry INT UNSIGNED NOT NULL AUTO_INCREMENT, SourceIP INT UNSIGNED NOT NULL, SourcePort INT NOT NULL, DestinationIP INT UNSIGNED NOT NULL, DestinationPort INT NOT NULL, Occurances INT DEFAULT 1 NOT NULL, CONSTRAINT PKSyslog PRIMARY KEY (entry));")
            connection.execute("CREATE TABLE Nodes (IPAddress INT UNSIGNED NOT NULL, CONSTRAINT PKNodes PRIMARY KEY (IPAddress));")
            connection.execute("CREATE TABLE Links (SourceIP INT UNSIGNED NOT NULL, DestinationIP INT UNSIGNED NOT NULL, DestinationPort INT NOT NULL, CONSTRAINT PKLinks PRIMARY KEY (SourceIP, DestinationIP, DestinationPort), CONSTRAINT FKSrc FOREIGN KEY (SourceIP) REFERENCES Nodes (IPAddress), CONSTRAINT FKDest FOREIGN KEY (DestinationIP) REFERENCES Nodes (IPAddress));")
        dbconfig.params['db'] = saved_db


    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self, name):
        rows = []
        try:
            rows = db.select('Syslog')
        except Exception as e:
            # see http://dev.mysql.com/doc/refman/5.7/en/error-messages-server.html for codes
            if e[0] == 1049:  # Unknown database 'samapper'
                self.create_database()
                return self.GET(name)
            elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
                rows = [e[1], "Check you username / password? (dbconfig_local.py)"]
        # index is name of template.
        return render.index(name, rows)


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
