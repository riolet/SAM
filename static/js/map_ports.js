
var m_portinfo;
var m_ports = [];
var m_port_requests = [];

function port_loaded(port) {
    return m_ports.hasOwnProperty(port);
}

function get_port_name(port) {
    if (!m_ports.hasOwnProperty(port)){
        return port.toString();
    }

    if (m_ports[port].active) {
        if (m_ports[port].alias_name !== "" && m_ports[port].alias_name !== null) {
            return port.toString() + " - " + m_ports[port].alias_name;
        } else if (m_ports[port].name.length !== 0) {
            return port.toString() + " - " + m_ports[port].name;
        } else {
            return port.toString();
        }
    }
    return port.toString();
}

function get_port_alias(port) {
    if (!m_ports.hasOwnProperty(port)){
        return port.toString();
    }

    if (m_ports[port].active) {
        if (m_ports[port].alias_name !== null && m_ports[port].alias_name.length !== 0) {
            return m_ports[port].alias_name;
        } else if (m_ports[port].name !== null && m_ports[port].name.length !== 0) {
            return m_ports[port].name;
        } else {
            return port.toString();
        }
    }
    return port.toString();
}

function get_port_description(port) {
    if (!m_ports.hasOwnProperty(port)){
        return ""
    }

    if (m_ports[port].active) {
        //this checks name and uses description on purpose
        if (m_ports[port].alias_name !== "" && m_ports[port].alias_name !== null && m_ports[port].alias_description !== null) {
            return m_ports[port].alias_description;
        } else {
            return m_ports[port].description;
        }
    }
    return "";
}

function update_port(info) {
    var port = {};
    port.active = info.active;
    port.port = Number(info.port);
    port.name = info.name;
    port.description = info.description;
    port.alias_name = info.alias_name;
    port.alias_description = info.alias_description;

    m_ports[Number(info.port)] = port;
}

function port_click(event) {
    port = Number((event.target.innerHTML.split(" ")[0]));
    show_window(port)
}

function port_request_add(port_number) {
    if (!port_loaded(port_number)) {
        m_port_requests.push(port_number);
    }
}

function port_request_submit() {
    var request = m_port_requests.filter(function (element) {
        return !m_ports.hasOwnProperty(element.port);
    });

    //remove duplicates by sorting and comparing neighbors
    request = request.sort().filter(function(item, pos, ary) {
        return !pos || item != ary[pos - 1];
    });

    m_port_requests = [];
    if (request.length > 0) {
        GET_portinfo(request);
    }
}

function port_save() {
    var differences = false;
    if (document.getElementById("port_active").checked !== (m_portinfo.active === 1)) {
        //toggle active between 0 and 1
        m_portinfo.active = 1 - m_portinfo.active;
        differences = true;
    }
    if (document.getElementById("port_alias_name").value !== m_portinfo.alias_name) {
        m_portinfo.alias_name = document.getElementById("port_alias_name").value;
        differences = true;
    }
    if (document.getElementById("port_alias_description").value !== m_portinfo.alias_description) {
        m_portinfo.alias_description = document.getElementById("port_alias_description").value;
        differences = true;
    }
    update_port(m_portinfo);
    if (differences) {
        delete m_portinfo.name;
        delete m_portinfo.description;
        POST_portinfo(m_portinfo);
    }
}

function show_window(port) {
    document.getElementById("port_number").innerHTML = port;
    document.getElementById("port_name").innerHTML = "loading...";
    document.getElementById("port_description").innerHTML = "loading...";
    document.getElementById("port_alias_name").value = "";
    document.getElementById("port_alias_description").value = "";

    if (m_ports.hasOwnProperty(port)){
        port_display(m_ports[port]);
    } else {
        m_portinfo = {"port":port};
        GET_portinfo([port]);
    }
    $('.ui.modal.ports')
        .modal({
            onApprove : port_save
        })
        .modal('show')
    ;
}

function port_display(port) {
    if (port !== undefined) {
        m_portinfo = port;
    }
    if (port === undefined || port.active === undefined) {
        document.getElementById("port_active").checked = true;
        m_portinfo.active = 1;
    } else {
        document.getElementById("port_active").checked = (port.active === 1);
    }
    if (port === undefined || port.name === undefined || port.name === null || port.name === "") {
        document.getElementById("port_name").innerHTML = "none";
    } else {
        document.getElementById("port_name").innerHTML = port.name;
    }
    if (port === undefined || port.description === undefined || port.description === null || port.description === "") {
        document.getElementById("port_description").innerHTML = "none";
    } else {
        document.getElementById("port_description").innerHTML = port.description;
    }
    if (port === undefined || port.alias_name === undefined || port.alias_name === null) {
        document.getElementById("port_alias_name").value = "";
        m_portinfo.port_alias_name = "";
    } else {
        document.getElementById("port_alias_name").value = port.alias_name;
    }
    if (port === undefined || port.alias_description === undefined || port.alias_description === null) {
        document.getElementById("port_alias_description").value = "";
        m_portinfo.port_alias_description = "";
    } else {
        document.getElementById("port_alias_description").value = port.alias_description;
    }
}

function GET_portinfo_callback(result) {
    result.forEach(update_port);
    sel_update_display(m_selection["selection"]);
    port = result.pop();
    port_display(port);
}

