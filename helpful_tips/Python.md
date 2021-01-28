# Python Errors and Helpful Tips

## Error: updating cartoframes
Library conflict issue between cartoframes v 1.0.4 and other libraries.

### Solution
Revert to cartoframes version 0.9

## Error: writing geopandas dataframes to shapefiles
Warning message: Value 555715003 of field WDPAID of feature 17317 not successfully written. Possibly due to too larger number with respect to field width

### Solution
Misleading since the feature is still correctly written. Feel free to ignore it. 
