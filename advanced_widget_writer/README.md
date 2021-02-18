**Write Advanced Widgets**

This folder contains Python scripts to write advanced widgets in the Resource Watch backoffice.

Folder contents:
1. **advanced_chart_widget.py**: This Python script helps you create or update advanced chart widgets from a working Vega configuration. You can take any working Vega configuration from a Vega editor and plug it in to this script. This script will add the Resource Watch-specific fields needed to make it into a widget. You can also add metadata to an advanced widget using this script or update the existing metadata of an advanced widget.
2. **embed_map_widget.py**: This Python script helps you create multi-layer map embed widgets. Note that these widgets use just as much data as a regular embed to load, so they should be added to dashboards with caution. The advantage to creating these (instead of just using a regular embed) is that you can include metadata such as a title, links to the source, etc. which are not available for a regular map embed.

To create your advanced widget:
<br><br>
For advanced chart widgets, use the code in the appropriate script to create the advanced widget.
<br><br>
For the multi-layer map embed widgets, you will have to create an empty widget in the back office first. You do not need to actually make a real widget, just click advanced, and give it the title, description, and whatever other metadata you want. Save that empty advanced widget.
<br><br>
Before running either of the script, you will need to load your .env file first. Please follow more detailed instructions inside the appropriate script.
