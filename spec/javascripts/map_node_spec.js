describe("map_node.js file", function () {
  beforeEach(function () {
    n1 = new Node("bob", "192.168", 168, 24, 1, 1, 1, 10);
  });
  describe("Node", function () {
    it("prepares details for population", function () {
      expect(n1.hasOwnProperty("details")).toEqual(true);
      expect(n1.details.hasOwnProperty("loaded")).toEqual(true);
      expect(n1.details.loaded).toBe(false);
    });
    it("prepares children for population", function () {
      expect(typeof(n1.children)).toEqual("object");
      expect(n1.childrenLoaded).toBe(false);
    });
  });


  describe("get_node_name", function () {
    it("uses name when it can", function () {
      node = new Node("West", "192.168", 168, 16, 0, 0, 0, 0);
      expect(get_node_name(node)).toEqual("West");
    });
    it("uses number when it must", function () {
      node = new Node("", "192.168", 168, 16, 0, 0, 0, 0);
      expect(get_node_name(node)).toEqual("168");
    });
  });


  describe("get_node_address", function () {
    it("returns a dotted decimal string", function () {
      node = new Node("", "192.168.0.17", 17, 32, 9, 123, -123, 500);
      expect(get_node_address(node)).toEqual("192.168.0.17");
    });
    it("displays subnet", function () {
      node = new Node("", "192.168.0.16", 17, 30, 9, 123, -123, 500);
      expect(get_node_address(node)).toEqual("192.168.0.16/30");
    });
    it("right pads with zeroes as needed.", function () {
      node = new Node("", "192.168", 168, 16, 9, 123, -123, 500);
      expect(get_node_address(node)).toEqual("192.168.0.0/16");
      node = new Node("", "192.168.0", 168, 24, 9, 123, -123, 500);
      expect(get_node_address(node)).toEqual("192.168.0.0/24");
      node = new Node("", "192", 192, 8, 9, 123, -123, 500);
      expect(get_node_address(node)).toEqual("192.0.0.0/8");
    });
  });


  describe("set_node_name", function () {
    beforeEach(function () {
      spyOn(window, "POST_node_alias");
      spyOn(window, "render_all");
    });

    it("doesn't run if no change", function () {
      node = new Node("old_name", "192.168", 168, 16, 9, 123, -123, 500);
      set_node_name(node, "old_name");
      expect(window.POST_node_alias).not.toHaveBeenCalled();
    });
    it("runs if change happens", function () {
      var old_name = "old"
      var new_name = "new"
      node = new Node(old_name, "192.168", 168, 16, 9, 123, -123, 500);
      set_node_name(node, new_name);
      expect(window.POST_node_alias).toHaveBeenCalledWith("192.168", new_name);
    });
    it("updates locally", function () {
      var old_name = "old"
      var new_name = "new"
      node = new Node(old_name, "192.168", 168, 16, 9, 123, -123, 500);
      set_node_name(node, new_name);
      expect(window.render_all).toHaveBeenCalled();
      expect(node.alias).toEqual(new_name)
    });
  });


  describe("node_alias_submit", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("node_info_click", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("determine_number", function () {
    it("works with /8", function () {
      node = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192 };
      expect(determine_number(node)).toEqual(192);
    });
    it("works with /16", function () {
      node = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168 };
      expect(determine_number(node)).toEqual(168);
    });
    it("works with /24", function () {
      node = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168, "ip24":0 };
      expect(determine_number(node)).toEqual(0);
    });
    it("works with /32", function () {
      node = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168, "ip24":0, "ip32":7 };
      expect(determine_number(node)).toEqual(7);
    });
  });


  describe("import_node", function () {
    it("/8 imports", function () {
      m_nodes = {};
      node8 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192 };
      import_node(null, node8);
      expect(Object.keys(m_nodes)).toContain("192");
      expect(m_nodes[192].address).toEqual("192");
    });
    it("/16 imports", function () {
      m_nodes = {};
      node8 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192 };
      node16 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168 };
      import_node(null, node8);
      import_node(m_nodes[192], node16);
      expect(Object.keys(m_nodes[192].children)).toContain("168");
      expect(m_nodes[192].children[168].address).toEqual("192.168");
    });
    it("/24 imports", function () {
      m_nodes = {};
      node8 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192 };
      node16 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168 };
      node24 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168, "ip24":0 };
      import_node(null, node8);
      import_node(m_nodes[192], node16);
      import_node(m_nodes[192].children[168], node24);
      expect(Object.keys(m_nodes[192].children[168].children)).toContain("0");
      expect(m_nodes[192].children[168].children[0].address).toEqual("192.168.0");
    });
    it("/32 imports", function () {
      m_nodes = {};
      node8 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192 };
      node16 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168 };
      node24 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
        "ip8":192, "ip16":168, "ip24":0 };
      node32 = { "connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":0,
        "ip8":192, "ip16":168, "ip24":0, "ip32":7 };
      import_node(null, node8);
      import_node(m_nodes[192], node16);
      import_node(m_nodes[192].children[168], node24);
      import_node(m_nodes[192].children[168].children[0], node32);
      expect(Object.keys(m_nodes[192].children[168].children[0].children)).toContain("7");
      expect(m_nodes[192].children[168].children[0].children[7].address).toEqual("192.168.0.7");
    });
  });


  describe("node_update", function () {
    beforeEach(function() {
      m_nodes = {};
      response1 = {
        "192": [{"connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1, "ip8":192}],
      };
      response2 = {
        "192.168":
            [{"connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
              "ip8":192, "ip16":168}]
      };
      response3 = {
        "192.168.0":
            [{"connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":1,
              "ip8":192, "ip16":168, "ip24":0}]
      };
      response4 = {
        "192.168.0.7":
            [{"connections":1, "alias":'', "radius":1, "y":1, "x":1, "children":0,
              "ip8":192, "ip16":168, "ip24":0, "ip32":7}]
      };
      spyOn(window, "link_request_submit");
      spyOn(window, "updateRenderRoot");
      spyOn(window, "render_all");
    });
    it("single import", function () {
      node_update(response1);
      expect(m_nodes.hasOwnProperty("192")).toEqual(true);
    });
    it("/8 /16 import", function () {
      node_update(response1);
      node_update(response2);
      expect(m_nodes.hasOwnProperty("192")).toEqual(true);
      expect(m_nodes['192'].children.hasOwnProperty("168")).toEqual(true);
    });
    it("/8 /16 /24 import", function () {
      node_update(response1);
      node_update(response2);
      node_update(response3);
      expect(m_nodes.hasOwnProperty("192")).toEqual(true);
      expect(m_nodes['192'].children.hasOwnProperty("168")).toEqual(true);
      expect(m_nodes['192'].children['168'].children.hasOwnProperty("0")).toEqual(true);
    });
    it("/8 /16 /24 /32 import", function () {
      node_update(response1);
      node_update(response2);
      node_update(response3);
      node_update(response4);
      expect(m_nodes.hasOwnProperty("192")).toEqual(true);
      expect(m_nodes['192'].children.hasOwnProperty("168")).toEqual(true);
      expect(m_nodes['192'].children['168'].children.hasOwnProperty("0")).toEqual(true);
      expect(m_nodes['192'].children['168'].children['0'].children.hasOwnProperty("7")).toEqual(true);
    });
  });
});
