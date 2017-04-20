var m_nodes = {};

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
    this.x = x;                         //render: x position in graph
    this.y = y;                         //render: y position in graph
    this.radius = radius;               //render: radius
    this.children = {};                 //child nodes (if this is subnet 8, 16, or 24)
    this.childrenLoaded = false;        //whether the children have been loaded
    this.inputs = [];                   //input connections. an array like: [(ip, [port, ...]), ...]
    this.outputs = [];                  //output connections. an array like: [(ip, [port, ...]), ...]
    this.ports = {};                    //ports by which other nodes connect to this one ( /32 only). Contains a key for each port number
    this.server = false;                //whether this node acts as a client
    this.client = false;                //whether this node acts as a server
    this.details = {"loaded": false};   //detailed information about this node (aliases, metadata, selection panel stuff)

    //queue the node to have links loaded
    link_request_add(address.toString());
}

function get_node_name(node) {
    "use strict";
    if (node.alias.length === 0) {
      if (config.flat) {
        return node.address.toString();
      } else {
        return determine_number(node).toString();
      }
    } else {
        return node.alias;
    }
}

function port_to_pos(node, side) {
    "use strict";
    var x = 0;
    var y = 0;
    if (side === 't-l') {
        x = node.x - node.radius / 3;
        y = node.y - node.radius * 7 / 5;
    } else if (side === 't-r') {
        x = node.x + node.radius / 3;
        y = node.y - node.radius * 7 / 5;
    } else if (side === 'b-l') {
        x = node.x - node.radius / 3;
        y = node.y + node.radius * 7 / 5;
    } else if (side === 'b-r') {
        x = node.x + node.radius / 3;
        y = node.y + node.radius * 7 / 5;
    } else if (side === 'l-t') {
        x = node.x - node.radius * 7 / 5;
        y = node.y - node.radius / 3;
    } else if (side === 'l-b') {
        x = node.x - node.radius * 7 / 5;
        y = node.y + node.radius / 3;
    } else if (side === 'r-t') {
        x = node.x + node.radius * 7 / 5;
        y = node.y - node.radius / 3;
    } else if (side === 'r-b') {
        x = node.x + node.radius * 7 / 5;
        y = node.y + node.radius / 3;
    }
    return [x, y];
}

function nearest_corner(node, x1, y1) {
    "use strict";
    var x = 0;
    var y = 0;
    if (x1 < node.x) {
        x = node.x - node.radius;
    } else {
        x = node.x + node.radius;
    }
    if (y1 < node.y) {
        y = node.y - node.radius;
    } else {
        y = node.y + node.radius;
    }

    return [x, y];
}

function delta_to_dest(node, x1, y1) {
    "use strict";
    let dx = node.x - x1;
    let dy = node.y - y1;
    var x = 0;
    var y = 0;
    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //leftward flowing
            x = node.x + node.radius;
            y = node.y - node.radius * 0.2;
        } else {
            //rightward flowing
            x = node.x - node.radius;
            y = node.y + node.radius * 0.2;
        }
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //upward flowing
            y = node.y + node.radius;
            x = node.x + node.radius * 0.2;
        } else {
            //downward flowing
            y = node.y - node.radius;
            x = node.x - node.radius * 0.2;
        }
    }
    return [x, y];
}

function delta_to_src(node, x2, y2) {
    "use strict";
    let dx = node.x - x2;
    let dy = node.y - y2;
    var x = 0;
    var y = 0;
    if (Math.abs(dx) > Math.abs(dy)) {
        //arrow is more horizontal than vertical
        if (dx < 0) {
            //leftward flowing
            x = node.x + node.radius;
            y = node.y + node.radius * 0.2;
        } else {
            //rightward flowing
            x = node.x - node.radius;
            y = node.y - node.radius * 0.2;
        }
    } else {
        //arrow is more vertical than horizontal
        if (dy < 0) {
            //upward flowing
            y = node.y + node.radius;
            x = node.x - node.radius * 0.2;
        } else {
            //downward flowing
            y = node.y - node.radius;
            x = node.x + node.radius * 0.2;
        }
    }
    return [x, y];
}

function get_inbound_link_point(node, x1, y1, port) {
  "use strict";
  //given a line from (x1, y1) to this node, where should it connect?
  if (node.ports.hasOwnProperty(port)) {
    //get the port connection point
    return port_to_pos(node, node.ports[port]);
  } else if (node.subnet == 32) {
    //get the nearest corner (because the ports are all taken)
    return nearest_corner(node, x1, y1);
  } else {
    //get the closest side and offset a little bit
    return delta_to_dest(node, x1, y1);
  }
}

function get_outbound_link_point(node, x2, y2) {
  "use strict";
  //given a line from this node to (x2, y2), where should it connect?
  if (node.subnet == 32) {
    //get the nearest corner (because the ports are all taken)
    return nearest_corner(node, x2, y2);
  } else {
    //get the closest side and offset a little bit
    return delta_to_src(node, x2, y2);
  }
}

function node_flat_scale() {
    "use strict";
    //These three magic numbers (160, 0.027101, 54.2) are related
    // based on the global scale such that nodes will growing as you
    // zoom in up to a point, and then stay a constant size.
    var r = 0;
    if (g_scale > 0.027101) {
        //stop getting bigger after a certain zoom.
        r =  54.2 / g_scale;
    } else {
        r = 160 / Math.pow(g_scale, 0.7);
    }
    Object.keys(m_nodes).forEach(function (k) {
        m_nodes[k].radius = r;
    });
}

