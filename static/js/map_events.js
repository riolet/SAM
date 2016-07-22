function mousedown(event) {
    deselectText();
    mdownx = event.clientX - rect.left;
    mdowny = event.clientY - rect.top;
    ismdown = true;
}

function deselectText() {
    if (window.getSelection) {
      if (window.getSelection().empty) {  // Chrome
        window.getSelection().empty();
      } else if (window.getSelection().removeAllRanges) {  // Firefox
        window.getSelection().removeAllRanges();
      }
    } else if (document.selection) {  // IE?
      document.selection.empty();
    }
}

function mouseup(event) {
    if (ismdown == false) {
        return
    }

    ismdown = false;
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;

    if (mx == mdownx && my == mdowny) {
        //mouse hasn't moved. treat this as a "pick" operation
        selection = pick((mx - tx) / scale, (my - ty) / scale);
        updateSelection(selection);
    }

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
        if (scale >= 60.0) {
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
        if (scale <= 0.0005) {
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

function keydown(event) {
    //if key is 'f', reset the view
    if (event.keyCode == 70) {
        scale = 0.0007;
        tx = rect.width / 2;
        ty = rect.height / 2;
        updateRenderRoot();
        render(tx, ty, scale);
    }
    return;
}

//For onMouseUp, returns node if a node was clicked on, else null.
function pick(x, y) {
    var best = null;
    var bestDist = +Infinity;
    var tempDist = 0;
    for (var i in renderCollection) {
        if (contains(renderCollection[i], x, y)) {
            tempDist = distanceSquared(x, y, renderCollection[i].x, renderCollection[i].y)
            if (tempDist < bestDist || renderCollection[i].level > best.level) {
                bestDist = tempDist;
                best = renderCollection[i];
            }
        }
    }
    return best;
}

//Helper for pick. Distance**2 between two points
function distanceSquared(x1, y1, x2, y2) {
    return (x2-x1) * (x2-x1) + (y2-y1) * (y2-y1);
}

//Helper for pick. Determines if a coordinate is within a node's bounding box
function contains(node, x, y) {
    return x < node.x + node.radius
        && x > node.x - node.radius
        && y < node.y + node.radius
        && y > node.y - node.radius;
}


var g_timer = null;
function onfilter(event) {
    if (g_timer != null) {
        clearTimeout(g_timer);
    }
    g_timer = setTimeout(applyfilter, 700);
}

function applyfilter(event=null) {
    filterElement = document.getElementById("filter");
    filter = filterElement.value;

    updateSelection(null);
    nodeCollection = null;
    currentSubnet = "";
    scale = 0.0007;
    tx = rect.width / 2;
    ty = rect.height / 2;
    updateRenderRoot();
    loadData();
}

function onResize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    rect = canvas.getBoundingClientRect();
    ctx.lineJoin = "bevel"; //seems to get reset on resize?
    render(tx, ty, scale);
    checkLoD();
    updateFloatingPanel();
}

function updateConfig(text, value){
    config.show_clients = document.getElementById("show_clients").checked;
    config.show_servers = document.getElementById("show_servers").checked;
    config.show_in = document.getElementById("show_in").checked;
    config.show_out = document.getElementById("show_out").checked;
    updateRenderRoot();
    render(tx, ty, scale);
}

function updateFloatingPanel() {
    var side = document.getElementById("sidebar");
    var heightAvailable = rect.height - 40;
    side.style.maxHeight = heightAvailable + "px";

    heightAvailable -= 10; //for padding
    heightAvailable -= 10; //for borders

    contentTitles = $("#selectionInfo div.title");
    for (var i = 0; i < contentTitles.length; i++) {
        //offsetHeight is height + vertical padding + vertical borders
        heightAvailable -= contentTitles[i].offsetHeight;
    }
    heightAvailable -= document.getElementById('selectionName').offsetHeight;
    heightAvailable -= document.getElementById('selectionNumber').offsetHeight;

    contentBlocks = $("#selectionInfo div.content");
    for (var i = 0; i < contentBlocks.length; i++) {
        contentBlocks[i].style.maxHeight = heightAvailable + "px";
    }
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