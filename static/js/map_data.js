function loadData() {
    $.ajax({
        url: "/query",
        success: onLoadData,
        error: onNotLoadData
        });
}

Node.prototype = {
    alias: "",
    address: 0,
    level: 8,
    connections: 0,
    x: 0,
    y: 0,
    radius: 0,
    children: {},
    childrenLoaded: false,
    inputs: [],
    ports: {}
};

function Node(address, alias, level, connections, x, y, radius, inputs) {
    this.address = address;
    this.alias = alias;
    this.level = level;
    this.connections = connections;
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.children = {};
    this.childrenLoaded = false;
    this.inputs = inputs;
    this.ports = {};
}

// Function(jqXHR jqXHR, String textStatus, String errorThrown)
function onNotLoadData(xhr, textStatus, errorThrown) {
    console.log("Failed to load data:");
    console.log("\t" + textStatus);
    console.log("\t" + errorThrown);
}

function onLoadData(result) {
    // result should be a json object.
    // I am expecting `result` to be an array of objects
    // where each object has address, alias, connections, x, y, radius,
    nodeCollection = {};
    console.log("Loaded base data:");
    console.log(result);
    console.log("rows: " + result.length);
    for (var row in result) {
        name = result[row].address;
        nodeCollection[result[row].address] = new Node(result[row].address, name, 8, result[row].connections, result[row].x, result[row].y, result[row].radius, result[row].inputs);
    }
    for (var i in nodeCollection) {
        for (var j in nodeCollection[i].inputs) {
            preprocessConnection(nodeCollection[i].inputs[j])
        }
    }

    renderCollection = nodeCollection;

    render(tx, ty, scale);
}

function checkLoD() {
    level = currentLevel();
    visible = onScreen();

    for (var i in visible) {
        if (visible[i].level < level && visible[i].childrenLoaded == false) {
            loadChildren(visible[i]);
        }
    }
    updateRenderRoot();
    render(tx, ty, scale);
}

function loadChildren(node) {
    node.childrenLoaded = true;
    //console.log("Dynamically loading children of " + node.alias);
    $.ajax({
        url: "/query/" + node.alias.split(".").join("/"),
        dataType: "json",
        error: onNotLoadData,
        success: function(result) {
        for (var row in result) {
            //console.log("Loaded " + node.alias + " -> " + result[row].address);
            name = node.alias + "." + result[row].address;
            node.children[result[row].address] = new Node(result[row].address, name, node.level + 8, result[row].connections, result[row].x, result[row].y, result[row].radius, result[row].inputs);
        }
        // process the connections
        for (var i in node.children) {
            if (node.children[i].level == 32) {
                preprocessConnection32(node.children[i].inputs)
            } else {
                for (var j in node.children[i].inputs) {
                    preprocessConnection(node.children[i].inputs[j])
                }
            }
        }
        updateRenderRoot()
        render(tx, ty, scale);
    }});
}

function preprocessConnection32(links) {
    if (links.length == 0) {
        return
    }

    var destination = findNode(links[0].dest8, links[0].dest16,
                               links[0].dest24, links[0].dest32);

    // I apologize for doing this this way...
    //
    //    3 2
    //  4|   |1
    //  5|   |0
    //    6 7
    //
    used = [false, false, false, false, false, false, false, false];
    locations = [ {'x':destination.x + destination.radius, 'y':destination.y + destination.radius/3, 'side': 'right'}
                , {'x':destination.x + destination.radius, 'y':destination.y - destination.radius/3, 'side': 'right'}
                , {'x':destination.x + destination.radius/3, 'y':destination.y - destination.radius, 'side': 'top'}
                , {'x':destination.x - destination.radius/3, 'y':destination.y - destination.radius, 'side': 'top'}
                , {'x':destination.x - destination.radius, 'y':destination.y - destination.radius/3, 'side': 'left'}
                , {'x':destination.x - destination.radius, 'y':destination.y + destination.radius/3, 'side': 'left'}
                , {'x':destination.x - destination.radius/3, 'y':destination.y + destination.radius, 'side': 'bottom'}
                , {'x':destination.x + destination.radius/3, 'y':destination.y + destination.radius, 'side': 'bottom'}
                ];

    var ports = {}
    for (var j in links) {
        if (links[j].port in ports) continue;
        var choice = closestEmptyPort(links[j], used);
        ports[links[j].port] = locations[choice];
        used[choice] = true;
        if (Object.keys(ports).length >= 8) break;
    }
    destination.ports = ports;

    for (let link of links) {
        var source = findNode(link.source8, link.source16,
                              link.source24, link.source32);

        //offset endpoints by radius
        var dx = link.x2 - link.x1;
        var dy = link.y2 - link.y1;

        if (link.port in ports) {
            if (ports[link.port].side == "top") {
                link.x2 = ports[link.port].x;
                link.y2 = ports[link.port].y - 0.6;
            } else if (ports[link.port].side == "left") {
                link.x2 = ports[link.port].x - 0.6;
                link.y2 = ports[link.port].y;
            } else if (ports[link.port].side == "right") {
                link.x2 = ports[link.port].x + 0.6;
                link.y2 = ports[link.port].y;
            } else if (ports[link.port].side == "bottom") {
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
    }
}

function closestEmptyPort(link, used) {
    var right = [1, 0, 2, 7, 3, 6, 4, 5];
    var top = [3, 2, 4, 1, 5, 0, 6, 7];
    var bottom = [6, 7, 5, 0, 4, 1, 3, 2];
    var left = [4, 5, 3, 6, 2, 7, 1, 0];

    var dx = link.x2 - link.x1;
    var dy = link.y2 - link.y1;

    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //port on right
            for (let i of right) {
                if (used[i] == false) return i;
            }
        } else {
            //port on left
            for (let i of left) {
                if (used[i] == false) return i;
            }
        }
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //port on bottom
            for (let i of bottom) {
                if (used[i] == false) return i;
            }
        } else {
            //port on top
            for (let i of top) {
                if (used[i] == false) return i;
            }
        }
    }
    return -1;
}

