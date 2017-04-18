var m_link_requests = [];
var m_link_timer;

function link_request_add(address) {
    "use strict";
    m_link_requests.push(address);
}

function link_request_add_all(collection) {
    "use strict";
    Object.keys(collection).forEach(function (node_name) {
        link_request_add(collection[node_name].address)
        link_request_add_all(collection[node_name].children);
    });
}

function dist_between_squared(x1, y1, x2, y2) {
    "use strict";
    return Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2);
}

function link_comparator(a, b) {
    "use strict";
    //determine value of a and b
    var centerx = (rect.width - 2 * tx) / (2 * g_scale);
    var centery = (rect.height - 2 * ty) / (2 * g_scale);

    var aNode = findNode(a);
    var bNode = findNode(b);
    if (aNode === null || bNode === null) {
        return 0;
    }
    var aValue = 1 / Math.max(1, dist_between_squared(aNode.x, aNode.y, centerx, centery));
    var bValue = 1 / Math.max(1, dist_between_squared(bNode.x, bNode.y, centerx, centery));
    // _Value is now a number between 0 and 1, where 1 is closer to center screen

    if (renderCollection.indexOf(aNode) != -1) {
        aValue += 32 - aNode.subnet;
    }
    // _Value is now a number between 0 and 25 based on being visible and zoomed further out

    //return bValue - aValue to sort by most valuable first
    return bValue - aValue;
}

function link_request_submit() {
    "use strict";
    var request = m_link_requests.slice();

    //remove duplicates by sorting and comparing neighbors
    request = request.sort().filter(function(address, i, ary) {
        return !i || address != ary[i - 1];
    });
    request.sort(link_comparator);

    if (request.length == 0) {
        m_link_requests = [];
        return;
    }

    if (g_chunkSize > request.length) {
        GET_links(request);
        m_link_requests = [];
    } else {
        GET_links(request.slice(0, g_chunkSize));
        m_link_requests = request.slice(g_chunkSize);
        m_link_timer = setTimeout(link_request_submit, 500);
    }
}

function link_remove_all(collection) {
    "use strict";
    Object.keys(collection).forEach(function (node_name) {
        collection[node_name].inputs = [];
        collection[node_name].outputs = [];
        collection[node_name].server = false;
        collection[node_name].client = false;
        link_remove_all(collection[node_name].children);
    });
}

function links_reset() {
    "use strict";
    link_remove_all(m_nodes);
    link_request_add_all(m_nodes);
    link_request_submit();
}

function GET_links_callback(result) {
    "use strict";
    //for each node address in result:
    //  find that node,
    //  add the new inputs/outputs to that node

    Object.keys(result).forEach(function (address) {
        var node = findNode(address);
        node.inputs = result[address].inputs;
        node.outputs = result[address].outputs;
        //position links
        if (node.subnet === 32) {
            link_processPorts(node.inputs, node);
        }
        //determine server/client
        node.server = node.inputs.length > 0;
        node.client = node.outputs.length > 0;
        //colorize links (map_render::color_links)
        color_links(node.inputs);
        color_links(node.outputs);
    });
    ports.request_submit();
    updateRenderRoot();
    render_all();
}

function link_closestEmptyPort(dest, src, used) {
    "use strict";
    var right = [1, 0, 2, 7, 3, 6, 4, 5];
    var top = [3, 2, 4, 1, 5, 0, 6, 7];
    var bottom = [6, 7, 5, 0, 4, 1, 3, 2];
    var left = [4, 5, 3, 6, 2, 7, 1, 0];

    //console.log("Link_closest from ", src.x, src.y, " to ", dest.x, dest.y);
    var dx = dest.x - src.x;
    var dy = dest.y - src.y;

    var chooser = function (i) {
        return used[i] === false;
    };
    var choice;

    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //port on right
            choice = right.find(chooser);
        } else {
            //port on left
            choice = left.find(chooser);
        }
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //port on bottom
            choice = bottom.find(chooser);
        } else {
            //port on top
            choice = top.find(chooser);
        }
    }
    return choice;
}

function link_processPorts(links, dest) {
    "use strict";
    if (links.length === 0) {
        return;
    }

    //
    //    3_2
    //  4|   |1
    //  5|___|0
    //    6 7
    //
    var used = [false, false, false, false, false, false, false, false];
    var locations = ["r-b", "r-t",
                     "t-r", "t-l",
                     "l-t", "l-b",
                     "b-l", "b-r"];

    var port_tracker = {};
    var j;
    var choice = 0;
    //the first 8 unique port numbers should be mapped to locations.
    for (j = 0; j < Object.keys(links).length; j += 1) {
        if (port_tracker.hasOwnProperty(links[j].port)) {
            continue;
        }
        ports.request_add(links[j].port);
        var source = find_by_range(links[j].src_start, links[j].src_end);
        choice = link_closestEmptyPort(dest, source, used);
        if (choice === undefined) {
            continue;
        }
        port_tracker[links[j].port] = locations[choice];
        used[choice] = true;
        if (Object.keys(port_tracker).length >= 8) {
            break;
        }
    }
    dest.ports = port_tracker;
}
