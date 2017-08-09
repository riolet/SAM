describe("map_node.js file", function () {
  describe("Node", function () {
    beforeEach(function () {
      n1 = new Node("bob", "192.168", 168, 24, 1, 1, 1, 10);
    });
    it("prepares details member", function () {
      expect(n1.hasOwnProperty("details")).toEqual(true);
      expect(n1.details.hasOwnProperty("loaded")).toEqual(true);
      expect(n1.details.loaded).toBe(false);
    });
    it("prepares children member", function () {
      expect(typeof(n1.children)).toEqual("object");
      expect(n1.childrenLoaded).toBe(false);
    });
  });

  describe("find_by_addr", function () {
    beforeEach(function () {
      nodes.nodes = get_mock_node_tree();
    });

    it("can find addresses", function () {
      let n = nodes.find_by_addr("110");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.0.0.0");

      n = nodes.find_by_addr("110.145");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.0.0");
      
      n = nodes.find_by_addr("110.145.200");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.0");

      n = nodes.find_by_addr("110.145.200.79");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.79");
    });

    it("works with subnets", function () {
      let n = nodes.find_by_addr("110/8");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.0.0.0");
      n = nodes.find_by_addr("110.0/8");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.0.0.0");
      n = nodes.find_by_addr("110.0.0/8");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.0.0.0");
      n = nodes.find_by_addr("110.0.0.0/8");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.0.0.0");

      n = nodes.find_by_addr("110.145/16");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.0.0");
      n = nodes.find_by_addr("110.145.0/16");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.0.0");
      n = nodes.find_by_addr("110.145.0.0/16");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.0.0");
      
      n = nodes.find_by_addr("110.145.200/24");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.0");
      n = nodes.find_by_addr("110.145.200.0/24");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.0");

      n = nodes.find_by_addr("110.145.200.79/32");
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.79");
    });
  });

  describe("find_by_range", function () {
    beforeEach(function () {
      nodes.nodes = get_mock_node_tree();
    });

    it("finds nodes", function () {
      let n = nodes.find_by_range(1845493760, 1862270975);
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.0.0.0");

      n = nodes.find_by_range(1854996480, 1855062015);
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.0.0");

      n = nodes.find_by_range(1855047680, 1855047935);
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.0");

      n = nodes.find_by_range(1855047759, 1855047759);
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.79");
    });

    it("finds nearest node when missing", function () {
      let n = nodes.find_by_range(1855062016, 1855127551);
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.0.0.0");

      n = nodes.find_by_range(1855047936, 1855048191);
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.0.0");

      n = nodes.find_by_range(1855047760, 1855047760);
      expect(n).not.toBeNull();
      expect(n.address).toEqual("110.145.200.0");
    });

    it("returns null when nothing available", function () {
      let n = nodes.find_by_range(2147483648, 2164260863)
      expect(n).toBeNull();
    });
  });

  describe("find_common_root", function () {
    beforeEach(function () {
      nodes.nodes = get_mock_node_tree();
    });

    it("finds parents", function () {
      let nodeA = nodes.find_by_addr("110.145.200.77");
      let nodeB = nodes.find_by_addr("110.145.216.179");
      let nodeC = nodes.find_by_addr("110.145.200.146");
      let parent;
      parent = nodes.find_common_root(nodeA, nodeB);
      expect(parent.address).toEqual("110.145.0.0")
      parent = nodes.find_common_root(nodeA, nodeC);
      expect(parent.address).toEqual("110.145.200.0")
      parent = nodes.find_common_root(nodeB, nodeC);
      expect(parent.address).toEqual("110.145.0.0")
    })
  });

  describe("insert", function () {
    beforeEach(function () {
      nodes.nodes = get_mock_node_tree();
    });

    it("works in normal case", function () {
      let n = nodes.find_by_addr("136.164");
      expect(n.address).toEqual("136.0.0.0");
      let record = {
        "subnet":16,
        "ipstart":2292449280,
        "ipend":2292514815,
        "alias":null,
        "radius":864,
        "env":null,
        "y":29030.4,
        "x":12441.6
      };
      let flat = false;
      nodes.insert(record, flat);
      n = nodes.find_by_addr("136.164");
      expect(n.address).toEqual("136.164.0.0");
    });
  });

  describe("GET_response", function () {
    it("works in the root case", function () {
      let root_response = {"_":[
        {"subnet":8,"ipstart":352321536,"ipend":369098751,"alias":null,"radius":20736,"env":null,"y":-287539.188,"x":-110592},
        {"subnet":8,"ipstart":889192448,"ipend":905969663,"alias":null,"radius":20736,"env":null,"y":-199065.594,"x":-110592},
        {"subnet":8,"ipstart":1325400064,"ipend":1342177279,"alias":null,"radius":20736,"env":null,"y":-154828.797,"x":331776},
        {"subnet":8,"ipstart":1845493760,"ipend":1862270975,"alias":null,"radius":20736,"env":null,"y":-66355.203,"x":287539.188},
        {"subnet":8,"ipstart":2030043136,"ipend":2046820351,"alias":null,"radius":20736,"env":null,"y":-22118.4,"x":66355.203},
        {"subnet":8,"ipstart":2281701376,"ipend":2298478591,"alias":null,"radius":20736,"env":null,"y":22118.4,"x":22118.4},
        {"subnet":8,"ipstart":3170893824,"ipend":3187671039,"alias":null,"radius":20736,"env":null,"y":154828.797,"x":243302.406},
        {"subnet":8,"ipstart":3489660928,"ipend":3506438143,"alias":null,"radius":20736,"env":null,"y":243302.406,"x":-331776}]};
      nodes.nodes = {};
      nodes.GET_response(root_response);
      let expected = ["1325400064","1845493760","2030043136","2281701376","3170893824","3489660928","352321536","889192448"];
      let real = Object.keys(nodes.nodes).sort();
      expect(real).toEqual(expected);
    });

    it("works in the child case", function () {
      nodes.nodes = get_mock_node_tree();
      let response = {"136.0.0.0/8":[{"subnet":16,"ipstart":2292449280,"ipend":2292514815,"alias":null,"radius":864,"env":null,"y":29030.4,"x":12441.6}]};
      let n = nodes.find_by_addr("136.164");
      expect(n.address).toEqual("136.0.0.0");
      nodes.GET_response(response);
      n = nodes.find_by_addr("136.164");
      expect(n.address).toEqual("136.164.0.0");
    });
  });

  describe("determine_number", function () {
    it("/8", function () {
      let n = nodes.find_by_addr("110");
      expect(nodes.determine_number(n)).toEqual(110);
    });
    it("/16", function () {
      let n = nodes.find_by_addr("110.145");
      expect(nodes.determine_number(n)).toEqual(145);
    });
    it("/24", function () {
      let n = nodes.find_by_addr("110.145.200");
      expect(nodes.determine_number(n)).toEqual(200);
    });
    it("/32", function () {
      let n = nodes.find_by_addr("110.145.200.79");
      expect(nodes.determine_number(n)).toEqual(79);
    });
  });

  describe("port_to_pos", function () {
    it("matches correctly", function () {
      let n = {"abs_x": 970, "abs_y": 50, "radius": 15};
      expect(nodes.port_to_pos(n, 't-l')).toEqual([965, 29]);
      expect(nodes.port_to_pos(n, 't-r')).toEqual([975, 29]);
      expect(nodes.port_to_pos(n, 'b-l')).toEqual([965, 71]);
      expect(nodes.port_to_pos(n, 'b-r')).toEqual([975, 71]);
      expect(nodes.port_to_pos(n, 'l-t')).toEqual([949, 45]);
      expect(nodes.port_to_pos(n, 'l-b')).toEqual([949, 55]);
      expect(nodes.port_to_pos(n, 'r-t')).toEqual([991, 45]);
      expect(nodes.port_to_pos(n, 'r-b')).toEqual([991, 55]);
    });
  });

  describe("nearest_corner", function() {
    it("matches corners", function() {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15};
      expect(nodes.nearest_corner(n, 400, 30)).toEqual([485, 35]);
      expect(nodes.nearest_corner(n, 400, 50)).toEqual([485, 65]);
      expect(nodes.nearest_corner(n, 400, 70)).toEqual([485, 65]);
      expect(nodes.nearest_corner(n, 500, 30)).toEqual([515, 35]);
      expect(nodes.nearest_corner(n, 500, 50)).toEqual([515, 65]);
      expect(nodes.nearest_corner(n, 500, 70)).toEqual([515, 65]);
      expect(nodes.nearest_corner(n, 600, 30)).toEqual([515, 35]);
      expect(nodes.nearest_corner(n, 600, 50)).toEqual([515, 65]);
      expect(nodes.nearest_corner(n, 600, 70)).toEqual([515, 65]);
    });
  });

  describe("delta_to_dest", function () {
    it("follows normal path", function () {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15};
      expect(nodes.delta_to_dest(n, 400, 30)).toEqual([485, 53]);
      expect(nodes.delta_to_dest(n, 400, 50)).toEqual([485, 53]);
      expect(nodes.delta_to_dest(n, 400, 70)).toEqual([485, 53]);
      expect(nodes.delta_to_dest(n, 500, 30)).toEqual([497, 35]);
      expect(nodes.delta_to_dest(n, 500, 50)).toEqual([497, 35]);
      expect(nodes.delta_to_dest(n, 500, 70)).toEqual([503, 65]);
      expect(nodes.delta_to_dest(n, 600, 30)).toEqual([515, 47]);
      expect(nodes.delta_to_dest(n, 600, 50)).toEqual([515, 47]);
      expect(nodes.delta_to_dest(n, 600, 70)).toEqual([515, 47]);
    });
  });

  describe("delta_to_src", function () {
    it("follows normal path", function () {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15};
      expect(nodes.delta_to_src(n, 400, 30)).toEqual([485, 47]);
      expect(nodes.delta_to_src(n, 400, 50)).toEqual([485, 47]);
      expect(nodes.delta_to_src(n, 400, 70)).toEqual([485, 47]);
      expect(nodes.delta_to_src(n, 500, 30)).toEqual([503, 35]);
      expect(nodes.delta_to_src(n, 500, 50)).toEqual([503, 35]);
      expect(nodes.delta_to_src(n, 500, 70)).toEqual([497, 65]);
      expect(nodes.delta_to_src(n, 600, 30)).toEqual([515, 53]);
      expect(nodes.delta_to_src(n, 600, 50)).toEqual([515, 53]);
      expect(nodes.delta_to_src(n, 600, 70)).toEqual([515, 53]);
    });
  });

  describe("get_inbound_link_point", function () {

  });
});
