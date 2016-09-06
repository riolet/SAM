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
    "use strict";
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
    "use strict";
    var address = determine_address(node);
    if (parent === null) {
        m_nodes[address] = new Node(node.alias, address, address, 8, node.connections, node.x, node.y, node.radius);
    } else {
        var name = parent.address + "." + address;
        parent.children[address] = new Node(node.alias, name, address, parent.subnet + 8, node.connections, node.x, node.y, node.radius);
    }
}

// `response` should be an object, where keys are address strings ("12.34.56.78") and values are arrays of objects (nodes)
function node_update(response) {
    "use strict";
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
        }
    });
    port_request_submit();
    link_request_submit();
}