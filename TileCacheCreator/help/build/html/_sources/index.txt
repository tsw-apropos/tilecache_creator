.. tilecachecreator documentation master file, created by
   sphinx-quickstart on Sun Feb 12 17:11:03 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TileCache Creator's documentation!
=============================================
Overview
--------
TileCache Creator is designed to create local tile caches for off line display of Web Map Service (WMS) base maps. When used together with the TileLayer Plugin by Minoru Akagi, you have fast offline use of WMS base maps.

When using this plugin is it very important to make sure that the WMS service you want to use offline, permits you to make a local copy of the files. Examples of services that permit such use are:

* Open Street Map (irs.gis-lab.info)
* Canada NRCAN Toporama (wms.ess-ws.nrcan.gc.ca/wms/toporama_en)

Like the TileLayer Plugin, right now TileCache Creator only supports Spherical Mercator projections (EPSG:3857) and creation of local tile caches from WMS services. Future support for WMTS and other projections may be added in the future.

Controls
--------

This plugin has only one page, seen below:

.. _fig_mainpage:

.. figure:: _static/screenshot.png
   :align: left
   :figwidth: 100 %

Configuration files contain the information about the TileCache settings shown in this figure and they are named with a .tcc extension but are simple text files.

The main fields and actions are:

* TileCache Dir Name - the directory where the tile cache will be created

* Source Name - the name of the source for these tiles

* Source URL - the url (without the ``http://`` prefix) of the WMS

* Service Layer - the layer from this service you want to use. Clicking on the tool button to the right will query the system for available layers you can choose from.

* Minimum Zoom - the furthest out you want to zoom (values >= 0)

* Maximum Zoom - the furthest in you want to zoom (values <= 21)

* Project Extents Layer - if you have a vector or raster layer you want to use to get project extents, you can select it here.

* Update from extents layer - update layer extents from the layer selected in the "Project Extents Layer" dropdown list. lease note you should transform your default CRS for your project to to EPSG:3857 before doing this.

* Update from canvans - update layer extents from the current views extents

* Tile Image Format - select the file format you want to save tiles in. JPG is generally the most space efficient of the options provided.

Usage
-----
When you create a tile cache, the system will notify you both of zoom level progress and tile level progress. Clicking on cancel will cancel the process after the current zoom level tiles are processed.

When TileCache Creator updates or creates a tile cache, it also creates an input file for the TileLayer plugin so that you can work the tile cache results without the need for further manual configuration.


.. toctree::
   :maxdepth: 2
