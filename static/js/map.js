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
var scale = 0.01;

var map = {};

var nodeCollection = {};
var renderCollection;
var selection = null;


function init() {
    canvas = document.getElementById("canvas");
    navBarHeight = $('#navbar').height();
    $('#output').css('top', navBarHeight);
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    width = canvas.width;
    height = canvas.height;
    rect = canvas.getBoundingClientRect();
    ctx = canvas.getContext("2d");
    ctx.lineJoin = "bevel";


    //Event listeners for detecting clicks and zooms
    canvas.addEventListener('mousedown', mousedown);
    canvas.addEventListener('mousemove', mousemove);
    canvas.addEventListener('mouseup', mouseup);
    canvas.addEventListener('wheel', wheel);

    loadData();

    render(tx, ty, scale);
}

function currentLevel() {
    if (scale < 0.07) {
        return 8;
    }
    if (scale < 0.5) {
        return 16;
    }
    if (scale < 3.5) {
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