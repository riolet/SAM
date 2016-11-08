var g_typing_timer = null;
var g_running_requests = [];
var g_state = null;
var g_data = {"quick": null, "inputs": null, "outputs": null, "ports": null, "children": null};

function buildKeyValueRow(key, value) {
    "use strict";
    var tr = document.createElement("TR");
    var td = document.createElement("TD");
    td.appendChild(document.createTextNode(key.toString()));
    tr.appendChild(td);

    td = document.createElement("TD");
    td.appendChild(document.createTextNode(value.toString()));
    tr.appendChild(td);
    return tr;
}

function buildKeyMultiValueRows(key, values) {
    "use strict";
    var rows = [];
    var tr = document.createElement("TR");
    var td = document.createElement("TD");
    td.appendChild(document.createTextNode(key.toString()));
    tr.appendChild(td);
    td.rowSpan = values.length;

    values.forEach(function (e) {
        td = document.createElement("TD");
        td.appendChild(document.createTextNode(e.toString()));
        tr.appendChild(td);
        rows.push(tr);
        tr = document.createElement("TR");
    });
    return rows;
}

function build_table_children(dataset) {
    "use strict";
    var tbody = document.createElement("TBODY");
    var tr, td;
    dataset.forEach(function (row) {
        tr = document.createElement("TR");
        // each row has .address .hostname .subnet .endpoints .ratio
        td = document.createElement("TD");
        td.appendChild(create_link(row.address, row.subnet));
        tr.appendChild(td);
        td = document.createElement("TD");
        td.appendChild(document.createTextNode(row.hostname));
        tr.appendChild(td);
        td = document.createElement("TD");
        td.appendChild(document.createTextNode(row.endpoints));
        tr.appendChild(td);
        td = document.createElement("TD");
        td.appendChild(document.createTextNode(build_role_text(row.ratio)));
        tr.appendChild(td);
        tbody.appendChild(tr);
    });
    return tbody;
}

function build_role_text(ratio) {
    "use strict";
    var role_text = ratio + " (";
    if (ratio <= 0) {
        role_text += "client";
    } else if (ratio < 0.35) {
        role_text += "mostly client";
    } else if (ratio < 0.65) {
        role_text += "mixed client/server";
    } else if (ratio < 1) {
        role_text += "mostly server";
    } else {
        role_text += "server";
    }
    role_text += ")";
    return role_text;
}

function create_link(address, subnet) {
    "use strict";
    var text = address + "/" + subnet;
    var link = "/metadata?ip=" + text;

    var icon = document.createElement("I");
    icon.className = "tasks icon";

    var a = document.createElement("A");
    a.appendChild(icon);
    a.appendChild(document.createTextNode(text));
    a.href = link;
    return a;
}

function present_quick_info(info) {
    "use strict";
    var target = document.getElementById("quickinfo");
    target.innerHTML = "";
    info.forEach(function (kv_pair) {
        if (Array.isArray(kv_pair[1])) {
            buildKeyMultiValueRows(kv_pair[0], kv_pair[1]).forEach(function (row) {
                target.appendChild(row);
            });
        } else {
            target.appendChild(buildKeyValueRow(kv_pair[0], kv_pair[1]));
        }
    });
}

function present_detailed_info(info) {
    "use strict";
    if (info === undefined) {
        info = g_data
    }
    var old_body;
    var new_body;
    if (info.hasOwnProperty("inputs") && info.inputs !== null) {
        old_body = document.getElementById("conn_in");
        new_body = sel_build_table_connections(info.inputs);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "conn_in";
    }

    if (info.hasOwnProperty("outputs") && info.outputs !== null) {
        old_body = document.getElementById("conn_out");
        new_body = sel_build_table_connections(info.outputs);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "conn_out";
    }

    if (info.hasOwnProperty("ports") && info.ports !== null) {
        old_body = document.getElementById("ports_in");
        new_body = sel_build_table_ports(info.ports);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "ports_in";
    }

    if (info.hasOwnProperty("children") && info.children !== null) {
        old_body = document.getElementById("child_nodes");
        new_body = build_table_children(info.children);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "child_nodes";
    }

    //enable the tooltips on ports
    $('.popup').popup();
}

function normalizeIP(ipString) {
    "use strict";
    var add_sub = ipString.split("/");

    var address = add_sub[0];
    var subnet = add_sub[1];

    var segments = address.split(".");
    var num;
    var final_ip;
    segments = segments.reduce(function (list, element) {
        num = parseInt(element);
        if (!isNaN(num)) {
            list.push(num);
        }
        return list;
    }, []);

    final_ip = segments.join(".");

    var zeroes_to_add = 4 - segments.length;
    for (; zeroes_to_add > 0; zeroes_to_add -= 1) {
        final_ip += ".0";
    }
    num = parseInt(subnet);
    if (num) {
        final_ip += "/" + subnet;
    } else {
        final_ip += "/" + (segments.length * 8);
    }
    return final_ip;
}

