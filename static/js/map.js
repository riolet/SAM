var canvas;
var ctx;
var width;
var height;
var rect;
var navBarHeight;

var ismdown = false;
var mdownx, mdowny;
var mx, my;
var tx = 532;
var ty = 288;
var scale = 0.01;

var map = {};

var nodeCollection;
var renderCollection;
var linkCollection;


function init() {
    canvas = document.getElementById("canvas");
    navBarHeight = $('#navbar').height();
    $('#output').css('top', navBarHeight);
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    rect = canvas.getBoundingClientRect();
    ctx = canvas.getContext("2d");
    ctx.lineJoin = "bevel";


    //Event listeners for detecting clicks and zooms
    canvas.addEventListener('mousedown', mousedown);
    canvas.addEventListener('mousemove', mousemove);
    canvas.addEventListener('mouseup', mouseup);
    canvas.addEventListener('wheel', wheel);

    loadData();

    render(tx, ty, scale);
}

//==========================================
//  Data Processing Functions
//==========================================

function loadData() {
    $.ajax({
        url: "/query",
        success: onLoadData,
        error: onNotLoadData
        });
}

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
    inputs: []
};

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
        for (var i in node.children) {
            for (var j in node.children[i].inputs) {
                preprocessConnection(node.children[i].inputs[j])
            }
        }
    }});
}

function preprocessConnection(link) {
    //TODO: move this preprocessing into the database instead of client-side.
    var source = {};
    var dest = {};
    if ("source32" in link) {
        source = findNode(link.source8, link.source16, link.source24, link.source32)
        dest = findNode(link.dest8, link.dest16, link.dest24, link.dest32)
    } else if ("source24" in link) {
        source = findNode(link.source8, link.source16, link.source24)
        dest = findNode(link.dest8, link.dest16, link.dest24)
    } else if ("source16" in link) {
        source = findNode(link.source8, link.source16)
        dest = findNode(link.dest8, link.dest16)
    } else {
        source = findNode(link.source8)
        dest = findNode(link.dest8)
    }

    //offset endpoints by radius
    var dx = link.x2 - link.x1;
    var dy = link.y2 - link.y1;

    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //leftward flowing
            link.x1 -= source.radius;
            link.x2 += dest.radius;
            link.y1 += source.radius * 0.2;
            link.y2 += dest.radius * 0.2;
        } else {
            //rightward flowing
            link.x1 += source.radius;
            link.x2 -= dest.radius;
            link.y1 -= source.radius * 0.2;
            link.y2 -= dest.radius * 0.2;
        }
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //upward flowing
            link.y1 -= source.radius;
            link.y2 += dest.radius;
            link.x1 += source.radius * 0.2;
            link.x2 += dest.radius * 0.2;
        } else {
            //downward flowing
            link.y1 += source.radius;
            link.y2 -= dest.radius;
            link.x1 -= source.radius * 0.2;
            link.x2 -= dest.radius * 0.2;
        }
    }

}

//==========================================
//  Drawing Functions
//==========================================

function updateRenderRoot() {
    renderCollection = onScreen();
}

function render(x, y, scale) {
    ctx.resetTransform();
    ctx.fillStyle = "#AAFFDD";
    ctx.globalAlpha = 1.0;
    ctx.fillRect(0, 0, width, height);

    ctx.setTransform(scale, 0, 0, scale, x, y, 1);

    ctx.lineWidth = 1;
    ctx.fillStyle = "#0000FF";
    ctx.strokeStyle = "#5555CC";

    //TODO: replace nodeCollection with onScreen() to only render visible nodes
    renderClusters(renderCollection);

    ctx.strokeStyle = "#000000";
    for (var link in linkCollection) {
        var start = nodeCollection[linkCollection[link].Source];
        var end = nodeCollection[linkCollection[link].Destination];
        drawArrow(start.x, start.y, end.x, end.y, 25, linkCollection[link].Occurrences);
    }
}

