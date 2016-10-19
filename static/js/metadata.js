var g_typing_timer = null;
var g_running_requests = [];
var g_state = null;

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
    } else {
        console.log("Requesting More Details");
        setTimeout(function () {
            console.log("More Details Arrived. Returning to waiting.");
        }, 2000);
    }
}

function requestBasicInfo(event) {
    "use strict";
    //typing happens:
    //  abortRequests
    //  proceed to restartTypingTimer
    //Info arrives:
    //  proceed to requestMoreDetails()
    var searchbar = document.getElementById("hostSearch");
    searchbar.classList.add("loading");

    if (event.type === "input") {
        console.log("Aborting Requests");
        abortRequests(g_running_requests);
        searchbar.classList.remove("loading");
        dispatcher(new StateChangeEvent(restartTypingTimer));
    } else {
        console.log("Requesting Basic Info");
        g_running_requests.push(setTimeout(function () {
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

function init() {
    "use strict";
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    input.oninput = dispatcher;
}

window.onload = function () {
    "use strict";
    init();
    g_state = restartTypingTimer;
};