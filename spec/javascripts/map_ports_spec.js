describe("map_ports.js file", function () {
  describe("port_loaded", function () {
    beforeEach(function () {
      m_ports = get_mock_m_ports()
    })
    it("exists", function () {
      expect(port_loaded(443)).toEqual(true)
    });
    it("doesn't exist", function () {
      expect(port_loaded(444)).toEqual(false)
    });
    it("is disabled", function () {
      expect(port_loaded(8081)).toEqual(true)
    });
  });


  describe("get_port_name", function () {
    beforeEach(function () {
      m_ports = get_mock_m_ports()
    })
    it("doesn't exist", function () {
      expect(get_port_name(444)).toEqual("444");
    });
    it("exists", function () {
      expect(get_port_name(443)).toEqual("443 - https");
    });
    it("has an alias", function () {
      expect(get_port_name(3268)).toEqual("3268 - other name");
    });
    it("is disabled", function () {
      expect(get_port_name(8081)).toEqual("8081")
    });
  });


  describe("get_port_alias", function () {
    beforeEach(function () {
      m_ports = get_mock_m_ports()
    })
    it("doesn't exist", function () {
      expect(get_port_alias(444)).toEqual("444");
    });
    it("exists", function () {
      expect(get_port_alias(443)).toEqual("https");
    });
    it("has an alias", function () {
      expect(get_port_alias(3268)).toEqual("other name");
    });
    it("is disabled", function () {
      expect(get_port_alias(8081)).toEqual("8081")
    });
  });


  describe("get_port_description", function () {
    beforeEach(function () {
      m_ports = get_mock_m_ports()
    })
    it("doesn't exist", function () {
      expect(get_port_description(444)).toEqual("");
    });
    it("exists", function () {
      expect(get_port_description(443)).toEqual("http protocol over TLS/SSL");
    });
    it("has an alias", function () {
      expect(get_port_description(3268)).toEqual("other description");
    });
    it("is disabled", function () {
      expect(get_port_description(8081)).toEqual("")
    });
  });


  describe("update_port", function () {
    beforeEach(function () {
      m_ports = get_mock_m_ports()
    })
    it("creates new port", function () {
      expect(get_port_alias(4)).toEqual("4");
      expect(get_port_description(4)).toEqual("");

      new_port = {
        active: 1,
        name: "name1",
        description: "desc1",
        alias_name: "name2",
        alias_description: "desc2",
      }
      update_port(4, new_port);
      expect(get_port_alias(4)).toEqual("name2");
      expect(get_port_description(4)).toEqual("desc2");
    });
    it("update existing port", function () {
      expect(get_port_alias(443)).toEqual("https");
      expect(get_port_description(443)).toEqual("http protocol over TLS/SSL");

      new_port = {
        active: 1,
        name: "name1",
        description: "desc1",
        alias_name: "name2",
        alias_description: "desc2",
      }
      update_port(443, new_port);

      expect(get_port_alias(443)).toEqual("name2");
      expect(get_port_description(443)).toEqual("desc2");
    });
  });


  describe("GET_portinfo_callback", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("port_click", function () {
    beforeEach(function () {
      link = document.createElement("a");
      link.onclick = port_click
      spyOn(window, "show_window");

      link.innerHTML = "443 - https";
      link.click();

      link.innerHTML = "444";
      link.click();

      link.innerHTML = "12345 - rainbow";
      link.click();
    });
    it("show_window is called", function () {
      expect(window.show_window).toHaveBeenCalledTimes(3);
    });
    it("extracts args", function () {
      expect(window.show_window).toHaveBeenCalledWith(443);
      expect(window.show_window).toHaveBeenCalledWith(444);
      expect(window.show_window).toHaveBeenCalledWith(12345);
    });
  });


  describe("port_request_add", function () {
    beforeEach(function () {
      m_ports = get_mock_m_ports();
      m_port_requests = [];
    });
    it("add simple", function () {
      port_request_add(47);
      port_request_add(48);
      port_request_add(49);
      port_request_add(50);
      expect(m_port_requests).toEqual([47,48,49,50]);
    });
    it("add duplicates", function () {
      port_request_add(47);
      port_request_add(47);
      port_request_add(47);
      port_request_add(50);
      expect(m_port_requests).toEqual([47,47,47,50]);
    });
    it("add existing", function () {
      port_request_add(7680);
      port_request_add(3268);
      port_request_add(443);
      port_request_add(50);
      expect(m_port_requests).toEqual([50]);
    });
  });


  describe("port_request_submit", function () {
    beforeEach(function () {
      m_ports = get_mock_m_ports();
      spyOn(window, "GET_portinfo");
    });

    it("removes duplicates mid", function () {
      m_port_requests = [40, 47, 47, 47, 50];
      port_request_submit();
      expect(window.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(window.GET_portinfo).toHaveBeenCalledWith([40, 47, 50]);
    });
    it("removes duplicates start", function () {
      m_port_requests = [47, 47, 47, 40, 50];
      port_request_submit();
      expect(window.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(window.GET_portinfo).toHaveBeenCalledWith([40, 47, 50]);
    });
    it("removes duplicates end", function () {
      m_port_requests = [40, 50, 47, 47, 47];
      port_request_submit();
      expect(window.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(window.GET_portinfo).toHaveBeenCalledWith([40, 47, 50]);
    });

    it("removes already loaded ports", function () {
      m_port_requests = [443, 3268, 50, 7680, 8081];
      port_request_submit();
      expect(window.GET_portinfo).toHaveBeenCalledTimes(1);
      expect(window.GET_portinfo).toHaveBeenCalledWith([50]);
    });

    it("doesn't fire empty requests", function () {
      m_port_requests = [443, 3268, 7680, 8081];
      port_request_submit();
      m_port_requests = [443, 443, 443, 443];
      port_request_submit();
      expect(window.GET_portinfo).not.toHaveBeenCalled();
    });
  });


  describe("port_save", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("show_window", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });


  describe("port_display", function () {
    it(" ", function () {
      expect(1).toEqual(1);
    });
  });
});
