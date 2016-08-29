var m_nodes = {};

function Node(alias, address, number, subnet, connections, x, y, radius) {
    "use strict";
    if (typeof alias === "string") {
        this.alias = alias;  //Custom address translation
    } else {
        this.alias = "";
    }
    this.address = address.toString();  //address: 12.34.56.78
    this.number = number;               //ip segment number: 78
    this.subnet = subnet;               //ip subnet number: 8, 16, 24, 32
    this.connections = connections;     //number of connections (not unique) this node is involved in
    this.x = x;                         //render: x position in graph
    this.y = y;                         //render: y position in graph
    this.radius = radius;               //render: radius
    this.children = {};                 //child nodes (if this is subnet 8, 16, or 24)
    this.childrenLoaded = false;        //whether the children have been loaded
    this.inputs = [];                   //input connections. an array like: [(ip, [port, ...]), ...]
    this.outputs = [];                  //output connections. an array like: [(ip, [port, ...]), ...]
    this.ports = {};                    //ports by which other nodes connect to this one ( /32 only). Contains a key for each port number
    this.server = false;                //whether this node acts as a client
    this.client = false;                //whether this node acts as a server
    this.details = {"loaded": false};   //detailed information about this node (aliases, metadata, selection panel stuff)

    //queue the node to have links loaded
    link_request_add(address.toString());
}

function get_node_name(node) {
    "use strict";
    if (node.alias.length === 0) {
        return node.number;
    } else {
        return node.alias;
    }
}

function get_node_address(node) {
    "use strict";
    var add = node.address;
    var terms = 4 - add.split(".").length;
    while (terms > 0) {
        add += ".0";
        terms -= 1;
    }
    if (node.subnet < 32) {
        add += "/" + node.subnet;
    }
    return add;
}

function set_node_name(node, name) {
    "use strict";
    var oldName = node.alias;
    if (oldName === name) {
        return;
    }
    POST_node_alias(node, name);
    node.alias = name;
    render(tx, ty, scale);
}

function node_alias_submit(event) {
    "use strict";
    if (event.keyCode === 13 || event.type === "blur") {
        var newName = document.getElementById("node_alias_edit");
        set_node_name(m_selection["selection"], newName.value);
        return true;
    }
    return false;
}

function node_info_click(event) {
    "use strict";
    var node = m_selection['selection'];

    $('.ui.modal.nodeinfo')
        .modal({
            onApprove : function () { console.log("approved!"); }
        })
        .modal('show')
    ;
}

function determine_address(node) {
    if (node.hasOwnProperty("ip32")) {
        return node.ip32
    }
    if (node.hasOwnProperty("ip24")) {
        return node.ip24
    }
    if (node.hasOwnProperty("ip16")) {
        return node.ip16
    }
    if (node.hasOwnProperty("ip8")) {
        return node.ip8
    }
    return undefined
}

function import_node(parent, node) {
    address = determine_address(node);
    if (parent === null) {
        m_nodes[address] = new Node(node.alias, address, address, 8, node.connections, node.x, node.y, node.radius);
    } else {
        var name = parent.address + "." + address;
        parent.children[address] = new Node(node.alias, name, address, parent.subnet + 8, node.connections, node.x, node.y, node.radius);
    }
}

// `response` should be an object, where keys are address strings ("12.34.56.78") and values are arrays of objects (nodes)
function node_update(response) {
    Object.keys(response).forEach(function (parent_address) {
        if (parent_address === "_") {
            //must be top subnet
            m_nodes = {};
            response[parent_address].forEach(function (node) {
                import_node(null, node);
            });
            resetViewport(m_nodes);
        } else {
            parent = findNode(parent_address);
            response[parent_address].forEach(function (node) {
                import_node(parent, node);
            });
            Object.keys(parent.children).forEach(function (child) {
                if (parent.children[child].subnet === 32) {
                    node_processPorts(parent.children[child].inputs);
                }
            });
        }
    });
    port_request_submit();
    link_request_submit();
}

