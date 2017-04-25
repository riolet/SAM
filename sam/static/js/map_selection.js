var m_selection = {};

function sel_init() {
    "use strict";
    m_selection["selection"] = null;
    m_selection["sidebar"] = document.getElementById("sel_bar");
    m_selection["titles"] = document.getElementById("sel_titles");
    m_selection["unique_in"] = document.getElementById("unique_in");
    m_selection["unique_out"] = document.getElementById("unique_out");
    m_selection["unique_ports"] = document.getElementById("unique_ports");
    m_selection["conn_in"] = document.getElementById("conn_in");
    m_selection["conn_out"] = document.getElementById("conn_out");
    m_selection["ports_in"] = document.getElementById("ports_in");
}

function sel_set_selection(node) {
    "use strict";
    m_selection["selection"] = node;
    sel_clear_display();

    if (node !== null && node.details.loaded === false) {
        // load details
        m_selection["titles"].firstChild.innerHTML = "Loading selection...";
        GET_details(node, sel_update_display);
    } else {
        sel_update_display();
    }
}

function sel_clear_display() {
    "use strict";
    // clear all title data
    m_selection["titles"].innerHTML = "";

    // clear connection sums
    m_selection["unique_in"].childNodes[0].textContent = "0";
    m_selection["unique_out"].childNodes[0].textContent = "0";
    m_selection["unique_ports"].childNodes[0].textContent = "0";

    // clear all data from tables
    m_selection["conn_in"].innerHTML = "";
    m_selection["conn_in"].nextElementSibling.innerHTML = "";
    m_selection["conn_out"].innerHTML = "";
    m_selection["conn_out"].nextElementSibling.innerHTML = "";
    m_selection["ports_in"].innerHTML = "";
    m_selection["ports_in"].nextElementSibling.innerHTML = "";

    // remove link to details page
    document.getElementById("sel_link").style.display = "none";

    // add "No selection" title back in.
    var h4 = document.createElement("h4");
    h4.appendChild(document.createTextNode("No selection"));
    m_selection["titles"].appendChild(h4);
    // for spacing.
    m_selection["titles"].appendChild(document.createElement("h5"));
}

function sel_remove_all(collection) {
    "use strict";
    Object.keys(collection).forEach(function (node_name) {
        if (collection[node_name].details.loaded) {
            collection[node_name].details = {"loaded": false};
        }
        sel_remove_all(collection[node_name].children);
    });
}

function sel_build_title(node) {
  "use strict";
  var s_name = nodes.get_name(node);
  var s_address = nodes.get_address(node);
  var s_name_edit_callback = nodes.alias_submit_CB;

  var titles = document.createElement("div")
  var input_group = document.createElement("div");
  var input = document.createElement("input");
  input.id = "node_alias_edit";
  input.type = "text";
  input.placeholder = "Node Alias";
  input.style.textAlign = "center";
  input.value = s_name;
  input.onkeyup = s_name_edit_callback;
  input.onblur = s_name_edit_callback;
  var input_icon = document.createElement("i");
  input_icon.classList.add("write");
  input_icon.classList.add("icon");
  input_group.classList.add("ui");
  input_group.classList.add("transparent");
  input_group.classList.add("icon");
  input_group.classList.add("input");
  input_group.appendChild(input);
  input_group.appendChild(input_icon);

  var title = document.createElement("h4");
  title.appendChild(input_group);

  var subtitle = document.createElement("h5");
  subtitle.appendChild(document.createTextNode(s_address));

  titles.appendChild(title);
  titles.appendChild(subtitle);
  return titles;
}

