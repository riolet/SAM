function disambiguateDeletion(what) {
    "use strict";
    if (what.indexOf("tag") >= 0) return "tags";
    if (what.indexOf("env") >= 0) return "envs";
    if (what.indexOf("hostname") >= 0) return "aliases";
    if (what.indexOf("connection") >= 0) return "connections";
    return "unknown";
}

function catDeleteMessage(what, extra) {
    "use strict";
    var msg = "Are you sure you want to permanently delete ";
    if (what === "tags") {
        msg += "all host/subnet metadata tags? (Across all data sources)"
    } else if (what === "envs") {
        msg += "all host/subnet environment data? (Across all data sources)"
    } else if (what === "aliases") {
        msg += "all hostnames? (Across all data sources)"
    } else if (what === "connections") {
        msg += "connection information? (For the selected data source)"
    } else if (what === "datasource") {
        msg += "'" + getDSName(extra) + "'?"
    }
    return msg
}

function getConfirmation(msg, confirmCallback, denyCallback) {
    "use strict";
    let modal = document.getElementById("deleteModal");
    let modalMsg = document.getElementById("deleteMessage")
    modalMsg.innerHTML = "";
    modalMsg.appendChild(document.createTextNode(msg));
    $(modal).modal({
        onDeny: denyCallback,
        onApprove: confirmCallback
    })
    .modal("show");
}

function deleteData(what) {
    "use strict";
    let target = disambiguateDeletion(what)
    let deleteMessage = catDeleteMessage(target)
    getConfirmation(deleteMessage, function () {
        //target is one of 'tags', 'envs', 'aliases', 'connections'
        if (target === "tags") {
            POST_del_tags()
        } else if (target === "envs") {
            POST_del_envs()
        } else if (target === "aliases") {
            POST_del_aliases()
        } else if (target === "connections") {
            POST_del_connections()
        }
    });
}

function getSelectedDS() {
    "use strict";
    let tabgroup = document.getElementById("ds_tabs");
    let tabs = tabgroup.getElementsByTagName("A");
    let i = tabs.length - 1;
    var ds = undefined;
    for (; i >= 0; i -= 1) {
        if (tabs[i].classList.contains("active")) {
            ds = tabs[i].dataset['tab'];
            break;
        }
    }
    return ds;
}

function getDSName(ds) {
    "use strict";
    let tabgroup = document.getElementById("ds_tabs");
    let tabs = tabgroup.getElementsByTagName("A");
    let i = tabs.length - 1;
    var name = "";
    for (; i >= 0; i -= 1) {
        if (tabs[i].dataset['tab'] === ds) {
            name = tabs[i].innerText;
            break;
        }
    }
    return name;
}

function setDSTabName(ds, newName) {
    "use strict";
    let tabgroup = document.getElementById("ds_tabs");
    let tabs = tabgroup.getElementsByTagName("A");
    let i = tabs.length - 1;
    var icon;
    for (; i >= 0; i -= 1) {
        if (tabs[i].dataset['tab'] == ds) {
            tabs[i].innerHTML = "";
            icon = document.createElement("I");
            icon.className = "on square icon";
            tabs[i].appendChild(icon);
            icon = document.createElement("I");
            icon.className = "off square outline icon";
            tabs[i].appendChild(icon);
            tabs[i].appendChild(document.createTextNode(newName));
            break;
        }
    }
    return name;
}

function getDSId(name) {
    "use strict";
    let tabgroup = document.getElementById("ds_tabs");
    let tabs = tabgroup.getElementsByTagName("A");
    let i = tabs.length - 1;
    var id = "";
    for (; i >= 0; i -= 1) {
        if (tabs[i].innerText === name) {
            id = tabs[i].dataset['tab'];
            break;
        }
    }
    return id;
}

function deleteDS() {
    "use strict";
    let targetDS = getSelectedDS();
    getConfirmation(catDeleteMessage("datasource", targetDS), function () {
        console.log("Deleting " + targetDS + ".");
        POST_ds_delete(targetDS)
    });
}

