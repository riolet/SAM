//rendering configuration settings
var renderConfig = {
  backgroundColor: "#AAFFDD",
  nodeColor: "#5555CC",
  nodeColorFaded: "#95D5D9",
  linkColorTcp: "#5555CC",
  linkColorTcpFaded: "#95D5D9",
  linkColorUdp: "#55CC55",
  linkColorUdpFaded: "#95D995",
  labelColor: "#000000",
  labelBackgroundColor: "#FFFFFF",
  labelColorError: "#996666"
};

function fadeFont(color, alpha) {
  r = parseInt(color.slice(1, 3), 16);
  g = parseInt(color.slice(3, 5), 16);
  b = parseInt(color.slice(5, 7), 16);
  return "rgba(" + r + "," + g + "," + b + "," + alpha + ")";
}

//Given a node's subnet, return the opacity to render it at.
function opacity(subnet, type, scale) {
    "use strict";
    var startZoom = -Infinity;
    var endZoom = Infinity;

    if (subnet === 8) {
        endZoom = zLinks16;
    } else if (subnet === 16) {
        endZoom = zLinks24;
        if (type === "node") {
            startZoom = zNodes16;
        } else {
            startZoom = zLinks16;
        }
    } else if (subnet === 24) {
        endZoom = zLinks32;
        if (type === "node") {
            startZoom = zNodes24;
        } else {
            startZoom = zLinks24;
        }
    } else if (subnet === 32) {
        if (type === "node") {
            startZoom = zNodes32;
        } else {
            startZoom = zLinks32;
        }
    }

    if (scale <= startZoom) {
        // before it's time
        return 0.0;
    } else if (scale >= endZoom * 2) {
        // after it's time
        return 0.0;
    } else if (scale >= startZoom * 2 && scale <= endZoom) {
        // in it's time
        return 1.0;
    } else if (scale < startZoom * 2) {
        // ramping up, linearly
        return 1 - (scale - startZoom * 2) / (-startZoom);
    } else {
        // ramping down, linearly
        return (scale - endZoom * 2) / (-endZoom);
    }
}

function magnitudeSquared(x, y) {
    "use strict";
    return x * x + y * y;
}

function getSubnetLabel() {
    "use strict";
    var subnet = currentSubnet(g_scale);
    if (subnet === 8) {
        return "";
    }
    var closest = null;
    var dist = Infinity;
    var tempDist;
    renderCollection.forEach(function (node) {
        if (node.subnet === subnet - 8) {
            tempDist = magnitudeSquared(
                node.x * g_scale + tx - rect.width / 2,
                node.y * g_scale + ty - rect.height / 2
            );
            if (tempDist < dist) {
                dist = tempDist;
                closest = node;
            }
        }
    });
    if (closest === null) {
        return "";
    }
    return closest.address;
}

function onScreenRecursive(left, right, top, bottom, collection, subnet) {
    "use strict";
    var selected = [];
    var x;
    var y;
    var r;
    Object.keys(collection).forEach(function (node) {
        x = collection[node].x;
        y = collection[node].y;
        r = collection[node].radius * 2;

        if ((x + r) > left && (x - r) < right && (y + r) > top && (y - r) < bottom) {
            selected.push(collection[node]);
            if (collection[node].childrenLoaded && collection[node].subnet < subnet) {
                selected = selected.concat(onScreenRecursive(left, right, top, bottom, collection[node].children, subnet));
            }
        }
    });
    return selected;
}

//build a collection of all nodes currently visible in the window.
function onScreen(x, y, scale) {
    "use strict";
    var left = -x / scale;
    var right = (rect.width - x) / scale;
    var top = -y / scale;
    var bottom = (rect.height - y) / scale;
    var visible = [];

    visible = onScreenRecursive(left, right, top, bottom, m_nodes, currentSubnet(scale));
    if (visible.length === 0) {
        console.log("Cannot see any nodes");
    }

    var filtered = [];
    visible.forEach(function (node) {
        if ((node.client === true && config.show_clients) ||
                (node.server === true && config.show_servers) ||
                (node.client === true && node.server === true)) {
            filtered.push(node);
        }
    });
    filtered.sort(function (a, b) {
        return b.subnet - a.subnet;
    });
    return filtered;
}

