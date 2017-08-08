/**
 * Class Ports
 * public:
 *   ports = []
 *   display_callback = null
 * private:
 *   requests = []
 *   editing = undefined
 *
 * public functions:
 *   loaded(port)
 *   get_name(port)
 *   get_alias(port)
 *   get_description(port)
 *   get_presentation(port)
 *   set(port, new_info)
 *   request_add(port)
 *   request_submit(callback)
 *   show_edit_window(port)
 *
 * private functions:
 *   click(event)
 *   GET_response(response)
 *   save()
 *   edit(portinfo)
 *   update_displays()
 *
 */

;(function () {
    "use strict";
    let ports = {};
    // Member variables
    ports.ports = [];
    ports.display_callback = null;
    ports.private = {};
    ports.private.requests = [];
    ports.private.editing = undefined;


    // ==================================
    // Public functions
    // ==================================
    ports.loaded = function (port) {
        return ports.ports.hasOwnProperty(port);
    };
    ports.get_name = function (port) {
        if (!ports.loaded(port)){
            return port.toString();
        }

        if (ports.ports[port].active) {
            if (ports.ports[port].alias_name !== "" && ports.ports[port].alias_name !== null) {
                return port.toString() + " - " + ports.ports[port].alias_name;
            } else if (ports.ports[port].name.length !== 0) {
                return port.toString() + " - " + ports.ports[port].name;
            } else {
                return port.toString();
            }
        }
        return port.toString();
    };
    ports.get_alias = function (port) {
        if (!ports.loaded(port)){
            return port.toString();
        }

        if (ports.ports[port].active) {
            if (ports.ports[port].alias_name !== null && ports.ports[port].alias_name.length !== 0) {
                return ports.ports[port].alias_name;
            } else if (ports.ports[port].name !== null && ports.ports[port].name.length !== 0) {
                return ports.ports[port].name;
            } else {
                return port.toString();
            }
        }
        return port.toString();
    };
    ports.get_description = function (port) {
        if (!ports.loaded(port)){
            return ""
        }
        if (ports.ports[port].active) {
            //this checks name and uses description on purpose
            if (ports.ports[port].alias_name !== "" && ports.ports[port].alias_name !== null && ports.ports[port].alias_description !== null) {
                return ports.ports[port].alias_description;
            } else {
                return ports.ports[port].description;
            }
        }
        return "";
    };
    ports.get_protocols = function (port) {
        if (!ports.loaded(port)){
            return ""
        }
        return ports.ports[port].protocols
    };
    ports.get_presentation = function (port) {
        var link = document.createElement('a');
        link.onclick = ports.private.click;
        if (ports.loaded(port)) {
            link.innerText = ports.get_name(port);
            if (ports.ports[port].active) {
              link.dataset['tooltip'] = ports.get_description(port);
            }
            //This works as an alternative, but it's ugly.
            //link.title = get_port_description(port.port)
        } else {
            link.innerText = port.toString();
        }
        return link;
    };
    ports.set = function (port, new_info) {
        // update m_ports
        // POST_portinfo anything new
        // settable properties: active, alias_name, alias_description
        var old_info = {};
        var delta = {};

        if (ports.loaded(port)) {
            old_info = ports.ports[port];
        } else {
            old_info = {
                "port": port,
                "protocols": "",
                "active": 1,
                "name": "",
                "description": "",
                "alias_name": "",
                "alias_description": ""
            };
        }

        if (new_info.hasOwnProperty("active") && new_info.active !== old_info.active) {
            delta.active = old_info.active = new_info.active;
        }
        if (new_info.hasOwnProperty("alias_name") && new_info.alias_name !== old_info.alias_name) {
            old_info.alias_name = new_info.alias_name;
            if (new_info.alias_name !== null) {
                delta.alias_name = new_info.alias_name;
            }
        }
        if (new_info.hasOwnProperty("alias_description") && new_info.alias_description !== old_info.alias_description) {
            old_info.alias_description = new_info.alias_description;
            if (new_info.alias_name !== null) {
                delta.alias_description = new_info.alias_description;
            }
        }
        if (new_info.hasOwnProperty("name") && new_info.name !== old_info.name) {
            old_info.name = new_info.name;
        }
        if (new_info.hasOwnProperty("description") && new_info.description !== old_info.description) {
            old_info.description = new_info.description;
        }
        if (new_info.hasOwnProperty("protocols")) {
            old_info.protocols = new_info.protocols.toLocaleLowerCase().replace(/,/g, ", ");
        }
        // if it had already been loaded, and there are changes, push those changes back to the db.
        if (Object.keys(delta).length > 0) {
            delta.port = port;
            ports.POST_portinfo(delta);
            ports.private.update_displays();
        }

        ports.ports[port] = old_info;
    };
    ports.request_add = function (port) {
        if (!ports.loaded(port)) {
            ports.private.requests.push(port);
        }
    };
    ports.request_submit = function (callback) {
        var request = ports.private.requests.filter(function (element) {
            return !ports.ports.hasOwnProperty(element.toString());
        });

        //remove duplicates by sorting and comparing neighbors
        request = request.sort().filter(function(item, pos, ary) {
            return pos === 0 || item != ary[pos - 1];
        });

        ports.private.requests = [];
        if (request.length > 0) {
            ports.GET_portinfo(request, callback);
        }
    };
    ports.show_edit_window = function (port) {
        document.getElementById("port_number").innerHTML = port;
        document.getElementById("port_name").innerHTML = strings.loading;
        document.getElementById("port_description").innerHTML = strings.loading;
        document.getElementById("port_protocols").innerHTML = "";
        document.getElementById("port_alias_name").value = "";
        document.getElementById("port_alias_description").value = "";

        if (ports.loaded(port)) {
            ports.private.edit(port, ports.ports[port]);
        } else {
            ports.request_add(port);
            ports.request_submit(function () {
                ports.private.edit(port, ports.ports[port]);
            });
        }
        $('.ui.modal.ports')
            .modal({
                onApprove : ports.private.save
            })
            .modal('show')
        ;
    };


    // ==================================
    // Private functions
    // ==================================
    ports.POST_portinfo = function (request) {
        $.ajax({
            url: "./portinfo",
            type: "POST",
            data: request,
            error: generic_ajax_failure,
            success: generic_ajax_success
        });
    };
    ports.GET_portinfo = function (port_list, callback) {
        //ports is an array of Numbers
        var requestData = {"port": port_list.join(",")};
        $.ajax({
            url: "./portinfo",
            type: "GET",
            data: requestData,
            dataType: "json",
            error: generic_ajax_failure,
            success: function (response) {
                ports.private.GET_response(response);

                if (typeof callback === "function") {
                    callback();
                }
            }
        });
    };
    ports.private.GET_response = function (response) {
        Object.keys(response).forEach(function (key) {
            // response[key]
            ports.ports[Number(key)] = {
              "port": Number(key),
              "protocols": response[key].protocols,
              "active": response[key].active,
              "name": response[key].name,
              "description": response[key].description,
              "alias_name": response[key].alias_name,
              "alias_description": response[key].alias_description
            }
        });
        ports.private.update_displays();
    };
    ports.private.click = function (event) {
        var port = parseInt(event.target.innerHTML);
        ports.show_edit_window(port);
    };
    ports.private.save = function () {
        var info = {};
        if (document.getElementById("port_active").checked) {
            info.active = 1;
        } else {
            info.active = 0;
        }
        info.alias_name = document.getElementById("port_alias_name").value;
        info.alias_description = document.getElementById("port_alias_description").value;
        
        ports.set(ports.private.editing, info);
    };
    ports.private.edit = function (port, portinfo) {
        ports.private.editing = port;
    
        if (portinfo === undefined || portinfo.active === undefined) {
            document.getElementById("port_active").checked = true;
        } else {
            document.getElementById("port_active").checked = (portinfo.active === 1);
        }
        if (portinfo === undefined || portinfo.protocols === undefined || portinfo.protocols === null) {
            document.getElementById("port_protocols").innerHTML = "(none)";
        } else {
            document.getElementById("port_protocols").innerHTML = portinfo.protocols;
        }
        if (portinfo === undefined || portinfo.name === undefined || portinfo.name === null || portinfo.name === "") {
            document.getElementById("port_name").innerHTML = "none";
        } else {
            document.getElementById("port_name").innerHTML = portinfo.name;
        }
        if (portinfo === undefined || portinfo.description === undefined || portinfo.description === null || portinfo.description === "") {
            document.getElementById("port_description").innerHTML = "none";
        } else {
            document.getElementById("port_description").innerHTML = portinfo.description;
        }
        if (portinfo === undefined || portinfo.alias_name === undefined || portinfo.alias_name === null) {
            document.getElementById("port_alias_name").value = "";
        } else {
            document.getElementById("port_alias_name").value = portinfo.alias_name;
        }
        if (portinfo === undefined || portinfo.alias_description === undefined || portinfo.alias_description === null) {
            document.getElementById("port_alias_description").value = "";
        } else {
            document.getElementById("port_alias_description").value = portinfo.alias_description;
        }
    };
    ports.private.update_displays = function () {
        if (typeof(ports.display_callback) === "function") {
            ports.display_callback();
        }
    };

    // Export ports instance to global scope
    window.ports = ports;
})();


