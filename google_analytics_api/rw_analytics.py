from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import os
import requests
import pygsheets
import pandas as pd
import io
import logging
import dotenv
#insert the location of your .env file here:

# Set up logging
# Get the top-level logger object
logger = logging.getLogger()
for handler in logger.handlers: logger.removeHandler(handler)
logger.setLevel(logging.INFO)
# Make it print to the console
console = logging.StreamHandler()
logger.addHandler(console)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Define the auth scopes to request
SCOPES = 'https://www.googleapis.com/auth/analytics.readonly'
# Location of analytics key
KEY_FILE_LOCATION = os.path.abspath(os.getenv('ANALYTICS_APPLICATION_CREDENTIALS'))
DISCOVERY_URI = 'https://analyticsreporting.googleapis.com/$discovery/rest'
# View ID of RW "all website data" in analytics
VIEW_ID = os.getenv('VIEW_ID')
# Create variable to store credentials
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, scopes=SCOPES)
HTTP = CREDENTIALS.authorize(httplib2.Http())
# Authenticate and construct service
SERVICE = build('analytics', 'v4', http=HTTP, discoveryServiceUrl=DISCOVERY_URI)
# Path to our creadentials
SERVICE_FILE_PATH = os.path.abspath(os.getenv('SPREADSHEETS_APPLICATION_CREDENTIALS'))

# INPUTS
# Enter dates to fetch from Analytics API
startDate = '2020-12-14'
endDate = '2021-12-14'

# Name of google sheet where you're sending all pagePath data
# Change if you wish to create a new sheet
rw_metrics_sheet = 'pagepath_metrics_sheet'
# Name of google sheet where you're sending aggregated pagePath data
# Change if you wish to create a new sheet
rw_metrics_aggr_sheet = 'pagepath_metrics_aggregated_sheet'
# Name of the two google sheet where you're sending the eventLabel and eventAction data
# Change if you wish to create new sheets
downloaded_from_rw = 'download_from_rw'
downloaded_from_source = 'download_from_source'
# Name of the two google sheet where you're aggregated download activity
# Change if you wish to create new sheets
downloaded_aggr_sheet = 'download_aggregated_sheet'
# Create a dictionary to replace topic codes 
topic_codes = {"bio": "biodiversity", "blo": "blog", "cit": "cities",
               "cli": "climate", "com": "commerce", "dis": "disaster",
               "ene": "energy", "foo": "food and agriculture", "for": "forests", 
               "loc": "local data", "req": "request", "soc": "society",
               "ocn": "ocean", "wat": "water"}

