var m_nodes = {};

function Node(alias, address, number, level, connections, x, y, radius, inputs, outputs) {
    "use strict";
    if (typeof alias === "string") {
        this.alias = alias;
    } else {
        this.alias = "";
    }
    this.address = address.toString();
    this.number = number;
    this.level = level;
    this.connections = connections;
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.children = {};
    this.childrenLoaded = false;
    this.inputs = inputs;
    this.outputs = outputs;
    this.ports = {};
    if (inputs.length > 0) {
        this.server = true;
    }
    if (outputs.length > 0) {
        this.client = true;
    }
    this.details = {"loaded": false};
}

Node.prototype = {
    alias: "",             //DNS translation
    address: "0",          //address: 12.34.56.78
    number: 0,             //ip segment number: 78
    level: 8,              //ip segment/subnet: 8, 16, 24, or 32
    connections: 0,        //number of connections (not unique) this node is involved in
    x: 0,                  //render: x position in graph
    y: 0,                  //render: y position in graph
    radius: 0,             //render: radius
    children: {},          //child (subnet) nodes (if this is level 8, 16, or 24)
    childrenLoaded: false, //whether the children have been loaded
    inputs: [],            //input connections. an array like: [(ip, [port, ...]), ...]
    outputs: [],           //output connections. an array like: [(ip, [port, ...]), ...]
    ports: {},             //ports by which other nodes connect to this one ( /32 only). Contains a key for each port number
    client: false,         //whether this node acts as a client
    server: false,         //whether this node acts as a server
    details: {}            //detailed information about this node (aliases, metadata, selection panel stuff)
};

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
    if (node.level < 32) {
        add += "/" + node.level;
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

function import_node(parent, node) {
    if (parent === null) {
        m_nodes[node.address] = new Node(node.alias, node.address, node.address, 8, node.connections, node.x, node.y, node.radius, node.inputs, node.outputs);
    } else {
        var name = parent.address + "." + node.address;
        parent.children[node.address] = new Node(node.alias, name, node.address, parent.level + 8, node.connections, node.x, node.y, node.radius, node.inputs, node.outputs);
    }
}

// `response` should be an object, where keys are address strings ("12.34.56.78") and values are arrays of objects (nodes)
function node_update(response) {
    Object.keys(response).forEach(function (parent_address) {
        if (parent_address === "_") {
            //must be top level
            m_nodes = {};
            response[parent_address].forEach(function (node) {
                import_node(null, node);
            });
            Object.keys(m_nodes).forEach(function (key) {
                m_nodes[key].inputs.forEach(preprocessConnection);
                m_nodes[key].outputs.forEach(preprocessConnection);
            });
            resetViewport(m_nodes);
        } else {
            parent = findNode(parent_address);
            response[parent_address].forEach(function (node) {
                import_node(parent, node);
            });
            Object.keys(parent.children).forEach(function (child) {
                if (parent.children[child].level === 32) {
                    preprocessConnection32(parent.children[child].inputs);
                } else {
                    parent.children[child].inputs.forEach(preprocessConnection);
                }
                parent.children[child].outputs.forEach(preprocessConnection);
            });
        }
    });
    port_request_submit();
}