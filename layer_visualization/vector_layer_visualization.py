#Import necessary layers
import os
import json
import cartosql
import pandas as pd
import mapclassify
from colour import Color
import json
import time 
import logging
import sys
from IPython.display import display

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


# username and api key of the carto account 
CARTO_USER = os.getenv('CARTO_WRI_RW_USER')
CARTO_KEY = os.getenv('CARTO_WRI_RW_KEY')

'''
Set up parameters for dataset
'''
# name of table on Carto which you want to make the visualization
# this should be a table name that is currently in use
table_name = '' #e.g. 'soc_039_rw1_out_of_school_rate_edit'

# if the dataset has a timeline, set timeline = True
# otherwise, set timeline = False
timeline = True
# if timeline is true, set the year for making the visualization
# if timeline is false, the year variable wont't be used, but don't comment it out
year = 2018

# geometry type
geo_type = 'polygon' # 'polygon', 'line', or 'point'

# set break type
# basic - if use only one color
# unique - if the colors are determined by unique values
# choropleth - if use gradient colors determined by values
break_type = 'choropleth' # 'basic', 'unique', or 'choropleth'

# number of unique values/number of gradient breaks
# if break_type is 'basic', the num_break variable wont't be used, but don't comment it out
num_break = 5 

# set colors
# helpful sources for color palette: https://colorbrewer2.org/, https://carto.com/carto-colors/
# if break_type is 'basic', you have to manually set the color
# colors = [''] # e.g. '#ffc0cb'
# if break_type is 'unique' or 'choropleth', you can manually set the colors by the list, or use the function below to set the color ramp
# colors = [''] # e.g. '#ffc0cb'
colors = [color.hex_l for color in list(Color("white").range_to(Color("pink"), num_break))]

# set break method
# if the break_type is 'choropleth', you have to choose a break_method below
# if break_type is 'basic' or 'unique', the break_method variable wont't be used, but don't comment it out
break_method = 'Quantiles' # 'Jenks', 'EqualIntervals', 'Quantiles', or 'Manual'
# if break_method is 'Manual', you have to manually set the break points in the list below
# if break_method is not 'Manual', the selected_breaks variable wont't be used, but don't comment it out
selected_breaks = [] # e.g. [100,200,300,400,500]

# if need to join dataset with WRI shapefile
join_WRI_shape = True

# fetch columns
# name of the value column, which has the unique values or gradient values 
col_value = 'value'
# name of the datetime column, which has the timestamps
# if timeline is FALSE, col_datetime won't be used, you can leave it blank, but don't comment it out
col_datetime = 'datetime'
# name of the country column, which has the country names (used to join with the wri shapefile)
# if join_WRI_shape is FALSE, col_country won't be used, you can leave it blank, but don't comment it out
col_country = 'location'
# name of other columns that you want to included in the final table (e.g. need more columns for interaction)
# if you don't need any other columns, keep the col_interactive as a blank list
col_interactive = [] # e.g. 'time'


'''
Define functions
'''
def create_headers(timeline, year):
    '''
    creat layer config header
    INPUT  timeline: if the dataset has a timeline or not (Bool)
           year: if the dataset has a timeline, the year that used to create the map (Number)
    OUTPUT layer config header
    '''
    if timeline == True:
        return {
            'account': CARTO_USER,
            "layerType": "vector",
            "timelineLabel": str(year),
            "order": year,
            "timeline": True,
        }
    else:
        return {
            'account': CARTO_USER,
            "layerType": "vector",
        } 

