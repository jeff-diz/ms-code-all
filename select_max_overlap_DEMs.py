# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 14:30:33 2019

@author: disbr007
Selects the DEMs with the most overlap to consider for pair-wise
coregistration. 

"""

import argparse
import geopandas as gpd
import numpy as np
from osgeo import gdal
import os
import pandas as pd

from id_parse_utils import write_ids


## Preselected DEM footprint
#dems_p = r'E:\disbr007\umn\ms_proj_2019jul05\data\dems\banks\all_hs_sel\setsm_reg_sel_lewk_hs.shp'
#out_dir = r'E:\disbr007\umn\ms_proj_2019jul05\data\dems\banks\all_hs_sel'
#
### Number pairs to keep
#n = 50


def select_max_ovlp(dems_p, out_dir, dem_id, n):
    '''
    Select n DEM footprint pairs with the highest percent overlap
    dems_p: path to footprint of dems
    out_dir: directory to write '_pairs.shp' and '_paths.shp' to
    n: number of dems to keep
    '''
    
    def create_pair_id(row):
        both_ids = [row['{}_1'.format(dem_id)], row['{}_2'.format(dem_id)]]
        both_ids.sort()
        pair_id = '__'.join(both_ids)
        return pair_id
    
    ## Out names
    out_basename = os.path.basename(dems_p).split('.')[0]
    out_pairs = os.path.join(out_dir, '{}_pairs.shp'.format(out_basename))
    out_paths = os.path.join(out_dir, '{}_paths.shp'.format(out_basename))
    out_filepath = os.path.join(out_dir, 'filepath_pairs.txt'.format(out_basename))
    out_win_path = os.path.join(out_dir, 'win_path_pairs.txt'.format(out_basename))
    
    ## Load DEMs footprint
    dems = gpd.read_file(dems_p)
    dems['area'] = dems.geometry.area
    og_cols = list(dems)
    og_cols.sort() # Not nec.? later list comp will always be same order?
    og_cols.remove('geometry')
    og_geoms = dems[[dem_id, 'geometry']]
    
    ## Intersections of all polygons in dems to each other
    isect = gpd.overlay(dems, dems)
    
    ## Remove self intersections
    isect = isect[isect['{}_1'.format(dem_id)]!= isect['{}_2'.format(dem_id)]]
    
    ## Remove flipped pair duplicates (dem2-dem1 is a DUP of dem1-dem2)
    isect['pair_id'] = isect.apply(lambda x: create_pair_id(x), axis=1)
    isect.drop_duplicates(subset='pair_id', inplace=True)
    
    ## Create name for output folder
    ## Use this df to reorganize by pairs
    isect['dir_name'] = isect['{}_1'.format(dem_id)].str.slice(0,13) + '-' + isect['{}_2'.format(dem_id)].str.slice(0,13)
    
    
    ## Calculate overlap percent for left and right polygons of intersection
    isect['ovlp_perc_1'] = (isect.geometry.area / isect['area_1']).round(decimals=2)*100
    isect['ovlp_perc_2'] = (isect.geometry.area / isect['area_2']).round(decimals=2)*100
    # Take average ovlp to get an idea of how much of each will be worked on
    isect['ovlp_perc'] = ((isect['ovlp_perc_1'] + isect['ovlp_perc_2']) / 2)
    ## Get average of number of points in each polygon
    isect['mean_count'] = ((isect['pts_count_1'] + isect['pts_count_2']) / 2)
    
    ## Select top n records
#    isect = isect[isect['mean_count']>10]
    isect.sort_values(by='ovlp_perc', ascending=False, inplace=True)
    isect = isect[0:n]
    
    ## Select pair names
    isect['filepath_1_full'] = isect['filepath_1'] + r'/' + isect['dem_name_1']
    isect['filepath_2_full'] = isect['filepath_2'] + r'/' + isect['dem_name_2']

    isect['win_path_1_full'] = isect['win_path_1'] + r'\\' + isect['dem_name_1']
    isect['win_path_2_full'] = isect['win_path_2'] + r'\\' + isect['dem_name_2']

    pairs_filepath= list(zip(list(isect['filepath_1_full']), list(isect['filepath_2_full'])))
#    pairs_filepath= list(zip(list(isect['dem_name_1']), list(isect['dem_name_2']))) # scenes path
    pairs_win_path = list(zip(list(isect['win_path_1_full']), list(isect['win_path_2_full'])))
    
    ## Write paths out to text file
    with open(out_filepath, 'w') as f:
        for each_pair in pairs_filepath:
            for each_id in each_pair:
    #            print(each_id)
                f.write('{}, '.format(each_id))
            f.write('\n')
            
    with open(out_win_path, 'w') as f:
        for each_pair in pairs_win_path:
            for each_id in each_pair:
                f.write('{}, '.format(each_id))
            f.write('\n')
    
    ## Create shapefile to pass to copy_dems.py
    ## One dem_id per line with win_path and 
    # Store left dem columns
    left_dt = {}
    left_cols = [c+'_1' for c in og_cols]
    left_cols.append('ovlp_perc')
    left_rn = dict(zip(left_cols, og_cols))
    # Store right dem columns
    right_dt = {}
    right_cols = [c+'_2' for c in og_cols]
    right_cols.append('ovlp_perc')
    right_rn = dict(zip(right_cols, og_cols))
    
    ## Loop intersections
    for i, row in isect.iterrows():
        ## Pull out left columns of row, add to dict
        left = row[left_cols]
        left.rename(left_rn, inplace=True)
        left_dt[left[dem_id]] = left
        ## Pull out right columns of row, add to dict
        right = row[right_cols]
        right.rename(right_rn, inplace=True)
        right_dt[right[dem_id]] = right
        
    ## Create two dataframes
    left_df = pd.DataFrame.from_dict(left_dt, orient='index')
    right_df = pd.DataFrame.from_dict(right_dt, orient='index')
    ## Stack dataframes
    out_df = pd.concat([left_df, right_df])
    ## Find original geometry based on dem_id field
    out_df = out_df.merge(og_geoms)
    out_df = gpd.GeoDataFrame(out_df, geometry='geometry')
    ## Drop duplicates ...why are there?
    out_df.drop_duplicates(subset=dem_id, keep='first', inplace=True)
    
    ## Write out shape to use for copy_dems.py and to use for organizing pairs
    out_df.to_file(out_paths)
    isect.to_file(out_pairs)


#select_max_ovlp(dems_p, out_dir, n)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('dem_footprint', type=str,
                        help='Path to dem footprint selection.')
    parser.add_argument('out_dir', type=str,
                        help='Directory to write pairs and selection footprints to.')
    parser.add_argument('dem_id', type=str,
                        help='Field to identify unique DEMs. E.g. "dem_id", or "scene_id".')
    parser.add_argument('keep_num', type=int,
                        help='Number of PAIRS to keep.')
    
    args = parser.parse_args()
    
    dem_footprint = args.dem_footprint
    dem_id = args.dem_id
    keep_num = args.keep_num
    out_dir = args.out_dir
    
    select_max_ovlp(dem_footprint, out_dir, dem_id, keep_num)
