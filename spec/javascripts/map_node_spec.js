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
    it("lines up to existing ports", function () {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 32, "ports": {123: "t-l", 456: "r-b"}};
      expect(nodes.get_inbound_link_point(n, 400, 30, 123)).toEqual(nodes.port_to_pos(n, "t-l"));
      expect(nodes.get_inbound_link_point(n, 400, 30, 456)).toEqual(nodes.port_to_pos(n, "r-b"));
    });
    it("uses normal connection points when subnet is not 32", function () {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 8, ports: {}};
      let x = 400;
      let y = 30;
      let port = 123;
      expect(nodes.get_inbound_link_point(n, x, y, port)).toEqual(nodes.delta_to_dest(n, x, y));
      n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 16, ports: {}};
      x = 800;
      y = 30;
      expect(nodes.get_inbound_link_point(n, x, y, port)).toEqual(nodes.delta_to_dest(n, x, y));
      n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 24, ports: {}};
      x = 800;
      y = 90;
      expect(nodes.get_inbound_link_point(n, x, y, port)).toEqual(nodes.delta_to_dest(n, x, y));
      n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 32, ports: {}};
      x = 400;
      y = 90;
      expect(nodes.get_inbound_link_point(n, x, y, port)).not.toEqual(nodes.delta_to_dest(n, x, y));
    });
    it("picks a corner if subnet is 32 but no port match", function () {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 32, "ports": {123: "t-l", 456: "r-b"}};
      let x = 400;
      let y = 30;
      let port = 80;
      expect(nodes.get_inbound_link_point(n, x, y, port)).toEqual(nodes.nearest_corner(n, x, y));
      port = 123;
      expect(nodes.get_inbound_link_point(n, x, y, port)).not.toEqual(nodes.nearest_corner(n, x, y));
      x = 600;
      y = 70;
      port = 443;
      expect(nodes.get_inbound_link_point(n, x, y, port)).toEqual(nodes.nearest_corner(n, x, y));
      port = 456;
      expect(nodes.get_inbound_link_point(n, x, y, port)).not.toEqual(nodes.nearest_corner(n, x, y));
    });
  });

  describe("get_outbound_link_point", function () {
    it("uses normal connection points when subnet is not 32", function () {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 8, ports: {}};
      let x = 400;
      let y = 30;
      let port = 123;
      expect(nodes.get_outbound_link_point(n, x, y, port)).toEqual(nodes.delta_to_src(n, x, y));
      n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 16, ports: {}};
      x = 800;
      y = 30;
      expect(nodes.get_outbound_link_point(n, x, y, port)).toEqual(nodes.delta_to_src(n, x, y));
      n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 24, ports: {}};
      x = 800;
      y = 90;
      expect(nodes.get_outbound_link_point(n, x, y, port)).toEqual(nodes.delta_to_src(n, x, y));
      n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 32, ports: {}};
      x = 400;
      y = 90;
      expect(nodes.get_outbound_link_point(n, x, y, port)).not.toEqual(nodes.delta_to_src(n, x, y));
    });
    it("picks a corner if subnet is 32", function () {
      let n = {"abs_x": 500, "abs_y": 50, "radius": 15, "subnet": 32, "ports": {123: "t-l", 456: "r-b"}};
      let x = 400;
      let y = 30;
      let port = 80;
      expect(nodes.get_outbound_link_point(n, x, y, port)).toEqual(nodes.nearest_corner(n, x, y));
      port = 123;
      expect(nodes.get_outbound_link_point(n, x, y, port)).toEqual(nodes.nearest_corner(n, x, y));
      x = 600;
      y = 70;
      port = 443;
      expect(nodes.get_outbound_link_point(n, x, y, port)).toEqual(nodes.nearest_corner(n, x, y));
      port = 456;
      expect(nodes.get_outbound_link_point(n, x, y, port)).toEqual(nodes.nearest_corner(n, x, y));
    });
  });

  describe("update_pos_tree", function () {
    beforeEach(function () {
      a = {address: "10.0.0.0", subnet: 8, children: {}, rel_x: 1000, rel_y: 1};
      b = {address: "10.20.0.0", subnet: 16, children: {}, rel_x: 100, rel_y: 2};
      c = {address: "10.20.30.0", subnet: 24, children: {}, rel_x: 10, rel_y: 4};
      d = {address: "10.20.30.40", subnet: 32, children: {}, rel_x: 1, rel_y: 8};
      a.children[169082880] = b;
      b.children[169090560] = c;
      c.children[169090600] = d;
      b.parent = a;
      c.parent = b;
      d.parent = c;
    });
    it("calculates absolute pos, cascading", function () {
      nodes.update_pos_tree(a, null);
      expect(a.abs_x).toEqual(1000);
      expect(a.abs_y).toEqual(1);
      expect(b.abs_x).toEqual(1100);
      expect(b.abs_y).toEqual(3);
      expect(c.abs_x).toEqual(1110);
      expect(c.abs_y).toEqual(7);
      expect(d.abs_x).toEqual(1111);
      expect(d.abs_y).toEqual(15);
    });
  });

  describe("set_relative_pos", function () {
    beforeEach(function () {
      a = {address: "10.0.0.0", subnet: 8, children: {}, rel_x: 1000, rel_y: 1};
      b = {address: "10.20.0.0", subnet: 16, children: {}, rel_x: 100, rel_y: 2};
      c = {address: "10.20.30.0", subnet: 24, children: {}, rel_x: 10, rel_y: 4};
      d = {address: "10.20.30.40", subnet: 32, children: {}, rel_x: 1, rel_y: 8};
      a.children[169082880] = b;
      b.children[169090560] = c;
      c.children[169090600] = d;
      b.parent = a;
      c.parent = b;
      d.parent = c;
    });
    it("cascades", function () {
      nodes.set_relative_pos(a, 2000, 17);
      expect(a.abs_x).toEqual(2000);
      expect(a.abs_y).toEqual(17);
      expect(b.abs_x).toEqual(2100);
      expect(b.abs_y).toEqual(19);
      expect(c.abs_x).toEqual(2110);
      expect(c.abs_y).toEqual(23);
      expect(d.abs_x).toEqual(2111);
      expect(d.abs_y).toEqual(31);
    });
  });

  describe("get_name", function () {
    it("prefers an alias", function () {
      let alias = "test1";
      let n = {"alias": alias, address: "10.20.30.40", subnet: 32, children: {}, rel_x: 1, rel_y: 8};
      expect(nodes.get_name(n)).toEqual(alias);
      expect(typeof(nodes.get_name(n))).toEqual("string");
    });
    it("returns a number string otherwise", function () {
      let addr = "10.20.30.40";
      nodes.layout_flat = true;
      let n = {alias: "", address: addr, subnet: 16, ipstart: 169082880, ipend: 169148415};
      expect(nodes.get_name(n)).toEqual(addr);
      expect(typeof(nodes.get_name(n))).toEqual("string");
      nodes.layout_flat = false;
      expect(nodes.get_name(n)).toEqual("20");
      expect(typeof(nodes.get_name(n))).toEqual("string");
    });
  });

  describe("flat_scale", function () {});

  describe("get_address", function () {
    it("appends subnet (unless =32)", function () {
      let n = {address: "1.2.3.4", subnet: 32};
      expect(nodes.get_address(n)).toEqual("1.2.3.4");
      n = {address: "1.2.3.4", subnet: 24};
      expect(nodes.get_address(n)).toEqual("1.2.3.4/24");
      n = {address: "1.2.3.4", subnet: 16};
      expect(nodes.get_address(n)).toEqual("1.2.3.4/16");
      n = {address: "1.2.3.4", subnet: 8};
      expect(nodes.get_address(n)).toEqual("1.2.3.4/8");
    });
    it("pads with zeroes", function () {
      let n = {address: "1.2.3", subnet: 24};
      expect(nodes.get_address(n)).toEqual("1.2.3.0/24");
      n = {address: "1.2", subnet: 16};
      expect(nodes.get_address(n)).toEqual("1.2.0.0/16");
      n = {address: "1", subnet: 8};
      expect(nodes.get_address(n)).toEqual("1.0.0.0/8");
    });
  });

  describe("do_layout", function () {});

  describe("set_layout", function () {
    it("only works with valid styles", function () {
      spyOn(nodes, "do_layout");
      expect(nodes.set_layout("Circle")).toBe(true);
      expect(nodes.set_layout("Square")).toBe(false);
      expect(nodes.set_layout("Grid")).toBe(true);
      expect(nodes.set_layout("Litmus")).toBe(false);
      expect(nodes.set_layout("Address")).toBe(true);
      expect(nodes.do_layout).toHaveBeenCalledTimes(3);
    });
  });
});