def create_sql(timeline, year, join_WRI_shape, table_name, col_value, col_datetime, col_country, col_interactive):
    '''
    create sql statement to tell what data to pull from Carto
    INPUT  timeline: if the dataset has a timeline (Bool)
           year: use which year of the data to create the map (Number)
           join_WRI_shape: if the dateset need to be joined with WRI shapefile (Bool)
           table_name: name of the Carto table (String)
           col_value: the column the unique values or gradient values are based on (String)
           col_datetime: the column the timestamp is based on (String)
           col_country: the column the country name are based on (when join with the wri shapefile) (String)
           col_interactive: name of other columns that you want to included in the sql query (List)
    OUTPUT the sql statement 
    '''
    if len(col_interactive)>0:
        cols_interactive = [f'data.{col_inter}' for col_inter in col_interactive]
        separator = ', '
        cols_interactive = ', '+separator.join(cols_interactive)
    else:
        cols_interactive = ''

    if (join_WRI_shape == True and timeline == True):
        return f"SELECT wri.cartodb_id, ST_Transform(wri.the_geom, 3857) AS the_geom_webmercator, wri.name, data.{col_country}, data.{col_value}, data.{col_datetime}{cols_interactive} "\
               f"FROM {table_name} data "\
               f"LEFT OUTER JOIN wri_countries_a wri ON wri.iso_a3 ILIKE TRIM(data.{col_country}) "\
               f"WHERE EXTRACT(YEAR FROM data.{col_datetime}) = {year} AND data.{col_value} IS NOT NULL AND wri.iso_a3 IS NOT NULL "\
               "UNION "\
               f"SELECT wri.cartodb_id, ST_Transform(wri.the_geom, 3857) AS the_geom_webmercator, wri.name, data.{col_country}, data.{col_value}, data.{col_datetime}{cols_interactive} "\
               f"FROM {table_name} data "\
               f"INNER JOIN rw_aliasing_countries aliasing ON TRIM(data.{col_country}) ILIKE aliasing.alias "\
               "INNER JOIN wri_countries_a wri ON wri.iso_a3 = aliasing.iso "\
               f"WHERE EXTRACT(YEAR FROM data.{col_datetime}) = {year} AND data.{col_value} IS NOT NULL"
    if (join_WRI_shape == True and timeline == False):
        return f"SELECT wri.cartodb_id, ST_Transform(wri.the_geom, 3857) AS the_geom_webmercator, wri.name, data.{col_country}, data.{col_value}{cols_interactive} "\
               f"FROM {table_name} data "\
               f"LEFT OUTER JOIN wri_countries_a wri ON wri.iso_a3 ILIKE TRIM(data.{col_country}) "\
               f"WHERE data.{col_value} IS NOT NULL AND wri.iso_a3 IS NOT NULL "\
               "UNION "\
               f"SELECT wri.cartodb_id, ST_Transform(wri.the_geom, 3857) AS the_geom_webmercator, wri.name, data.{col_country}, data.{col_value}{cols_interactive} "\
               f"FROM {table_name} data "\
               f"INNER JOIN rw_aliasing_countries aliasing ON TRIM(data.{col_country}) ILIKE aliasing.alias "\
               "INNER JOIN wri_countries_a wri ON wri.iso_a3 = aliasing.iso "\
               f"WHERE data.{col_value} IS NOT NULL"
    if (join_WRI_shape == False and timeline == True):
        return f"SELECT * FROM {table_name} data"\
               f"WHERE EXTRACT(YEAR FROM data.{col_datetime}) = {year} AND data.{col_value} IS NOT NULL"
    if (join_WRI_shape == False and timeline == False):
        return f"SELECT * FROM {table_name}"

def fetch_carto():
    '''
    fetch Carto table
    OUTPUT carto table as a pandas dataframe
    '''
    sql = create_sql(timeline, year, join_WRI_shape, table_name, col_value, col_datetime, col_country, col_interactive)
    try_num = 1
    while try_num <= 3:
        try: 
            # convert response into json and make dictionary of layers
            r = cartosql.get(sql, user=CARTO_USER, key=CARTO_KEY).text
            df_dict = json.loads(r)
            break
        except:
            logging.info("Failed to fetch layers. Trying again after 30 seconds.")
            time.sleep(30)
            try_num += 1
    
    df_carto = pd.DataFrame(df_dict['rows'])

    return df_carto

def set_breaks(col_value, num_break, break_method, selected_breaks, break_type):
    '''
    set up break points
    INPUT  col_value: the column the unique values or gradient values are based on (String)
           num_break: number of breaks (Number)
           break_method: break method (for gradient breaks) (String)
           selected_breaks: the manully setted break points (List)
           break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT the break points saved in a list
    '''
    df_carto = fetch_carto()
    if break_type == 'choropleth':
        if break_method!='Manual':
            if break_method == 'Jenks':
                bin = mapclassify.JenksCaspall(df_carto[str(col_value)], k = num_break)
            elif break_method == 'EqualIntervals':
                bin = mapclassify.EqualInterval(df_carto[str(col_value)], k = num_break)
            elif break_method == "Quantiles":
                bin = mapclassify.Quantiles(df_carto[str(col_value)], k = num_break)
            final_breaks = [round(num, 2) for num in bin.bins]
        else:
            final_breaks = selected_breaks
    elif break_type == 'unique':
        if break_method!='Manual':
            final_breaks = pd.unique(df_carto[col_value])
        else:
            final_breaks = selected_breaks
    elif break_type == 'basic':
        final_breaks = selected_breaks
    return final_breaks

