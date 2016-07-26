function updateRenderRoot() {
    renderCollection = onScreen();
    currentSubnet = getSubnet();
}

function render(x, y, scale) {
    ctx.resetTransform();
    ctx.fillStyle = "#AAFFDD";
    ctx.globalAlpha = 1.0;
    ctx.fillRect(0, 0, width, height);

    if (Object.keys(nodeCollection).length == 0) {
        ctx.fillStyle = "#996666";
        ctx.font = "3em sans";
        var size = ctx.measureText("No data available");
        ctx.fillText("No data available", rect.width / 2 - size.width / 2, rect.height / 2);
        return
    }

    ctx.setTransform(scale, 0, 0, scale, x, y, 1);

    ctx.lineWidth = 1;
    ctx.fillStyle = "#0000FF";
    ctx.strokeStyle = "#5555CC";

    renderClusters(renderCollection, x, y, scale);
}

function renderClusters(collection, x, y, scale) {
    var level = currentLevel();
    var alpha = 1.0;

    for (var node in collection) {
        if (collection[node].level > level) {
            return;
        }

        alpha = opacity(collection[node].level);
        ctx.globalAlpha = alpha;
        ctx.lineWidth = 5 / scale;
        if (collection[node] == selection) {
            ctx.strokeStyle = "#BFBFFF";
        } else {
            ctx.strokeStyle = "#5555CC";
        }
        drawClusterNode(collection[node]);
        renderLinks(collection[node]);
    }
    renderLabels(collection, x, y, scale);
}

function renderLabels(collection, x, y, scale) {
    ctx.resetTransform();
    ctx.font = "1.5em sans";
    ctx.fillStyle = "#000000";
    if (scale > 25) {
        //Draw port labels here
        for (var node in collection) {
            if (collection[node].level > level) {
                return;
            }
            ctx.globalAlpha = opacity(collection[node].level);
            for (var p in collection[node].ports) {
                var text = p;
                if (collection[node].ports[p].alias != '') {
                    text = collection[node].ports[p].alias;
                }
                ctx.font = "1.5em sans";
                var sizeMin = ctx.measureText("mmmmm");
                var size = Math.max(ctx.measureText(text).width, sizeMin.width);
                var hOffset = sizeMin.width * 0.07;

                var newSize = (1.2 * scale) / size * 1.6;
                ctx.font = newSize.toString() + "em sans";
                size = ctx.measureText(text).width;
                //node.ports[p].x
                if (collection[node].ports[p].side == "left") {
                    var px = collection[node].ports[p].x * scale + x - size / 2;
                    var py = collection[node].ports[p].y * scale + y + hOffset;
                    ctx.fillText(text, px, py);
                } else if (collection[node].ports[p].side == "right") {
                    var px = collection[node].ports[p].x * scale + x - size / 2;
                    var py = collection[node].ports[p].y * scale + y + hOffset;
                    ctx.fillText(text, px, py);
                } else if (collection[node].ports[p].side == "top") {
                    var px = collection[node].ports[p].x * scale + x;
                    var py = collection[node].ports[p].y * scale + y;
                    ctx.save();
                    ctx.translate(px, py);
                    ctx.rotate(Math.PI/2);
                    ctx.fillText(text, -size / 2, hOffset);
                    ctx.restore();
                } else if (collection[node].ports[p].side == "bottom") {
                    var px = collection[node].ports[p].x * scale + x;
                    var py = collection[node].ports[p].y * scale + y;
                    ctx.save();
                    ctx.translate(px, py);
                    ctx.rotate(Math.PI/2);
                    ctx.fillText(text, -size / 2, hOffset);
                    ctx.restore();
                }
            }
        }
    }
    ctx.font = "1.5em sans";
    for (var node in collection) {
        //Draw node labels here
        var text = collection[node].number;
        var size = ctx.measureText(text);
        var px = collection[node].x * scale + x - size.width / 2;
        var py;
        if (collection[node].level == 32) {
            py = collection[node].y * scale + y + 10;
        } else {
            py = (collection[node].y - collection[node].radius) * scale + y - 5;
        }
        var alpha = opacity(collection[node].level);

        //ctx.font = fontsize + "em sans";
        ctx.globalAlpha = alpha * 0.5;
        ctx.fillStyle = "#FFFFFF";
        ctx.fillRect(px, py + 2, size.width, -21);
        ctx.globalAlpha = alpha;
        ctx.fillStyle = "#000000";
        ctx.fillText(text, px, py);
    }
    //Draw region label
    ctx.font = "3em sans";
    var size = ctx.measureText(currentSubnet);
    ctx.fillStyle = "#FFFFFF";
    ctx.strokeStyle = "#5555CC";
    ctx.lineWidth = 3;
    ctx.globalAlpha = 1.0 - opacity(8);
    ctx.fillRect((rect.width - size.width) / 2 - 5, 20, size.width + 10, 40);
    ctx.strokeRect((rect.width - size.width) / 2 - 5, 20, size.width + 10, 40);
    ctx.fillStyle = "#000000";
    ctx.fillText(currentSubnet, (rect.width - size.width) / 2, 55);

}