function renderClusters(collection) {
    var level = currentLevel();
    var alpha = 1.0;

    for (var node in collection) {
        if (collection[node].level > level) {
            return;
        }
        //Font size below 2 pixels: the letter spacing is broken.
        //Font size above 2000 pixels: letters stop getting bigger.
        ctx.font = Math.max(collection[node].radius / 2, 2) + "px sans";
        alpha = opacity(collection[node].level);
        ctx.globalAlpha = alpha;
        ctx.lineWidth = 5 / scale;
        drawClusterNode(collection[node].alias, collection[node].x, collection[node].y, collection[node].radius, alpha);
        renderLinks(collection[node])
        //if (collection[node].childrenLoaded) {
        //    renderClusters(collection[node].children);
        //}
    }
}

function drawClusterNode(name, x, y, radius, opacity) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2, 0);
    ctx.stroke();
    var size = ctx.measureText(name);
    ctx.fillText(name, x - size.width / 2, y - radius * 1.25);
}

function renderLinks(node) {
    var link = node.inputs
    for (var i in link) {
        drawArrow(link[i].x1, link[i].y1, link[i].x2, link[i].y2, findNode(link[i].source8).radius, node.radius, link[i].links);
    }
}

function drawArrow(x1, y1, x2, y2, rStart = 0, rEnd = 0, thickness = 1) {
    var dx = x2-x1;
    var dy = y2-y1;
    if (Math.abs(dx) + Math.abs(dy) < 10) {
        return;
    }

    ctx.beginPath();
    ctx.lineWidth = (Math.log(thickness) / 4 + 1) / scale;
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);

    var len = Math.hypot(dx, dy);
    var xTemp = (-dx) / len * (30 / scale);
    var yTemp = (-dy) / len * (30 / scale);

    var c = Math.cos(0.3);
    var s = Math.sin(0.3);
    var x3 = xTemp * c - yTemp * s + x2;
    var y3 = xTemp * s + yTemp * c + y2;
    var x4 = xTemp * c - yTemp * -s + x2;
    var y4 = xTemp * -s + yTemp * c + y2;

    ctx.lineTo(x3, y3);
    ctx.lineTo(x4, y4);
    ctx.lineTo(x2, y2);
    ctx.stroke();
}

//==========================================
//  Mouse Interaction Handlers
//==========================================

function mousedown(event) {
    mdownx = event.clientX - rect.left;
    mdowny = event.clientY - rect.top;
    ismdown = true;
}

function mouseup(event) {
    if (ismdown == false) {
        return
    }

    ismdown = false;
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;
    tx = tx + mx - mdownx;
    ty = ty + my - mdowny;
    render(tx, ty, scale);
    checkLoD();
}

function mousemove(event) {
    if (ismdown == false) {
        return
    }
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;
    render(tx + mx - mdownx, ty + my - mdowny, scale);
}

function wheel(event) {
    //event is a WheelEvent
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;

    if (event.deltaY < 0) { // Zoom in
        if (scale >= 49.0) {
            return;
        }
        tx -= mx;
        ty -= my;
        scale *= 1.15;
        tx *= 1.15;
        ty *= 1.15;
        tx += mx;
        ty += my;
    } else if (event.deltaY > 0) { // Zoom out
        if (scale <= 0.01) {
            return;
        }
        tx -= mx;
        ty -= my;
        scale *= 0.87;
        tx *= 0.87;
        ty *= 0.87;
        tx += mx;
        ty += my;
    } else {
        return;
    }
    render(tx, ty, scale);
    checkLoD();
}

//==========================================
//  Other Event Handlers
//==========================================

function onResize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    rect = canvas.getBoundingClientRect();
    ctx.lineJoin = "bevel"; //seems to get reset on resize?
    render(tx, ty, scale);
    checkLoD();
}

(function() {
    var throttle = function(type, name, obj) {
        obj = obj || window;
        var running = false;
        var func = function() {
            if (running) { return; }
            running = true;
             requestAnimationFrame(function() {
                obj.dispatchEvent(new CustomEvent(name));
                running = false;
            });
        };
        obj.addEventListener(type, func);
    };

    /* init - you can init any event */
    throttle("resize", "optimizedResize");
})();

