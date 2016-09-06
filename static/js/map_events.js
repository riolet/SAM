function deselectText() {
    "use strict";
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

function mousedown(event) {
    "use strict";
    deselectText();
    mdownx = event.clientX - rect.left;
    mdowny = event.clientY - rect.top;
    ismdown = true;
}

//Helper for pick. Distance**2 between two points
function distanceSquared(x1, y1, x2, y2) {
    "use strict";
    return (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
}

//Helper for pick. Determines if a coordinate is within a node's bounding box
function contains(node, x, y) {
    "use strict";
    return x < node.x + node.radius
            && x > node.x - node.radius
            && y < node.y + node.radius
            && y > node.y - node.radius;
}

//For onMouseUp, returns node if a node was clicked on, else null.
function pick(x, y) {
    "use strict";
    var best = null;
    var bestDist = +Infinity;
    var tempDist = 0;
    renderCollection.forEach(function (node) {
        tempDist = distanceSquared(x, y, node.x, node.y);
        if (tempDist < node.radius*node.radius) {
        //if (contains(node, x, y)) {
            if (tempDist < bestDist || node.subnet > best.subnet) {
                bestDist = tempDist;
                best = node;
            }
        }
    });
    if (best !== null && best.subnet < currentSubnet() - 8) {
        best = null;
    }
    return best;
}

function mouseup(event) {
    "use strict";
    if (ismdown === false) {
        return;
    }

    ismdown = false;
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;

    if (mx === mdownx && my === mdowny) {
        //mouse hasn't moved. treat this as a "pick" operation
        var selection = pick((mx - tx) / scale, (my - ty) / scale);
        //updateSelection(selection);
        sel_set_selection(selection);
    }

    tx = tx + mx - mdownx;
    ty = ty + my - mdowny;
    render(tx, ty, scale);
    checkLoD();
}

function mousemove(event) {
    "use strict";
    if (ismdown === false) {
        return;
    }
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;
    render(tx + mx - mdownx, ty + my - mdowny, scale);
}

function wheel(event) {
    "use strict";
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
    "use strict";
    //don't interfere with input dialogs
    if (document.activeElement.localName !== "body") {
        return;
    }
    //if key is 'f', reset the view
    if (event.keyCode === 70) {
        resetViewport(m_nodes);
        updateRenderRoot();
        resetViewport(renderCollection);
        render(tx, ty, scale);
    }
    return;
}

function applyfilter() {
    "use strict";
    config.filter = document.getElementById("filter").value;
    sel_set_selection(null);
    links_reset();
    updateRenderRoot();
    render(tx, ty, scale);
}
function onfilter() {
    "use strict";
    if (g_timer !== null) {
        clearTimeout(g_timer);
    }
    g_timer = setTimeout(applyfilter, 700);
}

function applysearch() {
    "use strict";
    var target = document.getElementById("search").value;
    var ips = target.split(".");
    var segment;
    var subnet = null;
    var i = 0;

    for (i = 0; i < ips.length; i += 1) {
        if (ips[i] === "") {
            continue;
        }
        segment = Number(ips[i]);
        if (Number.isNaN(segment) || segment < 0 || segment > 255) {
            break;
        }
        if (subnet === null) {
            if (m_nodes.hasOwnProperty(segment)) {
                subnet = m_nodes[segment];
            } else {
                break;
            }
        } else {
            if (subnet.childrenLoaded === false && subnet.subnet < 32) {
                //load more and restart when loading is complete.
                GET_nodes([subnet], applysearch);
                return;
            }
            if (subnet.children.hasOwnProperty(segment)) {
                subnet = subnet.children[segment];
            } else {
                break;
            }
        }
    }

    if (subnet === null) {
        return;
    }

    resetViewport([subnet], 0.2);
    sel_set_selection(subnet);
    updateRenderRoot();
    render(tx, ty, scale);
}
function onsearch() {
    "use strict";
    if (g_timer !== null) {
        clearTimeout(g_timer);
    }
    g_timer = setTimeout(applysearch, 700);
}

function updateFloatingPanel() {
    "use strict";
    var side = document.getElementById("sel_bar");
    var heightAvailable = rect.height - 40;
    side.style.maxHeight = heightAvailable + "px";

    heightAvailable -= 10; //for padding
    heightAvailable -= 10; //for borders

    var contentTitles = $("#selectionInfo div.title");
    var i;
    for (i = 0; i < contentTitles.length; i += 1) {
        //offsetHeight is height + vertical padding + vertical borders
        heightAvailable -= contentTitles[i].offsetHeight;
    }
    heightAvailable -= document.getElementById("sel_titles").offsetHeight;

    var contentBlocks = $("#selectionInfo div.content");
    for (i = 0; i < contentBlocks.length; i += 1) {
        contentBlocks[i].style.maxHeight = heightAvailable + "px";
    }
}

function onResize() {
    "use strict";
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - $("#navbar").height();
    rect = canvas.getBoundingClientRect();
    ctx.lineJoin = "bevel"; //seems to get reset on resize?
    render(tx, ty, scale);
    checkLoD();
    updateFloatingPanel();
}

function updateConfig() {
    "use strict";
    config.show_clients = document.getElementById("show_clients").checked;
    config.show_servers = document.getElementById("show_servers").checked;
    config.show_in = document.getElementById("show_in").checked;
    config.show_out = document.getElementById("show_out").checked;
    updateRenderRoot();
    render(tx, ty, scale);
}

(function () {
    "use strict";
    var throttle = function (type, name, obj) {
        obj = obj || window;
        var running = false;
        var func = function () {
            if (running) {
                return;
            }
            running = true;
             requestAnimationFrame(function () {
                obj.dispatchEvent(new CustomEvent(name));
                running = false;
            });
        };
        obj.addEventListener(type, func);
    };

    /* init - you can init any event */
    throttle("resize", "optimizedResize");
}());

// handle event
window.addEventListener("optimizedResize", onResize);