describe("address layout", function () {
  beforeEach(function () {
    address = nodes.layouts.Address;
  });
  describe("recursive_placement", function () {
    it("base case", function () {
      expect(address.recursive_placement(150, [0])).toEqual({x: -75, y: -75});
      expect(address.recursive_placement(150, [1])).toEqual({x: -65, y: -75});
      expect(address.recursive_placement(150, [14])).toEqual({x: 65, y: -75});
      expect(address.recursive_placement(150, [15])).toEqual({x: 75, y: -75});
      expect(address.recursive_placement(150, [16])).toEqual({x: -75, y: -65});
      expect(address.recursive_placement(150, [239])).toEqual({x: 75, y: 65});
      expect(address.recursive_placement(150, [240])).toEqual({x: -75, y: 75});
      expect(address.recursive_placement(150, [241])).toEqual({x: -65, y: 75});
      expect(address.recursive_placement(150, [254])).toEqual({x: 65, y: 75});
      expect(address.recursive_placement(150, [255])).toEqual({x: 75, y: 75});
    });
    it("recursive case", function () {
      expect(address.recursive_placement(36000, [0, 0])).toEqual({x: -19125, y: -19125});
      expect(address.recursive_placement(36000, [15, 0])).toEqual({x: -16875, y: -19125});
      expect(address.recursive_placement(36000, [240, 0])).toEqual({x: -19125, y: -16875});
      expect(address.recursive_placement(36000, [255, 0])).toEqual({x: -16875, y: -16875});

      expect(address.recursive_placement(36000, [0, 15])).toEqual({x: 16875, y: -19125});
      expect(address.recursive_placement(36000, [15, 15])).toEqual({x: 19125, y: -19125});
      expect(address.recursive_placement(36000, [240, 15])).toEqual({x: 16875, y: -16875});
      expect(address.recursive_placement(36000, [255, 15])).toEqual({x: 19125, y: -16875});
      
      expect(address.recursive_placement(36000, [0, 240])).toEqual({x: -19125, y: 16875});
      expect(address.recursive_placement(36000, [15, 240])).toEqual({x: -16875, y: 16875});
      expect(address.recursive_placement(36000, [240, 240])).toEqual({x: -19125, y: 19125});
      expect(address.recursive_placement(36000, [255, 240])).toEqual({x: -16875, y: 19125});
      
      expect(address.recursive_placement(36000, [0, 255])).toEqual({x: 16875, y: 16875});
      expect(address.recursive_placement(36000, [15, 255])).toEqual({x: 19125, y: 16875});
      expect(address.recursive_placement(36000, [240, 255])).toEqual({x: 16875, y: 19125});
      expect(address.recursive_placement(36000, [255, 255])).toEqual({x: 19125, y: 19125});
    });
  });

  describe("get_segment_difference", function () {
    it("base case", function () {
      expect(address.get_segment_difference(0, 8, 169090600)).toEqual(["10"]);
      expect(address.get_segment_difference(0, 16, 169090600)).toEqual(["10", "20"]);
      expect(address.get_segment_difference(0, 24, 169090600)).toEqual(["10", "20", "30"]);
      expect(address.get_segment_difference(0, 32, 169090600)).toEqual(["10", "20", "30", "40"]);
      expect(address.get_segment_difference(8, 16, 169090600)).toEqual(["20"]);
      expect(address.get_segment_difference(8, 24, 169090600)).toEqual(["20", "30"]);
      expect(address.get_segment_difference(8, 32, 169090600)).toEqual(["20", "30", "40"]);
      expect(address.get_segment_difference(16, 24, 169090600)).toEqual(["30"]);
      expect(address.get_segment_difference(16, 32, 169090600)).toEqual(["30", "40"]);
      expect(address.get_segment_difference(24, 32, 169090600)).toEqual(["40"]);
      expect(address.get_segment_difference(0, 0, 169090600)).toEqual([]);
      expect(address.get_segment_difference(8, 8, 169090600)).toEqual([]);
      expect(address.get_segment_difference(16, 16, 169090600)).toEqual([]);
      expect(address.get_segment_difference(24, 24, 169090600)).toEqual([]);
      expect(address.get_segment_difference(32, 32, 169090600)).toEqual([]);
    });
  });

  describe("arrange_collection", function () {});
  describe("layout", function () {});
});

