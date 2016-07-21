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
    var ports = {}
    //for (var j in links) {
    //    ports.add(links[j].port);
    //}

    var portsToDisplay = Math.min(ports.size, 8);
    var destination = findNode(links[0].dest8, links[0].dest16,
                               links[0].dest24, links[0].dest32);

    /*
    ports.add(88888);
    ports.add(77777);
    ports.add(66666);
    ports.add(55555);
    ports.add(44444);
    ports.add(33333);
    ports.add(22222);
    ports.add(11111);
    for (let port of ports) {
        destination.ports[port] = {'x':destination.x, 'y':destination.x};
    }
    */
    ports['88888'] = false;
    ports['77777'] = false;
    ports['66666'] = false;
    ports['55555'] = false;
    ports['44444'] = false;
    ports['33333'] = false;
    ports['22222'] = false;
    ports['11111'] = false;

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

    for (var port in ports) {
        destination.ports[port] = locations[port / 11111 - 1];
    }

    for (let link of links) {
        var source = findNode(link.source8, link.source16,
                              link.source24, link.source32);

        //offset endpoints by radius
        var dx = link.x2 - link.x1;
        var dy = link.y2 - link.y1;

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
        document.getElementById("selectionInfo").innerHTML = "";
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
            document.getElementById("selectionInfo").innerHTML = result;
            $('.ui.accordion').accordion();
    }});
}