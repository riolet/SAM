function init() {
    console.log("init!");
    var slider = document.getElementById("range-slider");
    slider.onmousedown = onMouseDown;
}

function onMouseDown(event) {

    var slider = document.getElementById("range-slider");
    var rect = slider.getBoundingClientRect();
    var minx = rect.left;
    var maxx = rect.right;
    var leftSlider = document.getElementById("slider-start");
    leftSlider.style.left = (event.clientX - minx) + "px";
}

//execute when document is 'ready'
$(init);