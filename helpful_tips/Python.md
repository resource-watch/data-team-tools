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

## Error: When running a command line process from a python script using subprocess.run, the command does not run as desired 
Example: 
```
File "/home/rthoms/anaconda3/envs/rw/lib/python3.7/site-packages/GDAL-2.3.3-py3.7-linux-x86_64.egg-info/scripts/gdal_calc.py", line 350, in doit
    myResult = ((1 * (myNDVs == 0)) * myResult) + (myOutNDV * myNDVs)
numpy.core._exceptions.UFuncTypeError: ufunc 'multiply' did not contain a loop with signature matching types...
```

### Solution 
Use shlex (defualt library) to format the command line subprocess
```python
import shlex
cmd = 'gdalwarp -with -all -my -fancy -command -options -i -know -work -in -my -shell'
posix_cmd = shlex.split(cmd, posix=True)
subprocess.check_call(posix_cmd, cwd=cwd)
```

## Error: Time out when uploading large files to GCS with util_cloud.gcs_upload
Example: 
```
... raise ConnectionError(err, request=request)
requests.exceptions.ConnectionError: ('Connection aborted.', timeout('The write operation timed out'))
```

### Solution
Manually change the upload speed in the processing script 
```python
# The default setting requires an uploading speed at 10MB/min. Reduce the chunk size, if the network condition is not good.
storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024* 1024  # 5 MB
storage.blob._MAX_MULTIPART_SIZE = 5 * 1024* 1024  # 5 MB
```