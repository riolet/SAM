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

function deleteHosts() {
  let deleteMessage = strings.set_del_host;
  getConfirmation(deleteMessage, function () {
    POST_del_aliases();
  });
}

function deleteTags() {
  let deleteMessage = strings.set_del_tags;
  getConfirmation(deleteMessage, function () {
    POST_del_tags();
  });
}

function deleteEnvs() {
  let deleteMessage = strings.set_del_envs;
  getConfirmation(deleteMessage, function () {
    POST_del_envs();
  });
}

function deleteConnectionsDS(e) {
  let targetDS = getSelectedDS();
  let targetName = getDSName(targetDS);
  let deleteMessage = strings.set_del_conns + targetName + "?";
  getConfirmation(deleteMessage, function () {
    POST_del_connections(targetDS);
  })
}

function getSelectedDS() {
  /**
   * Get the id of the active datasource. () -> "ds1"
   * fail case: () -> ""
   */
  "use strict";
  let ds = "";
  let tabgroup = document.getElementById("ds_tabs");
  let active_row = null;
  if (tabgroup) {
    let active_rows = tabgroup.getElementsByClassName("active");
    if (active_rows.length === 1) {
      active_row = active_rows[0];
    }
  }
  if (active_row) {
    ds = active_row.id.slice(0, -8);
  }
  return ds;
}

function getDSName(ds) {
  /**
   * Get the text name of a ds given it's id. ("ds1") -> "default"
   * fail case: ("bad") -> ""
   */
  "use strict";
  let name = "";
  let rowname = ds + "_tab_row";
  let row = document.getElementById(rowname); 
  let label;
  if (row) {
    let labels = row.getElementsByClassName("tablabel");
    if (labels.length === 1) {
      label = labels[0];
      name = label.innerText;
    }
  }
  return name;
}

function setDSTabName(ds, newName) {
  /**
   * Assigns the newName to the tab for the given DS. ("ds1", "bob") -> undefined
   * Fail case: no effect.
   */
  "use strict";
  let rowname = ds + "_tab_row";
  let row = document.getElementById(rowname);
  let label;
  if (row) {
    let labels = row.getElementsByClassName("tablabel");
    if (labels.length === 1) {
      label = labels[0];
      label.innerText = newName;
    }
  }
}

function getDSId(name) {
  /**
   * Translate datasource name into datasource ID. ("default") -> "ds1"
   * fail case: ("bad") -> ""
   */
  "use strict";
  let tabgroup = document.getElementById("ds_tabs");
  let tabs = tabgroup.getElementsByClassName("tablabel");
  let i = tabs.length - 1;
  var id = "";
  for (; i >= 0; i -= 1) {
    if (tabs[i].innerText.trim() === name) {
      id = tabs[i].dataset['tab'];
      break;
    }
  }
  return id;
}

function getDSs() {
  /**
   * Get DSs as a list of [id, name] pairs with the active DS first in the list. () -> [['ds1', 'default'], ['ds2', 'other DS']]
   */
  "use strict";
  let tabgroup = document.getElementById("ds_tabs");
  let rows = tabgroup.getElementsByTagName("TR");
  let DSs = [];
  let currentDS;
  let i = rows.length - 1;
  for (; i >= 0; i -= 1) {
    let ds = rows[i].id.slice(0, -8);
    let name = getDSName(ds);
    if (rows[i].classList.contains("active")) {
      currentDS = [ds, name];
    } else {
      DSs.push([ds, name]);
    }
  }
  if (currentDS) {
    DSs.unshift(currentDS);
  }
  return DSs;
}