function validateDSName(name) {
    "use strict";
    //must start with a letter (upper OR lower case) and then follow with either letters, numbers, underscore, or space.
    return (typeof(name) === "string" && name.length > 0 && name.match(/^[a-z][a-z0-9_ ]*$/i));
}

function validateInterval(interval) {
    "use strict";
    interval = parseInt(interval)
    return !isNaN(interval) && interval >= 5 && interval <= 1800
}

function getNewDSName(confirmCallback, denyCallback) {
    "use strict";
    let modal = document.getElementById("newDSModal");
    $(modal).modal({
        onDeny: denyCallback,
        onApprove: function () {
            let name = document.getElementById("newDSName").value.trim();
            if (validateDSName(name)) {
                confirmCallback(name);
            } else {
                return false;
            }
        }
    })
    .modal("show");
}

function addDS() {
    "use strict";
    getNewDSName(function(name) {
        console.log("Adding new ds named " + name);
        POST_ds_new(name)
    }, function() {
        console.log("Not adding anything");
    })
}

function markupWriteInput(classname, datacontent, placeholder, default_value, changeCallback) {
    "use strict";
    var input;
    var icon;
    var div;

    div = document.createElement("DIV");
    div.className = "ui transparent left icon input";

    input = document.createElement("INPUT");
    input.className = classname;
    input.dataset['content'] = datacontent;
    input.placeholder = placeholder;
    input.type = "text";
    input.value = default_value;
    input.onchange = changeCallback;

    icon = document.createElement("I");
    icon.className = "write icon";

    div.appendChild(input);
    div.appendChild(icon);
    return div;
}

function markupCheckboxInput(classname, checked, labeltext, changeCallback) {
    var div;
    var input;
    var label;

    div = document.createElement("DIV");
    div.className = "ui toggle checkbox";

    input = document.createElement("INPUT");
    input.className = classname;
    input.name = classname;
    input.type = "checkbox";
    input.checked = (checked === 1);
    input.onchange = changeCallback;

    label = document.createElement("LABEL");
    if (typeof(labeltext) == "string" && labeltext.length > 0) {
        label.appendChild(document.createTextNode(labeltext))
    } else {
        label.innerHTML = "&nbsp;";
    }

    div.appendChild(input);
    div.appendChild(label);
    return div;
}

function markupRow(td1_child, td2_child) {
    let tr = document.createElement("TR");

    let td1 = document.createElement("TD");
    td1.className = "right aligned";
    td1.appendChild(td1_child);

    let td2 = document.createElement("TD");
    td2.appendChild(td2_child);

    tr.appendChild(td1);
    tr.appendChild(td2);
    return tr;
}

function addDSTab(ds) {
    //ds.id, ds.name, ds.ar_active, ds.ar_interval

    //add tab
    let tabholder = document.getElementById("ds_tabs");
    var a, icon;
    a = document.createElement("A");
    a.className = "item";
    a.dataset["tab"] = "ds_" + ds.id;
    icon = document.createElement("I");
    icon.className = "on square icon";
    a.appendChild(icon);
    icon = document.createElement("I");
    icon.className = "off square outline icon";
    a.appendChild(icon);
    a.appendChild(document.createTextNode(ds.name));
    tabholder.appendChild(a);

    //add tab_contents
    let tabcontents = document.getElementById("ds_tab_contents");
    var tr, table, tbody, div;

    div = document.createElement("DIV");
    div.className = "ui tab segment"
    div.dataset["tab"] = "ds_" + ds.id;

    table = document.createElement("TABLE");
    table.className = "ui fixed definition table";

    tbody = document.createElement("TBODY");
    tr = markupRow(document.createTextNode("Name:"), markupWriteInput("ds_name", ds.name, "-", ds.name, POST_ds_namechange));
    tbody.appendChild(tr);

    tr = markupRow(document.createTextNode("Auto-refresh (map view):"), markupCheckboxInput(ds.live, ds.ar_active, " ", POST_ds_livechange));
    tbody.appendChild(tr);

    tr = markupRow(document.createTextNode("Auto-refresh interval (seconds):"), markupWriteInput("ds_interval", ds.ar_interval, "-", ds.ar_interval, POST_ds_intervalchange));
    tbody.appendChild(tr);

    table.appendChild(tbody);

    div.appendChild(table);

    tabcontents.appendChild(div);
}

