import ee
import geemap


class Sent2DownProcNDVI:

    # DEFAULT PARAMETERS
    AOI = ee.Geometry.Point(-122.269, 45.701)
    START_DATE = '2020-06-01'
    END_DATE = '2020-06-02'
    CLOUD_FILTER = 60
    CLD_PRB_THRESH = 50
    NIR_DRK_THRESH = 0.15
    CLD_PRJ_DIST = 1
    BUFFER = 50

    # ***************************************** FETCH DATA - START ******************************************
    # 1) DEFINE A FUNCTION TO FETCH AND FILTER SR AND S2CLOUDLESS DATA USING EARTH ENGINE API
    def get_collection(self, aoi, start_date, end_date):

        """
        sentinel 2 surface reflectance collection and sentinel-2 cloud probability collection are fetched based on the
        parameters entered by the user and two collections are joined together and the image collection is returned.

        :param aoi: Area of interest
        :param start_date: Date from which you want to start searching for images
        :param end_date: Date from which you want to stop searching for images
        :return: image collection
        """

        # Import and filter S2 SR.
        s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR')
                     .filterBounds(aoi)
                     .filterDate(start_date, end_date)
                     .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', self.CLOUD_FILTER)))

        # Import and filter s2cloudless.
        s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
                            .filterBounds(aoi)
                            .filterDate(start_date, end_date))

        # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
        return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
            'primary': s2_sr_col,
            'secondary': s2_cloudless_col,
            'condition': ee.Filter.equals(**{
                'leftField': 'system:index',
                'rightField': 'system:index'
            })
        }))

    # ******************************************* FETCH DATA - END ******************************************


    # ***************************************** PRE-PROCESSING - START **************************************
    # 2) CLOUD MASK COMPONENT FUNCTION DEFINITIONS
    def add_cloud_bands(self, img):

        """
        Here we access the s2cloudless image joined in the get_collection function and select the probability band.
        if the probability of a pixel is greater than threshold value then the pixel is considered cloud and the cloud
        probability and cloud mask are added as bands to every image in the image collection

        :param img:
        :return:
        """

        # Get s2cloudless image, subset the probability band.
        cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

        # Condition s2cloudless by the probability threshold value.
        is_cloud = cld_prb.gt(self.CLD_PRB_THRESH).rename('clouds')

        # Add the cloud probability layer and cloud mask as image bands.
        return img.addBands(ee.Image([cld_prb, is_cloud]))

    def add_shadow_bands(self, img):

        """
        This function first identifies water pixels using SCL band, and then identifies the dark nir pixels that are not
        water. Next, the direction of cloud shadow is determined and the cloud shadows are projected based on the
        distance specified. Then the intersection of the dark pixels with the cloud shadows is identified and the bands
        are added to the input image.

        :param img:
        :return:
        """
        # Identify water pixels from the SCL band.
        not_water = img.select('SCL').neq(6)

        # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
        SR_BAND_SCALE = 1e4
        dark_pixels = img.select('B8').lt(self.NIR_DRK_THRESH * SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')

        # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
        shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));

        # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
        cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, self.CLD_PRJ_DIST * 10)
                    .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
                    .select('distance')
                    .mask()
                    .rename('cloud_transform'))

        # Identify the intersection of dark pixels with cloud shadow projection.
        shadows = cld_proj.multiply(dark_pixels).rename('shadows')

        # Add dark pixels, cloud projection, and identified shadows as image bands.
        return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))


    def add_cld_shdw_mask(self, img):

        """
        Add the cloud shadow mask to the image as a new band.

        :param img:
        :return:
        """

        # Add cloud component bands.
        img_cloud = self.add_cloud_bands(img)

        # Add cloud shadow component bands.
        img_cloud_shadow = self.add_shadow_bands(img_cloud)

        # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
        is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)

        # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
        # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
        is_cld_shdw = (is_cld_shdw.focalMin(2).focalMax(self.BUFFER * 2 / 20)
                       .reproject(**{'crs': img.select([0]).projection(), 'scale': 20})
                       .rename('cloudmask'))

        # Add the final cloud-shadow mask to the image.
        return img_cloud_shadow.addBands(is_cld_shdw)


    # 3) CLOUD MASK FUNCTION
    def apply_cld_shdw_mask(self, img):
        # Subset the cloudmask band and invert it so clouds/shadow are 0, else 1.
        not_cld_shdw = img.select('cloudmask').Not()

        # Subset reflectance bands and update their masks, return the result.
        return img.select('B.*').updateMask(not_cld_shdw)
    # ***************************************** PRE-PROCESSING - END ****************************************


    # 4) FUNCTION TO LOAD A SHAPEFILE
    def load_shape_file(self, filename):

        """
        This function is used to load a shapefile as a feature collection using geemap.

        :param filename: shapefile path
        :return: returns a feature collection
        """
        return geemap.shp_to_ee(filename)


    # ***************************************** DOWNLOAD - START *******************************************
    # 5) FUNCTION TO DOWNLOAD AN IMAGE
    def download(self, img, geom, scale, filename):

        """
        This function is used to download an image in the form of a tif.

        :param img: image to be downloaded
        :param geom: feature collection that is converted to geometry should be used
        :param scale: resolution in meters
        :param filename: name of the file with which it should be downloaded in the local drive
        :return: none
        """
        img = img.clip(geom).unmask()
        geemap.ee_export_image(
            img, filename=filename, scale=scale, region=geom, file_per_band=False
        )
    # ***************************************** DOWNLOAD - END *******************************************


    # ***************************************** NDVI - START *******************************************
    # 6) FUNCTION TO CREATE AN NDVI
    def ndvi(self, img):

        """
        This function extracts nir, red band from the image passed as an argument and returns an ndvi image

        :param img: image from which ndvi should be extracted
        :return: returns an ndvi image
        """
        nir = img.select('B8')
        red = img.select('B4')
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('ndvi')
        return ndvi
    # ***************************************** NDVI - START *******************************************


    # ***************************************** CREATE COMPOSITE - START *******************************************
    # 7) FUNCTION TO CREATE A CLOUD FREE COMPOSITE
    def cloud_masked_composite(self, collection):
        """
        This function creates a composite out of an image collection after masking the clouds and returns the composite

        :param collection: image collection from which composite should be created
        :return:
        """
        return collection.map(self.add_cld_shdw_mask).map(self.apply_cld_shdw_mask).median()
    # ***************************************** CREATE COMPOSITE - END *******************************************