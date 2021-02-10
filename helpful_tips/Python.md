# Python Errors and Helpful Tips

## Error: updating cartoframes
Library conflict issue between cartoframes v 1.0.4 and other libraries.

### Solution
Revert to cartoframes version 0.9

## Error: writing geopandas dataframes to shapefiles
Warning message: Value 555715003 of field WDPAID of feature 17317 not successfully written. Possibly due to too larger number with respect to field width

### Solution
Misleading since the feature is still correctly written.

## Error: 'false' occur in the the_geom field on Carto table

### Solution
If it's a point shapefile, one possible cause is that points have been read as multipoints by geopandas and made Carto confused. To solve the issue, clean up the geometry column by extracting the points from multipoints. There is an example in the script of bio_007b.
