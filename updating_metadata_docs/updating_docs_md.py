import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

#Before starting you need to set credentials in the anaconda prompt
#set GOOGLE_APPLICATION_CREDENTIALS=

# Part of this code is Licensed under the Apache License, Version 2.0
# Copy of License at http://www.apache.org/licenses/LICENSE-2.0

#filepath for your credentials
cred_file = ""

#define the scopes you may need to use, discovery info
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/documents",
         "https://www.googleapis.com/auth/drive.metadata.readonly"]

#build helps call the api that you're going to use - in this case docs and drive
drive_service = build('drive', 'v3')
doc_service = build('docs', 'v1')
sheets_service = build('sheets', 'v4')

#used to authenticate Google Spreadsheets
credentials = ServiceAccountCredentials.from_json_keyfile_name(cred_file, scope)
gc = gspread.authorize(credentials)

#Google Sheet you will be using to store metadata
SPREADSHEET_ID = "" #add id
workbook = gc.open_by_key(SPREADSHEET_ID)
sheet = workbook.worksheet("Master")

#fields from the RW metadata template
#this is used in creating a dataframe as well (see: metadata_df)
#if any of these fields change, you must change metadata_df as well
doc_fields = ["Source Organizations", "Function", "Overview", "Methodology", 
              "Cautions", "Additional Information", "Visualizing the Data", 
              "Citation", "License", "Disclaimer", "Direct Download link", 
              "Download from Source link", "Learn More link", "Formal Name", 
              "Date of Content", "Spatial Resolution", "Frequency of Updates", 
              "Geographic Coverage", "Data Format", 
              "Subtitle \n(example: UNEP-WCMC/IUCN)", "Published Language", 
              "Data shown on Resource Watch Map"]
 
"""
Extract text from Google Doc and save it as a dictionary.
"""
def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.
    """
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')
def read_strucutural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
    """
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_strucutural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get('tableOfContents')
            text += read_strucutural_elements(toc.get('content'))
    return text

'''
Creates dataframe that contains metadata from the Google Docs
'''
def metadata_dataframe():
    
    doc_files = drive_service.files().list(q="mimeType='application/vnd.google-apps.document'", spaces='drive',
                                          fields='files(id, name)').execute()
    doc_info = doc_files['files']
    
    metadata_dict = []
    for x in range(len(doc_info)):
        #get the document id and name
        DOCUMENT_ID = doc_info[x]['id']
        DOCUMENT_NAME = doc_info[x]['name']
        
        #gets the text in a documents
        doc = doc_service.documents().get(documentId=DOCUMENT_ID).execute()
        doc_content = doc.get('body').get('content')
        doc_text = read_strucutural_elements(doc_content)

        #checks if metadata fields are repeated in the text
        #if fields appear more than once
        #consider revising the document on Google Docs
        for metadata_field in doc_fields:
            if metadata_field not in doc_text:
                print("The %s is not in the %s text" % (metadata_field, DOCUMENT_NAME))
                exit()
            elif doc_text.count(metadata_field) != 1:
                print("The %s repeats more than once in %s" % (metadata_field, DOCUMENT_NAME))
                exit()

        print("%s ready for ingestion." % DOCUMENT_NAME)
        
        #stores text in dictionary based on metadata fields
        doc_dict = {}
        n = 1
        for field in range(len(doc_fields)-1):
            space_index = DOCUMENT_NAME.index(" ")
            doc_dict['Public Title'] = DOCUMENT_NAME[space_index+1:]
            doc_dict['WRI_ID'] = DOCUMENT_NAME[:space_index]
            metadata_text = doc_text.partition(doc_fields[n-1])[2]
            field_text = metadata_text.partition(doc_fields[n])[0].strip()
            #remaining_text = metadata_text.partition(doc_fields[n])[2] 
            doc_dict[doc_fields[n-1]] = field_text 
            n += 1
            
        metadata_dict += [doc_dict]
        print("%s metadata has been saved." % DOCUMENT_NAME)
    #creates a pandas datafrmae
    df = pd.DataFrame(metadata_dict)
    df['Processed Data Link (S3)'] = ""
    #reorders columns so that WRI_ID and Public Title appear first
    df = df[[
             'WRI_ID',
             'Public Title',
             'Source Organizations',
             'Function',
             'Overview',
             'Methodology',
             'Cautions',
             'Additional Information',
             'Visualizing the Data',
             'Citation',
             'License',
             'Disclaimer',
             'Direct Download link',
             'Processed Data Link (S3)',
             'Download from Source link',
             'Learn More link',
             'Formal Name',
             'Date of Content',
             'Spatial Resolution',
             'Frequency of Updates',             
             'Geographic Coverage',
             'Data Format',
             
             'Subtitle \n(example: UNEP-WCMC/IUCN)',
             'Published Language'
             ]]
    
    return df

'''
Takes dataframe and adds it to a Google spreadsheet
'''
def iter_pd(df):
    for val in df.columns:
        yield val
    for row in df.to_numpy():
        for val in row:
            if pd.isna(val):
                yield ""
            else:
                yield val
def pandas_to_sheets(pandas_df, sheet, clear = True):
    # Updates all values in a workbook to match a pandas dataframe
    if clear:
        sheet.clear()
    (row, col) = pandas_df.shape
    cells = sheet.range("A1:{}".format(gspread.utils.rowcol_to_a1(row + 1, col)))
    for cell, val in zip(cells, iter_pd(pandas_df)):
        cell.value = val
    sheet.update_cells(cells)
    print("Google Sheet has been updated.")


#Once the docs are in the appropriate folder,
#along with the spreadsheet, run this
pandas_to_sheets(metadata_dataframe(), sheet)



