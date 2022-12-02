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
    

## Documentation

### 1. Attributes
    AOI -> This is the area of interest
    START_DATE -> Date from which you want to start searching for images
    END_DATE -> Date from which you want to stop searching for images
    CLOUD_FILTER -> Percentage of cloud cover you want to retain while filtering
    CLD_PRB_THRESH -> Values greater than this are considered clouds (in percentage)
    NIR_DRK_THRESH -> Values less than this are considered as cloud shadow
    CLD_PRJ_DIST -> This value is in metres which tells the maximum distance to be searched for a cloud shadow from the edge of a cloud
    BUFFER -> Distance to dilate the edge of cloud identified objects.

### 2. Functions
#### 2.1. get_collection:
    Sentinel 2 surface reflectance collection and sentinel-2 cloud probability collection are fetched based on the parameters entered by the user and two collections are joined together and the image collection is returned.

#### 2.2. add_cloud_bands:
    Here we access the s2cloudless image joined in the get_collection function and select the probability band. If the probability of a pixel is greater than threshold value then the pixel is considered cloud and the cloud probability and cloud mask are added as bands to the image.

#### 2.3. add_shadow_bands:
    This function first identifies water pixels using SCL band, and then identifies the dark nir pixels that are not water. Next, the direction of cloud shadow is determined and the cloud shadows are projected based on the distance specified. Then the intersection of the dark pixels with the cloud shadows is identified and the bands are added to the input image.

#### 2.4. add_cld_shdw_mask:
    Add the cloud shadow mask to the image as a new band.

#### 2.5. cloud_masked_composite:
    This function creates a composite out of an image collection after masking the clouds in the composite and returns the composite.

#### 2.6. load_shape_file:
    This function is used to load a shapefile using geemap.

#### 2.7. download: 
    This function is used to download an image in the form of a tif.

#### 2.8. ndvi:
    This function extracts nir, red band from the image passed as an argument and returns an ndvi image.
## Usage/Examples

The usage of this python module is clearly mentioned in the python notebook with name test.ipynb in the repository.
