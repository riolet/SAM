function Node(alias, address, number, level, connections, x, y, radius, inputs, outputs) {
    "use strict";
    this.alias = alias.toString();
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
    server: false          //whether this node acts as a server
};

function closestEmptyPort(link, used) {
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

function preprocessConnection32(links) {
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
        choice = closestEmptyPort(links[j], used);
        if (choice === undefined) {
            continue;
        }
        ports[links[j].port] = locations[choice];
        if (links[j].shortname !== null) {
            ports[links[j].port].alias = links[j].shortname;
        }
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
                link.x1 += source.radius;
                link.x2 -= destination.radius;
            } else {
                link.x1 -= source.radius;
                link.x2 += destination.radius;
            }
            if (dy > 0) {
                link.y1 += source.radius;
                link.y2 -= destination.radius;
            } else {
                link.y1 -= source.radius;
                link.y2 += destination.radius;
            }
        }
    });
}

function preprocessConnection(link) {
    "use strict";
    //TODO: move this preprocessing into the database (preprocess.py) instead of client-side.
    var source = {};
    var destination = {};
    if (link.hasOwnProperty("source32")) {
        source = findNode(link.source8, link.source16, link.source24, link.source32);
        destination = findNode(link.dest8, link.dest16, link.dest24, link.dest32);
    } else if (link.hasOwnProperty("source24")) {
        source = findNode(link.source8, link.source16, link.source24);
        destination = findNode(link.dest8, link.dest16, link.dest24);
    } else if (link.hasOwnProperty("source16")) {
        destination = findNode(link.dest8, link.dest16);
        source = findNode(link.source8, link.source16);
    } else {
        destination = findNode(link.dest8);
        source = findNode(link.source8);
    }

    var dx = link.x2 - link.x1;
    var dy = link.y2 - link.y1;

    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //leftward flowing
            link.x1 -= source.radius;
            link.x2 += destination.radius;
            link.y1 += source.radius * 0.2;
            link.y2 += destination.radius * 0.2;
        } else {
            //rightward flowing
            link.x1 += source.radius;
            link.x2 -= destination.radius;
            link.y1 -= source.radius * 0.2;
            link.y2 -= destination.radius * 0.2;
        }
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //upward flowing
            link.y1 -= source.radius;
            link.y2 += destination.radius;
            link.x1 += source.radius * 0.2;
            link.x2 += destination.radius * 0.2;
        } else {
            //downward flowing
            link.y1 += source.radius;
            link.y2 -= destination.radius;
            link.x1 -= source.radius * 0.2;
            link.x2 -= destination.radius * 0.2;
        }
    }
}

function onLoadData(result) {
    "use strict";
    // result should be an array of objects
    // where each object has address, alias, connections, x, y, radius,
    nodeCollection = {};
    result.forEach(function (node) {
        var name = node.address;
        nodeCollection[node.address] = new Node(name, name, node.address, 8, node.connections, node.x, node.y, node.radius, node.inputs, node.outputs);
    });

    Object.keys(nodeCollection).forEach(function (key) {
        nodeCollection[key].inputs.forEach(preprocessConnection);
        nodeCollection[key].outputs.forEach(preprocessConnection);
    });

    resetViewport(nodeCollection);
    updateRenderRoot();
    render(tx, ty, scale);
}

// Function(jqXHR jqXHR, String textStatus, String errorThrown)
function onNotLoadData(xhr, textStatus, errorThrown) {
    "use strict";
    console.log("Failed to load data:");
    console.log("\t" + textStatus);
    console.log("\t" + errorThrown);
}

function loadData() {
    "use strict";
    $.ajax({
        url: "/query",
        data: {"filter": filter},
        success: onLoadData,
        error: onNotLoadData
    });
}

function loadChildren(parent, callback) {
    "use strict";
    if (parent.childrenLoaded === true) {
        return;
    }

    parent.childrenLoaded = true;
    //console.log("Loading children of " + node.address);
    var temp = parent.address.split(".");
    var requestData = {"ip24": -1, "ip16": -1, "ip8": -1};
    if (temp.length >= 3) {
        requestData.ip24 = temp[2];
    }
    if (temp.length >= 2) {
        requestData.ip16 = temp[1];
    }
    if (temp.length >= 1) {
        requestData.ip8 = temp[0];
    }
    requestData.filter = filter;

    $.ajax({
        url: "/query",
        type: "GET",
        data: requestData,
        dataType: "json",
        error: onNotLoadData,
        success: function (result) {
            // result should be an array of objects
            // where each object has address, alias, connections, x, y, radius,
            result.forEach(function (child) {
                //console.log("Loaded " + node.alias + " -> " + result[row].address);
                var name = parent.alias + "." + child.address;
                parent.children[child.address] = new Node(name, name, child.address, parent.level + 8, child.connections, child.x, child.y, child.radius, child.inputs, child.outputs);
            });
            // process the connections
            Object.keys(parent.children).forEach(function (child) {
                if (parent.children[child].level === 32) {
                    preprocessConnection32(parent.children[child].inputs);
                } else {
                    parent.children[child].inputs.forEach(preprocessConnection);
                }
                parent.children[child].outputs.forEach(preprocessConnection);
            });
            if (typeof callback === "function") {
                callback();
            } else {
                updateRenderRoot();
                render(tx, ty, scale);
            }
        }
    });
}

