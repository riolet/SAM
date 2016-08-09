
var m_portinfo;

function port_click(event) {
    port = Number((event.target.innerHTML.split(" ")[0]));
    show_window(port)
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
    if (differences) {
        delete m_portinfo.name;
        delete m_portinfo.description;
        POST_portinfo(m_portinfo);
    }
}

function show_window(port) {
    document.getElementById("port_number").innerHTML = port;
    document.getElementById("port_name").innerHTML = "...";
    document.getElementById("port_description").innerHTML = "...";
    $('.ui.modal.ports')
        .modal({
            onApprove : port_save
        })
        .modal('show')
    ;
    GET_portinfo(port);
}

function GET_portinfo_callback(result) {
    m_portinfo = result;
    document.getElementById("port_active").checked = (result.active === 1);
    if (result.name === undefined || result.name === null) {
        document.getElementById("port_name").innerHTML = "none";
    } else {
        document.getElementById("port_name").innerHTML = result.name;
    }
    if (result.description === undefined || result.description === null) {
        document.getElementById("port_description").innerHTML = "none";
    } else {
        document.getElementById("port_description").innerHTML = result.description;
    }
    if (result.alias_name === undefined || result.alias_name === null) {
        document.getElementById("port_alias_name").value = "";
        m_portinfo.alias_name = "";
    } else {
        document.getElementById("port_alias_name").value = result.alias_name;
    }
    if (result.alias_description === undefined || result.alias_description === null) {
        document.getElementById("port_alias_description").value = "";
        m_portinfo.alias_description = "";
    } else {
        document.getElementById("port_alias_description").value = result.alias_description;
    }
}

