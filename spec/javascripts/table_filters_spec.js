describe("table_filters.js file", function () {
  beforeEach(function () {
    g_known_tags = ["tag1", "tag2"];
    g_known_envs = ["production", "dev", "inherit"];
  });

  describe("members", function () {
    it("has filter types", function () {
      expect(Object.keys(filters.private.types)).toContain("connections");
      expect(Object.keys(filters.private.types)).toContain("env");
      expect(Object.keys(filters.private.types)).toContain("mask");
      expect(Object.keys(filters.private.types)).toContain("port");
      expect(Object.keys(filters.private.types)).toContain("protocol");
      expect(Object.keys(filters.private.types)).toContain("role");
      expect(Object.keys(filters.private.types)).toContain("tags");
      expect(Object.keys(filters.private.types)).toContain("target");
      expect(Object.keys(filters.private.types)).toContain("subnet");
      Object.keys(filters.private.types).forEach(function (k) {
        let f = filters.private.types[k];
        expect(typeof(f[0])).toEqual("function");
        expect(typeof(f[1])).toEqual("string");
        expect(typeof(f[2][0])).toEqual("string");
      });
    });
  });
  describe("addFilter", function () {
    it("adds a filter", function () {
      filters.filters = [];
      filters.addFilter("env", ["production"]);
      expect(filters.filters.length).toEqual(1);
      expect(filters.filters[0].type).toEqual("env");
    });
    it("fails on bad params", function () {
      filters.filters = [];
      spyOn(filters.private, "createFilter");
      filters.addFilter("env", ["production", "dev"]);
      expect(filters.private.createFilter).not.toHaveBeenCalled();
      expect(filters.filters.length).toEqual(0);
    });
    it("fails on bad filter", function () {
      filters.filters = [];
      spyOn(filters.private, "createFilter");
      filters.addFilter("envy", ["production"]);
      expect(filters.private.createFilter).not.toHaveBeenCalled();
      expect(filters.filters.length).toEqual(0);
    });
  });
  describe("deleteFilter", function () {
    it("removes the filter in question", function () {
      spyOn(filters.private, "updateSummary");
      filters.filters = [0,1,2,3,4];
      filters.deleteFilter(2);
      expect(filters.filters).toEqual([0,1,3,4])
      expect(filters.private.updateSummary).toHaveBeenCalled();
    });
    it("doesn't run on out-of-bounds", function () {
      spyOn(filters.private, "updateSummary");
      filters.filters = [0,1,2,3,4];
      filters.deleteFilter(7);
      expect(filters.filters).toEqual([0,1,2,3,4])
      expect(filters.private.updateSummary).not.toHaveBeenCalled();
    });
  });
  describe("updateDisplay", function () {});
  describe("getFilters", function () {
    it("works on all filter types", function () {
      filters.ds = "ds5";
      filters.filters = [];
      filters.addFilter("connections", [">", "i", "300"]);
      filters.addFilter("env", ["production"]);
      filters.addFilter("mask", ["192.168.0.0/16"]);
      filters.addFilter("port", ["1", "443"]);
      filters.addFilter("protocol", ["0", "TCP"]);
      filters.addFilter("role", [">", "0.75"]);
      filters.addFilter("tags", ["1", "64GB"]);
      filters.addFilter("target", ["10.20.30.40", "0"]);
      filters.addFilter("subnet", ["24"]);
      let expected = "ds5|0;1;>;i;300|1;1;production|2;1;192.168.0.0/16|3;1;1;443|4;1;0;TCP|5;1;>;0.75|7;1;1;64GB|8;1;10.20.30.40;0|6;1;24";
      let actual = filters.getFilters();
      expect(actual).toEqual(expected);
    });
  });
  describe("setFilters", function () {
    it("works on all filter types", function () {
      let filterstring = "ds1|0;1;>;i;300|1;1;production|2;1;192.168.0.0/16|3;1;1;443|4;1;0;TCP|5;1;>;0.75|7;1;1;64GB|8;1;10.20.30.40;0|6;1;24";
      filters.filters = [];
      filters.setFilters(filterstring);
      expect(filters.filters.length).toEqual(9);
    })
  });
  describe("private.createFilter", function () {
    it("works for each type", function () {
      function rmkr(p) {
        return [document.createElement("DIV")];
      }
      let f1 = filters.private.createFilter(true, "connections", [">", "i", "300"], rmkr);
      let f2 = filters.private.createFilter(false, "env", ["production"], rmkr);
      let f3 = filters.private.createFilter(true, "mask", ["192.168.0.0/16"], rmkr);
      let f4 = filters.private.createFilter(false, "port", ["1", "443"], rmkr);
      let f5 = filters.private.createFilter(true, "protocol", ["0", "TCP"], rmkr);
      let f6 = filters.private.createFilter(false, "role", [">", "0.75"], rmkr);
      let f7 = filters.private.createFilter(true, "tags", ["1", "64GB"], rmkr);
      let f8 = filters.private.createFilter(false, "target", ["10.20.30.40", "0"], rmkr);
      let f9 = filters.private.createFilter(true, "subnet", ["24"], rmkr);
      let enableds = [f1.enabled, f2.enabled, f3.enabled, f4.enabled, f5.enabled, f6.enabled, f7.enabled, f8.enabled, f9.enabled];
      let expected_enableds = [true, false, true, false, true, false, true, false, true];
      expect(enableds).toEqual(expected_enableds);
      let types = [f1.type, f2.type, f3.type, f4.type, f5.type, f6.type, f7.type, f8.type, f9.type];
      let expected_types = ["connections", "env", "mask", "port", "protocol", "role", "tags", "target", "subnet"];
      expect(types).toEqual(expected_types);
    });
  });
  describe("private.createSubnetFilterRow", function () {});
  describe("private.createMaskFilterRow", function () {});
  describe("private.createRoleFilterRow", function () {});
  describe("private.createEnvFilterRow", function () {});
  describe("private.createPortFilterRow", function () {});
  describe("private.createProtocolFilterRow", function () {});
  describe("private.createTagFilterRow", function () {});
  describe("private.createTargetFilterRow", function () {});
  describe("private.createConnectionsFilterRow", function () {});
  describe("private.markupBoilerplate", function () {});
  describe("private.markupSelection", function () {});
  describe("private.markupTags", function () {});
  describe("private.markupInput", function () {});
  describe("private.markupSpan", function () {});
  describe("private.dsCallback", function () {});
  describe("private.addCallback", function () {
    it("works normally", function () {
      let div = document.createElement("DIV");
      let button = document.createElement("BUTTON");
      let icon = document.createElement("I");
      let selector_div = document.createElement("DIV");
      let selector_input = document.createElement("INPUT");
      let garbage_div = document.createElement("DIV");
      let garbage_input = document.createElement("INPUT");
      button.appendChild(icon);
      selector_div.appendChild(selector_input);
      garbage_div.appendChild(garbage_input);
      div.appendChild(button);
      div.appendChild(selector_div);
      div.appendChild(garbage_div);

      selector_input.value = "protocol";
      garbage_input.value = "wrong";
      mock_event = {target: icon};
      mock_event2 = {target: button};
      spyOn(filters.private, "extractRowValues").and.returnValue(["mock_params"]);
      spyOn(filters, "addFilter");
      spyOn(filters, "updateDisplay");
      
      filters.private.addCallback(mock_event);
      expect(filters.private.extractRowValues).toHaveBeenCalled();
      expect(filters.addFilter).toHaveBeenCalledWith("protocol", ["mock_params"]);
      
      filters.private.addCallback(mock_event2);
      expect(filters.private.extractRowValues).toHaveBeenCalled();
      expect(filters.addFilter).toHaveBeenCalledWith("protocol", ["mock_params"]);
    });
  });
  describe("private.deleteCallback", function () {});
  describe("private.updateEvent", function () {});
  describe("private.getRowIndex", function () {});
  describe("private.extractRowValues", function () {});
  describe("private.writeSummary", function () {
    it("summarizes connections", function () {
      filter = {type: "connections", direction: "i", comparator: "<", limit: "50"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("<50 conns/s (in)");
      filter = {type: "connections", direction: "o", comparator: ">", limit: "60"};
      expect(filters.private.writeSummary(filter).innerText).toEqual(">60 conns/s (out)");
      filter = {type: "connections", direction: "c", comparator: ">", limit: "60"};
      expect(filters.private.writeSummary(filter).innerText).toEqual(">60 conns/s (in+out)");
    });
    it("summarizes subnet", function () {
      filter = {type: "subnet", subnet: "24"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("subnet /24");
    });
    it("summarizes mask", function () {
      filter = {type: "mask", mask: "192.168.0.0/16"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("subnet 192.168.0.0/16");
    });
    it("summarizes port", function () {
      filter = {type: "port", port: "443", connection: "0"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("conn to (443)");
      filter = {type: "port", port: "443", connection: "1"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("no conn to (443)");
      filter = {type: "port", port: "443", connection: "2"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("conn from (443)");
      filter = {type: "port", port: "443", connection: "3"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("no conn from (443)");
    });
    it("summarizes protocol", function () {
      filter = {type: "protocol", protocol: "TCP", handles: "0"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("TCP in");
      filter = {type: "protocol", protocol: "TCP", handles: "1"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("no TCP in");
      filter = {type: "protocol", protocol: "TCP", handles: "2"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("TCP out");
      filter = {type: "protocol", protocol: "TCP", handles: "3"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("no TCP out");
    });
    it("summarizes target", function () {
      filter = {type: "target", target: "10.20.30.40", to: "0"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("to 10.20.30.40");
      filter = {type: "target", target: "10.20.30.40", to: "1"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("not to 10.20.30.40");
      filter = {type: "target", target: "10.20.30.40", to: "2"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("from 10.20.30.40");
      filter = {type: "target", target: "10.20.30.40", to: "3"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("not from 10.20.30.40");
    });
    it("summarizes tags", function () {
      filter = {type: "tags", tags: "A,B", has: "1"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("tagged (A,B)");
      filter = {type: "tags", tags: "A,B", has: "0"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("no tag (A,B)");
    });
    it("summarizes env", function () {
      filter = {type: "env", env: "spleen"};
      expect(filters.private.writeSummary(filter).innerText).toEqual("env: spleen");
    });
    it("summarizes role", function () {
      filter = {type: "role", comparator: ">", ratio: "0.248"};
      expect(filters.private.writeSummary(filter).innerText).toEqual(">25% server");
    });
  });
  describe("private.updateSummary", function () {});
  describe("private.dropKeys", function () {
    it("doesn't affect the original object list", function () {
      let test = [
        {a: 11, b: 21, c: 31},
        {a: 12, b: 22, c: 32},
        {a: 13, b: 23, c: 33},
        {a: 14, b: 24, c: 34}
      ];
      let actual = filters.private.dropKeys(test, ["b"]);
      expect(Object.keys(actual[0])).not.toContain("b");
      expect(Object.keys(actual[1])).not.toContain("b");
      expect(Object.keys(actual[2])).not.toContain("b");
      expect(Object.keys(actual[3])).not.toContain("b");
      expect(Object.keys(test[0])).toContain("b");
      expect(Object.keys(test[1])).toContain("b");
      expect(Object.keys(test[2])).toContain("b");
      expect(Object.keys(test[3])).toContain("b");
    });
    it("works with multiple drop keys", function () {
      let test = [
        {a: 11, b: 21, c: 31},
        {a: 12, b: 22, c: 32},
        {a: 13, b: 23, c: 33},
        {a: 14, b: 24, c: 34}
      ];

      actual = filters.private.dropKeys(test, ["b", "c"]);
      expect(actual[0]).toEqual({a: 11});
      expect(actual[1]).toEqual({a: 12});
      expect(actual[2]).toEqual({a: 13});
      expect(actual[3]).toEqual({a: 14});
    });
  });
  describe("private.encodeFilters", function () {
    it("encodes all types", function () {
      filters.ds = "ds5";

      filters.filters = [];
      filters.addFilter("connections", [">", "i", "300"]);
      let input = filters.private.dropKeys(filters.filters, ["html"]);
      let expected = "ds5|0;1;>;i;300";
      let actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("env", ["production"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|1;1;production";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("mask", ["192.168.0.0/16"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|2;1;192.168.0.0/16";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("port", ["1", "443"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|3;1;1;443";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("protocol", ["0", "TCP"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|4;1;0;TCP";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("role", [">", "0.75"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|5;1;>;0.75";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("tags", ["1", "64GB"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|7;1;1;64GB";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("target", ["10.20.30.40", "0"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|8;1;10.20.30.40;0";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);

      filters.filters = [];
      filters.addFilter("subnet", ["24"]);
      input = filters.private.dropKeys(filters.filters, ["html"]);
      expected = "ds5|6;1;24";
      actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);
    });
    it("encodes multiple filters", function () {
      filters.ds = "ds5";
      filters.filters = [];
      filters.addFilter("connections", [">", "i", "300"]);
      filters.addFilter("target", ["10.20.30.40", "0"]);
      filters.addFilter("subnet", ["24"]);
      let input = filters.private.dropKeys(filters.filters, ["html"]);
      let expected = "ds5|0;1;>;i;300|8;1;10.20.30.40;0|6;1;24";
      let actual = filters.private.encodeFilters(input);
      expect(actual).toEqual(expected);
    })
  });
  describe("private.decodeFilters", function () {});
  describe("private.createFilterCreator", function () {});
});