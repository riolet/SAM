import common
import json
import web
import re
import models.settings
import models.links
import base


class Stats(base.Headless):
    pageTitle = "Stats"

    def __init__(self):
        base.Headless.__init__(self)
        #TODO: restructure this file.
        self.sub = common.get_subscription()
        self.settingsModel = models.settings.Settings()
        self.table_links = "s{acct}_ds{{id}}_Links".format(acct=self.sub)
        self.stats = []

    def collect_stats(self, ds):
        table_links = self.table_links.format(id=ds)

        rows = common.db.query("SELECT dst AS 'Address' "
                               "FROM {table_links} GROUP BY Address;".format(table_links=table_links))
        destIPs = len(rows)
        self.stats.append(("Unique destination IP addresses:", str(destIPs)))

        rows = common.db.query("SELECT src AS 'Address' "
                               "FROM {table_links} GROUP BY Address;".format(table_links=table_links))
        self.stats.append(("Unique source IP addresses:", str(len(rows))))

        rows = common.db.query("SELECT DISTINCT port AS 'Port' "
                               "FROM {table_links};".format(table_links=table_links))

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
            "FROM {table_links} GROUP BY Address ORDER BY Ports DESC, Connections DESC LIMIT 100;"
                .format(table_links=table_links))
        if len(rows) > 0:
            lrows = rows.list()
            self.stats.append(("Max ports for one destination: ", str(lrows[0]['Ports'])))
            count = 0
            while count < len(lrows) and lrows[count]['Ports'] > 10:
                count += 1
            if count != len(lrows):
                self.stats.append(("Percent of destinations with fewer than 10 ports: ", "{0:0.3f}%"
                                   .format((destIPs - count) * 100 / float(destIPs))))

        rows = common.db.query("SELECT 1 FROM {table_links} GROUP BY src, dst, port;".format(table_links=table_links))
        self.stats.append(("Total Number of distinct connections (node -> node:port) stored:", str(len(rows))))
        rows = common.db.query("SELECT SUM(links) AS 'links' FROM {table_links} "
                               "GROUP BY src, dst, port HAVING links > 100;".format(table_links=table_links))
        self.stats.append(("Number of distinct connections occurring more than 100 times:", str(len(rows))))

    @staticmethod
    def decode_ds(data):
        ds_match = re.search("(\d+)", data.get('ds', ''))
        settingsModel = models.settings.Settings()
        default_ds = settingsModel['datasource']

        if ds_match:
            try:
                ds = int(ds_match.group())
            except ValueError:
                ds = default_ds
        else:
            ds = default_ds

        return ds

    def decode_get_request(self, data):
        query = data.get('q')
        if not query:
            raise base.RequiredKey('query', 'q')

        ds = self.decode_ds(data)

        return {'query': query, 'ds': ds}

    def perform_get_command(self, request):
        if request['query'] == 'timerange':
            linksModel = models.links.Links(request['ds'])
            return linksModel.get_timerange()
        elif request['query'] == 'protocols':
            linksModel = models.links.Links(request['ds'])
            return linksModel.get_protocol_list()
        else:
            raise base.MalformedRequest("Query not recognized.")

    def encode_get_response(self, response):
        return response

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        if "q" in self.inbound:
            return base.Headless.GET(self)

        else:
            ds = self.decode_ds(self.inbound)
            self.collect_stats(ds)
            return str(common.render._head(self.pageTitle)) \
                   + str(common.render._header(common.navbar, self.pageTitle)) \
                   + str(common.render.stats(self.stats)) \
                   + str(common.render._tail())
