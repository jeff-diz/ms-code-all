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
    Take an input DEM and create a derivative product
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
    """
    OpenCV implementation of TPI
    dem: array
    size: int, kernel size in x and y directions (square kernel)
    Note - borderType determines handline of edge cases. REPLICATE will take the outermost row and columns and extend
    them as far as is needed for the given kernel size.
    """
    kernel = np.ones((size,size),np.float32)/(size*size)
    # -1 indicates new output array
    dem_conv = cv2.filter2D(dem, -1, kernel, borderType=cv2.BORDER_REPLICATE)
    tpi = dem - dem_conv

    return tpi


def calc_tpi_dev(dem, size):
    """
    Based on (De Reu 2013)
    Calculates the tpi/standard deviation of the kernel to account for surface roughness.
    dem: array
    size: int, kernel size in x and y directions (square kernel)
    """
    tpi = calc_tpi(dem, size)
    # Calculate the standard deviation of each cell, mode='nearest' == cv2.BORDER_REPLICATE
    std_array = generic_filter(dem, np.std, size=size, mode='nearest')

    tpi_dev = tpi / std_array

    return tpi_dev
