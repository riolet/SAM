import json
import web
import dbaccess
import common


# This class is for getting the main selection details, such as ins, outs, and ports.


class Details:
    def GET(self):
        """
        The expected GET data includes:
            'address': dotted-decimal IP addresses.
                Each address is only as long as the subnet,
                    so 12.34.0.0/16 would be written as 12.34
            'filter': optional. If included, ignored.
            'tstart': optional. Used with 'tend'. The start of the time range to report links during.
            'tend': optional. Used with 'tstart'. The end of the time range to report links during.
        :return: A JSON-encoded dictionary where
            the keys are ['conn_in', 'conn_out', 'ports_in', 'unique_in', 'unique_out', 'unique_ports'] and
            the values are numbers or lists
        """
        web.header("Content-Type", "application/json")

        get_data = web.input()
        port_filter = -1  # get_data.get('filter', -1)
        timestart = get_data.get("tstart", 1)
        timeend = get_data.get("tend", 2 ** 31 - 1)
        timestart = int(timestart)
        timeend = int(timeend)

        if 'address' in get_data:
            ips = get_data["address"].split(".")
            ips = [int(i) for i in ips]

            details = dbaccess.get_details(*ips, port=port_filter, timerange=(timestart, timeend))

            conn_in = {}
            for connection in details['conn_in']:
                ip = common.IPtoString(connection.pop("ip"))
                if ip in conn_in:
                    # add a port
                    conn_in[ip] += [connection]
                else:
                    # add a new entry
                    conn_in[ip] = [connection]
            # convert to list of tuples to make it sortable
            conn_in = conn_in.items()
            conn_in.sort(key=key_by_link_sum, reverse=True)
            details['conn_in'] = conn_in

            conn_out = {}
            for connection in details['conn_out']:
                ip = common.IPtoString(connection.pop("ip"))
                if ip in conn_out:
                    # add a port
                    conn_out[ip] += [connection]
                else:
                    # add a new entry
                    conn_out[ip] = [connection]
            # convert to list of tuples to make it sortable
            conn_out = conn_out.items()
            conn_out.sort(key=key_by_link_sum, reverse=True)
            details['conn_out'] = conn_out
        else:
            details = {"result": "ERROR: Malformed request. The 'address' key was missing"}

        return json.dumps(details)


def key_by_link_sum(connection):
    tally = 0
    for con in connection[1]:
        tally += con.links
    return tally
