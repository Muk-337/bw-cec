import os
from io import BytesIO
import requests
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import folium
import urllib.request
import urllib.parse
import mapbox_vector_tile
import xml.etree.ElementTree as xmlet
import lxml.etree as xmltree
from PIL import Image as plimg
from PIL import ImageDraw
import numpy as np
import pandas as pd
from owslib.wms import WebMapService
from IPython.display import Image, display
import geopandas as gpd
from shapely.geometry import box
import urllib.request
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.plot import show
import fiona
from datetime import datetime, timedelta


# Connect to GIBS WMS Service
wms = WebMapService('https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?', version='1.1.1')

# Configure request for MODIS_Terra_CorrectedReflectance_TrueColor
img = wms.getmap(layers=['MODIS_Terra_CorrectedReflectance_TrueColor'],  # Layers
                 srs='epsg:4326',  # Map projection
                 bbox=(-180,-90,180,90),  # Bounds
                 size=(1200, 600),  # Image size
                 time='2021-09-21',  # Time of data
                 format='image/png',  # Image format
                 transparent=True)  # Nodata transparency

# Save output PNG to a file
out = open('python-examples/MODIS_Terra_CorrectedReflectance_TrueColor.png', 'wb')
out.write(img.read())
out.close()

# View image
Image('python-examples/MODIS_Terra_CorrectedReflectance_TrueColor.png')

# Construct capability URL.
wmsUrl = 'https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?\
SERVICE=WMS&REQUEST=GetCapabilities'

# Request WMS capabilities.
response = requests.get(wmsUrl)

# Display capabilities XML in original format. Tag and content in one line.
WmsXml = xmltree.fromstring(response.content)
# print(xmltree.tostring(WmsXml, pretty_print = True, encoding = str))

# Currently total layers are 1081.

# Coverts response to XML tree.
WmsTree = xmlet.fromstring(response.content)

alllayer = []
layerNumber = 0

# Parse XML.
for child in WmsTree.iter():
    for layer in child.findall("./{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer//*/"): 
         if layer.tag == '{http://www.opengis.net/wms}Layer': 
            f = layer.find("{http://www.opengis.net/wms}Name")
            if f is not None:
                alllayer.append(f.text)
                
                layerNumber += 1

print('There are layers: ' + str(layerNumber))

for one in sorted(alllayer)[:5]:
    print(one)
print('...')
for one in sorted(alllayer)[-5:]:
    print(one)

    # Define layername to use.
layerName = 'Landsat_WELD_CorrectedReflectance_Bands157_Global_Annual'  

# Get general information of WMS.
for child in WmsTree.iter():
    if child.tag == '{http://www.opengis.net/wms}WMS_Capabilities': 
        print('Version: ' +child.get('version'))
    
    if child.tag == '{http://www.opengis.net/wms}Service': 
        print('Service: ' +child.find("{http://www.opengis.net/wms}Name").text)
        
    if child.tag == '{http://www.opengis.net/wms}Request': 
        print('Request: ')
        for e in child:
            print('\t ' + e.tag.partition('}')[2])
                            
        all = child.findall(".//{http://www.opengis.net/wms}Format")
        if all is not None:
            print("Format: ")
            for g in all:
                print("\t " + g.text)     
                
        for e in child.iter():
            if e.tag == "{http://www.opengis.net/wms}OnlineResource":
                print('URL: ' + e.get('{http://www.w3.org/1999/xlink}href'))
                break

# Get layer attributes.
for child in WmsTree.iter():
    for layer in child.findall("./{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer//*/"): 
         if layer.tag == '{http://www.opengis.net/wms}Layer': 
            f = layer.find("{http://www.opengis.net/wms}Name")
            if f is not None:
                if f.text == layerName:
                    # Layer name.
                    print('Layer: ' + f.text)
                    
                    # All elements and attributes:
                    # CRS
                    e = layer.find("{http://www.opengis.net/wms}CRS")
                    if e is not None:
                        print('\t CRS: ' + e.text)
                    
                    # BoundingBox.
                    e = layer.find("{http://www.opengis.net/wms}EX_GeographicBoundingBox")
                    if e is not None:
                        print('\t LonMin: ' + e.find("{http://www.opengis.net/wms}westBoundLongitude").text)
                        print('\t LonMax: ' + e.find("{http://www.opengis.net/wms}eastBoundLongitude").text)
                        print('\t LatMin: ' + e.find("{http://www.opengis.net/wms}southBoundLatitude").text)
                        print('\t LatMax: ' + e.find("{http://www.opengis.net/wms}northBoundLatitude").text)
                    
                    # Time extent.
                    e = layer.find("{http://www.opengis.net/wms}Dimension")
                    if e is not None:
                        print('\t TimeExtent: ' + e.text)
                        
                    # Style.
                    e = layer.find("{http://www.opengis.net/wms}Style")
                    if e is not None:
                        f = e.find("{http://www.opengis.net/wms}Name")
                        if f is not None:
                            print('\t Style: ' + f.text)

print('')                         