function sel_build_table(headers, dataset) {
  "use strict";
  var tr;
  var td;
  var tbody = document.createElement("tbody");
  var row;
  var header;
  for (row = 0; row < dataset.length; row += 1) {
    tr = document.createElement("tr");
    for (header = 0; header < headers.length; header += 1) {
        td = document.createElement("td");
        if (headers[header][0] === "port") {
            td.appendChild(ports.get_presentation(dataset[row][header]));
        } else if (headers[header][0] === "sum_bytes") {
            td.appendChild(document.createTextNode(build_label_bytes(dataset[row][header])));
        } else if (headers[header][0] === "avg_duration") {
            td.appendChild(document.createTextNode(build_label_duration(dataset[row][header])));
        } else {
            td.appendChild(document.createTextNode(dataset[row][header]));
        }
        tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  return tbody;
}

function sel_build_table_headers(headers, order, callback) {
    "use strict";
    var tr = document.createElement("tr");
    var th;
    var sort_dir;
    var sort_by;
    if (order) {
        sort_dir = order.charAt(0);
        sort_by = order.substr(1)
    }
    headers.forEach(function (header) {
        th = document.createElement("th");
        th.dataset.value = header[0];
        if (typeof(callback) == "function") {
            th.onclick = callback;
        }
        th.appendChild(document.createTextNode(header[1]));
        if (header[0] === sort_by) {
            th.classList.add("sorted")
            if (sort_dir === "-") {
                th.classList.add("descending");
            } else {
                th.classList.add("ascending");
            }
        }
        tr.appendChild(th);
    });
    return tr;
}

function sel_build_overflow(amount, columns) {
    "use strict";
    var row = document.createElement("tr");
    if (amount > 0) {
        var th = document.createElement("th");
        th.appendChild(document.createTextNode("Plus " + amount + " more..."));
        row.appendChild(th);

        if (columns > 1) {
            th = document.createElement("th");
            th.colSpan = columns - 1;
            row.appendChild(th);
        }
      return row;
    }
    return undefined;
}

function build_label_bytes(bytes) {
    "use strict";
    if (bytes < 10000) {
        return bytes + " B";
    }
    bytes /= 1024;
    if (bytes < 10000) {
        return Math.round(bytes) + " KB";
    }
    bytes /= 1024;
    if (bytes < 10000) {
        return Math.round(bytes) + " MB";
    }
    bytes /= 1024;
    if (bytes < 10000) {
        return Math.round(bytes) + " GB";
    }
    bytes /= 1024;
    return Math.round(bytes) + " TB";
}

function build_label_datarate(bps) {
  "use strict";
  if (bps < 1000) {
    return bps.toFixed(2) + " B/s";
  }
  bps /= 1024;
  if (bps < 1000) {
    return bps.toFixed(2) + " KiB/s";
  }
  bps /= 1024;
  if (bps < 1000) {
    return bps.toFixed(2) + " MiB/s";
  }
  bps /= 1024;
  return bps.toFixed(2) + " GiB/s";
}

function build_label_duration(elapsed) {
    "use strict";
    if (elapsed < 120) {
        return Math.round(elapsed) + " seconds";
    }
    elapsed /= 60;
    if (elapsed < 120) {
        return Math.round(elapsed) + " minutes";
    }
    elapsed /= 60;
    if (elapsed < 48) {
        return Math.round(elapsed) + " hours";
    }
    elapsed /= 24;
    if (elapsed < 14) {
        return Math.round(elapsed) + " days";
    }
    elapsed /= 7;
    return Math.round(elapsed) + " weeks";
}

function sel_panel_height() {
    "use strict";
    var side = document.getElementById("sel_bar");
    var heightAvailable = rect.height - 40;
    side.style.maxHeight = heightAvailable + "px";

    heightAvailable -= 10; //for padding
    heightAvailable -= 10; //for borders

    var contentTitles = $("#selectionInfo div.title");
    var i;
    for (i = 0; i < contentTitles.length; i += 1) {
        //offsetHeight is height + vertical padding + vertical borders
        heightAvailable -= contentTitles[i].offsetHeight;
    }
    heightAvailable -= document.getElementById("sel_titles").offsetHeight;
    heightAvailable -= document.getElementById("sel_link").offsetHeight;

    var contentBlocks = $("#selectionInfo div.content");
    for (i = 0; i < contentBlocks.length; i += 1) {
        contentBlocks[i].style.maxHeight = heightAvailable + "px";
    }
}

function sel_create_link(node) {
    var address = nodes.get_address(node);
    var link = "/metadata#ip=" + address + "&ds=" + config.ds;
    if (window.location.pathname.substr(1,4) === "demo") {
      link = "/demo" + link
    }
    var text = "More details for " + address;

    var icon = document.createElement("I");
    icon.className = "tasks icon";

    var a = document.createElement("A");
    a.appendChild(icon);
    a.appendChild(document.createTextNode(text));
    a.href = link;
    return a;
}

function sel_details_sort_callback(event) {
    var sort_dir = '-';
    if (event.target.classList.contains("descending")) {
        sort_dir = '+';
    }
    var new_sort = sort_dir + event.target.dataset.value;
    var pid = event.target.parentElement.id;
    var component;
    if (pid === "conn_in_h") {
        component = "inputs";
    } else if (pid === "conn_out_h") {
        component = "outputs";
    } else if (pid === "ports_in_h") {
        component = "ports";
    } else {
        console.error("Unknown component to sort");
        return;
    }
    GET_details_sorted(m_selection.selection, component, new_sort, sel_update_display);
}

function sel_update_display(node) {
    "use strict";
    if (node === undefined) {
        node = m_selection["selection"];
    }
    if (node === null || !node.details.loaded) {
        return;
    }
    var tbody;
    var old_row;
    var new_row;
    var overflow;
    var overflow_amount;

    //fill the title div
    m_selection["titles"].innerHTML = "";
    m_selection["titles"].appendChild(sel_build_title(node));

    //fill in the section titles
    m_selection["unique_in"].childNodes[0].textContent = node.details["unique_in"].toString();
    m_selection["unique_out"].childNodes[0].textContent = node.details["unique_out"].toString();
    m_selection["unique_ports"].childNodes[0].textContent = node.details["unique_ports"].toString();

    //fill in the tables
    //Input Connections table
    old_row = document.getElementById("conn_in_h");
    new_row = sel_build_table_headers(node.details.inputs.headers, node.details.inputs.order, sel_details_sort_callback);
    old_row.parentElement.replaceChild(new_row, old_row);
    new_row.id = "conn_in_h";
    tbody = sel_build_table(node.details.inputs.headers, node.details.inputs.rows);
    m_selection['conn_in'].parentElement.replaceChild(tbody, m_selection['conn_in']);
    m_selection['conn_in'] = tbody;

    //Output Connections table
    old_row = document.getElementById("conn_out_h");
    new_row = sel_build_table_headers(node.details.outputs.headers, node.details.outputs.order, sel_details_sort_callback);
    old_row.parentElement.replaceChild(new_row, old_row);
    new_row.id = "conn_out_h";
    tbody = sel_build_table(node.details.outputs.headers, node.details.outputs.rows);
    m_selection['conn_out'].parentElement.replaceChild(tbody, m_selection['conn_out']);
    m_selection['conn_out'] = tbody;

    //Ports Accessed table
    old_row = document.getElementById("ports_in_h");
    new_row = sel_build_table_headers(node.details.ports.headers, node.details.ports.order, sel_details_sort_callback);
    old_row.parentElement.replaceChild(new_row, old_row);
    new_row.id = "ports_in_h";
    //tbody = sel_build_table_ports(node.details.ports.rows);
    tbody = sel_build_table(node.details.ports.headers, node.details.ports.rows);
    m_selection['ports_in'].parentElement.replaceChild(tbody, m_selection['ports_in']);
    m_selection['ports_in'] = tbody;

    //fill in the overflow table footer
    //Input Connections
    overflow = m_selection["conn_in"].nextElementSibling;
    overflow_amount = node.details["unique_in"] - node.details.inputs.rows.length;
    overflow.innerHTML = "";
    new_row = sel_build_overflow(overflow_amount, 3);
    if (new_row) {
      overflow.appendChild(new_row);
    }

    //Output Connections
    overflow = m_selection["conn_out"].nextElementSibling;
    overflow_amount = node.details["unique_out"] - node.details.outputs.rows.length;
    overflow.innerHTML = "";
    new_row = sel_build_overflow(overflow_amount, 3);
    if (new_row) {
      overflow.appendChild(new_row);
    }

    //Ports Accessed
    overflow = m_selection["ports_in"].nextElementSibling;
    overflow_amount = node.details["unique_ports"] - node.details.ports.rows.length;
    overflow.innerHTML = "";
    new_row = sel_build_overflow(overflow_amount, 2);
    if (new_row) {
      overflow.appendChild(new_row);
    }

    //Link to metadata
    new_row = document.getElementById("sel_link");
    new_row.innerHTML = "";
    new_row.style.display = "block";
    new_row.appendChild(sel_create_link(node));


    //activate new popups (tooltips)
    $('.popup').popup();

    //refresh the panel size
    sel_panel_height();
}