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

//settings/options data
var config = {
    "show_clients": true,
    "show_servers": true,
    "show_in": true,
    "show_out": true,
    "update": true,
    "update_interval": 60,
    "filter": "",
    "tstart": 1,
    "tend": 2147483647,
    "protocol": "all",
    "ds": null
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

    filterElement = document.getElementById("proto_filter");
    filterElement.oninput = onProtocolFilter;
    config.protocol = filterElement.value;

    var searchElement = document.getElementById("search");
    searchElement.value = "";
    searchElement.oninput = onsearch;

    sel_panel_height();

    //retrieve config settings
    GET_settings(function (settings) {
        config.update = (settings.datasource.ar_active === 1);
        config.update_interval = settings.datasource.ar_interval;
        config.ds = "ds_" + (settings.datasource.id) + "_"
        init_configbuttons();
	    runUpdate();
    });

    $(".ui.accordion").accordion();
    $("#settings_menu").dropdown({
        action: updateConfig
    });

    $(".input.icon").popup();

    //configure ports
    ports.display_callback = function() {
        render_all();
        sel_update_display();
    };

	  updateCall();
}

function init_toggleButton(id, ontext, offtext, isOn) {
    var toggleButton = document.getElementById(id);
    if (isOn) {
        toggleButton.appendChild(document.createTextNode(ontext));
        toggleButton.classList.add("active");
    } else {
        toggleButton.appendChild(document.createTextNode(offtext));
    }
    $(toggleButton).state({
        text: {
            inactive: offtext,
            active  : ontext
        }
    });
}

function init_configbuttons() {
    init_toggleButton("show_clients", "Clients Shown", "Clients Hidden", config.show_clients);
    init_toggleButton("show_servers", "Servers Shown", "Servers Hidden", config.show_servers);
    init_toggleButton("show_in", "Inbound Shown", "Inbound Hidden", config.show_in);
    init_toggleButton("show_out", "Outbound Shown", "Outbound Hidden", config.show_out);
    init_toggleButton("update", "Auto refresh enabled", "Auto-refresh disabled", config.update);
    $(".ds.toggle.button").state();
    let active_ds = document.getElementById(config.ds);
    active_ds.classList.add("active");
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

function find_by_range(ipstart, ipend) {
    var segments;
    var range = ipend - ipstart;
    if (range === 16777215) {
        segments = 1;
    } else if (range === 65535) {
        segments = 2;
    } else if (range === 255) {
        segments = 3;
    } else if (range === 0) {
        segments = 4;
    } else {
        console.error("invalid ip range? (ipstart=" + ipstart + ", ipend=" + ipend + ")");
    }

    ips = [(ipstart & 0xff000000) >> 24];
    if (ips[0] < 0) {
        ips[0] = 256 + ips[0];
    }

    if (segments > 1) {
        ips[1] = (ipstart & 0xff0000) >> 16;
    } else {
        ips[1] = undefined;
    }
    if (segments > 2) {
        ips[2] = (ipstart & 0xff00) >> 8;
    } else {
        ips[2] = undefined;
    }
    if (segments > 3) {
        ips[3] = (ipstart & 0xff);
    } else {
        ips[3] = undefined;
    }

    return findNode(ips[0], ips[1], ips[2], ips[3]);
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
