var g_typing_timer = null;
var g_running_requests = [];
var g_state = null;
var g_data = {"quick": null, "inputs": null, "outputs": null, "ports": null};

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

function present_quick_info(info) {
    "use strict";
    var target = document.getElementById("quickinfo");
    target.innerHTML = "";
    info.forEach(function (kv_pair) {
       target.appendChild(buildKeyValueRow(kv_pair[0], kv_pair[1]));
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

    //enable the tooltips on ports
    $('.popup').popup();
}


function onNotLoadData(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("Failed to load data: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}

function GET_data(ip, part, callback){
    "use strict";
    var request = {"address": ip}
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
        //xhr.abort();
        clearTimeout(xhr);
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

        GET_data(input.value, "inputs,outputs,ports", function (response) {
            // More details arrived
            // TODO: remove loading icon from tabs??
            // Render into browser
            g_data.inputs = response.inputs;
            g_data.outputs = response.outputs;
            g_data.ports = response.ports;
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
        GET_data(input.value, "quick_info", function (response) {
            // Quick info arrived
            searchbar.classList.remove("loading");
            // Render into browser
            present_quick_info(response.quick_info)
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
    sel_init()

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
}

window.onload = function () {
    "use strict";
    init();
};