function rebuild_tabs(settings, datasources) {
    "use strict";
    //erase what's there.
    let tabholder = document.getElementById("ds_tabs");
    let tabcontents = document.getElementById("ds_tab_contents");
    tabholder.innerHTML = "";
    tabcontents.innerHTML = "";

    //for each ds,
    //   add the ds
    datasources.forEach(addDSTab);

    //build tabs
    let tabs = $(".tabular.menu .item")
    tabs.tab({
        onVisible: POST_ds_selection
    });

    //select active one
    var active_ds = settings.datasource;
    tabs.tab("change tab", "ds_" + active_ds);
}

function getDSs() {
    "use strict";
    //getDSs() returns DSs as [[id, name], ...] with the index 0 being the selected DS.
    let datasource_group = document.getElementById("ds_tabs");
    let datasources = datasource_group.getElementsByTagName("A");
    let i = datasources.length - 1;
    var DSs = [];
    var currentDS;
    var name;
    var id;

    for (; i >= 0; i -= 1) {
        name = datasources[i].innerText;
        id = datasources[i].dataset['tab'];
        if (datasources[i].classList.contains("active")) {
            currentDS = [id, name];
        } else {
            DSs.push([id,name]);
        }
    }
    DSs.unshift(currentDS);
    return DSs;
}

function populateUploadDSList(options) {
    "use strict";
    let log_ds = document.getElementById("log_ds");
    let log_ds_list = document.getElementById("log_ds_list");
    log_ds_list.innerHTML = "";

    //set options
    var div;
    options.forEach(function (option) {
        div = document.createElement("DIV");
        div.className = "item"
        div.dataset['value'] = option[0];
        div.appendChild(document.createTextNode(option[1]));
        log_ds_list.appendChild(div);
    });

    //set default value
    if (options.length == 0) {
        log_ds.value = "";
    } else {
        $(log_ds.parentElement).dropdown("set selected", getSelectedDS());
    }
}

function populateLiveDestDSList(options) {
    "use strict";
    let live_dest_list = document.getElementById("live_dest_list");
    live_dest_list.innerHTML = "";

    //set options
    var div;

    options.forEach(function (option) {
        div = document.createElement("DIV");
        div.className = "item"
        div.dataset['value'] = option[0];
        div.appendChild(document.createTextNode(option[1]));
        live_dest_list.appendChild(div);
    });
}

function validateUpload() {
    "use strict";
    let log_path = document.getElementById("log_path").value;
    let log_ds = document.getElementById("log_ds").value;
    let log_format = document.getElementById("log_format").value;
    console.log("validating...");
    console.log("path: '" + log_path + "'");
    console.log("dsrc: '" + log_ds + "'");
    console.log("frmt: '" + log_format + "'");
    return true;
}

function uploadLog() {
    "use strict";
    let DSs = getDSs();

    populateUploadDSList(DSs);

    let modal = document.getElementById("uploadModal");
    $(modal).modal({
        onApprove: function () {
            if (validateUpload()) {
                let log_file = document.getElementById("log_path").files[0];
                let log_format = document.getElementById("log_format").value;
                let log_ds = document.getElementById("log_ds").value;

                let reader = new FileReader();
                reader.onload = function(event){
                    POST_upload_log(log_ds, log_format, reader.result);
                };
                reader.readAsDataURL(log_file);

                //console.log("uploading " + log_path + " as " + log_format + " to " + log_ds);
            } else {
                console.log("invalid input");
                return false;
            }
        },
        onDeny: function () { console.log("upload cancelled.");}
    })
    .modal("show");
}