def write_to_gsheet_ga(sheet_name, df):
    '''
    This function takes a dataframe and writes it under spreadsheet_id
    and sheet_name using your google spreadsheet credentials under SERVICE_FILE_PATH
    INPUT sheet_name: name you want to give the neww sheet (string)
          df: dataframe to upload as a google spreadsheet (dataframe)
    '''
    # Id of the spreadsheet we're using to store the analytics information
    spreadsheet_id = os.getenv('DATA_CATALOGUE_ASSESSMENT_ID')
    gc = pygsheets.authorize(service_file=SERVICE_FILE_PATH)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        sh.add_worksheet(sheet_name)
    except:
        pass
    wks_write = sh.worksheet_by_title(sheet_name)
    wks_write.clear('A1', None, '*')
    wks_write.set_dataframe(df, (1, 1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1
    logger.info('Uploading {} to spreadsheets'.format(sheet_name))

def request_to_df(DIMS, METRICS, requests_list, startDate, endDate):
    '''
    This function transforms Analytics API response into a dataframe
    INPUT DIMS: dimensions to request from Analytics (list)
          METRICS: metrics to request from Analytics (list)
          requests_dict: parameters to build requests for analytics (list)
          startDate: Beginning date for request (string)
          endDate: End date for request (string)
    '''
    # This function builds the request to Analytics API
    data = SERVICE.reports().batchGet(body={'reportRequests': requests_list }).execute()
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
    DIMS = ['ga:pagePath'] # You can add more dimensions here: eg. 'month', 'year', 'country'
    # Metrics that we are going to request
    METRICS = ['ga:pageviews', 'ga:uniquePageviews', 'ga:avgTimeOnPage',
               'ga:bounceRate', 'ga:entrances', 'ga:exitRate']
    # This request fetches metrics for datasets in RW
    # "dimensionFilterClauses" filters the "pagePath" so we only have datasets paths
    requests_list = [{
        'viewId': VIEW_ID,
        'pageSize': 100000,
        'dateRanges': [{'startDate': startDate, 'endDate': endDate}],
        'dimensions': [{'name': name} for name in DIMS],
        "dimensionFilterClauses":[
            {"operator": "AND",
             "filters":[
                 {"dimensionName": "ga:pagePath",
                  "operator": "BEGINS_WITH",
                  "expressions": [
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
    df = request_to_df(DIMS, METRICS, requests_list, startDate, endDate)
    
    return df

def process_pagePath(df):
    '''
    This function extracts the RW API id or slug from pagePath and uses it to request
    information about the dataset from RW API, so we can merge it later with the data team spreadsheet.
    INPUT df: dataframe containing Google analytics response (dataframe)
    '''
    # Creating column with subset of pagePath
    # Split pagePath column to extract the dataset string as a series
    new = df['pagePath'].str.split("/data/explore/", n=1, expand=True)
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
    # Using list comprehension + enumerate() to remove duplicated from list 
    # We do this to avoid making too much API calls 
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
    df_pagepath = df.merge(df2, left_on="slug_or_id", right_on="slug_or_id", how='left')

    return df_pagepath

def process_spreadsheet(df, topic_codes):
    '''
    This function merges the data team spreadsheet with the dataframe containing the information 
    fetched from RW and Google Analytics API's
    INPUT df: dataframe with information from both API's (dataframe) 
          topic_codes: dictionary to replace topic codes (dictionaty)
    '''
    # Reading data team spreadsheet
    sheet = requests.get(os.getenv('METADATA_SHEET')).content
    spreadsheet = pd.read_csv(io.StringIO(sheet.decode('utf-8')), header=0, usecols=['New WRI_ID', 'API_ID', 'Status', 'Public Title', 'Frequency of Updates', 'Date of Content', 'Spatial Resolution', 'Geographic Coverage', 'Data Type', 'Last Update', 'Latest Check'])
    # Merge analytics dataframe with data team spreadsheet on RW API id 
    rw_dataset_analytics = df.merge(spreadsheet, left_on="rw_api_id", right_on="API_ID", how='outer')
    # Drop records that cannot be merged to the metadata spreadsheet
    rw_dataset_analytics.dropna(subset=['API_ID'], inplace=True)
    rw_dataset_analytics.reset_index(drop=True, inplace=True)
    # Create a topic column based on the first characters of WRI ID
    rw_dataset_analytics['topic'] = rw_dataset_analytics['New WRI_ID'].str[:3]
    # We replace the abbreviated codes with their full names
    rw_dataset_analytics['topic'] = rw_dataset_analytics['topic'].replace(topic_codes, regex=True)
    # Write pagePath dataframe to a new Google Spreadsheet
    write_to_gsheet_ga(rw_metrics_sheet, rw_dataset_analytics)
    # We create a version of the dataframe with aggregated metrics
    rw_aggr_analytics = rw_dataset_analytics.copy()
    # Drop columns thatwon't be used
    rw_aggr_analytics.drop(['avgTimeOnPage', 'bounceRate', 'exitRate'], axis=1, inplace=True)
    # drop NAN records before aggregating metrics
    rw_aggr_analytics.dropna(subset=['API_ID',], inplace=True)
    rw_aggr_analytics.dropna(subset=['pageviews',], inplace=True)
    rw_aggr_analytics.dropna(subset=['uniquePageviews',], inplace=True)
    rw_aggr_analytics.dropna(subset=['entrances',], inplace=True)
    # convert data type to integer
    rw_aggr_analytics['pageviews'] = rw_aggr_analytics['pageviews'].astype(int)
    rw_aggr_analytics['uniquePageviews'] = rw_aggr_analytics['uniquePageviews'].astype(int)
    rw_aggr_analytics['entrances'] = rw_aggr_analytics['entrances'].astype(int)
    # aggregate by API_ID
    rw_aggr_analytics = rw_aggr_analytics.groupby(['API_ID'], as_index=False).agg({'pagePath': 'first', 'pageviews': 'sum', 'uniquePageviews': 'sum',
                                                                                   'entrances': 'sum', 'startDate': 'first', 'endDate': 'first', 'slug_or_id': 'first',
                                                                                   'rw_api_id':'first', 'dataset_name':'first', 'slug':'first',
                                                                                   'published': 'first', 'New WRI_ID': 'first', 'Status': 'first',
                                                                                   'Public Title': 'first', 'Date of Content': 'first',
                                                                                   'Frequency of Updates': 'first', 'Spatial Resolution': 'first',
                                                                                   'Geographic Coverage': 'first', 'Data Type': 'first',
                                                                                   'Last Update': 'first', 'Latest Check': 'first', 'topic': 'first'})
    # Write aggregated pagePath dataframe to a new Google Spreadsheet
    write_to_gsheet_ga(rw_metrics_aggr_sheet, rw_aggr_analytics)
    
    return rw_dataset_analytics

def request_eventLabel(startDate, endDate, topic_codes):
    '''
    This function requests the eventLabel and eventAction information from
    google analytics. In this way we can know which datasets are the most downloaded.
    INPUT startDate: Beginning date for request (string)
          endDate: End date for request (string)
          topic_codes: dictionary to replace topic codes (dictionary)
    '''
    # We set the dimensions and variables that we will request
    DIMS = ['ga:eventLabel', 'ga:eventAction'] # You can add more dimensions here
    METRICS = ['ga:totalEvents']
    requests_list = [{
        'viewId': VIEW_ID,
        'pageSize': 100000,
        'dateRanges': [{'startDate': startDate, 'endDate': endDate}],
        'dimensions': [{'name': name} for name in DIMS],
        'metrics': [{'expression': exp} for exp in METRICS],
        'orderBys': [{"fieldName": "ga:totalEvents", "sortOrder": "DESCENDING"}], 
        }]
    # Transform the response dictionary into a dataframe
    logger.info('Requesting eventLabel data to Analytics')
    df = request_to_df(DIMS, METRICS, requests_list, startDate, endDate)
    # We filter the eventAction to only retain the events that interests us
    df = df.loc[(df['eventAction'] == 'Download Data From Source' ) | (df['eventAction'] == 'Download Data')]
    # Reading data team spreadsheet
    sheet = requests.get(os.getenv('METADATA_SHEET')).content
    spreadsheet = pd.read_csv(io.StringIO(sheet.decode('utf-8')), header=0, usecols=['New WRI_ID', 'API_ID', 'Status', 'Public Title', 'Frequency of Updates', 'Date of Content', 'Spatial Resolution', 'Geographic Coverage', 'Data Type', 'Last Update', 'Latest Check']) 
    # Merging with data team sheet
    merged = df.merge(spreadsheet, left_on="eventLabel", right_on="Public Title", how='left')
    # We split the merged dataset into two
    # One dataset holds metrics for datasets downloaded directly from RW and the other those downloaded from the source site
    download_from_rw = merged.loc[merged['eventAction'] == 'Download Data']
    download_from_source = merged.loc[merged['eventAction'] == 'Download Data From Source']
    # Create a topic column based on the first characters of WRI ID
    download_from_rw.loc[:, 'topic'] = download_from_rw.loc[:, 'New WRI_ID'].str[:3]
    # We replace the abbreviated codes with their full names
    download_from_rw.loc[:, 'topic'] = download_from_rw.loc[:, 'topic'].replace(topic_codes, regex=True)
    # We reset the index and upload to google spreadsheet
    download_from_rw.reset_index(inplace=True, drop=True)
    write_to_gsheet_ga(downloaded_from_rw, download_from_rw)
    # Create a topic column based on the first characters of WRI ID
    download_from_source.loc[:, 'topic'] = download_from_source.loc[:, 'New WRI_ID'].str[:3]
    # We replace the abbreviated codes with their full names
    download_from_source.loc[:, 'topic'] = download_from_source.loc[:, 'topic'].replace(topic_codes, regex=True)
    # We reset the index and upload to google spreadsheet
    download_from_source.reset_index(inplace=True, drop=True)
    write_to_gsheet_ga(downloaded_from_source, download_from_source)
    # We create a version of the dataframe for aggregated metrics
    download_aggr_sheet = download_from_rw.append(download_from_source)
    # drop records before aggregating metrics
    download_aggr_sheet.dropna(subset=['API_ID'], inplace=True)
    download_aggr_sheet.dropna(subset=['totalEvents'], inplace=True)
    # Drop columns that won't be used
    download_aggr_sheet.drop(['eventAction'], axis=1, inplace=True)
    download_aggr_sheet['totalEvents'] = download_aggr_sheet['totalEvents'].astype(int)
    # aggregate by API_ID
    download_aggr_sheet = download_aggr_sheet.groupby(['API_ID'], as_index=False).agg({'eventLabel': 'first', 'totalEvents':'sum',
                                                                                   'startDate': 'first', 'endDate':'first',
                                                                                   'New WRI_ID':'first', 'Status':'first',
                                                                                   'Public Title':'first', 'Date of Content':'first',
                                                                                   'Frequency of Updates':'first', 'Spatial Resolution':'first',
                                                                                   'Geographic Coverage':'first', 'Data Type':'first',
                                                                                   'Last Update':'first', 'Latest Check':'first',
                                                                                   'topic':'first'})
    # We reset the index and upload to google spreadsheet
    download_aggr_sheet.reset_index(inplace=True, drop=True)
    write_to_gsheet_ga(downloaded_aggr_sheet, download_aggr_sheet)

    return merged

'''
Create RW GA metrics google spreadsheet
'''
# Variable to request full page path
# Request to fetch metrics from Analytics API and process them as a dataframe
df_analytics = request_pagePath(startDate, endDate)
# Process the analytics dataframe and fetch information from RW's API
df_analytics = process_pagePath(df_analytics)
# Merge the processed analytics dataframe with data team spreadsheet
# then upload to a new spreadsheet
rw_dataset_analytics = process_spreadsheet(df_analytics, topic_codes)
# Request eventLabel data and write it to a google spreadsheet
event_analytics = request_eventLabel(startDate, endDate, topic_codes)


'''
Merge RW GA metrics and RW API metrics
'''
def write_to_gsheet_api(sheet_name, df):
    '''
    This function takes a dataframe and writes it under spreadsheet_id
    and sheet_name using your google spreadsheet credentials under SERVICE_FILE_PATH
    INPUT sheet_name: name you want to give the neww sheet (string)
          df: dataframe to upload as a google spreadsheet (dataframe)
    '''
    # Id of the spreadsheet we're using to store the analytics information
    spreadsheet_id = os.getenv('RW_API_SPREADSHEET_ID')
    gc = pygsheets.authorize(service_file=SERVICE_FILE_PATH)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        sh.add_worksheet(sheet_name)
    except:
        pass
    wks_write = sh.worksheet_by_title(sheet_name)
    wks_write.clear('A1', None, '*')
    wks_write.set_dataframe(df, (1, 1), encoding='utf-8', fit=True)
    wks_write.frozen_rows = 1
    logger.info('Uploading {} to spreadsheets'.format(sheet_name))

def process_gsheet_ga(ga_spreadsheet_id, gc):
    '''
    This function processes the Google Analytics metrics and prepares them for merging with RW API metrics
    INPUT ga_spreadsheet_id: Id of the spreadsheet we're using to store the GA metrics (string)
          gc: google account authorization
    '''
    # Open GA metrics google spreadsheet by key
    ga_sh = gc.open_by_key(ga_spreadsheet_id)
    # Open worksheets by titles
    rw_metrics_aggr_ws = ga_sh.worksheet_by_title('pagepath_metrics_aggregated_sheet')
    downloaded_from_rw_ws = ga_sh.worksheet_by_title('download_from_rw')
    downloaded_from_source_ws = ga_sh.worksheet_by_title('download_from_source')
    # Load all records in the worksheets to pandas dataframes
    rw_metrics_aggr_df = pd.DataFrame(rw_metrics_aggr_ws.get_all_records())
    downloaded_from_rw_df = pd.DataFrame(downloaded_from_rw_ws.get_all_records())
    downloaded_from_source_df = pd.DataFrame(downloaded_from_source_ws.get_all_records())
    # merge download from RW worksheet and download from source worksheet and keep all records
    downloaded_df = downloaded_from_rw_df.merge(downloaded_from_source_df, left_on="API_ID", right_on="API_ID", how="outer")
    # drop records without API_ID
    downloaded_df.dropna(subset=['API_ID'], inplace=True)
    # select columns
    downloaded_df = downloaded_df.loc[:, ['totalEvents_x', 'totalEvents_y', 'API_ID', 'New WRI_ID_x', 'New WRI_ID_y', 'Status_x', 'Public Title_x', 'Status_y', 'Public Title_y', 'topic_x', 'topic_y']]
    # aggregate two columns with the same name from two worksheets to one column
    downloaded_df['New WRI_ID_x'].update(downloaded_df.pop('New WRI_ID_y'))
    downloaded_df['Status_x'].update(downloaded_df.pop('Status_y'))
    downloaded_df['Public Title_x'].update(downloaded_df.pop('Public Title_y'))
    downloaded_df['topic_x'].update(downloaded_df.pop('topic_y'))
    # rename columns
    downloaded_df.rename(columns={'totalEvents_x': 'download_rw', 'totalEvents_y': 'download_source', 'New WRI_ID_x': 'New WRI_ID', 'Status_x': 'Status', 'Public Title_x': 'Public Title', 'topic_x': 'topic'}, inplace=True)
    # merge aggregated RW metrics worksheet and download metrics worksheet and keep all records
    ga_df = rw_metrics_aggr_df.merge(downloaded_df, left_on="API_ID", right_on="API_ID", how="outer")
    # select columns
    ga_df = ga_df.loc[:, ['API_ID', 'published', 'New WRI_ID_x', 'Status_x',  'New WRI_ID_y', 'Status_y','Public Title_x', 'Public Title_y', 'topic_x', 'topic_y', 'pagePath', 'pageviews', 'uniquePageviews', 'entrances','download_rw', 'download_source']]
    # aggregate two columns with the same name from two worksheets to one column
    ga_df['New WRI_ID_x'].update(ga_df.pop('New WRI_ID_y'))
    ga_df['Status_x'].update(ga_df.pop('Status_y'))
    ga_df['Public Title_x'].update(ga_df.pop('Public Title_y'))
    ga_df['topic_x'].update(ga_df.pop('topic_y'))
    # rename columns
    ga_df.rename(columns={'New WRI_ID_x': 'New WRI_ID', 'Status_x': 'Status', 'Public Title_x': 'Public Title', 'topic_x': 'topic'}, inplace=True)
    
    return ga_df

def process_gsheet_api(api_spreadsheet_id, gc):
    '''
    This function processes the Resource Watch API metrics and prepares them for merging with Google Analytics metrics 
    INPUT api_spreadsheet_id: Id of the spreadsheet we're using to store the API metrics (string)
          gc: google account authorization
    '''
    # Open google spreadsheet by key
    api_sh = gc.open_by_key(api_spreadsheet_id)
    # Open worksheet by title
    api_ws = api_sh.worksheet_by_title('api-datasets-table')
    # Load all records in the worksheets to pandas dataframes
    api_df = pd.DataFrame(api_ws.get_all_records())
    # select columns
    api_df = api_df.loc[:, ['datasetId', 'application', 'numApps', 'name', 'published', 'datasetViewCount', 'layerViewCount', 'widgetViewCount']]
    # select records to keep 'rw' datasets
    api_df = api_df.loc[api_df.application == 'rw']

    return api_df


# Id of the spreadsheet we're using to store the metrics
ga_spreadsheet_id = os.getenv('DATA_CATALOGUE_ASSESSMENT_ID')
api_spreadsheet_id = os.getenv('RW_API_SPREADSHEET_ID')
# Authorization
gc = pygsheets.authorize(service_file=SERVICE_FILE_PATH)
# Process Google Analytics metrics and Resource Watch API metrics
ga_df = process_gsheet_ga(ga_spreadsheet_id, gc)
api_df = process_gsheet_api(api_spreadsheet_id, gc)
# Merge processed metrics
merge_df = ga_df.merge(api_df, left_on="API_ID", right_on="datasetId", how='right')
# aggregate two columns with the same name from two worksheets to one column
merge_df['API_ID'].update(merge_df.pop('datasetId'))
merge_df['published_x'].update(merge_df.pop('published_y'))
# rename columns
merge_df.rename(columns={'published_x': 'published'}, inplace=True)
# upload the merged dataframe to Google Analytics google spreadsheet
write_to_gsheet_ga('merge_ga_api', merge_df)
