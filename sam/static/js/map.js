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
    "filter": "",
    "tmin": 1,  // range minimum
    "tmax": 2147483647,  // range maximum
    "tstart": 1,  // window minimum
    "tend": 2147483647,  // window maximum
    "protocol": "all",
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
  let controller = {
    canvas: null,
    ctx: null,
    rect: {},
    datasources: [],
    datasource: {},
    dsid: 0,
    settings: {},
    autorefresh: false,
    autorefresh_period: 0,
    stats_endpoint: "./stats",
    settings_endpoint: "./settings"
  };

  controller.init = function() {
    //get ctx/canvas reference
    //update screen rect reference
    controller.init_window();

    //initialize selection, sidebar, ports, demo plugins
    sel_init();
    map_settings.init();
    //map_settings.add_object(null, null, controller.init_timeslider());
    ports.display_callback = function() {
      render_all();
      sel_update_display();
    };
    controller.init_demo();

    // add ip_search to settings panel
    map_settings.add_object(null, null, map_settings.create_input("search", strings.map_set_search, "search", strings.map_set_search_default, strings.map_set_search_hint, onsearch));
    // add port_filter to settings panel
    map_settings.add_object(null, null, map_settings.create_input("filter", strings.map_set_port, "filter", strings.map_set_port_default, strings.map_set_port_hint, onfilter));
    // add protocol_filter to settings panel
    map_settings.add_object(null, null, map_settings.create_input("proto_filter", strings.map_set_protocol, "exchange", strings.map_set_protocol_default, strings.map_set_protocol_hint, onProtocolFilter));

    // display intermediate menu.
    map_settings.rebuild();

    //get settings && get datasources
    //   add data sources to settings panel
    //   add refresh-enabled to settings panel
    //   get timerange for datasource (start/end time)
    //      create/update timerange slider
    //      trigger the get-node sequence
    controller.GET_settings(null, function (result) {
      let btn_list = []

      // auto-refresh button
      map_settings.add_object(strings.map_set_ds, null, map_settings.btn_toggleable(map_settings.create_iconbutton("autorefresh", "refresh", strings.map_set_ds_ar_hint, controller.autorefresh, null), controller.event_auto_refresh));
      // datasource buttons
      controller.datasources.forEach(function (ds) {
        btn_list.push(map_settings.create_labeliconbutton("ds_"+ds.id, "database", ds.name, strings.map_set_ds_hint1 + ds.name + strings.map_set_ds_hint2, ds.id==controller.dsid, null));
      });
      map_settings.add_object(strings.map_set_ds, null, map_settings.create_divider());
      map_settings.add_object(strings.map_set_ds, null, map_settings.create_buttongroup(btn_list, "vertical labeled icon", controller.event_datasource));

      controller.GET_timerange(controller.dsid, function (result) {
        nodes.set_datasource(controller.datasource);
        controller.init_buttons(nodes.layout_flat, nodes.layout_arrangement);

        nodes.GET_request(null, function (response) {
          resetViewport(nodes.nodes);
          updateRenderRoot();
          render_all();
        });
        map_settings.rebuild();
      });
    });
  };

  controller.init_buttons = function (isFlat, layout) {
    let btn_list;
    //(id, icon_name, tooltip, active, callback)

    btn_list = [
      map_settings.create_labelbutton("lw_links", strings.map_set_lw_lc, strings.map_set_lw_lc_hint, true, null),
      map_settings.create_labelbutton("lw_bytes", strings.map_set_lw_bc, strings.map_set_lw_bc_hint, false, null),
      map_settings.create_labelbutton("lw_packets", strings.map_set_lw_pc, strings.map_set_lw_pc_hint, false, null)
    ];
    map_settings.add_object(strings.map_set_lw, null, map_settings.create_buttongroup(btn_list, "vertical", controller.event_line_width));

    map_settings.add_object(strings.map_set_vis, null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_clients", "desktop", strings.map_set_vis_c, true, null), controller.event_show_buttons));
    map_settings.add_object(strings.map_set_vis, null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_servers", "server", strings.map_set_vis_s, true, null), controller.event_show_buttons));
    map_settings.add_object(strings.map_set_vis, null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_inputs", "sign in", strings.map_set_vis_i, true, null), controller.event_show_buttons));
    map_settings.add_object(strings.map_set_vis, null, map_settings.btn_toggleable(map_settings.create_iconbutton("show_outputs", "sign out", strings.map_set_vis_o, true, null), controller.event_show_buttons));

    btn_list = [
      map_settings.create_iconbutton("lm_Heirarchy", "cube", strings.map_set_lay_m_use, !isFlat, null),
      map_settings.create_iconbutton("lm_Flat", "cubes", strings.map_set_lay_m_flat, isFlat, null)
    ];
    map_settings.add_object(strings.map_set_lay, strings.map_set_lay_m, map_settings.create_buttongroup(btn_list, "icon", controller.event_layout_mode));

    btn_list = [
      map_settings.create_iconbutton("la_Address", "qrcode", strings.map_set_lay_a_add, layout=="Address", null),
      map_settings.create_iconbutton("la_Grid", "table", strings.map_set_lay_a_grid, layout=="Grid", null),
      map_settings.create_iconbutton("la_Circle", "maximize", strings.map_set_lay_a_circle, layout=="Circle", null)
    ];
    map_settings.add_object(strings.map_set_lay, strings.map_set_lay_a, map_settings.create_buttongroup(btn_list, "icon", controller.event_layout_arrangement));
  };

  controller.init_demo = function () {
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

  controller.init_window = function () {
    controller.canvas = document.getElementById("canvas");
    controller.ctx = controller.canvas.getContext("2d");

    let navBarHeight = $("#navbar").height();
    $("#output").css("top", navBarHeight);
    controller.canvas.width = window.innerWidth;
    controller.canvas.height = window.innerHeight - navBarHeight;
    controller.ctx.lineJoin = "bevel";
    controller.rect = controller.canvas.getBoundingClientRect();

    tx = controller.rect.width / 2;
    ty = controller.rect.height / 2;

    //Event listeners for detecting clicks and zooms
    let pusher = document.getElementsByClassName("pusher")[0];
    pusher.addEventListener("mousedown", mousedown);
    pusher.addEventListener("mousemove", mousemove);
    pusher.addEventListener("mouseup", mouseup);
    pusher.addEventListener("mouseout", mouseup);
    pusher.addEventListener("wheel", wheel);
    pusher.addEventListener("keydown", keydown, false);
  };

  controller.GET_settings = function (ds, successCallback) {
    if (typeof(successCallback) !== "function") {
        return;
    }
    let request = $.ajax({
      url: controller.settings_endpoint,
      type: "GET",
      data: {"headless": 1},
      dataType: "json",
      error: generic_ajax_failure,
      success: response_builder(controller.import_settings, successCallback)
    });

    return request;
  };

  controller.import_settings = function (settings) {
    controller.settings = settings;
    controller.datasources = [];
    Object.keys(settings.datasources).forEach( function (key) {
      controller.datasources.push(settings.datasources[key]);
    });
    controller.datasource = settings.datasources[settings.datasource];
    controller.dsid = settings.datasource;

    controller.autorefresh = (controller.datasource.ar_active === 1);
    controller.autorefresh_period = controller.datasource.ar_interval;
    setAutoUpdate();
  }

  controller.GET_timerange = function (ds, successCallback) {
    let request = $.ajax({
      url: controller.stats_endpoint,
      type: "GET",
      data: {"q": "timerange", 'ds': ds},
      dataType: "json",
      error: generic_ajax_failure,
      success: response_builder(controller.import_timerange, successCallback)
    });

    return request;
  };

  controller.import_timerange = function(range) {
    if (range.min >= range.max) {
      config.tmin = range.min - 300;
      config.tmax = range.max;
    } else {
      config.tmin = range.min;
      config.tmax = range.max;
    }
    config.tend = config.tmax;
    config.tstart = config.tmax - 300;
    slider_init();
  }

  controller.event_to_tag = function (event, tagName) {
    let element = event.target;
    while (element && element.tagName !== tagName) {
      element = element.parentElement;
    }
    return element;
  };

  controller.event_datasource = function (e_ds) {
    //determine which datasource (ds) buttons are clicked.
    let element = controller.event_to_tag(e_ds, "BUTTON");
    let old_ds = controller.dsid;
    let new_ds = parseInt(element.id.substr(3));
    
    if (new_ds !== old_ds) {
      controller.dsid = new_ds;
      let i;
      for(i=0; i < controller.datasources.length; i += 1) {
        if (controller.datasources[i].id === new_ds) {
          controller.datasource = controller.datasources[i];
          break;
        }
      }
      link_remove_all(nodes.nodes);
      config.initial_zoom = false;
      controller.autorefresh = (controller.datasource.ar_active === 1);
      controller.autorefresh_period = controller.datasource.ar_interval;
      let ar_btn = document.getElementById("autorefresh");
      if (controller.autorefresh) {
        ar_btn.classList.add("active");
      } else {
        ar_btn.classList.remove("active");
      }
      nodes.set_flat(controller.datasources.flat === 1);
      setAutoUpdate();
      updateCall();
    }
  }

  controller.event_auto_refresh = function (e_auto_refresh) {
    let button = controller.event_to_tag(e_auto_refresh, "BUTTON");
    let active = button.classList.contains("active");
    controller.autorefresh = active;
    setAutoUpdate();
  }

  controller.event_line_width = function (e_lines_btn) {
    let element = controller.event_to_tag(e_lines_btn, "BUTTON");
    if (!element) { return; }
    var oldLW = renderConfig.linewidth;
    var newLW = element.id.substr(3);
    
    if (newLW !== oldLW) {
      // do special stuff
      renderConfig.linewidth = newLW;
      render_all();
    }
  };

  controller.event_show_buttons = function (e_show_btn) {
    let element = controller.event_to_tag(e_show_btn, "BUTTON");
    if (!element) { return; }
    if (renderConfig.hasOwnProperty(element.id)) {
      renderConfig[element.id] = element.classList.contains("active");
    }
    updateRenderRoot();
    render_all();
  };

  controller.event_layout_mode = function (e_lm_btn) {
    // Event: layout mode (flat/heirarchical) button clicked.
    let element = controller.event_to_tag(e_lm_btn, "BUTTON");
    if (!element) { return; }
    
    let new_flat = element.id.substr(3) === "Flat";
    let old_flat = nodes.layout_flat;
    if (new_flat !== old_flat) {
      if (m_link_timer) {
        clearTimeout(m_link_timer);
      }
      nodes.set_flat(new_flat);
      nodes.GET_request(null, function (response) {
        resetViewport(nodes.nodes);
        updateRenderRoot();
        render_all();
      });
    }
  };

  controller.event_layout_arrangement = function (e_la_btn) {
    let element = controller.event_to_tag(e_la_btn, "BUTTON");
    if (!element) { return; }

    let new_layout = element.id.substr(3);
    let old_layout = nodes.layout_arrangement;
    if (new_layout !== old_layout) {
      nodes.set_layout(new_layout);
      resetViewport(nodes.nodes);
      updateRenderRoot();
      render_all();
    }
  };

  window.controller = controller;
}());

// map_settings
(function () {
  "use strict";
  let map = {};
  map.structure = {objects: [], children: {}};

  map.reset = function () {
    map.structure = {objects: [], children: {}};
  };

  map.clear_html = function (accordion) {
    accordion.innerHTML = "";
  };

  map.make_html = function (parent, structure) {
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

      map.make_html(contentDiv, cat);

      parent.appendChild(titleDiv);
      parent.appendChild(contentDiv);
    });
  };

  map.init_accordion = function (accordion) {
    $(accordion).accordion({
      exclusive: false,
      animateChildren: false
    });
  };

  map.rebuild = function () {
    let accordion = document.getElementById("mapconfig");
    map.clear_html(accordion);
    map.make_html(accordion, map.structure);
    map.init_accordion(accordion);
  };

  map.add_category = function (cat) {
    if (map.structure.children.hasOwnProperty(cat)) {
      return;
    }
    map.structure.children[cat] = {objects: [], children: {}};
  };

  map.add_subcategory = function (cat, subcat) {
    if (!map.structure.children.hasOwnProperty(cat)) {
      map.add_category(cat);
    }
    if (map.structure.children[cat].children.hasOwnProperty(subcat)) {
      return;
    }
    map.structure.children[cat].children[subcat] = {objects: [], children: {}};
  };

  map.add_object = function (cat, subcat, obj) {
    if (cat) {
      if (!map.structure.children.hasOwnProperty(cat)) {
        map.add_category(cat);
      }
      if (subcat) {
        if (!map.structure.children[cat].children.hasOwnProperty(subcat)) {
          map.add_subcategory(cat, subcat);
        }
        map.structure.children[cat].children[subcat].objects.push(obj);
      } else {
        map.structure.children[cat].objects.push(obj);
      }
    } else if (subcat) {
      if (!map.structure.children.hasOwnProperty(subcat)) {
        map.add_category(subcat);
        map.structure.children[subcat].objects.push(obj);
      }
    } else {
      map.structure.objects.push(obj);
    }
  };

  map.create_labeliconbutton = function (id, icon_name, label, tooltip, active, callback) {
    //create button
    let btn = document.createElement("BUTTON");
    btn.className = "ui icon inverted blue button";
    if (active) {
      btn.classList.add("active");
    }
    if (id) {
      btn.id = id;
    }
    // .dataset[...] is for the tooltip.
    btn.dataset["tooltip"] = tooltip;
    btn.dataset["inverted"] = "true";
    btn.dataset["position"] = "top left";
    btn.dataset["delay"] = "500";

    let icon = document.createElement("I");
    icon.className = icon_name + " icon";
    btn.appendChild(icon);
    btn.appendChild(document.createTextNode(label));
    if (typeof(callback) === "function") {
      btn.onclick = callback;
    }

    return btn;
  };

  map.create_iconbutton = function (id, icon_name, tooltip, active, callback) {
    //create button
    let btn = document.createElement("BUTTON");
    btn.className = "ui icon inverted blue button";
    if (active) {
      btn.classList.add("active");
    }
    if (id) {
      btn.id = id;
    }
    // .dataset[...] is for the tooltip.
    btn.dataset["tooltip"] = tooltip;
    btn.dataset["inverted"] = "true";
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

  map.create_labelbutton = function (id, label, tooltip, active, callback) {
    //create button
    let btn = document.createElement("BUTTON");
    btn.className = "ui inverted blue button";
    if (active) {
      btn.classList.add("active");
    }
    if (id) {
      btn.id = id;
    }
    // .dataset[...] is for the tooltip.
    btn.dataset["tooltip"] = tooltip;
    btn.dataset["inverted"] = "true";
    btn.dataset["position"] = "top left";
    btn.dataset["delay"] = "500";

    btn.appendChild(document.createTextNode(label));

    if (typeof(callback) === "function") {
      btn.onclick = callback;
    }

    return btn;
  };

  map.create_divider = function () {
    //<div class="divider"></div>
    let div = document.createElement("DIV");
    div.className = "divider";
    return div;
  }

  map.btn_toggleable = function (btn, callback) {
    btn.onclick = function (e_click) {
      btn.classList.toggle('active');
      if (typeof(callback) === "function") {
        callback(e_click);
      }
    };

    return btn;
  };

  map.create_buttongroup = function (btnlist, css_classes, callback) {
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

  map.create_input = function (id, label_text, icon_name, placeholder, tooltip, callback) {
    let outer_div = document.createElement("DIV");
    let div = document.createElement("DIV");
    let icon = document.createElement("I");
    let label = document.createElement("LABEL");
    let input = document.createElement("INPUT");

    outer_div.className = "textinput";
    div.className = "ui inverted fluid icon input";
    label.appendChild(document.createTextNode(label_text));
    label.className = "configlabel";
    label.htmlFor = id;
    input.id = id;
    input.placeholder = placeholder;
    input.type="text";
    if (typeof(callback) == "function") {
      input.oninput = callback;
    }
    icon.className = icon_name + " icon";

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

  map.init = function () {
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
  window.map_settings = map;
}());

function init() {
  controller.init();
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

function get_view_center(viewrect, x, y, scale) {
  let center = {
    x: ((viewrect.width / 2) - x) / (scale),
    y: ((viewrect.height / 2) - y) / (scale)
  };
  return center;
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
    "use strict";
    if (response.hasOwnProperty("result")) {
        console.log("Result: " + response.result);
    }
}

function ip_ntos(ip) {
  return Math.floor(ip / 16777216).toString() + "." + (Math.floor(ip / 65536) % 256).toString() + "." + (Math.floor(ip / 256) % 256).toString() + "." + (ip % 256).toString();
}

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

function response_builder(method, extra_callback) {
  callback = function (response) {
    method(response);
    if (typeof(extra_callback) === "function") {
      extra_callback(response);
    }
  }
  return callback;
}
