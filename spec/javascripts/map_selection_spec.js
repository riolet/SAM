function get_loadednode() {
  loadednode = {
    "alias":"",
    "address":"189.58.134.0",
    "ipstart":3174729216,
    "ipend":3174729471,
    "subnet":24,
    "abs_x":348846.88785769616,
    "abs_y":210204.1784277373,
    "rel_x":-122.1880517890354,
    "rel_y":40.72935059634517,
    "radius":36,
    "radius_orig":36,
    "parent":null,
    "children":{},
    "childrenLoaded":true,
    "inputs":[],
    "outputs":[],
    "ports":{},
    "server":true,
    "client":false,
    "details":{
      "loaded":true,
      "unique_in":2,
      "unique_out":0,
      "unique_ports":3,
      "inputs":{
        "direction":"desc",
        "rows":[["79.80.181.189",3268,"36.00"],["79.80.0.189",443,"0.40"],["79.80.181.189",389,"0.40"],["79.80.0.189",389,"0.20"]],
        "component":"inputs",
        "page_size":50,
        "order":"-links",
        "headers":[["src","Source IP"],["port","Dest. Port"],["links","Count / Min"]],
        "page":1},
      "outputs":{
        "direction":"desc",
        "rows":[],
        "component":"outputs",
        "page_size":50,
        "order":"-links",
        "headers":[["dst","Dest. IP"],["port","Dest. Port"],["links","Count / Min"]],
        "page":1},
      "ports":{
        "rows":[[3268,"36.00"],[389,"0.60"],[443,"0.40"]],
        "component":"ports",
        "page_size":50,
        "order":"-links",
        "headers":[["port","Port Accessed"],["links","Count / Min"]],"page":1
      }
    }
  };
  return loadednode;
}
function get_unloadednode() {
  unloadednode = {
    "alias":"",
    "address":"79.64.243.81",
    "ipstart":1329656657,
    "ipend":1329656657,
    "subnet":32,
    "abs_x":454150.92676827166,
    "abs_y":-225201.06472856653,
    "rel_x":-22.061731573020282,
    "rel_y":-8.485281374238571,
    "radius":1.5,
    "radius_orig":1.5,
    "parent":null,
    "children":{},
    "childrenLoaded":false,
    "inputs":[],
    "outputs":[],
    "ports":{},
    "server":false,
    "client":true,
    "details":{
      "loaded":false
    }
  };
  return unloadednode;
}
function get_dom() {
  dom = "<div id=\"sel_bar\">\
    <div id=\"sel_titles\">\
      <h4>No selection</h4>\
      <h5>&nbsp;</h5>\
    </div>\
    <div id=\"selectionInfo\" class=\"ui styled fluid accordion\">\
      <div class=\"title\">\
        <i class=\"dropdown icon\"></i>\
        Unique inbound clients: <span id=\"unique_in\">0</span>\
      </div>\
      <div class=\"content\">\
        <div class=\"transition hidden\">\
          <table class=\"ui very compact sortable celled structured table\">\
            <thead>\
            <tr id=\"conn_in_h\">\
              <th>Source IP</th>\
              <th>Dest. Port</th>\
              <th>Count</th>\
            </tr>\
            </thead>\
            <tbody id=\"conn_in\"></tbody>\
            <tfoot class=\"full-width\" id=\"conn_in_overflow\"></tfoot>\
          </table>\
        </div>\
      </div>\
      <div class=\"title\">\
        <i class=\"dropdown icon\"></i>\
        Unique servers contacted: <span id=\"unique_out\">0</span>\
      </div>\
      <div class=\"content\">\
        <div class=\"transition hidden\">\
          <table class=\"ui very compact sortable celled structured table\">\
            <thead>\
              <tr id=\"conn_out_h\">\
                <th>Dest. IP</th>\
                <th>Dest. Port</th>\
                <th>Count</th>\
              </tr>\
            </thead>\
            <tbody id=\"conn_out\"></tbody>\
            <tfoot class=\"full-width\" id=\"conn_out_overflow\"></tfoot>\
          </table>\
        </div>\
      </div>\
      <div class=\"title\">\
        <i class=\"dropdown icon\"></i>\
        Unique ports accessed: <span id=\"unique_ports\">0</span>\
      </div>\
      <div class=\"content\">\
        <div class=\"transition hidden\">\
          <table class=\"ui very compact sortable celled table\">\
            <thead>\
              <tr id=\"ports_in_h\">\
                <th>Port Accessed</th>\
                <th class=\"sorted descending\">Occurrences</th>\
              </tr>\
            </thead>\
            <tbody id=\"ports_in\"></tbody>\
            <tfoot class=\"full-width\" id=\"ports_in_overflow\"></tfoot>\
          </table>\
        </div>\
      </div>\
    </div>\
    <div id=\"sel_link\" class=\"bottom attached ui segment\" style=\"display: none\"></div>\
  </div>";
  div = document.createElement("div");
  div.innerHTML = dom;
  return div;
}

