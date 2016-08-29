// Function(jqXHR jqXHR, String textStatus, String errorThrown)
function onNotLoadData(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("Failed to load data: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}

/*
Retrieves the children of the given nodes and imports them. Optionally calls a callback when done.

parents: either an array of nodes, or null.
    if a list of nodes, retrieves the children of the nodes that don't have children loaded
    if null, retreives the top-level nodes. (the /8 subnet)
callback: if is a function, call it when done importing.

ajax response: should be an object, where keys are address strings ("12.34.56.78") and values are arrays of objects (nodes)
*/
function GET_nodes(parents, callback) {
    var request = {}

    if (parents !== null) {
        //filter out parents with children already loaded
        parents = parents.filter(function (parent) {
            return !parent.childrenLoaded;
        });
        if (parents.length == 0) {
            return;
        }
        request.address = parents.map(function (parent) {
            parent.childrenLoaded = true;
            return parent.address;
        }).join(",");
    }
    request.filter = filter;

    $.ajax({
        url: "/nodes",
        type: "GET",
        data: request,
        dataType: "json",
        error: onNotLoadData,
        success: function (response) {
            node_update(response);
            if (typeof callback === "function") {
                callback(response);
            } else {
                updateRenderRoot();
                render(tx, ty, scale);
            }
        }
    });
}

function reportErrors(response) {
    if (response.code !== 0) {
        console.log("Error: " + response.message);
    }
}

function POST_node_alias(node, name) {
    "use strict";
    var request = {"node": node.address, "alias": name}
    $.ajax({
        url: "/nodeinfo",
        type: "POST",
        data: request,
        error: onNotLoadData,
        success: reportErrors
    });
}

function GET_links(addrs) {
    "use strict";
    var requestData = {
        "address": addrs.join(","),
        "filter": filter};
    $.ajax({
        url: "/links",
        type: "GET",
        data: requestData,
        error: onNotLoadData,
        success: GET_links_callback
    });
}

function POST_portinfo(request) {
    "use strict";
    $.ajax({
        url: "/portinfo",
        type: "POST",
        data: request,
        error: onNotLoadData,
        success: reportErrors
    });
}

function GET_portinfo(port) {
    "use strict";
    var requestData = {"port": port.join(",")};
    $.ajax({
        url: "/portinfo",
        type: "GET",
        data: requestData,
        dataType: "json",
        error: onNotLoadData,
        success: GET_portinfo_callback
    });
}

function checkLoD() {
    "use strict";

    var nodesToLoad = []
    renderCollection.forEach(function (node) {
        if (node.subnet < currentSubnet()) {
            nodesToLoad.push(node);
        }
    });
    GET_nodes(nodesToLoad);
    updateRenderRoot();
    render(tx, ty, scale);
}

function GET_details(node, callback) {
    "use strict";

    var requestData = {"address": node.address}

    $.ajax({
        url: "/details",
        //dataType: "json",
        type: "GET",
        data: requestData,
        error: onNotLoadData,
        success: function (result) {
            node.details["unique_in"] = result.unique_in;
            node.details["unique_out"] = result.unique_out;
            node.details["unique_ports"] = result.unique_ports;
            node.details["conn_in"] = result.conn_in;
            node.details["conn_out"] = result.conn_out;
            node.details["ports_in"] = result.ports_in;
            node.details["loaded"] = true;

            result.conn_in.forEach(function (element) {
                element[1].forEach(function (port) {
                    port_request_add(port.port);
                });
            });
            result.conn_out.forEach(function (element) {
                element[1].forEach(function (port) {
                    port_request_add(port.port);
                });
            });
            result.ports_in.forEach(function (element) {
                port_request_add(element.port);
            });
            port_request_submit();

            if (typeof callback === "function") {
                callback();
            }
        }
    });
}