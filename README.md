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

## Struggles
### Lack of documentation
One of the hardest parts of this project is the lack of documentation. Esri does a really bad job of documenting how custom raster types work, and what any of the different parameters do. This led me to have to experiment a lot, and look at other raster type implementations (many of which are poorly written). This was a huge time sync and made it hard for me to implement some of the more complex features id like to have, specifically compositing. The documentation for using custom raster functions on import is non-existent and there is no real error reporting from ArcGIS which makes it difficult to understand whats going on.

### Lack of debugging tools and hot reloading
Another struggle I had was the fact that each time I made a change in the code I had to completely close ArcGIS Pro and then reopen it for my changes to go into affect, this ate up a lot of my time and made debugging a huge chore. Another pain point is the fact that ArcGIS has almost no error reporting for custom raster types, if you dont give it exactly what it wants it doesnt work, and doesnt tell you why. These two things combined made it incredibly difficult to understand whats going wrong when something doesn't work as intended.