def create_cartocss_polygon(table_name, break_method, colors, break_type):
    '''
    create cartocss for polygon layer
    INPUT  table_name: name of the Carto table (String)
           break_method: break method (for gradient breaks) (String)
           colors: the list of color(s) (List)
           break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT the cartocss statement
    * polygon boundary was set to white with 0.3 line-width by default
    '''
    final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)

    if break_type == 'choropleth':
        cartocss = f"#{table_name} "\
                "{polygon-opacity: 1; line-width: 0.3; line-color: #FFF; line-opacity: 1;} "
        for i in range(num_break):
            if i == 0:
                cartocss = cartocss + f"[{col_value}<{final_breaks[i]}]"+"{polygon-fill:"+f"{colors[i]}"+";} "
            else:
                cartocss = cartocss + f"[{col_value}>={final_breaks[i-1]}][{col_value}<{final_breaks[i]}]"+"{polygon-fill:"+f"{colors[i]}"+";} "
    if break_type == 'unique':
        cartocss = f"#{table_name} "\
                "{polygon-opacity: 1; line-width: 0.3; line-color: #FFF; line-opacity: 1;} "
        for i in range(num_break):
                cartocss = cartocss + f"[{col_value}={final_breaks[i]}]"+"{polygon-fill:"+f"{colors[i]}"+";} "
    if break_type == 'basic':
        cartocss = f"#{table_name} "\
                "{polygon-fill:"+f"{colors[0]}"+"; polygon-opacity: 1; line-width: 0.3; line-color: #FFF; line-opacity: 1;} "
    
    return cartocss

def create_cartocss_line(table_name, break_method, colors, break_type):
    '''
    create cartocss for line layer
    INPUT  table_name: name of the Carto table (String)
           break_method: break method (for gradient breaks) (String)
           colors: the list of color(s) (List)
           break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT the cartocss statement
    * line-width set to 1.5 by default
    '''
    final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)

    if break_type == 'choropleth':
        cartocss = f"#{table_name} "\
                "{line-width: 1.5; line-opacity: 1; line-comp-op: screen;} "
        for i in range(num_break):
            if i == 0:
                cartocss = cartocss + f"[{col_value}<{final_breaks[i]}]"+"{line-color:"+f"{colors[i]}"+";} "
            else:
                cartocss = cartocss + f"[{col_value}>={final_breaks[i-1]}][{col_value}<{final_breaks[i]}]"+"{line-color:"+f"{colors[i]}"+";} "
    if break_type == 'unique':
        cartocss = f"#{table_name} "\
                "{line-width: 1.5; line-opacity: 1; line-comp-op: screen;} "
        for i in range(num_break):
                cartocss = cartocss + f"[{col_value}={final_breaks[i]}]"+"{line-color:"+f"{colors[i]}"+";} "
    if break_type == 'basic':
        cartocss = f"#{table_name} "\
                "{line-color:"+f"{colors[0]}"+"; line-width: 1.5; line-opacity: 1; line-comp-op: screen;} "
    
    return cartocss

def create_cartocss_point(table_name, break_method, colors, break_type):
    '''
    create cartocss for point layer
    INPUT  table_name: name of the Carto table (String)
           break_method: break method (for gradient breaks) (String)
           colors: the list of color(s) (List)
           break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT the cartocss statement
    * point boundary was set to white with 0.3 line-width by default
    '''
    final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)

    if break_type == 'choropleth':
        cartocss = f"#{table_name} "\
                "{marker-fill-opacity: 1; marker-line-width: 0.3; marker-line-color: #FFF; marker-line-opacity: 1; marker-allow-overlap: true;} "
        for i in range(num_break):
            if i == 0:
                cartocss = cartocss + f"[{col_value}<{final_breaks[i]}]"+"{marker-fill:"+f"{colors[i]}"+";} "
            else:
                cartocss = cartocss + f"[{col_value}>={final_breaks[i-1]}][{col_value}<{final_breaks[i]}]"+"{marker-fill:"+f"{colors[i]}"+";} "
    if break_type == 'unique':
        cartocss = f"#{table_name} "\
                "{marker-fill-opacity: 1; marker-line-width: 0.3; marker-line-color: #FFF; marker-line-opacity: 1; marker-allow-overlap: true;} "
        for i in range(num_break):
                cartocss = cartocss + f"[{col_value}={final_breaks[i]}]"+"{marker-fill:"+f"{colors[i]}"+";} "
    if break_type == 'basic':
        cartocss = f"#{table_name} "\
                "{marker-fill:"+f"{colors[0]}"+"; marker-fill-opacity: 1; marker-line-width: 0.3; marker-line-color: #FFF; marker-line-opacity: 1; marker-allow-overlap: true;} "
    
    return cartocss

