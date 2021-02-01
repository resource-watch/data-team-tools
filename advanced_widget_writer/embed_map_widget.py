import LMIPy as lmi
import dotenv
dotenv.load_dotenv('')

# input widget API ID for the empty advanced widget you have created and want to overwrite
widget_to_overwrite = ''

# enter embed url that you want to be shown in widget. see example below:
# url_to_embed = r"https://resourcewatch.org/embed/data/explore/cli006-Polar-Sea-Ice-Monthly-Median-Extents?section=All%20data&zoom=0.8955740754997088&lat=4.40585468259109&lng=-51.06249926194696&pitch=0&bearing=0&basemap=dark&labels=light&layers=%255B%257B%2522dataset%2522%253A%2522b1ebea96-5963-4c2c-9273-7d08536ac07d%2522%252C%2522opacity%2522%253A1%252C%2522layer%2522%253A%2522d87bb471-1ac0-4f79-818a-e270f04185bf%2522%257D%252C%257B%2522dataset%2522%253A%2522e740efec-c673-431a-be2c-b214613f641a%2522%252C%2522opacity%2522%253A1%252C%2522layer%2522%253A%2522d0713c73-941e-446f-a94d-8e75951e3b03%2522%257D%252C%257B%2522dataset%2522%253A%2522484fbba1-ac34-402f-8623-7b1cc9c34f17%2522%252C%2522opacity%2522%253A1%252C%2522layer%2522%253A%2522b92c01ee-eb2c-4835-8625-d138db75a1cd%2522%257D%255D&page=1&sort=most-viewed&sortDirection=-1&topics=%255B%2522sea_ice%2522%255D"
url_to_embed = r""

# create payload to send to API
payload = {
    "widgetConfig": {
        "url":f"{url_to_embed}"
      }
    }

# load in API credentials
API_TOKEN = os.getenv('RW_API_KEY')

# load the widget we are going to overwrite
widget = lmi.Widget(widget_to_overwrite)

# Update the widget
widget = widget.update(update_params=payload, token=API_TOKEN)