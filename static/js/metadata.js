/*global
    ports, $, sel_init, sel_build_table_connections, sel_build_table_ports, window, g_initial_ip, g_known_tags, g_known_envs
*/
var g_typing_timer = null;
var g_running_requests = [];
var g_state = null;
var g_data = {"quick": null, "inputs": null, "outputs": null, "ports": null, "children": null};

/********************
   Helper functions
 ********************/
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
    while (zeroes_to_add > 0) {
        final_ip += ".0";
        zeroes_to_add -= 1;
    }
    num = parseInt(subnet);
    if (num) {
        final_ip += "/" + subnet;
    } else {
        final_ip += "/" + (segments.length * 8);
    }
    return final_ip;
}

function getIP_Subnet() {
    "use strict";
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    var normalizedIP = normalizeIP(input.value);
    var split = normalizedIP.split("/");
    return {
        "normal": normalizedIP,
        "ip": split[0],
        "subnet": parseInt(split[1])
    };
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

/**************************
   Presentation Functions
 **************************/
function buildKeyValueRow(key, value) {
    "use strict";
    var tr = document.createElement("TR");
    var td = document.createElement("TD");
    td.appendChild(document.createTextNode(key));
    tr.appendChild(td);
    if (typeof(value) === "object") {
        tr.appendChild(value);
    } else {
        td = document.createElement("TD");
        td.appendChild(document.createTextNode(value));
        tr.appendChild(td);
    }
    return tr;
}

function buildKeyMultiValueRows(key, values) {
    "use strict";
    var rows = [];
    var tr = document.createElement("TR");
    var td = document.createElement("TD");
    td.appendChild(document.createTextNode(key));
    tr.appendChild(td);
    td.rowSpan = values.length;

    values.forEach(function (e) {
        td = document.createElement("TD");
        td.appendChild(document.createTextNode(e));
        tr.appendChild(td);
        rows.push(tr);
        tr = document.createElement("TR");
    });
    return rows;
}

function build_link(address, subnet) {
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

function build_role_text(ratio) {
    "use strict";
    var role_text = parseFloat(ratio).toFixed(2) + " (";
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

function build_table_children(dataset) {
    "use strict";
    var tbody = document.createElement("TBODY");
    var tr;
    var td;
    dataset.forEach(function (row) {
        tr = document.createElement("TR");
        // each row has .address .hostname .subnet .endpoints .ratio
        td = document.createElement("TD");
        td.appendChild(build_link(row.address, row.subnet));
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

function build_pagination(page, page_size, component, total) {
    "use strict";
    var has_prev = page > 1;
    var has_next = total > page * page_size;
    var page_first = (page - 1) * page_size + 1;
    var page_last = Math.min(total, page_first + page_size - 1);
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    var normalizedIP = normalizeIP(input.value);

    var div = document.createElement("DIV");
    var button;
    var span;

    // PREV button
    button = document.createElement("BUTTON");
    button.appendChild(document.createTextNode("prev"));
    if (has_prev) {
        button.className = "ui button";
        button.onclick = function () {
            GET_page(normalizedIP, component, page - 1);
        };
    } else {
        button.className = "ui button disabled";
    }
    div.appendChild(button);

    // descriptive text
    span = document.createElement("SPAN");
    span.appendChild(document.createTextNode("showing " + page_first + "-" + page_last + " of " + total));
    div.appendChild(span);

    // NEXT button
    button = document.createElement("BUTTON");
    button.appendChild(document.createTextNode("next"));
    if (has_next) {
        button.className = "ui button";
        button.onclick = function () {
            GET_page(normalizedIP, component, page + 1);
        };
    } else {
        button.className = "ui button disabled";
    }
    div.appendChild(button);
    return div;
}

function build_label(text, color, disabled) {
    "use strict";
    var label = document.createElement("SPAN");
    label.className = "ui " + color + " large label";
    if (disabled) {
        label.classList.add("disabled");
    }
    label.appendChild(document.createTextNode(text));
    return label;
}

function present_quick_info(info) {
    "use strict";
    var target = document.getElementById("quickinfo");
    var input;
    var key;
    var values;
    var i;
    var div;
    var td;
    var tag_div;
    target.innerHTML = "";
    if (info.hasOwnProperty("address")) {
        target.appendChild(buildKeyValueRow("IPv4 address / subnet", info.address));
    }
    if (info.hasOwnProperty("error")) {
        target.appendChild(buildKeyValueRow(info.error, "..."));
    } else if (info.hasOwnProperty("message")) {
        target.appendChild(buildKeyValueRow(info.message, "..."));
    } else {
        if (info.hasOwnProperty("name")) {
            input = document.createElement("INPUT");
            input.placeholder = "-";
            input.type = "text";
            input.value = info.name;
            input.dataset.content = info.name;
            input.onblur = hostname_edit_callback;
            input.onkeyup = hostname_edit_callback;
            i = document.createElement("I");
            i.className = "write icon";
            div = document.createElement("DIV");
            div.className = "ui transparent left icon input";
            div.appendChild(input);
            div.appendChild(i);
            td = document.createElement("TD");
            td.appendChild(div);
            target.appendChild(buildKeyValueRow("Name", td));
        }
        if (info.hasOwnProperty("tags")) {
            tag_div = document.createElement("TD");

            //create a selection box
            /*
            <div class="ui multiple search selection dropdown">
              <input name="gender" value="default,default2" type="hidden">
              <i class="dropdown icon"></i>
              <div class="default text">Default</div>
              <div class="menu">
                  <div class="item" data-value="0">Value</div>
                  <div class="item" data-value="1">Another Value</div>
                  <div class="item" data-value="default">Default Value</div>
                  <div class="item" data-value="default2">Second Default</div>
              </div>
            </div>
            */
            div = document.createElement("DIV");
            div.className = "ui multiple search selection dropdown";
            input = document.createElement("INPUT");
            input.name = "tags";
            input.value = info.tags.tags.join(",");
            input.type = "hidden";
            div.appendChild(input);
            i = document.createElement("I");
            i.className = "dropdown icon";
            div.appendChild(i);
            key = document.createElement("DIV");
            key.className = "default text";
            key.appendChild(document.createTextNode("tags"));
            div.appendChild(key);
            values = document.createElement("DIV");
            values.className = "menu";
            g_known_tags.forEach(function (tag) {
                key = document.createElement("DIV");
                key.className = "item";
                key.dataset.value = tag;
                key.appendChild(document.createTextNode(tag));
                values.appendChild(key);
            });
            div.appendChild(values);
            tag_div.appendChild(div);

            //display a span of inherited tags inline
            info.tags.p_tags.forEach(function (tag) {
                tag_div.appendChild(build_label(tag, "teal", true));
            });
            //attach the row to the table
            target.appendChild(buildKeyValueRow("Tags", tag_div));

            //Activate the selector
            $(div).dropdown({
                allowAdditions: true,
                onChange: tag_change_callback
            });
        }
        if (info.hasOwnProperty("envs")) {
            tag_div = document.createElement("TD");

            div = document.createElement("DIV");
            div.className = "ui search selection dropdown";
            input = document.createElement("INPUT");
            input.name = "env";
            input.value = info.envs.env;
            input.type = "hidden";
            div.appendChild(input);
            i = document.createElement("I");
            i.className = "dropdown icon";
            div.appendChild(i);
            key = document.createElement("DIV");
            key.className = "default text";
            key.appendChild(document.createTextNode("environment"));
            div.appendChild(key);
            values = document.createElement("DIV");
            values.className = "menu";
            g_known_envs.forEach(function (tag) {
                key = document.createElement("DIV");
                key.className = "item";
                key.dataset.value = tag;
                if (tag === "inherit") {
                    key.appendChild(document.createTextNode(tag + " (" + info.envs.p_env + ")"));
                } else {
                    key.appendChild(document.createTextNode(tag));
                }
                values.appendChild(key);
            });
            div.appendChild(values);
            tag_div.appendChild(div);

            target.appendChild(buildKeyValueRow("Environment", tag_div));

            //Activate the selector
            $(div).dropdown({
                allowAdditions: true,
                onChange: env_change_callback
            });
        }
        if (info.hasOwnProperty("in")) {
            key = "Inbound connections";
            values = [info.in.u_ip + " unique source IPs",
                    info.in.u_conn + " unique connections (source and port)",
                    //info.in.total + " total connections",
                    parseFloat(info.in.total / info.in.seconds).toFixed(3) + " connections per second"];
            buildKeyMultiValueRows(key, values).forEach(function (row) {
                target.appendChild(row);
            });
        }
        if (info.hasOwnProperty("out")) {
            key = "Outbound connections";
            values = [info.out.u_ip + " unique destination IPs",
                    info.out.u_conn + " unique connections (destination and port)",
                    //info.out.total + " total connections",
                    parseFloat(info.out.total / info.out.seconds).toFixed(3) + " connections per second"];
            buildKeyMultiValueRows(key, values).forEach(function (row) {
                target.appendChild(row);
            });
        }
        if (info.hasOwnProperty("role")) {
            target.appendChild(buildKeyValueRow("Role (0 = client, 1 = server)", build_role_text(info.role)));
        }
        if (info.hasOwnProperty("ports")) {
            target.appendChild(buildKeyValueRow("Local ports accessed", info.ports));
        }
        if (info.hasOwnProperty("endpoints")) {
            var possible = Math.pow(2, 32 - getIP_Subnet().subnet);
            target.appendChild(buildKeyValueRow("Endpoints represented", info.endpoints + " (of " + possible + " possible)"));
        }
    }
}

function present_detailed_info(info) {
    "use strict";
    if (info === undefined) {
        info = g_data;
    }
    var old_body;
    var new_body;
    if (info.hasOwnProperty("inputs") && info.inputs !== null) {
        // fill headers
        old_body = document.getElementById("conn_in_h");
        new_body = sel_build_table_headers(info.inputs.headers, info.inputs.order, header_sort_callback);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "conn_in_h";
        // fill table
        old_body = document.getElementById("conn_in");
        new_body = sel_build_table_connections(info.inputs.rows);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "conn_in";
        // add paginator
        old_body = document.getElementById("in_pagination");
        new_body = build_pagination(info.inputs.page, info.inputs.page_size, "inputs", g_data.quick.in.u_conn);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "in_pagination";
    }

    if (info.hasOwnProperty("outputs") && info.outputs !== null) {
        // fill headers
        old_body = document.getElementById("conn_out_h");
        new_body = sel_build_table_headers(info.outputs.headers, info.outputs.order, header_sort_callback);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "conn_out_h";
        // fill table
        old_body = document.getElementById("conn_out");
        new_body = sel_build_table_connections(info.outputs.rows);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "conn_out";
        // add paginator
        old_body = document.getElementById("out_pagination");
        new_body = build_pagination(info.outputs.page, info.outputs.page_size, "outputs", g_data.quick.out.u_conn);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "out_pagination";
    }

    if (info.hasOwnProperty("ports") && info.ports !== null) {
        // fill headers
        old_body = document.getElementById("ports_in_h");
        new_body = sel_build_table_headers(info.ports.headers, info.ports.order, header_sort_callback);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "ports_in_h";
        // fill table
        old_body = document.getElementById("ports_in");
        new_body = sel_build_table_ports(info.ports.rows);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "ports_in";
        // add paginator
        old_body = document.getElementById("port_pagination");
        new_body = build_pagination(info.ports.page, info.ports.page_size, "ports", g_data.quick.ports);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "port_pagination";
    }

    if (info.hasOwnProperty("children") && info.children !== null) {
        // fill headers
        old_body = document.getElementById("child_nodes_h");
        new_body = sel_build_table_headers(info.children.headers, info.children.order, header_sort_callback);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "child_nodes_h";
        // fill table
        old_body = document.getElementById("child_nodes");
        new_body = build_table_children(info.children.rows);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "child_nodes";
        // add paginator
        old_body = document.getElementById("child_pagination");
        new_body = build_pagination(info.children.page, info.children.page_size, "children", info.children.count);
        old_body.parentElement.replaceChild(new_body, old_body);
        new_body.id = "child_pagination";
    }

    //enable the tooltips on ports
    $(".popup").popup();
}

/*******************
   AJAX Connection
 *******************/
function onNotLoadData(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("Failed to load data: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}

function ajax_error(x, s, e) {
    console.error("Server error: " + e);
    console.log("\tText Status: " + s);
}

function header_sort_callback(event) {
    "use strict";
    var sortDir = '-';
    if (event.target.classList.contains("descending")) {
        sortDir = '+';
    }
    var newSort = sortDir + event.target.dataset.value;
    var pid = event.target.parentElement.id;
    var component;
    if (pid === "conn_in_h") {
        component = "inputs";
    } else if (pid === "conn_out_h") {
        component = "outputs";
    } else if (pid === "ports_in_h") {
        component = "ports";
    } else if (pid === "child_nodes_h") {
        component = "children";
    } else {
        return;
    }
    var ip = getIP_Subnet().normal;
    console.log("requesting an update: GET_page(ip=" + ip + ", part=" + component + ", page=" + g_data[component].page + ", order=" + newSort);
    GET_page(ip, component, g_data[component].page, newSort);
}

function hostname_edit_callback(event) {
    "use strict";
    if (event.keyCode === 13 || event.type === "blur") {
        var input = event.target;
        var new_name = input.value;
        var old_name = input.dataset.content;
        var ip = getIP_Subnet().normal;

        if (new_name !== old_name) {
            input.dataset.content = new_name;
            var request = {"node": ip, "alias": new_name};
            $.ajax({
                url: "/nodeinfo",
                type: "POST",
                data: request,
                error: ajax_error,
                success: function (r) {
                    if (r.hasOwnProperty("result")) {
                        console.log("Result: " + r.result);
                    }
                }
            });
        }
        return true;
    }
    return false;
}

function tag_change_callback(new_tags) {
    var ip = getIP_Subnet().normal;
    var request = {"node": ip, "tags": new_tags};
    $.ajax({
        url: "/nodeinfo",
        type: "POST",
        data: request,
        error: ajax_error,
        success: function (r) {
            if (r.hasOwnProperty("result")) {
                console.log("Result: " + r.result);
            }
        }
    });
}

function env_change_callback(new_env) {
    var ip = getIP_Subnet().normal;
    if (new_env === "") {
        new_env = "inherit";
    }
    var request = {"node": ip, "env": new_env};
    $.ajax({
        url: "/nodeinfo",
        type: "POST",
        data: request,
        error: ajax_error,
        success: function (r) {
            if (r.hasOwnProperty("result")) {
                console.log("Result: " + r.result);
            }
        }
    });
}

function POST_tags(ip, tags, callback) {
    "use strict";

    var request = {"address": minimizeIP(ip),
            "tags": tags};
    $.ajax({
        url: "/details/" + part,
        type: "GET",
        data: request,
        error: onNotLoadData,
        success: GET_page_callback
    });
}

function GET_data(ip, part, order, callback) {
    "use strict";

    var request = {
        "address": minimizeIP(ip),
        "order": order
    };
    $.ajax({
        url: "/details/" + part,
        type: "GET",
        data: request,
        error: onNotLoadData,
        success: callback
    });
}

function GET_page_callback(response) {
    "use strict";
    Object.keys(response).forEach(function (key) {
        if (response[key].hasOwnProperty("component")) {
            console.log("component is " + response[key].component);
            g_data[response[key].component] = response[key];
            present_detailed_info(g_data);
        }
    });
    scanForPorts(response);
}

function GET_page(ip, part, page, order) {
    "use strict";

    var request = {"address": minimizeIP(ip),
            "page": page,
            "order": order};
    $.ajax({
        url: "/details/" + part,
        type: "GET",
        data: request,
        error: onNotLoadData,
        success: GET_page_callback
    });
}

function abortRequests(requests) {
    "use strict";
    var xhr = requests.pop();
    while (xhr) {
        xhr.abort();
        xhr = requests.pop();
    }
}

/***************************
   Searching state-machine
 ***************************/
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

function scanForPorts(response) {
    "use strict";
    if (response.hasOwnProperty("inputs")) {
        response.inputs.rows.forEach(function (element) {
            ports.request_add(element.port);
        });
    }
    if (response.hasOwnProperty("outputs")) {
        response.outputs.rows.forEach(function (element) {
            ports.request_add(element.port);
        });
    }
    if (response.hasOwnProperty("ports")) {
        response.ports.rows.forEach(function (port) {
            ports.request_add(port.port);
        });
    }
    ports.request_submit(present_detailed_info);
}

function requestMoreDetails(event) {
    "use strict";
    //typing happens:
    //  abortRequests
    //  proceed to restartTypingTimer
    //Info arrives:
    //  proceed to waiting
    var searchbar = document.getElementById("hostSearch");

    if (event.type === "stateChange") {
        //Requesting more details
        var input = searchbar.getElementsByTagName("input")[0];
        console.log("Requesting More Details");

        GET_data(input.value, "inputs,outputs,ports,children", "-links", function (response) {
            // More details arrived
            // Render into browser
            g_data.inputs = response.inputs;
            g_data.outputs = response.outputs;
            g_data.ports = response.ports;
            g_data.children = response.children;
            present_detailed_info(g_data);

            scanForPorts(response);

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

    if (event.type === "stateChange") {
        //Requesting Quick Info
        var input = searchbar.getElementsByTagName("input")[0];
        console.log("Requesting Quick Info");
        searchbar.classList.add("loading");
        present_quick_info({"__order": ["Loading"], Loading: "..."});
        var normalizedIP = normalizeIP(input.value);
        GET_data(normalizedIP, "quick_info", "", function (response) {
            // Quick info arrived
            searchbar.classList.remove("loading");
            // Render into browser
            console.log("BEFORE");
            present_quick_info(response.quick_info);
            console.log("AFTER");
            g_data.quick = response.quick_info;
            if (response.quick_info.hasOwnProperty("error")) {
                console.log("Quick info Arrived. No host found. Back to waiting.");
                //Return to waiting
                dispatcher(new StateChangeEvent(restartTypingTimer));
            } else {
                console.log("Quick info Arrived. Proceeding to Request More Details");
                //Continue to more details
                dispatcher(new StateChangeEvent(requestMoreDetails));
            }

        });
    } else if (event.type === "input") {
        //Aborting requests
        console.log("Aborting Requests");
        abortRequests(g_running_requests);
        searchbar.classList.remove("loading");
        //Clear quickinfo
        present_quick_info({"__order": ["Waiting"], Waiting: "..."});
        //Continue to typing timer
        dispatcher(new StateChangeEvent(restartTypingTimer));
        dispatcher(event);
    }
}

/***************************
       Initialization
 ***************************/
function init() {
    "use strict";
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    input.oninput = dispatcher;
    sel_init();

    // Enable tabbed views
    $(".secondary.menu .item").tab();
    // Enable the port data popup window
    $(".input.icon").popup();
    // Make the ports table sortable
    //$("table.sortable").tablesort();

    //configure ports
    ports.display_callback = present_detailed_info;

    dispatcher(new StateChangeEvent(restartTypingTimer));

    if (g_initial_ip !== "") {
        input.value = g_initial_ip;
        dispatcher(new StateChangeEvent(requestQuickInfo));
    }
}

window.onload = function () {
    "use strict";
    init();
};