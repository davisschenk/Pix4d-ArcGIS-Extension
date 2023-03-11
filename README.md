# Pix4d ArcGIS Extension
This is extension allows for the outputs of Pix4d projects to be easily loaded into an ArcGIS Mosaic Dataset. Currently it supports imagery that only has a single tiff, but in the future I plan on adding support for compositing multispectral bands.

It works by reading data from the p4d project file and then converting the data into a custom raster type that ArcGIS is able to read. It also finds a mean date and time (while removing possible outlier dates from bad gps fix) and adds that as a field on the mosaic.

## Why is this useful
When analyzing many datasets, it is tedious to manually load all of the mosaics and then also add metadata separately and it can be difficult to manually find data about different cameras and bands.

## What does this package provide
- A Custom Raster Type
- A Tool for building a mosaic dataset

## Things I plan on improving in the future
1. Add support for compositing multiple bands
2. Fix weird input when selecting a p4d project
3. More data fields derived from p4d