describe("grid layout", function () {
  beforeEach(function () {
    grid = nodes.layouts.Grid;
  });
  describe("arrange_collection", function () {});
  describe("layout", function () {});
});

describe("circle layout", function () {
  beforeEach(function () {
    circle = nodes.layouts.Circle;
  });
  describe("find_center_node", function () {
    it("finds the most-connected node", function () {
      let tree = get_mock_node_tree();
      let fake_tree = {
        b: {inputs: [1,2], outputs: [4,5,6]},
        a: {inputs: [1,2,3], outputs: [4,5,6]},
        c: {inputs: [1,2,3], outputs: [4,5]},
      };
      expect(circle.find_center_node(fake_tree)).toEqual(fake_tree['a']);
      expect(circle.find_center_node(tree)).toEqual(tree[352321536])
    });
  });

  //cannot test because test data has input/output connections broken.
  describe("get_all_attached_nodes", function () {});

  describe("sorted_unique", function () {
    it("sorts", function () {
      sorter = function(a, b) {return a-b};
      expect(circle.sorted_unique([3,2,7,6,8], sorter)).toEqual([2,3,6,7,8]);
    });
    it("uniquifies", function () {
      sorter = function(a, b) {return a.ipstart-b.ipstart};
      nodelist = [
        {address: "30", ipstart: 30, subnet: 5},
        {address: "10", ipstart: 10, subnet: 5},
        {address: "20", ipstart: 20, subnet: 5},
        {address: "30", ipstart: 30, subnet: 5},
        {address: "20", ipstart: 20, subnet: 5},
        {address: "10", ipstart: 10, subnet: 5},
        {address: "10", ipstart: 10, subnet: 5},
        {address: "30", ipstart: 30, subnet: 5},
        {address: "20", ipstart: 20, subnet: 5},
      ]
      expected = [
        {address: "10", ipstart: 10, subnet: 5},
        {address: "20", ipstart: 20, subnet: 5},
        {address: "30", ipstart: 30, subnet: 5},
      ]

      expect(circle.sorted_unique(nodelist, sorter)).toEqual(expected);
    })
  });

  describe("remove_item", function () {
    it("removes an item", function () {
      numlist = [3,2,7,6,8];
      circle.remove_item(numlist, 6);
      expect(numlist).toEqual([3,2,7,8]);
    });
  });

  describe("move_to_center", function () {});
  describe("arrange_nodes_recursion", function () {});
  describe("arrange_nodes_evenly", function () {});

  describe("node_sorter", function () {
    it("sorts", function () {
      nodelist = [
        {ipstart: 30, subnet: 5},
        {ipstart: 25, subnet: 10},
        {ipstart: 31, subnet: 1},
        {ipstart: 20, subnet: 5},
        {ipstart: 25, subnet: 5},
        {ipstart: 10, subnet: 5},
        {ipstart: 20, subnet: 10},
        {ipstart: 15, subnet: 10},
      ]
      expected = [
        {ipstart: 10, subnet: 5},
        {ipstart: 15, subnet: 10},
        {ipstart: 20, subnet: 5},
        {ipstart: 20, subnet: 10},
        {ipstart: 25, subnet: 5},
        {ipstart: 25, subnet: 10},
        {ipstart: 30, subnet: 5},
        {ipstart: 31, subnet: 1},
      ]
      expect(circle.sorted_unique(nodelist, circle.node_sorter)).toEqual(expected);
    });
  });

  describe("layout", function () {});
});

