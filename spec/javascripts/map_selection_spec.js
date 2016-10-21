describe("map_selection.js file", function () {
  describe("sel_init", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("sel_set_selection", function () {
    beforeEach(function () {
      loadednode = {"alias":"","address":"189.58.134","number":134,"subnet":24,"connections":1266,
        "x":250041.609,"y":142444.797,"radius":36,"children":{},"childrenLoaded":false,
        "inputs":[{"source16":256,"x1":327628.812,"links":170,"dest16":58,"dest24":134,
          "y1":-134092.797,"dest8":189,"x2":250034.406,"source24":256,"source8":79,
          "y2":142408.797}],"outputs":[],"ports":{},"server":true,"client":false,
        "details":{"loaded":true,"unique_in":1,"unique_out":0,"unique_ports":1,
          "conn_in":[["79.80.181.189",[{"port":3268,"links":190}]]],"conn_out":[],
          "ports_in":[{"port":3268,"links":190}]}};
      unloadednode = {"alias":"","address":"189.58.134","number":134,"subnet":24,"connections":1266,
        "x":250041.609,"y":142444.797,"radius":36,"children":{},"childrenLoaded":false,
        "inputs":[{"source16":256,"x1":327628.812,"links":170,"dest16":58,"dest24":134,
          "y1":-134092.797,"dest8":189,"x2":250034.406,"source24":256,"source8":79,
          "y2":142408.797}],"outputs":[],"ports":{},"server":true,"client":false,
        "details":{"loaded":false}};
      m_selection['titles'] = document.createElement("div");
      m_selection['titles'].appendChild(document.createElement("h1"));
      spyOn(window, "sel_clear_display");
      spyOn(window, "sel_update_display");
      spyOn(window, "GET_details");
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
      expect(window.GET_details).toHaveBeenCalledTimes(1);
      expect(window.GET_details).toHaveBeenCalledWith(unloadednode, window.sel_update_display);
    });
    it("updates the display", function () {
      sel_set_selection(loadednode);
      sel_set_selection(unloadednode);
      sel_set_selection(null);
      expect(window.sel_update_display).toHaveBeenCalledTimes(2);
    });
  });


  describe("sel_clear_display", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("sel_remove_all", function () {
    beforeEach(function () {
      childnode = {"alias":"","address":"189.58.134","number":134,"subnet":24,"connections":1266,
        "x":250041.609,"y":142444.797,"radius":36,"children":{},"childrenLoaded":false,
        "inputs":[{"source16":256,"x1":327628.812,"links":170,"dest16":58,"dest24":134,
          "y1":-134092.797,"dest8":189,"x2":250034.406,"source24":256,"source8":79,
          "y2":142408.797}],"outputs":[],"ports":{},"server":true,"client":false,
        "details":{"loaded":true,"unique_in":1,"unique_out":0,"unique_ports":1,
          "conn_in":[["79.80.181.189",[{"port":3268,"links":190}]]],"conn_out":[],
          "ports_in":[{"port":3268,"links":190}]}};
      parentnode = {"alias":"","address":"189.58","number":58,"subnet":16,"connections":1266,
        "x":250041.609,"y":142444.797,"radius":36,"children":{},"childrenLoaded":false,
        "inputs":[{"source16":256,"x1":327628.812,"links":170,"dest16":58,"dest24":134,
          "y1":-134092.797,"dest8":189,"x2":250034.406,"source24":256,"source8":79,
          "y2":142408.797}],"outputs":[],"ports":{},"server":true,"client":false,
        "details":{"loaded":true,"unique_in":1,"unique_out":0,"unique_ports":1,
          "conn_in":[["79.80.181.189",[{"port":3268,"links":190}]]],"conn_out":[],
          "ports_in":[{"port":3268,"links":190}]}};
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


  describe("sel_update_display", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("sel_build_title", function () {
    beforeEach(function () {
      loadednode = {"alias":"","address":"189.58.134","number":134,"subnet":24,"connections":1266,
        "x":250041.609,"y":142444.797,"radius":36,"children":{},"childrenLoaded":false,
        "inputs":[{"source16":256,"x1":327628.812,"links":170,"dest16":58,"dest24":134,
          "y1":-134092.797,"dest8":189,"x2":250034.406,"source24":256,"source8":79,
          "y2":142408.797}],"outputs":[],"ports":{},"server":true,"client":false,
        "details":{"loaded":true,"unique_in":1,"unique_out":0,"unique_ports":1,
          "conn_in":[["79.80.181.189",[{"port":3268,"links":190}]]],"conn_out":[],
          "ports_in":[{"port":3268,"links":190}]}};
    });
    it("returns an html entity", function () {
      var result = sel_build_title(loadednode);
      expect(result.nodeName).toBe("DIV");
    });
    it("has an input field for the name", function () {
      var result = sel_build_title(loadednode);
      var name = get_node_name(loadednode);
      title = result.getElementsByTagName("input");
      expect(title.length).toBe(1);
      expect(title[0].value).toBe(name);
    });
    it("shows the node address", function () {
      var result = sel_build_title(loadednode);
      var address = get_node_address(loadednode);
      var s1 = result.innerHTML;
      expect(s1.search(address)).not.toBe(-1);
    });
  });


  describe("sel_build_port_display", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });

    it("returns a text node", function () {
      var test_port = 443;
      var link = sel_build_port_display(test_port);
      expect(link.innerText).toBe(get_port_name(test_port));

      var test_port = 3268;
      var link = sel_build_port_display(test_port);
      expect(link.innerText).toBe(get_port_name(test_port));

      var test_port = 7680;
      var link = sel_build_port_display(test_port);
      expect(link.innerText).toBe(get_port_name(test_port));

      var test_port = 8081;
      var link = sel_build_port_display(test_port);
      expect(link.innerText).toBe(get_port_name(test_port));

      var test_port = 4;
      var link = sel_build_port_display(test_port);
      expect(link.innerText).toBe(get_port_name(test_port));
    });
    it("has an onclick attached", function () {
      var test_port = 3268;
      var link = sel_build_port_display(test_port);
      expect(typeof(link.onclick)).toBe("function");
      var test_port = 4;
      var link = sel_build_port_display(test_port);
      expect(typeof(link.onclick)).toBe("function");
    });
  });


  describe("sel_build_table_connections", function () {
    beforeEach(function () {
      details = {"ports_in": [{"port": 445, "links": 4}, {"port": 139, "links": 2}], "conn_in": [["21.66.134.179", [{"port": 445, "links": 4}, {"port": 139, "links": 2}]]], "unique_ports": 2, "unique_out": 1, "unique_in": 1, "conn_out": [["21.66.1.145", [{"port": 5061, "links": 1}]]]};
    });

    it("returns a tbody element", function () {
      var tbody = sel_build_table_connections(details['conn_in']);
      expect(tbody.nodeName).toBe("TBODY");
      var tbody = sel_build_table_connections(details['conn_out']);
      expect(tbody.nodeName).toBe("TBODY");
      var tbody = sel_build_table_connections([]);
      expect(tbody.nodeName).toBe("TBODY");
    });
  });


  describe("sel_build_table_ports", function () {
    beforeEach(function () {
      details = {"ports_in": [{"port": 445, "links": 4}, {"port": 139, "links": 2}], "conn_in": [["21.66.134.179", [{"port": 445, "links": 4}, {"port": 139, "links": 2}]]], "unique_ports": 2, "unique_out": 1, "unique_in": 1, "conn_out": [["21.66.1.145", [{"port": 5061, "links": 1}]]]};
    });

    it("returns a tbody element", function () {
      var tbody = sel_build_table_ports(details['ports_in']);
      expect(tbody.nodeName).toBe("TBODY");
      var tbody = sel_build_table_ports([]);
      expect(tbody.nodeName).toBe("TBODY");
    });
  });


  describe("sel_build_overflow", function () {
    it("creates normal row", function () {
      var row = sel_build_overflow(100, 3);
      expect(row.nodeName).toBe("TR");
    });
    it("only creates if overflow exists", function () {
      var row = sel_build_overflow(10, 3);
      expect(row.nodeName).toBe("TR");
      var row = sel_build_overflow(1, 3);
      expect(row.nodeName).toBe("TR");
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
});
