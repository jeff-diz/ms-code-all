# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 14:14:40 2019

@author: disbr007
"""

import argparse
from osgeo import gdal
import os
import re
from tqdm import tqdm


gdal.UseExceptions()

# working_dir = r'E:\disbr007\umn\ms_proj_2019jul05\data\dems\banks\raw_dems'
# ext = 'tif'

def create_ovr(tif):
    ds = gdal.Open(tif, 0)
    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
    ds.BuildOverviews("NEAREST" , [2,4,6,8,16,32,64])
    del ds
    

def batch_compute_stats(working_dir, ext, regex, force_stats, force_ovr):
    
    matches = []
    for root, dirs, files in os.walk(working_dir):
        for f in files:
            if f.endswith(ext):
                matches.append(os.path.join(root, f))
                
    if regex:
        reg = re.compile(regex)            
        matches = [each for each in matches if reg.search(each)]

    for m in tqdm(matches):
        print(m)
        ovr = m + '.ovr'
        aux_xml = m + '.aux.xml'
        
        if not os.path.exists(aux_xml):
            tqdm.write('Calculating statistics...')
            gdal.Info(m, stats=True)
        else:
            if force_stats:
                tqdm.write('Recalculating statistics...')
                gdal.Info(m, stats=True)
            else:
                tqdm.write('Statistics exist.')
            

        if not os.path.exists(ovr):
            tqdm.write('Creating overviews...')
            create_ovr(m)
        else:
            if force_ovr:
                tqdm.write('Recreating overviews...')
                create_ovr(m)
            else:
                tqdm.write('Overview exists.')


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('dir', type=str, help='Directory to scan.')
    parser.add_argument('--ext', type=str, default='tif',
                        help='Extension to calculate_stats on.')
    parser.add_argument('--regex', type=str, default=None, 
                        help='Pattern to search in file names.')
    parser.add_argument('--force_stats', action='store_true',
                        help='Force recalculation of statistics even if .aux.xml file present.')
    parser.add_argument('--force_ovr', action='store_true',
                        help='Force recomputation of overviews, even if .ovr file present.')
    
    args = parser.parse_args()
    working_dir = args.dir
    ext = args.ext
    regex = args.regex
    force_stats = args.force_stats
    force_ovr = args.force_ovr
    
    batch_compute_stats(args.dir, args.ext, args.regex, force_stats, force_ovr)