function removeLiveKey(e) {
  "use strict";
  let row = e.target.parentElement.parentElement;
  console.log("row"); console.log(row);
  let key_collection = row.getElementsByClassName("secret key");
  console.log("key collection"); console.log(key_collection);
  let key = key_collection[0].innerText;
  console.log("key"); console.log(key);
  POST_del_live_key(key);
}

function addLiveKey(e) {
  "use strict";
  let ds = document.getElementById("live_dest").value;
  POST_add_live_key(ds);
}

function rebuildLiveKeys(livekeys) {
  "use strict";
  let tbody = document.getElementById("live_update_tbody");
  tbody.innerHTML = "";
  livekeys.forEach(function (lk) {
    let tr = document.createElement("TR");
    var td = document.createElement("TD");

    let button = document.createElement("BUTTON");
    let i = document.createElement("I");
    i.className = "red delete icon";
    button.appendChild(i);
    button.className = "remove_live_key ui small icon button";
    button.onclick = removeLiveKey;
    td.appendChild(button);
    td.className = "collapsing";
    tr.appendChild(td);

    td = document.createElement("TD");
    td.appendChild(document.createTextNode(lk.access_key))
    td.className = "secret key";
    tr.appendChild(td);

    td = document.createElement("TD");
    td.appendChild(document.createTextNode(lk.datasource))
    tr.appendChild(td);
    tbody.appendChild(tr);
  });
  if (livekeys.length === 0) {
    let tr = document.createElement("TR");
    var td = document.createElement("TD");

    let button = document.createElement("BUTTON");
    let i = document.createElement("I");
    i.className = "red delete icon";
    button.appendChild(i);
    button.className = "disabled ui small icon button";
    td.appendChild(button);
    td.className = "collapsing";
    tr.appendChild(td);

    td = document.createElement("TD");
    td.appendChild(document.createTextNode("none"));
    td.colspan = "2";
    tr.appendChild(td);
    tbody.appendChild(tr);
  }
}

