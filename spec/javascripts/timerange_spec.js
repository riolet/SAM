describe("timerange.js file", function () {
  describe("dateConverter", function () {
    it("converts to", function () {
      let converter = dateConverter();
      expect(converter.to(1.5e9)).toEqual("2017-07-13 19:40");
    })
    it("converts from", function () {
      let converter = dateConverter();
      expect(converter.from("2017-07-13 19:40")).toEqual(1.5e9);
    })
  });
  
  describe("slider_create", function () {});
  describe("slider_hookup", function () {});
  describe("slider_build", function () {});
  describe("slider_rebuild", function () {});
  describe("slider_update", function () {});
});