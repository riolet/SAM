var DEFAULT_PAGE_SIZE = 10;

;(function () {
    "use strict";
    var cookies = {};

    cookies.set = function(name, value, days) {
        var d = new Date();
        d.setTime(d.getTime() + (days*24*60*60*1000));
        var expires = "expires="+ d.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/";
    };
    cookies.get = function(name, def_value) {
        var name_code = name + "=";
        var ca = document.cookie.split(';');
        for(var i = 0; i <ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name_code) == 0) {
                return c.substring(name_code.length,c.length);
            }
        }
        return def_value;
    };
    cookies.del = function(name) {
        cookies.set(name, '', -1000);
    };

    window.cookie_data = cookies;
}());

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

function applyFilter(page) {
    console.log("applying filter!");
    searchs = [
        ["page", 1],
        ['page_size', cookie_data.get('page_size', DEFAULT_PAGE_SIZE)],
        ["sort", "Address"]
    ];
    var filterString = filters.getFilters();
    if (filterString.length > 0) {
        searchs.push(["filters", encodeURIComponent(filterString)])
    }

    var searchString = "";
    searchs.forEach(function (term) {
        searchString += "&" + term.join("=");
    });
    window.location.search = "?" + searchString.substr(1);
}

function btn_pagesize_callback(e) {
    "use strict";
    var oldSize = cookie_data.get('page_size', DEFAULT_PAGE_SIZE);
    var newSize = e.target.innerText;
    if (newSize !== oldSize) {
        cookie_data.set('page_size', e.target.innerText);
        applyFilter();
    }
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

    // For opening the 'filters' accordion
    //$(".ui.accordion").accordion("open", 0);
    $(".ui.accordion").accordion();

    //toggle buttons
    $(".ui.swapper.button").state({
      text: {
        inactive : 'Vote',
        active   : 'Voted'
      }
    });

    //Configure Filters
    filters.displayDiv = document.getElementById("filters");
    filters.applyCallback = applyFilter;
    filters.updateDisplay();

    //Configure Table
    //table.setTable(document.getElementById("resultsTable"));
    //table.setColumns(["Address", "Hostname", "Role", "Environment", "Tags"]);

    //Configure page_size buttons
    var buttonGroups = document.getElementsByClassName("buttons pagesize");
    var i, j, buttons;
    var saved_pagesize = cookie_data.get("page_size", DEFAULT_PAGE_SIZE);
    for (i=0; i < buttonGroups.length; i += 1) {
        buttons = buttonGroups[i].getElementsByTagName("button");
        for (j=0; j < buttons.length; j += 1) {
            buttons[j].onclick = btn_pagesize_callback;
            if (buttons[j].innerText == saved_pagesize) {
                buttons[j].classList.add("active");
            }
        }
    }

    //Interpret URL
    importURL();
}

window.onload = function () {
    "use strict";
    init();
};