function AjaxError(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("AJAX Failed: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}

function AjaxSuccess(response) {
    "use strict";
    console.log("Server response:");
    console.log("\t" + response.result + ": " + response.message);
}

function POST_AJAX(command, successCallback) {
    "use strict";
    $.ajax({
        url: "/settings",
        type: "POST",
        data: command,
        error: AjaxError,
        success: function(response) {
            AjaxSuccess(response);
            if (typeof(successCallback) == "function") {
                successCallback(response);
            }
        }
    });
}

function POST_upload_log(ds, format, file) {
  "use strict";
  POST_AJAX({
    "command": "upload",
    "ds": ds,
    "format": format,
    "file": file
  }, function (response) {
    if (response.result === "success") {
      document.getElementById("upload_results").innerHTML = "Your log file was uploaded successfully.";
      document.getElementById("upload_results_title").innerHTML = "Success";
    } else {
      document.getElementById("upload_results").innerHTML = "There was an error uploading your log file.";
      document.getElementById("upload_results_title").innerHTML = "Error";
    }
    $('.ui.response.modal').modal('show');
  });
}

function POST_ds_new(name) {
    "use strict";
    POST_AJAX({"command":"ds_new", "name":name}, function (response) {
        if (response.result === 'success') {
            //successfully created new data source
            rebuild_tabs(response.settings, response.datasources);
            populateLiveDestDSList(getDSs());
        }
    });
}

function POST_ds_delete(id) {
    "use strict";
    POST_AJAX({"command":"ds_rm", "ds":id}, function (response) {
        if (response.result === 'success') {
            //successfully deleted the data source
            rebuild_tabs(response.settings, response.datasources);
            populateLiveDestDSList(getDSs());
            rebuildLiveKeys(response.livekeys)
        }
    });
}

function POST_ds_namechange(e) {
    "use strict";
    var newName = e.target.value.trim();
    if (!validateDSName(newName)) {
        e.target.value = e.target.dataset['content'];
        return;
    }

    if (newName !== e.target.dataset['content']) {
        //in case trim() changed the name
        e.target.value = newName;
        var ds = getSelectedDS();
        console.log("Changing the name of " + ds + " to " + newName);
        POST_AJAX({"command":"ds_name", "ds":ds, "name":newName}, function(response) {
            var id = getDSId(e.target.dataset['content']);
            setDSTabName(id, newName);
            if (response.result === 'success') {
                e.target.dataset['content'] = newName
            }

        });
    }
}

function POST_ds_livechange(e) {
    "use strict";
    var active = e.target.checked;
    var ds = getSelectedDS();
    POST_AJAX({"command":"ds_live", "ds":ds, "is_active":active});
}

function POST_ds_intervalchange(e) {
    "use strict";
    var newInterval = parseInt(e.target.value);
    if (!validateInterval(newInterval)) {
        e.target.value = e.target.dataset['content'];
        return;
    }

    if (newInterval !== parseInt(e.target.dataset['content'])) {
        //in case trim() changed the name
        e.target.value = newInterval;
        var ds = getSelectedDS();
        console.log("Changing the refresh interval of " + ds + " to " + newInterval);
        POST_AJAX({"command":"ds_interval", "ds":ds, "interval":newInterval});
    }
}

function POST_ds_flatchange(e) {
    "use strict";
    var active = e.target.checked;
    var ds = getSelectedDS();
    POST_AJAX({"command":"ds_flat", "ds":ds, "is_flat":active});
}

function POST_ds_selection(ds) {
    "use strict";
    POST_AJAX({"command":"ds_select", "ds":ds});
}

function POST_del_tags() {
    "use strict";
    POST_AJAX({"command":"rm_tags"});
}

function POST_del_envs() {
    "use strict";
    POST_AJAX({"command":"rm_envs"});
}

function POST_del_aliases() {
    "use strict";
    POST_AJAX({"command":"rm_hosts"});
}

function POST_del_connections() {
    "use strict";
    let ds = getSelectedDS();
    POST_AJAX({"command":"rm_conns", "ds":ds});
}

function POST_del_live_key(key) {
  "use strict";
  POST_AJAX({"command": "del_live_key", "key":key}, function (response) {
    if (response.result === 'success') {
      //rebuild live_key list
      rebuildLiveKeys(response.livekeys);
    }
  });
}

function POST_add_live_key(ds) {
  "use strict";
  POST_AJAX({"command":"add_live_key", "ds":ds}, function (response) {
    if (response.result === 'success') {
      //rebuild live_key list
      rebuildLiveKeys(response.livekeys);
    }
  });
}

function foreach(entities, callback) {
    "use strict";
    if (typeof(callback) !== "function") {
        console.error("foreach called with non-function");
        return;
    }
    var i = entities.length - 1;
    for (; i >= 0; i -= 1) {
        callback(entities[i], i, entities);
    }
}

function init() {
    "use strict";

    //initialize datasource tabs
    $(".tabular.menu .item").tab({
        onVisible: POST_ds_selection
    });

    $(".ui.selection.dropdown").dropdown({
        action: "activate"
    });

    $(".ui.deletion.dropdown").dropdown({
        action: "hide",
        onChange: deleteData
    });

    document.getElementById("rm_ds").onclick = deleteDS;
    document.getElementById("add_ds").onclick = addDS;
    document.getElementById("upload_log").onclick = uploadLog;

    foreach(document.getElementsByClassName("remove_live_key"), function(entity) {
      entity.onclick = removeLiveKey;
    });
    document.getElementById("add_live_key").onclick = addLiveKey;

    foreach(document.getElementsByClassName("ds_name"), function(entity) {
        entity.onchange = POST_ds_namechange
    });
    foreach(document.getElementsByClassName("ds_live"), function(entity) {
        entity.onchange = POST_ds_livechange
    });
    foreach(document.getElementsByClassName("ds_interval"), function(entity) {
        entity.onchange = POST_ds_intervalchange
    });
    foreach(document.getElementsByClassName("ds_flat"), function(entity) {
        entity.onchange = POST_ds_flatchange
    });
}