function deleteDS(e) {
    "use strict";
    let targetDS = e.target.dataset['tab'];
    if (targetDS == undefined) {
      targetDS = e.target.parentElement.dataset['tab'];
    }
    getConfirmation(strings.set_del_ds + "\"" + getDSName(targetDS) + "\"?", function () {
        console.log("Deleting " + targetDS + ".");
        POST_ds_delete(targetDS);
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
    div.className = "ui transparent left icon fluid input";

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
    td1.appendChild(td1_child);

    let td2 = document.createElement("TD");
    td2.appendChild(td2_child);

    tr.appendChild(td1);
    tr.appendChild(td2);
    return tr;
}

function addDSTab(ds) {
    "use strict";
    //ds.id, ds.name, ds.ar_active, ds.ar_interval, ds.flat

    //add tab
    let tabholder = document.getElementById("ds_tabs");
    let tab_tr = document.createElement("TR");
    tab_tr.className = "item";
    tab_tr.id="ds" + ds.id + "_tab_row";
    let td1 = document.createElement("TD");
    td1.className = "center aligned collapsing";
    let btn_del = document.createElement("BUTTON");
    btn_del.className = "ui small icon button del_ds"
    btn_del.dataset['tab'] = "ds" + ds.id;
    btn_del.onclick = deleteDS;
    let icon = document.createElement("I");
    icon.className = "red delete icon";
    btn_del.appendChild(icon);
    td1.appendChild(btn_del);
    tab_tr.appendChild(td1);
    let td2 = document.createElement("TD");
    td2.className = "tablabel";
    td2.dataset['tab'] = "ds" + ds.id;
    td2.appendChild(document.createTextNode(ds.name));
    tab_tr.appendChild(td2);
    tabholder.appendChild(tab_tr);

    //add tab_contents
    let tabcontents = document.getElementById("ds_tab_contents");
    let tr, table, tbody, div, btn;

    div = document.createElement("DIV");
    div.className = "ui tab segment"
    div.dataset["tab"] = "ds" + ds.id;

    table = document.createElement("TABLE");
    table.className = "ui fixed definition table";

    tbody = document.createElement("TBODY");
    tr = markupRow(document.createTextNode(strings.set_ds_name), markupWriteInput("ds_name", ds.name, "-", ds.name, POST_ds_namechange));
    tbody.appendChild(tr);

    tr = markupRow(document.createTextNode(strings.set_ds_ar), markupCheckboxInput("ds_live", ds.ar_active, " ", POST_ds_livechange));
    tbody.appendChild(tr);

    tr = markupRow(document.createTextNode(strings.set_ds_ari), markupWriteInput("ds_interval", ds.ar_interval, "-", ds.ar_interval, POST_ds_intervalchange));
    tbody.appendChild(tr);

    tr = markupRow(document.createTextNode(strings.set_ds_flat), markupCheckboxInput("ds_flat", ds.ar_active, " ", POST_ds_flatchange));
    tbody.appendChild(tr);

    btn = document.createElement("BUTTON");
    btn.className = "ui compact icon button del_con";
    btn.onclick = deleteConnectionsDS;
    icon = document.createElement("I");
    icon.className="red trash icon";
    btn.appendChild(icon);
    btn.appendChild(document.createTextNode(strings.set_ds_del));
    tr = markupRow(document.createTextNode(strings.set_ds_del_hint), btn)
    tbody.appendChild(tr);

    btn = document.createElement("BUTTON");
    btn.className = "ui compact icon button upload_con";
    btn.onclick = uploadLog;
    icon = document.createElement("I");
    icon.className="green upload icon";
    btn.appendChild(icon);
    btn.appendChild(document.createTextNode(strings.set_ds_up));
    tr = markupRow(document.createTextNode(strings.set_ds_up_hint), btn)
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
    //initialize datasource tabs
    $('.tablabel')
      .on('click', tab_change_callback)
    ;

    //select active one
    var active_ds = settings.datasource;
    $.tab();  // This initializes the tabs. Must be done prior to changing tabs.
    $.tab("change tab", "ds" + active_ds);
    let active_tab = document.getElementById("ds" + active_ds + "_tab_row");
    active_tab.classList.add("active");
}

function tab_change_callback(e) {
  // programmatically activating tab
  $.tab('change tab', e.target.dataset['tab']);
  // change which row has the active class.
  $(document.getElementById(e.target.dataset['tab'] + '_tab_row'))
    .addClass('active')
    .siblings()
    .removeClass('active')
  ;
  POST_ds_selection(e.target.dataset['tab']);
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
        div.className = "item";
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
  let row = e.target;
  while (row.tagName != "TR" && row.parentElement) {
    row = row.parentElement;
  }
  let key_collection = row.getElementsByClassName("secret key");
  let key = key_collection[0].innerText;
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
    td.appendChild(document.createTextNode(strings.set_livekey_empty));
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

/*
-----------------  Posts -------------------
*/

function POST_AJAX(command, successCallback) {
    "use strict";
    $.ajax({
        url: "./settings",
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
      document.getElementById("upload_results").innerHTML = strings.set_upload_success_d;
      document.getElementById("upload_results_title").innerHTML = strings.set_upload_success;
    } else {
      document.getElementById("upload_results").innerHTML = strings.set_upload_fail_d;
      document.getElementById("upload_results_title").innerHTML = strings.set_upload_fail;
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
            let dses = getDSs()
            populateLiveDestDSList(dses);
            populateUploadDSList(dses);
        }
    });
}

function POST_ds_delete(id) {
    "use strict";
    POST_AJAX({"command":"ds_rm", "ds":id}, function (response) {
        if (response.result === 'success') {
            //successfully deleted the data source
            rebuild_tabs(response.settings, response.datasources);
            let dses = getDSs()
            populateLiveDestDSList(dses);
            populateUploadDSList(dses);
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
        console.log("updating dataset to {}", newInterval);
        e.target.dataset['content'] = newInterval;
        var ds = getSelectedDS();
        console.log("Changing the refresh interval of " + ds + " to " + newInterval);
        POST_AJAX({"command":"ds_interval", "ds":ds, "interval":newInterval});
    }
}

function POST_ds_flatchange(e) {
    "use strict";
    let flat = e.target.checked;
    let ds = getSelectedDS();
    POST_AJAX({"command":"ds_flat", "ds":ds, "is_flat":flat});
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

function POST_del_connections(ds) {
    "use strict";
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
/*
-----------------  Initialization -------------------
*/
function init() {
    "use strict";

    //initialize datasource tabs
    $('.tablabel').on('click', tab_change_callback);

    //initialize datasource delete buttons
    $('.del_ds').on('click', deleteDS);

    $(".ui.selection.dropdown").dropdown({
        action: "activate"
    });

    $('.del_con').on('click', deleteConnectionsDS);
    $('.upload_con').on('click', uploadLog);

    document.getElementById("add_ds").onclick = addDS;
    document.getElementById("del_host").onclick = deleteHosts;
    document.getElementById("del_tag").onclick = deleteTags;
    document.getElementById("del_env").onclick = deleteEnvs;

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
