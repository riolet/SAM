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

(function () {
    "use strict";
    var csv = {};

    csv.escape = function (datum, escape) {
        var escaped = datum.replace(/\"/g, escape + "\"");
        if (escaped.indexOf(",") !== -1) {
            return "\"" + escaped + "\"";
        }
        return escaped;
    }

    csv.encode_row = function (ary, colsep, escape) {
        if (ary.length == 0) {
            return "";
        }
        var first = csv.escape(ary.shift(), escape);
        if (ary.length == 0) {
            return first;
        }
        return ary.reduce(function (accumulator, currentValue) {
            return accumulator + colsep + csv.escape(currentValue, escape);
        }, first);
    }

    csv.encode = function (data, colsep, rowsep, escape) {
        if (data.length == 0) {
            return ""
        }
        var first = csv.encode_row(data.shift(), colsep, escape);

        if (data.length == 0) {
            return first;
        }
        return data.reduce(function (accumulator, currentValue) {
            return accumulator + rowsep + csv.encode_row(currentValue, colsep, escape);
        }, first);
    }

    csv.download = function (data, filename) {
        var holder = document.getElementById("linkplace");
        var downloadLink = document.createElement("A");
        downloadLink.download = filename;
        downloadLink.href = "data:application/csv;charset=utf-8," + encodeURIComponent(data);
        downloadLink.style="display: none";

        //place into the DOM so that .click() works
        holder.innerHTML = "";
        holder.appendChild(downloadLink);
        downloadLink.click();
    }

    window.csv = csv;
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
    var link = "/table?" + searchString.substr(1);
    if (window.location.pathname.substr(1,4) === "demo") {
      link = "/demo" + link
    }
    window.location.assign(link);
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
                url: "/nodes",
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

function get_stamp() {
    "use strict";
    var d = new Date();
    return d.getFullYear() + "_" + d.getMonth() + "_" + d.getDay() + "_" + d.getHours() + "_" + d.getMinutes();
}

function scrape_thead(thead) {
    "use strict";
    var ths = thead.getElementsByTagName("TH");
    var headers = [];
    var i;
    for(i=ths.length - 1; i >= 0; i -= 1) {
        headers[i] = ths[i].innerText;
    }
    console.log("Headers: ");
    console.log(headers);
    return headers;
}

function scrape_tbody(tbody) {
    "use strict";
    var trs = tbody.getElementsByTagName("TR");
    var tds;
    var rows = [];
    var row;
    var irow;
    var icol;
    for (irow = trs.length - 1; irow >= 0; irow -= 1) {
        row = [];
        tds = trs[irow].getElementsByTagName("TD");
        for (icol = tds.length - 1; icol >= 0; icol -= 1) {
            row[icol] = tds[icol].innerText;
            if (row[icol] === "") {
                //console.log("table empty at row " + irow + " and column " + icol);
                //For column Hostname:
                //    try searching for an input with a value
                var inputs = tds[icol].getElementsByTagName("INPUT");
                if (inputs.length == 1) {
                    row[icol] = inputs[0].value;
                }
                //For column Tags:
                //TODO: Should be comma separated? Currently works as just concatenated with spaces
            }
        }
        rows[irow] = row;
    }
    return rows;
}

function table_to_csv(table, colsep=",", rowsep="\r\n", escape="\\") {
    var headers = scrape_thead(table.getElementsByTagName("THEAD")[0]);
    var rows = scrape_tbody(table.getElementsByTagName("TBODY")[0]);
    rows.unshift(headers);
    return csv.encode(rows, colsep, rowsep, escape);

    //  http://localhost:8080/table?page=1&page_size=20&sort=0,asc&filters=3%3B1%3B0%3B8080%7C6%3B1%3B32
}

function download(link, filename) {
    var holder = document.getElementById("linkplace");
    var downloadLink = document.createElement("A");
    downloadLink.download = filename;
    downloadLink.href = link;
    downloadLink.style="display: none";

    //place into the DOM so that .click() works
    holder.innerHTML = "";
    holder.appendChild(downloadLink);
    downloadLink.click();
}

function initiateDownload(event) {
    "use strict";
    var target = event.target;
    var btn_text = target.innerText;
    if (btn_text.toLocaleLowerCase().indexOf("all") == -1) {
        //download page
        console.log("Downloading this page of data at " + get_stamp());
        var data = table_to_csv(document.getElementById("resultsTable"));
        csv.download(data, "table_" + get_stamp() + ".csv");
    } else {
        //download all
        console.log("Downloading ALL the data");
        var download_string = "/table?download=1&" + location.search.substr(1)
        if (window.location.pathname.substr(1,4) === "demo") {
          download_string = "/demo" + download_string
        }
        download(download_string, "table_" + get_stamp() + ".csv")
    }
}

function init() {
    "use strict";

    // For opening the "filters" accordion
    //$(".ui.accordion").accordion("open", 0);
    $(".ui.accordion").accordion();

    $(".dropdown.button").dropdown({
        action: 'combo'
    });
    document.getElementById("btn_dl").onclick = initiateDownload

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

    //"demo" message box
    if (window.location.pathname.substr(1,4) === "demo") {
      let msgbox = document.getElementById("demo_msg");
      $(msgbox).transition("fade");
    }
    $('.message .close')
      .on('click', function() {
        $(this)
          .closest('.message')
          .transition('fade');
    });


    //Create name inputs
    var targets = $(".td_alias").find("input");
    targets.keyup(hostname_edit_callback);
    targets.blur(hostname_edit_callback);

    //Interpret URL
    importURL();
}
