# Alternative MTA Maps

_Under construction_

## Dependencies

- [Python](https://www.python.org/) 2.7+ or 3.6+
- [OpenCV for Python](https://github.com/skvark/opencv-python) for computer vision / symbol detection
- [Node.js](https://nodejs.org/en/) for running a simple server for editor UI

## Process for re-building the MTA map

The following rebuilds the existing MTA map from scratch. The results of this process are already in this repository, so no need to repeat these steps unless you are using new or different data and need to start from scratch.

Install dependencies for web UI using Node.js, then start server (defaults to [localhost:2222/editor/](http://localhost:2222/editor/)):

```
npm install
npm run
```

Run a script to process station data from the [MTA](http://web.mta.info/developers/developer-data-terms.html#data).  This combines [station data](http://web.mta.info/developers/data/nyct/subway/Stations.csv) with [color data](http://web.mta.info/developers/data/colors.csv). This creates a .json file `./preprocess_mta/output/routes.json`:

```
cd preprocess_mta
python routes.py
```

Run a script to recognize symbols. Creates a .json file in `./preprocess_mta/output/symbols.json`

```
python symbols.py
```

Now go to [localhost:2222/editor/symbols.html](http://localhost:2222/editor/symbols.html). Click on the symbol associated with the station listed in the select box on the top left. The next station should display automatically after a station is clicked. Continue until the line is complete, then select another line. You can click on an existing selected station to "undo" it.  The results will be saved to `./preprocess_mta/usergen/routes.json`.

Next go to [localhost:2222/editor/lines.html](http://localhost:2222/editor/lines.html). Click on each station to tweak the line's position, bezier curve, label, rotation, etc. All changes will update `./preprocess_mta/usergen/routes.json`
