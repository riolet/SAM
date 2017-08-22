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
    event.preventDefault();
    deselectText();
    event.target.focus();
    mdownx = event.clientX - controller.rect.left;
    mdowny = event.clientY - controller.rect.top;
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
    return x <= node.abs_x + node.radius
            && x >= node.abs_x - node.radius
            && y <= node.abs_y + node.radius
            && y >= node.abs_y - node.radius;
}

//For onMouseUp, returns node if a node was clicked on, else null.
function pick(x, y, scale) {
    "use strict";
    var best = null;
    var bestDist = +Infinity;
    var tempDist = 0;
    renderCollection.forEach(function (node) {
        tempDist = distanceSquared(x, y, node.abs_x, node.abs_y);
        if (tempDist < node.radius*node.radius) {
            if (tempDist < bestDist || node.subnet > best.subnet) {
                bestDist = tempDist;
                best = node;
            }
        }
    });
    if (best !== null && best.subnet < currentSubnet(scale) - 8) {
        best = null;
    }
    return best;
}

function mouseup(event) {
  "use strict";
  if (ismdown === false) {
    return;
  }
  event.preventDefault();

  ismdown = false;
  mx = event.clientX - controller.rect.left;
  my = event.clientY - controller.rect.top;

  if (mx === mdownx && my === mdowny) {
    //mouse hasn't moved. treat this as a "pick" operation
    var selection = pick((mx - tx) / g_scale, (my - ty) / g_scale, g_scale);
    //updateSelection(selection);
    sel_set_selection(selection);
  }

  tx = tx + mx - mdownx;
  ty = ty + my - mdowny;
  updateRenderRoot();
  render_all();
  if (config.flat === false) {
    checkLoD();
  }
}

function mousemove(event) {
    "use strict";
    if (ismdown === false) {
      return;
    }
    event.preventDefault();
    mx = event.clientX - controller.rect.left;
    my = event.clientY - controller.rect.top;
    requestAnimationFrame(function () {render(controller.ctx, tx + mx - mdownx, ty + my - mdowny, g_scale);});
}

function wheel(event) {
  "use strict";
  //event is a WheelEvent
  mx = event.clientX - controller.rect.left;
  my = event.clientY - controller.rect.top;

  if (event.deltaY < 0) { // Zoom in
    if (g_scale >= 60.0) {
      return;
    }
    tx -= mx;
    ty -= my;
    g_scale *= 1.15;
    tx *= 1.15;
    ty *= 1.15;
    tx += mx;
    ty += my;
  } else if (event.deltaY > 0) { // Zoom out
    if (g_scale <= 0.0005) {
      return;
    }
    tx -= mx;
    ty -= my;
    g_scale *= 0.87;
    tx *= 0.87;
    ty *= 0.87;
    tx += mx;
    ty += my;
  } else {
    return;
  }
  updateRenderRoot();
  render_all();
  if (nodes.layout_flat === false) {
    checkLoD();
  }
}

function keydown(event) {
    "use strict";
    //if key is 'f', reset the view
    if (event.keyCode === 70) {
        resetViewport(nodes.nodes);
        resetViewport(renderCollection);
        render_all();
    }
    return;
}

function applyfilter() {
    "use strict";
    config.filter = document.getElementById("filter").value;
    sel_set_selection(null);
    links_reset();
    updateRenderRoot();
    render_all();
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
  let searchElement = document.getElementById("search");
  let addr = searchElement.value;
  let normalized_addr = normalize_addr(addr);
  let nearest = nodes.find_by_addr(addr);

  //if we got nothing, give up.
  if (nearest == null) {
    //pass
  }
  //if we have a perfect match:
  else if (nearest.address + "/" + nearest.subnet == normalized_addr) {
    resetViewport([nearest], 0.2);
    sel_set_selection(nearest);
    render_all();
  }
  //we have an imperfect match at this point. Are there more children to load?
  else if (nearest.childrenLoaded) {
    //no more child nodes to load.
    resetViewport([nearest], 0.2);
    sel_set_selection(nearest);
    render_all();
  } else {
    //load more child nodes.
    nodes.GET_request([nearest], applysearch);
  }
}
function onsearch() {
  "use strict";
  if (g_timer !== null) {
    clearTimeout(g_timer);
  }
  g_timer = setTimeout(applysearch, 700);
}

function applyProtocolFilter() {
    "use strict";
    console.log("fired");
    config.protocol = document.getElementById("proto_filter").value;
    sel_set_selection(null);
    links_reset();
    updateRenderRoot();
    render_all();
}
function onProtocolFilter() {
    "use strict";
    console.log("on");
    if (g_timer !== null) {
        clearTimeout(g_timer);
    }
    g_timer = setTimeout(applyProtocolFilter, 700);
}

function onResize() {
    "use strict";
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - $("#navbar").height();
    controller.rect = canvas.getBoundingClientRect();
    controller.ctx.lineJoin = "bevel"; //seems to get reset on resize?
    render_all();
    checkLoD();
    sel_panel_height();
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
