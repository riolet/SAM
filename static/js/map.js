var canvas;
var ctx;
var width;
var height;
var rect;
var navBarHeight;

var ismdown = false;
var mdownx, mdowny;
var mx, my;
var tx = 532;
var ty = 288;
var scale = 0.001;

var map = {};

var nodeCollection = {};
var renderCollection;
var selection = null;
var config = {
    "show_clients": true,
    "show_servers": true,
    "show_in": true,
    "show_out": false};

// var zoom8 = 0.012;
// var zoom16 = 0.3;
// var zoom24 = 7.5;
var zoom8 = 0.0108;
var zoom16 = 0.27;
var zoom24 = 6.75;


function init() {
    canvas = document.getElementById("canvas");
    navBarHeight = $('#navbar').height();
    $('#output').css('top', navBarHeight);
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    rect = canvas.getBoundingClientRect();
    tx = rect.width / 2;
    ty = rect.height / 2;
    ctx = canvas.getContext("2d");
    ctx.lineJoin = "bevel";


    //Event listeners for detecting clicks and zooms
    canvas.addEventListener('mousedown', mousedown);
    canvas.addEventListener('mousemove', mousemove);
    canvas.addEventListener('mouseup', mouseup);
    canvas.addEventListener('keydown', mouseup);
    canvas.addEventListener('wheel', wheel);
    window.addEventListener('keydown',keydown,false);

    updateFloatingPanel();


    $('.ui.accordion').accordion();
    $('.ui.dropdown')
    .dropdown({
        //action: 'none'
        action: updateConfig
    });

    loadData();

    render(tx, ty, scale);
}

function currentLevel() {
    if (scale < zoom8) {
        return 8;
    }
    if (scale < zoom16) {
        return 16;
    }
    if (scale < zoom24) {
        return 24;
    }
    return 32;
}

function findNode(seg1=-1, seg2=-1, seg3=-1, seg4=-1) {
    if (seg1 in nodeCollection) {
        if (seg2 in nodeCollection[seg1].children) {
            if (seg3 in nodeCollection[seg1].children[seg2].children) {
                if (seg4 in nodeCollection[seg1].children[seg2].children[seg3].children) {
                    return nodeCollection[seg1].children[seg2].children[seg3].children[seg4];
                } else {
                    return nodeCollection[seg1].children[seg2].children[seg3];
                }
            } else {
                return nodeCollection[seg1].children[seg2];
            }
        } else {
            return nodeCollection[seg1];
        }
    } else {
        return null;
    }
}