function drawClusterNode(node) {
    ctx.fillStyle = "#FFFFFF";
    if (node.level < 31) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2, 0);
        ctx.stroke();
    } else {
        //terminal node (final IP address)
        ctx.strokeRect(node.x - node.radius, node.y - node.radius, node.radius*2, node.radius * 2);
        //draw ports
        var width = 1.2;
        var height = 0.8;
        for (var p in node.ports) {
            if (node.ports[p].side == "left") {
                //if the port is on the left side
                ctx.fillRect( node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
                ctx.strokeRect( node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
            } else if (node.ports[p].side == "right") {
                //if the port is on the right side
                ctx.fillRect( node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
                ctx.strokeRect( node.ports[p].x - 0.6, node.ports[p].y - 0.4, width, height);
            } else if (node.ports[p].side == "bottom") {
                //if the port is on the bottom side
                ctx.fillRect( node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
                ctx.strokeRect( node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
            } else {
                //the port must be on the top side
                ctx.fillRect( node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
                ctx.strokeRect( node.ports[p].x - 0.4, node.ports[p].y - 0.6, height, width);
            }
        }
    }
}

function renderLinks(node) {
    var link = node.inputs
    if (config.show_in) {
        for (var i in link) {
            drawArrow(link[i].x1, link[i].y1, link[i].x2, link[i].y2, link[i].links);
        }
    }
    if (config.show_out) {
        link = node.outputs
        for (var i in link) {
            drawArrow(link[i].x1, link[i].y1, link[i].x2, link[i].y2, link[i].links);
        }
    }
}

function drawArrow(x1, y1, x2, y2, thickness = 1) {
    var dx = x2-x1;
    var dy = y2-y1;
    if (Math.abs(dx) + Math.abs(dy) < 10) {
        return;
    }

    var len = Math.hypot(dx, dy);
    var xTemp = (-dx) / len * (30 / scale); //make the arrowhead 30 screen pixels in size
    var yTemp = (-dy) / len * (30 / scale);

    var c = Math.cos(0.3); //0.3 is half angle of arrowhead in radians
    var s = Math.sin(0.3);
    var x3 = xTemp * c - yTemp * s + x2;
    var y3 = xTemp * s + yTemp * c + y2;
    var x4 = xTemp * c - yTemp * -s + x2;
    var y4 = xTemp * -s + yTemp * c + y2;

    ctx.beginPath();
    ctx.lineWidth = (Math.log(thickness) / 4 + 2) / scale;
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.lineTo(x3, y3);
    ctx.lineTo(x4, y4);
    ctx.lineTo(x2, y2);
    ctx.stroke();
}

//Given a node's level (subnet) return the opacity to render it at.
function opacity(level) {
    if (level == 8) {
        if (scale <= zoom8) {
            return 1.0;
        } else if (scale >= zoom8*2) {
            return 0.0;
        } else {
            return (scale - zoom8*2) / (-zoom8);
        }
    } else if (level == 16) {
        if (scale <= zoom8) {
            return 0.0;
        } else if (scale >= zoom16*2) {
            return 0.0;
        } else if (scale >= zoom8*2 && scale <= zoom16) {
            return 1.0;
        } else if (scale < zoom8*2) {
            return 1 - (scale - zoom8*2) / (-zoom8);
        } else if (scale > zoom16) {
            return (scale - zoom16*2) / (-zoom16);
        }
    } else if (level == 24) {
        if (scale <= zoom16) {
            return 0.0;
        } else if (scale >= zoom24*2) {
            return 0.0;
        } else if (scale >= zoom16*2 && scale <= zoom24) {
            return 1.0;
        } else if (scale < zoom16*2) {
            return 1 - (scale - zoom16*2) / (-zoom16);
        } else if (scale > zoom24) {
            return (scale - zoom24*2) / (-zoom24);
        }
    } else if (level == 32) {
        if (scale <= zoom24) {
            return 0.0;
        } else if (scale >= zoom24*2) {
            return 1.0;
        } else if (scale < zoom24*2) {
            return 1 - (scale - zoom24*2) / (-zoom24);
        }
    } else {
        return 0.0;
    }
}

function getSubnet() {
    var level = currentLevel();
    if (level == 8) {
        return "";
    }
    var closest = null;
    var dist = Infinity;
    var tempDist;
    for (var i in renderCollection) {
        if (renderCollection[i].level != level - 8) {
            continue;
        }
        tempDist = magnitudeSquared(
            renderCollection[i].x * scale + tx - rect.width / 2,
            renderCollection[i].y * scale + ty - rect.height / 2);
        if (tempDist < dist) {
            dist = tempDist;
            closest = renderCollection[i];
        }
    }
    if (closest == null) {
        return "";
    }
    return closest.address;
}

function magnitudeSquared(x, y) {
    return x*x+y*y;
}

//build a collection of all nodes currently visible in the window.
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

    var filtered = [];
    for (var node in visible) {
        if ((visible[node].client == true && config.show_clients) ||
            (visible[node].server == true && config.show_servers) ||
            (visible[node].client == true && visible[node].server == true)) {
            filtered.push(visible[node]);
        }
    }
    return filtered;
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

function resetViewport(collection) {
        var bbox = {'left': Infinity, 'right': -Infinity, 'top': Infinity, 'bottom': -Infinity};
        for (var i in collection) {
            var node = collection[i];
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
        }
        var scaleA = 0.92 * rect.width / (bbox.right - bbox.left);
        var scaleB = 0.92 * rect.height / (bbox.bottom - bbox.top);
        scale = Math.min(scaleA, scaleB);
        tx = rect.width / 2 - ((bbox.left + bbox.right) / 2) * scale;
        ty = rect.height / 2 - ((bbox.top + bbox.bottom) / 2) * scale;
}