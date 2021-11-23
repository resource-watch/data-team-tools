from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import os
import ast
import requests
import pygsheets
import pandas as pd
import numpy as np
import io
import time
import logging
import dotenv
#insert the location of your .env file here:
dotenv.load_dotenv('/home/hastur_2021/documents/rw_github/cred/.env')

# Set up logging
# Get the top-level logger object
logger = logging.getLogger()
for handler in logger.handlers: logger.removeHandler(handler)
logger.setLevel(logging.INFO)
# make it print to the console.
console = logging.StreamHandler()
logger.addHandler(console)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Define the auth scopes to request.
scopes = 'https://www.googleapis.com/auth/analytics.readonly'
# Location of analytics key
key_file_location = os.path.abspath(os.getenv('ANALYTICS_APPLICATION_CREDENTIALS'))
DISCOVERY_URI = 'https://analyticsreporting.googleapis.com/$discovery/rest'
# View ID of RW "all website data" in analytics
view_id = os.getenv('VIEW_ID')
# Create variable to store credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file_location, scopes=scopes)
http = credentials.authorize(httplib2.Http())
# Authenticate and construct service.
service = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

# INPUTS
# Enter dates to fetch from Analytics API
startDate = '2020-10-31'
endDate = '2021-10-31'

# Name of google sheet where you're sending the pagePath data
# Change if you wish to create a new sheet
rw_metrics_sheet = 'pagepath_metrics_sheet'
# Name of the two google sheet where you're sending the eventLabel and eventAction data
# Change if you wish to create new sheets
downloaded_from_rw = 'download_from_rw'
downloaded_from_source = 'download_from_source'

