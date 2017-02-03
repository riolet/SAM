/*global
    ports, window, filters, cookie_data, $, g_known_tags, g_known_envs
*/

/**
 *  Class Filters:
 *  public:
 *    filters = [];
 *    displayDiv = null;
 *    applyCallback = null;
 *  private:
 *    types = {};
 *
 *  public methods:
 *    addFilter(type, params)  // Add a new filter to the state
 *    deleteFilter(index)  // Remove a filter from the state
 *    updateDisplay()  //updates the HTML display from the state
 *    getFilters()  //returns an object encapsulating the filter state (for use in ajax requests)
 *    setFilters(filterstring) //imports a filter set based on an encoded string
 *
 *  private methods:
 *      //create filter list HTML items, and filter objects
 *      createFilter(enabled, type, params, row)
 *      createSubnetFilterRow(subnet)
 *      createMaskFilterRow(subnet)
 *      createEnvFilterRow(subnet)
 *      createPortFilterRow(comparator, port)
 *      createTagFilterRow(has, tags)
 *      createTargetFilterRow(has, tags)
 *      createConnectionsFilterRow(comparator, limit)
 *
 *      //create HTML for each filter type
 *
 *      //create form component markup
 *      markupBoilerplate(enabled)
 *      markupSelection(name, placeholderText, options, selected)
 *      markupTags(name, placeholderText, preset)
 *      markupInput(name, placeholderText, preset)
 *      markupSpan(text)
 *
 *      //+, X callback events to add and delete
 *      addCallback(event)
 *      deleteCallback(event)
 *      updateEvent(event)  //called when an input value changes
 *      getRowIndex(rowHTML)
 *      extractRowValues(head)  //reads the HTML for a filter row to get the input values provided by the user.
 *
 *      updateSummary()  //the short filter text when the filter panel isn't expanded.
 *      encodeFilters(filterArray) //encode the filter set as a string
 *      decodeFilters(filterString) //decode a filter string into a set of filters
 *      createFilterCreator()  //the "new filter" row with the "+" button.
 *
 */


