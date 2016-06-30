tilecache_creator
=================

NOTE: This plugin is now deprecated. Use the QTiles plugin for creating local tile caches. Use the QTiles Tools plugin to create TileLayer Plugin configuration files.


Create local disk cache from WMS service for offline use in QGIS from online wms sources in Spherical Mercator Projection (EPSG:3857). 

Requires owslib.wms. This is most easily installed with either easy_install or pip (Under Linux these tools can be found in the python-setuptools package or as sometimes as python-pip, depending on your distro)

Please note that other projections are not supported and attempting to download them will generate an error.
