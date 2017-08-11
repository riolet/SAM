xdescribe("map_links file", function () {
  
  describe("link_request_add", function () {
    it("adds to the queue", function () {
      m_link_requests = [];
      link_request_add("1.2.3.4");
      link_request_add("2.3.4.5");
      link_request_add("3.4.5.6");
      link_request_add("4.5.6.7");
      let expected = [
        "1.2.3.4",
        "2.3.4.5",
        "3.4.5.6",
        "4.5.6.7"
      ]
      expect(m_link_requests).toEqual(expected);
    })
  });
  
  describe("link_request_add_all", function () {
    it("adds all nodes", function () {
      nodeE = {address: "110.169.200.144", subnet: 32, children: []};
      nodeD = {address: "110.169.200.0", subnet: 24, children: [nodeE]};
      nodeC = {address: "110.169.0.0", subnet: 16, children: [nodeD]};
      nodeB = {address: "110.0.0.0", subnet: 8, children: [nodeC]};
      nodeA = {address: "21.0.0.0", subnet: 8, children: []};
      let coll = {
        a: nodeA,
        b: nodeB
      }
      m_link_requests = [];
      link_request_add_all(coll);
      let expected = ['21.0.0.0/8', '110.0.0.0/8', '110.169.0.0/16', 
        '110.169.200.0/24', '110.169.200.144'];
      expect(m_link_requests).toEqual(expected);
    });
  });
  
  describe("dist_between_squared", function () {
    it("is accurate", function () {
      expect(dist_between_squared(0, 0, 0, 10)).toEqual(100);
      expect(dist_between_squared(0, 0, 10, 0)).toEqual(100);
      expect(dist_between_squared(0, 10, 0, 0)).toEqual(100);
      expect(dist_between_squared(10, 0, 0, 0)).toEqual(100);
      expect(dist_between_squared(3, 4, 6, 8)).toEqual(25);
    });
  });
  
  describe("link_comparator", function () {
    it("finds the middlemost", function () {
      let nodeA = {ipstart: 168427520, ipend: 168493055, address: "10.10.0.0", abs_x:  0, abs_y: 0, subnet: 16};
      let nodeB = {ipstart: 169082880, ipend: 169148415, address: "10.20.0.0", abs_x: 10, abs_y: 0, subnet: 16};
      let nodeC = {ipstart: 169738240, ipend: 169803775, address: "10.30.0.0", abs_x: 14, abs_y: 14, subnet: 16};
      let nodeD = {ipstart: 167772160, ipend: 184549375, address: "10.0.0.0", abs_x: 20, abs_y: 0, subnet: 8};
      let nodeE = {ipstart: 170393600, ipend: 170459135, address: "10.40.0.0", abs_x: 0, abs_y: 20, subnet: 16};
      let nodeF = {ipstart: 171048960, ipend: 171114495, address: "10.50.0.0", abs_x: 15, abs_y: 15, subnet: 16};
      let nodeG = {ipstart: 171704320, ipend: 171769855, address: "10.60.0.0", abs_x: 20, abs_y: 20, subnet: 16};
      nodeD.children = {
        168427520: nodeA,
        169082880: nodeB,
        169738240: nodeC,
        170393600: nodeE,
        171048960: nodeF,
        171704320: nodeG,
      };
      nodes.nodes = {
        "167772160": nodeD
      };
      renderCollection = [nodeA, nodeB, nodeC, nodeD, nodeE, nodeF, nodeG];
      controller.rect = { x: 0, y: 58, width: 959, height: 555, top: 58, right: 959, bottom: 613, left: 0 };
      tx = controller.rect.width / 2;
      ty = controller.rect.height / 2;
      g_scale = 1;
      let request = ["10.20.0.0/16", "10.50.0.0/16", "10.30.0.0/16", "10.60.0.0/16", "10.40.0.0/16", "10.0.0.0/8", "10.10.0.0/16"];
      request.sort(link_comparator);
      let expected = ["10.0.0.0/8", "10.10.0.0/16", "10.20.0.0/16", "10.30.0.0/16", "10.40.0.0/16", "10.50.0.0/16", "10.60.0.0/16"];
      expect(request).toEqual(expected);
    });
    it("delays nodes that aren't in the render collection", function () {
      let nodeA = {ipstart: 168427520, ipend: 168493055, address: "10.10.0.0", abs_x:  0, abs_y: 0, subnet: 16};
      let nodeB = {ipstart: 169082880, ipend: 169148415, address: "10.20.0.0", abs_x: 10, abs_y: 0, subnet: 16};
      let nodeC = {ipstart: 169738240, ipend: 169803775, address: "10.30.0.0", abs_x: 14, abs_y: 14, subnet: 16};
      let nodeD = {ipstart: 167772160, ipend: 184549375, address: "10.0.0.0", abs_x: 20, abs_y: 0, subnet: 8};
      let nodeE = {ipstart: 170393600, ipend: 170459135, address: "10.40.0.0", abs_x: 0, abs_y: 20, subnet: 16};
      let nodeF = {ipstart: 171048960, ipend: 171114495, address: "10.50.0.0", abs_x: 15, abs_y: 15, subnet: 16};
      let nodeG = {ipstart: 171704320, ipend: 171769855, address: "10.60.0.0", abs_x: 20, abs_y: 20, subnet: 16};
      nodeD.children = {
        168427520: nodeA,
        169082880: nodeB,
        169738240: nodeC,
        170393600: nodeE,
        171048960: nodeF,
        171704320: nodeG,
      };
      nodes.nodes = {
        "167772160": nodeD
      };
      renderCollection = [nodeA, nodeB, nodeC, nodeE, nodeF, nodeG];
      controller.rect = { x: 0, y: 58, width: 959, height: 555, top: 58, right: 959, bottom: 613, left: 0 };
      tx = controller.rect.width / 2;
      ty = controller.rect.height / 2;
      g_scale = 1;
      let request = ["10.20.0.0/16", "10.50.0.0/16", "10.30.0.0/16", "10.60.0.0/16", "10.40.0.0/16", "10.0.0.0/8", "10.10.0.0/16"];
      request.sort(link_comparator);
      let expected = ["10.10.0.0/16", "10.20.0.0/16", "10.30.0.0/16", "10.40.0.0/16", "10.50.0.0/16", "10.60.0.0/16", "10.0.0.0/8"];
      expect(request).toEqual(expected);
    })
  });

  describe("link_request_submit", function () {
    it("submits a limited number", function () {
      spyOn(window, "GET_links")
      //100 reqests
      m_link_requests = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
        'a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2', 'i2', 'j2', 'k2', 'l2', 'm2', 'n2', 'o2', 'p2', 'q2', 'r2', 's2', 't2',
        'a3', 'b3', 'c3', 'd3', 'e3', 'f3', 'g3', 'h3', 'i3', 'j3', 'k3', 'l3', 'm3', 'n3', 'o3', 'p3', 'q3', 'r3', 's3', 't3',
        'a4', 'b4', 'c4', 'd4', 'e4', 'f4', 'g4', 'h4', 'i4', 'j4', 'k4', 'l4', 'm4', 'n4', 'o4', 'p4', 'q4', 'r4', 's4', 't4',
        'a5', 'b5', 'c5', 'd5', 'e5', 'f5', 'g5', 'h5', 'i5', 'j5', 'k5', 'l5', 'm5', 'n5', 'o5', 'p5', 'q5', 'r5', 's5', 't5',
      ];
      g_chunkSize = 20;
      let expected = [ 'a', 'a2', 'a3', 'a4', 'a5', 'b', 'b2', 'b3', 'b4', 'b5', 'c', 'c2', 'c3', 'c4', 'c5', 'd', 'd2', 'd3', 'd4', 'd5' ];
      link_request_submit();
      clearTimeout(m_link_timer);
      expect(window.GET_links).toHaveBeenCalledTimes(1);
      expect(window.GET_links).toHaveBeenCalledWith(expected);
    });
    it("doesn't fire if empty", function () {
      spyOn(window, "GET_links")
      m_link_requests = [];
      link_request_submit();
      expect(window.GET_links).not.toHaveBeenCalled();
    });
    it("skips duplicates", function () {
      spyOn(window, "GET_links")
      m_link_requests = ['a', 'b', 'c', 'b', 'a', 'b', 'c', 'b', 'a'];
      let expected = ['a', 'b', 'c'];
      link_request_submit();
      clearTimeout(m_link_timer);
      expect(window.GET_links).toHaveBeenCalledTimes(1);
      expect(window.GET_links).toHaveBeenCalledWith(expected);
    });
  });

  describe("link_remove_all", function () {
    it("removes inputs, outputs, server, client", function () {
      let coll = get_mock_node_tree();
      node21 = coll["352321536"];
      node110 = coll["1845493760"];
      node110_145 = node110.children["1854996480"];
      node110_145_200 = node110_145.children["1855047680"]

      expect(node21.inputs.length).toEqual(4);
      expect(node21.outputs.length).toEqual(3);
      expect(node21.server).toBe(true);
      expect(node21.client).toBe(true);
      expect(node110_145_200.inputs.length).toEqual(0);
      expect(node110_145_200.outputs.length).toEqual(1);
      expect(node110_145_200.server).toBe(false);
      expect(node110_145_200.client).toBe(true);
      link_remove_all(coll);
      expect(node21.inputs.length).toEqual(0);
      expect(node21.outputs.length).toEqual(0);
      expect(node21.server).toBe(false);
      expect(node21.client).toBe(false);
      expect(node110_145_200.inputs.length).toEqual(0);
      expect(node110_145_200.outputs.length).toEqual(0);
      expect(node110_145_200.server).toBe(false);
      expect(node110_145_200.client).toBe(false);
    })
  });

  describe("links_reset", function () {});
  describe("GET_links", function () {});
  describe("GET_links_callback", function () {});
  
  describe("fix_link_pointers", function () {
    it("fixes inputs and outputs", function () {
      let node1 = {"address": "10.0.0.0", subnet: 8, ipstart: 167772160, ipend: 184549375};
      let node11 = {"address": "10.10.0.0", subnet: 16, ipstart: 168427520, ipend: 168493055};
      let node111 = {"address": "10.10.10.0", subnet: 24, ipstart: 168430080, ipend: 168430335};
      let node1111 = {"address": "10.10.10.10", subnet: 32, ipstart: 168430090, ipend: 168430090};
      let node112 = {"address": "10.10.20.0", subnet: 24, ipstart: 168432640, ipend: 168432895};
      let node1122 = {"address": "10.10.20.20", subnet: 32, ipstart: 168432660, ipend: 168432660};
      let node13 = {"address": "10.30.0.0", subnet: 16, ipstart: 169738240, ipend: 169803775};
      let node133 = {"address": "10.30.30.0", subnet: 24, ipstart: 169745920, ipend: 169746175};
      let node1333 = {"address": "10.30.30.30", subnet: 32, ipstart: 169745950, ipend: 169745950};
      node1.children = {
        168427520: node11,
        169738240: node13
      };
      node11.children = {
        168430080: node111,
        168432640: node112,
      };
      node111.children = {168430090: node1111};
      node112.children = {168432660: node1122};
      node13.children = {169745920: node133};
      node133.children = {169745950: node1333};
      node1333.parent = node133;
      node133.parent = node13;
      node13.parent = node1;
      node1122.parent = node112;
      node112.parent=node11;
      node1111.parent = node111;
      node111.parent = node11
      node11.parent = node1;
      node1111.inputs = [
        {src_start: 168432660, src_end: 168432660}
      ];
      node1111.outputs = [
        {dst_start: 169745950, dst_end: 169745950}
      ];
      nodes.nodes = {
        167772160: node1
      };
      fix_link_pointers(node1111);
      expect(node1111.inputs[0].src.address).toEqual("10.10.20.0");
      expect(node1111.outputs[0].dst.address).toEqual("10.30.0.0");
    })
  });
  
  describe("link_closestEmptyPort", function () {
    it("chooses closest port", function () {
      let nodeLeft = {abs_x: -10, abs_y: 0};
      let nodeRight = {abs_x: 10, abs_y: 0};
      let nodeBottom = {abs_x: 0, abs_y: 10};
      let nodeTop = {abs_x: 0, abs_y: -10};
      let used = [false, false, false, false, false, false, false, false];
      expect(link_closestEmptyPort(nodeLeft, nodeRight, used)).toEqual(1);
      expect(link_closestEmptyPort(nodeRight, nodeLeft, used)).toEqual(4);
      expect(link_closestEmptyPort(nodeTop, nodeBottom, used)).toEqual(6);
      expect(link_closestEmptyPort(nodeBottom, nodeTop, used)).toEqual(3);
    });
    it("skips used ports", function () {
      let nodeLeft = {abs_x: -10, abs_y: 0};
      let nodeRight = {abs_x: 10, abs_y: 0};
      let nodeBottom = {abs_x: 0, abs_y: 10};
      let nodeTop = {abs_x: 0, abs_y: -10};
      let used = [true, true, false, false, false, false, false, false];
      expect(link_closestEmptyPort(nodeLeft, nodeRight, used)).toEqual(2);
      used = [false, false, false, false, true, true, false, false];
      expect(link_closestEmptyPort(nodeRight, nodeLeft, used)).toEqual(3);
      used = [false, false, false, false, false, false, true, true];
      expect(link_closestEmptyPort(nodeTop, nodeBottom, used)).toEqual(5);
      used = [false, false, true, true, false, false, false, false];
      expect(link_closestEmptyPort(nodeBottom, nodeTop, used)).toEqual(4);
    });
  });
  
  describe("link_processPorts", function () {
    it("adds ports as needed", function () {
      let node1 = {"address": "10.0.0.0", subnet: 8, ipstart: 167772160, ipend: 184549375, abs_x: 0, abs_y: 0};
      let node11 = {"address": "10.10.0.0", subnet: 16, ipstart: 168427520, ipend: 168493055, abs_x: 0, abs_y: 0};
      let node111 = {"address": "10.10.10.0", subnet: 24, ipstart: 168430080, ipend: 168430335, abs_x: 0, abs_y: 0};
      let node1111 = {"address": "10.10.10.10", subnet: 32, ipstart: 168430090, ipend: 168430090, abs_x: 10, abs_y: 0, ports: {}};
      let node112 = {"address": "10.10.20.0", subnet: 24, ipstart: 168432640, ipend: 168432895, abs_x: 0, abs_y: 0};
      let node1122 = {"address": "10.10.20.20", subnet: 32, ipstart: 168432660, ipend: 168432660, abs_x: 0, abs_y: 0};
      let node13 = {"address": "10.30.0.0", subnet: 16, ipstart: 169738240, ipend: 169803775, abs_x: 0, abs_y: 0};
      let node133 = {"address": "10.30.30.0", subnet: 24, ipstart: 169745920, ipend: 169746175, abs_x: 0, abs_y: 0};
      let node1333 = {"address": "10.30.30.30", subnet: 32, ipstart: 169745950, ipend: 169745950, abs_x: -10, abs_y: 0};
      node1.children = {
        168427520: node11,
        169738240: node13
      };
      node11.children = {
        168430080: node111,
        168432640: node112,
      };
      node111.children = {168430090: node1111};
      node112.children = {168432660: node1122};
      node13.children = {169745920: node133};
      node133.children = {169745950: node1333};
      node1333.parent = node133;
      node133.parent = node13;
      node13.parent = node1;
      node1122.parent = node112;
      node112.parent=node11;
      node1111.parent = node111;
      node111.parent = node11
      node11.parent = node1;
      nodes.nodes = {
        167772160: node1
      };
      
      let dest = node1111;
      expect(Object.keys(dest.ports)).toEqual([]);
      let links = [
        {port: 27, src_start: 169745950, src_end: 169745950},
        {port: 28, src_start: 169745950, src_end: 169745950},
        {port: 29, src_start: 169745950, src_end: 169745950},
        {port: 30, src_start: 169745950, src_end: 169745950},
        {port: 31, src_start: 169745950, src_end: 169745950}
      ];
      link_processPorts(links, dest);
      expect(Object.keys(dest.ports).sort()).toEqual(["27", "28", "29", "30", "31"]);
      link_processPorts(links, dest);
      expect(Object.keys(dest.ports).sort()).toEqual(["27", "28", "29", "30", "31"]);
      links = [
        {port: 26, src_start: 169745950, src_end: 169745950},
      ];
      link_processPorts(links, dest);
      expect(Object.keys(dest.ports).sort()).toEqual(["26", "27", "28", "29", "30", "31"]);
      links = [
        {port: 32, src_start: 169745950, src_end: 169745950},
        {port: 33, src_start: 169745950, src_end: 169745950},
        {port: 34, src_start: 169745950, src_end: 169745950},
        {port: 35, src_start: 169745950, src_end: 169745950},
        {port: 36, src_start: 169745950, src_end: 169745950},
        {port: 37, src_start: 169745950, src_end: 169745950},
        {port: 38, src_start: 169745950, src_end: 169745950},
      ];
      link_processPorts(links, dest);
      expect(Object.keys(dest.ports).sort()).toEqual(["26", "27", "28", "29", "30", "31", "32", "33"]);
    });
  });
});