/*
------------------------------------
            Node Object
------------------------------------
*/

function Node(alias, address, ipstart, ipend, subnet, x, y, radius) {
    "use strict";
    if (typeof alias === "string") {
        this.alias = alias;  //Custom address translation
    } else {
        this.alias = "";
    }
    this.address = address.toString();  //address: 12.34.56.78
    this.ipstart = ipstart;             //ip range start
    this.ipend = ipend;                 //ip range end
    this.subnet = subnet;               //ip subnet number: 8, 16, 24, 32
    this.abs_x = x;                     //render: absolute y position
    this.abs_y = y;                     //render: absolute x position
    this.rel_x = x;                     //render: relative x position in graph
    this.rel_y = y;                     //render: relative y position in graph
    this.radius = radius;               //render: radius
    this.radius_orig = radius;          //render: original radius (because it will be overwritten);
    this.parent = null;                 //pointer to parent node. This is null if at the top level.
    this.children = {};                 //child nodes (if this is subnet 8, 16, or 24)
    this.childrenLoaded = false;        //whether the children have been loaded
    this.inputs = [];                   //input connections. an array like: [(ip, [port, ...]), ...]
    this.outputs = [];                  //output connections. an array like: [(ip, [port, ...]), ...]
    this.ports = {};                    //ports by which other nodes connect to this one ( /32 only). Contains a key for each port number
    this.server = false;                //whether this node acts as a client
    this.client = false;                //whether this node acts as a server
    this.details = {"loaded": false};   //detailed information about this node (aliases, metadata, selection panel stuff)

    //queue the node to have links loaded
    link_request_add(address.toString() + "/" + subnet);
}

/*
------------------------------------
            `nodes` namespace
------------------------------------
*/

