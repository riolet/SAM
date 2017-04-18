import time
import web
from sam import common
import threading
import sam.models.whois
from sam.models.links import Links


class Nodes(object):
    default_environments = {'production', 'dev', 'inherit'}

    def __init__(self, db, subscription):
        """
        :type db: web.DB
        :type subscription: int
        :param db: 
        :param subscription: 
        """
        self.db = db
        self.sub = subscription
        self.table_nodes = 's{acct}_Nodes'.format(acct=self.sub)
        self.table_tags = 's{acct}_Tags'.format(acct=self.sub)

    def set_alias(self, address, alias):
        """
        :param address: node address to edit. e.g. '10.20.30.40', '50.60', '192.0.0.0/24'
        :type address: unicode
        :param alias: name to use. string or none
        :type alias: unicode or None
        :return: 
        """
        r = common.determine_range_string(address)
        where = {"ipstart": r[0], "ipend": r[1]}
        self.db.update(self.table_nodes, where, alias=alias)

    def get(self, address):
        r = common.determine_range_string(address)
        qvars = {"start": r[0], "end": r[1]}
        rows = self.db.select(self.table_nodes, where="ipstart=$start and ipend=$end", vars=qvars)
        return rows.first()

    def set_tags(self, address, new_tags):
        """
        Assigns a new set of tags to an address overwriting any existing tag assignments.

        :param address: A string dotted-decimal IP address such as "192.168.2.100" or "21.66" or "1.2.0.0/16"
        :param new_tags: A list of tag strings. e.g. ['tag_one', 'tag_two', 'tag_three']
        :return: None
        """
        what = "ipstart, ipend, tag"
        r = common.determine_range_string(address)
        row = {"ipstart": r[0], "ipend": r[1]}
        where = "ipstart = $ipstart AND ipend = $ipend"

        existing = list(self.db.select(self.table_tags, vars=row, what=what, where=where))
        new_tags = set(new_tags)
        old_tags = {x.tag for x in existing}
        removals = old_tags - new_tags
        additions = new_tags - old_tags

        for tag in additions:
            row['tag'] = tag
            self.db.insert(self.table_tags, **row)

        for tag in removals:
            row['tag'] = tag
            where = "ipstart = $ipstart AND ipend = $ipend AND tag = $tag"
            self.db.delete(self.table_tags, where=where, vars=row)

    def get_tags(self, address):
        """
        Gets all directly assigned tags and inherited parent tags for a given addresss
    
        :param address: A string dotted-decimal IP address such as "192.168.2.100" or "21.66" or "1.2.0.0/16"
        :return: A dict of lists of strings, with keys 'tags' and 'p_tags'
                where p_tags are inherited tags from parent nodes
        """
        ipstart, ipend = common.determine_range_string(address)
        where = 'ipstart <= $start AND ipend >= $end'
        qvars = {'start': ipstart, 'end': ipend}
        data = self.db.select(self.table_tags, vars=qvars, where=where)
        parent_tags = []
        tags = []
        for row in data:
            if row.ipend == ipend and row.ipstart == ipstart:
                tags.append(row.tag)
            else:
                parent_tags.append(row.tag)
        return {"p_tags": parent_tags, "tags": tags}
    
    def get_tag_list(self):
        return [row.tag for row in self.db.select(self.table_tags, what="DISTINCT tag") if row.tag]

    def set_env(self, address, env):
        r = common.determine_range_string(address)
        where = {"ipstart": r[0], "ipend": r[1]}
        self.db.update(self.table_nodes, where, env=env)

    def get_env(self, address):
        ipstart, ipend = common.determine_range_string(address)
        where = 'ipstart <= $start AND ipend >= $end'
        qvars = {'start': ipstart, 'end': ipend}
        data = self.db.select(self.table_nodes, vars=qvars, where=where, what="ipstart, ipend, env")
        parent_env = "production"
        env = "inherit"
        nearest_distance = -1
        for row in data:
            if row.ipend == ipend and row.ipstart == ipstart:
                if row.env:
                    env = row.env
            else:
                dist = row.ipend - ipend + ipstart - row.ipstart
                if nearest_distance == -1 or dist < nearest_distance:
                    if row.env and row.env != "inherit":
                        parent_env = row.env
        return {"env": env, "p_env": parent_env}
    
    def get_env_list(self):
        envs = set(row.env for row in self.db.select(self.table_nodes, what="DISTINCT env") if row.env)
        envs |= self.default_environments
        return envs

    def delete_custom_tags(self):
        common.db.delete(self.table_tags, "1")

    def delete_custom_envs(self):
        common.db.update(self.table_nodes, "1", env=web.sqlliteral("NULL"))

    def delete_custom_hostnames(self):
        common.db.update(self.table_nodes, "1", alias=common.web.sqlliteral("NULL"))

    def get_root_nodes(self):
        return list(self.db.select(self.table_nodes, where="subnet=8"))

    def get_flat_nodes(self, ds):
        link_model = Links(self.db, self.sub, ds)
        query = """SELECT ipstart, ipend, subnet, alias, env, x, y, radius
FROM {t_nodes} AS `n`
  JOIN (SELECT src AS 'ip' from {t_links}
        UNION
        SELECT dst AS 'ip' from {t_links}) AS `lnks`
  ON `lnks`.ip = `n`.ipstart
WHERE `n`.ipstart=`n`.ipend;""".format(t_nodes=self.table_nodes, t_links=link_model.table_links)
        nodes = list(self.db.query(query))
        return nodes

    def get_children(self, address):
        ip_start, ip_end = common.determine_range_string(address)
        diff = ip_end - ip_start
        if diff > 16777215:
            subnet = 8
        elif diff > 65536:
            subnet = 16
        elif diff > 255:
            subnet = 24
        elif diff > 0:
            subnet = 32
        else:
            return []

        where = "subnet={2} AND ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end, subnet)
        rows = self.db.select(self.table_nodes, where=where)
        return list(rows)

    def get_all_endpoints(self):
        rows = self.db.select(self.table_nodes, what='ipstart', where='subnet=32')
        return [row['ipstart'] for row in rows]

    def delete_hosts(self, hostlist):
        # type: (Nodes, [str]) -> int
        collection = "({})".format(','.join(map(str, map(int, hostlist))))
        # int cast is to cause failure if sql injection attacks.
        # Almost equivalent to:
        #    hostlist = str(tuple(map(int, collection)))
        # Which is better?
        deleted = self.db.delete(self.table_nodes, where='ipstart=ipend and ipstart IN {hosts}'.format(hosts=collection))

        # the deleted endpoints may have (now childless) aggregate parents
        # TODO: delete childless parent nodes (e.g. subnets like /24)

        return deleted

    def delete_collection(self, nodes):
        """
        :type self: Nodes
        :type nodes: list[str]
        :param nodes: list of nodes to delete, along with their children
        :return: The number of nodes deleted
        :rtype: int
        """
        deleted = 0
        for node in nodes:
            low, high = common.determine_range_string(node)
            where = 'ipstart={low} and ipend={high}'.format(low=low, high=high)
            deleted += self.db.delete(self.table_nodes, where=where)

        return deleted


class WhoisService(threading.Thread):
    def __init__(self, db, sub, *args, **kwargs):
        super(WhoisService, self).__init__(*args, **kwargs)
        self.db = db
        self.sub = sub
        self.missing = []
        self.table = 's{acct}_Nodes'.format(acct=self.sub)
        self.n_model = Nodes(self.db, self.sub)
        self.alive = True

    def get_missing(self):
        where = 'subnet=32 AND alias IS NULL'
        rows = self.db.select(self.table, what='ipstart', where=where)
        missing = [common.IPtoString(row['ipstart']) for row in rows]
        return missing

    def run(self):
        # while there are missing hosts
        # run the lookup command
        # save the hostname
        print("starting whois run")
        while self.alive:
            self.missing = self.get_missing()
            while self.missing:
                address = self.missing.pop()
                try:
                    whois = sam.models.whois.Whois(address)
                    org = whois.ip_to_org()
                    self.n_model.set_alias(address, org)
                except:
                    continue
                if not self.alive:
                    break
            time.sleep(5)
        return

    def shutdown(self):
        self.alive = False