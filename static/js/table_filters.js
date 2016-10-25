/**
 *  Class Filters:
 *  public:
 *    filters = [];
 *    displayDiv = null;
 *  private:
 *
 *  public methods:
 *    addFilter(type, ...params)  // Add a new filter to the state
 *    deleteFilter(id)  // Remove a filter from the state
 *    updateDisplay()  //updates the HTML display from the state
 *    getFilters()  //returns an object encapsulating the filter state (for use in ajax requests)
 *
 *  private methods:
 *    markup(filter)
 *    markupBoilerplate(preface, enabled)
 *    markupSelection(name, placeholderText, options)
 *    markupInput(placeholderText)
 *
 */


;(function () {
    "use strict";
    var filters = {};

    filters.filters = [];
    filters.displayDiv = null;
    filters.private = {};


    // ==================================
    // Public methods
    // ==================================
    filters.addFilter = function (type) {
        //create a filter item and add it to the array
        //a filter item includes description and reference to an HTML element
        var newFilter = null;
        var source = null;
        if (filters.private.types.hasOwnProperty(type)) {
            source = filters.private.types[type];
            if (arguments.length === source[1] + 1) {
                var params = (arguments.length === 1 ? [arguments[0]] : Array.apply(null, arguments));
                params.shift();
                newFilter = source[0](params);
            } else {
                console.error("addFilter: Argument length didn't match:");
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
    filters.deleteFilter = function (id) {
        //remove a filter item from the list
        // ???trigger the removal from the display???
        console.error("Not implemented");
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
    };
    filters.getFilters = function () {
        //collapse the filter list into descriptions that can be transmitted via AJAX
        console.error("Not implemented");
    };


    // ==================================
    // Private methods
    // ==================================
    filters.private.createSubnetFilter = function (mask) {
        var filterdiv = filters.private.markupBoilerplate("Subnet mask is ", true);
        filterdiv.appendChild(filters.private.markupSelection("subnet", "Choose subnet...", [
            ['8', '/8'],
            ['16', '/16'],
            ['24', '/24'],
            ['32', '/32'],
        ]));

        var filter = {};
        filter.type = "subnet";
        filter.mask = mask;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createPortFilter = function (comparator_port) {
        var comparator=comparator_port[0], port=comparator_port[1];
        var filterdiv = filters.private.markupBoilerplate("Ports used are ", true);
        filterdiv.appendChild(filters.private.markupSelection("comparator", "Filter type...", [
            ['=', 'equal to'],
            ['<', 'less than'],
            ['>', 'greater than'],
        ]));
        filterdiv.appendChild(filters.private.markupInput("Port number"));

        var filter = {};
        filter.type = "port";
        filter.comparator = comparator;
        filter.port = port;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.createConnectionsFilter = function (comparator_quantity) {
        var comparator=comparator_quantity[0], quantity=comparator_quantity[1];
        var filterdiv = filters.private.markupBoilerplate("Is involved in ", true);
        filterdiv.appendChild(filters.private.markupSelection("comparator", "Filter type...", [
            ['=', 'equal to'],
            ['<', 'less than'],
            ['>', 'greater than'],
        ]));
        filterdiv.appendChild(filters.private.markupInput("a number of"));
        filterdiv.appendChild(filters.private.markupSpan("connections."));

        var filter = {};
        filter.type = "port";
        filter.comparator = comparator;
        filter.quantity = quantity;
        filter.html = filterdiv;
        return filter;
    };
    filters.private.markupBoilerplate = function (preface, enabled) {
        // preface: The leading label text
        // enabled: true/false, enable the filter checkbox

        //The delete button
        var deleteIcon = document.createElement("i");
        deleteIcon.className = "delete icon";
        var deleteButton = document.createElement("button");
        deleteButton.className = "ui compact icon button";
        deleteButton.appendChild(deleteIcon);

        //The Enable/Disable toggle
        var toggleInput = document.createElement("input");
        toggleInput.title = "Enable this filter";
        toggleInput.type = "checkbox";
        toggleInput.checked = enabled;
        var toggleLabel = document.createElement("label");
        toggleLabel.className = "inline";
        toggleLabel.appendChild(document.createTextNode(preface));
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
    filters.private.markupSelection = function (name, placeholderText, options) {
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

        //Transform to semantic styled selection box
        //TODO: Does this work?
        $(selectionDiv).dropdown();
        return selectionDiv;
    };
    filters.private.markupInput = function (placeholderText) {
        //input element
        var input = document.createElement("input");
        input.placeholder = placeholderText;
        input.type = "text";

        //encompassing div
        var inputdiv = document.createElement("div")
        inputdiv.className = "ui input";
        inputdiv.appendChild(input);
        return inputdiv;
    };
    filters.private.markupSpan = function (text) {
        var span = document.createElement("span");
        span.appendChild(document.createTextNode(text));
        return span;
    };


    //Down here because it needs to be AFTER the declaration of the functions it references.
    filters.private.types = {
        "subnet": [filters.private.createSubnetFilter, 1],
        "port": [filters.private.createPortFilter, 2],
        "connections": [filters.private.createConnectionsFilter, 2],
    };

    // Export ports instance to global scope
    window.filters = filters;
})();