// handle event
window.addEventListener("optimizedResize", onResize);

//==========================================
//  Other Utilities
//==========================================

function currentLevel() {
    if (scale < 0.07) {
        return 8;
    }
    if (scale < 0.5) {
        return 16;
    }
    if (scale < 3.5) {
        return 24;
    }
    return 32;
}

function opacity(level) {
    if (level == 8) {
        if (scale <= 0.07) {
            return 1.0;
        } else if (scale >= 0.14) {
            return 0.0;
        } else {
            return (scale - 0.14) / (-0.07);
        }
    } else if (level == 16) {
        if (scale <= 0.07) {
            return 0.0;
        } else if (scale >= 1.0) {
            return 0.0;
        } else if (scale >= 0.14 && scale <= 0.5) {
            return 1.0;
        } else if (scale < 0.14) {
            return 1 - (scale - 0.14) / (-0.07);
        } else if (scale > 0.5) {
            return (scale - 1.0) / (-0.5);
        }
    } else if (level == 24) {
        if (scale <= 0.5) {
            return 0.0;
        } else if (scale >= 7.0) {
            return 0.0;
        } else if (scale >= 1.0 && scale <= 3.5) {
            return 1.0;
        } else if (scale < 1.0) {
            return 1 - (scale - 1.0) / (-0.5);
        } else if (scale > 3.5) {
            return (scale - 7.0) / (-3.5);
        }
    } else if (level == 32) {
        if (scale <= 3.5) {
            return 0.0;
        } else if (scale >= 7.0) {
            return 1.0;
        } else if (scale < 7.0) {
            return 1 - (scale - 7.0) / (-3.5);
        }
    }
}

function canSee(level) {
    if (level <= 8) {
        return true;
    }
    if (scale > 0.07 && level <= 16) {
        return true;
    }
    if (scale > 0.5 && level <= 24) {
        return true;
    }
    if (scale > 3.5 && level <= 32) {
        return true;
    }
    return false;
}

function onScreen() {
    var left = -tx/scale;
    var right = (rect.width-tx)/scale;
    var top = -ty/scale;
    var bottom = (rect.height-ty)/scale;
    var visible = [];
    var x;
    var y;
    var r;

    var level = currentLevel();

    visible = onScreenRecursive(left, right, top, bottom, nodeCollection);

    if (visible.length == 0) {
        console.log("Cannot see any nodes");
    }
    return visible;
}

function onScreenRecursive(left, right, top, bottom, collection) {
    var selected = [];
    for (var node in collection) {
        x = collection[node].x;
        y = collection[node].y;
        r = collection[node].radius * 2;

        if ((x + r) > left && (x - r) < right && (y + r) > top && (y - r) < bottom) {
            selected.push(collection[node]);
            if (collection[node].childrenLoaded && collection[node].level < currentLevel()) {
                selected = selected.concat(onScreenRecursive(left, right, top, bottom, collection[node].children))
            }
        }
    }
    return selected;
}

function findNode(seg1=-1, seg2=-1, seg3=-1, seg4=-1) {
    if (seg1 in nodeCollection) {
        if (seg2 in nodeCollection[seg1].children) {
            if (seg3 in nodeCollection[seg1].children[seg2].children) {
                if (seg4 in nodeCollection[seg1].children[seg2].children[seg3].children) {
                    return nodeCollection[seg1].children[seg2].children[seg3].children[seg4];
                } else {
                    return nodeCollection[seg1].children[seg2].children[seg3];
                }
            } else {
                return nodeCollection[seg1].children[seg2];
            }
        } else {
            return nodeCollection[seg1];
        }
    } else {
        return null;
    }
}

/*
//Note: this function hasn't been tested.
function findClosest(x, y, collection) {
    var closestDist = Infinity;
    var closest = null;
    var dist = 0;
    for (var node in collection) {
        //NOTE: this is an approximation, rather than the true distance.
        dist = Math.abs(collection[node].x - x) + Math.abs(collection[node].y - y)
        if (dist < closestDist) {
            closestDist = dist;
            closest = collection[node];
        }
    }
    return closest;
}
*/