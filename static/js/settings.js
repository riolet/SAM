function disambiguateDeletion(what) {
    if (what.indexOf("tag") >= 0) return "tags";
    if (what.indexOf("env") >= 0) return "envs";
    if (what.indexOf("hostname") >= 0) return "aliases";
    if (what.indexOf("connection") >= 0) return "connections";
    return "unknown";
}

function catDeleteMessage(what, extra) {
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
    let target = disambiguateDeletion(what)
    let deleteMessage = catDeleteMessage(target)
    getConfirmation(deleteMessage, function () {
        console.log("Deleting the " + target + ".");
    });
}

function getSelectedDS() {
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
    let targetDS = getSelectedDS();
    getConfirmation(catDeleteMessage("datasource", targetDS), function () {
        console.log("Deleting " + targetDS + ".");
    });
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
}

window.onload = init;