(function () {
    "use strict";
    var filters = {};

    filters.filters = [];
    filters.displayDiv = null;
    filters.applyCallback = null;
    filters.ds = null;
    filters.private = {};
    filters.private.types = {};

    // ==================================
    // Public methods
    // ==================================
    filters.addFilter = function (type, params) {
        //create a filter item and add it to the array
        //a filter item includes description and reference to an HTML element
        var newFilter = null;
        var source = null;
        if (filters.private.types.hasOwnProperty(type)) {
            source = filters.private.types[type];
            if (params.length === source[2].length) {
                var paramObj = {};
                source[2].forEach(function (name, index) {
                    paramObj[name] = params[index];
                });
                newFilter = filters.private.createFilter(true, type, paramObj, source[0]);
            } else {
                console.error("addFilter: Params length didn't match:");
                console.log(arguments);
            }
        } else {
            console.error("addFilter: No filter type matched: " + type);
            console.log(arguments);
        }
        if (newFilter !== null) {
            filters.filters.push(newFilter);
        }
    };
    filters.deleteFilter = function (index) {
        //remove a filter item from the list
        filters.filters.splice(index, 1);
        filters.private.updateSummary();
    };
    filters.updateDisplay = function () {
        //compare the existing display to the filters array and update it when there's a mismatch?
        //or, empty and rebuild the filter list.
        if (filters.displayDiv === null) {
            return;
        }

        //Apply Filter button
        var buttonIcon = document.createElement("i");
        buttonIcon.className = "refresh blue icon";
        var buttonApply = document.createElement("button");
        buttonApply.className = "ui compact icon button";
        buttonApply.onclick = filters.applyCallback;
        buttonApply.appendChild(buttonIcon);
        buttonApply.appendChild(document.createTextNode("Apply Filter"));

        //DS Switcher
        var DSSelector = document.createElement("DIV");
        var pairs = [];
        Object.keys(g_dses).forEach(function (key) {
          pairs.push([g_dses[key], key]);
        });
        var ds = filters.ds || Object.values(g_dses)[0];
        DSSelector.appendChild(filters.private.markupSelection("ds_choice", "Data source", pairs, ds, filters.private.dsCallback));
        DSSelector.appendChild(filters.private.markupSpan("Data Source"))

        // Clear the div
        filters.displayDiv.innerHTML = "";
        // Put new things in the div
        filters.displayDiv.appendChild(DSSelector);
        filters.filters.forEach(function (filter) {
            filters.displayDiv.appendChild(filter.html);
        });
        filters.displayDiv.appendChild(filters.private.createFilterCreator());
        filters.displayDiv.appendChild(buttonApply);
        filters.private.updateSummary();
    };
    filters.getFilters = function () {
        //collapse the filter list into a minimal set of data
        var filterArray = filters.filters.reduce(function (data, filter) {
            var newItem = {};
            Object.keys(filter).forEach(function (key) {
                if (key === "html") {
                    return;
                }
                newItem[key] = filter[key];
            });
            data.push(newItem);
            return data;
        }, []);
        return filters.private.encodeFilters(filterArray);
    };
    filters.setFilters = function (filterString) {
        if (filterString === "") {
            return;
        }
        filters.filters = filters.private.decodeFilters(filterString);
        filters.updateDisplay();
    };

    // ==================================
    // Private methods
    // ==================================
    filters.private.createFilter = function(enabled, type, params, row) {
      let filter = {};
      let filterdiv = filters.private.markupBoilerplate(enabled);
      let parts = row(params);
      parts.forEach(function (part) {
        filterdiv.appendChild(part);
      });

      filter.enabled = enabled;
      filter.type = type;
      filter.html = filterdiv;
      Object.keys(params).forEach(function (key) {
        filter[key] = params[key];
      });
      return filter;
    }

    filters.private.createSubnetFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSpan("Return results from subnet "));
        parts.push(filters.private.markupSelection("subnet", "Choose subnet...", [
            ["8", "/8"],
            ["16", "/16"],
            ["24", "/24"],
            ["32", "/32"]
        ], params.subnet));
        return parts;
    };
    filters.private.createMaskFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSpan("Search children of "));
        parts.push(filters.private.markupInput("mask", "192.168.0.0/24", params.mask));
        return parts;
    };
    filters.private.createRoleFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSpan("Client/Server ratio is "));
        parts.push(filters.private.markupSelection("comparator", "more/less than", [
            [">", "more than"],
            ["<", "less than"]
        ], params.comparator));
        parts.push(filters.private.markupInput("ratio", "0.5", params.ratio));
        parts.push(filters.private.markupSpan(" (0 = client, 1 = server)"));
        return parts;
    };
    filters.private.createEnvFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSpan("Node environment is "));
        parts.push(filters.private.markupSelection("env", "Choose environment",
                g_known_envs.map(function (e) { return [e, e];}), params.env));
        return parts;
    };
    filters.private.createPortFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSelection("connection", "Filter type...", [
            ["0", "Connects to"],
            ["1", "Doesn't connect to"],
            ["2", "Receives connections from"],
            ["3", "Doesn't receive connections from"]
        ], params.connection));
        parts.push(filters.private.markupSpan("another host via port"));
        //parts.push(filters.private.markupInput("port", "80,443,8000-8888", port));
        parts.push(filters.private.markupInput("port", "443", params.port));
        return parts;
    };
    filters.private.createProtocolFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSelection("handles", "handles in/outbound", [
            ["0", "Handles inbound"],
            ["1", "Doesn't handle inbound"],
            ["2", "Initiates outbound"],
            ["3", "Doesn't intiate outbound"]
        ], params.handles));
        parts.push(filters.private.markupSpan("connections using protocol"));
        parts.push(filters.private.markupInput("protocol", "UDP", params.protocol));
        return parts;
    };
    filters.private.createTagFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSpan("host "));
        parts.push(filters.private.markupSelection("has", "has/not", [
            ["1", "has"],
            ["0", "doesn't have"]
        ], params.has));
        parts.push(filters.private.markupSpan(" tags: "));
        parts.push(filters.private.markupTags("tags", "Choose tag(s)",
                g_known_tags.map(function (tag) { return [tag, tag];}), params.tags));
        return parts;
    };
    filters.private.createTargetFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSpan("Show only hosts that "));
        parts.push(filters.private.markupSelection("to", "connect to/from", [
            ["0", "connect to"],
            ["1", "don't connect to"],
            ["2", "receive connections from"],
            ["3", "don't receive connections from"]
        ], params.to));
        parts.push(filters.private.markupSpan(" IP address:"));
        parts.push(filters.private.markupInput("target", "192.168.0.4", params.target));
        return parts;
    };
    filters.private.createConnectionsFilterRow = function (params) {
        var parts = [];
        if (params == undefined) {
          params = {};
        }

        parts.push(filters.private.markupSpan("Handles "));
        parts.push(filters.private.markupSelection("comparator", "Filter type...", [
            [">", "more than"],
            ["<", "fewer than"]
        ], params.comparator));
        parts.push(filters.private.markupInput("limit", "a number of", params.limit));
        parts.push(filters.private.markupSelection("direction", "in/outbound", [
            ["i", "inbound"],
            ["o", "outbound"],
            ["c", "combined"]
        ], params.direction));
        parts.push(filters.private.markupSpan("connections / second."));
        return parts;
    };

    filters.private.markupBoilerplate = function (enabled) {
        // enabled: true/false, enable the filter checkbox

        //The delete button
        var deleteIcon = document.createElement("i");
        deleteIcon.className = "delete red icon";
        var deleteButton = document.createElement("button");
        deleteButton.className = "ui compact icon button";
        deleteButton.onclick = filters.private.deleteCallback;
        deleteButton.appendChild(deleteIcon);

        //The Enable/Disable toggle
        var toggleInput = document.createElement("input");
        toggleInput.title = "Enable this filter";
        toggleInput.type = "checkbox";
        toggleInput.checked = enabled;
        toggleInput.name = "enabled";
        toggleInput.onchange = filters.private.updateEvent;
        var toggleLabel = document.createElement("label");
        toggleLabel.className = "inline";
        var toggleEnabled = document.createElement("div");
        toggleEnabled.className = "ui toggle checkbox";
        toggleEnabled.appendChild(toggleInput);
        toggleEnabled.appendChild(toggleLabel);

        //The encompassing div
        var filterdiv = document.createElement("div");
        filterdiv.classList.add("filter");
        filterdiv.appendChild(deleteButton);
        filterdiv.appendChild(toggleEnabled);
        return filterdiv;
    };
    filters.private.markupSelection = function (name, placeholderText, options, selected, onchange) {
        //name: the form name used by this element
        //placeholderText: text shown before a selection is made
        //options: the selection choices. Pairs of data value and string, like [["=", "equal to"], ["<", "less than"]]

        //The underlaying input box
        var input = document.createElement("input");
        input.name = name;
        input.type = "hidden";
        input.onchange = onchange || filters.private.updateEvent;

        //The dropdown icon
        var icon = document.createElement("i");
        icon.className = "dropdown icon";

        //The placeholder text (before making a selection)
        var placeholder = document.createElement("div");
        placeholder.className = "default text";
        placeholder.appendChild(document.createTextNode(placeholderText));

        var menu = document.createElement("div");
        menu.className = "menu";
        var menuitem;
        options.forEach(function (item) {
            menuitem = document.createElement("div");
            menuitem.className = "item";
            menuitem.dataset.value = item[0];
            menuitem.appendChild(document.createTextNode(item[1]));
            menu.appendChild(menuitem);
        });

        //The encompassing div
        var selectionDiv = document.createElement("div");
        selectionDiv.className = "ui selection dropdown";
        selectionDiv.appendChild(input);
        selectionDiv.appendChild(icon);
        selectionDiv.appendChild(placeholder);
        selectionDiv.appendChild(menu);

        //Transform to semantic-ui styled selection box
        if (selected) {
            $(selectionDiv).dropdown("set exactly", selected);
        } else {
            $(selectionDiv).dropdown();
        }
        return selectionDiv;
    };
    filters.private.markupTags = function (name, placeholderText, options, selected) {
        var selectionDiv = filters.private.markupSelection(name, placeholderText, options);
        selectionDiv.className = "ui multiple search selection dropdown";
        //$(selectionDiv).dropdown("setup menu", {
        //    allowAdditions: true
        //});
        $(selectionDiv).dropdown({
            allowAdditions: true
        });
        if (selected) {
            var tags = selected.split(",");
            $(selectionDiv).dropdown("set exactly", tags);
        }
        return selectionDiv;
    };
    filters.private.markupInput = function (name, placeholderText, preset) {
        //input element
        var input = document.createElement("input");
        input.placeholder = placeholderText;
        input.type = "text";
        input.onchange = filters.private.updateEvent;
        input.name = name;

        //encompassing div
        var inputdiv = document.createElement("div");
        inputdiv.className = "ui input";
        inputdiv.appendChild(input);

        //fill in known data
        if (preset) {
            input.value = preset;
        }

        return inputdiv;
    };
    filters.private.markupSpan = function (text) {
        var span = document.createElement("span");
        span.appendChild(document.createTextNode(text));
        return span;
    };

    filters.private.dsCallback = function (event) {
        filters.ds = event.target.value;
    }
    filters.private.addCallback = function (event) {
        //extract: filter type
        var button = event.target;
        while (button.tagName !== "BUTTON") {
            button = button.parentElement;
        }
        var typeSelector = button.nextElementSibling;
        var type = typeSelector.getElementsByTagName("input")[0].value;
        if (!filters.private.types.hasOwnProperty(type)) {
            return;
        }
        var params = filters.private.extractRowValues(typeSelector);
        filters.addFilter(type, params);
        //filters.private.deleteCallback(event);
        filters.updateDisplay();
    };
    filters.private.deleteCallback = function (event) {
        var button = event.target;
        while (button.tagName !== "BUTTON") {
            button = button.parentElement;
        }
        var row = button.parentElement;
        var i = filters.private.getRowIndex(row);
        if (i !== -1) {
            filters.deleteFilter(i);
            $(row).remove();
        }
    };
    filters.private.updateEvent = function (e) {
        var input = e.target;
        var newValue = input.value;
        if (e.target.parentElement.classList.contains("checkbox")) {
            newValue = input.checked;
        }
        var row = input;
        //ascend the heirarchy until you hit null OR an element that is both a DIV and contains "filter" class
        while (row !== null && !(row.tagName === "DIV" && row.classList.contains("filter"))) {
            row = row.parentNode;
        }
        var i = filters.private.getRowIndex(row);
        if (i !== -1) {
            filters.filters[i][input.name] = newValue;
            filters.private.updateSummary();
        }
    };
    filters.private.getRowIndex = function (rowHTML) {
        var i = filters.filters.length - 1;
        while (i >= 0 && filters.filters[i].html !== rowHTML) {
            i -= 1;
        }
        return i;
    };
    filters.private.extractRowValues = function (head) {
        var params = [];
        var walker = head.nextElementSibling;
        var inputs;
        while (walker !== undefined && walker !== null) {
            inputs = walker.getElementsByTagName("input");
            if (inputs.length > 0) {
                params.push([inputs[0].name, inputs[0].value]);
            }
            walker = walker.nextElementSibling;
        }

        //sort the values by lexical order of keys
        params.sort(function (a, b) {
            if (a[0] < b[0]) {
                return -1;
            }
            if (b[0] < a[0]) {
                return 1;
            }
            return 0;
        });
        //return just the values
        return params.map(function (e) {
            return e[1];
        });
    };

    filters.private.updateSummary = function () {
        var header = filters.displayDiv.previousElementSibling;
        var icon = header.getElementsByTagName("i")[0];
        header.innerHTML = "";
        header.appendChild(icon);
        var span;

        //span = filters.private.markupSpan("Filter: ");
        header.appendChild(document.createTextNode("Filter: "));

        //span.style = "color: grey;";
        if (filters.filters.length > 0) {
            filters.filters.forEach(function (filter) {
                if (filter.type === "subnet") {
                    span = filters.private.markupSpan("subnet /" + filter.subnet);

                } else if (filter.type === "mask") {
                    span = filters.private.markupSpan("within " + filter.mask);

                } else if (filter.type === "port") {
                    if (filter.connection === "0") {
                        span = filters.private.markupSpan("conn to (" + filter.port + ")");
                    } else if (filter.connection === "1") {
                        span = filters.private.markupSpan("X conn to (" + filter.port + ")");
                    } else if (filter.connection === "2") {
                        span = filters.private.markupSpan("conn from (" + filter.port + ")");
                    } else if (filter.connection === "3") {
                        span = filters.private.markupSpan("X conn from (" + filter.port + ")");
                    }

                } else if (filter.type === "connections") {
                    var dir = ""
                    if (filter.direction == 'i') {
                      dir = " (in)";
                    } else if (filter.direction == 'o') {
                      dir = " (out)";
                    }
                    span = filters.private.markupSpan(filter.comparator + filter.limit + " conns/s" + dir);

                } else if (filter.type === "protocol") {
                    if (filter.handles === "0") {
                        span = filters.private.markupSpan(filter.protocol+ " in");
                    } else if (filter.handles === "1") {
                        span = filters.private.markupSpan("no " + filter.protocol + " in");
                    } else if (filter.handles === "2") {
                        span = filters.private.markupSpan(filter.protocol + " out");
                    } else if (filter.handles === "3") {
                        span = filters.private.markupSpan("no " + filter.protocol + " out");
                    }

                } else if (filter.type === "target") {
                    if (filter.to === "0") {
                        span = filters.private.markupSpan("to " + filter.target);
                    } else if (filter.to === "1") {
                        span = filters.private.markupSpan("not to " + filter.target);
                    } else if (filter.to === "2") {
                        span = filters.private.markupSpan("from " + filter.target);
                    } else if (filter.to === "3") {
                        span = filters.private.markupSpan("not from " + filter.target);
                    }

                } else if (filter.type === "tags") {
                    if (filter.has === "1") {
                        span = filters.private.markupSpan("tagged (" + filter.tags + ")");
                    } else {
                        span = filters.private.markupSpan("no tag (" + filter.tags + ")");
                    }

                } else if (filter.type === "env") {
                    span = filters.private.markupSpan("env: " + filter.env);

                } else if (filter.type === "role") {
                    span = filters.private.markupSpan(filter.comparator + Math.round(filter.ratio * 100) + "% server");
                }
                if (!filter.enabled) {
                    span.style = "color: LightGray;";
                }
                header.appendChild(span);
                header.appendChild(document.createTextNode(", "));
            });
            //remove last comma
            header.lastChild.remove();
        } else {
            header.appendChild(document.createTextNode("none"));
        }
    };
    filters.private.encodeFilters = function (filterArray) {
        var filterString = "";
        var f_s;
        filterArray.forEach(function (filter) {
            //Save type
            var f_type = Object.keys(filters.private.types).sort().indexOf(filter.type);
            f_s = f_type.toString();
            delete filter.type;

            //Save enabled state.
            if (filter.enabled) {
                f_s += ";1";
            } else {
                f_s += ";0";
            }
            delete filter.enabled;

            //Save other data alphabetically
            var keys = Object.keys(filter);
            keys.sort();
            keys.forEach(function (k) {
                f_s += ";" + filter[k];
            });
            filterString += "|" + f_s;
        });
        return filters.ds + filterString;
    };
    filters.private.decodeFilters = function (filterGET) {
        var decodedFilters = [];
        let types = Object.keys(filters.private.types).sort()

        //split by |
        var filterList = filterGET.split("|");
        filters.ds = filterList[0]
        filterList.slice(1).forEach(function (filterString) {
            // Should I decodeURIComponent()?
            // split by ;
            var filterArgs = filterString.split(";");
            var typeIndex = filterArgs.shift();
            var type = types[typeIndex];
            var filterReg = filters.private.types[type];
            var enabled = filterArgs.shift();
            enabled = (enabled === "1");
            //param count matches:
            if (filterArgs.length !== filterReg[2].length) {
              console.error("Cannot import "+type+" filter. Param length is " + filterArgs.length + ". (expected " + filterReg[2].length + ")");
              return;
            }
            var params = {};
            filterReg[2].forEach(function (name, index) {
              params[name] = filterArgs[index];
            });

            var filter = filters.private.createFilter(enabled, type, params, filterReg[0])
            decodedFilters.push(filter);
        });
        return decodedFilters;
    };

    //Register filter types, and their constructors
    // format: [row-builder(), type"", param_names[]]
    filters.private.types.connections = [filters.private.createConnectionsFilterRow, "connections", ["comparator", "direction", "limit"]];
    filters.private.types.env = [filters.private.createEnvFilterRow, "env", ["env"]];
    filters.private.types.mask = [filters.private.createMaskFilterRow, "mask", ["mask"]];
    filters.private.types.port = [filters.private.createPortFilterRow, "port", ["connection", "port"]];
    filters.private.types.protocol = [filters.private.createProtocolFilterRow, "protocol", ["handles", "protocol"]];
    filters.private.types.role = [filters.private.createRoleFilterRow, "role", ["comparator", "ratio"]];
    filters.private.types.tags = [filters.private.createTagFilterRow, "tags", ["has", "tags"]];
    filters.private.types.target = [filters.private.createTargetFilterRow, "target", ["target", "to"]];
    filters.private.types.subnet = [filters.private.createSubnetFilterRow, "subnet", ["subnet"]];

    filters.private.createFilterCreator = function () {
        //The add button
        var addIcon = document.createElement("i");
        addIcon.className = "add green icon";
        var addButton = document.createElement("button");
        addButton.className = "ui compact icon button";
        addButton.onclick = filters.private.addCallback;
        addButton.appendChild(addIcon);

        //The type selector
        var typeOptions = Object.keys(filters.private.types).map(function (x) {
            return [x, x];
        });
        var typeSelector = filters.private.markupSelection("type", "Filter Type", typeOptions);
        typeSelector.id = "addFilterType";

        //The encompassing div
        var filterdiv = document.createElement("div");
        filterdiv.classList.add("filter");
        filterdiv.appendChild(addButton);
        filterdiv.appendChild(typeSelector);

        //Update trick
        $(typeSelector).dropdown({
            action: "activate",
            onChange: function (type) {
                while (typeSelector.nextElementSibling !== null) {
                    filterdiv.removeChild(typeSelector.nextElementSibling);
                }
                var filterParts = filters.private.types[type][0]();
                filterParts.forEach(function (part) {
                    filterdiv.appendChild(part);
                });
            }
        });

        return filterdiv;
    };

    // Export filters instance to global scope
    window.filters = filters;
}());