import osgeo.gdal as gdal
import xml.dom.minidom
import sys
import os

map_file = sys.argv[1]
dem_file = sys.argv[2]
output_file = 'DEM_converted_data_tmp.txt'
if len(sys.argv) == 4:
    output_file = sys.argv[3]

gdalData = gdal.Open(dem_file)
fout = open(output_file, 'w')

osm_map = xml.dom.minidom.parse(map_file)
bounds = osm_map.getElementsByTagName("bounds")[0]
minlat = float(bounds.getAttribute('minlat'))
maxlat = float(bounds.getAttribute('maxlat'))
minlon = float(bounds.getAttribute('minlon'))
maxlon = float(bounds.getAttribute('maxlon'))

start_lon = gdalData.GetGeoTransform()[0]
start_lat = gdalData.GetGeoTransform()[3]
delta_lon = gdalData.GetGeoTransform()[1]
delta_lat = gdalData.GetGeoTransform()[5]

def getLon(row):
    lon = (start_lon + row * delta_lon)
    return lon

def getLat(col):
    lat = (start_lat + col * delta_lat)
    return lat

xsize = gdalData.RasterXSize
ysize = gdalData.RasterYSize
raster = gdalData.ReadAsArray()

i = 0
while (getLon(i) < (minlon - abs(delta_lon))):
    i += 1
lon_min_index = i
i = 0
while (getLon(i) < (maxlon + abs(delta_lon))):
    i += 1
i -= 1
lon_max_index = i
i = 0
while (getLat(i) > (minlat - abs(delta_lat))):
    i += 1
i -= 1
lat_min_index = i
i = 0
while (getLat(i) > (maxlat + abs(delta_lat))):
    i += 1
lat_max_index = i

fout.write(str(lon_max_index-lon_min_index+1) + ' ' + str(lat_min_index-lat_max_index+1) + '\n')
fout.write(str(getLon(lon_min_index)) + ' ' + str(getLat(lat_max_index)) + '\n')
fout.write(str(delta_lon) + ' ' + str(delta_lat) + '\n')

not_empty = False
for row in range( ysize ):
    for col in range(xsize):
      if (getLon(row) >= (minlon - abs(delta_lon))) and (getLon(row) <= (maxlon + abs(delta_lon))) and (getLat(col) >= (minlat - abs(delta_lat))) and (getLat(col) <= (maxlat + abs(delta_lat))):
          not_empty = True
          fout.write(str(raster[row, col]) + ' ')
          #print 'Lon: ' + str(start_lon + row*delta_lon) + '; Lat: ' + str(start_lat + col * delta_lat) + '; Height: ' + str(raster[row,col] - height_delta)
    if not_empty:
        fout.write('\n')
    not_empty = False

fout.close()
print os.path.abspath(fout.name)