function resetViewport(collection, fill) {
    "use strict";
    if (fill === undefined) {
        fill = 0.92;
    }
    var bbox = {"left": Infinity, "right": -Infinity, "top": Infinity, "bottom": -Infinity};
    Object.keys(collection).forEach(function (nodeKey) {
        var node = collection[nodeKey];
        if (node.x - node.radius < bbox.left) {
            bbox.left = node.x - node.radius;
        }
        if (node.x + node.radius > bbox.right) {
            bbox.right = node.x + node.radius;
        }
        if (node.y - node.radius < bbox.top) {
            bbox.top = node.y - node.radius;
        }
        if (node.y + node.radius > bbox.bottom) {
            bbox.bottom = node.y + node.radius;
        }
    });
    var scaleA = fill * rect.width / (bbox.right - bbox.left);
    var scaleB = fill * rect.height / (bbox.bottom - bbox.top);
    g_scale = Math.min(scaleA, scaleB);
    tx = rect.width / 2 - ((bbox.left + bbox.right) / 2) * g_scale;
    ty = rect.height / 2 - ((bbox.top + bbox.bottom) / 2) * g_scale;
}

function updateRenderRoot() {
    "use strict";
    renderCollection = onScreen(tx, ty, g_scale);
    subnetLabel = getSubnetLabel();
}

function drawLoopArrow(node, scale) {
    "use strict";
    var x1 = node.radius * Math.cos(3 * Math.PI / 8);
    var y1 = node.radius * Math.sin(3 * Math.PI / 8);
    var x2 = 3 * x1 + node.x;
    var y2 = 3 * y1 + node.y;
    var x4 = node.radius * Math.cos(1 * Math.PI / 8);
    var y4 = node.radius * Math.sin(1 * Math.PI / 8);
    var x3 = 3 * x4 + node.x;
    var y3 = 3 * y4 + node.y;

    x1 += node.x;
    y1 += node.y;
    x4 += node.x;
    y4 += node.y;

    ctx.moveTo(x1, y1);
    ctx.bezierCurveTo(x2, y2, x3, y3, x4, y4);
    // precalculated as math.cos(math.pi/8-0.2), math.sin(math.pi/8-0.2)
    //               to math.cos(math.pi/8+0.4), math.sin(math.pi/8+0.4)
    ctx.lineTo(x4 + 0.981490 * 24 / scale, y4 + 0.191509 * 24 / scale);
    ctx.lineTo(x4 + 0.701925 * 24 / scale, y4 + 0.712250 * 24 / scale);
    ctx.lineTo(x4, y4);
}

function drawArrow(x1, y1, x2, y2, scale, bIncoming) {
    "use strict";
    if (bIncoming === undefined) {
        bIncoming = true;
    }
    var dx = x2 - x1;
    var dy = y2 - y1;
    if (Math.abs(dx) + Math.abs(dy) < 10) {
        return;
    }

    var len = Math.hypot(dx, dy);
    // This fixes an issue Firefox has with drawing long lines at high zoom levels.
    if (len * scale > 10000) {
        if (bIncoming) {
            x1 = (-dx) / len * (10000 / scale) + x2;
            y1 = (-dy) / len * (10000 / scale) + y2;
        } else {
            x2 = (dx) / len * (10000 / scale) + x1;
            y2 = (dy) / len * (10000 / scale) + y1;
        }
    }
    // make the arrowheads 30 pixels (screen coordinates)
    var xTemp = (-dx) / len * (30 / scale);
    var yTemp = (-dy) / len * (30 / scale);

    // 0.3 is half the arrowhead angle in radians
    var c = Math.cos(0.3);
    var s = Math.sin(0.3);
    var x3 = xTemp * c - yTemp * s + x2;
    var y3 = xTemp * s + yTemp * c + y2;
    var x4 = xTemp * c - yTemp * -s + x2;
    var y4 = xTemp * -s + yTemp * c + y2;

    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.lineTo(x3, y3);
    ctx.lineTo(x4, y4);
    ctx.lineTo(x2, y2);
}

function renderLinks(node, scale) {
    "use strict";
    if (config.show_in) {
        node.inputs.forEach(function (link) {
            if (link.src_start === link.dst_start
                    && link.src_end === link.dst_end) {
                drawLoopArrow(node, link.links, scale);
            } else {
                drawArrow(link.x1, link.y1, link.x2, link.y2, scale);
            }
        });
    }
    if (config.show_out) {
        node.outputs.forEach(function (link) {
            if (link.src_start === link.dst_start
                    && link.src_end === link.dst_end) {
                drawLoopArrow(node, link.links, scale);
            } else {
                drawArrow(link.x1, link.y1, link.x2, link.y2, scale, false);
            }
        });
    }
}

