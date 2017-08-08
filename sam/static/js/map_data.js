function checkLoD() {
  "use strict";
  let nodesToLoad = [];
  renderCollection.forEach(function (node) {
    if (node.subnet < currentSubnet(g_scale)) {
      nodesToLoad.push(node);
    }
  });
  if (nodesToLoad.length > 0) {
    nodes.GET_request(nodesToLoad, function () {
      updateRenderRoot();
      render_all();
    });
  }
}