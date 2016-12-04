/* 
 * This file was created to hold the functionality related to live updates on the UI side.
 * It consists of several variables for	tracking related stats and the following functions.
 * 		runUpdate(): the main function call that enables this. It racks the current
 *		status of the update button and handles the timer for the updates.
 *		updateCall(): makes the required json calls to perform an update.
 *		updateSliderRange(): The bulk of the file, this destroys the range slider
 *		then recreates it to better reflect the current data. 
 */

// Timing variables
var MILLIS_PER_MIN 	= 60000;
var MINS_PER_UPDATE = 5; //Change this value to configure your update time.
var updateTimer 	= 0;

//Vairables for Time Slider
var sliderMade		= false;
var minSlideRange 	= 1;
var maxSlideRange 	= 2147483647;


//Main live update functionality.
function runUpdate() {
	if (config.update == true && updateTimer === 0) { //timer is not running
		updateTimer = window.setInterval(updateCall,Math.abs(MILLIS_PER_MIN * MINS_PER_UPDATE));
	} else if (config.update == false){ //timer has been turned off
		window.clearInterval(updateTimer);
		updateTimer = 0;
	}
}

//the actual json calls that are executed when the update triggers
function updateCall() {
	//updates the nodes visible on the map
	GET_nodes(null);
	//makes / updates the time slider
	slider_init();
}

