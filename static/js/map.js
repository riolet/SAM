var canvas;
var ctx;
var width;
var height;
var rect;
var navBarHeight;

var ismdown = false;
var mdownx, mdowny;
var mx, my;
var tx = 366;
var ty = 187;
var scale = 0.75;

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

function Node(number, x, y) {
    this.number = number;
    this.inputs = [];
    this.x = x;
    this.y = y;
}

Node.prototype = {
    name: "",
    number: 0,
    visits: 0,
    inputs: [],
    x: 0,
    y: 0
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
    // I am expecting it to be an array of objects
    // where each object has Source, Destination, Occurrences
    nodeCollection = {};
    for (var row in result) {
        if (!(result[row].Source in nodeCollection)) {
            nodeCollection[result[row].Source] = new Node(result[row].Source, 0, 0);
        }
        if (!(result[row].Destination in nodeCollection)) {
            nodeCollection[result[row].Destination] = new Node(result[row].Destination, 0, 0);
        }
        //save the link:  record the inputs (sources) for the destination
        nodeCollection[result[row].Destination].inputs.push(result[row].Source);
    }
    linkCollection = result;

    arrangeCircle();

    render(tx, ty, scale);
}

function arrangeCircle() {
    var numKeys = Object.keys(nodeCollection).length
    var i = 0
    for (var node in nodeCollection) {
        var ix = i / numKeys * Math.PI * 2;
        nodeCollection[node].x = Math.sin(ix) * 200;
        nodeCollection[node].y = Math.cos(ix) * 200;
        i++
    }
}

//==========================================
//  Drawing Functions
//==========================================

function render(x, y, scale) {
    ctx.resetTransform();
    ctx.fillStyle = "#AAFFDD";
    ctx.fillRect(0, 0, width, height);

    ctx.setTransform(scale, 0, 0, scale, x, y, 1);

    ctx.lineWidth = 1;
    ctx.font = "20px sans";
    ctx.fillStyle = "#0000FF";
    ctx.strokeStyle = "#5555CC";
    ctx.lineWidth = 5;
    for (var node in nodeCollection) {
        drawClusterNode(nodeCollection[node].number, nodeCollection[node].x, nodeCollection[node].y, 50, 50);
    }

    ctx.strokeStyle = "#000000";
    for (var link in linkCollection) {
        var start = nodeCollection[linkCollection[link].Source];
        var end = nodeCollection[linkCollection[link].Destination];
        drawArrow(start.x, start.y, end.x, end.y, 25, linkCollection[link].Occurrences);
    }
}

function zoomLevel() {
    if (scale > ) return 4;
    if (scale > )
}

function drawClusterNode(name, x, y, width, height) {
    ctx.beginPath();
    ctx.arc(x, y, height / 2, 0, Math.PI * 2, 0);
    ctx.stroke();
    var size = ctx.measureText(name);
    ctx.fillText(name, x - size.width / 2, y + 8);
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
    }
    render(tx, ty, scale);
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
