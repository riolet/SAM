function checkLoD() {
  "use strict";
  let nodesToLoad = [];
  renderCollection.forEach(function (node) {
    if (node.subnet < currentSubnet(g_scale)) {
      nodesToLoad.push(node);
    }
  });
  if (nodesToLoad.length > 0) {
    nodes.GET_request(nodesToLoad, function () {
      updateRenderRoot();
      render_all();
    });
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
        "ds": controller.ds
        };

    $.ajax({
        url: "./details",
        //dataType: "json",
        type: "GET",
        data: requestData,
        error: generic_ajax_failure,
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
        "ds": controller.ds
        };

    $.ajax({
        url: "./details",
        //dataType: "json",
        type: "GET",
        data: requestData,
        error: generic_ajax_failure,
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
