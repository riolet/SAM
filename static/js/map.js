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
    $.ajax({url: "/query", dataType: "json", success: onLoadData, error: onNotLoadData});
}

function Node(address, alias, level, connections, x, y, radius) {
    this.address = address;
    this.alias = alias;
    this.level = level;
    this.connections = connections;
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.children = {};
    this.childrenLoaded = false;
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
    childrenLoaded: false
};

// Function(jqXHR jqXHR, String textStatus, String errorThrown)
function onNotLoadData(xhr, textStatus, errorThrown) {
    console.log("Failed to load data.");
    console.log(textStatus);
    console.log(errorThrown);
}

function onLoadData(result) {
    console.log("Data loaded!");
    console.log(result);
    console.log("There are " + result.length + " connections to map");
    // result should be a json object.
    // I am expecting `result` to be an array of objects
    // where each object has IPAddress, alias, connections, x, y, radius,
    nodeCollection = {};
    for (var row in result) {
        name = result[row].IPAddress;
        nodeCollection[result[row].IPAddress] = new Node(result[row].IPAddress, name, 8, result[row].connections, result[row].x, result[row].y, result[row].radius);
    }
    //linkCollection = result;

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
}

function loadChildren(node) {
    node.childrenLoaded = true;
    console.log("Dynamically loading children of " + node.address);
    // TODO: Fix address notation. Only works for /16 nodes.
    $.ajax({url: "/query/" + node.address, dataType: "json", error: onNotLoadData, success: function(result) {
        console.log("Loaded node " + node.address + "'s children:");
        console.log(result);
        console.log("There are " + result.length + " of them.")

        for (var row in result) {
            name = result[row].parent8 + "." + result[row].IPAddress;
            node.children[result[row].IPAddress] = new Node(result[row].IPAddress, name, 16, result[row].connections, result[row].x, result[row].y, result[row].radius);
        }
    }});
}

//==========================================
//  Drawing Functions
//==========================================

function render(x, y, scale) {
    ctx.resetTransform();
    ctx.fillStyle = "#AAFFDD";
    ctx.globalAlpha = 1.0;
    ctx.fillRect(0, 0, width, height);

    ctx.setTransform(scale, 0, 0, scale, x, y, 1);

    ctx.lineWidth = 1;
    ctx.fillStyle = "#0000FF";
    ctx.strokeStyle = "#5555CC";
    ctx.lineWidth = 5 / scale;
    renderClusters(nodeCollection);

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
        ctx.font = (collection[node].radius / 2) + "px sans";
            //TODO: Fade in/out based on scale
            alpha = opacity(collection[node].level);
            ctx.globalAlpha = alpha;
            drawClusterNode(collection[node].alias, collection[node].x, collection[node].y, collection[node].radius, alpha);
        if (collection[node].childrenLoaded) {
            renderClusters(collection[node].children);
        }
    }
}

function drawClusterNode(name, x, y, radius, opacity) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2, 0);
    ctx.stroke();
    var size = ctx.measureText(name);
    ctx.fillText(name, x - size.width / 2, y - radius * 1.25);
}

function drawArrow(x1, y1, x2, y2, radius = 0, thickness = 1) {
    var dx = x2-x1;
    var dy = y2-y1;
    if (Math.abs(dx) + Math.abs(dy) < 10) {
        return;
    }
    //offset endpoints by radius
    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //leftward flowing
            x1 = x1 - radius;
            x2 = x2 + radius;
            y1 += 5;
            y2 += 5;
        } else {
            //rightward flowing
            x1 = x1 + radius;
            x2 = x2 - radius;
            y1 -= 5;
            y2 -= 5;
        }
        dx = x2 - x1;
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //upward flowing
            y1 = y1 - radius;
            y2 = y2 + radius;
            x1 += 5;
            x2 += 5;
        } else {
            //downward flowing
            y1 = y1 + radius;
            y2 = y2 - radius;
            x1 -= 5;
            x2 -= 5;
        }
        dy = y2 - y1;
    }

    ctx.beginPath();
    ctx.lineWidth = Math.log(thickness) / 4 + 1;
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);

    var len = Math.hypot(dx, dy);
    var xTemp = (-dx) / len * 10;
    var yTemp = (-dy) / len * 10;

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
        tx -= mx;
        ty -= my;
        scale *= 1.15;
        tx *= 1.15;
        ty *= 1.15;
        tx += mx;
        ty += my;
    } else if (event.deltaY > 0) { // Zoom out
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
    checkLoD()
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
        //TODO: test this
        if (scale <= 0.5) {
            return 0.0;
        } else if (scale >= 7.0) {
            return 0.0;
        } else if (scale >= 1.0 && scale <= 3.5) {
            return 1.0;
        } else if (scale < 1.0) {
            return 1 - (scale - 1.0) / (-0.5);
        } else if (scale > 3.5) {
            return (scale - 1.0) / (-3.5);
        }
    } else if (level == 32) {
        //TODO: test this
        if (scale <= 3.5) {
            return 0.0;
        } else if (scale >= 7.0) {
            return 1.0;
        } else if (scale < 7.0) {
            return 1 - (scale - 7.0) / (3.5);
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

    for (var node in nodeCollection) {
        if (nodeCollection[node].x > left && nodeCollection[node].x < right && nodeCollection[node].y > top && nodeCollection[node].y < bottom) {
            visible.push(nodeCollection[node]);
        }
    }
    return visible;
}
