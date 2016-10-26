/**
 *  Class Filters:
 *  public:
 *    filters = [];
 *    displayDiv = null;
 *  private:
 *
 *  public methods:
 *    addFilter(type, params)  // Add a new filter to the state
 *    deleteFilter(id)  // Remove a filter from the state
 *    updateDisplay()  //updates the HTML display from the state
 *    getFilters()  //returns an object encapsulating the filter state (for use in ajax requests)
 *
 *  private methods:
 *    markup(filter)
 *    markupBoilerplate(preface, enabled)
 *    markupSelection(name, placeholderText, options)
 *    markupInput(placeholderText)
 *    createFilterCreator()
 *
 */


;(function () {
    "use strict";
    var filters = {};

    filters.filters = [];
    filters.displayDiv = null;
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
                newFilter = source[0](params);
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
    };
    filters.updateDisplay = function () {
        //compare the existing display to the filters array and update it when there's a mismatch?
        //or, empty and rebuild the filter list.
        if (filters.displayDiv === null) {
            return;
        }

        filters.displayDiv.innerHTML = "";
        filters.filters.forEach(function (filter) {
            filters.displayDiv.appendChild(filter.html);
        });
        filters.displayDiv.appendChild(filters.private.createFilterCreator());
        filters.private.updateSummary();
    };
    filters.getFilters = function () {
        //collapse the filter list into descriptions that can be transmitted via AJAX
        console.error("Not implemented");
    };


    // ==================================
    // Private methods
    // ==================================
    filters.private.createSubnetFilterRow = function (mask) {
        var filter;
        var filterdiv = filters.private.markupBoilerplate(true);
        var parts = filters.private.createSubnetFilter(mask);
        parts.forEach(function (part) { filterdiv.appendChild(part); });

        filter = {};
        filter.type = "subnet";
        filter.mask = mask;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createSubnetFilter = function (mask) {
        var parts = [];
        parts.push(filters.private.markupSpan("Subnet mask is "));
        parts.push(filters.private.markupSelection("subnet", "Choose subnet...", [
            ['8', '/8'],
            ['16', '/16'],
            ['24', '/24'],
            ['32', '/32'],
        ], mask));
        return parts;
    };
    filters.private.createPortFilterRow = function (comparator_port) {
        var comparator, port;
        if (comparator_port) {
            comparator = comparator_port[0];
            port = comparator_port[1];
        }
        var filterdiv = filters.private.markupBoilerplate(true);
        var parts = filters.private.createPortFilter(comparator, port);
        parts.forEach(function (part) { filterdiv.appendChild(part); });

        var filter = {};
        filter.type = "port";
        filter.comparator = comparator;
        filter.port = port;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createPortFilter = function (comparator, port) {
        var parts = [];
        parts.push(filters.private.markupSpan("Ports used are "));
        parts.push(filters.private.markupSelection("comparator", "Filter type...", [
            ['=', 'equal to'],
            ['<', 'less than'],
            ['>', 'greater than'],
        ], comparator));
        parts.push(filters.private.markupInput("Port number", port));
        return parts;
    };
    filters.private.createConnectionsFilterRow = function (comparator_limit) {
        var comparator, limit;
        if (comparator_limit) {
            comparator = comparator_limit[0];
            limit = comparator_limit[1];
        }
        var filterdiv = filters.private.markupBoilerplate("Is involved in ", true);
        var parts = filters.private.createConnectionsFilter(comparator, limit);
        parts.forEach(function (part) { filterdiv.appendChild(part); });

        var filter = {};
        filter.type = "connections";
        filter.comparator = comparator;
        filter.limit = limit;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createConnectionsFilter = function (comparator, limit) {
        var parts = [];
        parts.push(filters.private.markupSpan("Is involved in "));
        parts.push(filters.private.markupSelection("comparator", "Filter type...", [
            ['=', 'equal to'],
            ['<', 'less than'],
            ['>', 'greater than'],
        ], comparator));
        parts.push(filters.private.markupInput("a number of", limit));
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
    filters.private.markupInput = function (placeholderText, preset) {
        //input element
        var input = document.createElement("input");
        input.placeholder = placeholderText;
        input.type = "text";

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

    filters.private.deleteCallback = function (event) {
        var row = event.target.parentElement;
        var i;
        for(i = 0; i < filters.filters.length; i += 1) {
            if (filters.filters[i].html === row) {
                break;
            }
        }
        if (i !== filters.filters.length) {
            filters.deleteFilter(i);
            $(row).remove();
        }
    };
    filters.private.addCallback = function (event) {
        var row = event.target.parentElement;
        //extract: filter type
        var typeSelector = event.target.nextElementSibling;
        var type = typeSelector.getElementsByTagName("input")[0].value;
        if (!filters.private.types.hasOwnProperty(type)) {
            return;
        }
        var params = filters.private.extractCreationValues(typeSelector);
        filters.addFilter(type, params);
        //filters.private.deleteCallback(event);
        filters.updateDisplay();
    };
    filters.private.extractCreationValues = function(head) {
        var params = [];
        var walker = head.nextElementSibling;
        var inputs;
        var i;
        while (walker !== undefined && walker !== null) {
            inputs = walker.getElementsByTagName("input");
            for (i = 0; i < inputs.length; i += 1) {
                params.push(inputs[i].value);
            }
            walker = walker.nextElementSibling;
        }
        return params;
    };

    filters.private.updateSummary = function() {
        //build summary
        var summary = "Filter: ";
        filters.filters.forEach(function (filter) {
            if (filter.type === "subnet") {
                summary += "subnet /" + filter.mask
            } else if (filter.type === "port") {
                if (filter.comparator === "=") {
                    summary += "port " + filter.port;
                } else {
                    summary += "ports " + filter.comparator + filter.port;
                }
            } else if (filter.type === "connections") {
                if (filter.comparator === "=") {
                    summary += filter.limit + " conns";
                } else {
                    summary += filter.comparator + filter.limit + " conns";
                }
            }
            summary += ", ";
        });
        summary = summary.slice(0, -2);

        //display summary
        var header = filters.displayDiv.previousElementSibling
        var icon = header.getElementsByTagName("i")[0];
        header.innerHTML = "";
        header.appendChild(icon);
        header.appendChild(document.createTextNode(summary));
    }

    //Register filter types, and their constructors
    filters.private.types['subnet'] = [filters.private.createSubnetFilterRow, filters.private.createSubnetFilter, 1];
    filters.private.types['port'] = [filters.private.createPortFilterRow, filters.private.createPortFilter, 2];
    filters.private.types['connections']= [filters.private.createConnectionsFilterRow, filters.private.createConnectionsFilter, 2]

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
    }

    // Export ports instance to global scope
    window.filters = filters;
})();
