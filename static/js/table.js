function init() {
    "use strict";

    $(".ui.accordion").accordion();

    $('#filter1').find('.dropdown').dropdown('set exactly', '/24');
    $('#filter2').find('.dropdown').dropdown('set exactly', '=');
    $('#filter3').find('.dropdown').dropdown('set exactly', '>');
}

window.onload = function () {
    "use strict";
    init();
};