def create_layers(table_name, geo_type):
    '''
    create layers json
    INPUT  table_name: name of the Carto table (String)
           geo_type: geometry type (String)
    OUTPUT layers json
    '''
    if geo_type == 'polygon':
        cartocss = create_cartocss_polygon(table_name, break_method, colors, break_type)
    elif geo_type == 'line':
        cartocss = create_cartocss_line(table_name, break_method, colors, break_type)
    elif geo_type == 'point':
        cartocss = create_cartocss_point(table_name, break_method, colors, break_type)

    sql = create_sql(timeline, year, join_WRI_shape, table_name, col_value, col_datetime, col_country, col_interactive)
    return {
        "options": {
            "cartocss_version": "2.3.0",
            "cartocss": f"{cartocss}",
            "sql": f"{sql}"
        },
        "type": "mapnik"
    }

def create_vectorLayers_polygon(col_value, break_type):
    '''
    create vectorlayers json for polygon layer
    INPUT  col_value: the column the unique values or gradient values are based on (String)
           break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT vectorlayers json
    '''
    if break_type == 'choropleth':
        final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)
        fill_color = ["step", ["to-number",["get", f"{col_value}"]], colors[0]]
        for color, selected_break in zip(colors[1:], final_breaks[:-1]):
            fill_color.append(selected_break)
            fill_color.append(color)
        return [{
            "paint": {
                "fill-color": fill_color,
                "fill-opacity": 1
            },
            "source-layer": "layer0",
            "type": "fill",
            "filter": [
                "all"
            ]
        }]
    if break_type == 'unique':
        final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)
        vectorLayers = [{"paint": {"fill-opacity": 1},"source-layer": "layer0","type": "fill","filter": ["all"]}]
        for color, selected_break in zip(colors, final_breaks):
            vectorLayers.append({"paint": {"fill-color": f'{color}'},"source-layer": "layer0","type": "fill","filter": ["all",["==", f"{col_value}", selected_break]]})
        return vectorLayers
    if break_type == 'basic':
        vectorLayers = [{"paint": {"fill-color": f"{colors[0]}","fill-opacity": 1},"source-layer": "layer0","type": "fill","filter": ["all"]}]
        return vectorLayers

def create_vectorLayers_line(col_value, break_type):
    '''
    create vectorlayers json for line layer
    INPUT  col_value: the column the unique values or gradient values are based on (String)
           break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT vectorlayers json
    * line width was set to 1.5 by default
    '''
    if break_type == 'choropleth':
        final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)
        line_color = ["step", ["to-number",["get", f"{col_value}"]], colors[0]]
        for color, selected_break in zip(colors[1:], final_breaks[:-1]):
            line_color.append(selected_break)
            line_color.append(color)
        return [{
            "paint": {
                "line-color": line_color,
                "line-width": 1.5,
                "line-opacity": 1
            },
            "source-layer": "layer0",
            "type": "line",
            "filter": [
                "all"
            ]
        }]
    if break_type == 'unique':
        final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)
        vectorLayers = []
        for color, selected_break in zip(colors, final_breaks):
            vectorLayers.append({"paint": {"line-color": f'{color}', "line-width":1.5, "line-opacity": 1},"source-layer": "layer0","type": "line","filter": ["all",["==", f"{col_value}", selected_break]]})
        return vectorLayers
    if break_type == 'basic':
        vectorLayers = [{"paint": {"line-color": f"{colors[0]}", "line-width":1.5, "line-opacity": 1},"source-layer": "layer0","type": "line","filter": ["all"]}]
        return vectorLayers