function get_node_address(node) {
    "use strict";
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

function offset_node(node, dx, dy) {
  //move node
  node.x += dx;
  node.y += dy;
}

function set_node_name(node, name) {
    "use strict";
    var oldName = node.alias;
    if (oldName === name) {
        return;
    }
    POST_node_alias(node.address, name);
    node.alias = name;
    render_all();
}

function node_alias_submit(event) {
    "use strict";
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
function determine_number(node) {
    "use strict";
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

function ip_to_string(ip) {
  return Math.floor(ip / 16777216).toString() + "." + (Math.floor(ip / 65536) % 256).toString() + "." + (Math.floor(ip / 256) % 256).toString() + "." + (ip % 256).toString();
}

function insert_node(record) {
  "use strict";
  //create node
  let address = ip_to_string(record.ipstart);
  let node = new Node(record.alias, address, record.ipstart, record.ipend, record.subnet, record.x, record.y, record.radius);
  node.childrenLoaded = true;
  //console.log("installing node ", address);

  //find parents
  let parentColl = m_nodes;
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
      parentColl = parentColl[m_keys[index]].children;
    }
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
      delete parentColl[m_keys[i]];
    }
  }
  
  //insert at that point in the tree.
  parentColl[node.ipstart] = node;
}

// `response` should be an object, where keys are address strings ("12.34.56.78") and values are arrays of objects (nodes)
function node_update(response) {
    "use strict";
    Object.keys(response).forEach(function (parent_address) {
        if (parent_address === "flat") {
          m_nodes = {};
          response[parent_address].forEach(function (record) {
            insert_node(record);
          });
        } else if (parent_address === "_") {
          //must be a call using null, update everything
          m_nodes = {};
          response[parent_address].forEach(function (record) {
            insert_node(record);
          });
          if (subnetLabel == "") { //resets view if we aren't zoomed in.
            resetViewport(m_nodes);
          }
        } else {
          response[parent_address].forEach(function (record) {
            import_node(record);
          });
        }
    });
    link_request_submit();
    updateRenderRoot();
    render_all();
}

function find_by_addr(address) {
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
  return find_by_range(start, end);
}

function find_by_range(start, end, coll) {
  if (!coll) {
    coll = m_nodes;
  }
  //console.log("  searching by ", start, "..", end, " in ", coll);
  let m_keys = Object.keys(coll);
  m_keys.sort(function(a, b){return a-b});
  let high = m_keys.length - 1;
  let low = 0;
  let mid;
  while (low <= high) {
    mid = Math.floor(low + (high-low) / 2);
    let node = coll[m_keys[mid]];
    //console.log("searching: %s<%s<%s. found %s", low, mid, high, node.address);
    if (node.ipstart == start && end == node.ipend) {
      return node;
    } else if (node.ipstart <= start && end <= node.ipend) {
      let finer = find_by_range(start, end, node.children);
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

function get_len(link) {
  return Math.sqrt(Math.pow(link.x2 - link.x1, 2) + Math.pow(link.y2 - link.y1, 2));
}

function calculate_average_distance() {
  var sum_length = 0
  var n_lengths = 0

  Object.keys(m_nodes).forEach(function (ip, i, ary) {
    let node = m_nodes[ip];
    node.inputs.forEach(function (input, i, ary2) {
      sum_length += get_len(input);
      n_lengths += 1;
    });
  });
  let avg_len = sum_length / n_lengths
  return avg_len;
}

function jiggle_node(node, goal_dist) {
  node.inputs.forEach(function (input, i, ary2) {
    let real_dist = get_len(input);
    let proportion = ((real_dist - goal_dist) / 3) / real_dist;
    let dx = (input.x1 - input.x2) * proportion;
    let dy = (input.y1 - input.y2) * proportion;
    offset_node(node, dx, dy);
  });
  node.outputs.forEach(function (output, i, ary2) {
    let real_dist = get_len(output);
    let proportion = ((real_dist - goal_dist) / 3) / real_dist;
    let dx = (output.x2 - output.x1) * proportion;
    let dy = (output.y2 - output.y1) * proportion;
    offset_node(node, dx, dy);
  });
}

function jiggle_nodes(iterations) {
  if (iterations === 0) {
    render_all();
    return 0;
  }
  if (!iterations) {
    var iterations = 1;
  }
  //var dist_avg = calculate_average_distance()
  var dist_avg = 200000;

  Object.keys(m_nodes).forEach(function (ip, i, ary) {
    let node = m_nodes[ip];
    jiggle_node(node, dist_avg);
  });
  link_updateAllPositions();
  return jiggle_nodes(iterations - 1)
}

function node_print_tree(collection, prestring) {
  if (!prestring) {
    prestring = "";
  }
  let col_keys = Object.keys(collection);
  col_keys.sort(function(a, b){return a-b});
  col_keys.forEach(function (key, i, ary) {
    let node = collection[key];
    var r = "";
    if (renderCollection.indexOf(node) != -1) {
      r = " (rendered)";
    }
    
    if (i == ary.length - 1) {
      console.log("%s`---%s%s", prestring, node.address, r);
    } else {
      console.log('%s+---%s%s', prestring, node.address, r);
    }
    if (Object.keys(node.children).length != 0) {
      if (i == ary.length - 1) {
        node_print_tree(node.children, prestring + "    ");
      } else {
        node_print_tree(node.children, prestring + "|   ");
      }
    }
  });
}