var canvas;
var ctx;
var rect; //render region on screen

//global transform coordinates, with initial values
var tx = 0;
var ty = 0;
var g_scale = 0.0007;

//mouse interaction variables
var ismdown = false;
var mdownx;
var mdowny;
var mx;
var my;

//store the data displayed in the map
var renderCollection = [];
var subnetLabel = "";

// Timing variables
var MILLIS_PER_MIN = 60000;
var MINS_PER_UPDATE   = 5;

//settings/options data
var config = {
    "show_clients": true,
    "show_servers": true,
    "show_in": true,
    "show_out": true,
    "filter": "",
    "tstart": 1,
    "tend": 2147483647
};

//Constants.  Used for zoom levels in map::currentSubnet and map_render::opacity
var zNodes16 = 0.00231;
var zLinks16 = 0.0111;
var zNodes24 = 0.0555;
var zLinks24 = 0.267;
var zNodes32 = 1.333;
var zLinks32 = 6.667;
//max number of link requests to make at once, in link_request_submit()
var g_chunkSize = 40;

//for filtering and searching
var g_timer = null;

function init() {
    "use strict";
    canvas = document.getElementById("canvas");
    ctx = canvas.getContext("2d");
    init_canvas(canvas, ctx);

    rect = canvas.getBoundingClientRect();
    tx = rect.width / 2;
    ty = rect.height / 2;

    window.addEventListener("keydown", keydown, false);

    sel_init();

    var filterElement = document.getElementById("filter");
    filterElement.oninput = onfilter;
    config.filter = filterElement.value;

    var searchElement = document.getElementById("search");
    searchElement.value = "";
    searchElement.oninput = onsearch;

    updateFloatingPanel();

    document.getElementById("show_clients").checked = config.show_clients;
    document.getElementById("show_servers").checked = config.show_servers;
    document.getElementById("show_in").checked = config.show_in;
    document.getElementById("show_out").checked = config.show_out;

    $(".ui.accordion").accordion();
    $(".ui.dropdown").dropdown({
        action: updateConfig
    });
    $(".input.icon").popup();
    $("table.sortable").tablesort();

    //loadData();
    GET_nodes(null);

	window.setInterval(function(){GET_nodes(null);},Math.abs(MILLIS_PER_MIN * MINS_PER_UPDATE));
	
}

function init_canvas(c, cx) {
    var navBarHeight = $("#navbar").height();
    $("#output").css("top", navBarHeight);
    c.width = window.innerWidth;
    c.height = window.innerHeight - navBarHeight;
    cx.lineJoin = "bevel";

    //Event listeners for detecting clicks and zooms
    c.addEventListener("mousedown", mousedown);
    c.addEventListener("mousemove", mousemove);
    c.addEventListener("mouseup", mouseup);
    c.addEventListener("mouseout", mouseup);
    c.addEventListener("wheel", wheel);
}

function currentSubnet(scale) {
    "use strict";
    if (scale < zNodes16) {
        return 8;
    }
    if (scale < zNodes24) {
        return 16;
    }
    if (scale < zNodes32) {
        return 24;
    }
    return 32;
}

function findNode(ip8, ip16, ip24, ip32) {
    "use strict";
    if (typeof ip8 === "string") {
        var ips = ip8.split(".");
        if (ips.length == 1) {
            ip8 = Number(ips[0]);
        } else if (ips.length == 2) {
            ip8 = Number(ips[0]);
            ip16 = Number(ips[1]);
        } else if (ips.length == 3) {
            ip8 = Number(ips[0]);
            ip16 = Number(ips[1]);
            ip24 = Number(ips[2]);
        } else if (ips.length == 4) {
            ip8 = Number(ips[0]);
            ip16 = Number(ips[1]);
            ip24 = Number(ips[2]);
            ip32 = Number(ips[3]);
        }
    }
    if (ip8 === undefined) {
        ip8 = -1;
    }
    if (ip16 === undefined) {
        ip16 = -1;
    }
    if (ip24 === undefined) {
        ip24 = -1;
    }
    if (ip32 === undefined) {
        ip32 = -1;
    }

    if (m_nodes.hasOwnProperty(ip8)) {
        if (m_nodes[ip8].children.hasOwnProperty(ip16)) {
            if (m_nodes[ip8].children[ip16].children.hasOwnProperty(ip24)) {
                if (m_nodes[ip8].children[ip16].children[ip24].children.hasOwnProperty(ip32)) {
                    return m_nodes[ip8].children[ip16].children[ip24].children[ip32];
                } else {
                    return m_nodes[ip8].children[ip16].children[ip24];
                }
            } else {
                return m_nodes[ip8].children[ip16];
            }
        } else {
            return m_nodes[ip8];
        }
    } else {
        return null;
    }
}

function removeChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}
