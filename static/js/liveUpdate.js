// Timing variables
var MILLIS_PER_MIN 	= 60000;
var MINS_PER_UPDATE = 0.080;
var updateTimer 	= 0;

//Vairables for Time Slider
var sliderMade		= false;
var minSlideRange 	= 1;
var maxSlideRange 	= 2147483647;


//Main live update functionality.
function runUpdate() {
	if (config.update == true && updateTimer === 0) {
		updateTimer = window.setInterval(updateCall,Math.abs(MILLIS_PER_MIN * MINS_PER_UPDATE));
	} else if (config.update == false){
		window.clearInterval(updateTimer);
		updateTimer = 0;
	}
}

//the actual json calls that are executed when the update triggers
function updateCall() {
	//updates the nodes visible on the map
	GET_nodes(null);
	slider_init();
      
	//updates the range of the time slider
 /*  $.ajax({
        url: "/stats",
        type: "GET",
        data: {'q': 'timerange'},
        dataType: "json",
        error: onNotLoadData,
        success: function (response) {
			var sliderDate = document.getElementById("slider-date").innerHTML
			if (sliderDate = "") {
				           	config.tstart = response.max - (5*60);
            				config.tend = response.max;
            				create_slider(Math.floor(response.min), Math.floor(response.max));
			} else {
				updateSliderRange(Math.floor(response.min), Math.floor(response.max));
			}
        }
    });
/*
*/
}

// the callback function for the query that gets the ranges for the slider
function updateSliderRange (min, max) {

	//retreive the slider element
	sliderDate = document.getElementById("slider-date");
	


	//check handle positions to update slider ranges

	//neither is at an edge
	if (config.tstart != minSlideRange && config.tend != maxSlideRange)	{
		sliderDate.noUiSlider.updateOptions({
			range: {
				'min': min,
				'max': max
			}
		});
	
		minSlideRange = min;
		maxSlideRange = max;
		return;
	} 
	
	//only start is at edge
	if (config.tstart == minSlideRange && config.tend != maxSlideRange) {
		sliderDate.noUiSlider.updateOptions({
			range: {
				'min': min,
				'max': max
			},
			start: [min, null]
		});
		minSlideRange = min;
		maxSlideRange = max;
		return;
	}  

	//only end is on an edge
	if (config.tstart != minSlideRange && config.tend == maxSlideRange) {
		sliderDate.noUiSlider.updateOptions({
			range: {
				'min': min,
				'max': max
			},
			start: [null, max]
		});
		minSlideRange = min;
		maxSlideRange = max;
		return;
	}

	//both are at an edge
	if (config.tstart != minSlideRange && config.tend == maxSlideRange) {
		sliderDate.noUiSlider.updateOptions({
			range: {
				'min': min,
				'max': max
			},
			start: [min, max]
		});
		minSlideRange = min;
		maxSlideRange = max;
		return;
	}
}
