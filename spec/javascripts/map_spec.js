describe("map.js file", function () {  describe("zoom levels", function() {
    it("defined", function () {
      expect(zNodes16).toBeDefined();
      expect(zNodes24).toBeDefined();
      expect(zNodes32).toBeDefined();
      expect(zLinks16).toBeDefined();
      expect(zLinks24).toBeDefined();
      expect(zLinks32).toBeDefined();
    });
    it("ascending order", function () {
      expect(zLinks16).toBeLessThan(zLinks24);
      expect(zLinks24).toBeLessThan(zLinks32);
      expect(zNodes16).toBeLessThan(zNodes24);
      expect(zNodes24).toBeLessThan(zNodes32);
    });
  });


  describe("config", function () {
    it("defined", function() {
      cfg = Object.keys(config);
      expect(cfg).toContain('show_clients');
      expect(cfg).toContain('show_servers');
      expect(cfg).toContain('show_in');
      expect(cfg).toContain('show_out');
      expect(cfg).toContain('filter');
      expect(cfg).toContain('tstart');
      expect(cfg).toContain('tend');
    });
  })


  describe("init", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("init_canvas", function () {
    it('defined', function() {
      document.getElementById = jasmine.createSpy('HTML Element')
        .and.returnValue(document.createElement("canvas"));
      init();
      expect(canvas).toBeDefined();
      expect(ctx).toBeDefined();
      expect(canvas).not.toBeNull();
      expect(ctx).not.toBeNull();
    });
  });


  describe("currentSubnet", function () {
    beforeEach(function () {
      epsilon = 0.00001;
    });
    it("matches 8", function () {
      expect(currentSubnet(zNodes16 - epsilon)).toEqual(8);
    });
    it("matches 16", function () {
      expect(currentSubnet(zNodes16)).toEqual(16);
      expect(currentSubnet(zNodes24 - epsilon)).toEqual(16);
    });
    it("matches 24", function () {
      expect(currentSubnet(zNodes24)).toEqual(24);
      expect(currentSubnet(zNodes32 - epsilon)).toEqual(24);
    });
    it("matches 24", function () {
      expect(currentSubnet(zNodes32)).toEqual(32);
    });
  });


  describe("findNode", function () {
    beforeEach(function () {
      m_nodes = get_mock_node_tree()
    });
    it("finds /8", function () {
      node = findNode("189");
      expect(node.address).toEqual("189");
      node = findNode(189);
      expect(node.address).toEqual("189");
    });
    it("finds /16", function () {
      node = findNode("189.58");
      expect(node.address).toEqual("189.58");
      node = findNode(189, 58);
      expect(node.address).toEqual("189.58");
    });
    it("finds /24", function () {
      node = findNode("189.58.134");
      expect(node.address).toEqual("189.58.134");
      node = findNode(189, 58, 134);
      expect(node.address).toEqual("189.58.134");
    });
    it("finds /32", function () {
      node = findNode("189.58.134.156");
      expect(node.address).toEqual("189.58.134.156");
      node = findNode(189, 58, 134, 156);
      expect(node.address).toEqual("189.58.134.156");
    });
  });


  describe("removeChildren", function () {
    it("works without children", function () {
      var div = document.createElement("div");
      removeChildren(div);
      expect(div.childElementCount).toEqual(0);
    });
    it("works with children", function () {
      var div = document.createElement("div");
      div.appendChild(document.createElement("p"));
      div.appendChild(document.createElement("p"));
      div.appendChild(document.createElement("p"));
      removeChildren(div);
      expect(div.childElementCount).toEqual(0);
    });
    it("works with grandchildren", function () {
      var i;
      var div = document.createElement("div");
      var cdiv;
      for (i = 0; i < 10; i += 1) {
        cdiv = document.createElement("div");
        cdiv.appendChild(document.createElement("p"));
        cdiv.appendChild(document.createElement("p"));
        cdiv.appendChild(document.createElement("p"));
        div.appendChild(cdiv)
      }
      removeChildren(div);
      expect(div.childElementCount).toEqual(0);
    });
  });
});