function renderSubnetLabel(scale) {
    "use strict";
    //Draw subnet label
    ctx.font = "3em sans";
    var text = subnetLabel;
    if (config.filter !== "") {
        text += ":" + config.filter;
    }
    var size = ctx.measureText(text);
    ctx.fillStyle = renderConfig.labelBackgroundColor;
    ctx.strokeStyle = renderConfig.nodeColor;
    ctx.lineWidth = 3;
    if (config.filter === "") {
        ctx.globalAlpha = 1.0 - opacity(8, "label", scale);
    } else {
        ctx.globalAlpha = 1.0;
    }
    ctx.fillRect((rect.width - size.width) / 2 - 5, 20, size.width + 10, 40);
    ctx.strokeRect((rect.width - size.width) / 2 - 5, 20, size.width + 10, 40);
    ctx.fillStyle = fadeFont(renderConfig.labelColor, ctx.globalAlpha);
    ctx.globalAlpha = 1.0;
    ctx.fillText(text, (rect.width - size.width) / 2, 55);
}

function renderLabels(node, x, y, scale) {
    "use strict";
    var alpha = 0;
    ctx.font = "1.5em sans";
    ctx.globalAlpha = 1.0;
    if (scale > 25) {
        //Draw port labels at this zoom level
        alpha = opacity(32, "label", scale);
        if (m_selection["selection"] === null || m_selection["selection"] === node) {
            ctx.fillStyle = fadeFont(renderConfig.labelColor, alpha);
        } else {
            ctx.fillStyle = fadeFont(renderConfig.labelColor, alpha * 0.33);
        }
        if (node.subnet === 32) {
            Object.keys(node.ports).forEach(function (p) {
                var text = ports.get_alias(p);
                ctx.font = "1.5em sans";
                var sizeMin = ctx.measureText("mmmmm");
                var size = Math.max(ctx.measureText(text).width, sizeMin.width);
                var hOffset = sizeMin.width * 0.07;

                var newSize = (1.2 * scale) / size * 1.6;
                ctx.font = newSize.toString() + "em sans";
                size = ctx.measureText(text).width;
                var px;
                var py;
                if (node.ports[p].side === "left") {
                    px = node.ports[p].x * scale + x - size / 2;
                    py = node.ports[p].y * scale + y + hOffset;
                    ctx.fillText(text, px, py);
                } else if (node.ports[p].side === "right") {
                    px = node.ports[p].x * scale + x - size / 2;
                    py = node.ports[p].y * scale + y + hOffset;
                    ctx.fillText(text, px, py);
                } else if (node.ports[p].side === "top") {
                    px = node.ports[p].x * scale + x;
                    py = node.ports[p].y * scale + y;
                    ctx.save();
                    ctx.translate(px, py);
                    ctx.rotate(Math.PI / 2);
                    ctx.fillText(text, -size / 2, hOffset);
                    ctx.restore();
                } else if (node.ports[p].side === "bottom") {
                    px = node.ports[p].x * scale + x;
                    py = node.ports[p].y * scale + y;
                    ctx.save();
                    ctx.translate(px, py);
                    ctx.rotate(Math.PI / 2);
                    ctx.fillText(text, -size / 2, hOffset);
                    ctx.restore();
                }
            });
        }
    }
    //Draw node labels here
    ctx.font = "1.5em sans";
    var text = get_node_name(node);
    var size = ctx.measureText(text);
    var px = node.x * scale + x - size.width / 2;
    var py;
    if (node.subnet === 32) {
        py = node.y * scale + y + 10;
    } else {
        py = (node.y - node.radius) * scale + y - 5;
    }
    alpha = opacity(node.subnet, "label", scale);

    //ctx.font = fontsize + "em sans";
    if (m_selection["selection"] === null || m_selection["selection"] === node) {
        ctx.fillStyle = fadeFont(renderConfig.labelBackgroundColor, alpha * 0.5);
        ctx.fillRect(px, py + 2, size.width, -21);
        ctx.fillStyle = fadeFont(renderConfig.labelColor, alpha);
        ctx.fillText(text, px, py);
    } else {
        ctx.fillStyle = fadeFont(renderConfig.labelBackgroundColor, alpha * 0.166);
        ctx.fillRect(px, py + 2, size.width, -21);
        ctx.fillStyle = fadeFont(renderConfig.labelColor, alpha * 0.33);
        ctx.fillText(text, px, py);
    }
}

