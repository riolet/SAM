import common

class Stats:
    pageTitle = "Stats"
    stats = []

    def collect_stats(self):
        self.stats = []
        dbworks = common.test_database()
        if dbworks == 1049:  #database not found
            common.create_database()
        elif dbworks == 1045:  #invalid username/password
            self.stats.append(("Access Denied. Check username/password?", "Error 1045"))
            return

        rows = common.db.query("SELECT COUNT(*) AS 'cnt' FROM Syslog;")
        self.stats.append(("Number of rows imported from the Syslog:", str(rows[0]['cnt'])))

        rows = common.db.query("SELECT DestinationIP AS 'Address', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Address;")
        destIPs = len(rows)
        self.stats.append(("Unique destination IP addresses:", str(destIPs)))

        rows = common.db.query("SELECT SourceIP AS 'Address', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Address;")
        self.stats.append(("Unique source IP addresses:", str(len(rows))))

        rows = common.db.query("SELECT DestinationPort AS 'Port', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Port;")
        lrows = rows.list()
        self.stats.append(("Unique destination ports:", str(len(lrows))))
        lrows = [i for i in lrows if i['Port'] < 32768]
        self.stats.append(("Unique destination ports (under 32768):", str(len(lrows))))

        rows = common.db.query("SELECT DestinationIP AS 'Address', COUNT(DISTINCT DestinationPort) AS 'Ports', COUNT(*) AS 'Connections' FROM Syslog GROUP BY Address ORDER BY Ports DESC, Connections DESC LIMIT 100;")
        if len(rows) > 0:
            lrows = rows.list()
            self.stats.append(("Max ports for one destination: ", str(lrows[0]['Ports'])))
            count = 0
            while count < len(lrows) and lrows[count]['Ports'] > 10:
                count += 1
            if count != len(lrows):
                self.stats.append(("Percent of destinations with fewer than 10 ports: ", "{0:0.3f}%".format((destIPs - count) * 100 / float(destIPs))))

        rows = common.db.query("SELECT COUNT(*) FROM Syslog GROUP BY SourceIP, DestinationIP, DestinationPort;")
        self.stats.append(("Total Number of distinct connections (node -> node:port) stored:", str(len(rows))))
        rows = common.db.query("SELECT COUNT(*) FROM Syslog GROUP BY SourceIP, DestinationIP, DestinationPort HAVING COUNT(*) > 100;")
        self.stats.append(("Number of distinct connections occurring more than 100 times:", str(len(rows))))


    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        self.collect_stats()
        return str(common.render._head(self.pageTitle)) \
             + str(common.render._header(common.navbar, self.pageTitle)) \
             + str(common.render.stats(self.stats)) \
             + str(common.render._tail())