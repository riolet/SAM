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
        msg += "the datasource '" + getDSName(extra) + "'?"
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
        console.log("Deleting the " + target + ".");
    });
}

function getSelectedDS() {
    "use strict";
    let tabgroup = document.getElementById("ds_choice");
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
    let tabgroup = document.getElementById("ds_choice");
    let tabs = tabgroup.getElementsByTagName("A");
    let i = tabs.length - 1;
    var name = "";
    for (; i >= 0; i -= 1) {
        if (tabs[i].dataset['tab'] === ds) {
            //TODO: if the user renames the ds, will it be reflected here?
            name = tabs[i].innerText;
            break;
        }
    }
    return name;
}

function deleteDS() {
    "use strict";
    let targetDS = getSelectedDS();
    getConfirmation(catDeleteMessage("datasource", targetDS), function () {
        console.log("Deleting " + targetDS + ".");
    });
}

function validateDSName(name) {
    "use strict";
    //must start with a letter (upper OR lower case) and then follow with either letters, numbers, underscore, or space.
    return (typeof(name) === "string" && name.length > 0 && name.match(/^[a-z][a-z0-9_ ]*$/i));
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
    }, function() {
        console.log("Not adding anything");
    })
}

function getDSs() {
    //getDSs() returns DSs as [[id, name], ...] with the index 0 being the selected DS.
    "use strict";
    let datasource_group = document.getElementById("ds_choice");
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
        $(log_ds.parentElement).dropdown("set selected", options[0][0]);
    }
}

function validateUpload() {
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
                console.log("uploading");
            } else {
                console.log("invalid input");
                return false;
            }
        },
        onDeny: function () { console.log("upload cancelled.");}
    })
    .modal("show");
}

function init() {
    "use strict";

    //initialize datasource tabs
    $(".tabular.menu .item").tab();

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
}

window.onload = init;