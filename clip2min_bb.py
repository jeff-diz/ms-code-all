# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 14:44:41 2019

@author: disbr007
Takes paths to DEMs, or a directory containing DEMs and applies gdal_translate
to clip to given shapefile's extent, rounded to the nearest whole coordinate.
"""

from osgeo import ogr, gdal, osr
import os, logging, argparse


## Set up logging and exceptions
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
gdal.UseExceptions()

## Directory containing dems
#dems_dir = r'V:\pgc\data\scratch\jeff\ms_proj_2019jul05\dems\raw\raw'


def matching_files(directory, suffix):
    '''
    Takes a directory and finds all files matching the given suffix.
    '''
    ## Get all files in directory that match the suffix
    matching_paths = []
    for file in os.listdir(directory):
        if file.endswith(suffix):
            matching_paths.append(os.path.join(directory, file))
    return matching_paths

    
def parse_src(src, suffix):
    '''
    Takes a (potentially) mixed list of directories files and returns a 
    list of files in the directories matching the specified suffix and 
    any files explicitly provided
    src: list of paths, can be directories and/or paths
    '''
    ## List to store all paths
    file_paths = []
    ## Loop over input, determining if directory or file
    for item in src:
        # if directory, parse it and add each file
        if os.path.isdir(item):
            for f in matching_files(item, suffix):
                file_paths.append(f)
        ## if file, check suffix, then add it
        elif os.path.isfile(item):
            if item.endswith(suffix):
                file_paths.append(item)
    logging.info('file_paths: {}'.format(file_paths))
    return file_paths


def raster_bounds(path):
    '''
    GDAL only version of getting bounds for a single raster.
    '''
    src = gdal.Open(path)
    gt = src.GetGeoTransform()
    ulx = gt[0]
    uly = gt[3]
    lrx = ulx + (gt[1] * src.RasterXSize)
    lry = uly + (gt[5] * src.RasterYSize)
    
    return ulx, lry, lrx, uly

    
def minimum_bounding_box(rasters):
    '''
    Takes a list of DEMs (or rasters) and returns the minimum bounding box of all in
    the order of bounds specified for gdal.Translate.
    dems: list of dems
    '''
    ## Determine minimum bounding box
    ulxs, lrys, lrxs, ulys = list(), list(), list(), list()
    #geoms = list()
    for raster_p in rasters:
        ulx, lry, lrx, uly = raster_bounds(raster_p)
    #    geom_pts = [(ulx, lry), (lrx, lry), (lrx, uly), (ulx, uly)]
    #    geom = Polygon(geom_pts)
    #    geoms.append(geom)
        ulxs.append(ulx)
        lrys.append(lry)
        lrxs.append(lrx)
        ulys.append(uly)        
    
    ## Find the smallest extent of all bounding box corners
    ulx = max(ulxs)
    uly = min(ulys)
    lrx = min(lrxs)
    lry = max(lrys)

    projWin = [ulx, uly, lrx, lry]

    return projWin


def translate_rasters(rasters, projWin, out_dir, out_suffix='_trans'):
    '''
    Takes a list of rasters and translates (clips) them to the minimum bounding box
    '''
    ## Translate (clip) to minimum bounding box
    translated = {}
    for raster_p in rasters:
        if not out_dir:
            out_dir == os.path.dirname(raster_p)
        logging.info('Translating {}...'.format(raster_p))
        raster_out_name = '{}_{}.tif'.format(os.path.basename(raster_p).split('.')[0], out_suffix)
        raster_op = os.path.join(out_dir, raster_out_name)
        
        raster_ds = gdal.Open(raster_p)
        translated[raster_out_name] = gdal.Translate(raster_op, raster_ds, projWin=projWin)
    
    return translated


def clip2min_bb(src, out_dir, suffix=('.tif'), out_suffix='_trans'):
    '''
    Wrapper function to clip a number of rasters to a the minimum bounding box of all.
    src: list of raster paths and/or directories
    out_dir: directory to write clipped rasters to, can use /vsiem/ to only save to 
             memory
    suffix: common suffix among rasters, can supply multiple as tuple
    out_suffix: suffix to append to output rasters.
    '''
    ## Get paths of rasters in src
    file_paths = parse_src([src], suffix=suffix)
    ## Get min bounding box of rasters
    projWin = minimum_bounding_box(file_paths)
    ## Translate rasters, returns dict of filepath: translated_raster
    translated = translate_rasters(file_paths, projWin, out_dir, out_suffix=out_suffix)

    return translated
    

def write_min_bb(projWin, out_dir, dems):
    '''
    Takes a projWin and writes a shapefile of it. If no out_dir has been supplied
    write the shapefile to the directory of the first DEM provided.'
    projWin: ulx, uly, lrx, lry
    '''
    ## Write path specification
    if not out_dir:
        out_dir = os.path.dirname(dems[0])
    out_path = os.path.join(out_dir, 'minimum_bb.shp')
    
    ## Get projection information from the first DEM provided
    dem_ds = gdal.Open(dems[0])
    prj = dem_ds.GetProjection()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(prj)
        
    ## OGR Polygon
    ulx, uly, lrx, lry = projWin
    
    out_driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(out_path):
        out_driver.DeleteDataSource(out_path)

    out_data_source = out_driver.CreateDataSource(out_path)
    out_layer = out_data_source.CreateLayer(out_path, geom_type=ogr.wkbPolygon, srs=srs)
    
    feature_defn = out_layer.GetLayerDefn()
    feature = ogr.Feature(feature_defn)
    
    # Geometry building
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(ulx, lry)
    ring.AddPoint(lrx, lry)
    ring.AddPoint(lrx, uly)
    ring.AddPoint(ulx, uly)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    feature.SetGeometry(poly)
    out_layer.CreateFeature(feature)
    
    # Save feature and data source
    feature = None
    out_data_source = None    
#    min_bb = Polygon([(ulx, lry), (lrx, lry), (lrx, uly), (ulx, uly)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', nargs="+", type=str,
                        help="Directory to rasters or paths individual rasters.")
    parser.add_argument('-s', '--suffix', nargs='?', default='.tif', type=str,
                        help="Suffix that all rasters share.")
    parser.add_argument('-w', '--write_shp', action='store_true',
                        help="Optional flag to write shape")
    parser.add_argument('-o', '--out_dir', type=str,
                        help='''Directory to write translated rasters to. Defaults to current
                        directory for each raster provided. Alternatively, can supply
                        /vsimem/ to not save rasters anywhere (in case of just wanting
                        shapefile of minimum bounding box.)''')
    
    args = parser.parse_args()
    
    src = [os.path.abspath(s) for s in args.src]
    suffix = args.suffix
    write_shp = args.write_shp
    out_dir = args.out_dir
    
    rasters = parse_src(src, suffix)
    projWin = minimum_bounding_box(rasters)
    translate_rasters(rasters, projWin, out_dir=out_dir)

    if write_shp == True:
        write_min_bb(projWin, out_dir, rasters)
        


## DEBUG PLOTTING
#edgecolors = ['r' for x in range(len(geoms))]
#geoms.append(min_bb)
#edgecolors.append('b')
#
#gdf = gpd.GeoDataFrame({'geometry': geoms, 'ID':[x for x in range(len(geoms))],'edgecolor': edgecolors})
#fig, ax = plt.subplots()
#gdf.plot(column='ID', color='', edgecolor=gdf['edgecolor'], ax=ax)
#
#ul = Point(ulx, uly)
#lr = Point(lrx, lry)
#pts = gpd.GeoDataFrame(geometry=[ul, lr])
#pts.plot(ax=ax)
    
    
