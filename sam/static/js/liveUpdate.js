// Timing variables
var MILLIS_PER_SEC = 1000;
var updateTimer = null;

//Turn autoupdate on or off based on config setting.
function setAutoUpdate() {
  if (controller.autorefresh == true && updateTimer === null) { //timer is not running
    updateTimer = window.setInterval(updateCall,Math.abs(MILLIS_PER_SEC * controller.autorefresh_period));
  } else if (controller.autorefresh == false && updateTimer !== null) { //timer has been turned off
    window.clearInterval(updateTimer);
    updateTimer = null;
  }
}

function updateTimeConfig(newRange) {
  "use strict";
  let stickyStart = config.tstart === config.tmin;
  let stickyEnd = config.tend === config.tmax;
  if (newRange.min == newRange.max) {
    //if the newRange is zero, decrease the min by 5 minutes to indicate a range.
    //  and since there's only 5 minutes, set the start/end to match.
    config.tmin = newRange.min - 300;
    config.tmax = newRange.max;
    config.tstart = config.tmax - 300;
    config.tend = config.tmax;
  } else {
    //newRange is at least 5 minutes
    // should anything stick, or is the range different?
    let sticky = config.tmin === newRange.min || config.tmax === newRange.max;
    config.tmin = newRange.min;
    config.tmax = newRange.max;
    if (sticky && stickyEnd) {
      config.tend = config.tmax;
    } else if (config.tend < config.tmin + 300 || config.tend > config.tmax) {
      config.tend = config.tmax;
    }
    if (sticky && stickyStart) {
      config.tstart = config.tmin;
    } else if (config.tstart < config.tmin || config.tstart > config.tmax - 300) {
      config.tstart = config.tend - 300;
    }
  }
  //console.log("config time:", config.tmin % 10000, "<=", config.tstart % 10000, "<=", config.tend % 10000, "<=", config.tmax % 10000);
}


//The actual json calls that are executed when the update triggers
function updateCall() {
  //get time range,
  controller.GET_timerange(controller.dsid, function (range) {
    // TODO: some redundant code here, with the default callback for GET_timerange...
    updateTimeConfig(range);

    slider_init();
    nodes.GET_request(null, null);
  });
}