import web
import common

#TODO: test 'active' toggle -- it was moved to PortAlias from Ports

class Ports:
    MAX_NAME_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 255

    def __init__(self, subscription):
        self.db = common.db
        self.sub = subscription
        self.table_ports = "Ports"
        self.table_aliases = "s{acct}_PortAliases".format(acct=self.sub)

    def reset(self):
        # delete from table
        query_delete = "DELETE FROM {table_aliases}".format(table_aliases=self.table_aliases)
        self.db.query(query_delete)
        # copy from Ports
        query_insert = "INSERT INTO {table_aliases} (port, protocols, name, description) " \
                       "SELECT port, protocols, name, description " \
                       "FROM {table_ports}".format(
            table_aliases=self.table_aliases, table_ports=self.table_ports)
        self.db.query(query_insert)

    def get(self, ports):
        if isinstance(ports, list):
            arg = "({0})".format(",".join(map(str, ports)))
        else:
            arg = "({0})".format(ports)

        query = """SELECT ports.port, ports.name, ports.protocols, ports.description,
    aliases.active,
    aliases.name AS alias_name,
    aliases.description AS alias_description
FROM {table_ports} AS `ports`
RIGHT JOIN {table_aliases} AS `aliases`
    ON ports.port=aliases.port
WHERE ports.port IN {port_list}""".format(
            table_ports=self.table_ports,
            table_aliases=self.table_aliases,
            port_list=web.reparam(arg, {}))

        rows = self.db.query(query, vars={'plist': arg})
        return list(rows)

    def set(self, port, updates):
        formatted_updates = {}

        if 'alias_name' in updates:
            formatted_updates['name'] = updates['alias_name'][:self.MAX_NAME_LENGTH]
        if 'alias_description' in updates:
            formatted_updates['description'] = updates['alias_description'][:self.MAX_DESCRIPTION_LENGTH]
        if 'active' in updates:
            formatted_updates['active'] = 1 if str(updates['active']) == '1' else 0

        # update PortAliases database of names to include the new information
        exists = self.db.select(self.table_aliases, what="1", where={"port": port})

        if formatted_updates:
            if len(exists) == 1:
                common.db.update(self.table_aliases, {"port": port}, **formatted_updates)
            else:
                common.db.insert(self.table_aliases, port=port, **formatted_updates)
