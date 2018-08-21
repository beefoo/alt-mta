'use strict';

var AppLines = (function() {

  function AppLines(config) {
    var defaults = {
      routeData: "/preprocess_mta/output/routes.json",
      urouteData: "/preprocess_mta/usergen/routes.json"
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  AppLines.prototype.init = function(){
    var _this = this;
    var opt = this.opt;

    this.$map = $('#map');
    this.$symbols = $('#symbols');
    this.$lines = $('#lines');
    this.$select = $('#select-line');

    this.saveDataQueue = [];

    $.when(
      $.getJSON(opt.routeData),
      $.getJSON(opt.urouteData)

    ).done(function(routes, uroutes){
      routes = routes[0];
      uroutes = uroutes[0];

      console.log(routes.length + " routes loaded.");
      console.log(_.keys(uroutes).length + " user-generated routes loaded.");

      _this.loadData(routes, uroutes);
      _this.loadView();
      _this.loadListeners();
      _this.onRouteChange(0);
    });

  };

  AppLines.prototype.drawLines = function(){
    var routes = this.routes;

    _.each(routes, function(route){
      var g = route.graphics;
      var lineWidth = 5;
      var color = parseInt("0x" + route.color.slice(1));
      color = 0x000000;
      var alpha = 1.0;
      g.lineStyle(lineWidth, color, alpha);
      _.each(route.stations, function(station, i){
        var p = station.point;
        var s = station.size;
        var x = p[0] + s[0] * 0.5;
        var y = p[1] + s[1] * 0.5;
        if (i===0) {
          g.moveTo(x, y);
        } else {
          g.lineTo(x, y);
        }
      });
    });
  };

  AppLines.prototype.loadData = function(routes, uroutes){
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
    });
    this.routes = routes;
    // console.log(routes);
  };

  AppLines.prototype.loadListeners = function(){
    var _this = this;

    this.$select.on('change', function(e){
      _this.onRouteChange(parseInt($(this).val()));
    });
  };

  AppLines.prototype.loadView = function(){
    var $map = this.$map;
    var width = $map.width();
    var height = $map.height();
    var routes = this.routes;
    var $container = $('<div />');

    // get unique station symbols
    var stations = _.pluck(routes, "stations");
    stations = _.flatten(stations, true);
    stations = _.filter(stations, function(station){ return station.point && station.size; });
    stations = _.map(stations, function(station){
      station.point_id = station.point[0] + "_" + station.point[1];
      return station;
    });
    stations = _.uniq(stations, function(station) { return station.point_id; });

    // draw symbols
    _.each(stations, function(station){
      var $symbol = $('<div class="symbol" data-id="'+station.id+'"></div>');
      $symbol.css({
        top: station.point[1],
        left: station.point[0],
        width: station.size[0],
        height: station.size[1]
      });
      $container.append($symbol);
    });
    this.$symbols.append($container);

    // init select route
    var $select = this.$select;
    _.each(routes, function(route, i){
      var selected = i === 0 ? ' selected' : '';
      var $option = $('<option value="'+i+'"'+selected+'>'+route.id+'</option>');
      $select.append($option);
    });

    // init lines
    var _this = this;
    var app = new PIXI.Application(width, height, {antialias: true, transparent: true});
    _.each(routes, function(route, i){
      var graphics = new PIXI.Graphics();
      graphics.visible = false;
      app.stage.addChild(graphics);
      routes[i].graphics = graphics;
    })
    this.$lines.append(app.view);
    this.drawLines();
  };

  AppLines.prototype.onRouteChange = function(index){
    if (this.currentRoute) {
      this.currentRoute.graphics.visible = false;
    }

    this.currentRouteIndex = index;
    this.currentRoute = this.routes[index];
    this.currentRoute.graphics.visible = true;

    $('.symbol').removeClass('selected');

    // select symbols for this route
    _.each(this.currentRoute.stations, function(s){
      $('.symbol[data-id="'+s.id+'"]').addClass('selected');
    });
  };

  return AppLines;

})();

$(function() {
  var app = new AppLines({});
});
