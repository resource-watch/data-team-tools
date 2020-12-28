**Creating Mult-layer Advanced Map Widgets**

This tool was created to create multi-layer map embed widgets. These widgets use just as much data as a regular embed to load, so they should be added to dashboards with caution. The advantage to creating these (instead of just using a regular embed) is that you can include metadata such as a title, links to the source, etc. which are not available for a regular map embed.

To create your embed widget: 
  1. Pick one of the datasets in your overlay and create a new widget. Make it an advanced widget (you do not need to actually make a real widget, just click advanced) and give it the title, description, and whatever else you want. Save that empty advanced widget.
    <br><br>
  2. Use the code in embed_widget.py to overwrite the widget with the map embed url. You will need to load your .env file in like always, put in the widget id for the widget you created as widget_to_overwrite and replace the url_to_embed with the correct embed url.