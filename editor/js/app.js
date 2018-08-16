'use strict';

var App = (function() {

  function App(config) {
    var defaults = {
      routeData: "/preprocess_mta/output/routes.json",
      symbolData: "/preprocess_mta/output/symbols.json",
      saveData: "/preprocess_mta/usergen/routes.json"
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  App.prototype.init = function(){
    var _this = this;
    var opt = this.opt;

    this.$symbols = $('#symbols');
    this.$select = $('#select-line');
    this.$station = $('#station');

    $.when(
      $.getJSON(opt.routeData),
      $.getJSON(opt.symbolData),
      $.getJSON(opt.saveData)

    ).done(function(routes, symbols, uroutes){
      routes = routes[0];
      symbols = symbols[0];
      uroutes = uroutes[0];

      console.log(routes.length + " routes loaded.");
      console.log(symbols.length + " symbols loaded.");
      console.log(uroutes.length + " user-generated routes loaded.");

      _this.symbols = symbols;
      _this.routes = routes;
      _this.uroutes = uroutes;

      _this.loadData(routes, uroutes);
      _this.loadView(symbols, routes);
      _this.loadListeners();
      _this.onRouteChange(0);
    });

  };

  App.prototype.loadData = function(routes, uroutes){
    // Initialize uroutes
    _.each(routes, function(route){
      var uroute = _.find(uroutes, function(r){ return r.id === route.id; });

      // route found, make sure stations exist
      if (uroute) {
        _.each(route.stations, function(station){
          var ustation = _.find(uroute.stations, function(s){ return s.id === station.id; });
          if (!ustation) {
            uroute.stations.push({ id: station.id });
          }
        });

      // route not found, add empty route and stations
      } else {
        uroutes.push({
          id: route.id,
          stations: _.map(route.stations, function(s){ return {id: s.id}; })
        })
      }
    });
  };

  App.prototype.loadListeners = function(){
    var _this = this;

    this.$symbols.on('click', '.symbol', function(e){
      _this.onClickSymbol($(this));
    });

    this.$select.on('change', function(e){
      _this.onRouteChange(parseInt($(this).val()));
    });
  };

  App.prototype.loadView = function(symbols, routes){
    var $container = $('<div />');

    _.each(symbols, function(symbol, i){
      var $symbol = $('<div class="symbol" data-index="'+i+'"></div>');
      $symbol.css({
        top: symbol.point[1],
        left: symbol.point[0],
        width: symbol.size[0],
        height: symbol.size[1]
      });
      $container.append($symbol);
      symbols[i].$el = $symbol;
    });
    this.$symbols.append($container);

    var $select = this.$select;
    _.each(routes, function(route, i){
      var selected = i === 0 ? ' selected' : '';
      var $option = $('<option value="'+i+'"'+selected+'>'+route.id+'</option>');
      $select.append($option);
    });
  };

  App.prototype.onClickSymbol = function($symbol){
    var index = parseInt($symbol.attr('data-index'));
    var selected = $symbol.hasClass('selected');

    $symbol.toggleClass('selected');

    if (!selected) {
      this.symbolAttach(this.symbols[index]);
    } else {
      this.symbolDetach(this.symbols[index]);
    }
  };

  App.prototype.onRouteChange = function(index){
    this.currentRouteIndex = index;
    this.currentRoute = this.routes[index];
    this.currentURoute = this.uroutes[index];

    $('.symbol').removeClass('selected');

    // select symbols for this route
    var symbols = this.symbols;
    var ustations = _.filter(this.currentURoute.stations, function(s){ return s.point && s.size; });
    _.each(ustations, function(s){
      var symbol = _.find(symbols, function(sb){ sb.point[0]===s.point[0] && sb.point[1]===s.point[1]; });
      if (symbol) {
        symbol.$el.addClass('selected');
      }
    });

    this.showNextStation();
  };

  App.prototype.showNextStation = function(){
    this.$station.text("--");
    var currentUStation = _.find(this.currentURoute.stations, function(s){ return !s.point || !s.size; });
    this.currentUStation = currentUStation;

    if (currentUStation) {
      this.showStation(currentUStation);
    } else {
      this.$station.text("[route is complete]");
    }
  };

  App.prototype.showStation = function(ustation){
    var station = _.find(this.currentRoute.stations, function(s){ return s.id===ustation.id; });
    this.currentStation = station;

    if (!station) {
      console.log("Could not find "+ustation.id);
      return false;
    }

    this.$station.text(station.label);
  };

  App.prototype.symbolAttach = function(symbol){
    if (!this.currentStation || !symbol) return false;

    this.currentUStation.point = _.clone(symbol.point);
    this.currentUStation.size = _.clone(symbol.size);
    console.log(this.currentUStation);

    this.showNextStation();
  };

  App.prototype.symbolDetach = function(symbol){
    if (!symbol) return false;
    var _this = this;

    _.each(this.currentURoute.stations, function(station, i){
      if (station.point[0]===symbol.point[0] && station.point[1]===symbol.point[1]) {
        _this.currentURoute.stations[i] = _.omit(station, ['point', 'size']);
      }
    });

    this.showNextStation();
  };

  return App;

})();

$(function() {
  var app = new App({});
});
