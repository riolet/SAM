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
    '/', 'index',  # matched groups (in parens) are sent as arguments
    '/map', 'map',
    '/stats', 'stats'
)


class Common:
    navbar = [
        {
            "name": "Map",
            "icon": "sitemap",
            "link": "/map"
        },
        {
            "name": "Stats",
            "icon": "filter",
            "link": "/stats"
        }
    ]

    @staticmethod
    def test_database():
        result = 0;
        try:
            rows = db.query("SELECT COUNT(*) FROM Nodes")
        except Exception as e:
            result = e[0]
            # see http://dev.mysql.com/doc/refman/5.7/en/error-messages-server.html for codes
            # if e[0] == 1049:  # Unknown database 'samapper'
            #     Common.create_database()
            #     return self.GET(name)
            # elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
            #     rows = [e[1], "Check you username / password? (dbconfig_local.py)"]
        return result

    @staticmethod
    def create_database():
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


class index:
    pageTitle = "Overview"
    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        return str(render._head(self.pageTitle)) \
             + str(render._header(Common.navbar, self.pageTitle)) \
             + str(render.overview()) \
             + str(render._tail())


class map:
    pageTitle = "Map"
    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        return str(render._head(self.pageTitle)) \
             + str(render._header(Common.navbar, self.pageTitle)) \
             + str(render.map()) \
             + str(render._tail())


class stats:
    pageTitle = "Stats"
    stats = []

    def collect_stats(self):
        self.stats = []
        dbworks = Common.test_database()
        if dbworks == 1049:  #database not found
            Common.create_database()
            self.collect_stats()
        elif dbworks == 1045:  #invalid username/password
            self.stats.append(("Access Denied. Check username/password?", "Error 1045"))
            return

        rows = db.query("SELECT COUNT(*) AS 'cnt' FROM Syslog;")
        self.stats.append(("Number of rows imported from the Syslog:", str(rows[0]['cnt'])))

        rows = db.query("SELECT DestinationIP AS 'Address', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Address;")
        destIPs = len(rows)
        self.stats.append(("Unique destination IP addresses:", str(destIPs)))

        rows = db.query("SELECT SourceIP AS 'Address', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Address;")
        self.stats.append(("Unique source IP addresses:", str(len(rows))))

        rows = db.query("SELECT DestinationPort AS 'Port', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Port;")
        lrows = rows.list()
        self.stats.append(("Unique destination ports:", str(len(lrows))))
        lrows = [i for i in lrows if i['Port'] < 32768]
        self.stats.append(("Unique destination ports (under 32768):", str(len(lrows))))

        rows = db.query("SELECT DestinationIP AS 'Address', COUNT(DISTINCT DestinationPort) AS 'Ports', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Address ORDER BY Ports DESC, Connections DESC LIMIT 100;")
        lrows = rows.list()
        self.stats.append(("Max ports for one destination: ", str(lrows[0]['Ports'])))
        count = 0
        while count < len(lrows) and lrows[count]['Ports'] > 10:
            count += 1
        if count != len(lrows):
            self.stats.append(("Percent of destinations with fewer than 10 ports: ", "{0:0.3f}%".format((destIPs - count) * 100 / float(destIPs))))

        rows = db.query("SELECT COUNT(*) AS 'cnt' FROM (SELECT COUNT(*) FROM Syslog GROUP BY SourceIP, DestinationIP, DestinationPort) AS cnxs;")
        self.stats.append(("Total Number of distinct connections (node -> node:port) stored:", str(rows[0]['cnt'])))
        rows = db.query("SELECT COUNT(*) AS 'cnt' FROM (SELECT COUNT(*) FROM Syslog GROUP BY SourceIP, DestinationIP, DestinationPort HAVING COUNT(*) > 100) AS cnxs;")
        self.stats.append(("Number of distinct connections occurring more than 100 times:", str(rows[0]['cnt'])))


    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        self.collect_stats()
        return str(render._head(self.pageTitle)) \
             + str(render._header(Common.navbar, self.pageTitle)) \
             + str(render.stats(self.stats)) \
             + str(render._tail())


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
