# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 13:52:48 2019

@author: disbr007
GDAL DEM Derivatives
"""

## Standard Libs
import logging, os, sys
import numpy as np

## Third Party Libs
import cv2
from osgeo import gdal
from scipy.ndimage.filters import generic_filter

## Local libs
from misc_utils.RasterWrapper import Raster


gdal.UseExceptions()


def gdal_dem_derivative(input_dem, output_path, derivative, return_array=False, *args):
    '''
    Takes an input DEM and creates a derivative product
    input_dem: DEM
    derivate: one of "hillshade", "slope", "aspect", "color-relief", "TRI", "TPI", "Roughness"
    return_array: optional argument to return the computed derivative as an array. (slow IO as it just loads the new file.)
    Example usage: slope_array = dem_derivative(dem, 'slope', array=True)
    '''
    
    supported_derivatives = ["hillshade", "slope", "aspect", "color-relief", 
                             "TRI", "TPI", "Roughness"]
    if derivative not in supported_derivatives:
        logging.error('Unsupported derivative type. Must be one of: {}'.format(supported_derivatives))
        sys.exit()
    
#    out_name = '{}_{}.tif'.format(os.path.basename(input_dem).split('.')[0], derivative)
#    out_path = os.path.join(os.path.dirname(input_dem), out_name)
    
    
    gdal.DEMProcessing(output_path, input_dem, derivative, *args)
    
    if return_array:
        from RasterWrapper import Raster
        array = Raster(output_path).Array
        
        return array

    
def calc_tpi(dem, size):
    '''
    OpenCV implementation of TPI
    dem: array
    size: int, kernel size in x and y directions (square kernel)
    Note - borderType determines handline of edge cases. REPLICATE will take the outermost row and columns and extend
    them as far as is needed for the given kernel size.
    '''
    kernel = np.ones((size,size),np.float32)/(size*size)
    ## -1 indicates new output array
    dem_conv = cv2.filter2D(dem, -1, kernel, borderType=cv2.BORDER_REPLICATE)
    tpi = dem - dem_conv
    
    return tpi


def calc_tpi_dev(dem, size):
    '''
    Based on (De Reu 2013)
    Calculates the tpi/standard deviation of the kernel to account for surface roughness.
    dem: array
    size: int, kernel size in x and y directions (square kernel)
    '''
    tpi = calc_tpi(dem, size)
    ## Calculate the standard deviation of each cell, mode='nearest' == cv2.BORDER_REPLICATE
    std_array = generic_filter(dem, np.std, size=size, mode='nearest')
    
    tpi_dev = tpi / std_array
    
    return tpi_dev


## TESTING
size = 101
test_dem_p = r'C:\code\ms-code-all\sample_data\tks_examples\rts_ex1.tif'
test_dem_src = Raster(test_dem_p)
test_dem = test_dem_src.Array

print('tpi')
tpi = calc_tpi(test_dem, size)
print('dev')
dev = calc_tpi_dev(test_dem, size)

test_dem_src.WriteArray(tpi, r'C:\code\ms-code-all\scratch\tpi_{}.tif'.format(size))
test_dem_src.WriteArray(dev, r'C:\code\ms-code-all\scratch\dev_{}.tif'.format(size))
#for deriv in ['slope', 'aspect', 'Roughness', 'TRI', 'TPI']:
#    print(deriv)
#    out_p = os.path.join('C:\code\ms-code-all\scratch', '{}.tif'.format(deriv))
#    print(out_p)
#    gdal_dem_derivative(test_dem_p, out_p, deriv)


## Slope
from scipy.ndimage.filters import maximum_filter, minimum_filter

test = np.array([[50,54,50],[30,30,30],[8, 10,10]])

test_max = maximum_filter(test, size=3, mode='nearest')
test_min = minimum_filter(test, size=3, mode='nearest')
test_det = test_max - test_min
np.gradient('')



