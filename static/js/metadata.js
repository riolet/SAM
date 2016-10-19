var g_timer = null;

window.onload = function() {
  init()
};

function init() {
  var searchbar = document.getElementById("hostSearch");
  var input = searchbar.getElementsByTagName("input")[0];
  console.log("init");
  console.log(input);
  input.oninput = onsearch;
}


function search(){
  console.log("searching...");
  var searchbar = document.getElementById("hostSearch");
  searchbar.classList.add("loading");
  setTimeout(function () {
    searchbar.classList.remove("loading");
    console.log("done searching");
  }, 3000);
}


function applysearch() {
    "use strict";
    var searchbar = document.getElementById("hostSearch");
    var input = searchbar.getElementsByTagName("input")[0];
    var target = input.value;

    searchbar.classList.add("loading");
    setTimeout(function () {
    searchbar.classList.remove("loading");
    console.log("Found " + target + "!!!");
  }, 3000);

}
function onsearch() {
    "use strict";
    if (g_timer !== null) {
        clearTimeout(g_timer);
    }
    g_timer = setTimeout(applysearch, 700);
}