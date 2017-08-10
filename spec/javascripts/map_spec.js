describe("map.js file", function () {  
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
      expect(cfg).toContain('filter');
      expect(cfg).toContain('tmin');
      expect(cfg).toContain('tmax');
      expect(cfg).toContain('tstart');
      expect(cfg).toContain('tend');
      expect(cfg).toContain('protocol');
      expect(cfg).toContain('initial_zoom');
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

  describe("get_view_center", function () {
    beforeEach(function () {
      viewrect = { x: 0, y: 58, width: 959, height: 555, top: 58, right: 959, bottom: 613, left: 0 };
    });
    it("untransformed", function () {
      expect(get_view_center(viewrect, 0, 0, 1)).toEqual({x: viewrect.width / 2, y: viewrect.height / 2});
    });
    it("translated", function () {
      let x = viewrect.width / 2;
      let y = viewrect.height / 2;
      expect(get_view_center(viewrect, x, y, 1)).toEqual({x: 0, y: 0});
      expect(get_view_center(viewrect, x - 100, y - 100, 1)).toEqual({x: 100, y: 100});
      expect(get_view_center(viewrect, x + 100, y + 100, 1)).toEqual({x: -100, y: -100});
    });
    it("scaled", function () {
      let x = viewrect.width / 2;
      let y = viewrect.height / 2;
      let scale = 0.5;
      expect(get_view_center(viewrect, x, y, 1)).toEqual({x: 0, y: 0});
      expect(get_view_center(viewrect, x - 100, y - 100, scale)).toEqual({x: 200, y: 200});
      expect(get_view_center(viewrect, x + 100, y + 100, scale)).toEqual({x: -200, y: -200});
      scale = 2;
      expect(get_view_center(viewrect, x, y, 1)).toEqual({x: 0, y: 0});
      expect(get_view_center(viewrect, x - 100, y - 100, scale)).toEqual({x: 50, y: 50});
      expect(get_view_center(viewrect, x + 100, y + 100, scale)).toEqual({x: -50, y: -50});
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

  describe("normalize_addr", function () {
    it("doesn't change good addrs", function () {
      expect(normalize_addr("192.168.100.101/32")).toEqual("192.168.100.101/32");
      expect(normalize_addr("192.168.0.0/32")).toEqual("192.168.0.0/32");
      expect(normalize_addr("192.168.0.0/16")).toEqual("192.168.0.0/16");
    });
    it("pads zeroes", function () {
      expect(normalize_addr("192/32")).toEqual("192.0.0.0/32");
      expect(normalize_addr("192/24")).toEqual("192.0.0.0/24");
      expect(normalize_addr("192/16")).toEqual("192.0.0.0/16");
      expect(normalize_addr("192/8")).toEqual("192.0.0.0/8");
      expect(normalize_addr("192")).toEqual("192.0.0.0/8");
    });
    it("works without subnet", function () {
      expect(normalize_addr("192")).toEqual("192.0.0.0/8");
      expect(normalize_addr("192.168")).toEqual("192.168.0.0/16");
      expect(normalize_addr("192.168.0")).toEqual("192.168.0.0/24");
      expect(normalize_addr("192.168.0.1")).toEqual("192.168.0.1/32");
    });
  });

  describe("generic_ajax_failure", function () {});
  describe("generic_ajax_success", function () {});
  describe("ip_ntos", function () {
    it("converts", function () {
      expect(ip_ntos(16909060)).toEqual("1.2.3.4");
      expect(ip_ntos(4026531840)).toEqual("240.0.0.0");
      expect(ip_ntos(4042388211)).toEqual("240.241.242.243");
    });
  });

  describe("checkLoD", function () {});
});

xdescribe("controller", function () {
  describe("init", function () {});
  describe("init_buttons", function () {});
  describe("init_demo", function () {});
  describe("init_window", function () {});
  describe("GET_settings", function () {});
  
  describe("import_settings", function () {
    it("sets variables", function () {
      settings = {
        "color_bg":11206621,
        "color_node":5592524,
        "color_tcp":5592524,
        "color_udp":13391189,
        "color_error":10053222,
        "color_label":0,
        "color_label_bg":16777215,
        "datasources":{
          "3":{
            "flat":0,
            "name":"default",
            "ar_active":0,
            "ar_interval":300,
            "id":3,
            "subscription":1
          },
          "7":{
            "flat":0,
            "name":"seventh",
            "ar_active":1,
            "ar_interval":300,
            "id":7,
            "subscription":1
          }
        },
        "datasource":7,
        "subscription":1
      };
      controller.import_settings(settings);
      expect(controller.dsid).toEqual(7);
      expect(controller.datasource).toEqual(settings["datasources"]["7"]);
      expect(controller.autorefresh).toBe(true);
      settings["datasource"] = 3;
      controller.import_settings(settings);
      expect(controller.dsid).toEqual(3);
      expect(controller.datasource).toEqual(settings["datasources"]["3"]);
      expect(controller.autorefresh).toBe(false);
    })
  });
  
  describe("GET_timerange", function () {});
  
  describe("import_timerange", function () {
    beforeEach(function () {
      spyOn(window, "slider_init");
    })
    it("window is 300s", function () {
      controller.import_timerange({min: 1000, max: 1000});
      expect(config.tend - config.tstart).toEqual(300);
      controller.import_timerange({min: 1000, max: 2000});
      expect(config.tend - config.tstart).toEqual(300);
      expect(slider_init).toHaveBeenCalledTimes(2);
    });
    it("range is at least 300s", function () {
      range = {min: 1000, max: 1000}
      controller.import_timerange(range);
      expect(config.tmax).toEqual(1000);
      expect(config.tmin).toEqual(700);

      range = {min: 1000, max: 2000}
      controller.import_timerange(range);
      expect(config.tmax).toEqual(2000);
      expect(config.tmin).toEqual(1000);
      expect(slider_init).toHaveBeenCalledTimes(2);
    });
  });
  
  describe("event_to_tag", function () {
    it("works both ways", function () {
      let div = {tagName: "DIV"};
      let button = {tagName: "BUTTON", parentElement: div};
      let header = {tagName: "H4", parentElement: button};
      let optA = {target: button};
      let optB = {target: header};
      let objA = controller.event_to_tag(optA, "BUTTON");
      let objB = controller.event_to_tag(optB, "BUTTON");
      expect(objA.tagName).toEqual("BUTTON");
      expect(objB.tagName).toEqual("BUTTON");
    });
  });
  
  describe("event_datasource", function () {});
  describe("event_auto_refresh", function () {});
  describe("event_line_width", function () {});
  describe("event_show_buttons", function () {});
  describe("event_layout_mode", function () {});
  describe("event_layout_arrangement", function () {});
});

xdescribe("map", function () {
  beforeEach(function () {
    map = map_settings;
  });
  describe("reset", function () {
    it("resets the object", function () {
      map.structure = {"any": "thing", "can": "go", "in": "here"};
      map.reset();
      let keys = Object.keys(map.structure);
      expect(keys).toContain("objects");
      expect(map.structure.objects.length).toEqual(0);
      expect(keys).toContain("children");
      expect(Object.keys(map.structure.children).length).toEqual(0);
    })
  });
  describe("clear_html", function () {});
  describe("make_html", function () {});
  describe("init_accordion", function () {});
  describe("rebuild", function () {});
  
  describe("add_category", function () {
    it("adds a category if missing", function () {
      map.reset();
      map.add_category("cat1");
      map.add_category("cat2");
      map.add_category("cat3");
      map.add_category("cat2");
      map.add_category("cat1");
      map.add_category("cat2");
      let cats = Object.keys(map.structure.children);
      cats.sort();
      expect(cats).toEqual(["cat1", "cat2", "cat3"]);
    });
  });
  
  describe("add_subcategory", function () {
    it("adds when needed", function () {
      map.reset();
      map.add_subcategory("cat1", "sc1");
      map.add_subcategory("cat2", "sc2");
      map.add_subcategory("cat1", "sc3");
      map.add_subcategory("cat2", "sc4");
      map.add_subcategory("cat1", "sc1");
      map.add_subcategory("cat2", "sc2");
      let cats = Object.keys(map.structure.children).sort();
      expect(cats).toEqual(["cat1", "cat2"]);
      let subcat1 = Object.keys(map.structure.children.cat1.children).sort();
      expect(subcat1).toEqual(["sc1", "sc3"]);
      let subcat2 = Object.keys(map.structure.children.cat2.children).sort();
      expect(subcat2).toEqual(["sc2", "sc4"]);
    });
  });
  
  describe("add_object", function () {
    it("creates heirarchy", function () {
      map.reset();
      let objA = {"a": 1};
      let objB = {"b": 3};
      let objC = {"c": 9};
      let objD = {"d": 27};
      map.add_object("cat1", "sc1", objA);
      map.add_object("cat2", "sc2", objB);
      map.add_object("cat1", "sc3", objC);
      map.add_object("cat2", "sc4", objD);
      let cats = Object.keys(map.structure.children).sort();
      expect(cats).toEqual(["cat1", "cat2"]);
      let subcat1 = Object.keys(map.structure.children.cat1.children).sort();
      expect(subcat1).toEqual(["sc1", "sc3"]);
      let subcat2 = Object.keys(map.structure.children.cat2.children).sort();
      expect(subcat2).toEqual(["sc2", "sc4"]);
      expect(map.structure.children.cat1.children.sc1.objects).toEqual([objA]);
      expect(map.structure.children.cat1.children.sc3.objects).toEqual([objC]);
      expect(map.structure.children.cat2.children.sc2.objects).toEqual([objB]);
      expect(map.structure.children.cat2.children.sc4.objects).toEqual([objD]);
    });
    it("if needed", function () {
      map.reset();
      let objA = {"a": 1};
      let objB = {"b": 3};
      let objC = {"c": 9};
      let objD = {"d": 27};
      map.add_object(null, null, objA);
      map.add_object(null, "sc1", objB);
      map.add_object("cat1", null, objC);
      map.add_object("cat1", "sc1", objD);
      expect(map.structure.objects).toEqual([objA]);
      expect(map.structure.children.sc1.objects).toEqual([objB]);
      expect(map.structure.children.cat1.objects).toEqual([objC]);
      expect(map.structure.children.cat1.children.sc1.objects).toEqual([objD]);
    })
  });
  
  describe("create_labeliconbutton", function () {
    it("returns a button", function () {
      let btn = map.create_labeliconbutton("id1", "lock", "Secure", "click me", true, null);
      expect(btn.tagName).toEqual("BUTTON");
    })
  });
  describe("create_iconbutton", function () {
    it("returns a button", function () {
      let btn = map.create_iconbutton("id1", "lock", "click me", true, null);
      expect(btn.tagName).toEqual("BUTTON");
    })
  });
  describe("create_labelbutton", function () {
    it("returns a button", function () {
      let btn = map.create_labelbutton("id1", "Secure", "click me", true, null);
      expect(btn.tagName).toEqual("BUTTON");
    })
  });
  describe("create_divider", function () {});
  describe("btn_toggleable", function () {});
  describe("create_buttongroup", function () {});
  describe("create_input", function () {});
  describe("init", function () {});
});