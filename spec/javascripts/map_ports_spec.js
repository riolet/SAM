describe("map_ports.js file", function () {
  describe("ports.loaded", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });
    it("exists", function () {
      expect(ports.loaded(443)).toEqual(true)
    });
    it("doesn't exist", function () {
      expect(ports.loaded(444)).toEqual(false)
    });
    it("is disabled", function () {
      expect(ports.loaded(8081)).toEqual(true)
    });
  });


  describe("ports.get_name", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });
    it("doesn't exist", function () {
      expect(ports.get_name(444)).toEqual("444");
    });
    it("exists", function () {
      expect(ports.get_name(443)).toEqual("443 - https");
    });
    it("has an alias", function () {
      expect(ports.get_name(3268)).toEqual("3268 - other name");
    });
    it("is disabled", function () {
      expect(ports.get_name(8081)).toEqual("8081")
    });
  });


  describe("ports.get_alias", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });
    it("doesn't exist", function () {
      expect(ports.get_alias(444)).toEqual("444");
    });
    it("exists", function () {
      expect(ports.get_alias(443)).toEqual("https");
    });
    it("has an alias", function () {
      expect(ports.get_alias(3268)).toEqual("other name");
    });
    it("is disabled", function () {
      expect(ports.get_alias(8081)).toEqual("8081")
    });
  });


  describe("ports.get_description", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });
    it("doesn't exist", function () {
      expect(ports.get_description(444)).toEqual("");
    });
    it("exists", function () {
      expect(ports.get_description(443)).toEqual("http protocol over TLS/SSL");
    });
    it("has an alias", function () {
      expect(ports.get_description(3268)).toEqual("other description");
    });
    it("is disabled", function () {
      expect(ports.get_description(8081)).toEqual("")
    });
  });


  describe("ports.get_protocols", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });
    it("doesn't exist", function () {
      expect(ports.get_protocols(444)).toEqual("");
    });
    it("exists", function () {
      expect(ports.get_protocols(443)).toEqual("UDP,SCTP,TCP")
    });
  });


  describe("ports.get_presentation", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });
    it("doesn't exist", function () {
      let link = ports.get_presentation(444);
      expect(link.outerHTML).toEqual("<a>444</a>");
      expect(typeof(link.onclick)).toBe("function");
    });
    it("exists", function () {
      let link = ports.get_presentation(443);
      expect(link.outerHTML).toEqual("<a data-tooltip=\"http protocol over TLS/SSL\">443 - https</a>")
      expect(typeof(link.onclick)).toBe("function");
    });
    it("has alias", function () {
      let link = ports.get_presentation(3268);
      expect(link.outerHTML).toEqual("<a data-tooltip=\"other description\">3268 - other name</a>")
      expect(typeof(link.onclick)).toBe("function");
    });
    it("is disabled", function () {
      let link = ports.get_presentation(8081);
      expect(link.outerHTML).toEqual("<a>8081</a>")
      expect(typeof(link.onclick)).toBe("function");
    });
  })


  describe("ports.set", function () {
    beforeEach(function () {
      get_mock_m_ports();
    });
    it("creates new port", function () {
      expect(ports.get_alias(4)).toEqual("4");
      expect(ports.get_description(4)).toEqual("");

      var new_port = {
        active: 1,
        name: "name1",
        description: "desc1",
        alias_name: "name2",
        alias_description: "desc2",
      };
      ports.set(4, new_port);
      expect(ports.get_alias(4)).toEqual("name2");
      expect(ports.get_description(4)).toEqual("desc2");
    });
    it("update existing port", function () {
      expect(ports.get_alias(443)).toEqual("https");
      expect(ports.get_description(443)).toEqual("http protocol over TLS/SSL");

      var new_port = {
        active: 1,
        name: "name1",
        description: "desc1",
        alias_name: "name2",
        alias_description: "desc2",
      };
      ports.set(443, new_port);

      expect(ports.get_alias(443)).toEqual("name2");
      expect(ports.get_description(443)).toEqual("desc2");
    });
  });


  describe("ports.request_add", function () {
    beforeEach(function () {
      get_mock_m_ports();
      ports.private.requests = [];
    });
    it("add simple", function () {
      ports.request_add(47);
      ports.request_add(48);
      ports.request_add(49);
      ports.request_add(50);
      expect(ports.private.requests).toEqual([47,48,49,50]);
    });
    it("add duplicates", function () {
      ports.request_add(47);
      ports.request_add(47);
      ports.request_add(47);
      ports.request_add(50);
      expect(ports.private.requests).toEqual([47,47,47,50]);
    });
    it("add existing", function () {
      ports.request_add(7680);
      ports.request_add(3268);
      ports.request_add(443);
      ports.request_add(50);
      expect(ports.private.requests).toEqual([50]);
    });
  });


  describe("ports.request_submit", function () {
    beforeEach(function () {
      get_mock_m_ports();
      spyOn(ports, "GET_portinfo");
    });

    it("removes duplicates mid", function () {
      ports.private.requests = [40, 47, 47, 47, 50];
      ports.request_submit();
      expect(ports.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(ports.GET_portinfo).toHaveBeenCalledWith([40, 47, 50], undefined);
    });
    it("removes duplicates start", function () {
      ports.private.requests = [47, 47, 47, 40, 50];
      ports.request_submit();
      expect(ports.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(ports.GET_portinfo).toHaveBeenCalledWith([40, 47, 50], undefined);
    });
    it("removes duplicates end", function () {
      ports.private.requests = [40, 50, 47, 47, 47];
      ports.request_submit();
      expect(ports.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(ports.GET_portinfo).toHaveBeenCalledWith([40, 47, 50], undefined);
    });

    it("removes already loaded ports", function () {
      ports.private.requests = [443, 3268, 50, 7680, 8081];
      ports.request_submit();
      expect(ports.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(ports.GET_portinfo).toHaveBeenCalledWith([50], undefined);
    });

    it("doesn't fire empty requests", function () {
      ports.private.requests = [443, 3268, 7680, 8081];
      ports.request_submit();
      ports.private.requests = [443, 443, 443, 443];
      ports.request_submit();
      expect(ports.GET_portinfo).not.toHaveBeenCalled();
    });
  });
  
  
  describe("show_edit_window", function () {
    beforeEach(function () {
      get_mock_m_ports();
      pa_id = document.createElement("input");
      pa_id.type = "checkbox";
      pnum_id = document.createElement("span");
      p_proto = document.createElement("span");
      pn_id = document.createElement("td");
      pd_id = document.createElement("td");
      pan_id = document.createElement("input");
      pan_id.type = "text";
      pad_id = document.createElement("input");
      pad_id.type = "text";
      document.getElementById = function(query) {
        if (query === "port_name") { return pn_id; }
        if (query === "port_active") { return pa_id; }
        if (query === "port_number") { return pnum_id; }
        if (query === "port_protocols") { return p_proto; }
        if (query === "port_alias_name") { return pan_id; }
        if (query === "port_description") { return pd_id; }
        if (query === "port_alias_description") { return pad_id; }
      };
      spyOn(ports, "GET_portinfo");
      spyOn(ports.private, "edit");
    });
    it("loaded", function () {
      ports.show_edit_window(443);
      expect(ports.GET_portinfo).not.toHaveBeenCalled();
      expect(ports.private.edit).toHaveBeenCalled();
    });
    it("not loaded", function () {
      ports.show_edit_window(444);
      expect(ports.GET_portinfo).toHaveBeenCalled();
      expect(ports.private.edit).not.toHaveBeenCalled();
    });
  });


  describe("ports.POST_portinfo", function () {
    beforeEach(function () {
      spyOn($, "ajax");
    });
    it("sends all request data", function () {
      ports.POST_portinfo({'a': '123', 'b': '456'})
      let expected = {
        url: "./portinfo",
        type: "POST",
        data: {'a': '123', 'b': '456'},
        error: generic_ajax_failure,
        success: generic_ajax_success
      };
      expect($.ajax).toHaveBeenCalledWith(expected);
    });
  });


  //don't know how to test this.
  describe("ports.GET_portinfo", function () {
    beforeEach(function () {
      spyOn($, "ajax")
    })
    it("doesn't run with zero ports", function () {
      ports.GET_portinfo([]);
      expect($.ajax).not.toHaveBeenCalled();
    });
    it("runs ajax", function () {
      ports.GET_portinfo([443]);
      expect($.ajax).toHaveBeenCalledTimes(1);
    });
  });


  describe("ports.private.GET_response", function () {
    beforeEach(function () {
      get_mock_m_ports();
      ports.private.requests = [];
    });
    it("adds new ports", function () {
      results = {
        "389": {"protocols": "UDP,TCP", "description": "Lightweight Directory Access Protocol", "active": 1, "alias_name": "ldap", "port": 389, "alias_description": "Lightweight Directory Access Protocol", "name": "ldap"}, 
      };
      expect(ports.ports[389]).toBe(undefined);
      ports.private.GET_response(results)
      expect(ports.ports[389]).toEqual(results["389"]);
    });
    it("updates existing ports", function () {
      results = {
        "445": {"protocols": "UDP,TCP", "description": "Microsoft-DS", "active": 1, "alias_name": "microsoft-", "port": 445, "alias_description": "Microsoft-DS", "name": "microsoft-"}
      };
      expect(ports.ports[445]).toBe(undefined);
      ports.private.GET_response(results)
      expect(ports.ports[445]).toEqual(results["445"]);
      results2 = {
        "445": {"protocols": "AB", "description": "CD", "active": 1, "alias_name": "EF", "port": 445, "alias_description": "GH", "name": "IJ"}
      };
      ports.private.GET_response(results2)
      expect(ports.ports[445]).toEqual(results2["445"]);
    });
  });


  describe("ports.private.click", function () {
    beforeEach(function () {
      link = document.createElement("a");
      link.onclick = ports.private.click;
      spyOn(ports, "show_edit_window");

      link.innerHTML = "443 - https";
      link.click();

      link.innerHTML = "444";
      link.click();

      link.innerHTML = "12345 - rainbow";
      link.click();
    });
    it("show_window is called", function () {
      expect(ports.show_edit_window).toHaveBeenCalledTimes(3);
    });
    it("extracts args", function () {
      expect(ports.show_edit_window).toHaveBeenCalledWith(443);
      expect(ports.show_edit_window).toHaveBeenCalledWith(444);
      expect(ports.show_edit_window).toHaveBeenCalledWith(12345);
    });
  });

  
  describe("ports.private.save", function () {
    beforeEach(function () {
      get_mock_m_ports();
      m_portinfo = {};
      pa_id = document.createElement("input");
      pa_id.type = "checkbox";
      pnum_id = document.createElement("span");
      p_proto = document.createElement("span");
      pn_id = document.createElement("td");
      pd_id = document.createElement("td");
      pan_id = document.createElement("input");
      pan_id.type = "text";
      pad_id = document.createElement("input");
      pad_id.type = "text";
      document.getElementById = function(query) {
        if (query === "port_name") { return pn_id; }
        if (query === "port_active") { return pa_id; }
        if (query === "port_number") { return pnum_id; }
        if (query === "port_protocols") { return p_proto; }
        if (query === "port_alias_name") { return pan_id; }
        if (query === "port_description") { return pd_id; }
        if (query === "port_alias_description") { return pad_id; }
      };
      set_to = function(test_port) {
        "use strict";
        pnum_id.innerHTML = test_port;
        ports.private.edit(test_port, ports.ports[test_port]);
      };
      spyOn(ports, "POST_portinfo");
    });

    it("doesn't get called with no changes.", function () {
      set_to(3268);
      ports.private.save();
      expect(ports.POST_portinfo).not.toHaveBeenCalled();
    });
    it("gets called when 'active' changes.", function () {
      set_to(3268);
      pa_id.checked = false;
      ports.private.save();
      expect(ports.POST_portinfo).toHaveBeenCalled();
      var changes = {port: 3268, active: 0};
      expect(ports.ports[3268].active).toEqual(0);
      expect(ports.POST_portinfo).toHaveBeenCalledWith(changes);
    });
    it("gets called when 'alias_name' changes.", function () {
      set_to(3268);
      pan_id.value = "new_alias";
      ports.private.save();
      expect(ports.POST_portinfo).toHaveBeenCalled();
      var changes = {port: 3268, alias_name: "new_alias"};
      expect(ports.ports[3268].alias_name).toEqual("new_alias");
      expect(ports.POST_portinfo).toHaveBeenCalledWith(changes);

    });
    it("gets called when 'alias_description' changes.", function () {
      set_to(3268);
      pad_id.value = "new_desc";
      ports.private.save();
      expect(ports.POST_portinfo).toHaveBeenCalled();
      var changes = {port: 3268, alias_description: "new_desc"};
      expect(ports.ports[3268].alias_description).toEqual("new_desc");
      expect(ports.POST_portinfo).toHaveBeenCalledWith(changes);
    });
  });


  describe("ports.private.edit", function () {
    beforeEach(function () {
      get_mock_m_ports();
      pa_id = document.createElement("input");
      pa_id.type = "checkbox";
      pnum_id = document.createElement("span");
      p_proto = document.createElement("span");
      pn_id = document.createElement("td");
      pd_id = document.createElement("td");
      pan_id = document.createElement("input");
      pan_id.type = "text";
      pad_id = document.createElement("input");
      pad_id.type = "text";
      document.getElementById = function(query) {
        if (query === "port_name") { return pn_id; }
        if (query === "port_active") { return pa_id; }
        if (query === "port_number") { return pnum_id; }
        if (query === "port_protocols") { return p_proto; }
        if (query === "port_alias_name") { return pan_id; }
        if (query === "port_description") { return pd_id; }
        if (query === "port_alias_description") { return pad_id; }
      };
      set_to = function(test_port) {
        "use strict";
        pnum_id.innerHTML = test_port;
        ports.private.edit(test_port, ports.ports[test_port]);
      };
    });
    it("sets div values (exists)", function () {
      "use strict";
      ports.private.edit(3268, ports.ports[3268]);
      expect(pa_id.checked).toEqual(true);
      expect(pn_id.innerHTML).toEqual("msft-gc");
      expect(pd_id.innerHTML).toEqual("Microsoft Global Catalog");
      expect(pan_id.value).toEqual("other name");
      expect(pad_id.value).toEqual("other description");
    });
    it("sets div values (unaliased)", function () {
      "use strict";
      ports.private.edit(8081, ports.ports[8081]);
      expect(pa_id.checked).toEqual(false);
      expect(pn_id.innerHTML).toEqual("sunproxyad");
      expect(pd_id.innerHTML).toEqual("Sun Proxy Admin Service");
      expect(pan_id.value).toEqual("");
      expect(pad_id.value).toEqual("");
    });
    it("sets div values (not exists)", function () {
      "use strict";
      ports.private.edit(4, ports.ports[4]);
      expect(pa_id.checked).toEqual(true);
      expect(pn_id.innerHTML).toEqual("none");
      expect(pd_id.innerHTML).toEqual("none");
      expect(pan_id.value).toEqual("");
      expect(pad_id.value).toEqual("");
    });
  });
});