def write_to_gsheet(sheet_name, df):
    """
    this function takes  a df and writes it under spreadsheet_id
    and sheet_name using your google spreadsheet credentials under service_file_path
    INPUT sheet_name: name you want to give the neww sheet (string)
          df: dataframe to upload as a google spreadsheet
    """
    # Path to our creadentials
    service_file_path = os.path.abspath(os.getenv('SPREADSHEETS_APPLICATION_CREDENTIALS'))
    # Id of the spreadsheet we're using to store the analytics information
    spreadsheet_id = os.getenv('DATA_CATALOGUE_ASSESMENT_ID')
    gc = pygsheets.authorize(service_file=service_file_path)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        sh.add_worksheet(sheet_name)
    except:
        pass
    wks_write = sh.worksheet_by_title(sheet_name)
    wks_write.clear('A1',None,'*')
    wks_write.set_dataframe(df, (1,1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1
    logger.info('Uploading {} to spreadsheets'.format(sheet_name))

def request_to_df(DIMS, METRICS,requests_list, startDate, endDate):
    '''
    This function transforms Analytics API response into a dataframe
    INPUT DIMS: dimensions to request from Analytics (list)
          METRICS: metrics to request from Analytics (list)
          requests_dict: parameters to build requests for analytics (list)
          startDate: Beginning date for request (string)
          endDate: End date for request (string)
    '''
    # This function builds the request to Analytics API
    data = service.reports().batchGet(body={'reportRequests':requests_list }).execute()
    # Transforming analytics response from dictionary to dataframe
    data_dic = {f"{i}": [] for i in DIMS + METRICS}
    for report in data.get('reports', []):
        rows = report.get('data', {}).get('rows', [])
        for row in rows:
            for i, key in enumerate(DIMS):
                data_dic[key].append(row.get('dimensions', [])[i]) # Get dimensions
            dateRangeValues = row.get('metrics', [])
            for values in dateRangeValues:
                all_values = values.get('values', []) # Get metric values
                for i, key in enumerate(METRICS):
                    data_dic[key].append(all_values[i])

    # Create a dataframe to store dictionary values   
    df = pd.DataFrame(data=data_dic)
    df.columns = [col.split(':')[-1] for col in df.columns]
    # Add a column with startDate and endDate for analytics request
    df['startDate'] = startDate 
    df['endDate'] = endDate 
    
    return df

def request_pagePath(startDate, endDate):
    '''
    This function specifies the metrics and dimensions to requesto to the analytics API
    INPUT startDate: Beginning date for request (string)
          endDate: End date for request (string)
    '''
    # Variable to request full page path
    DIMS = ['ga:pagePath'] # You can add up to 7 dimensions here: eg. 'month', 'year','country'
    # Metrics that we are going to request
    METRICS = ['ga:pageviews', 'ga:uniquePageviews', 'ga:avgTimeOnPage',
               'ga:bounceRate','ga:entrances', 'ga:exitRate',
               'ga:pageValue']
    # This request fetches metrics for datasets in RW
    # "dimensionFilterClauses" filters the "pagePath" so we only have datasets paths
    requests_list =  [{
        'viewId': view_id,
        'pageSize': 100000,
        'dateRanges': [{'startDate': startDate, 'endDate': endDate}],
        'dimensions': [{'name': name} for name in DIMS],
        "dimensionFilterClauses":[
            {"operator":"AND",
             "filters":[
                 {"dimensionName":"ga:pagePath",
                  "operator":"BEGINS_WITH",
                  "expressions":[
                      "/data/explore/"
                  ]
                 }
             ]
            }
        ],
        'metrics': [{'expression': exp} for exp in METRICS],
        'orderBys': [{"fieldName": "ga:pageviews", "sortOrder": "DESCENDING"}], 
        }]
    
    # Transform the dictionary into a dataframe
    logger.info('Requesting pagePath data to Analytics')
    df = request_to_df(DIMS, METRICS,requests_list, startDate, endDate)
    
    return df

def process_pagePath(df):
    '''
    This function extracts the RW API id or slug from pagePath and uses it to request
    information about the dataset from RW API, so we can merge it later with the 
    data team spreadsheet.
    INPUT df: dataframe containing Google analytics response
    '''
    # Creating column with subset of pagePath
    # Split pagePath column to extract the dataset string as a series
    new = df['pagePath'].str.split("/data/explore/", n = 1, expand = True)
    # Add the series to the analytics dataframe
    df['slug_or_id'] = new[1]
    # We remove the row with the '/data/explore/' and '/data/explore/24ffab8a-588d-4fb8-92de-8bc54abf7da6/metadata'
    # pagePaths because they will cause problems later on
    df = df[df.pagePath != '/data/explore/']
    df = df[df.pagePath != '/data/explore/24ffab8a-588d-4fb8-92de-8bc54abf7da6/metadata']
    # We create lists to store id, name, slug, publishing status from RW API
    ids = []
    names = []
    slugs = []
    published = []
    # Create a list with slugs and ids to obtain dataset information from RW API
    slug_ids_list_raw = df['slug_or_id'].tolist()
    # using list comprehension + enumerate() to remove duplicated from list 
    # we do this to avoid making too much API calls 
    slug_ids_list = [i for n, i in enumerate(slug_ids_list_raw) if i not in slug_ids_list_raw[:n]]
    logger.info('Requesting data to RW API')
    for index, element in enumerate(slug_ids_list):
        url = f'https://api.resourcewatch.org/v1/dataset/{element}'
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()['data']
            ids.append(data['id']) 
            names.append(data['attributes']['name']) 
            slugs.append(data['attributes']['slug'])
            published.append(data['attributes']['published']) 
        else:
            ids.append('No value') 
            names.append('No value') 
            slugs.append('No value')
            published.append('No value')
    
    # We append the lists we created as columns to a dataframe
    df2 = pd.DataFrame(slug_ids_list, columns=['slug_or_id'])
    df2['rw_api_id'] = ids
    df2['dataset_name'] = names
    df2['slug'] = slugs
    df2['published'] = published
    
    # We merge the dataset containing the information from RW API with 
    # the one containing the google analytics information
    df_pagepath = df.merge(df2,left_on="slug_or_id",right_on="slug_or_id", how = 'left')

    return df_pagepath

def process_spreadsheet(df):
    '''
    This function merges the data team spreadsheet with the dataframe containing the information 
    fetched from RW and Google Analytics API's
    INPUT df: dataframe with information from both API's    
    '''
    # Reading data team spreadsheet
    sheet = requests.get(os.getenv('METADATA_SHEET')).content
    spreadsheet = pd.read_csv(io.StringIO(sheet.decode('utf-8')),header=0, usecols=['New WRI_ID', 'API_ID','Status', 'Public Title', 'Frequency of Updates', 'Date of Content','Data Type'])
    # Merge analytics dataframe with data team spreadsheet on RW API id 
    rw_dataset_analytics = df.merge(spreadsheet,left_on="rw_api_id",right_on="API_ID", how = 'left')
    rw_dataset_analytics.reset_index(drop=True, inplace = True)
    # Create a topic column based on the first characters of WRI ID
    rw_dataset_analytics['topic'] = rw_dataset_analytics['New WRI_ID'].str[:3]
    # Create a dictionary to replace topic codes 
    topic_codes = {"foo":"Food and Agriculture",
                   "ene":"energy", "cli":"climate",
                   "dis":"disaster",
                   "for": "forests", "wat":"water",
                   "loc":"local data",
                   "soc":"society",
                   "ocn":"ocean", "cit":"cities",
                   "bio": "biodiversity",
                   "com":"commerce",
                   "cit":"cities", "blo":"blog",
                   "req":"request"}
    # We replace the abbreviated codes with their full names
    rw_dataset_analytics['topic'] = rw_dataset_analytics['topic'].replace(topic_codes, regex=True)
    # Write pagePath dataframe to a new Google Spreadsheet
    write_to_gsheet(rw_metrics_sheet,rw_dataset_analytics)

    return rw_dataset_analytics

def request_eventLabel(startDate,endDate):
    '''
    This function requests the eventLabel and eventAction information from
    google analytics. In this way we can know which datasets are the most downloaded.
    INPUT startDate: Beginning date for request (string)
          endDate: End date for request (string)
    '''
    # We set the dimensions and variables that we will request
    DIMS = ['ga:eventLabel','ga:eventAction']
    METRICS = ['ga:totalEvents']
    requests_list =  [{
        'viewId': view_id,
        'pageSize': 100000,
        'dateRanges': [{'startDate': startDate, 'endDate': endDate}],
        'dimensions': [{'name': name} for name in DIMS],
        'metrics': [{'expression': exp} for exp in METRICS],
        'orderBys': [{"fieldName": "ga:totalEvents", "sortOrder": "DESCENDING"}], 
        }]
    # Transform the response dictionary into a dataframe
    logger.info('Requesting eventLabel data to Analytics')
    df = request_to_df(DIMS, METRICS,requests_list, startDate, endDate)
    # We filter the eventAction to only retain the events that interests us
    df = df.loc[(df['eventAction'] == 'Download Data From Source' ) | (df['eventAction'] == 'Download Data')]
    # Reading data team spreadsheet
    sheet = requests.get(os.getenv('METADATA_SHEET')).content
    spreadsheet = pd.read_csv(io.StringIO(sheet.decode('utf-8')),header=0, usecols=['New WRI_ID', 'API_ID','Status', 'Public Title', 'Frequency of Updates', 'Date of Content','Data Type']) 
    # Merging with data team sheet
    merged = df.merge(spreadsheet,left_on="eventLabel",right_on="Public Title", how = 'left')
    # We split the merged dataset into two
    # One dataset holds metrics for datasets downloaded directly from RW and the other those downloaded from the source site
    download_from_rw = merged.loc[merged['eventAction'] == 'Download Data']
    download_from_source = merged.loc[merged['eventAction'] == 'Download Data From Source']
    # We reset the index and upload to google spreadsheet
    download_from_rw.reset_index(inplace = True, drop = True)
    write_to_gsheet(downloaded_from_rw,download_from_rw)
    # We reset the index and upload to google spreadsheet
    download_from_source.reset_index(inplace = True, drop = True)
    write_to_gsheet(downloaded_from_source,download_from_source)
    
    return merged

# Variable to request full page path
# Request to fetch metrics from Analytics API and process them as a dataframe
df_analytics = request_pagePath(startDate, endDate)
# Process the analytics dataframe and fetch information from RW's API
df_analytics = process_pagePath(df_analytics)
# Merge the processed analytics dataframe with data team spreadsheet
# then upload to a new spreadsheet
rw_dataset_analytics = process_spreadsheet(df_analytics)
# Request eventLabel data and write it to a google spreadsheet
event_analytics = request_eventLabel(startDate,endDate)


