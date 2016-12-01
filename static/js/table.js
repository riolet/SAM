/*global
    ports, window, filters, cookie_data, $
*/

var DEFAULT_PAGE_SIZE = 10;
var DEFAULT_SORT = "0,asc";

(function () {
    "use strict";
    var cookies = {};

    cookies.set = function (name, value, days) {
        var d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        var expires = "expires=" + d.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/";
    };
    cookies.get = function (name, def_value) {
        var name_code = name + "=";
        var ca = document.cookie.split(";");
        var i;
        var c;
        for (i = 0; i < ca.length; i += 1) {
            c = ca[i];
            while (c.charAt(0) === " ") {
                c = c.substring(1);
            }
            if (c.indexOf(name_code) === 0) {
                return c.substring(name_code.length, c.length);
            }
        }
        return def_value;
    };
    cookies.del = function (name) {
        cookies.set(name, "", -1000);
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
        filters.setFilters(decodeURIComponent(params.filters));
    } else {
        $(".ui.accordion").accordion("open", 0);
    }
}

function applyFilter() {
    "use strict";
    // Apply last filter if it was fully filled out
    var typeSelector = document.getElementById("addFilterType");
    var type = typeSelector.getElementsByTagName("input")[0].value;
    if (filters.private.types.hasOwnProperty(type)) {
        var params = filters.private.extractRowValues(typeSelector);
        if (params.every(function (el) {
            return !!el;
        })) {
            filters.addFilter(type, params);
        }
    }

    // Gather terms for query string
    var searchs = [
        ["page", 1],
        ["page_size", cookie_data.get("page_size", DEFAULT_PAGE_SIZE)],
        ["sort", cookie_data.get("sort", DEFAULT_SORT)]
    ];
    var filterString = filters.getFilters();
    if (filterString.length > 0) {
        searchs.push(["filters", encodeURIComponent(filterString)]);
    }

    // Put together new URL target
    var searchString = "";
    searchs.forEach(function (term) {
        searchString += "&" + term.join("=");
    });
    //window.location.search = "?" + searchString.substr(1);
    window.location.assign("/table?" + searchString.substr(1));
}

function btn_pagesize_callback(e) {
    "use strict";
    var oldSize = cookie_data.get("page_size", DEFAULT_PAGE_SIZE);
    var newSize = e.target.innerText;
    if (newSize !== oldSize) {
        cookie_data.set("page_size", newSize);
        applyFilter();
    }
}

function btn_header_callback(e) {
    "use strict";
    var oldSort = cookie_data.get("sort", DEFAULT_SORT);
    var newSort = e.target.id.substr(6) + ",asc";
    if (newSort !== oldSort) {
        cookie_data.set("sort", newSort);
    } else {
        cookie_data.set("sort", e.target.id.substr(6) + ",desc");
    }
    applyFilter();
}

function hostname_edit_callback(event) {
    "use strict";
    if (event.keyCode === 13 || event.type === "blur") {
        var input = event.target;
        var new_name = input.value;
        var old_name = input.dataset.content;
        var address = event.target.parentNode.parentNode.parentNode.dataset.content;

        if (new_name !== old_name) {
            input.dataset.content = new_name;
            var request = {"node": address, "alias": new_name};
            $.ajax({
                url: "/nodeinfo",
                type: "POST",
                data: request,
                error: function (x, s, e) {
                    console.error("Failed to set name: " + e);
                    console.log("\tText Status: " + s);
                },
                success: function (r) {
                    if (r.hasOwnProperty("result")) {
                        console.log("Result: " + r.result);
                    }
                }
            });
        }
        return true;
    }
    return false;
}

function init() {
    "use strict";

    // For opening the "filters" accordion
    //$(".ui.accordion").accordion("open", 0);
    $(".ui.accordion").accordion();

    //toggle buttons
    $(".ui.swapper.button").state({
        text: {
            inactive: "Vote",
            active: "Voted"
        }
    });

    //Configure Filters
    filters.displayDiv = document.getElementById("filters");
    filters.applyCallback = applyFilter;
    filters.updateDisplay();

    //Configure page_size buttons
    var buttonGroups = document.getElementsByClassName("buttons pagesize");
    var i;
    var j;
    var buttons;
    var saved_pagesize = cookie_data.get("page_size", DEFAULT_PAGE_SIZE);
    for (i = 0; i < buttonGroups.length; i += 1) {
        buttons = buttonGroups[i].getElementsByTagName("button");
        for (j = 0; j < buttons.length; j += 1) {
            buttons[j].onclick = btn_pagesize_callback;
            if (buttons[j].innerText === saved_pagesize) {
                buttons[j].classList.add("active");
            }
        }
    }

    //Configure sorting buttons
    var sorters = document.getElementsByTagName("TH");
    for (j = 0; j < sorters.length; j += 1) {
        sorters[j].onclick = btn_header_callback;
    }

    //Create name inputs
    var targets = $(".td_alias").find("input");
    targets.keyup(hostname_edit_callback);
    targets.blur(hostname_edit_callback);

    //Interpret URL
    importURL();
}

window.onload = function () {
    "use strict";
    init();
};
