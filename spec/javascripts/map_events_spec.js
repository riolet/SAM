describe("map_events.js file", function () {
  describe("deselectText", function () {});
  
  describe("distanceSquared", function () {
    it("is accurate", function () {
      expect(distanceSquared(0, 0, 0, 10)).toEqual(100);
      expect(distanceSquared(0, 0, 10, 0)).toEqual(100);
      expect(distanceSquared(0, 10, 0, 0)).toEqual(100);
      expect(distanceSquared(10, 0, 0, 0)).toEqual(100);
      expect(distanceSquared(3, 4, 6, 8)).toEqual(25);
    });
  });
  describe("contains", function () {
    it("works", function () {
      let n = {abs_x: 50, abs_y: 500, radius: 10}
      expect(contains(n, 10, 10)).toBe(false);
      expect(contains(n, 50, 489)).toBe(false);
      expect(contains(n, 50, 490)).toBe(true);
      expect(contains(n, 50, 510)).toBe(true);
      expect(contains(n, 50, 511)).toBe(false);
      expect(contains(n, 61, 500)).toBe(false);
      expect(contains(n, 60, 500)).toBe(true);
      expect(contains(n, 40, 500)).toBe(true);
      expect(contains(n, 39, 500)).toBe(false);
    });
  });
  
  describe("pick", function () {
    it("works", function () {
      let nodeA = {subnet: 32, abs_x: 20, abs_y: 20, radius: 5}
      let nodeB = {subnet: 32, abs_x: 20, abs_y: 40, radius: 5}
      let nodeC = {subnet: 32, abs_x: 40, abs_y: 20, radius: 5}
      let nodeD = {subnet: 32, abs_x: 40, abs_y: 40, radius: 5}
      renderCollection = [nodeA, nodeB, nodeC, nodeD];
      expect(pick(20, 20, 1)).toBe(nodeA);
      expect(pick(20, 40, 1)).toBe(nodeB);
      expect(pick(40, 40, 1)).toBe(nodeD);
      expect(pick(40, 20, 1)).toBe(nodeC);
      expect(pick(30, 30, 1)).toBeNull();
      
      expect(pick(24, 20, 1)).toBe(nodeA);
      expect(pick(20, 24, 1)).toBe(nodeA);
      expect(pick(24, 24, 1)).toBeNull();
    });

    it("skips subnets when zoomed in", function () {
      let nodeA = {subnet: 32, abs_x: 20, abs_y: 20, radius: 5}
      let nodeB = {subnet: 16, abs_x: 20, abs_y: 20, radius: 50}
      renderCollection = [nodeA, nodeB];
      expect(pick(20, 20, 1)).toBe(nodeA);
      expect(pick(20, 26, 1)).toBe(nodeB);
      nodeB = {subnet: 8, abs_x: 20, abs_y: 20, radius: 50}
      renderCollection = [nodeA, nodeB];
      expect(pick(20, 26, 1)).toBe(null);
    });
  });
  
  //these do not lend themselves well to unit testing...
  describe("mouseup", function () {});
  describe("mousemove", function () {});
  describe("wheel", function () {});
  describe("keydown", function () {});
  describe("applyfilter", function () {});
  describe("onfilter", function () {});
  describe("applysearch", function () {});
  describe("onsearch", function () {});
  describe("applyProtocolFilter", function () {});
  describe("onProtocolFilter", function () {});
  describe("onResize", function () {});
});