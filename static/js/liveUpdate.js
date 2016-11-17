// Timing variables
var MILLIS_PER_MIN 	= 60000;
var MINS_PER_UPDATE = 0.080;
var updateTimer 	= 0;

//Vairables for Time Slider
var slideTimer 		= 0;
var minSlideRange 	= 1;
var maxSlideRange 	= 2147483647;


function runUpdate() {
	if (config.update == true && updateTimer === 0) {
		updateCall();
		updateTimer = window.setInterval(updateCall,Math.abs(MILLIS_PER_MIN * MINS_PER_UPDATE));
		//slideTimer  = window.setInterval(updateSliderRange,Math.abs(MILLIS_PER_MIN * MINS_PER_UPDATE));
	} else if (config.update == false){
		window.clearInterval(updateTimer);
		updateTimer = 0;
	}
}

function updateCall() {
/*	if (subnetLabel != "") {
		GET_Nodes([subnetLabel]);
	} else {
		GET_nodes(null);
	}

*/
        //sel_remove_all(m_nodes);
        //sel_set_selection(m_selection.selection)
        //links_reset();
        updateRenderRoot();
        render_all();
/*
   $.ajax({
        url: "/stats",
        type: "GET",
        data: {'q': 'timerange'},
        dataType: "json",
        error: onNotLoadData,
        success: function (response) {
            updateSliderRange(Math.floor(response.min), Math.floor(response.max));
        }
    });
*/
}

function updateSliderRange (min, max) {

	sliderDate = document.getElementById("slider-date");
	if (config.tstart != minSlideRange && config.tend != maxSlideRange)	{
		sliderDate.noUiSlider.updateOptions({
			range: {
				'min': min,
				'max': max
			}
		});
	} else if (config.tstart == minSlideRange) {
		sliderDate.noUiSlider.updateOptions({
			range: {
				'min': min,
				'max': max
			},
			start: [min, config.tend]
		});
	} else if (config.tstart == maxSlideRange) {
		sliderDate.noUiSlider.updateOptions({
			range: {
				'min': min,
				'max': max
			},
			start: [config.tstart, max]
		});
	}
	minSlideRange = min;
	maxSlideRange = max;
}
