var canvas;
var ctx;
var width;
var height;
var navBarHeight;
var nodes;

function init() {
    canvas = document.getElementById("canvas");
    navBarHeight = $('#navbar').height();
    $('#output').css('top', navBarHeight);
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    ctx = canvas.getContext("2d");
    render();
}

function render() {
    ctx.fillStyle = "#AAFFDD";
    ctx.fillRect(0, 0, width, height);

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




function onResize() {
    console.log("Resource conscious resize callback!");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    render();
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