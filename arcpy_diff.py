# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 13:28:15 2019

@author: disbr007
"""

import argparse
import os
import logging

import arcpy
from arcpy.sa import *


def order_by_date(dems):
    dems.sort(key=lambda x: os.path.split(x)[1][5:12])
    return dems

def main(src_dir):
    arcpy.env.overwriteOutput = True
    for p in os.listdir(src_dir):
    #src_dir = pair_dir
        pair_dir = os.path.join(src_dir, p)
        print(pair_dir)
        files = os.listdir(pair_dir)
        suffix = ('dem.tif', 'DEM.tif', 'trans.tif', 'dem_reg.tif', )
        dems = [os.path.join(pair_dir, x) for x in files if x.endswith(suffix)]
        if len(dems) == 2:
            dems = order_by_date(dems)
            
            print('Computing difference...')
            diff = Raster(dems[1]) - Raster(dems[0])
            
            # Pair name - used for output
            pair_name = os.path.split(os.path.split(pair_dir)[0])[1]
            op = os.path.join(pair_dir, '{}_{}_diff.tif'.format(pair_name, os.path.split(pair_dir)[1]))
            print('Writing difference: {}'.format(op))
            diff.save(op)
            
        #    arcpy.BuildPyramidsandStatistics_management(pair_dir)
        else:
            print('Incorrect number of DEMs found: {}'.format(len(dems)))


#main(pair_dir)
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src_dir',type=os.path.abspath,
                        help='Directory holding subdirs of pairs to difference')
    args = parser.parse_args()
    main(args.src_dir)
    
    
    