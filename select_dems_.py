# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 13:37:12 2019

@author: disbr007
Select DEMs from danco footprint that meet the following
parameters:
    -multispectral (maybe...)
    -have ICESAT translations
    -contain waterbodies
"""

import argparse
import geopandas as gpd
import numpy as np
import os
import time

from query_danco import query_footprint


## Outpaths
#dems_p = r'E:\disbr007\umn\ms_proj_2019jul05\data\shapefile\scene_dem.gdb\arctic_dem_scenes'
#out_path = r'E:\disbr007\umn\ms_proj_2019jul05\data\dems\banks\all_hs_sel\setsm_reg_sel_lewk_hs.shp'
#aoi_p = r'E:\disbr007\umn\ms_proj_2019jul05\data\shapefile\lewk_2019_hs.shp'
#dem_id = 'dem_id'
#dems_p = None
#scenes = False
#fgdb = False
#xtrack=False
#icesat=True
#ms=False


def select_setsm_dems(aoi_p, out_path, dem_id=None, dems_p=None, scenes=False, fgdb=False, icesat=True, ms=False, xtrack=False):
    '''
    Select dems from setsm danco footprint that intersect AOI
    and other optional parameters.
    aoi_p: path to aoi shapefile (or other OGR layer)
    out_path: path to write output selection
    dems_p: path to preselected dems
    fgdb: True if dems_p is a path to a feature class
    icesat: True to select only ICEsat registered DEMs
    ms: True to select only multispectral sourced DEMs
    xtrack: True to include cross-track
    
    '''
    def count_points(row_geom, points_geom):
        '''
        Count the number of points in each rows geometry
        '''
    #    points_geom = points.geometry.name
    #    row_geom = row.geometry.name
    #    pts_within = points[points_geom].within(row[row_geom])
    #    num_within = len(pts_within[pts_within==True])
    
        points_within = points_geom.within(row_geom)
        num_within = len(points_within[points_within==True])
    
    #    try:
    #        pts_within = points['geom'].within(row['geom'])
    #        num_within = len(pts_within[pts_within==True])
    #    except:
    #        print('err2')
    #        pass
    #    print('row:')
    #    print(type(row))
    #    time.sleep(2)
    #    print(row['geom'])
    #    print(row.geometry)
    #    print('points')
    #    print(type(points))
    #    print(points.geometry)
        return num_within
    
    
    print('Loading data...')
    ## Load AOI
    aoi = gpd.read_file(aoi_p)
    
    ## Load DEMs footprint (either strips or scenes)
    if dems_p:
        if scenes == True:
            dems_p = r'E:\disbr007\umn\ms_proj_2019jul05\data\shapefile\scene_dem.gdb\arctic_dem_scenes'
            fgdb = True
        
        if fgdb == False:
            dems = gpd.read_file(dems_p)
        
        elif fgdb == True:
            gdb_p = os.path.split(dems_p)[0]
            layer = os.path.split(dems_p)[1]
            dems = gpd.read_file(gdb_p, driver='OpenFileGDB', layer=layer)
    else:
        ## Parameter setup
        db = 'footprint'
        layer = 'pgc_dem_setsm_strips'
        ## Query danco for DEMs
        dems = query_footprint(layer=layer, db=db)
    
    sensors = ['IK01', 'GE01', 'QB01', 'WV02', 'WV03']
    ms_sensors = ['WV02', 'WV03'] # IK01 intentially left out (low-res)
    
    ## Determine intrack or xtrack
    dems['platform'] = dems['pairname'].str[0:4]
    dems['stereo_type'] = np.where(dems['platform'].isin(sensors), 'intrack', 'xtrack')
    
    print('Selecting...')
    ## Select based on criteria
    if not xtrack:
        ## Select only intrack
        dems = dems[dems['stereo_type']=='intrack']
    if icesat:
        ## Select only strips with ICESat registration
        if 'reg_src' not in list(dems):
            # Load strips footprint, find pairnames with reg
            strip_dems = query_footprint('pgc_dem_setsm_strips', 'footprint')
            has_reg = set(list(strip_dems[strip_dems['reg_src']=='ICESat']['pairname']))
            dems = dems[dems['pairname'].isin(has_reg)]
            del strip_dems
        else:
            dems = dems[dems['reg_src'] == 'ICESat']
    if ms:
        dems = dems[dems['platform'].isin(ms_sensors)]
    
    print('Counting number of points in each DEM...')
    if aoi.crs != dems.crs:
        dems = dems.to_crs(aoi.crs)
    
    ## Count number points in each DEM
    dems = gpd.sjoin(dems, aoi, how='inner')
    dems.drop_duplicates(subset=dem_id, inplace=True)
    dems.drop(columns=['index_right', 'index_right'], inplace=True)
    
    ## Get count
    dems = dems[dems.geometry.is_valid == True]
    #print(list(dems))
    #print(list(aoi))
    dems['pts_count'] = dems.geometry.apply(lambda row: count_points(row, aoi.geometry))
    
    dems.drop_duplicates(subset=dem_id, inplace=True)
    
    ## Write out
    print('Writing shapefile to: {}'.format(out_path))
    dems.to_file(out_path, driver='ESRI Shapefile')

    
#select_setsm_dems(aoi_p, out_path, 'dem_id', dems_p=None, fgdb=True)
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('aoi', type=str, help='Shapefile to select DEMs by.')
    parser.add_argument('out_path', type=os.path.abspath, help='Path to create shapefile.')
    parser.add_argument('dem_id', type=str, 
                        help='Field containing unique IDs in DEM footprint. E.g. "dem_id", "scene_id"')
    parser.add_argument('--scenes', action='store_true', default=False,
                        help='''Flag to indicate selection at scene level. Uses a local
                        copy of the scenes DB as danco version is in wrong projection.''')
    parser.add_argument('--dems_path', type=str, default=None,
                        help='Path to prexisting DEM selection. If not, danco setsm footprint will be used.')
    parser.add_argument('--fgdb', action='store_true', help='Flag to use if dems_path is feature class in fgdb.')
    parser.add_argument('--icesat', action='store_true', help='Flag to select only DEMs with registration.')
    parser.add_argument('--ms', action='store_true', help='Flag to only select multispectral sourced DEMs.')
    parser.add_argument('--xtrack', action='store_true', help='Flag to include cross-track. Left out by default.')
    
    args = parser.parse_args()
    
    aoi = args.aoi
    out_path = args.out_path
    dem_id = args.dem_id
    scenes = args.scenes
    dems_path = args.dems_path
    fgdb = args.fgdb
    icesat = args.icesat
    ms = args.ms
    xtrack = args.xtrack

    print(
        'aoi: {}'.format(aoi),
        'out_path: {}'.format(out_path),
        'dem_id: {}'.format(dem_id),
        )

    select_setsm_dems(aoi, out_path, dem_id, dems_path, scenes, fgdb, icesat, ms, xtrack)

        