function minimizeIP(ip) {
    "use strict";
    var add_sub = ip.split("/");
    var subnet = parseInt(add_sub[1]) / 8;
    var segs = add_sub[0].split(".");
    if (isNaN(subnet)) {
        subnet = Math.min(4, segs.length);
    }
    var i;
    var minimized_ip = segs[0];
    for (i = 1; i < subnet; i += 1) {
        minimized_ip += "." + segs[i];
    }
    return minimized_ip;
}

function onNotLoadData(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("Failed to load data: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}

function GET_data(ip, part, callback){
    "use strict";

    var request = {"address": minimizeIP(ip)};
    $.ajax({
        url: "/details/" + part,
        type: "GET",
        data: request,
        error: onNotLoadData,
        success: callback
    });
}

function StateChangeEvent(newState) {
    "use strict";
    this.type = "stateChange";
    this.newState = newState;
}

function dispatcher(event) {
    "use strict";
    if (event.type === "stateChange") {
        g_state = event.newState;
    }
    if (g_state === null) {
        console.error("g_state is null");
    } else {
        g_state(event);
    }
}

function abortRequests(requests) {
    "use strict";
    var xhr;
    while (xhr = requests.pop()) {
        xhr.abort();
        //clearTimeout(xhr);
    }
}

function requestMoreDetails(event) {
    "use strict";
    //typing happens:
    //  abortRequests
    //  proceed to restartTypingTimer
    //Info arrives:
    //  proceed to waiting
    var searchbar = document.getElementById("hostSearch");

    if (event.type == "stateChange") {
        //Requesting more details
        var input = searchbar.getElementsByTagName("input")[0];
        console.log("Requesting More Details");

        GET_data(input.value, "inputs,outputs,ports,children", function (response) {
            // More details arrived
            // Render into browser
            g_data.inputs = response.inputs;
            g_data.outputs = response.outputs;
            g_data.ports = response.ports;
            g_data.children = response.children;
            present_detailed_info(g_data);

            response.inputs.forEach(function (element) {
                element[1].forEach(function (port) {
                    ports.request_add(port.port);
                });
            });
            response.outputs.forEach(function (element) {
                element[1].forEach(function (port) {
                    ports.request_add(port.port);
                });
            });
            response.ports.forEach(function (port) {
                ports.request_add(port.port);
            });
            ports.request_submit(present_detailed_info);

            console.log("More Details Arrived. Returning to waiting.");
            //Return to passively waiting
            dispatcher(new StateChangeEvent(restartTypingTimer));
        });

    } else if (event.type === "input") {
        //Aborting requests
        console.log("Aborting Requests");
        abortRequests(g_running_requests);
        //Clear details pane
        //TODO: actually clear details pane
        //Continue to typing timer
        dispatcher(new StateChangeEvent(restartTypingTimer));
        dispatcher(event);
    }
}

function requestQuickInfo(event) {
    "use strict";
    //typing happens:
    //  abortRequests
    //  proceed to restartTypingTimer
    //Info arrives:
    //  proceed to requestMoreDetails()
    var searchbar = document.getElementById("hostSearch");

    if (event.type == "stateChange") {
        //Requesting Quick Info
        var input = searchbar.getElementsByTagName("input")[0];
        console.log("Requesting Quick Info");
        searchbar.classList.add("loading");
        present_quick_info([["Loading", "..."]]);
        var normalizedIP = normalizeIP(input.value);
        GET_data(normalizedIP, "quick_info", function (response) {
            // Quick info arrived
            searchbar.classList.remove("loading");
            // Render into browser
            present_quick_info(response.quick_info);
            input.value = normalizedIP;
            console.log("Quick info Arrived. Proceeding to Request More Details");

            //Continue to more details
            dispatcher(new StateChangeEvent(requestMoreDetails));
        });
    } else if (event.type === "input") {
        //Aborting requests
        console.log("Aborting Requests");
        abortRequests(g_running_requests);
        searchbar.classList.remove("loading");
        //Clear quickinfo
        present_quick_info([["Waiting", "..."]]);
        //Continue to typing timer
        dispatcher(new StateChangeEvent(restartTypingTimer));
        dispatcher(event);
    }
}

function restartTypingTimer(event) {
    "use strict";
    //typing happens:
    //  restart the timer
    //timer times out:
    //  advance to request quick-info
    if (event.type === "input") {
        console.log("Restarting Timer");
        if (g_typing_timer !== null) {
            clearTimeout(g_typing_timer);
        }
        g_typing_timer = setTimeout(function () {
            //Timer expired. Run the quick-info request!
            console.log("Proceeding to Request Quick Info");

            dispatcher(new StateChangeEvent(requestQuickInfo));
        }, 700);
    }
}

function init() {
    "use strict";
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    input.oninput = dispatcher;
    sel_init();

    // Enable tabbed views
    $('.secondary.menu .item').tab();
    // Enable the port data popup window
    $(".input.icon").popup();
    // Make the ports table sortable
    $("table.sortable").tablesort();

    //configure ports
    ports.display_callback = function() {
        present_detailed_info();
    };

    dispatcher(new StateChangeEvent(restartTypingTimer));

    if (g_initial_ip !== '') {
        input.value = g_initial_ip;
        dispatcher(new StateChangeEvent(requestQuickInfo));
    }
}

window.onload = function () {
    "use strict";
    init();
};