def create_vectorLayers_point(col_value, break_type):
    '''
    create vectorlayers json for point layer
    INPUT  col_value: the column the unique values or gradient values are based on (String)
           break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT vectorlayers json
    * circle stroke width/color/opacity could be modified mannually
    '''
    if break_type == 'choropleth':
        final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)
        circle_color = ["step", ["to-number",["get", f"{col_value}"]], colors[0]]
        for color, selected_break in zip(colors[1:], final_breaks[:-1]):
            circle_color.append(selected_break)
            circle_color.append(color)
        return [{
            "paint": {
                "circle-color": circle_color,
                "circle-opacity": 1,
                "circle-stroke-width": 0.3,
                "circle-stroke-color": "#FFF",
                "circle-stroke-opacity": 0
            },
            "source-layer": "layer0",
            "type": "circle",
            "filter": [
                "all"
            ]
        }]
    if break_type == 'unique':
        final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)
        vectorLayers = [{
            "paint": {
                "circle-opacity": 1,
                "circle-stroke-width": 0.3,
                "circle-stroke-color": "#FFF",
                "circle-stroke-opacity": 0
            },
            "source-layer": "layer0",
            "type": "circle",
            "filter": [
                "all"
            ]
        }]
        for color, selected_break in zip(colors, final_breaks):
            vectorLayers.append({"paint": {"circle-color": f'{color}'},"source-layer": "layer0","type": "circle","filter": ["all",["==", f"{col_value}", selected_break]]})
        return vectorLayers
    if break_type == 'basic':
        vectorLayers = [{"paint": {"circle-color": f"{colors[0]}","circle-opacity": 1,"circle-stroke-width": 0.3,"circle-stroke-color": "#FFF","circle-stroke-opacity": 0},"source-layer": "layer0","type": "circle","filter": ["all"]}]
        return vectorLayers

def create_boundary():
    '''
    create the boundary json for polygon layer
    * polygon boundary was set to white with 0.3 line-width
    '''
    return {
        "paint": {
            "line-width": 0.3,
            "line-color": "#fff",
            "line-opacity": 1
        },
        "source-layer": "layer0",
        "type": "line",
        "filter": [
            "all"
        ]
    }

def create_layer_config(geo_type):
    '''
    create layer config
    INPUT  geo_type: geometry type (String)
    OUTPUT layer config json
    '''
    layer_config = create_headers(timeline, year)
    if geo_type == 'polygon':
        vectorLayer = create_vectorLayers_polygon(col_value, break_type)
        vectorLayer.append(create_boundary())
    elif geo_type == 'line':
        vectorLayer = create_vectorLayers_line(col_value, break_type)
    elif geo_type == 'point':
        vectorLayer = create_vectorLayers_point(col_value, break_type)

    layer_config["body"] = {
        "layers": [create_layers(table_name, geo_type)], 
        "maxzoom": 18, 
        "vectorLayers": vectorLayer
        }

    return layer_config

def create_legend_config(break_type):
    '''
    create legend config
    INPUT  break_type: break type ('basic', 'unique', or 'choropleth') (String)
    OUTPUT layer config json
    '''
    final_breaks = set_breaks(col_value, num_break, break_method, selected_breaks, break_type)
    items = []
    if break_type == 'choropleth':
        for id, (selected_break, color) in enumerate(zip(final_breaks,colors)):
            items.append({
                "name": f"<{selected_break}",
                "color": color,
                "id": id
            })
    if break_type == 'unique' or break_type == 'basic':
        for id, (selected_break, color) in enumerate(zip(final_breaks,colors)):
            items.append({
                "name": f"{selected_break}",
                "color": color,
                "id": id
            })
    return {
        "type": break_type,
        "items" : items
    }

def main():
    '''
    main function
    OUTPUT print out SQL, CartoCSS, layer config json, and legend config json
    '''
    layer = create_layers(table_name, geo_type)
    print("SQL:")
    print(layer['options']['sql'] + "\n")
    print("CartoCSS:")
    print(layer['options']['cartocss'] + "\n")

    layer_config = create_layer_config(geo_type)
    legend_config = create_legend_config(break_type)
    print("Layer config:")
    print(json.dumps(layer_config, indent=2) + "\n")
    print("Legend config:")
    print(json.dumps(legend_config, indent=2))

'''
Run main function
'''
main()