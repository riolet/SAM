function init() {
    "use strict";

    $(".ui.accordion").accordion();

    $('.selection.dropdown').dropdown({
        allowAdditions: true
    });

    filters.displayDiv = document.getElementById("filters");
}

window.onload = function () {
    "use strict";
    init();
};