function checkLoD() {
    "use strict";
    var visible = onScreen();

    visible.forEach(function (node) {
        if (node.level < currentLevel()) {
            loadChildren(node);
        }
    });
    updateRenderRoot();
    render(tx, ty, scale);
}

function updateSelection(node) {
    "use strict";
    selection = node;
    document.getElementById("unique_in").innerHTML = "0";
    document.getElementById("conn_in").innerHTML = "";
    document.getElementById("conn_in_overflow").innerHTML = "";
    document.getElementById("unique_out").innerHTML = "0";
    document.getElementById("conn_out").innerHTML = "";
    document.getElementById("conn_out_overflow").innerHTML = "";
    document.getElementById("unique_ports").innerHTML = "0";
    document.getElementById("ports_in").innerHTML = "";
    document.getElementById("ports_in_overflow").innerHTML = "";
    document.getElementById("selectionNumber").innerHTML = "";
    if (node === null) {
        document.getElementById("selectionName").innerHTML = "No selection";
        return;
    }
    document.getElementById("selectionName").innerHTML = "Loading details...";

    var temp = node.address.split(".");
    var requestData = {"ip32": -1, "ip24": -1, "ip16": -1, "ip8": -1};
    if (temp.length >= 4) {
        requestData.ip32 = temp[3];
    }
    if (temp.length >= 3) {
        requestData.ip24 = temp[2];
    }
    if (temp.length >= 2) {
        requestData.ip16 = temp[1];
    }
    if (temp.length >= 1) {
        requestData.ip8 = temp[0];
    }

    $.ajax({
        url: "/details",
        //dataType: "json",
        type: "GET",
        data: requestData,
        error: onNotLoadData,
        success: function (result) {
            document.getElementById("selectionName").innerHTML = "\"" + node.alias + "\"";
            document.getElementById("selectionNumber").innerHTML = node.address;
            document.getElementById("unique_in").innerHTML = result.unique_in;
            document.getElementById("unique_out").innerHTML = result.unique_out;
            document.getElementById("unique_ports").innerHTML = result.unique_ports;

            var conn_in = "";
            var conn_out = "";
            var ports_in = "";
            conn_in = result.conn_in.reduce(function (accum, connection) {
                //connection === (ip address, [ports])
                accum += "<tr><td rowspan=\"" + connection[1].length + "\">" + connection[0] + "</td>";
                accum += connection[1].reduce(function (ports, port) {
                    if (port.shortname === null) {
                        ports += "<td>" + port.port + "</td><td>" + port.links + "</td></tr><tr>";
                    } else {
                        ports += "<td>" + port.port + " - " + port.shortname + "</td><td>" + port.links + "</td></tr><tr>";
                    }
                    return ports;
                }, "");
                //erase the last opening <tr> tag
                return accum.substring(0, accum.length - 4);
            }, "");
            conn_out = result.conn_out.reduce(function (accum, connection) {
                //connection === (ip address, [ports])
                accum += "<tr><td rowspan=\"" + connection[1].length + "\">" + connection[0] + "</td>";
                accum += connection[1].reduce(function (ports, port) {
                    if (port.shortname === null) {
                        ports += "<td>" + port.port + "</td><td>" + port.links + "</td></tr><tr>";
                    } else {
                        ports += "<td>" + port.port + " - " + port.shortname + "</td><td>" + port.links + "</td></tr><tr>";
                    }
                    return ports;
                }, "");
                //erase the last opening <tr> tag
                return accum.substring(0, accum.length - 4);
            }, "");
            ports_in = result.ports_in.reduce(function (accum, port) {
                //result.ports_in === [{port, links, shortname, longname}, ...]
                //port === {port, links, shortname, longname}
                if (port.shortname === null) {
                    accum += "<tr><td>" + port.port + "</td><td>" + port.links + "</td></tr>";
                } else {
                    accum += "<tr><td>" + port.port + " - " + port.shortname + "</td><td>" + port.links + "</td></tr>";
                }
                return accum;
            }, "");

            document.getElementById("conn_in").innerHTML = conn_in;
            document.getElementById("conn_out").innerHTML = conn_out;
            document.getElementById("ports_in").innerHTML = ports_in;

            //indicate any overflow that hasn't been loaded
            var overflow = 0;
            var overflow_text = "";
            if (result.conn_in.length < result.unique_in) {
                overflow = result.unique_in - result.conn_in.length;
                overflow_text = "<tr><th>Plus " + overflow + " more...</th><th colspan=\"2\"></th></tr>";
                document.getElementById("conn_in_overflow").innerHTML = overflow_text;
            }
            if (result.conn_out.length < result.unique_out) {
                overflow = result.unique_out - result.conn_out.length;
                overflow_text = "<tr><th>Plus " + overflow + " more...</th><th colspan=\"2\"></th></tr>";
                document.getElementById("conn_out_overflow").innerHTML = overflow_text;
            }
            if (result.ports_in.length < result.unique_ports) {
                overflow = result.unique_ports - result.ports_in.length;
                overflow_text = "<tr><th>Plus " + overflow + " more...</th><th></th></tr>";
                document.getElementById("ports_in_overflow").innerHTML = overflow_text;
            }
            updateFloatingPanel();
        }
    });
}