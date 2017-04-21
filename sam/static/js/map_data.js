// Function(jqXHR jqXHR, String textStatus, String errorThrown)
function onNotLoadData(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("Failed to load data: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}


function GET_settings(ds, successCallback) {
    "use strict";
    if (typeof(successCallback) !== "function") {
        return;
    }
    $.ajax({
        url: "/settings",
        type: "GET",
        data: {"headless": 1, 'ds': ds},
        dataType: "json",
        error: onNotLoadData,
        success: successCallback
    });
}

function GET_timerange(successCallback) {
  "use strict";
  if (typeof(successCallback) !== "function") {
      return;
  }
  $.ajax({
    url: "/stats",
    type: "GET",
    data: {"q": "timerange", 'ds': config.ds},
    dataType: "json",
    error: onNotLoadData,
    success: successCallback
  });
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
  "use strict";
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
      return parent.address + "/" + parent.subnet;
    }).join(",");
  }
  request.flat = config.flat;
  request.ds = config.ds;
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
        render_all();
      }
    }
  });
}

function reportErrors(response) {
    if (response.hasOwnProperty("result")) {
        console.log("Result: " + response.result);
    }
}

/**
 * Update a node alias on the server.
 *
 * @param address  node address, "192.168"
 * @param name  the new name to use for that address
 */
function POST_node_alias(address, name) {
    "use strict";
    var request = {
      "node": address,
      "alias": name
    }
    $.ajax({
        url: "/nodes",
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
        "filter": config.filter,
        "protocol": config.protocol,
        "tstart": config.tstart,
        "tend": config.tend,
        "ds": config.ds
    };
    if (config.flat) {
      requestData.flat = true;
    }
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

function GET_portinfo(port, callback) {
    "use strict";
    var requestData = {"port": port.join(",")};
    $.ajax({
        url: "/portinfo",
        type: "GET",
        data: requestData,
        dataType: "json",
        error: onNotLoadData,
        success: function (response) {
            ports.private.GET_response(response);

            if (typeof callback === "function") {
                callback();
            }
        }
    });
}

function checkLoD() {
  "use strict";
  var nodesToLoad = [];
  renderCollection.forEach(function (node) {
    if (node.subnet < currentSubnet(g_scale)) {
      nodesToLoad.push(node);
    }
  });
  if (nodesToLoad.length > 0) {
    GET_nodes(nodesToLoad);
    updateRenderRoot();
    render_all();
  }
}

function GET_details(node, callback) {
    "use strict";

    var requestData = {
        "address": node.address + "/" + node.subnet,
        "filter": config.filter,
        "tstart": config.tstart,
        "tend": config.tend,
        "order": "-links",
        "simple": true,
        "ds": config.ds
        };

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
            node.details["inputs"] = result.inputs;
            node.details["outputs"] = result.outputs;
            node.details["ports"] = result.ports;
            node.details["loaded"] = true;

            var index;
            for (index = result.inputs.headers.length - 1; index >= 0 && result.inputs.headers[index][0] !== "port"; index -= 1) {};
            if (index >= 0) {
                result.inputs.rows.forEach(function (element) {
                    ports.request_add(element[index]);
                });
            }
            for (index = result.outputs.headers.length - 1; index >= 0 && result.outputs.headers[index][0] !== "port"; index -= 1) {};
            if (index >= 0) {
                result.outputs.rows.forEach(function (element) {
                    ports.request_add(element[index]);
                });
            }

            for (index = result.ports.headers.length - 1; index >= 0 && result.ports.headers[index][0] !== "port"; index -= 1) {};
            if (index >= 0) {
                result.ports.rows.forEach(function (element) {
                    ports.request_add(element[index]);
                });
            }
            ports.request_submit();

            if (typeof callback === "function") {
                callback();
            }
        }
    });
}

function GET_details_sorted(node, component, order, callback) {
    "use strict";

    var requestData = {
        "address": node.address + "/" + node.subnet,
        "filter": config.filter,
        "tstart": config.tstart,
        "tend": config.tend,
        "order": order,
        "simple": true,
        "component": component,
        "ds": config.ds
        };

    $.ajax({
        url: "/details",
        //dataType: "json",
        type: "GET",
        data: requestData,
        error: onNotLoadData,
        success: function (result) {
            var index;
            Object.keys(result).forEach(function (part) {
                node.details[part] = result[part]
                for (index = result[part].headers.length - 1; index >= 0 && result[part].headers[index][0] !== "port"; index -= 1) {};
                if (index >= 0) {
                    result[part].rows.forEach(function (element) {
                        ports.request_add(element[index]);
                    });
                }
            });
            ports.request_submit();

            if (typeof callback === "function") {
                callback();
            }
        }
    });
}
