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
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("sel_update_display", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });
});