function renderNode(node) {
    "use strict";
    if (node.subnet < 31) {
        ctx.moveTo(node.x + node.radius, node.y);
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2, 0);
    } else {
        //terminal node (final IP address)
        ctx.strokeRect(node.x - node.radius, node.y - node.radius, node.radius * 2, node.radius * 2);
        //draw ports
        var width = 1.2;
        var height = 0.8;
        Object.keys(node.ports).forEach(function (p) {
            if (node.ports[p].side === "left") {
                //if the port is on the left side
                ctx.fillRect(node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
                ctx.strokeRect(node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
            } else if (node.ports[p].side === "right") {
                //if the port is on the right side
                ctx.fillRect(node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
                ctx.strokeRect(node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
            } else if (node.ports[p].side === "bottom") {
                //if the port is on the bottom side
                ctx.fillRect(node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
                ctx.strokeRect(node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
            } else {
                //the port must be on the top side
                ctx.fillRect(node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
                ctx.strokeRect(node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
            }
        });
    }
}

function renderClusters(collection, x, y, scale) {
    "use strict";
    var alpha = 0;
    var skip = false;
    var drawingLevel;
    if (m_selection["selection"] === null) {
        ctx.strokeStyle = renderConfig.linkColorTcp;
    } else {
        ctx.strokeStyle = renderConfig.linkColorTcpFaded;
    }
    ctx.globalAlpha = 1;

    //Draw the graph edges
    ctx.lineWidth = 2 / scale;
    drawingLevel = collection[0].subnet;
    ctx.beginPath();
    alpha = opacity(collection[0].subnet, "links", scale);
    ctx.globalAlpha = alpha;
    skip = alpha === 0;
    collection.forEach(function (node) {
        if (node.subnet !== drawingLevel) {
            ctx.stroke();
            ctx.beginPath();
            alpha = opacity(node.subnet, "links", scale);
            ctx.globalAlpha = alpha;
            skip = alpha === 0;
            drawingLevel = node.subnet;
        }
        if (!skip) {
            renderLinks(node, scale);
        }
    });
    ctx.stroke();

    if (m_selection["selection"] === null) {
        ctx.strokeStyle = renderConfig.nodeColor;
    } else {
        ctx.strokeStyle = renderConfig.nodeColorFaded;
    }
    // Draw the graph nodes
    ctx.lineWidth = 5 / scale;
    drawingLevel = collection[0].subnet;
    ctx.fillStyle = renderConfig.labelBackgroundColor;
    ctx.beginPath();
    alpha = opacity(collection[0].subnet, "node", scale);
    ctx.globalAlpha = alpha;
    skip = alpha === 0;
    collection.forEach(function (node) {
        if (node.subnet !== drawingLevel) {
            ctx.stroke();
            ctx.beginPath();
            alpha = opacity(node.subnet, "node", scale);
            ctx.globalAlpha = alpha;
            skip = alpha === 0;
            drawingLevel = node.subnet;
        }
        if (!skip) {
            renderNode(node);
        }
    });
    ctx.stroke();

    //Draw the labels
    ctx.resetTransform();
    collection.forEach(function (node) {
        renderLabels(node, x, y, scale);
    });

    //Draw the selected item over top everything else
    if (m_selection["selection"] !== null) {

        ctx.setTransform(scale, 0, 0, scale, x, y, 1);
        ctx.strokeStyle = renderConfig.linkColorTcp;
        ctx.globalAlpha = 1;

        //ctx.globalAlpha = opacity(m_selection["selection"].subnet, "links", scale);
        ctx.lineWidth = 2 / scale;
        ctx.beginPath();
        renderLinks(m_selection["selection"], scale);
        ctx.stroke();

        //ctx.globalAlpha = opacity(m_selection["selection"].subnet, "node", scale);
        ctx.lineWidth = 5 / scale;
        ctx.strokeStyle = renderConfig.nodeColor;
        ctx.fillStyle = renderConfig.labelBackgroundColor;
        ctx.beginPath();
        renderNode(m_selection["selection"]);
        ctx.stroke();

        ctx.resetTransform();
        renderLabels(m_selection["selection"], x, y, scale);
    }
}

function render(x, y, scale) {
    "use strict";
    ctx.resetTransform();
    ctx.fillStyle = renderConfig.backgroundColor;
    ctx.globalAlpha = 1.0;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (Object.keys(m_nodes).length === 0) {
        ctx.fillStyle = renderConfig.labelColorError;
        ctx.font = "3em sans";
        var size = ctx.measureText("No data available");
        ctx.fillText("No data available", rect.width / 2 - size.width / 2, rect.height / 2);
        return;
    }

    ctx.setTransform(scale, 0, 0, scale, x, y, 1);

    if (renderCollection.length !== 0) {
        renderClusters(renderCollection, x, y, scale);
    }

    renderSubnetLabel(scale);
}

function render_all() {
    "use strict";
    render(tx, ty, g_scale);
}
