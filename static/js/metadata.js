var g_typing_timer = null;
var g_running_requests = [];
var g_state = null;
var g_data = {"quick": null, "inputs": null, "outputs": null, "ports": null};

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
    if (event.type === "input") {
        console.log("Aborting Requests");
        abortRequests(g_running_requests);
        dispatcher(new StateChangeEvent(restartTypingTimer));
    } else if (event.type == "stateChange") {
        console.log("Requesting More Details");
        setTimeout(function () {
            console.log("More Details Arrived. Returning to waiting.");
        }, 2000);
    }
}

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

function requestBasicInfo(event) {
    "use strict";
    //typing happens:
    //  abortRequests
    //  proceed to restartTypingTimer
    //Info arrives:
    //  proceed to requestMoreDetails()
    var searchbar = document.getElementById("hostSearch");
    var target = document.getElementById("quickinfo");

    if (event.type === "input") {
        console.log("Aborting Requests");
        abortRequests(g_running_requests);
        searchbar.classList.remove("loading");
        target.innerHTML = "";
        target.appendChild(buildKeyValueRow("Waiting", "..."));
        dispatcher(new StateChangeEvent(restartTypingTimer));
    } else if (event.type == "stateChange") {
        console.log("Requesting Basic Info");
        searchbar.classList.add("loading");
        target.innerHTML = "";
        target.appendChild(buildKeyValueRow("Loading", "..."));
        g_running_requests.push(setTimeout(function () {
            var input = searchbar.getElementsByTagName("input")[0];
            target.innerHTML = "";
            target.appendChild(buildKeyValueRow("Basic Info", "Arrived"));
            console.log("Basic Info Arrived. Proceeding to Request More Details");
            searchbar.classList.remove("loading");
            dispatcher(new StateChangeEvent(requestMoreDetails));
        }, 2000));
    }
}

function restartTypingTimer() {
    "use strict";
    //typing happens:
    //  restart the timer
    //timer times out:
    //  advance to request basic info
    console.log("Restarting Timer");
    if (g_typing_timer !== null) {
        clearTimeout(g_typing_timer);
    }
    g_typing_timer = setTimeout(function () {
        console.log("Proceeding to Request Basic Info");
        dispatcher(new StateChangeEvent(requestBasicInfo));
    }, 700);
}

function tabActivated(tabName) {
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    console.log("Activating " + tabName);
    GET_data(input.value, tabName, function (response) {
        console.log("Tab data received: ")
        Object.keys(response).forEach(function (key) {
            console.log("\t"+key+" "+response[key].toString());
        });
    });
}

function init() {
    "use strict";
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    input.oninput = dispatcher;

    // enable tabbed views
    $('.secondary.menu .item').tab({
        onLoad: tabActivated
    });
}

window.onload = function () {
    "use strict";
    init();
    g_state = restartTypingTimer;
};