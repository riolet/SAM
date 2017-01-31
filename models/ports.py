import web
import common


class Ports:
    MAX_NAME_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 255

    def __init__(self):
        self.db = common.db
        self.table = "Ports"
        self.table_aliases = "PortAliases"

    def get(self, ports):
        if isinstance(ports, list):
            arg = "({0})".format(",".join(map(str, ports)))
        else:
            arg = "({0})".format(ports)

        query = """
            SELECT Ports.port, Ports.active, Ports.name, Ports.description,
                PortAliases.name AS alias_name,
                PortAliases.description AS alias_description
            FROM {table}
            LEFT JOIN {alias_table}
                ON Ports.port=PortAliases.port
            WHERE Ports.port IN {port_list}
        """.format(table=self.table,
                   alias_table=self.table_aliases,
                   port_list=web.reparam(arg, {}))
        info = list(self.db.query(query))
        return info

    def set(self, port, updates):
        alias_name = ''
        alias_description = ''
        active = 0
        if 'alias_name' in updates:
            alias_name = updates['alias_name'][:self.MAX_NAME_LENGTH]
        if 'alias_description' in updates:
            alias_description = updates['alias_description'][:self.MAX_DESCRIPTION_LENGTH]
        if 'active' in updates:
            active = 1 if updates['active'] == '1' or updates['active'] == 1 else 0

        # update PortAliases database of names to include the new information
        exists = self.db.select(self.table_aliases, what="1", where={"port": port})

        if len(exists) == 1:
            kwargs = {}
            if 'alias_name' in updates:
                kwargs['name'] = alias_name
            if 'alias_description' in updates:
                kwargs['description'] = alias_description
            if kwargs:
                common.db.update(self.table_aliases, {"port": port}, **kwargs)
        else:
            common.db.insert(self.table_aliases, port=port, name=alias_name, description=alias_description)

        # update Ports database of default values to include the missing information
        exists = common.db.select('Ports', what="1", where={"port": port})
        if len(exists) == 1:
            if 'active' in updates:
                common.db.update(self.table, {"port": port}, active=active)
        else:
            common.db.insert(self.table, port=port, active=active, tcp=1, udp=1, name="", description="")
