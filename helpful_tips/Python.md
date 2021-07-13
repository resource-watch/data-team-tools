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

## Error: When updating a timestamp column of a Carto table through the SQL API, the response of the API is "column is of type timestamp without time zone but expression is of type text"

### Solution
Use date(column name) function in the sql query 

## Error: Upload timeout for util_cloud.gcs_upload, when the raster files are large, or the internet is not fast enough

## Error: Processed and/or raw data file cannot be uploaded to AWS because the zip exceeded the maximum file size

### Solution
Import zipfile, and set compress_type parameter to zipfile.ZIP_DEFALTED in the zip function.
```
import zipfile

with ZipFile(processed_data_dir,'w') as zipped:
    for file in processed_data_file:
        zipped.write(file, os.path.basename(file), compress_type= zipfile.ZIP_DEFLATED)
```




