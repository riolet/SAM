var slider_model = {}

function slider_add_listener(event, callback) {
    if (event == "edit") {
        slider_model.editListeners.push(callback);
    }
    if (event == "change") {
        slider_model.changeListeners.push(callback);
    }
}

function slider_init() {
    console.log("init!");
    var slider = document.getElementById("range-slider");

    slider.onmousedown = onMouseDown;
    slider.onmousemove = onMouseMove;
    slider.onmouseup = onMouseUp;
    slider_model.start = 0.2;
    slider_model.end = 0.8;
    slider_model.editListeners = []
    slider_model.changeListeners = []
    slider_model.sliding = false;

    var rect = slider.getBoundingClientRect();
    slider_model.minx = rect.left;
    slider_model.maxx = rect.right;
}

function updateDisplay() {
    var leftSlider = document.getElementById("slider-start");
    var rightSlider = document.getElementById("slider-end");
    var selection = document.getElementById("slider-active");
    leftSlider.style.left = (slider_model.start * 100) + "%";
    rightSlider.style.left = (slider_model.end * 100) + "%";
    selection.style.width = ((slider_model.end - slider_model.start) * 100) + "%";
    selection.style.left = (slider_model.start * 100) + "%";
}

function onMouseDown(event) {
    event.preventDefault();
    var clickPos = (event.clientX - slider_model.minx) / (slider_model.maxx - slider_model.minx);
    var distStart = Math.abs(slider_model.start - clickPos);
    var distEnd = Math.abs(slider_model.end - clickPos);
    if (distStart < distEnd) {
        slider_model.start = clickPos;
        if (distStart < 0.01) {
            slider_model.pinned = slider_model.end;
        } else {
            slider_model.pinned = slider_model.start;
        }
    } else {
        slider_model.end = clickPos;
        if (distEnd < 0.01) {
            slider_model.pinned = slider_model.start;
        } else {
            slider_model.pinned = slider_model.end;
        }
    }
    slider_model.sliding = true;
    fire_edit_event();
    fire_change_event();
    updateDisplay();
    return true;
}

function onMouseMove(event) {
    event.preventDefault();
    if (!slider_model.sliding) {
        return;
    }
    var clickPos = (event.clientX - slider_model.minx) / (slider_model.maxx - slider_model.minx);
    if (clickPos > slider_model.pinned) {
        slider_model.start = slider_model.pinned;
        slider_model.end = clickPos;
    } else {
        slider_model.start = clickPos;
        slider_model.end = slider_model.pinned;
    }
    updateDisplay();
    return true;
}

function onMouseUp(event) {
    event.preventDefault();
    slider_model.sliding = false;
    fire_change_event();
    return true;
}

function fire_edit_event() {
    slider_model.editListeners.forEach(function (callback) {
        callback(slider_model);
    });
}

function fire_change_event() {
    slider_model.changeListeners.forEach(function (callback) {
        callback(slider_model);
    });
}

//execute when document is 'ready'
$(slider_init);