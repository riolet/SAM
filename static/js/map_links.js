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
    const chunksize = 40;
    var i;
    var request = m_link_requests.filter(function (address) {
        return !m_links.hasOwnProperty(address);
    });

    //remove duplicates by sorting and comparing neighbors
    request = request.sort().filter(function(address, i, ary) {
        return !i || address != ary[i - 1];
    });

    for (i = 0; i < request.length; i += chunksize) {
        if (i + chunksize > request.length) {
            GET_links(request.slice(i));
        } else {
            GET_links(request.slice(i, i + chunksize));
        }
    }

    m_link_requests = [];
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