m_links = {};
m_link_requests = [];

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

function link_comparator(a, b) {
    //determine value of a and b

    //return bValue - aValue to sort by most valuable first
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

    // TODO: sort by value to user (i.e. what will the user need first?)
    //request.sort(link_comparator);

    console.log("requesting:")
    if (chunksize > request.length) {
        console.log(request);
        GET_links(request);
        m_link_requests = [];
    } else {
        console.log(request.slice(0, chunksize));
        GET_links(request.slice(0, chunksize));
        m_link_requests = request.slice(chunksize);
        setTimeout(link_request_submit, 500);
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