function node_closestEmptyPort(link, used) {
    "use strict";
    var right = [1, 0, 2, 7, 3, 6, 4, 5];
    var top = [3, 2, 4, 1, 5, 0, 6, 7];
    var bottom = [6, 7, 5, 0, 4, 1, 3, 2];
    var left = [4, 5, 3, 6, 2, 7, 1, 0];

    var dx = link.x2 - link.x1;
    var dy = link.y2 - link.y1;

    var chooser = function (i) {
        return used[i] === false;
    };
    var choice;

    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //port on right
            choice = right.find(chooser);
        } else {
            //port on left
            choice = left.find(chooser);
        }
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //port on bottom
            choice = bottom.find(chooser);
        } else {
            //port on top
            choice = top.find(chooser);
        }
    }
    return choice;
}

function node_processPorts(links) {
    "use strict";
    if (links.length === 0) {
        return;
    }

    var destination = findNode(links[0].dest8, links[0].dest16,
            links[0].dest24, links[0].dest32);

    //
    //    3_2
    //  4|   |1
    //  5|___|0
    //    6 7
    //
    var used = [false, false, false, false, false, false, false, false];
    var locations = [{"x": destination.x + destination.radius, "y": destination.y + destination.radius / 3, "alias": "", "side": "right"},
            {"x": destination.x + destination.radius, "y": destination.y - destination.radius / 3, "alias": "", "side": "right"},
            {"x": destination.x + destination.radius / 3, "y": destination.y - destination.radius, "alias": "", "side": "top"},
            {"x": destination.x - destination.radius / 3, "y": destination.y - destination.radius, "alias": "", "side": "top"},
            {"x": destination.x - destination.radius, "y": destination.y - destination.radius / 3, "alias": "", "side": "left"},
            {"x": destination.x - destination.radius, "y": destination.y + destination.radius / 3, "alias": "", "side": "left"},
            {"x": destination.x - destination.radius / 3, "y": destination.y + destination.radius, "alias": "", "side": "bottom"},
            {"x": destination.x + destination.radius / 3, "y": destination.y + destination.radius, "alias": "", "side": "bottom"}];

    var ports = {};
    var j;
    var choice = 0;
    //the first 8 unique port numbers should be mapped to locations.
    for (j = 0; j < Object.keys(links).length; j += 1) {
        if (ports.hasOwnProperty(links[j].port)) {
            continue;
        }
        port_request_add(links[j].port);
        choice = node_closestEmptyPort(links[j], used);
        if (choice === undefined) {
            continue;
        }
        ports[links[j].port] = locations[choice];
        used[choice] = true;
        if (Object.keys(ports).length >= 8) {
            break;
        }
    }
    destination.ports = ports;

    links.forEach(function (link) {
        var source = findNode(link.source8, link.source16,
                link.source24, link.source32);

        //offset endpoints by radius
        var dx = link.x2 - link.x1;
        var dy = link.y2 - link.y1;

        if (ports.hasOwnProperty(link.port)) {
            if (ports[link.port].side === "top") {
                link.x2 = ports[link.port].x;
                link.y2 = ports[link.port].y - 0.6;
            } else if (ports[link.port].side === "left") {
                link.x2 = ports[link.port].x - 0.6;
                link.y2 = ports[link.port].y;
            } else if (ports[link.port].side === "right") {
                link.x2 = ports[link.port].x + 0.6;
                link.y2 = ports[link.port].y;
            } else if (ports[link.port].side === "bottom") {
                link.x2 = ports[link.port].x;
                link.y2 = ports[link.port].y + 0.6;
            } else {
                //this should never execute
                link.x2 = ports[link.port].x;
                link.y2 = ports[link.port].y;
            }
        } else {
            //align to corners
            if (dx > 0) {
                link.x1 = source.x + source.radius;
                link.x2 = destination.x - destination.radius;
            } else {
                link.x1 = source.x - source.radius;
                link.x2 = destination.x + destination.radius;
            }
            if (dy > 0) {
                link.y1 = source.y + source.radius;
                link.y2 = destination.y - destination.radius;
            } else {
                link.y1 = source.y - source.radius;
                link.y2 = destination.y + destination.radius;
            }
        }
    });
}