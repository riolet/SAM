function importURL() {
    "use strict";
    var tmp;
    var params = {};
    location.search.substr(1).split("&").forEach(function (item) {
        tmp = item.split("=");
        params[tmp[0]] = tmp[1];
    });
    if (params.hasOwnProperty("filters")) {
        filters.setFilters(decodeURIComponent(params['filters']));
    }
}

function applyFilter() {
    console.log("applying filter!");
    var filterString = filters.getFilters();
    searchs = [
        ["filters", encodeURIComponent(filterString)],
        ["page", 1],
        ["sort", "Address"]
    ];
    var searchString = "";
    searchs.forEach(function (term) {
        searchString += "&" + term.join("=");
    });
    window.location.search = "?" + searchString.substr(1);
}

;(function () {
    "use strict";
    var table = {};
    table.data = [];
    table.html = null;
    table.private = {};
    table.private.tbody = null;
    table.private.thead = null;
    table.private.tfoot = null;
    table.private.columns = [];
    table.setTable = function(tableHTML) {
        table.html = tableHTML;
        table.private.thead = document.createElement("thead");
        table.private.tbody = document.createElement("tbody");
        table.private.tfoot = document.createElement("tfoot");
        table.html.innerHTML = "";
        table.html.appendChild(table.private.thead);
        table.html.appendChild(table.private.tbody);
        table.html.appendChild(table.private.tfoot);
    };
    table.setColumns = function(colNames) {
        table.private.columns = colNames;
        table.private.thead.appendChild(table.buildRow("th", colNames));
    };
    table.addRow = function(data) {
        var tr = table.buildRow('TD', data);
        tbody.appendChild(tr);
    };
    table.clearTable = function(data) {
        table.private.thead.innerHTML = "";
        table.private.tbody.innerHTML = "";
        table.private.tfoot.innerHTML = "";
    };
    table.buildRow = function(type, values) {   //type is "th" or "td"
        var tr = document.createElement("tr");
        var entry;
        var i = 0;
        //This will add "undefined" td elements as needed to match number of columns.
        for (; i < table.private.columns.length; i += 1) {
            entry = document.createElement(type);
            entry.appendChild(document.createTextNode(values[i]));
            tr.appendChild(entry);
        }
        return tr;
    };
    // Export table instance to global scope
    window.table = table;
})();

function init() {
    "use strict";

    $(".ui.accordion").accordion("open", 0);

    //Configure Filters
    filters.displayDiv = document.getElementById("filters");
    filters.applyCallback = applyFilter;
    filters.updateDisplay();

    //Configure Table
    table.setTable(document.getElementById("resultsTable"));
    table.setColumns(["Address", "Hostname", "Role", "Environment", "Tags"]);

    //Interpret URL
    importURL();
}

window.onload = function () {
    "use strict";
    init();
};