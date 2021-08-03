# Layer Visualization

This folder contains the tools used to aid in designing visualizations for datasets on Resource Watch. Each tool gives you instructions within on how to run them.

### Visualizing raster layers 
To use these tools, you will want to follow these steps: 
1. Make sure you have a Google Earth Engine account. If you do not have an account, you can make one for free [here](https://earthengine.google.com/).
2. Open the appropriate tool, based on type of data you have:
    - [categorical raster data visualizations](https://code.earthengine.google.com/4fa3776a4a609444bbdde586fbf264a0)
    - [quantitative raster data visualizations](https://code.earthengine.google.com/96b6d4b647c02c702c2efb3e7a7b9a0c)
3. Follow the instructions in the tool that you are using.
4. When you finished making a visualization, save the edited version of the tool as *wri_id_public_title* in the *users/resourcewatch/default/ResourceWatch* folder in Google Earth Engine. This will allow you to easily modify the visualization later, if needed.

### Visualizing vector layers
To use these tools, you will want to follow these steps: 
1. Use the [vector_layer_visualization.py](https://github.com/resource-watch/data-team-tools/blob/master/layer_visualization/vector_layer_visualization.py) tool
2. Set up the parameters
    - **table_name** (*String*): Name of table on Carto which you want to make the visualization.
    - **timeline** (*Bool*): If the dataset has a timeline.
    - **year** (*Number*): If timeline is true, set the year for making the visualization.
    - **geo_type** (*String*): Geometry type - 'polygon', 'line', or 'point'. 
    - **break_type** (*String*): Break type - 'basic', 'unique', or 'choropleth'.
    - **num_break** (*Number*): Number of unique values/number of gradient breaks.
    - **colors** (*List*): Manually set colors or use the color ramp.
    - **break_method** (*String*): If the **break_type** is 'choropleth', you have to set a break method - 'Jenks', 'EqualIntervals', 'Quantiles', or 'Manual'.
    - **selected_breaks** (*List*): If **break_method** is 'Manual', you have to manually set the break points in the list.
    - **join_WRI_shape** (*Bool*): If need to join dataset with WRI shapefile.
    - **col_value** (*String*): Name of the value column, which has the unique values or gradient values.
    - **col_datetime** (*String*): Name of the datetime column, which has the timestamps.
    - **col_country** (*String*): Name of the country column, which has the country names(used to join with the wri shapefile).
    - **col_interactive** (*List*): Name of other columns that you want to included in the final table (e.g. need more columns for interaction).
3. Run the script to get the SQL, CartoCSS, Layer config, and Legend config.
4. Create map on Carto:
    - Login to Carto and open the dataset.
    - Copy and paste the SQL to the SQL panel.
    - 'APPLY' the SQL and select 'CREATE MAP' to create a map on Carto.
    - Click on 'More options' of the layer and select 'Edit layer'.
    - Switch to CartoCSS view by click on the button at the bottom.
    - Copy and paste the CartoCSS to the CartoCSS panel.
    - 'APPLY' the CartoCSS and check the visualization.
5. If you don't think the visualization is appropriate, modify the parameters in the script, then repeat steps 3 and 4.
6. Run the script to get the Layer config, and Legend config. Copy and paste the Layer config and Legend config to the backoffice to create the map on Resource Watch.
7. Delete the map on Carto when you finished.