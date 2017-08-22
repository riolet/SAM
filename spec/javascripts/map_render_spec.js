describe("map_render.js file", function () {
  describe("fadeFont", function () {
    it("works", function () {
      expect(fadeFont("#FFFFFF", 1.0)).toEqual("rgba(255,255,255,1)");
      expect(fadeFont("#706050", 0.25)).toEqual("rgba(112,96,80,0.25)");
    });
  });
  describe("color_links", function () {
    it("works", function () {
      let linkU = {"protocols": "UDP"};
      let linkT = {"protocols": "TCP"};
      let linkUT = {"protocols": "UDP,TCP"};
      let linkS = {"protocols": "SCP"};
      color_links([linkU, linkT, linkUT, linkS]);
      expect(linkU.color).toEqual(renderConfig.linkColorUdp);
      expect(linkU.color_faded).toEqual(renderConfig.linkColorUdpFaded);
      expect(linkT.color).toEqual(renderConfig.linkColorTcp);
      expect(linkT.color_faded).toEqual(renderConfig.linkColorTcpFaded);
      expect(linkUT.color).toEqual(renderConfig.linkColorUdpTcp);
      expect(linkUT.color_faded).toEqual(renderConfig.linkColorUdpTcpFaded);
      expect(linkS.color).toEqual(renderConfig.linkColorOther);
      expect(linkS.color_faded).toEqual(renderConfig.linkColorOtherFaded);
    });
  });
  describe("opacity", function () {
    it("works for nodes", function () {
      expect(opacity(8, "node", 0.0007)).toEqual(1);
      expect(opacity(8, "node", zLinks16)).toEqual(1);
      expect(opacity(8, "node", zLinks16*2)).toEqual(0);

      expect(opacity(24, "node", zNodes24)).toEqual(0);
      expect(opacity(24, "node", zNodes24*2)).toEqual(1);
      expect(opacity(24, "node", zLinks32)).toEqual(1);
      expect(opacity(24, "node", zLinks32*2)).toEqual(0);

      expect(opacity(32, "node", zNodes32)).toEqual(0);
      expect(opacity(32, "node", zNodes32*2)).toEqual(1);
    });
    it("works for links", function () {
      expect(opacity(8, "link", 0.0007)).toEqual(1);
      expect(opacity(8, "link", zLinks16)).toEqual(1);
      expect(opacity(8, "link", zLinks16*2)).toEqual(0);

      expect(opacity(24, "link", zLinks24)).toEqual(0);
      expect(opacity(24, "link", zLinks24*2)).toEqual(1);
      expect(opacity(24, "link", zLinks32)).toEqual(1);
      expect(opacity(24, "link", zLinks32*2)).toEqual(0);

      expect(opacity(32, "link", zLinks32)).toEqual(0);
      expect(opacity(32, "link", zLinks32*2)).toEqual(1);
    });
  });
  describe("trapezoidInterpolation", function () {
    it("matches trapezoid shape", function () {
      let start = 2;
      let peak1 = 4;
      let peak2 = 6;
      let cease = 8;
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 1)).toEqual(0);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 2)).toEqual(0);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 2.5)).toEqual(0.25);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 3)).toEqual(0.5);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 3.5)).toEqual(0.75);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 4)).toEqual(1);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 5)).toEqual(1);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 6)).toEqual(1);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 6.5)).toEqual(0.75);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 7)).toEqual(0.5);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 7.5)).toEqual(0.25);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 8)).toEqual(0);
      expect(trapezoidInterpolation(start, peak1, peak2, cease, 9)).toEqual(0);
    })
  })
  describe("magnitudeSquared", function () {
    it("is accurate", function () {
      expect(magnitudeSquared(3, 3)).toEqual(18);
      expect(magnitudeSquared(4, 2)).toEqual(20);
      expect(magnitudeSquared(10, 0)).toEqual(100);
      expect(magnitudeSquared(0, 10)).toEqual(100);
    });
  });
  //depends on nodes in render collection, controller.rect, tx, ty, and g_scale.
  describe("getSubnetLabel", function () {});
  //TODO: these two are difficult to test
  describe("onScreenRecursive", function () {});
  describe("onScreen", function () {});
  describe("get_bbox", function () {
    it("works on a single node", function () {
      let collection = {abs_x: 100, abs_y: 50, radius_orig: 10};
      expected = {
        "left": 90, 
        "right": 110, 
        "top": 40, 
        "bottom": 60
      };
      expect(get_bbox({"a": collection})).toEqual(expected);
    });
  });

  //TODO: unit testing is a poor fit for the following.
  describe("resetViewport", function () {});
  describe("updateRenderRoot", function () {});
  describe("drawLoopArrow", function () {});
  describe("renderLinks", function () {});
  describe("renderSubnetLabel", function () {});
  describe("renderLabels", function () {});
  describe("renderNode", function () {});
  describe("renderClusters", function () {});
  describe("render_axis", function () {});
  describe("render", function () {});
  describe("render_all", function () {});
});