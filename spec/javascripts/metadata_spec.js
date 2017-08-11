xdescribe("metadata.js file", function () {
  describe("normalizeIP", function () {
    it("works with short IPs", function () {
      expect(normalizeIP("110")).toEqual("110.0.0.0/8");
      expect(normalizeIP("110.23")).toEqual("110.23.0.0/16");
      expect(normalizeIP("110.23.45")).toEqual("110.23.45.0/24");
      expect(normalizeIP("110.23.45.67")).toEqual("110.23.45.67/32");
    });
    it("works with subnets", function () {
      expect(normalizeIP("110.23.45.67/8")).toEqual("110.0.0.0/8");
      expect(normalizeIP("110.23.45.67/16")).toEqual("110.23.0.0/16");
      expect(normalizeIP("110.23.45.67/24")).toEqual("110.23.45.0/24");
      expect(normalizeIP("110.23.45.67/32")).toEqual("110.23.45.67/32");
    });
  });
  describe("getIP_Subnet", function () {});
  describe("minimizeIP", function () {
    it("drops extras", function () {
      expect(minimizeIP("12.34.56.78")).toEqual("12.34.56.78");
      expect(minimizeIP("12.34.56.78/32")).toEqual("12.34.56.78");
      expect(minimizeIP("12.34.56.78/24")).toEqual("12.34.56");
      expect(minimizeIP("12.34.56.78/16")).toEqual("12.34");
      expect(minimizeIP("12.34.56.78/8")).toEqual("12");
    });
  });
  describe("dsCallback", function () {});
  describe("writeHash", function () {});
  describe("readHash", function () {});

  
  describe("buildKeyValueRow", function () {
    it("creates a table row", function () {
      let tr = buildKeyValueRow("key1", "value1");
      expect(tr.tagName).toEqual("TR");
      expect(tr.childNodes.length).toEqual(2);
    });
    it("handles values", function () {
      let tr = buildKeyValueRow("key1", "value1");
      expect(tr.children[0].innerText).toEqual("key1");
      expect(tr.children[1].innerText).toEqual("value1");
      tr = buildKeyValueRow("key1", null);
      expect(tr.children[0].innerText).toEqual("key1");
      expect(tr.children[1].innerText).toEqual("null");
      tr = buildKeyValueRow("key1", undefined);
      expect(tr.children[0].innerText).toEqual("key1");
      expect(tr.children[1].innerText).toEqual("undefined");
      tr = buildKeyValueRow("key1", 405);
      expect(tr.children[0].innerText).toEqual("key1");
      expect(tr.children[1].innerText).toEqual("405");
      let child = document.createElement("BUTTON");
      let td = document.createElement("TD");
      td.appendChild(child);
      tr = buildKeyValueRow("key1", td);
      expect(tr.children[0].innerText).toEqual("key1");
      expect(tr.children[1].children[0].tagName).toEqual("BUTTON");
    });
  });
  describe("buildKeyMultiValueRows", function () {
    it("sets rowSpan", function () {
      let key = "k1";
      let val = [12, 34, 56, 78];
      let rows = buildKeyMultiValueRows(key, val);
      expect(rows[0].children[0].rowSpan).toEqual(val.length);
    });
  });
  describe("build_link", function () {
    it("returns an anchor", function () {
      g_ds = 6;
      let anchor = build_link("189.59.134.0", 24);
      expect(anchor.tagName).toEqual("A");
      let expected = "/metadata#ip=189.59.134.0/24&ds=6";
      expect(anchor.href.endsWith(expected)).toBe(true);
    });
  });
  describe("build_role_text", function () {
    it("matchs spec", function () {
      expect(build_role_text(0)).toEqual("0.00 (" + strings.meta_role_cc + ")");
      expect(build_role_text(0.1)).toEqual("0.10 (" + strings.meta_role_c + ")");
      expect(build_role_text(0.2)).toEqual("0.20 (" + strings.meta_role_c + ")");
      expect(build_role_text(0.3)).toEqual("0.30 (" + strings.meta_role_c + ")");
      expect(build_role_text(0.4)).toEqual("0.40 (" + strings.meta_role_cs + ")");
      expect(build_role_text(0.5)).toEqual("0.50 (" + strings.meta_role_cs + ")");
      expect(build_role_text(0.6)).toEqual("0.60 (" + strings.meta_role_cs + ")");
      expect(build_role_text(0.7)).toEqual("0.70 (" + strings.meta_role_s + ")");
      expect(build_role_text(0.8)).toEqual("0.80 (" + strings.meta_role_s + ")");
      expect(build_role_text(0.9)).toEqual("0.90 (" + strings.meta_role_s + ")");
      expect(build_role_text(1)).toEqual("1.00 (" + strings.meta_role_ss + ")");
    });
  });
  describe("build_label_packetrate", function () {
    it("matches spec", function () {
      let b = build_label_packetrate;
      expect(b(1)).toEqual("1.00 p/s");
      expect(b(100)).toEqual("100.00 p/s");
      expect(b(10000)).toEqual("10.00 Kp/s");
      expect(b(1000000)).toEqual("1.00 Mp/s");
      expect(b(100000000)).toEqual("100.00 Mp/s");
      expect(b(10000000000)).toEqual("10.00 Gp/s");
      expect(b(1000000000000)).toEqual("1000.00 Gp/s");
    });
  });
  describe("build_table_children", function () {});
  describe("build_pagination", function () {});
  describe("build_label", function () {
    it("produces a label", function () {
      let label = build_label("mytext", "blue", false);
      expect(label.tagName).toEqual("SPAN");
      expect(label.innerText).toEqual("mytext");
      expect(label.classList.contains("blue")).toBe(true);
      expect(label.classList.contains("disabled")).toBe(false);
      label = build_label("mytext", "green", true);
      expect(label.tagName).toEqual("SPAN");
      expect(label.innerText).toEqual("mytext");
      expect(label.classList.contains("green")).toBe(true);
      expect(label.classList.contains("disabled")).toBe(true);
    });
  });
  describe("present_quick_info", function () {});
  describe("present_detailed_info", function () {});
  describe("clear_detailed_info", function () {});
  describe("clear_quick_info", function () {});
  
  
  describe("generic_ajax_failure", function () {});
  describe("header_sort_callback", function () {});
  describe("hostname_edit_callback", function () {});
  describe("tag_change_callback", function () {});
  describe("env_change_callback", function () {});
  describe("POST_tags", function () {});
  describe("GET_data", function () {});
  describe("GET_page_callback", function () {});
  describe("GET_page", function () {});
  describe("abortRequests", function () {});
  
  
  describe("StateChangeEvent", function () {
    it("creates a new object with state", function () {
      let evt = new StateChangeEvent({"s": "state1"});
      expect(evt.type).toEqual("stateChange");
      expect(evt.newState).toEqual({"s": "state1"});
    });
  });
  describe("dispatcher", function () {
    it("filters by type", function () {
      let foo = {
        bar: function () {
          return true;
        }
      }
      spyOn(foo, "bar");
      let good = {type: "stateChange", newState: foo.bar};
      let bad = {type: "notStateChange", newState: foo.bar};
      dispatcher(good);
      expect(foo.bar).toHaveBeenCalledTimes(1);
      dispatcher(bad);
      // it is not called a second time for bad.
      expect(foo.bar).toHaveBeenCalledTimes(1);
    });
    it("executes or errors", function () {
      let foo = {
        bar: function () {
          return true;
        },
        baz: "not a function"
      }
      spyOn(foo, "bar");
      let good = {type: "stateChange", newState: foo.bar};
      let bad = {type: "stateChange", newState: foo.baz};
      expect(dispatcher(good)).toBe(true);
      expect(dispatcher(bad)).toBe(false);
    });
  });
  describe("restartTypingTimer", function () {});
  describe("scanForPorts", function () {
    it("reads inputs", function () {
      let response = {
        outputs: {headers: [], rows: []},
        ports: {headers: [], rows: []},
        inputs: {
          headers: [["notport", "Not Port"], ["port", "Port"], ["alsonotport", "Also Not Port"]],
          rows: [
            [123, 456, 789],
            [122, 455, 788],
            [121, 454, 787]
          ]
        }
      };
      spyOn(ports, "request_submit");
      ports.private.requests = [];
      scanForPorts(response);
      expect(ports.private.requests).toEqual([456, 455, 454]);
      expect(ports.request_submit).toHaveBeenCalled();
    });
    it("reads outputs", function () {
      let response = {
        inputs: {headers: [], rows: []},
        ports: {headers: [], rows: []},
        outputs: {
          headers: [["notport", "Not Port"], ["port", "Port"], ["alsonotport", "Also Not Port"]],
          rows: [
            [123, 456, 789],
            [122, 455, 788],
            [121, 454, 787]
          ]
        }
      };
      spyOn(ports, "request_submit");
      ports.private.requests = [];
      scanForPorts(response);
      expect(ports.private.requests).toEqual([456, 455, 454]);
      expect(ports.request_submit).toHaveBeenCalled();
    });
    it("reads ports", function () {
      let response = {
        inputs: {headers: [], rows: []},
        outputs: {headers: [], rows: []},
        ports: {
          headers: [["notport", "Not Port"], ["port", "Port"], ["alsonotport", "Also Not Port"]],
          rows: [
            [123, 456, 789],
            [122, 455, 788],
            [121, 454, 787]
          ]
        }
      };
      spyOn(ports, "request_submit");
      ports.private.requests = [];
      scanForPorts(response);
      expect(ports.private.requests).toEqual([456, 455, 454]);
      expect(ports.request_submit).toHaveBeenCalled();
    });
  });
  describe("requestMoreDetails", function () {});
  describe("requestQuickInfo", function () {});
  describe("init", function () {});
});