// the callback function for the query that gets the ranges for the slider
function updateSliderRange (min, max) {

	if (min == minSlideRange && max == maxSlideRange) {
		return; //no update in range, don't bother changing anything.
	}

	//retreive the slider element
	dateSlider = document.getElementById("slider-date");
	//destroy the slider so we can re-create it with the new proportions
	dateSlider.noUiSlider.destroy(); 
	
	//Get the range between the handles
	var lowPos  	= config.tstart;
	var highPos 	= config.tend;
	var handleDiff 	= highPos - lowPos;

	//position variable for updates.
	var newPOS;
    var inputA = document.getElementById('input-start');
    var inputB = document.getElementById('input-end');
    var converter = dateConverter();

	//check handle positions to update slider ranges

	//neither is at an edge
	if (config.tstart != minSlideRange && config.tend != maxSlideRange)	{
		noUiSlider.create(dateSlider, { //creating a new slider to fill the void
		    range: {
		       'min': min,
		       'max': max
		    },

		    // Steps of 5 minutes
		    step: 5 * 60,

		    // at least 5 minutes between handles
		    margin: 5 * 60,

		    // Two more timestamps indicate the handle starting positions.
		    start: [lowPos, highPos], //keep the positions the same as they were previously


		    // Shade the selection
		    connect: true,
		    // Allow range draggin
		    behaviour: "drag",

		    pips: {
		        mode: 'count',
		        values: 5,
		        stepped: true,
		        density: 6,
		        format: {"to": function(v) { return ""; } } //no labels
		    }
		});

		//attach required event handlers
		dateSlider.noUiSlider.on('update', function( values, handle ) {
			var value = values[handle];
			if ( handle ) {
			    inputB.value = converter.to(Math.round(value));
			    config.tend = Math.round(value);
			} else {
			    inputA.value = converter.to(Math.round(value));
			    config.tstart = Math.round(value);
			}
		});
		dateSlider.noUiSlider.on('end', function(){
			sel_remove_all(m_nodes);
			sel_set_selection(m_selection.selection)
			links_reset();
			updateRenderRoot();
			render_all();
		});

		inputA.addEventListener('change', function(){
			dateSlider.noUiSlider.set([converter.from(this.value), null]);
		});

		inputB.addEventListener('change', function(){
			dateSlider.noUiSlider.set([null, converter.from(this.value)]);
		});

		//update the slider range for comparison next time we need to update.
		minSlideRange = min;
		maxSlideRange = max;
		return;
	} 
	
	//only start is at edge
	if (config.tstart == minSlideRange && config.tend != maxSlideRange) {
		// set new position to be the distance between start and the right handle + the new start value
		newPOS = min + handleDiff;
			noUiSlider.create(dateSlider, {
		    range: {
		       'min': min,
		       'max': max
		    },

		    // Steps of 5 minutes
		    step: 5 * 60,

		    // at least 5 minutes between handles
		    margin: 5 * 60,

		    // Two more timestamps indicate the handle starting positions.
		    start: [min, newPOS], //ensure that the same timespan from start is kept


		    // Shade the selection
		    connect: true,
		    // Allow range draggin
		    behaviour: "drag",

		    pips: {
		        mode: 'count',
		        values: 5,
		        stepped: true,
		        density: 6,
		        format: {"to": function(v) { return ""; } } //no labels
		    }
		});


		//attach required event handlers
		dateSlider.noUiSlider.on('update', function( values, handle ) {
			var value = values[handle];
			if ( handle ) {
			    inputB.value = converter.to(Math.round(value));
			    config.tend = Math.round(value);
			} else {
			    inputA.value = converter.to(Math.round(value));
			    config.tstart = Math.round(value);
			}
		});
		dateSlider.noUiSlider.on('end', function(){
			sel_remove_all(m_nodes);
			sel_set_selection(m_selection.selection)
			links_reset();
			updateRenderRoot();
			render_all();
		});

		inputA.addEventListener('change', function(){
			dateSlider.noUiSlider.set([converter.from(this.value), null]);
		});

		inputB.addEventListener('change', function(){
			dateSlider.noUiSlider.set([null, converter.from(this.value)]);
		});

		//update the slider range for comparison next time we need to update.
		minSlideRange = min;
		maxSlideRange = max;
		return;
	}  

	//only end is on an edge
	if (config.tstart != minSlideRange && config.tend == maxSlideRange) {
		// set new position to be the distance between the left handle and the old end away from the new end 
		newPOS = max - handleDiff;
		noUiSlider.create(dateSlider, {
		    range: {
		       'min': min,
		       'max': max
		    },

		    // Steps of 5 minutes
		    step: 5 * 60,

		    // at least 5 minutes between handles
		    margin: 5 * 60,

		    // Two more timestamps indicate the handle starting positions.
		    start: [newPOS, max], //ensure that the same timespan from the end is kept


		    // Shade the selection
		    connect: true,
		    // Allow range draggin
		    behaviour: "drag",

		    pips: {
		        mode: 'count',
		        values: 5,
		        stepped: true,
		        density: 6,
		        format: {"to": function(v) { return ""; } } //no labels
		    }
		});

		//attach required event handlers
		dateSlider.noUiSlider.on('update', function( values, handle ) {
			var value = values[handle];
			if ( handle ) {
			    inputB.value = converter.to(Math.round(value));
			    config.tend = Math.round(value);
			} else {
			    inputA.value = converter.to(Math.round(value));
			    config.tstart = Math.round(value);
			}
		});
		dateSlider.noUiSlider.on('end', function(){
			sel_remove_all(m_nodes);
			sel_set_selection(m_selection.selection)
			links_reset();
			updateRenderRoot();
			render_all();
		});

		inputA.addEventListener('change', function(){
			dateSlider.noUiSlider.set([converter.from(this.value), null]);
		});

		inputB.addEventListener('change', function(){
			dateSlider.noUiSlider.set([null, converter.from(this.value)]);
		});

		//update the slider range for comparison next time we need to update.
		minSlideRange = min;
		maxSlideRange = max;
		

		return;
	}

	//both are at an edge
	if (config.tstart == minSlideRange && config.tend == maxSlideRange) {

		noUiSlider.create(dateSlider, {
		    range: {
		       'min': min,
		       'max': max
		    },

		    // Steps of 5 minutes
		    step: 5 * 60,

		    // at least 5 minutes between handles
		    margin: 5 * 60,

		    // Two more timestamps indicate the handle starting positions.
		    start: [min, max], //ensure that the window includes all values


		    // Shade the selection
		    connect: true,
		    // Allow range draggin
		    behaviour: "drag",

		    pips: {
		        mode: 'count',
		        values: 5,
		        stepped: true,
		        density: 6,
		        format: {"to": function(v) { return ""; } } //no labels
		    }
		});

		//attach required event handlers
		dateSlider.noUiSlider.on('update', function( values, handle ) {
			var value = values[handle];
			if ( handle ) {
			    inputB.value = converter.to(Math.round(value));
			    config.tend = Math.round(value);
			} else {
			    inputA.value = converter.to(Math.round(value));
			    config.tstart = Math.round(value);
			}
		});
		dateSlider.noUiSlider.on('end', function(){
			sel_remove_all(m_nodes);
			sel_set_selection(m_selection.selection)
			links_reset();
			updateRenderRoot();
			render_all();
		});

		inputA.addEventListener('change', function(){
			dateSlider.noUiSlider.set([converter.from(this.value), null]);
		});

		inputB.addEventListener('change', function(){
			dateSlider.noUiSlider.set([null, converter.from(this.value)]);
		});

		//update the slider range for comparison next time we need to update.
		minSlideRange = min;
		maxSlideRange = max;
		
		return;
	}
}
