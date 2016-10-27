/**
 *  Class Filters:
 *  public:
 *    filters = [];
 *    displayDiv = null;
 *  private:
 *    types = {};
 *
 *  public methods:
 *    addFilter(type, params)  // Add a new filter to the state
 *    deleteFilter(index)  // Remove a filter from the state
 *    updateDisplay()  //updates the HTML display from the state
 *    getFilters()  //returns an object encapsulating the filter state (for use in ajax requests)
 *
 *  private methods:
 *      //create filter list HTML items, and filter objects
 *      createSubnetFilter(subnet)
 *      createPortFilter(comparator_port)
 *      createTagFilter(has_tags)
 *      createConnectionsFilter(comparator_limit)
 *
 *      //create HTML for each filter type
 *      createSubnetFilterRow(subnet)
 *      createPortFilterRow(comparator, port)
 *      createTagFilterRow(has, tags)
 *      createConnectionsFilterRow(comparator, limit)
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
 *      createFilterCreator()  //the "new filter" row with the '+' button.
 *
 */


;(function () {
    "use strict";
    var filters = {};

    filters.filters = [];
    filters.displayDiv = null;
    filters.applyCallback = null;
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
            if (params.length === source[2]) {
                newFilter = source[0](params, true);
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
        // ???trigger the removal from the display???
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

        filters.displayDiv.innerHTML = "";
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
            var newItem = {}
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
        if (filterString == "") {
            return;
        }
        filters.filters = filters.private.decodeFilters(filterString);
        filters.updateDisplay();
    };

    // ==================================
    // Private methods
    // ==================================
    filters.private.createSubnetFilter = function (subnet, enabled) {
        var filter;
        var filterdiv = filters.private.markupBoilerplate(enabled);
        var parts = filters.private.createSubnetFilterRow(subnet);
        parts.forEach(function (part) { filterdiv.appendChild(part); });

        filter = {};
        filter.enabled = true;
        filter.type = "subnet";
        filter.subnet = subnet;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createSubnetFilterRow = function (subnet) {
        var parts = [];
        parts.push(filters.private.markupSpan("Subnet mask is "));
        parts.push(filters.private.markupSelection("subnet", "Choose subnet...", [
            ['8', '/8'],
            ['16', '/16'],
            ['24', '/24'],
            ['32', '/32'],
        ], subnet));
        return parts;
    };
    filters.private.createPortFilter = function (includes_port, enabled) {
        var includes, port;
        if (includes_port) {
            includes = includes_port[0];
            port = includes_port[1];
        }
        var filterdiv = filters.private.markupBoilerplate(enabled);
        var parts = filters.private.createPortFilterRow(includes, port);
        parts.forEach(function (part) { filterdiv.appendChild(part); });

        var filter = {};
        filter.enabled = true;
        filter.type = "port";
        filter.includes = includes;
        filter.port = port;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createPortFilterRow = function (includes, port) {
        var parts = [];
        parts.push(filters.private.markupSpan("Ports accessed "));
        parts.push(filters.private.markupSelection("includes", "Filter type...", [
            ['1', 'include'],
            ['0', 'exclude'],
        ], includes));
        parts.push(filters.private.markupInput("port", "80,443,8000-8888", port));
        return parts;
    };
    filters.private.createTagFilter = function (has_tags, enabled) {
        var has, tags;
        if (has_tags) {
            has = has_tags[0];
            tags = has_tags[1];
        } else {
            has = "1";
        }
        var filterdiv = filters.private.markupBoilerplate(enabled);
        var parts = filters.private.createTagFilterRow(has, tags);
        parts.forEach(function (part) { filterdiv.appendChild(part); });

        var filter = {};
        filter.enabled = true;
        filter.type = "tags";
        filter.has = has;
        filter.tags = tags;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createTagFilterRow = function (has, tags) {
        var parts = [];
        parts.push(filters.private.markupSpan("host "));
        parts.push(filters.private.markupSelection("has", "has/n't", [
            ["1", "has"],
            ["0", "doesn't have"],
        ], has));
        parts.push(filters.private.markupSpan(" tags: "));
        parts.push(filters.private.markupTags("tags", "Choose tag(s)", [
            ['server', "Server"],
            ["client", "Client"]
        ], tags));
        return parts;
    };
    filters.private.createConnectionsFilter = function (comparator_limit, enabled) {
        var comparator, limit;
        if (comparator_limit) {
            comparator = comparator_limit[0];
            limit = comparator_limit[1];
        }
        var filterdiv = filters.private.markupBoilerplate(enabled);
        var parts = filters.private.createConnectionsFilterRow(comparator, limit);
        parts.forEach(function (part) { filterdiv.appendChild(part); });

        var filter = {};
        filter.enabled = true;
        filter.type = "connections";
        filter.comparator = comparator;
        filter.limit = limit;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createConnectionsFilterRow = function (comparator, limit) {
        var parts = [];
        parts.push(filters.private.markupSpan("Is involved in "));
        parts.push(filters.private.markupSelection("comparator", "Filter type...", [
            ['=', 'equal to'],
            ['<', 'less than'],
            ['>', 'greater than'],
        ], comparator));
        parts.push(filters.private.markupInput("limit", "a number of", limit));
        parts.push(filters.private.markupSpan("connections."));
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
    filters.private.markupSelection = function (name, placeholderText, options, selected) {
        //name: the form name used by this element
        //placeholderText: text shown before a selection is made
        //options: the selection choices. Pairs of data value and string, like [["=", "equal to"], ["<", "less than"]]

        //The underlaying input box
        var input = document.createElement("input");
        input.name = name;
        input.type = "hidden";
        input.onchange = filters.private.updateEvent;

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
            menuitem.dataset['value'] = item[0];
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
            $(selectionDiv).dropdown('set exactly', selected);
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
        var inputdiv = document.createElement("div")
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

    filters.private.addCallback = function (event) {
        var row = event.target.parentElement;
        //extract: filter type
        var typeSelector = event.target.nextElementSibling;
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
        var row = event.target.parentElement;
        var i = filters.private.getRowIndex(row);
        if (i !== -1) {
            filters.deleteFilter(i);
            $(row).remove();
        }
    };
    filters.private.updateEvent = function(e) {
        var input = e.target;
        var newValue = input.value;
        if (e.target.parentElement.classList.contains("checkbox")) {
            newValue = input.checked;
        }
        var row = input;
        while (row !== null && !(row.tagName === "DIV" && row.classList.contains("filter"))) {
            row = row.parentElement;
        }
        var i = filters.private.getRowIndex(row);
        if (i !== -1) {
            filters.filters[i][input.name] = newValue;
            filters.private.updateSummary();
        }
    };
    filters.private.getRowIndex = function(rowHTML) {
        var i = filters.filters.length - 1;
        while (i >= 0 && filters.filters[i].html !== rowHTML) {
            i -= 1;
        }
        return i;
    };
    filters.private.extractRowValues = function(head) {
        var params = [];
        var walker = head.nextElementSibling;
        var inputs;
        var i;
        while (walker !== undefined && walker !== null) {
            inputs = walker.getElementsByTagName("input");
            if (inputs.length > 0) {
                params.push(inputs[0].value);
            }
            walker = walker.nextElementSibling;
        }
        return params;
    };

    filters.private.updateSummary = function() {
        //build summary
        var summary = "Filter: ";
        if (filters.filters.length > 0) {
            filters.filters.forEach(function (filter) {
                if (filter.type === "subnet") {
                    summary += "subnet /" + filter.subnet;
                } else if (filter.type === "port") {
                    if (filter.includes === "1") {
                        summary += "includes (" + filter.port + ")";
                    } else {
                        summary += "excludes (" + filter.port + ")";
                    }
                } else if (filter.type === "connections") {
                    if (filter.comparator === "=") {
                        summary += filter.limit + " conns";
                    } else {
                        summary += filter.comparator + filter.limit + " conns";
                    }
                } else if (filter.type === "tags") {
                    if (filter.has === "1") {
                        summary += "tagged (" + filter.tags + ")";
                    } else {
                        summary += "no tag (" + filter.tags + ")";
                    }
                }
                summary += ", ";
            });
            summary = summary.slice(0, -2);
        } else {
            summary += "none";
        }

        //display summary
        var header = filters.displayDiv.previousElementSibling
        var icon = header.getElementsByTagName("i")[0];
        header.innerHTML = "";
        header.appendChild(icon);
        header.appendChild(document.createTextNode(summary));
    };
    filters.private.encodeFilters = function(filterArray) {
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
            keys.forEach(function(k) {
                f_s += ";" + filter[k];
            });
            filterString += "|" + f_s;
        });
        return filterString.substr(1);
    }
    filters.private.decodeFilters = function(filterGET) {
        var decodedFilters = [];

        //split by &
        var filterList = filterGET.split("|");
        filterList.forEach(function (filterString) {
            // Should I decodeURIComponent()?
            // split by |
            var filterArgs = filterString.split(';');
            var typeIndex = filterArgs.shift();
            var enabled = filterArgs.shift();
            enabled = (enabled === "1")
            var type = Object.keys(filters.private.types).sort()[typeIndex];
            var filter = filters.private.types[type][0](filterArgs, enabled);
            decodedFilters.push(filter);
        });
        return decodedFilters;
    }

    //Register filter types, and their constructors
    filters.private.types['subnet'] = [filters.private.createSubnetFilter, filters.private.createSubnetFilterRow, 1];
    filters.private.types['port'] = [filters.private.createPortFilter, filters.private.createPortFilterRow, 2];
    filters.private.types['connections']= [filters.private.createConnectionsFilter, filters.private.createConnectionsFilterRow, 2];
    filters.private.types['tags']= [filters.private.createTagFilter, filters.private.createTagFilterRow, 2];

    filters.private.createFilterCreator = function () {
        //The add button
        var addIcon = document.createElement("i");
        addIcon.className = "add green icon";
        var addButton = document.createElement("button");
        addButton.className = "ui compact icon button";
        addButton.onclick = filters.private.addCallback;
        addButton.appendChild(addIcon);

        //The type selector
        var typeOptions = Object.keys(filters.private.types).map(function (x) { return [x, x]; });
        var typeSelector = filters.private.markupSelection("type", "Filter Type", typeOptions);

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
                    filterdiv.removeChild(typeSelector.nextElementSibling)
                }
                var filterParts = filters.private.types[type][1]();
                filterParts.forEach(function (part) { filterdiv.appendChild(part); });
            }
        });

        return filterdiv;
    };

    // Export filters instance to global scope
    window.filters = filters;
})();