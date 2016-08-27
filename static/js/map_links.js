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

function link_request_submit() {
    var request = m_link_requests.filter(function (address) {
        return !m_links.hasOwnProperty(address);
    });

    //remove duplicates by sorting and comparing neighbors
    request = request.sort().filter(function(address, i, ary) {
        return !i || address != ary[i - 1];
    });

    m_link_requests = [];
    if (request.length > 0) {
        GET_links(request);
    }
}

function link_removeAll(collection) {
    Object.keys(m_nodes).forEach(function (node_name) {
        collection[node_name].inputs = []
        collection[node_name].outputs = []
        removeAllLinks(collection[node_name].children);
    });
}

function GET_links_callback(result) {
    //for each node address in result:
    //  find that node,
    //  add the new inputs/outputs to that node

}