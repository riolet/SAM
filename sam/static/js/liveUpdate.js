/* 
 * This file was created to hold the functionality related to live updates on the UI side.
 * It consists of several variables for tracking related stats and the following functions.
 *        runUpdate(): the main function call that enables this. It racks the current
 *        status of the update button and handles the timer for the updates.
 *        updateCall(): makes the required json calls to perform an update.
 *        updateSliderRange(): The bulk of the file, this destroys the range slider
 *        then recreates it to better reflect the current data. 
 */

// Timing variables
var MILLIS_PER_SEC = 1000;
var updateTimer = null;

//Turn autoupdate on or off based on config setting.
function setAutoUpdate() {
  if (config.update == true && updateTimer === null) { //timer is not running
    updateTimer = window.setInterval(updateCall,Math.abs(MILLIS_PER_SEC * config.update_interval));
  } else if (config.update == false && updateTimer !== null) { //timer has been turned off
    window.clearInterval(updateTimer);
    updateTimer = null;
  }
}

function updateTimeConfig(newRange) {
  "use strict";
  let stickyStart = config.tstart === config.tmin;
  let stickyEnd = config.tend === config.tmax;
  if (newRange.min == newRange.max) {
    config.tmin = newRange.min - 300;
    config.tmax = newRange.max;
    config.tstart = config.tmax - 300;
    config.tend = config.tmax;
  } else {
    let sticky = config.tmin === newRange.min || config.tmax === newRange.max;
    config.tmin = newRange.min;
    config.tmax = newRange.max;
    if (sticky && stickyEnd) {
      config.tend = config.fmax;
    } else if (config.tend < config.tmin + 300 || config.tend > config.tmax) {
      config.tend = config.tmax;
    }
    if (sticky && stickyStart) {
      config.tstart = config.fmin;
    } else if (config.tstart < config.tmin || config.tstart > config.tmax - 300) {
      config.tstart = config.tend - 300;
    }
  }
}


//The actual json calls that are executed when the update triggers
function updateCall() {
  //get time range,
  GET_timerange(function (range) {
    updateTimeConfig(range)

    slider_init();
    GET_nodes(null);
  });
}