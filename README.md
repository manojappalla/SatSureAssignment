# SatSure Assignment 

This repository contains the python module to download, pre-process, and create an ndvi image using the google earth engine python api, geemap, and folium


## Features

- Access sentinel-2 images, and cloud probability data set from google earth engine.
- Pre-process sentinel-2 image to remove the clouds by cloud masking and create a composite image from the sentinel-2 image collection.
- Create an ndvi image from the composite image.
- Download the ndvi image of your area of interest.


## Modules to be installed prior using the code

```bash
  pip install earthengine-api
  pip install geemap
  pip install folium
```
    