function preprocessConnection(link) {
    //TODO: move this preprocessing into the database (preprocess.py) instead of client-side.
    var source = {};
    var destination = {};
    if ("source32" in link) {
        source = findNode(link.source8, link.source16, link.source24, link.source32)
        destination = findNode(link.dest8, link.dest16, link.dest24, link.dest32)
    } else if ("source24" in link) {
        source = findNode(link.source8, link.source16, link.source24)
        destination = findNode(link.dest8, link.dest16, link.dest24)
    } else if ("source16" in link) {
        source = findNode(link.source8, link.source16)
        destination = findNode(link.dest8, link.dest16)
    } else {
        source = findNode(link.source8)
        destination = findNode(link.dest8)
    }

    //offset endpoints by radius
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

function updateSelection(node) {
    selection = node;
    if (node == null) {
        document.getElementById("selectionName").innerHTML = "No selection";
        document.getElementById("selectionNumber").innerHTML = "";
        document.getElementById("unique_in").innerHTML = "0";
        document.getElementById("full_unique_in").innerHTML = "";
        document.getElementById("unique_out").innerHTML = "0";
        document.getElementById("full_unique_out").innerHTML = "";
        document.getElementById("unique_ports").innerHTML = "0";
        document.getElementById("full_unique_ports").innerHTML = "";
        return;
    }
    document.getElementById("selectionName").innerHTML = "\"" + node.alias + "\"";
    document.getElementById("selectionNumber").innerHTML = node.alias;
    $.ajax({
        url: "/details",
        //dataType: "json",
        type: "POST",
        data: node.alias,
        error: onNotLoadData,
        success: function(result) {
            document.getElementById("unique_in").innerHTML = result.unique_in;
            document.getElementById("unique_out").innerHTML = result.unique_out;
            document.getElementById("unique_ports").innerHTML = result.unique_ports;

            var conn_in = "";
            var conn_out = "";
            var ports_in = "";
            for (var i in result.conn_in) {
                conn_in += "<tr><td>" + result.conn_in[i].ip + "</td><td>" + result.conn_in[i].links + "</td></tr>";
            }
            for (var i in result.conn_out) {
                conn_out += "<tr><td>" + result.conn_out[i].ip + "</td><td>" + result.conn_out[i].links + "</td></tr>";
            }
            for (var i in result.ports_in) {
                ports_in += "<tr><td>" + result.ports_in[i].port + "</td><td>" + result.ports_in[i].links + "</td></tr>";
            }

            if (result.conn_in.length < result.unique_in) {
                conn_in += "<tr><td>Plus " + (result.unique_in - result.conn_in.length) + " more...</td><td>--</td></tr>";
            }
            if (result.conn_out.length < result.unique_out) {
                conn_out += "<tr><td>Plus " + (result.unique_out - result.conn_out.length) + " more...</td><td>--</td></tr>";
            }
            if (result.ports_in.length < result.unique_ports) {
                ports_in += "<tr><td>Plus " + (result.unique_ports - result.ports_in.length) + " more...</td><td>--</td></tr>";
            }

            document.getElementById("conn_in").innerHTML = conn_in;
            document.getElementById("conn_out").innerHTML = conn_out;
            document.getElementById("ports_in").innerHTML = ports_in;
            updateFloatingPanel();
    }});
}