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

// controller
(function () {
  "use strict";
  let self = {
    canvas: null,
    ctx: null,
    rect: {},
    datasources: [],
    settings: {},
    autorefresh: false,
    autorefresh_period: 0,
    stats_endpoint: "./stats",
    settings_endpoint: "./settings"
  };

  self.init = function() {
    console.log("self", "init");
    //get ctx/canvas reference
    //update screen rect reference
    self.init_window();

    //initialize selection, sidebar, ports, demo plugins
    sel_init();
    map_settings.init();
    //map_settings.add_object(null, null, self.init_timeslider());

    ports.display_callback = function() {
        render_all();
        sel_update_display();
    };
    self.init_demo();

    // add ip_search to settings panel
    map_settings.add_object(null, null, map_settings.create_input("search", "Search", "search", "Find IP...", "Find an IP address. e.g. 192.168.0.12", onsearch));
    // add port_filter to settings panel
    map_settings.add_object(null, null, map_settings.create_input("filter", "Port Filter", "filter", "Filter by port...", "Filter by port number. Try: 80", onfilter));
    // add protocol_filter to settings panel
    map_settings.add_object(null, null, map_settings.create_input("proto_filter", "Protocol Filter", "exchange", "Filter by protocol...", "Filter by protocol. Try: UDP", onProtocolFilter));
    // auto-refresh
    map_settings.add_object("Datasources", null, map_settings.btn_toggleable(map_settings.create_iconbutton("autorefresh", "refresh", "Autorefresh the node map", false, null), cb));

    // display intermediate menu.
    map_settings.rebuild();

    //get settings && get datasources
    //   add data sources to settings panel
    //   add refresh-enabled to settings panel
    //   get timerange for datasource (start/end time)
    //      create/update timerange slider
    //      trigger the get-node sequence
    self.GET_settings(null, function (result) {
      console.log("self", "init", "get_settings is 'done'");
      let btn_list = []
      self.datasources.forEach(function (ds) {
        btn_list.push(map_settings.create_iconbutton("ds"+ds.datasource, "database", ds.name, ds.id==self.ds, cb));
      });
      map_settings.add_object("Datasources", null, map_settings.create_buttongroup(btn_list, cb));

      self.GET_timerange(self.ds, function (result) {
        console.log("self", "init", "get_timerange is 'done'");
        console.log("self.datasource is ", self.datasource);
        nodes.set_datasource(self.datasource);
        self.init_buttons(nodes.layout_flat, nodes.layout_arrangement);

        nodes.GET_request(null, function (response) {
          resetViewport(nodes.nodes);
          updateRenderRoot();
          render_all();
        });
        map_settings.rebuild();
      });
    });
  };

  self.init_buttons = function (isFlat, layout) {
    let btn_list;
    //(id, icon_name, tooltip, active, callback)

    btn_list = [
      map_settings.create_iconbutton(null, "area chart", "Number of Occurrences", true, cb),
      map_settings.create_iconbutton(null, "bar chart", "Bytes Transferred", false, cb),
      map_settings.create_iconbutton(null, "line chart", "Packets Transmitted", false, cb)
    ];
    map_settings.add_object("Line width represents", null, map_settings.create_buttongroup(btn_list, "icon", cb));

    map_settings.add_object("Show/Hide", null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_clients", "desktop", "Show Pure Clients", config.show_clients, null), cb));
    map_settings.add_object("Show/Hide", null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_servers", "server", "Show Pure Servers", config.show_servers, null), cb));
    map_settings.add_object("Show/Hide", null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_in", "sign in", "Show Inbound Connections", config.show_in, null), cb));
    map_settings.add_object("Show/Hide", null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_out", "sign out", "Show Outbound Connections", config.show_out, null), cb));

    btn_list = [
      map_settings.create_iconbutton("lm_Heirarchy", "cube", "Use Heirarchy", !isFlat, cb),
      map_settings.create_iconbutton("lm_Flat", "cubes", "Flatten Heirarchy", isFlat, cb)
    ];
    map_settings.add_object("Layout", "mode", map_settings.create_buttongroup(btn_list, "icon", cb));

    btn_list = [
      map_settings.create_iconbutton("la_Address", "qrcode", "Address", layout=="la_Address", cb),
      map_settings.create_iconbutton("la_Grid", "table", "Grid", layout=="la_Grid", cb),
      map_settings.create_iconbutton("la_Circle", "maximize", "Circle", layout=="la_Circle", cb)
    ];
    map_settings.add_object("Layout", "arrangement", map_settings.create_buttongroup(btn_list, "icon", cb));
  };

  self.init_demo = function () {
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
  };

  self.init_window = function () {
    self.canvas = document.getElementById("canvas");
    self.ctx = self.canvas.getContext("2d");

    let navBarHeight = $("#navbar").height();
    $("#output").css("top", navBarHeight);
    self.canvas.width = window.innerWidth;
    self.canvas.height = window.innerHeight - navBarHeight;
    self.ctx.lineJoin = "bevel";
    self.rect = self.canvas.getBoundingClientRect();

    tx = self.rect.width / 2;
    ty = self.rect.height / 2;

    //Event listeners for detecting clicks and zooms
    /*
    self.canvas.addEventListener("mousedown", mousedown);
    self.canvas.addEventListener("mousemove", mousemove);
    self.canvas.addEventListener("mouseup", mouseup);
    self.canvas.addEventListener("mouseout", mouseup);
    self.canvas.addEventListener("wheel", wheel);
    */
    let pusher = document.getElementsByClassName("pusher")[0];
    pusher.addEventListener("mousedown", mousedown);
    pusher.addEventListener("mousemove", mousemove);
    pusher.addEventListener("mouseup", mouseup);
    pusher.addEventListener("mouseout", mouseup);
    pusher.addEventListener("wheel", wheel);

    window.addEventListener("keydown", keydown, false);
  };

  self.GET_settings = function (ds, successCallback) {
    console.log("self", "GET_settings");
    if (typeof(successCallback) !== "function") {
        return;
    }
    let request = $.ajax({
      url: self.settings_endpoint,
      type: "GET",
      data: {"headless": 1},
      dataType: "json",
      error: generic_ajax_failure,
      success: function (settings) {
        console.log("self", "GET_settings", "response");
        console.log("Settings received: ", settings);
        self.settings = settings;
        self.datasources = []
        Object.keys(settings.datasources).forEach( function (key) {
          self.datasources.push(settings.datasources[key]);
        });
        self.datasource = settings.datasources[settings.datasource];
        self.ds = settings.datasource;

        self.autorefresh = (self.datasource.ar_active === 1);
        self.autorefresh_period = self.datasource.ar_interval;
        setAutoUpdate();

        if (typeof(successCallback) == "function") {
          successCallback(settings);
        }
      }
    });

    return request;
  };

  self.GET_timerange = function (ds, successCallback) {
    console.log("self", "GET_timerange");
    let request = $.ajax({
      url: self.stats_endpoint,
      type: "GET",
      data: {"q": "timerange", 'ds': ds},
      dataType: "json",
      error: generic_ajax_failure,
      success: function (range) {
        console.log("self", "GET_timerange", "response");
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

        if (typeof(successCallback) == "function") {
          successCallback(range);
        }
      }
    });

    return request;
  };

  window.controller = self;
}());

// map_settings
(function () {
  "use strict";
  let self = {};
  self.structure = {objects: [], children: {}};

  self.reset = function () {
    self.structure = {objects: [], children: {}};
  };

  self.clear_html = function (accordion) {
    accordion.innerHTML = "";
  };

  self.make_html = function (parent, structure) {
    structure.objects.forEach( function (item) {
      parent.appendChild(item);
    });

    Object.keys(structure.children).forEach(function (key) {
      let cat = structure.children[key];

      let titleDiv = document.createElement("DIV");
      titleDiv.className = "title"
      let ddi = document.createElement("I");
      ddi.className = "dropdown icon";
      titleDiv.appendChild(ddi);
      titleDiv.appendChild(document.createTextNode(key));
      let contentDiv = document.createElement("DIV");
      contentDiv.className = "content";

      self.make_html(contentDiv, cat);

      parent.appendChild(titleDiv);
      parent.appendChild(contentDiv);
    });
  };

  self.init_accordion = function (accordion) {
    $(accordion).accordion({
      exclusive: false,
      animateChildren: false
    });
  };

  self.rebuild = function () {
    let accordion = document.getElementById("mapconfig");
    self.clear_html(accordion);
    self.make_html(accordion, self.structure);
    self.init_accordion(accordion);
  };

  self.add_category = function (cat) {
    if (self.structure.children.hasOwnProperty(cat)) {
      return;
    }
    self.structure.children[cat] = {objects: [], children: {}};
  };

  self.add_subcategory = function (cat, subcat) {
    if (!self.structure.children.hasOwnProperty(cat)) {
      self.add_category(cat);
    }
    if (self.structure.children[cat].children.hasOwnProperty(subcat)) {
      return;
    }
    self.structure.children[cat].children[subcat] = {objects: [], children: {}};
  };

  self.add_object = function (cat, subcat, obj) {
    if (cat) {
      if (!self.structure.children.hasOwnProperty(cat)) {
        self.add_category(cat);
      }
      if (subcat) {
        if (!self.structure.children[cat].children.hasOwnProperty(subcat)) {
          self.add_subcategory(cat, subcat);
        }
        self.structure.children[cat].children[subcat].objects.push(obj);
      } else {
        self.structure.children[cat].objects.push(obj);
      }
    } else {
      self.structure.objects.push(obj);
    }
  };

  self.create_iconbutton = function (id, icon_name, tooltip, active, callback) {
    //create button
    let btn = document.createElement("BUTTON");
    btn.className = "ui icon inverted button";
    if (active) {
      btn.classList.add("active");
    }
    if (id) {
      btn.id = id;
    }
    // .dataset[...] is for the tooltip.
    btn.dataset["tooltip"] = tooltip;
    btn.dataset["inverted"] = true;
    btn.dataset["position"] = "top left";
    btn.dataset["delay"] = "500";

    let icon = document.createElement("I");
    icon.className = icon_name + " icon";
    btn.appendChild(icon);
    if (typeof(callback) === "function") {
      btn.onclick = callback;
    }

    return btn;
  };

  self.btn_toggleable = function (btn, callback) {
    btn.onclick = function (e_click) {
      btn.classList.toggle('active');
      if (typeof(callback) === "function") {
        callback(e_click);
      }
    };

    return btn;
  };

  self.create_buttongroup = function (btnlist, css_classes, callback) {
    let group = document.createElement("DIV");
    group.className = "ui buttons " + css_classes;

    let handler = {
      activate: function(e_click) {
        $(this)
          .addClass('active')
          .siblings()
          .removeClass('active')
        ;
        if (typeof(callback) === "function") {
          callback(e_click);
        }
      }
    }

    btnlist.forEach(function (item) {
      item.onclick = handler.activate;
      group.appendChild(item);
    });

    return group;
  };

  self.create_input = function (id, label_text, icon_name, placeholder, tooltip, callback) {
    let outer_div = document.createElement("DIV");
    let div = document.createElement("DIV");
    let icon = document.createElement("I");
    let label = document.createElement("LABEL");
    let input = document.createElement("INPUT");

    outer_div.className = "textinput";
    div.className = "ui inverted fluid icon input";
    label.appendChild(document.createTextNode(label_text));
    label.classList = "configlabel";
    label.htmlFor = id;
    input.id = id;
    input.placeholder = placeholder;
    input.type="text";
    if (typeof(callback) == "function") {
      input.oninput = callback;
    }
    icon.classList = icon_name + " icon";

    div.dataset["tooltip"] = tooltip;
    div.dataset["inverted"] = true;
    div.dataset["position"] = "top left";
    div.dataset["delay"] = "500";

    div.appendChild(input);
    div.appendChild(icon);
    outer_div.appendChild(label);
    outer_div.appendChild(div);

    return outer_div;
  };

  self.init = function () {
    //sidebar init
    $('.ui.sidebarholder .ui.sidebar')
      .sidebar({
        context: $('.ui.sidebarholder'),
        dimPage: false,
        closable: false,
        transition: 'push'
      })
      .sidebar('attach events', '.drawer-toggle')
    ;
  };

  //install layout
  window.map_settings = self;
}());

function init() {
  controller.init();
}

function cb(param) {
  console.log("Clicked!", param);
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