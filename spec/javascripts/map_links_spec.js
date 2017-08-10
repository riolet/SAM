describe("map_links file", function () {
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
  //depends on controller.rect and g_scale.
  describe("link_comparator", function () {});

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
  describe("fix_link_pointers", function () {});
  describe("link_closestEmptyPort", function () {});
  describe("link_processPorts", function () {});
});