'use strict';

var App = (function() {

  function App(config) {
    var defaults = {
      routeData: "/preprocess_mta/output/routes.json",
      symbolData: "/preprocess_mta/output/symbols.json",
      saveData: "/preprocess_mta/output/stations.json"
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  App.prototype.init = function(){
    var _this = this;
    var opt = this.opt;

    $.when(
      $.getJSON(opt.routeData),
      $.getJSON(opt.symbolData)

    ).done(function(routes, symbols){
      routes = routes[0];
      symbols = symbols[0];
      console.log(routes.length + " routes loaded.");
      console.log(symbols.length + " symbols loaded.");

      _this.symbols = symbols;
      _this.routes = routes;
      _this.loadData(routes);
      _this.loadView(symbols, routes);
      _this.loadListeners();
    });

  };

  App.prototype.loadData = function(routes){

  };

  App.prototype.loadListeners = function(){
    var _this = this;

    $('#symbols').on('click', '.symbol', function(e){
      _this.onClickSymbol($(this));
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
    });
    $('#symbols').append($container);
  };

  App.prototype.onClickSymbol = function($symbol){
    var index = parseInt($symbol.attr('data-index'));
    var selected = $symbol.hasClass('selected');

    $symbol.toggleClass('selected');
  };

  return App;

})();

$(function() {
  var app = new App({});
});
