var canvas;
var ctx;
var width;
var height;
var navBarHeight;
var nodes;
var ismdown;
var mdownx, mdowny;
var mx, my;
var oldTransform;
var tx, ty;
var scale;


function init() {
    canvas = document.getElementById("canvas");
    navBarHeight = $('#navbar').height();
    $('#output').css('top', navBarHeight);
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    ctx = canvas.getContext("2d");

    //Event listeners for detecting clicks
    canvas.addEventListener('mousedown', mousedown);
    canvas.addEventListener('mousemove', mousemove);
    canvas.addEventListener('mouseup', mouseup);

    //default viewport coordinates
    tx = 400;
    ty = 120;
    scale = 1;

    render(tx, ty, scale);
}

//==========================================
//  Mouse Interaction Handlers
//==========================================

function mousedown(event) {
    var rect = canvas.getBoundingClientRect();
    mdownx = event.clientX - rect.left;
    mdowny = event.clientY - rect.top;
    ismdown = true;
}

function mouseup(event) {
    if (ismdown == false) {
        return
    }

    ismdown = false;
    var rect = canvas.getBoundingClientRect();
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
    var rect = canvas.getBoundingClientRect();
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;
    render(tx + mx - mdownx, ty + my - mdowny, scale);
}

//==========================================
//  Drawing Functions
//==========================================

function render(x, y, scale) {
    ctx.resetTransform();
    ctx.fillStyle = "#AAFFDD";
    ctx.fillRect(0, 0, width, height);

    ctx.setTransform(scale, 0, 0, scale, x, y, 1);

    drawNode("Node A", 0, 0, 100, 50);
    drawNode("Node B", 200, 0, 100, 50);
    drawNode("Node C", 200, 200, 100, 50);
    drawNode("Server", 0, 200, 100, 50);
}

function drawNode(name, x, y, width, height) {
    ctx.strokeStyle = "#000000";
    ctx.strokeRect(x, y, width, height);
    ctx.font = "20px sans";
    ctx.fillStyle = "#0000FF";
    var size = ctx.measureText(name);
    ctx.fillText(name, x + (width - size.width) / 2, y + 20);
}

//==========================================
//  Other Event Handlers
//==========================================

function onResize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
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