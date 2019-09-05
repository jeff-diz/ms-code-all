# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 10:20:36 2019

@author: disbr007

"""

from osgeo import gdal, osr, ogr
import numpy as np
import logging


class Raster():
    '''
    A class wrapper using GDAL to simplify working with rasters.
    Basic functionality:
        -read array from raster
        -read stacked array
        -write array out with same metadata
        -sample raster at point in geocoordinates
        -sample raster with window around point
    '''
    
    def __init__(self, raster_path):
        self.data_src = gdal.Open(raster_path)
        self.geotransform = self.data_src.GetGeoTransform()
        
        self.prj = osr.SpatialReference()
        self.prj.ImportFromWkt(self.data_src.GetProjectionRef())
        
        self.x_sz = self.data_src.RasterXSize
        self.y_sz = self.data_src.RasterYSize
        self.nodata_val = self.data_src.GetRasterBand(1).GetNoDataValue()
        self.dtype = self.data_src.GetRasterBand(1).DataType
        
        ## Get the raster as an array
        ## Defaults to band 1 -- use ReadArray() to return stack of multiple bands
        self.Array = self.data_src.ReadAsArray()


    def ReadStackedArray(self, stacked=True):
        '''
        Read raster as array, stacking multiple bands as either stacked array or multiple arrays
        stacked: boolean - specify False to return a separate array for each band
        '''
        ## Get number of bands in raster
        num_bands = self.data_src.RasterCount
        ## For each band read as array and add to list
        band_arrays = []
        for band in range(num_bands):
            band_arr = self.data_src.GetRasterBand(band).ReadAsArray()
            band_arrays.append(band_arr)
        
        ## If stacked is True, stack bands and return
        if stacked == True:
            ## Control for 1 band rasters as stacked=True is the default
            if num_bands > 1:
                stacked_array = np.dstack(band_arrays)
            else:
                stacked_array = band_arrays[0]
                
            return stacked_array
        
        ## Return list of band arrays
        else:
            return band_arrays
            
        
    def WriteArray(self, array, out_path):
        '''
        Writes the passed array with the metadata of the current raster object
        as new raster.
        '''
        # Get dimensions of input array
        rows, cols, depth = array.shape
        
        # Create output file
        fmt = 'GTiff'
        driver = gdal.GetDriverByName(fmt)
        dst_ds = driver.Create(out_path, self.x_sz, self.y_sz, 1, self.dtype)
        dst_ds.SetGeoTransform(self.geotransform)
        dst_ds.SetProjection(self.prj.ExportToWkt())

        # Loop through each layer of array and right as band
        for i in range(depth):        
            dst_ds.GetRasterBand(i).WriteArray(array)
            dst_ds.GetRasterBand(i).SetNoDataValue(self.nodata_val)
        
        dst_ds = None
        
        
    def SamplePoint(self, point):
        '''
        Samples the current raster object at the given point. Must be the
        sampe coordinate system used by the raster object.
        point: tuple of (y, x) in geocoordinates
        '''
        ## Convert point geocoordinates to array coordinates
        py = int(np.around((point[0] - self.geotransform[3]) / self.geotransform[5]))
        px = int(np.around((point[1] - self.geotransform[0]) / self.geotransform[1]))
        ## Handle point being out of raster bounds
        try:    
            point_value = self.Array[py, px]
        except IndexError as e:
            logging.error('Point not within raster bounds.')
            logging.error(e)
            point_value = None
        return point_value
    
    
    def SampleWindow(self, center_point, window_size, agg='mean', grow_window=False, max_grow=100000):
        '''
        Samples the current raster object using a window centered 
        on center_point. Assumes 1 band raster.
        center_point: tuple of (y, x) in geocoordinates
        window_size: tuple of (y_size, x_size) as number of pixels (must be odd)
        agg: type of aggregation, default is mean, can also me sum, min, max
        grow_window: set to True to increase the size of the window until a valid value is 
                        included in the window
        max_grow: the maximum area (x * y) the window will grow to          
        '''
        
        
        
        def window_bounds(window_size, py, px):
            '''
            Takes a window size and center pixel coords and 
            returns the window bounds as ymin, ymax, xmin, xmax
            window_size: tuple (3,3)
            py: int 125
            px: int 100
            '''
            ## Get window around center point
            # Get size in y, x directions
            y_sz = window_size[0]
            y_step = int(y_sz / 2)
            x_sz = window_size[1]
            x_step = int(x_sz / 2)
            
            # Get pixel locations of window bounds
            ymin = py - y_step
            ymax = py + y_step + 1 # slicing doesn't include stop val so add 1
            xmin = px - x_step
            xmax = px + x_step + 1 
            
            return ymin, ymax, xmin, xmax
        
        
        ## Convert center point geocoordinates to array coordinates
        py = int(np.around((center_point[0] - self.geotransform[3]) / self.geotransform[5]))
        px = int(np.around((center_point[1] - self.geotransform[0]) / self.geotransform[1]))
        
        ## Handle window being out of raster bounds
        try:
            growing = True
            while growing == True:
                ymin, ymax, xmin, xmax = window_bounds(window_size, py, px)
                window = self.Array[ymin:ymax, xmin:xmax].astype(np.float32)
                window = np.where(window==-9999.0, np.nan, window)
                
                ## Test for window with all nans to avoid getting 0's for all nans
                # Returns an array of True/False where True is valid values
                window_valid = window == window
                
                if True in window_valid:
                    ## Window contains at least one valid value, do aggregration
                    agg_lut = {
                        'mean': np.nanmean(window),
                        'sum': np.nansum(window),
                        'min': np.nanmin(window),
                        'max': np.nanmax(window)
                        }
                    window_agg = agg_lut[agg]
                    
                    # Do not grow if valid values found
                    growing = False
                    
                else:
                    ## Window all nan's, return nan value (arbitratily picking -9999)
                    # If grow_window is True, increase window (y+2, x+2)
                    if grow_window == True:
                        window_size = (window_size[0]+2, window_size[1]+2)
                    # If grow_window is False, return no data and exit while loop
                    else:
                        window_agg = -9999
                        growing = False
            
            
        except IndexError as e:
            logging.error('Window bounds not within raster bounds.')
            logging.error(e)
            window_agg = None
            
        return window_agg