;(function () {
  "use strict";
  let nodes = {};
  nodes.nodes = {};
  nodes.layouts = {};

  //what is rendered:
  // nodes.print_tree(nodes.nodes, "", function(n) {if (renderCollection.indexOf(n) === -1) return ""; else return " (rendered) ";});
  //relative and absolute position
  // nodes.print_tree(nodes.nodes, "", function (n) {return "rel(" + Math.floor(n.rel_x) + ", " + Math.floor(n.rel_y) + "), abs(" + Math.floor(n.abs_x) + ", " + Math.floor(n.abs_y) + ")";})
  nodes.print_tree = function(collection, prestring, poststring_func) {
    if (!prestring) {
      prestring = "";
    }
    let col_keys = Object.keys(collection);
    col_keys.sort(function(a, b){return a-b});
    col_keys.forEach(function (key, i, ary) {
      let node = collection[key];
      var post = "";
      if (typeof(poststring_func) == "function") {
        post = poststring_func(node);
      }

      if (i == ary.length - 1) {
        console.log("%s`---%s %s", prestring, node.address, post);
      } else {
        console.log('%s+---%s %s', prestring, node.address, post);
      }
      if (Object.keys(node.children).length != 0) {
        if (i == ary.length - 1) {
          nodes.print_tree(node.children, prestring + "    ", poststring_func);
        } else {
          nodes.print_tree(node.children, prestring + "|   ", poststring_func);
        }
      }
    });
  }

  nodes.find_by_addr = function (address) {
    let ip_subnet = address.split("/");
    let ip = ip_subnet[0];
    let start = 0;
    let end = 0;
    let subnet = -1;
    if (ip_subnet.length == 2) {
      subnet = +ip_subnet[1];
    }

    let ip_segs = ip.split(".");
    if (subnet == -1) {
      subnet = ip_segs.length * 8;
    } else {
      if (subnet <= 24) { ip_segs.pop(); }
      if (subnet <= 16) { ip_segs.pop(); }
      if (subnet <= 8) { ip_segs.pop(); }
    }

    if (ip_segs.length == 4) {
        start = Number(ip_segs[0]) * 16777216 + Number(ip_segs[1]) * 65536 + Number(ip_segs[2]) * 256 + Number(ip_segs[3]);;
        end = start;
    } else if (ip_segs.length == 3) {
        start = Number(ip_segs[0]) * 16777216 + Number(ip_segs[1]) * 65536 + Number(ip_segs[2]) * 256;
        end = start + 255;
    } else if (ip_segs.length == 2) {
        start = Number(ip_segs[0]) * 16777216 + Number(ip_segs[1]) * 65536;
        end = start + 65535;
    } else if (ip_segs.length == 1) {
        start = Number(ip_segs[0]) * 16777216;
        end = start + 16777215;
    } else {
      return null;
    }
    //console.log("searching for '%s'", address);
    return nodes.find_by_range(start, end);
  }
  nodes.find_by_range = function (start, end, node_coll) {
    if (!node_coll) {
      node_coll = nodes.nodes;
    }
    //console.log("  searching by ", start, "..", end, " in ", coll);
    let m_keys = Object.keys(node_coll);
    m_keys.sort(function(a, b){return a-b});
    let high = m_keys.length - 1;
    let low = 0;
    let mid;
    while (low <= high) {
      mid = Math.floor(low + (high-low) / 2);
      let node = node_coll[m_keys[mid]];
      //console.log("searching: %s<%s<%s. found %s", low, mid, high, node.address);
      if (node.ipstart == start && end == node.ipend) {
        return node;
      } else if (node.ipstart <= start && end <= node.ipend) {
        let finer =nodes.find_by_range(start, end, node.children);
        if (finer === null) {
          return node;
        } else {
          return finer;
        }
      } else if (node.ipend < end) {
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    return null;
  }
  nodes.find_common_root = function (nodeA, nodeB) {
    var root = nodeB.parent;
    while (root != null) {
      if (nodeA.ipstart < root.ipstart || nodeA.ipend > root.ipend) {
        root = root.parent;
      } else {
        break;
      }
    }
    return root;
  }
  nodes.find_step_closer = function (node_coll, target) {
    let m_keys = Object.keys(node_coll);
    m_keys.sort(function(a, b){return a-b});
    let high = m_keys.length - 1;
    let low = 0;
    let mid;
    while (low <= high) {
      mid = Math.floor(low + (high-low) / 2);
      let node = node_coll[m_keys[mid]];
      //console.log("searching: %s<%s<%s. found %s", low, mid, high, node.address);
      if (node.ipstart <= target.ipstart && target.ipend <= node.ipend) {
        return node;
      } else if (node.ipend < target.ipend) {
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    return null;
  }

  nodes.insert = function (record, flat) {
    //create node
    let address = ip_ntos(record.ipstart);
    let node = new Node(record.alias, address, record.ipstart, record.ipend, record.subnet, record.x, record.y, record.radius);
    if (flat) {
      node.childrenLoaded = true;
    }
    //console.log("installing node ", address);

    //find parents
    let parentColl = this.nodes;
    let parent = null;
    let old_parentColl = null;
    while (old_parentColl !== parentColl) {
      old_parentColl = parentColl;
      let index = -1;
      let m_keys = Object.keys(parentColl);
      m_keys.sort(function(a, b){return a-b});
      for(let i = 0; i < m_keys.length; i += 1) {
        if (m_keys[i] > node.ipstart) {
          break;
        }
        index = i;
      }
      if (index >= 0 && node.ipend <= parentColl[m_keys[index]].ipend) {
        //console.log("    parent: ", parentColl[m_keys[index]].address);
        parent = parentColl[m_keys[index]];
        parentColl = parent.children;
      }
    }
    node.parent = parent;
    if (parent) {
      node.rel_x = node.abs_x - parent.abs_x;
      node.rel_y = node.abs_y - parent.abs_y;
    }

    //console.log("  searching for children in range %s..%s", node.ipstart, node.ipend);
    //find children within parent collection
    let children = {};
    let m_keys = Object.keys(parentColl);
    m_keys.sort(function(a, b){return a-b});
    for(let i = 0; i < m_keys.length; i += 1) {
      let child = parentColl[m_keys[i]];
      if (node.ipstart <= child.ipstart && child.ipend <= node.ipend) {
        //console.log("    child added: ", child.address);
        node.children[child.ipstart] = child;
        child.parent = node;
        child.rel_x = child.abs_x - node.abs_x;
        child.rel_y = child.abs_x - node.abs_x;
        delete parentColl[m_keys[i]];
      }
    }

    //insert at that point in the tree.
    parentColl[node.ipstart] = node;
    //node_print_tree(nodes.nodes, "", function (n) {return "(" + n.abs_x + ", " + n.abs_y + ")";})
  }
  nodes.GET_response = function (response) {
    Object.keys(response).forEach(function (parent_address) {
      if (parent_address === "flat") {
        nodes.nodes = {};
        response[parent_address].forEach(function (record) {
          nodes.insert(record, true);
        });
      } else if (parent_address === "_") {
        //must be a call using null, update everything
        nodes.nodes = {};
        response[parent_address].forEach(function (record) {
          nodes.insert(record, false);
        });
        if (subnetLabel == "") { //resets view if we aren't zoomed in.
          resetViewport(nodes.nodes);
        }
      } else {
        response[parent_address].forEach(function (record) {
          nodes.insert(record, false);
        });
      }
    });
    link_request_submit();
  }
  /*
    Retrieves the children of the given nodes and imports them. Optionally calls a callback when done.
    parents: either an array of nodes, or null.
        if a list of nodes, retrieves the children of the nodes that don't have children loaded
        if null, retreives the top-level nodes. (the /8 subnet)
    callback: if is a function, call it when done importing.
    ajax response: should be an object, where keys are address strings ("12.34.56.78") and values are arrays of objects (nodes)
  */
  nodes.GET_request = function (ds, flat, parents, callback) {
    var request = {}
    if (parents !== null) {
      //filter out parents with children already loaded
      parents = parents.filter(function (parent) {
          return !parent.childrenLoaded;
      });
      if (parents.length == 0) {
        return;
      }
      request.address = parents.map(function (parent) {
        parent.childrenLoaded = true;
        return parent.address + "/" + parent.subnet;
      }).join(",");
    }
    request.flat = flat;
    request.ds = ds;
    $.ajax({
      url: "/nodes",
      type: "GET",
      data: request,
      dataType: "json",
      error: generic_ajax_failure,
      success: function (response) {
        nodes.GET_response(response);
        if (typeof callback === "function") {
          callback(response);
        }
      }
    });
  }
  /*
    Update a node alias on the server.
    @param address  node address, "192.168"
    @param name  the new name to use for that address
  */
  nodes.POST_name = function (address, name) {
    var request = {
      "node": address,
      "alias": name
    }
    $.ajax({
      url: "/nodes",
      type: "POST",
      data: request,
      error: onNotLoadData,
      success: reportErrors
    });
  }
  nodes.set_name = function (node, name) {
    let oldName = node.alias;
    if (oldName === name) {
      return;
    }
    this.POST_name(node.address, name);
    node.alias = name;
  }
  nodes.submit_alias_CB = function (event) {
    if (event.keyCode === 13 || event.type === "blur") {
      var newName = document.getElementById("node_alias_edit");
      set_node_name(m_selection["selection"], newName.value);
      return true;
    }
    return false;
}

  /**
   * Determine the last given number in this node's dotted decimal address.
   * ex: this node is 192.168.174.0/24,
   *     this returns 174 because it's the right-most number in the subnet.
   *
   * @param node object returned from the server. Different from Node object in javascript.
   *      should contain [ "connections", "alias", "radius", "y", "x", "ip8", "children" ] or more
   * @returns a subnet-local Number address
   */
  nodes.determine_number = function (node) {
    var size = parseInt(node.ipend) - parseInt(node.ipstart)
    if (size === 0) {
      return node.ipstart % 256;
    }
    if (size === 255) {
      return node.ipstart / 256 % 256;
    }
    if (size === 65535) {
      return node.ipstart / 65536 % 256;
    }
    if (size === 16777215) {
      return node.ipstart / 16777216 % 256;
    }
    console.error("failed to determine size (" + size + ") when " + node.ipend + " - " + node.ipstart + ".");
    return undefined
  }
  nodes.port_to_pos = function (node, side) {
    var x = 0;
    var y = 0;
    if (side === 't-l') {
      x = node.abs_x - node.radius / 3;
      y = node.abs_y - node.radius * 7 / 5;
    } else if (side === 't-r') {
      x = node.abs_x + node.radius / 3;
      y = node.abs_y - node.radius * 7 / 5;
    } else if (side === 'b-l') {
      x = node.abs_x - node.radius / 3;
      y = node.abs_y + node.radius * 7 / 5;
    } else if (side === 'b-r') {
      x = node.abs_x + node.radius / 3;
      y = node.abs_y + node.radius * 7 / 5;
    } else if (side === 'l-t') {
      x = node.abs_x - node.radius * 7 / 5;
      y = node.abs_y - node.radius / 3;
    } else if (side === 'l-b') {
      x = node.abs_x - node.radius * 7 / 5;
      y = node.abs_y + node.radius / 3;
    } else if (side === 'r-t') {
      x = node.abs_x + node.radius * 7 / 5;
      y = node.abs_y - node.radius / 3;
    } else if (side === 'r-b') {
      x = node.abs_x + node.radius * 7 / 5;
      y = node.abs_y + node.radius / 3;
    }
    return [x, y];
  }
  nodes.nearest_corner = function (node, x1, y1) {
    var x = 0;
    var y = 0;
    if (x1 < node.abs_x) {
      x = node.abs_x - node.radius;
    } else {
      x = node.abs_x + node.radius;
    }
    if (y1 < node.abs_y) {
      y = node.abs_y - node.radius;
    } else {
      y = node.abs_y + node.radius;
    }

    return [x, y];
  }
  nodes.delta_to_dest = function (node, x1, y1) {
    let dx = node.abs_x - x1;
    let dy = node.abs_y - y1;
    var x = 0;
    var y = 0;
    if (Math.abs(dx) > Math.abs(dy)) {
      //arrow is more horizontal than vertical
      if (dx < 0) {
        //leftward flowing
        x = node.abs_x + node.radius;
        y = node.abs_y - node.radius * 0.2;
      } else {
        //rightward flowing
        x = node.abs_x - node.radius;
        y = node.abs_y + node.radius * 0.2;
      }
    } else {
      //arrow is more vertical than horizontal
      if (dy < 0) {
        //upward flowing
        y = node.abs_y + node.radius;
        x = node.abs_x + node.radius * 0.2;
      } else {
        //downward flowing
        y = node.abs_y - node.radius;
        x = node.abs_x - node.radius * 0.2;
      }
    }
    return [x, y];
  }
  nodes.delta_to_src = function (node, x2, y2) {
    let dx = node.abs_x - x2;
    let dy = node.abs_y - y2;
    var x = 0;
    var y = 0;
    if (Math.abs(dx) > Math.abs(dy)) {
      //arrow is more horizontal than vertical
      if (dx < 0) {
        //leftward flowing
        x = node.abs_x + node.radius;
        y = node.abs_y + node.radius * 0.2;
      } else {
        //rightward flowing
        x = node.abs_x - node.radius;
        y = node.abs_y - node.radius * 0.2;
      }
    } else {
      //arrow is more vertical than horizontal
      if (dy < 0) {
        //upward flowing
        y = node.abs_y + node.radius;
        x = node.abs_x - node.radius * 0.2;
      } else {
        //downward flowing
        y = node.abs_y - node.radius;
        x = node.abs_x + node.radius * 0.2;
      }
    }
    return [x, y];
  }
  nodes.get_inbound_link_point = function (node, x1, y1, port) {
    //given a line from (x1, y1) to this node, where should it connect?
    if (node.ports.hasOwnProperty(port)) {
      //get the port connection point
      return nodes.port_to_pos(node, node.ports[port]);
    } else if (node.subnet == 32) {
      //get the nearest corner (because the ports are all taken)
      return nodes.nearest_corner(node, x1, y1);
    } else {
      //get the closest side and offset a little bit
      return nodes.delta_to_dest(node, x1, y1);
    }
  }
  nodes.get_outbound_link_point = function (node, x2, y2) {
    //given a line from this node to (x2, y2), where should it connect?
    if (node.subnet == 32) {
      //get the nearest corner (because the ports are all taken)
      return nodes.nearest_corner(node, x2, y2);
    } else {
      //get the closest side and offset a little bit
      return nodes.delta_to_src(node, x2, y2);
    }
  }
  nodes.update_pos_tree = function (node, parent) {
    if (parent) {
      node.abs_x = node.rel_x + parent.abs_x;
      node.abs_y = node.rel_y + parent.abs_y;
    } else {
      node.abs_x = node.rel_x;
      node.abs_y = node.rel_y;
    }
    Object.keys(node.children).forEach(function (k) {
      nodes.update_pos_tree(node.children[k], node);
    });
  }
  nodes.set_relative_pos = function (node, rel_dx, rel_dy) {
    //move node
    node.rel_x = rel_dx;
    node.rel_y = rel_dy;
    nodes.update_pos_tree(node, node.parent);
  }
  nodes.get_name = function (node) {
    if (node.alias.length === 0) {
      if (config.flat) {
        return node.address.toString();
      } else {
        return nodes.determine_number(node).toString();
      }
    } else {
        return node.alias;
    }
  }
  nodes.flat_scale = function () {
    let constant_size = 20 / g_scale;

    renderCollection.forEach(function (node) {
      node.radius = Math.max(constant_size, node.radius_orig);
    });
  }
  nodes.get_address = function (node) {
    var add = node.address;
    var missing_terms = 4 - add.split(".").length;
    while (missing_terms > 0) {
        add += ".0";
        missing_terms -= 1;
    }
    if (node.subnet < 32) {
      add += "/" + node.subnet;
    }
    return add;
  }

  // Export ports instance to global scope
  window.nodes = nodes;
})();

/*
------------------------- grid layout ----------------------
*/
; (function () {
  "use strict";
  let grid = {};

  grid.arrange_collection = function (coll, radius) {
    let count = Object.keys(coll).length;
    if (count == 1) {
      let node = coll[Object.keys(coll)[0]];
      nodes.set_relative_pos(node, 0, 0);
      if (Object.keys(node.children).length > 0) {
        circle.arrange_nodes_recursion(node.children, node.radius_orig);
      }
      return;
    }
    else if (count < 5) {
      radius /= 4;
    }
    else if (count < 17) {
      radius /= 2;
    }
    let n_per_side = Math.ceil(Math.sqrt(count));
    let side_length = Math.sqrt(Math.pow(radius*2, 2) / 2);
    let spacing = side_length / (n_per_side - 1);
    let offset = side_length / 2;
    Object.keys(coll).forEach(function (key, i, ary) {
      let x = -offset + (i % n_per_side) * spacing;
      let y = +offset - (Math.floor(i / n_per_side)) * spacing;
      let node = coll[key];
      nodes.set_relative_pos(node, x, y);

      if (Object.keys(node.children).length > 0) {
        circle.arrange_nodes_recursion(node.children, node.radius_orig);
      }
    });
  }

  grid.layout = function (node_coll) {
    return null;
  }

  //install layout
  nodes.layouts['Grid'] = grid;
})();

/*
------------------------- circle layout ----------------------
*/
;(function () {
  "use strict";
  let circle = {};

  circle.find_center_node = function (node_coll) {
    let center = null;
    let best = -1;
    Object.keys(node_coll).forEach(function (key) {
      let node = node_coll[key];
      let connectivity = node.inputs.length + node.outputs.length;
      if (connectivity > best) {
        best = connectivity;
        center = node;
      }
    });
    return center;
  }
  circle.get_all_attached_nodes = function (node) {
    let attached = [];
    let min = node.ipstart;
    let max = node.ipend;
    node.outputs.forEach(function (l_out) {
      // only if the destination is outside the node, add it.
      if (l_out.dst_end < min || max < l_out.dst_start) {
        attached.push(l_out.dst);
      }
    });
    node.inputs.forEach(function (l_in) {
      // only if the source is outside the node, add it.
      if (l_in.src_end < min || max < l_in.src_start) {
        attached.push(l_in.dst);
      }
    });
    return attached;
  }
  circle.sorted_unique = function (coll, sort_func) {
    coll.sort(sort_func);
    return coll.filter(function(item, pos, ary) {
      return !pos || (item.address + item.subnet) != (ary[pos - 1].address + ary[pos - 1].subnet);
    });
  }
  circle.remove_item = function (coll, item) {
    let index = coll.indexOf(item);
    if (index !== -1) {
      coll.splice(index, 1);
    }
  }
  circle.move_to_center = function (node) {
    nodes.set_relative_pos(node, 0, 0);
  }
  circle.get_bbox = function () {
    let left = -tx / g_scale;
    let right = (rect.width - tx) / g_scale;
    let top = -ty / g_scale;
    let bottom = (rect.height - ty) / g_scale;
    return {"left": left, "top": top, "right": right, "bottom": bottom};
  }
  circle.arrange_nodes_recursion = function (coll, radius) {
    let count = Object.keys(coll).length;
    if (count == 1) {
      let node = coll[Object.keys(coll)[0]];
      nodes.set_relative_pos(node, 0, 0);
      if (Object.keys(node.children).length > 0) {
        circle.arrange_nodes_recursion(node.children, node.radius_orig);
      }
      return;
    }
    else if (count < 5) {
      radius /= 4;
    }
    else if (count < 17) {
      radius /= 2;
    }
    let n_per_side = Math.ceil(Math.sqrt(count));
    let side_length = Math.sqrt(Math.pow(radius*2, 2) / 2);
    let spacing = side_length / (n_per_side - 1);
    let offset = side_length / 2;
    Object.keys(coll).forEach(function (key, i, ary) {
      let x = -offset + (i % n_per_side) * spacing;
      let y = +offset - (Math.floor(i / n_per_side)) * spacing;
      let node = coll[key];
      nodes.set_relative_pos(node, x, y);

      if (Object.keys(node.children).length > 0) {
        circle.arrange_nodes_recursion(node.children, node.radius_orig);
      }
    });
  }
  circle.arrange_nodes_evenly = function (node_coll) {
    // 0 rad is to the right.
    // pi/2 rad is down.
    let len = node_coll.length;
    let bbox = circle.get_bbox();
    let rx = (bbox.right - bbox.left) / 2;
    let ry = (bbox.bottom - bbox.top) / 2;
    rx *= 0.8;
    ry *= 0.8;

    node_coll.forEach(function (node, i, ary) {
      let x = Math.cos(i / len * 2 * Math.PI);
      let y = Math.sin(i / len * 2 * Math.PI);
      console.log("at ", i/len*2*Math.PI, " radians, placing ", node.alias, " (", node.address, ")");
      nodes.set_relative_pos(node, x * rx, y * ry);
      if (Object.keys(node.children).length > 0) {
        circle.arrange_nodes_recursion(node.children, node.radius_orig);
      }
    });
  }
  circle.layout = function (node_coll) {
    let center = circle.find_center_node(node_coll);
    circle.move_to_center(center);
    let attached = circle.get_all_attached_nodes(center);
    attached = circle.sorted_unique(attached, function (a, b) { if (a.ipstart - b.ipstart == 0) return a.subnet - b.subnet; else return a.ipstart - b.ipstart;});
    circle.remove_item(attached, center);
    circle.arrange_nodes_evenly(attached);
    circle.arrange_nodes_recursion(center.children, center.radius_orig);
  }

  //install layout
  nodes.layouts['Circle'] = circle;
})();