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

function node_reset() {
  "user strict";
  m_nodes = {};
  GET_nodes(null);
}

function get_node_name(node) {
    "use strict";
    if (node.alias.length === 0) {
        return node.number.toString();
    } else {
        return node.alias;
    }
}

function get_node_address(node) {
    "use strict";
    var add = node.address;
    var missing_terms = 4 - add.split(".").length;
    while (missing_terms > 0) {
        add += ".0";
        missing_terms -= 1;
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
    POST_node_alias(node.address, name);
    node.alias = name;
    render_all();
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

function node_info_click() {
    "use strict";
    //var node = m_selection['selection'];

    $('.ui.modal.nodeinfo')
        .modal({
            onApprove : function () { console.log("approved!"); }
        })
        .modal('show')
    ;
}

/**
 * Determine the last given number in this node's dotted decimal address.
 * ex: this node is 192.168.174.0/24,
 *     this returns 174 because it's the right-most number in the subnet.
 *
 * @param node object returned from the server. Different from Node object in javascript.
 *      should contain [ "connections", "alias", "radius", "y", "x", "ip8", "children" ] or more
 * @returns a subnet-local Number address
 */
function determine_number(node) {
    "use strict";
    var size = parseInt(node.ipend) - parseInt(node.ipstart)
    if (size === 0) {
        return node.ipstart % 256;
    }
    if (size === 255) {
        return node.ipstart / 256 % 256;
    }
    if (size === 65535) {
        return node.ipstart / 65536 % 256;
    }
    if (size === 16777215) {
        return node.ipstart / 16777216 % 256;
    }
    console.error("failed to determine size (" + size + ") when " + node.ipend + " - " + node.ipstart + ".");
    return undefined
}

/**
 *
 * @param parent Node object, ex: m_nodes['66'], or null if top-level
 * @param node the server node object, from a recent AJAX query
 */
function import_node(parent, node) {
    "use strict";
    var number = determine_number(node);
    if (parent === null) {
        m_nodes[number] = new Node(node.alias, number.toString(), number, 8, node.connections, node.x, node.y, node.radius);
    } else {
        var name = parent.address + "." + number.toString();
        parent.children[number] = new Node(node.alias, name, number, parent.subnet + 8, node.connections, node.x, node.y, node.radius);
    }
}

// `response` should be an object, where keys are address strings ("12.34.56.78") and values are arrays of objects (nodes)
function node_update(response) {
    "use strict";
    Object.keys(response).forEach(function (parent_address) {
        if (parent_address === "_") {
            //must be a call using null, update everything
            m_nodes = {};
            response[parent_address].forEach(function (node) {
                import_node(null, node);
            });
			if (subnetLabel == "") { //resets view if we aren't zoomed in.
            	resetViewport(m_nodes);
			}

        } else {
            var parent = findNode(parent_address);
            response[parent_address].forEach(function (node) {
                import_node(parent, node);
            });
        }
    });
    link_request_submit();
    updateRenderRoot();
    render_all();
}
