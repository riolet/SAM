describe("base map file", function () {
  describe("zoom levels", function() {
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
  describe("canvas", function () {
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

});