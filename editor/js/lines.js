'use strict';

var AppLines = (function() {

  var opt, routes, uroutes;
  var $map, $lines, $overlay, $symbols, $svg, $select;
  var $opacitySelect, $toggleMap, $toggleLines;

  function AppLines(config) {
    var defaults = {
      routeData: "/preprocess_mta/output/routes.json",
      urouteData: "/preprocess_mta/usergen/routes.json",
      lineWidth: 5,
      curviness: 0.2 // probably between 0.1 and 0.5
    };
    opt = _.extend({}, defaults, config);
    this.init();
  }

  function distance(p1, p2) {
    var deltaX = p2.x - p1.x;
    var deltaY = p2.y - p1.y;
    return Math.hypot(deltaX, deltaY);
  }

  function radiansBetweenPoints(p1, p2) {
    var deltaX = p2.x - p1.x;
    var deltaY = p2.y - p1.y;
    return Math.atan2(deltaY, deltaX);
  }

  function translatePoint(p, radians, distance) {
    var x2 = p.x + distance * Math.cos(radians);
    var y2 = p.y + distance * Math.sin(radians);
    return {
      x: x2,
      y: y2
    };
  }

  function routesToHTML(){
    var html = '';
    _.each(routes, function(route, i){
      html += '<g class="route active" id="route-'+route.id+'" stroke="'+route.color+'" stroke-width="'+opt.lineWidth+'" stroke-linecap="round" fill="none">';

      // get route's groups
      var groups = [route.stations];
      if (route.groups && route.groups.length > 1) {
        groups = route.groups
      }

      _.each(groups, function(group, i){
        var id = "route-group-" + route.id + (i+1);
        html += stationsToHTML(group, id);
      });

      html += '</g>';
    });
    return html;
  };

  function stationPosition(station) {
    var p = station.point;
    var s = station.size;
    var x = p[0] + s[0] * 0.5;
    var y = p[1] + s[1] * 0.5;
    return {
      x: x,
      y: y
    }
  }

  function stationsToHTML(stations, id) {
    var d = "";
    var count = stations.length;
    _.each(stations, function(station, i){
      var p = stationPosition(station);
      if (i<=0) {
        d += "M"+p.x+" "+p.y;
      } else {
        var p0 = stationPosition(stations[i-1]); // prev
        var p2 = (i < count-1) ? stationPosition(stations[i+1]) : false; // next
        var pd = distance(p0, p);
        var cpd = pd * opt.curviness;
        // next exists
        if (p2 !== false) {
          var r2 = radiansBetweenPoints(p2, p0);
          var cp2 = translatePoint(p, r2, cpd);
          // use shorthand if we're after the 2nd point
          if (i > 1) {
            d += " S"+cp2.x+","+cp2.y+" "+p.x+","+p.y;
          // otherwise, calculate curve
          } else {
            var r0 = radiansBetweenPoints(p0, p);
            var cp0 = translatePoint(p0, r0, cpd);
            d += " C"+cp0.x+","+cp0.y+" "+cp2.x+","+cp2.y+" "+p.x+","+p.y;
          }
        // otherwise we're at the last point
        } else {
          var r2 = radiansBetweenPoints(p, p0);
          var cp2 = translatePoint(p, r2, cpd);
          d += " S"+cp2.x+","+cp2.y+" "+p.x+","+p.y;
        }
      }
    });
    return '<path id="'+id+'" d="'+d+'" />';
  }

  AppLines.prototype.init = function(){
    var _this = this;

    $map = $('#map');
    $overlay = $('#overlay');
    $symbols = $('#symbols');
    $lines = $("#lines");
    $svg = $('#svg');
    $select = $('#select-line');
    $opacitySelect = $('#map-opacity');
    $toggleMap = $('#toggle-map');
    $toggleLines = $('#toggle-lines');

    $.when(
      $.getJSON(opt.routeData),
      $.getJSON(opt.urouteData)

    ).done(function(_routes, _uroutes){
      routes = _routes[0];
      uroutes = _uroutes[0];

      console.log(routes.length + " routes loaded.");
      console.log(_.keys(uroutes).length + " user-generated routes loaded.");

      _this.parseData();
      _this.loadView();
      _this.loadListeners();
      _this.onRouteChange(-1);
    });

  };

  AppLines.prototype.loadListeners = function(){
    var _this = this;
    var $document = $(document);

    $select.on('change', function(e){
      _this.onRouteChange(parseInt($(this).val()));
    });

    $toggleMap.on('change', function(e){
      var checked = $(this).is(':checked');
      _this.toggleMap(checked);
    });

    $toggleLines.on('change', function(e){
      var checked = $(this).is(':checked');
      _this.toggleLines(checked);
    });

    $document.on('input', '#map-opacity', function() {
      $overlay.css("opacity", 1-$opacitySelect.val());
    });
  };

  AppLines.prototype.loadView = function(){
    var width = $map.width();
    var height = $map.height();
    var $container = $('<div />');

    // get unique station symbols
    var stations = _.pluck(routes, "stations");
    stations = _.flatten(stations, true);
    stations = _.filter(stations, function(station){ return station.point && station.size; });
    // stations = _.map(stations, function(station){
    //   station.point_id = station.point[0] + "_" + station.point[1];
    //   return station;
    // });
    stations = _.uniq(stations, function(station) { return station.id; });

    // draw symbols
    _.each(stations, function(station){
      var $symbol = $('<a href="#" class="symbol" data-id="'+station.id+'"></a>');
      $symbol.css({
        top: station.point[1],
        left: station.point[0],
        width: station.size[0],
        height: station.size[1]
      });
      $container.append($symbol);
    });
    $symbols.append($container);

    // init select route
    _.each(routes, function(route, i){
      var $option = $('<option value="'+i+'">'+route.id+'</option>');
      $select.append($option);
    });

    // init lines
    $svg.attr('width', width);
    $svg.attr('height', height);
    $svg.html(routesToHTML());

    _.each(routes, function(route, i){
      routes[i].$group = $('#route-'+route.id);
    });
  };

  AppLines.prototype.onRouteChange = function(index){
    if (index < 0) {
      $(".route").addClass("active");
      $('.symbol').addClass('active');
      return false;
    }

    var currentRoute = routes[index];
    $('.symbol').removeClass('active');
    $('.route').removeClass('active');

    currentRoute.$group.addClass('active');

    // select symbols for this route
    _.each(currentRoute.stations, function(s){
      $('.symbol[data-id="'+s.id+'"]').addClass('active');
    });
  };

  AppLines.prototype.parseData = function(){
    // Combined routes and uroutes
    _.each(routes, function(route, i){
      var uroute = uroutes[route.id];
      if (uroute) {
        _.each(route.stations, function(station, j){
          var ustation = uroute.stations[station.id];
          if (ustation) {
            routes[i].stations[j] = _.extend({}, station, ustation);
          }
        });
      }
      if (route.groups && route.groups.length > 0) {
        var routeGroups = [];
        var stations = routes[i].stations;
        _.each(route.groups, function(group){
          var gstations = _.filter(stations, function(station){
            return station.groups && _.indexOf(station.groups, group) >= 0;
          });
          routeGroups.push(gstations);
        });
        routes[i].groups = routeGroups;
      }
    });
  };

  AppLines.prototype.toggleLines = function(on){
    if (on) {
      $lines.css("opacity", 1);
    } else {
      $lines.css("opacity", 0);
    }
  };

  AppLines.prototype.toggleMap = function(on){
    if (on) {
      $overlay.css("opacity", 1-$opacitySelect.val());
    } else {
      $overlay.css("opacity", 1);
    }
  };

  return AppLines;

})();

$(function() {
  var app = new AppLines({});
});
