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
function pick(x, y, scale) {
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

  ismdown = false;
  mx = event.clientX - rect.left;
  my = event.clientY - rect.top;

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
    mx = event.clientX - rect.left;
    my = event.clientY - rect.top;
    render(tx + mx - mdownx, ty + my - mdowny, g_scale);
}

function wheel(event) {
  "use strict";
  //event is a WheelEvent
  mx = event.clientX - rect.left;
  my = event.clientY - rect.top;

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
  if (config.flat === false) {
    checkLoD();
  }
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
    var searchElement = document.getElementById("search");
    var ips = searchElement.value.split(".");
    var segment;
    var subnet = null;
    var i = 0;

    //validate ip address numbers
   /* if (ips.length > 4 || ips.every(function (val) {
        var n = Number(val);
        return Number.isNaN(n) || n < 0 || n > 255;
        })) {
        searchElement.classList.add("error");
    } else {
        searchElement.classList.remove("error");
    }*/

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
    render_all();
}
function flatsearch() {
    "use strict";
    let searchElement = document.getElementById("search");
    let target = searchElement.value;
    let ips = target.split(".");

    if (ips.length !== 4) {
        return;
    }

    console.log('ips ', ips);
    let address = parseInt(ips[0]) * 16777216 + parseInt(ips[1]) * 65536 + parseInt(ips[2]) * 256 + parseInt(ips[3]);
    console.log('seeking address ', address);
    let node = m_nodes[address];
    if (!node) {
        console.log("Address not found: ", target);
        return;
    }

    resetViewport([node], 0.2);
    sel_set_selection(node);
    updateRenderRoot();
    render_all();
}
function onsearch() {
    "use strict";
    if (g_timer !== null) {
        clearTimeout(g_timer);
    }
    if (config.flat) {
        g_timer = setTimeout(flatsearch, 700);
    } else {
        g_timer = setTimeout(applysearch, 700);
    }
}

function onResize() {
    "use strict";
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - $("#navbar").height();
    rect = canvas.getBoundingClientRect();
    ctx.lineJoin = "bevel"; //seems to get reset on resize?
    render_all();
    checkLoD();
    sel_panel_height();
}

function updateDsSelection() {
  "use strict";
  //determine which datasource (ds) buttons are clicked.
  var btns = document.getElementsByClassName("ds button active");
  var oldDS = config.ds;
  var newDS = config.ds;
  var count = btns.length - 1;
  if (count === -1) {
    document.getElementById(newDS).classList.add("active");
    return;
  }
  for(; count >= 0; count -= 1) {
    if (btns[count].id !== oldDS) {
      newDS = btns[count].id;
    }
  }
  if (newDS !== oldDS) {
    config.ds = newDS;
    links_reset();
    GET_settings(newDS, function (settings) {
      let newDS_num = /^[^\d]+(\d+).*$/.exec(newDS)[1];
      let datasource = settings.datasources[newDS_num]
      config.update = (datasource.ar_active === 1);
      config.update_interval = datasource.ar_interval;
      config.flat = (datasource.flat === 1);
      init_toggleButton("update", "Auto refresh", "No refresh", config.update);
      setAutoUpdate();
      updateCall();
    });
    for(count = btns.length - 1; count >= 0; count -= 1) {
      if (btns[count].id !== newDS) {
        btns[count].classList.remove("active");
      }
    }
  }
}

function updateLwSelection() {
  "use strict";
  //lw is line width
  let lwbuttons = document.getElementsByClassName("lw button active");
  let num_buttons = lwbuttons.length;
  var oldLW = config.linewidth;
  var newLW = config.linewidth;
  if (num_buttons === 0) {
    document.getElementById(newLW).classList.add("active");
    return;
  }
  for(let i = num_buttons - 1; i >= 0; i -= 1) {
    if (lwbuttons[i].id !== oldLW) {
      newLW = lwbuttons[i].id;
    }
  }
  if (newLW !== oldLW) {
    // do special stuff
    config.linewidth = newLW;
    render_all();
    for(let i = num_buttons - 1; i >= 0; i -= 1) {
      if (lwbuttons[i].id !== newLW) {
        lwbuttons[i].classList.remove("active");
      }
    }
  }
}

function updateFlat(new_flatness) {
    if (config.flat === new_flatness) {
        return;
    }
    config.flat = new_flatness;
    m_nodes = {};
    GET_nodes(null);
}

function updateConfig() {
    "use strict";
    config.show_clients = document.getElementById("show_clients").classList.contains("active");
    config.show_servers = document.getElementById("show_servers").classList.contains("active");
    config.show_in = document.getElementById("show_in").classList.contains("active");
    config.show_out = document.getElementById("show_out").classList.contains("active");
    config.update = document.getElementById("update").classList.contains("active");
    updateFlat(document.getElementById("flat").classList.contains("active"));
    updateDsSelection();
    //Datasource choice
    updateLwSelection();
    //linewidth choice

    setAutoUpdate(); //required to kill the timer if we want to turn it off.
    updateRenderRoot();
    render_all();
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