describe("map_selection.js file", function () {
  beforeEach(function () {
    dom = get_dom();
    //window.appendChild(dom.outerHTML);
    document.getElementById = function (id) {
      return dom.querySelector("#" + id);
    }
  });
  
  describe("sel_init", function () {
    beforeEach(function () {
      spyOn(window, "sel_panel_height");
    });
    it("assigns properties to m_selection", function () {
      sel_init();
      expect(m_selection.hasOwnProperty("selection")).toBe(true);
      expect(m_selection.hasOwnProperty("sidebar")).toBe(true);
      expect(m_selection.hasOwnProperty("titles")).toBe(true);
      expect(m_selection.hasOwnProperty("unique_in")).toBe(true);
      expect(m_selection.hasOwnProperty("unique_out")).toBe(true);
      expect(m_selection.hasOwnProperty("unique_ports")).toBe(true);
      expect(m_selection.hasOwnProperty("conn_in")).toBe(true);
      expect(m_selection.hasOwnProperty("conn_out")).toBe(true);
      expect(m_selection.hasOwnProperty("ports_in")).toBe(true);
      expect(window.sel_panel_height).toHaveBeenCalled();
    });
  });

  //no branches or loops to test, skipped
  xdescribe("sel_clear_display", function () {});

  describe("sel_set_selection", function () {
    beforeEach(function () {
      loadednode = get_loadednode();
      unloadednode = get_unloadednode();
      sel_init();
      spyOn(window, "sel_clear_display");
      spyOn(window, "sel_update_display");
      spyOn(window, "sel_GET_details");
    });

    it("clears the existing data", function () {
      sel_set_selection(loadednode);
      sel_set_selection(unloadednode);
      sel_set_selection(null);
      expect(window.sel_clear_display).toHaveBeenCalledTimes(3);
    });
    it("assigns the selection variable", function () {
      sel_set_selection(loadednode);
      expect(m_selection['selection']).toEqual(loadednode);
      sel_set_selection(unloadednode);
      expect(m_selection['selection']).toEqual(unloadednode);
      sel_set_selection(null);
      expect(m_selection['selection']).toEqual(null);
    });
    it("tries to load missing data", function () {
      sel_set_selection(loadednode);
      sel_set_selection(unloadednode);
      sel_set_selection(null);
      expect(window.sel_GET_details).toHaveBeenCalledTimes(1);
      expect(window.sel_GET_details).toHaveBeenCalledWith(unloadednode, window.sel_update_display);
    });
    it("updates the display", function () {
      sel_set_selection(loadednode);
      sel_set_selection(unloadednode);
      sel_set_selection(null);
      expect(window.sel_update_display).toHaveBeenCalledTimes(2);
    });
  });

  describe("sel_remove_all", function () {
    beforeEach(function () {
      childnode = {
        "address":"189.58.134",
        "children":{},
        "childrenLoaded":false,
        "details":{
          "loaded":true,
          "unique_in":1,
          "unique_out":0,
          "unique_ports":1,
          "conn_in":[["79.80.181.189",[{"port":3268,"links":190}]]],
          "conn_out":[],
          "ports_in":[{"port":3268,"links":190}]
        }
      };
      parentnode = {
        "address":"189.58", 
        "children":{},
        "childrenLoaded":false,
        "details":{
          "loaded":true,
          "unique_in":1,
          "unique_out":0,
          "unique_ports":1,
          "conn_in":[["79.80.181.189",[{"port":3268,"links":190}]]],
          "conn_out":[],
          "ports_in":[{"port":3268,"links":190}]
        }
      };
    });

    it("clears elements", function () {
      expect(childnode.details.loaded).toBe(true);
      expect(parentnode.details.loaded).toBe(true);

      flat_collection = {"58": parentnode, '134': childnode};
      sel_remove_all(flat_collection);

      expect(childnode.details.loaded).toBe(false);
      expect(parentnode.details.loaded).toBe(false);
    });
    it("clears nested elements", function () {
      expect(childnode.details.loaded).toBe(true);
      expect(parentnode.details.loaded).toBe(true);

      parentnode.children['134'] = childnode;
      collection = {"58": parentnode};
      sel_remove_all(collection);

      expect(childnode.details.loaded).toBe(false);
      expect(parentnode.details.loaded).toBe(false);
    });
  });

  //no branches or loops to test, can skip
  describe("sel_build_title", function () {
    beforeEach(function () {
      loadednode = get_loadednode();
    });
    it("returns an html entity", function () {
      var result = sel_build_title(loadednode);
      expect(result.nodeName).toBe("DIV");
    });
    it("has an input field for the name", function () {
      var result = sel_build_title(loadednode);
      var name = nodes.get_name(loadednode);
      title = result.getElementsByTagName("input");
      expect(title.length).toBe(1);
      expect(title[0].value).toBe(name);
    });
    it("shows the node address", function () {
      var result = sel_build_title(loadednode);
      var address = nodes.get_address(loadednode);
      var s1 = result.innerHTML;
      expect(s1.search(address)).not.toBe(-1);
    });
  });

  describe("sel_build_table", function () {
    it("returns a tbody element with full elements", function () {
      let headers = [["dst","Dest. IP"],["port","Dest. Port"],["links","Count / Min"]];
      let dataset = [["189.158.26.26",389,"0.40"],["189.10.111.245",389,"0.20"],["189.10.175.216",389,"0.20"],["189.10.26.224",389,"0.20"],["189.10.26.224",445,"0.20"],["189.10.101.216",389,"0.20"]];

      var tbody = sel_build_table(headers, dataset)
      expect(tbody.tagName).toBe("TBODY");
      expect(tbody.childNodes.length).toEqual(6);
    });
    it("returns a tbody element with partial elements", function () {
      let headers = [["port","Port Accessed"],["links","Count / Min"]];
      let dataset = [];

      var tbody = sel_build_table(headers, dataset)
      expect(tbody.tagName).toBe("TBODY");
      expect(tbody.childNodes.length).toEqual(0);
    });
  });

  describe("sel_build_table_headers", function () {
    beforeEach(function () {
      headers = [["src","Source IP"],["port","Dest. Port"],["links","Count / Min"]];
      order = "-links";
    });

    it("returns a tbody element", function () {
      var tbody = sel_build_table_headers(headers, order);
      expect(tbody.tagName).toBe("TR");
      var tbody = sel_build_table_headers(headers);
      expect(tbody.tagName).toBe("TR");
    });
  });

  describe("sel_build_overflow", function () {
    it("creates normal row", function () {
      var row = sel_build_overflow(100, 3);
      expect(row.tagName).toBe("TR");
    });
    it("only creates if overflow exists", function () {
      var row = sel_build_overflow(10, 3);
      expect(row.tagName).toBe("TR");
      var row = sel_build_overflow(1, 3);
      expect(row.tagName).toBe("TR");
      var row = sel_build_overflow(0, 3);
      expect(row).not.toBeDefined();
    });
    it("matches columns requests", function () {
      var row = sel_build_overflow(10, 3);
      var columns = 0;
      var i = 0;
      for(; i<row.children.length; i += 1) {
        columns += row.children[i].colSpan;
      }
      expect(columns).toBe(3);

      row = sel_build_overflow(10, 30);
      columns = 0;
      i = 0;
      for(; i<row.children.length; i += 1) {
        columns += row.children[i].colSpan;
      }
      expect(columns).toBe(30);

      row = sel_build_overflow(10, 1);
      columns = 0;
      i = 0;
      for(; i<row.children.length; i += 1) {
        columns += row.children[i].colSpan;
      }
      expect(columns).toBe(1);
    });
  });

  describe("build_label_bytes", function () {
    it("bytes", function () {
      let b = build_label_bytes(9999);
      expect(b).toEqual("9999 B");
      b = build_label_bytes(10000);
      expect(b).toEqual("10 KB");
      b = build_label_bytes(100000);
      expect(b).toEqual("98 KB");
      b = build_label_bytes(1000000);
      expect(b).toEqual("977 KB");
      b = build_label_bytes(10000000);
      expect(b).toEqual("9766 KB");
      b = build_label_bytes(1000000000);
      expect(b).toEqual("954 MB");
      b = build_label_bytes(100000000000);
      expect(b).toEqual("93 GB");
      b = build_label_bytes(10000000000000);
      expect(b).toEqual("9313 GB");
      b = build_label_bytes(1000000000000000);
      expect(b).toEqual("909 TB");
    });
  });

  describe("build_label_datarate", function () {
    it("bps", function () {
      let b = build_label_datarate(9999);
      expect(b).toEqual("9.76 KB/s");
      b = build_label_datarate(10000);
      expect(b).toEqual("9.77 KB/s");
      b = build_label_datarate(100000);
      expect(b).toEqual("97.66 KB/s");
      b = build_label_datarate(1000000);
      expect(b).toEqual("976.56 KB/s");
      b = build_label_datarate(10000000);
      expect(b).toEqual("9.54 MB/s");
      b = build_label_datarate(1000000000);
      expect(b).toEqual("953.67 MB/s");
      b = build_label_datarate(100000000000);
      expect(b).toEqual("93.13 GB/s");
      b = build_label_datarate(10000000000000);
      expect(b).toEqual("9313.23 GB/s");
      b = build_label_datarate(1000000000000000);
      expect(b).toEqual("931322.57 GB/s");
    });
  });

  describe("build_label_duration", function () {
    it("time", function () {
      let b = build_label_duration(10);
      expect(b).toEqual("10 seconds");
      b = build_label_duration(100);
      expect(b).toEqual("100 seconds");
      b = build_label_duration(1000);
      expect(b).toEqual("17 minutes");
      b = build_label_duration(10000);
      expect(b).toEqual("3 hours");
      b = build_label_duration(100000);
      expect(b).toEqual("28 hours");
      b = build_label_duration(1000000);
      expect(b).toEqual("12 days");
      b = build_label_duration(10000000);
      expect(b).toEqual("17 weeks");
    });
  });

  // bad candidate for unit testing
  xdescribe("sel_panel_height", function () {});

  describe("sel_create_link", function () {
    it("returns a link", function () {
      let node = get_loadednode();
      controller.dsid = 6;
      let anchor = sel_create_link(node);
      expect(anchor.tagName).toEqual("A");
      expect(anchor.href.endsWith("/metadata#ip=189.58.134.0/24&ds=6")).toBe(true);
    });
  });

  // bad candidate for unit testing
  xdescribe("sel_details_sort_callback", function () {});

  // bad candidate for unit testing
  xdescribe("sel_update_display", function () {});
});
