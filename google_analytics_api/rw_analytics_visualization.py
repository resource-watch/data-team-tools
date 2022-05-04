from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import os
import pygsheets
import pandas as pd
import logging
import dotenv
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
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

# Get script folder
os.chdir(os.path.dirname(os.path.realpath(__file__)))
# Define working folder
data_dir = 'visualizations'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)


# Name of google sheets
rw_metrics_sheet = 'pagepath_metrics_sheet'
rw_metrics_aggr_sheet = 'pagepath_metrics_aggregated_sheet'
downloaded_from_rw = 'download_from_rw'
downloaded_from_source = 'download_from_source'
downloaded_aggr_sheet = 'download_aggregated_sheet'

# Path to our creadentials
service_file_path = os.path.abspath(os.getenv('SPREADSHEETS_APPLICATION_CREDENTIALS'))
# Id of the spreadsheet we're using to store the analytics information
spreadsheet_id = os.getenv('DATA_CATALOGUE_ASSESSMENT_ID')
# Authorization
gc = pygsheets.authorize(service_file=service_file_path)
# Open google spreadsheet by key
sh = gc.open_by_key(spreadsheet_id)

# Open worksheet by title
ws = sh.worksheet_by_title(rw_metrics_aggr_sheet)
# Load all records in the worksheet to pandas dataframe
df = pd.DataFrame(ws.get_all_records())
# Sort records by uniquePageviews
df = df.sort_values(by='uniquePageviews', ascending=False)
# Create a subset of the top 30 viewed datasets
top_30 = df.iloc[0: 30]
# Create a subset of published datasets with uniquePageviews less than 5 uniquePageviews
less_5_view_pub = df[(df.published == 'TRUE') & (df.uniquePageviews <= 5)]
# save as a csv file
less_5_view_pub.to_csv('visualizations/less_5_view_pub.csv', index=True)
# Create a subset of unpublished datasets with only one uniquePageviews 
less_1_view_unpub = df[(df.published == 'FALSE') & (df.uniquePageviews == 1)]
# save as a csv file
less_1_view_unpub.to_csv('visualizations/less_1_view_unpub.csv', index=True)

# Create a pie chart of top 30 datasets by topic
labels = top_30.groupby(['topic']).count().iloc[:,0].sort_values(ascending=False).index.tolist()
y = top_30.groupby(['topic']).count().iloc[:,0].sort_values(ascending=False).tolist()
y = [360/sum(y)*x for x in y]
colors = ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600']
fig, ax = plt.subplots(figsize=(6, 6))
patches, texts, pcts = ax.pie(y, labels=labels, autopct='%.1f%%', startangle=90, colors=colors)
ax.set_title('Top 30 datasets by topic', fontsize=16)
plt.setp(pcts, color='white', fontweight='bold')
plt.setp(texts, fontsize=12)
plt.tight_layout()
plt.savefig('visualizations/top_30_by_topic.png')

# Create a pie chart by published (or not)
labels = top_30.groupby(['Status']).count().iloc[:,0].sort_values(ascending=False).index.tolist()
y = top_30.groupby(['Status']).count().iloc[:,0].sort_values(ascending=False).tolist()
y = [360/sum(y)*x for x in y]
colors = ['#003f5c', '#bc5090', '#ffa600']
fig, ax = plt.subplots(figsize=(6, 6))
patches, texts, pcts = ax.pie(y, labels=labels, autopct='%.1f%%', startangle=90, colors=colors)
ax.set_title('Top 30 datasets by status', fontsize=16)
plt.setp(pcts, color='white', fontweight='bold')
plt.setp(texts, fontsize=12)
plt.tight_layout()
plt.savefig('visualizations/top_30_by_status.png')

# Create a pie chart of Regular VS NRT
labels = ['Regular', 'NRT']
y = [len(top_30)-len(top_30[top_30['New WRI_ID'].str.contains('nrt')]), len(top_30[top_30['New WRI_ID'].str.contains('nrt')])]
y = [360/sum(y)*x for x in y]
colors = ['#003f5c', '#ffa600']
fig, ax = plt.subplots(figsize=(6, 6))
patches, texts, pcts = ax.pie(y, labels=labels, autopct='%.1f%%', startangle=90, colors=colors)
ax.set_title('Top 30 datasets Regular VS NRT', fontsize=16)
plt.setp(pcts, color='white', fontweight='bold')
plt.setp(texts, fontsize=12)
plt.tight_layout()
plt.savefig('visualizations/top_30_NRT.png')

# Create a bar chart for top 30 datasets by uniquePageviews
labels = top_30['Public Title'][::-1]
y = top_30['uniquePageviews'][::-1]
category = list(top_30['topic'].unique())
labels_pos = [i for i, _ in enumerate(labels)]
fig, ax = plt.subplots(figsize=(12, 7))
colors = {'energy': "#fd7f6f", 'society': "#beb9db", 'biodiversity': "#fdcce5", 'commerce':"#bd7ebe", 
          'climate':"#ffb55a", 'water':"#7eb0d5", 'forests': "#b2e061", 'cities': "#ffee65"}
