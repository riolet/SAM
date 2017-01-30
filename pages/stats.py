import common
import dbaccess
import json
import web
import time
from datetime import datetime
import re


class Stats:
    pageTitle = "Stats"
    stats = []

    def __init__(self):
        self.settings = dbaccess.get_settings_cached()
        self.prefix = self.settings['prefix']

    def collect_stats(self):

        rows = common.db.query("SELECT dst AS 'Address' "
                               "FROM {prefix}Links GROUP BY Address;".format(prefix=self.prefix))
        destIPs = len(rows)
        self.stats.append(("Unique destination IP addresses:", str(destIPs)))

        rows = common.db.query("SELECT src AS 'Address' "
                               "FROM {prefix}Links GROUP BY Address;".format(prefix=self.prefix))
        self.stats.append(("Unique source IP addresses:", str(len(rows))))

        rows = common.db.query("SELECT DISTINCT port AS 'Port' "
                               "FROM {prefix}Links;".format(prefix=self.prefix))

        lrows = rows.list()
        self.stats.append(("Unique destination ports:", str(len(lrows))))
        sys_lrows = [i for i in lrows if i['Port'] < 1024]
        self.stats.append(("Unique system ports (0..1023):", str(len(sys_lrows))))
        usr_lrows = [i for i in lrows if 1024 <= i['Port'] < 49152]
        self.stats.append(("Unique user ports (1024..49151):", str(len(usr_lrows))))
        prv_lrows = [i for i in lrows if 49152 <= i['Port'] < 65536]
        self.stats.append(("Unique private ports (49152..65535):", str(len(prv_lrows))))

        rows = common.db.query(
            "SELECT dst AS 'Address', COUNT(DISTINCT port) AS 'Ports', COUNT(links) AS 'Connections' "
            "FROM {prefix}Links GROUP BY Address ORDER BY Ports DESC, Connections DESC LIMIT 100;"
                .format(prefix=self.prefix))
        if len(rows) > 0:
            lrows = rows.list()
            self.stats.append(("Max ports for one destination: ", str(lrows[0]['Ports'])))
            count = 0
            while count < len(lrows) and lrows[count]['Ports'] > 10:
                count += 1
            if count != len(lrows):
                self.stats.append(("Percent of destinations with fewer than 10 ports: ", "{0:0.3f}%"
                                   .format((destIPs - count) * 100 / float(destIPs))))

        rows = common.db.query("SELECT 1 FROM {prefix}Links GROUP BY src, dst, port;".format(prefix=self.prefix))
        self.stats.append(("Total Number of distinct connections (node -> node:port) stored:", str(len(rows))))
        rows = common.db.query("SELECT SUM(links) AS 'links' FROM {prefix}Links "
                               "GROUP BY src, dst, port HAVING links > 100;".format(prefix=self.prefix))
        self.stats.append(("Number of distinct connections occurring more than 100 times:", str(len(rows))))

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        get_data = web.input()
        if "q" in get_data:
            query = get_data['q']
            if query == "timerange":
                ds_match = re.search("(\d+)", get_data.get('ds', "0"))
                if ds_match:
                    ds = int(ds_match.group())
                else:
                    ds = 0
                web.header("Content-Type", "application/json")
                return json.dumps(dbaccess.get_timerange(ds))
            elif query == "protocols":
                ds_match = re.search("(\d+)", get_data.get('ds', "0"))
                if ds_match:
                    ds = int(ds_match.group())
                else:
                    ds = 0
                web.header("Content-Type", "application/json")
                return json.dumps(dbaccess.get_protocol_list(ds))

        else:
            self.collect_stats()
            return str(common.render._head(self.pageTitle)) \
                   + str(common.render._header(common.navbar, self.pageTitle)) \
                   + str(common.render.stats(self.stats)) \
                   + str(common.render._tail())
