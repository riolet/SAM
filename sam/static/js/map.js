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
    "tmin": 1,  // range minimum
    "tmax": 2147483647,  // range maximum
    "tstart": 1,  // window minimum
    "tend": 2147483647,  // window maximum
    "protocol": "all",
    "ds": null,
    "linewidth": "links",
    "flat": false,
    "initial_zoom": false
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
    $(".ui.accordion").accordion();
    $("#settings_menu").dropdown({
        action: updateConfig
    });
    $(".input.icon").popup();

    // for "demo data" message box
    if (window.location.pathname.substr(1,4) === "demo") {
      let msgbox = document.getElementById("demo_msg");
      $(msgbox).transition("fade");
    }
    $('.message .close')
      .on('click', function() {
        $(this)
          .closest('.message')
          .transition('fade');
    });

    //configure ports
    ports.display_callback = function() {
        render_all();
        sel_update_display();
    };

    //retrieve config settings
    GET_settings(null, function (settings) {
        config.update = (settings.datasources[settings.datasource].ar_active === 1);
        config.update_interval = settings.datasources[settings.datasource].ar_interval;
        config.flat = (settings.datasources[settings.datasource].flat === 1);
        config.ds = "ds" + settings.datasource;
        setAutoUpdate();

        GET_timerange(function (range) {
          if (range.min == range.max) {
            config.tmin = range.min - 300;
            config.tmax = range.max;
          } else {
            config.tmin = range.min;
            config.tmax = range.max;
          }
          config.tend = config.tmax;
          config.tstart = config.tmax - 300;
          slider_init(config);
          if (config.flat) {
            nodes.layout = "Circle";
          } else {
            nodes.layout = "Address";
          }
          nodes.GET_request(config.ds, config.flat, null, function (response) {
            resetViewport(nodes.nodes);
            updateRenderRoot();
            render_all();
          });
        });
        init_configbuttons();
    });
}

function init_toggleButton(id, ontext, offtext, isOn) {
    var toggleButton = document.getElementById(id);
    toggleButton.innerHTML = "";
    if (isOn) {
        toggleButton.appendChild(document.createTextNode(ontext));
        toggleButton.classList.add("active");
    } else {
        toggleButton.appendChild(document.createTextNode(offtext));
        toggleButton.classList.remove("active");
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
    init_toggleButton("update", "Auto refresh", "No refresh", config.update);
    init_toggleButton("flat", "Flatten subnets", "Use subnets", config.flat);
    $(".ds.toggle.button").state();
    $(".lw.toggle.button").state();
    document.getElementById("links").classList.add("active");
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

  if (config.flat) {
    let subnet = Math.ceil(5.79621 * Math.log(scale) + 29.5316);
    return Math.max(Math.min(subnet, 32), 0);
  }

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

function removeChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function normalize_addr(addr) {
  "use strict";
  let ip_subnet = addr.split("/");
  let ip = ip_subnet[0];
  let ip_segs = ip.split(".");

  //determine subnet
  let subnet = 0;
  if (ip_subnet.length > 1) {
    subnet = Number(ip_subnet[1]);
  } else {
    subnet = ip_segs.length * 8;
  }

  //determine ip range start
  while (ip_segs.length < 4) {
    ip_segs.push(0);
  }
  addr = ip_segs.join(".");
  return addr + "/" + subnet;
}

// Function(jqXHR jqXHR, String textStatus, String errorThrown)
function generic_ajax_failure(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("Failed to load data: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}

function generic_ajax_success(response) {
    if (response.hasOwnProperty("result")) {
        console.log("Result: " + response.result);
    }
}

function ip_ntos(ip) {
  return Math.floor(ip / 16777216).toString() + "." + (Math.floor(ip / 65536) % 256).toString() + "." + (Math.floor(ip / 256) % 256).toString() + "." + (ip % 256).toString();
}