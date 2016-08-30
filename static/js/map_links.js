var m_links = {};
var m_link_requests = [];
var m_link_timer;

function link_loaded(address) {
    return m_links.hasOwnProperty(address);
}

function link_request_add(address) {
    if (!link_loaded(address)) {
        m_link_requests.push(address);
    }
}

function link_request_add_all(collection) {
    Object.keys(collection).forEach(function (node_name) {
        link_request_add(collection[node_name].address)
        link_request_add_all(collection[node_name].children);
    });
}

function dist_between_squared(x1, y1, x2, y2) {
    return Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2);
}

function link_comparator(a, b) {
    var aValue;
    var bValue;
    //determine value of a and b
    var centerx = (rect.width - 2 * tx) / (2 * scale);
    var centery = (rect.height - 2 * ty) / (2 * scale);

    aNode = findNode(a);
    bNode = findNode(b);
    aValue = 1 / Math.max(1, dist_between_squared(aNode.x, aNode.y, centerx, centery));
    bValue = 1 / Math.max(1, dist_between_squared(bNode.x, bNode.y, centerx, centery));
    // _Value is now a number between 0 and 1, where 1 is closer to center screen

    if (renderCollection.indexOf(aNode) != -1) {
        aValue += 32 - aNode.subnet;
    }
    // _Value is now a number between 0 and 25 based on being visible and zoomed further out

    //return bValue - aValue to sort by most valuable first
    return bValue - aValue;
}

function link_request_submit() {
    const chunksize = 40;
    var request = m_link_requests.filter(function (address) {
        return !m_links.hasOwnProperty(address);
    });

    //remove duplicates by sorting and comparing neighbors
    request = request.sort().filter(function(address, i, ary) {
        return !i || address != ary[i - 1];
    });
    request.sort(link_comparator);

    if (request.length == 0) {
        m_link_requests = [];
        return;
    }

    console.log("requesting:")
    if (chunksize > request.length) {
        console.log(request);
        GET_links(request);
        m_link_requests = [];
    } else {
        console.log(request.slice(0, chunksize));
        GET_links(request.slice(0, chunksize));
        m_link_requests = request.slice(chunksize);
        m_link_timer = setTimeout(link_request_submit, 500);
    }

}

function link_remove_all(collection) {
    Object.keys(collection).forEach(function (node_name) {
        collection[node_name].inputs = [];
        collection[node_name].outputs = [];
        link_remove_all(collection[node_name].children);
    });
}

function links_reset() {
    link_remove_all(m_nodes);
    link_request_add_all(m_nodes);
    link_request_submit();
}

function GET_links_callback(result) {
    //for each node address in result:
    //  find that node,
    //  add the new inputs/outputs to that node
    Object.keys(result).forEach(function (address) {
        node = findNode(address);
        node.inputs = result[address].inputs;
        node.outputs = result[address].outputs;
        node.server = node.inputs.length > 0;
        node.client = node.outputs.length > 0;
    });
    render(tx, ty, scale);
}