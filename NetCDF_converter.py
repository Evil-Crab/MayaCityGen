from netCDF4 import Dataset
import xml.dom.minidom
import math
import sys
import os

def coordinates_dist(long1, lat1, long2, lat2):
    rad = 6372795

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    long1 = math.radians(long1)
    long2 = math.radians(long2)

    cl1 = math.cos(lat1)
    cl2 = math.cos(lat2)
    sl1 = math.sin(lat1)
    sl2 = math.sin(lat2)
    delta = long2 - long1
    cdelta = math.cos(delta)
    sdelta = math.sin(delta)

    y = math.sqrt(math.pow(cl2*sdelta, 2)+math.pow(cl1*sl2-sl1*cl2*cdelta, 2))
    x = sl1*sl2+cl1*cl2*cdelta
    ad = math.atan2(y, x)
    dist = ad*rad

    return dist

map_file = sys.argv[1]
wrf_file = sys.argv[2]
output_file = 'WRF_converted_data_tmp.txt'
if len(sys.argv) == 4:
    output_file = sys.argv[3]

wrf = Dataset(wrf_file, 'r')
fout = open(output_file, 'w')

osm_map = xml.dom.minidom.parse(map_file)
bounds = osm_map.getElementsByTagName("bounds")[0]
minlat = float(bounds.getAttribute('minlat'))
maxlat = float(bounds.getAttribute('maxlat'))
minlon = float(bounds.getAttribute('minlon'))
maxlon = float(bounds.getAttribute('maxlon'))

long = wrf.variables['XLONG'][0]
lat = wrf.variables['XLAT'][0]

w_stag = wrf.variables['W'][0]
u_stag = wrf.variables['U'][0][0]
v_stag = wrf.variables['V'][0][0]

stag_w = len(w_stag)
stag_u = len(u_stag[0])
stag_v = len(v_stag)

w = [[0 for i in range(stag_u-1)] for i in range(stag_v-1)]
for i in range(stag_v-1):
    for j in range(stag_u-1):
        w[i][j] = (w_stag[0][i][j] + w_stag[1][i][j])/2

u = [[0 for i in range(stag_u-1)] for i in range(stag_v-1)]
for i in range(stag_v-1):
    for j in range(stag_u-1):
        u[i][j] = (u_stag[i][j] + u_stag[i][j+1])/2

v = [[0 for i in range(stag_u-1)] for i in range(stag_v-1)]
for i in range(stag_v-1):
    for j in range(stag_u-1):
        v[i][j] = (v_stag[i][j] + v_stag[i+1][j])/2

min_i = 0
min_j = 0
min_dist = 1000000
empty = True
for i in range(len(long)):
    for j in range(len(long[0])):
        if min_dist > coordinates_dist((maxlon+minlon)/2, (maxlat+minlat)/2, long[i][j], lat[i][j]):
            min_dist = coordinates_dist((maxlon+minlon)/2, (maxlat+minlat)/2, long[i][j], lat[i][j])
            min_i = i
            min_j = j

        if (long[i][j] <= maxlon) and (long[i][j] >= minlon) and (lat[i][j] <= maxlat) and (lat[i][j] >= minlat):

            fout.write(str(long[i][j]) + ' ' + str(lat[i][j]) + ' ' + str(u[i][j]) + ' ' + str(w[i][j]) + ' ' + str(-v[i][j]) + '\n')
            empty = False

if empty:
    fout.write(str(long[min_i][min_j]) + ' ' + str(lat[min_i][min_j]) + ' ' + str(u[min_i][min_j]) + ' ' + str(w[min_i][min_j]) + ' ' + str(-v[min_i][min_j]) + '\n')

wrf.close()
fout.close()
print os.path.abspath(fout.name)