ax.barh(labels_pos, y, color=[colors[i] for i in top_30['topic'][::-1]])
ax.set_xlabel("uniquePageviews")
ax.set_title("Top 30 datasets uniquePageviews", fontsize=16)
ax.set_yticks(labels_pos, labels)
handles = [plt.Rectangle((0, 0), 1, 1, color=colors[i]) for i in category]
plt.legend(handles, category, title="Topics", loc="lower right")
plt.tight_layout()
plt.savefig('visualizations/top_30_uniquePageviews.png')

# Create a summary table for published datasets and unpublished datasets
topics = list(df.topic.unique())
cutoffs = [10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10, 0]

# Published datasets
df_list = []
index_list = []
for i in range(len(cutoffs)-1):
    index_list.append(str(cutoffs[i]) + '-' + str(cutoffs[i+1]))
    row_list = []
    for topic in topics:
        row_list.append(df[(df.published=='TRUE') & (df.topic==topic) & (df.uniquePageviews.astype(int) < cutoffs[i]) & (df.uniquePageviews.astype(int) >= cutoffs[i+1])].count()[0])
    df_list.append(row_list)
pub_sum_df = pd.DataFrame(df_list, columns=topics, index=index_list, dtype=int)
# add row total and column total
pub_sum_df['total'] = pub_sum_df.sum(axis=1)
pub_sum_df.loc['total'] = pub_sum_df.sum()
# add mean and median uniquePageviews by topic
for topic in topics:
    pub_sum_df.loc['mean uniquePagereviews', topic] = round(df[(df.published == 'TRUE') & (df.topic == topic)]['uniquePageviews'].astype(float).mean(), 2)
    pub_sum_df.loc['median uniquePagereviews', topic] = round(df[(df.published == 'TRUE') & (df.topic == topic)]['uniquePageviews'].astype(float).median(), 2)
# save as a csv file
pub_sum_df.to_csv('visualizations/published_dataset_summary.csv', index = True)

# Unpublished datasets
df_list = []
index_list = []
for i in range(len(cutoffs)-1):
    index_list.append(str(cutoffs[i]) + '-' + str(cutoffs[i+1]))
    row_list = []
    for topic in topics:
        row_list.append(df[(df.published=='FALSE') & (df.topic==topic) & (df.uniquePageviews.astype(int) < cutoffs[i]) & (df.uniquePageviews.astype(int) >= cutoffs[i+1])].count()[0])
    df_list.append(row_list)
unpub_sum_df = pd.DataFrame(df_list, columns=topics, index=index_list, dtype=int)
# add row total and column total
unpub_sum_df['total'] = unpub_sum_df.sum(axis=1)
unpub_sum_df.loc['total'] = unpub_sum_df.sum()
# add mean and median uniquePageviews by topic
for topic in topics:
    unpub_sum_df.loc['mean uniquePagereviews', topic] = round(df[(df.published == 'FALSE') & (df.topic == topic)]['uniquePageviews'].astype(float).mean(), 2)
    unpub_sum_df.loc['median uniquePagereviews', topic] = round(df[(df.published == 'FALSE') & (df.topic == topic)]['uniquePageviews'].astype(float).median(), 2)
# save as a csv file
unpub_sum_df.to_csv('visualizations/unpublished_dataset_summary.csv', index=True)

# Create a scatter plot of view vs download
# Open worksheet by title
ws = sh.worksheet_by_title(downloaded_aggr_sheet)
# Load all records in the worksheet to pandas dataframe
df_download = pd.DataFrame(ws.get_all_records())
# Merge view google sheet and download google sheet
df_view_download = df.merge(df_download[['API_ID','totalEvents']], left_on="API_ID", right_on="API_ID", how='inner')
df_view_download = df_view_download.sort_values(by='uniquePageviews', ascending=True)
# log transformation
view = [np.log(x) for x in df_view_download.uniquePageviews]
download = [np.log(x) for x in df_view_download.totalEvents]
# create plot
fig, ax = plt.subplots(figsize=(8, 6))
scatter = ax.scatter(view, download, c=df_view_download.Status.astype('category').cat.codes, cmap=matplotlib.colors.ListedColormap(['red', 'blue', 'orange', 'gray']))
ax.set_xlabel("uniquePageviews (log scale)")
ax.set_ylabel("Download (log scale)")
ax.set_title("View VS Download")
ax.legend(handles=scatter.legend_elements()[0], labels=['Archieved', 'Blog/request', 'Publishde', 'Unpublished'], loc='lower right')
plt.tight_layout()
plt.savefig('visualizations/view_vs_download.png')

# Create a bar chart for top 30 datasets by download
# Drop duplicate
df_download = df_download.drop_duplicates(subset=['Public Title'])
# Sort records by uniquePageviews
df_download = df_download.sort_values(by='totalEvents', ascending=False)
# Create a subset of the top 30 viewed datasets
top_30_download = df_download.iloc[0:30]
labels = top_30_download['Public Title'][::-1]
y = top_30_download['totalEvents'][::-1]
labels_pos = [i for i, _ in enumerate(labels)]
# create plot
fig, ax = plt.subplots(figsize=(12, 7))
ax.barh(labels_pos, y, color=["#7eb0d5"])
ax.set_xlabel("totalEvents (download)")
ax.set_title("Top 30 datasets totalEvents (download)", fontsize=16)
ax.set_yticks(labels_pos, labels)
plt.tight_layout()
plt.savefig('visualizations/top_30_download.png')