import re
import json
import decimal
import numbers
from sam import constants
import web
from sam import common
from sam import errors
from sam.models.settings import Settings
from sam.models.links import Links
from sam.models.datasources import Datasources
from sam.models.nodes import Nodes
from sam.models.subscriptions import Subscriptions
from sam.pages import base


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return obj.__float__()
    raise TypeError


class Stats(base.headed):
    pageTitle = "Stats"

    def __init__(self):
        super(Stats, self).__init__('Stats', True, True)
        # common.demo(on=False)
        # TODO: restructure this file.
        self.styles = ['/static/css/general.css']
        self.sub = None
        self.table_links = ''
        self.settingsModel = None

    def ds_stats(self, ds_id):
        table_links = self.table_links.format(id=ds_id)
        stats = []

        # get unique host information
        end_ips = set([row.ip for row in common.db.query("SELECT dst AS 'ip' FROM {table_links} GROUP BY ip"
                                                         .format(table_links=table_links))])
        stats.append(("Unique destination IP addresses:", str(len(end_ips))))

        source_ips = set([row.ip for row in common.db.query("SELECT src AS 'ip' FROM {table_links} GROUP BY ip"
                                                            .format(table_links=table_links))])
        stats.append(("Unique source IP addresses:", str(len(source_ips))))

        stats.append(("Unique IP addresses:", str(len(end_ips | source_ips))))

        # get unique destination ports and spread
        rows = common.db.query("SELECT DISTINCT port AS 'Port' FROM {table_links};"
                               .format(table_links=table_links))
        row_list = rows.list()
        stats.append(("Unique destination ports used:", str(len(row_list))))
        sys_row_list = [i for i in row_list if i['Port'] < 1024]
        stats.append(("Unique system ports used (0..1023):", str(len(sys_row_list))))
        usr_row_list = [i for i in row_list if 1024 <= i['Port'] < 49152]
        stats.append(("Unique user ports used (1024..49151):", str(len(usr_row_list))))
        prv_row_list = [i for i in row_list if 49152 <= i['Port'] < 65536]
        stats.append(("Unique private ports used (49152..65535):", str(len(prv_row_list))))

        rows = common.db.query(
            "SELECT dst AS 'Address', COUNT(DISTINCT port) AS 'Ports', COUNT(links) AS 'Connections' "
            "FROM {table_links} GROUP BY Address ORDER BY Ports DESC, Connections DESC LIMIT 100;"
                .format(table_links=table_links))
        row_list = list(rows)
        if len(row_list) > 0:
            stats.append(("Max ports for one destination: ", str(row_list[0]['Ports'])))
            count = 0
            while count < len(row_list) and row_list[count]['Ports'] > 10:
                count += 1
            if count != len(row_list):
                stats.append(("Percent of destinations with fewer than 10 ports: ", "{0:0.3f}%"
                              .format((len(end_ips) - count) * 100 / float(len(end_ips)))))

        rows = common.db.query("SELECT 1 FROM {table_links} GROUP BY src, dst, port;".format(table_links=table_links))
        row_list = list(rows)
        stats.append(("Total Number of distinct connections (node -> node:port) stored:", str(len(row_list))))
        rows = common.db.query("SELECT SUM(links) AS 'links' FROM {table_links} "
                               "GROUP BY src, dst, port HAVING links > 100;".format(table_links=table_links))
        row_list = list(rows)
        stats.append(("Number of distinct connections occurring more than 100 times:", str(len(row_list))))

        return stats

    def overall_stats(self):
        # ds_model = Datasources(self.session, self.sub)
        node_model = Nodes(common.db, self.sub)
        stats = [('Total hosts recorded', len(node_model.get_all_endpoints()))]
        return stats

    def decode_ds(self, data):
        ds_match = re.search("(\d+)", data.get('ds', ''))
        default_ds = self.settingsModel['datasource']

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
            raise errors.RequiredKey('query', 'q')

        ds = self.decode_ds(data)

        return {'query': query, 'ds': ds}

    def perform_get_command(self, request):
        self.page.require_group('read')
        if request['query'] == 'timerange':
            linksModel = Links(common.db, self.sub, request['ds'])
            return linksModel.get_timerange()
        elif request['query'] == 'protocols':
            linksModel = Links(common.db, self.sub, request['ds'])
            return linksModel.get_protocol_list()
        else:
            raise errors.MalformedRequest("Query not recognized.")

    def encode_get_response(self, response):
        return response

    def headless_get(self):
        self.sub = self.page.user.viewing
        if self.sub is None:
            sub_model = Subscriptions(common.db)
            self.sub = sub_model.get_by_email(constants.subscription['default-email'])
        if isinstance(self.sub, numbers.Integral):
            self.settingsModel = Settings(common.db, self.page.session, self.sub)
        else:
            self.outbound = {'result': 'failure', 'message': 'could not determine subscription information.'}
            return json.dumps(self.outbound, default=decimal_default)

        try:
            self.request = self.decode_get_request(self.page.inbound)
            self.response = self.perform_get_command(self.request)
            self.outbound = self.encode_get_response(self.response)
        except errors.MalformedRequest as e:
            self.outbound = {'result': 'failure', 'message': e.message}
        web.header("Content-Type", "application/json")
        return json.dumps(self.outbound, default=decimal_default)

    def headed_get(self):
        self.page.require_group('read')
        self.sub = self.page.user.viewing
        self.settingsModel = Settings(common.db, self.page.session, self.sub)
        self.table_links = "s{acct}_ds{{id}}_Links".format(acct=self.sub)

        segments = []
        segments.append(('Overall', self.overall_stats()))
        ds_model = Datasources(common.db, self.page.session, self.sub)
        for ds_id in ds_model.ds_ids:
            section_name = 'Datasource: {0}'.format(ds_model.datasources[ds_id]['name'])
            segments.append((section_name, self.ds_stats(ds_id)))

        return self.render('stats', segments)

    def GET(self):
        if "q" in self.page.inbound:
            return self.headless_get()
        else:
            return self.headed_get()
