from __future__ import division
import maya.cmds as cmds
import maya.mel as mel
import math
import os
import subprocess
import platform
import xml.dom.minidom
import urllib2

class CityGenerator():

    def __init__(self):

        self.widgets = {}
        try:
          mel.eval('mrRenderLayerPresetMenu "AOLayer";')
          if not cmds.objExists('AOLayer'):
              cmds.createRenderLayer(name='AOLayer', num=2)
              mel.eval("mrRenderLayerBuiltinPreset occlusion AOLayer;")
              cmds.editRenderLayerGlobals(currentRenderLayer='AOLayer')
              cmds.setAttr('mib_amb_occlusion1.samples', 64)
        except RuntimeError:
          print "mrRenderLayerPresetMenu already initializied"

        self.buildUI()

    def buildUI(self):

        if cmds.dockControl("cityGenerator_dockControl", exists = True):
            cmds.deleteUI("cityGenerator_dockControl")

        if cmds.window("cityGenerator_UI", exists = True):
            cmds.deleteUI("cityGenerator_UI")

        self.widgets["window"] = cmds.window("cityGenerator_UI", title = "City Generator", mnb = False, mxb = False)
        self.widgets["scrollLayout"] = cmds.scrollLayout(hst = 0, w = 300, cr = True)
        self.widgets["mainLayout"] = cmds.columnLayout(adj = True, columnAttach=('both', 0))
        self.widgets["menuBarLayout"] = cmds.menuBarLayout()

        cmds.menu(label='Help' )
        cmds.menuItem(label='Help')
        cmds.menuItem(label='About')

        #==========================================Input Files========================================================
        self.widgets["inputFiles_frameLayout"] = cmds.frameLayout(label = "Input Files", collapsable = True, parent = self.widgets["mainLayout"])
        self.widgets["inputFiles_formLayout"] = cmds.formLayout(h = 130, parent = self.widgets["inputFiles_frameLayout"])

        self.widgets["osmFileLabel"] = cmds.text(w = 45, h= 20, label = "OSM File")
        self.widgets["wrfFileLabel"] = cmds.text(w = 45, h= 20, label = "WRF File")
        self.widgets["demFileLabel"] = cmds.text(w = 45, h= 20, label = "DEM File")
        self.widgets["osmFileTextField"] = cmds.textField(w = 180, h= 20, text = "")
        self.widgets["wrfFileTextField"] = cmds.textField(w = 180, h= 20, text = "")
        self.widgets["demFileTextField"] = cmds.textField(w = 180, h= 20, text = "")
        self.widgets["wrfCheckBox"] = cmds.checkBox(label = "Raw WRF input")
        self.widgets["demCheckBox"] = cmds.checkBox(label = "Raw DEM input")
        self.widgets["osmFileButton"] = cmds.button(w = 20, h= 20, label = "...", c = lambda x:self.openFileDialog("OSM XML (*.osm)", 1, "osmFileTextField"))
        self.widgets["wrfFileButton"] = cmds.button(w = 20, h= 20, label = "...", c = lambda x:self.openFileDialog("Raw WRF Data (*.nc)" if cmds.checkBox(self.widgets["wrfCheckBox"], q=True, v=True) else "Preprocessed WRF Data (*.txt)", 1, "wrfFileTextField"))
        self.widgets["demFileButton"] = cmds.button(w = 20, h= 20, label = "...", c = lambda x:self.openFileDialog("Raw DEM Data (*.tif)" if cmds.checkBox(self.widgets["demCheckBox"], q=True, v=True) else "Preprocessed DEM Data (*.txt)", 1, "demFileTextField"))

        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["osmFileLabel"], 'top', 5),(self.widgets["osmFileLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["osmFileTextField"], 'top', 5),(self.widgets["osmFileTextField"], 'left', 50)])
        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["osmFileButton"], 'top', 5),(self.widgets["osmFileButton"], 'left', 235)])

        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["wrfFileLabel"], 'top', 30),(self.widgets["wrfFileLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["wrfFileTextField"], 'top', 30),(self.widgets["wrfFileTextField"], 'left', 50)])
        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["wrfFileButton"], 'top', 30),(self.widgets["wrfFileButton"], 'left', 235)])

        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["wrfCheckBox"], 'top', 55),(self.widgets["wrfCheckBox"], 'left', 10)])

        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["demFileLabel"], 'top', 80),(self.widgets["demFileLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["demFileTextField"], 'top', 80),(self.widgets["demFileTextField"], 'left', 50)])
        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["demFileButton"], 'top', 80),(self.widgets["demFileButton"], 'left', 235)])

        cmds.formLayout(self.widgets["inputFiles_formLayout"], edit = True, af = [(self.widgets["demCheckBox"], 'top', 105),(self.widgets["demCheckBox"], 'left', 10)])

        #==========================================Generator Settings=================================================
        self.widgets["generatorSettings_frameLayout"] = cmds.frameLayout(label = "Generator Settings", collapsable = True, collapse = True, parent = self.widgets["mainLayout"])
        self.widgets["generatorSettings_formLayout"] = cmds.formLayout(h = 130, parent = self.widgets["generatorSettings_frameLayout"])

        self.widgets["sizeMultLabel"] = cmds.text(w = 135, h= 20, label = "Size Multiplier (m/mdu)")
        self.widgets["sizeMultTextField"] = cmds.textField(w = 50, h= 20, text = "100")

        self.widgets["emitMultLabel"] = cmds.text(w = 135, h= 20, label = "Emitter Multiplier")
        self.widgets["emitMultTextField"] = cmds.textField(w = 50, h= 20, text = "10")

        self.widgets["haslLabel"] = cmds.text(w = 135, h= 20, label = "Height above sea level (m)")
        self.widgets["haslTextField"] = cmds.textField(w = 50, h= 20, text = "190")

        self.widgets["generateButton"] = cmds.button(w = 250, h= 40, label = "Generate City", c = self.generateCity)

        cmds.formLayout(self.widgets["generatorSettings_formLayout"], edit = True, af = [(self.widgets["sizeMultLabel"], 'top', 5),(self.widgets["sizeMultLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["generatorSettings_formLayout"], edit = True, af = [(self.widgets["sizeMultTextField"], 'top', 5),(self.widgets["sizeMultTextField"], 'left', 140)])

        cmds.formLayout(self.widgets["generatorSettings_formLayout"], edit = True, af = [(self.widgets["haslLabel"], 'top', 30),(self.widgets["haslLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["generatorSettings_formLayout"], edit = True, af = [(self.widgets["haslTextField"], 'top', 30),(self.widgets["haslTextField"], 'left', 140)])

        cmds.formLayout(self.widgets["generatorSettings_formLayout"], edit = True, af = [(self.widgets["emitMultLabel"], 'top', 55),(self.widgets["emitMultLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["generatorSettings_formLayout"], edit = True, af = [(self.widgets["emitMultTextField"], 'top', 55),(self.widgets["emitMultTextField"], 'left', 140)])

        cmds.formLayout(self.widgets["generatorSettings_formLayout"], edit = True, af = [(self.widgets["generateButton"], 'top', 80),(self.widgets["generateButton"], 'left', 20)])

        #==========================================Render Settings=====================================================
        self.widgets["renderSettings_frameLayout"] = cmds.frameLayout(label = "Render Settings", collapsable = True, collapse = True, parent = self.widgets["mainLayout"])
        self.widgets["renderSettings_formLayout"] = cmds.formLayout(h = 210, parent = self.widgets["renderSettings_frameLayout"])

        self.widgets["cameraDistLabel"] = cmds.text(w = 125, h= 20, label = "Camera distance (m)")
        self.widgets["cameraDistTextField"] = cmds.textField(w = 50, h= 20, text = "100")

        self.widgets["cameraHeightLabel"] = cmds.text(w = 125, h= 20, label = "Camera height (m)")
        self.widgets["cameraHeightTextField"] = cmds.textField(w = 50, h= 20, text = "200")

        self.widgets["cameraAngleLabel"] = cmds.text(w = 125, h= 20, label = "Camera angle (grad)")
        self.widgets["cameraAngleTextField"] = cmds.textField(w = 50, h= 20, text = "25")

        self.widgets["playbackTimeLabel"] = cmds.text(w = 125, h= 20, label = "Playback time (frames)")
        self.widgets["playbackTimeTextField"] = cmds.textField(w = 50, h= 20, text = "720")

        self.widgets["createCameraButton"] = cmds.button(w = 250, h= 40, label = "Create Camera", c = self.createCamera)

        self.widgets["pauseRenderButton"] = cmds.button(w = 120, h= 40, label = "Pause render", c = self.pauseRender)
        self.widgets["resumeRenderButton"] = cmds.button(w = 120, h= 40, label = "Resume render", c = self.resumeRender)

        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["cameraDistLabel"], 'top', 5),(self.widgets["cameraDistLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["cameraDistTextField"], 'top', 5),(self.widgets["cameraDistTextField"], 'left', 130)])

        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["cameraHeightLabel"], 'top', 30),(self.widgets["cameraHeightLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["cameraHeightTextField"], 'top', 30),(self.widgets["cameraHeightTextField"], 'left', 130)])

        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["cameraAngleLabel"], 'top', 55),(self.widgets["cameraAngleLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["cameraAngleTextField"], 'top', 55),(self.widgets["cameraAngleTextField"], 'left', 130)])

        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["playbackTimeLabel"], 'top', 80),(self.widgets["playbackTimeLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["playbackTimeTextField"], 'top', 80),(self.widgets["playbackTimeTextField"], 'left', 130)])

        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["createCameraButton"], 'top', 110),(self.widgets["createCameraButton"], 'left', 20)])

        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["pauseRenderButton"], 'top', 160),(self.widgets["pauseRenderButton"], 'left', 20)])
        cmds.formLayout(self.widgets["renderSettings_formLayout"], edit = True, af = [(self.widgets["resumeRenderButton"], 'top', 160),(self.widgets["resumeRenderButton"], 'left', 150)])

        #===========================================Yandex Jams=======================================================
        self.widgets["yandexJams_frameLayout"] = cmds.frameLayout(label = "Yandex Jams", collapsable = True, collapse = True, parent = self.widgets["mainLayout"])
        self.widgets["yandexJams_formLayout"] = cmds.formLayout(h = 30, parent = self.widgets["yandexJams_frameLayout"])

        self.widgets["jamsFileLabel"] = cmds.text(w = 45, h= 20, label = "Jams File")
        self.widgets["jamsFileTextField"] = cmds.textField(w = 180, h= 20, text = "")
        self.widgets["jamsFileButton"] = cmds.button(w = 20, h= 20, label = "...", c = lambda x:self.openFileDialog("Traffic Data (*.dat)", 1, "jamsFileTextField"))

        cmds.formLayout(self.widgets["yandexJams_formLayout"], edit = True, af = [(self.widgets["jamsFileLabel"], 'top', 5),(self.widgets["jamsFileLabel"], 'left', 0)])
        cmds.formLayout(self.widgets["yandexJams_formLayout"], edit = True, af = [(self.widgets["jamsFileTextField"], 'top', 5),(self.widgets["jamsFileTextField"], 'left', 50)])
        cmds.formLayout(self.widgets["yandexJams_formLayout"], edit = True, af = [(self.widgets["jamsFileButton"], 'top', 5),(self.widgets["jamsFileButton"], 'left', 235)])

        #===========================================OSM========================================================================
        self.widgets["osm_frameLayout"] = cmds.frameLayout(label = "Open Street Map", collapsable = True, collapse = True, parent = self.widgets["mainLayout"])
        self.widgets["osm_formLayout"] = cmds.formLayout(h = 160, parent = self.widgets["osm_frameLayout"])

        self.widgets["osmTopTextField"] = cmds.textField(w = 70, h= 30, text = "55.7858")
        self.widgets["osmBotTextField"] = cmds.textField(w = 70, h= 30, text = "55.7771")
        self.widgets["osmLeftTextField"] = cmds.textField(w = 70, h= 30, text = "37.7178")
        self.widgets["osmRightTextField"] = cmds.textField(w = 70, h= 30, text = "37.7356")

        self.widgets["osmImportButton"] = cmds.button(w = 80, h= 40, label = "Import", c = self.downloadOSM)

        cmds.formLayout(self.widgets["osm_formLayout"], edit = True, af = [(self.widgets["osmTopTextField"], 'top', 5),(self.widgets["osmTopTextField"], 'left', 110)])
        cmds.formLayout(self.widgets["osm_formLayout"], edit = True, af = [(self.widgets["osmBotTextField"], 'top', 60),(self.widgets["osmBotTextField"], 'left', 110)])
        cmds.formLayout(self.widgets["osm_formLayout"], edit = True, af = [(self.widgets["osmLeftTextField"], 'top', 33),(self.widgets["osmLeftTextField"], 'left', 20)])
        cmds.formLayout(self.widgets["osm_formLayout"], edit = True, af = [(self.widgets["osmRightTextField"], 'top', 33),(self.widgets["osmRightTextField"], 'left', 200)])
        cmds.formLayout(self.widgets["osm_formLayout"], edit = True, af = [(self.widgets["osmImportButton"], 'top', 100),(self.widgets["osmImportButton"], 'left', 105)])

        #==============================================================================================================
        cmds.dockControl("cityGenerator_dockControl", label = "City Generator", area = 'right', allowedArea = 'right', content = self.widgets["window"])

    def openFileDialog(self, filter, fileMode, textField):

        filePath = cmds.fileDialog2(fileFilter=filter, fileMode = fileMode, dialogStyle=2)
        if filePath is not None:
            cmds.textField(self.widgets[textField], edit = True, fi = filePath[0])

    def downloadOSM(self, *args):
        left = cmds.textField(self.widgets["osmLeftTextField"], q = True, fi = True)
        bot = cmds.textField(self.widgets["osmBotTextField"], q = True, fi = True)
        right = cmds.textField(self.widgets["osmRightTextField"], q = True, fi = True)
        top = cmds.textField(self.widgets["osmTopTextField"], q = True, fi = True)

        url = "http://api.openstreetmap.org/api/0.6/map?bbox=" + left + "," + bot + "," + right + "," + top
        filePath = cmds.fileDialog2(fileFilter="OSM XML (*.osm)", fileMode = 0, dialogStyle=2)
        if filePath is None:
            return
        file_name = filePath[0]

        try:
            u = urllib2.urlopen(url)
        except urllib2.HTTPError as err:
            if err.code == 400:
                cmds.confirmDialog(title='Error', message="HTTPError {0}: Incorrect borders".format(err.code))
            elif err.code == 509:
                cmds.confirmDialog(title='Error', message="HTTPError {0}: You have downloaded too much data. Please try again later".format(err.code))
            else:
                cmds.confirmDialog(title='Error', message="HTTPError {0}".format(err.code))
            return

        f = open(file_name, 'wb')
        cmds.progressWindow(title='Downloading map', min = 0, max = 100,  progress = 0, status = "Downloading: %s " % (file_name), isInterruptable = False)

        while True:
            buffer = u.read(8192)
            if not buffer:
                break
            f.write(buffer)
        f.close()
        cmds.progressWindow(endProgress = True)
        cmds.textField(self.widgets["osmFileTextField"], edit = True, fi = filePath[0])

    # http://gis-lab.info/qa/great-circles.html
    def coordinates_dist(self, long1, lat1, long2, lat2):
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

    def pauseRender(self, *args):
        if platform.system() == 'Windows':
            subprocess.check_output(["pssuspend", "mayabatch.exe"], shell=True)
        elif platform.system() == 'Darwin':
            subprocess.check_output(["killall", "-STOP", "mayabatch"], shell=False)
        elif platform.system() == 'Linux':
            subprocess.check_output(["killall", "-STOP", "mayabatch"], shell=False)

    def resumeRender(self, *args):
        if platform.system() == 'Windows':
            subprocess.check_output(["pssuspend", "-r", "mayabatch.exe"], shell=True)
        elif platform.system() == 'Darwin':
            subprocess.check_output(["killall", "-CONT", "mayabatch"], shell=False)
        elif platform.system() == 'Linux':
            subprocess.check_output(["killall", "-CONT", "mayabatch"], shell=False)


    def createCamera(self, *args):
        if cmds.objExists('path_curve'):
            cmds.delete('path_curve')

        if cmds.objExists('aim_curve'):
            cmds.delete('aim_curve')

        if cmds.objExists('render_camera1_group'):
            cmds.delete('render_camera1_group')

        map_file = cmds.textField(self.widgets["osmFileTextField"], q = True, fi = True)
        size_multiplier = int(cmds.textField(self.widgets["sizeMultTextField"], q = True, tx = True))
        camera_dist = int(cmds.textField(self.widgets["cameraDistTextField"], q = True, tx = True))
        camera_delta = camera_dist/size_multiplier
        fillet_radius = camera_delta * 2
        xmlData = xml.dom.minidom.parse(map_file)

        bounds = xmlData.getElementsByTagName("bounds")[0]
        minlat = float(bounds.getAttribute('minlat'))
        maxlat = float(bounds.getAttribute('maxlat'))
        minlon = float(bounds.getAttribute('minlon'))
        maxlon = float(bounds.getAttribute('maxlon'))

        dist_lon = self.coordinates_dist(minlon, minlat, maxlon, minlat)
        dist_lat = self.coordinates_dist(minlon, minlat, minlon, maxlat)

        cmds.curve(n="path_curve", d=1, ep=[(camera_delta, 0, (dist_lat/(2*size_multiplier)) + camera_delta), ((dist_lon/(2*size_multiplier)) - camera_delta, 0, (dist_lat/(2*size_multiplier)) + camera_delta)])

        cmds.curve(n="tmp_curve", d=1, ep=[((dist_lon/(2*size_multiplier)) + camera_delta, 0, (dist_lat/(2*size_multiplier)) - camera_delta), ((dist_lon/(2*size_multiplier)) + camera_delta, 0, -((dist_lat/(2*size_multiplier)) - camera_delta))])
        len =  cmds.arclen("path_curve")
        cmds.filletCurve("path_curve", "tmp_curve", cir=True, cp1=len, cp2=0, r=fillet_radius, t=True,  jn=True, rpo=True)

        cmds.curve("tmp_curve", r=True, d=1, ep=[((dist_lon/(2*size_multiplier)) - camera_delta, 0, -((dist_lat/(2*size_multiplier)) + camera_delta)), (-((dist_lon/(2*size_multiplier)) - camera_delta), 0, -((dist_lat/(2*size_multiplier)) + camera_delta))])
        len =  cmds.arclen("path_curve")
        cmds.filletCurve("path_curve", "tmp_curve", cir=True, cp1=len, cp2=0, r=fillet_radius, t=True,  jn=True, rpo=True)

        cmds.curve("tmp_curve", r=True, d=1, ep=[(-((dist_lon/(2*size_multiplier)) + camera_delta), 0, -((dist_lat/(2*size_multiplier)) - camera_delta)), (-((dist_lon/(2*size_multiplier)) + camera_delta), 0, ((dist_lat/(2*size_multiplier)) - camera_delta))])
        len =  cmds.arclen("path_curve")
        cmds.filletCurve("path_curve", "tmp_curve", cir=True, cp1=len, cp2=0, r=fillet_radius, t=True,  jn=True, rpo=True)

        cmds.curve("tmp_curve", r=True, d=1, ep=[(-((dist_lon/(2*size_multiplier)) - camera_delta), 0, ((dist_lat/(2*size_multiplier)) + camera_delta)), (-camera_delta, 0, ((dist_lat/(2*size_multiplier)) + camera_delta))])
        len =  cmds.arclen("path_curve")
        cmds.filletCurve("path_curve", "tmp_curve", cir=True, cp1=len, cp2=0, r=fillet_radius, t=True,  jn=True, rpo=True)

        cmds.delete("tmp_curve")

        x_scale = (dist_lon - camera_dist/2)/dist_lon
        z_scale = (dist_lat - camera_dist/2)/dist_lat
        cmds.duplicate("path_curve", n="aim_curve")
        cmds.select('aim_curve', r=True)
        cmds.scale(x_scale, 1, z_scale)

        camera_height = int(cmds.textField(self.widgets["cameraHeightTextField"], q = True, tx = True))
        camera_angle = int(cmds.textField(self.widgets["cameraAngleTextField"], q = True, tx = True))
        camera_angle = math.radians(camera_angle)
        aim_delta = math.tan(camera_angle) * (camera_delta/2)

        cmds.select('path_curve', r=True)
        cmds.move(0, camera_height/size_multiplier, 0)

        cmds.select('aim_curve', r=True)
        cmds.move(0, camera_height/size_multiplier - aim_delta, 0)

        cmds.camera(n="render_camera", hfv=85)
        mel.eval('cameraMakeNode 2 "";')

        cmds.group('render_camera1', n='path_group')
        cmds.group('render_camera1_aim', n='aim_group')

        start_time = 0
        playback_time = int(cmds.textField(self.widgets["playbackTimeTextField"], q = True, tx = True))
        cmds.playbackOptions(maxTime=playback_time)

        cmds.pathAnimation('path_group', c='path_curve', f=True, fa='z', ua='y', wu=(0.0, 1.0, 0.0), inverseFront=True, b=True, bs=3.0, stu=start_time, etu=playback_time)
        cmds.pathAnimation('aim_group', c='aim_curve', f=True, fa='z', ua='y', wu=(0.0, 1.0, 0.0), inverseFront=True, b=True, bs=3.0, stu=start_time, etu=playback_time)
        cmds.setAttr('render_cameraShape2.backgroundColor', 1, 1, 1, type='double3')

        xmlData.unlink()

    def generateCity(self, *args):
        map_file = cmds.textField(self.widgets["osmFileTextField"], q = True, fi = True)
        winds_file = cmds.textField(self.widgets["wrfFileTextField"], q = True, fi = True)
        heights_file = cmds.textField(self.widgets["demFileTextField"], q = True, fi = True)
        jams_file = cmds.textField(self.widgets["jamsFileTextField"], q = True, fi = True)

        raw_wrf = cmds.checkBox(self.widgets["wrfCheckBox"], q=True, v=True)
        raw_dem = cmds.checkBox(self.widgets["demCheckBox"], q=True, v=True)

        if raw_wrf:
            if platform.system() == 'Windows':
                s = subprocess.check_output(["where", "python"], shell=True)
            else:
                s = subprocess.check_output(["which", "python"], shell=False)
            python_path = s.splitlines()[-1]
            script_dir = os.path.dirname(os.path.realpath(__file__))
            winds_file = subprocess.check_output([python_path, script_dir + "\NetCDF_converter.py", map_file, winds_file], shell=False).rstrip()

        if raw_dem:
            if platform.system() == 'Windows':
                s = subprocess.check_output(["where", "python"], shell=True)
            else:
                s = subprocess.check_output(["which", "python"], shell=False)
            python_path = s.splitlines()[-1]
            script_dir = os.path.dirname(os.path.realpath(__file__))
            heights_file = subprocess.check_output([python_path, script_dir + "\DEM_converter.py", map_file, heights_file], shell=False).rstrip()


        if cmds.objExists('city'):
            cmds.delete('city')

        def calc_emmiter_level(waypoints):
            if (jams_file == ""):
                return 0

            jams_data = open(jams_file, 'r')
            sum_jams_level = 0
            jams_points = 0

            shift_lat = -0.00766
            shift_lon = 0.006868

            for waypoint in waypoints:
                for line in jams_data:
                    tmp = line.split(' ')
                    lon = float(tmp[0]) - shift_lon
                    lat = float(tmp[1]) - shift_lat
                    if lat < minlat or lat > maxlat or lon < minlon or lon > maxlon:
                        continue
                    data = float(tmp[2])
                    jams_point = convert_coordinates(lon, lat)
                    dist = math.sqrt(math.pow(waypoint[0]-jams_point[0], 2)+math.pow(waypoint[2]-jams_point[2], 2))
                    if dist < (25.0/size_multiplier):
                        sum_jams_level += data
                        jams_points += 1

            if jams_points >= (len(waypoints) * 0.5):
                return 1.0*sum_jams_level/jams_points
            else:
                return 0

            jams_data.close()


        def convert_coordinates(lon, lat):
            centered_lat = (lat-minlat) - (maxlat-minlat)/2
            centered_lon = (lon-minlon) - (maxlon-minlon)/2
            normalized_lat = centered_lat * norm_lat
            normalized_lon = centered_lon * norm_lon
            return [normalized_lon, 0, -normalized_lat]

        #meters
        size_multiplier = float(cmds.textField(self.widgets["sizeMultTextField"], q = True, tx = True))
        emit_multiplier = float(cmds.textField(self.widgets["emitMultTextField"], q = True, tx = True))
        hasl = float(cmds.textField(self.widgets["haslTextField"], q = True, tx = True))

        xmlData = xml.dom.minidom.parse(map_file)

        points_ids = []
        points = []
        heights = []

        bounds = xmlData.getElementsByTagName("bounds")[0]
        minlat = float(bounds.getAttribute('minlat'))
        maxlat = float(bounds.getAttribute('maxlat'))
        minlon = float(bounds.getAttribute('minlon'))
        maxlon = float(bounds.getAttribute('maxlon'))

        dist_lon = self.coordinates_dist(minlon, minlat, maxlon, minlat)
        dist_lat = self.coordinates_dist(minlon, minlat, minlon, maxlat)

        norm_lat = (dist_lat/size_multiplier)/(maxlat-minlat)
        norm_lon = (dist_lon/size_multiplier)/(maxlon-minlon)

        #============================Get heights===================================
        heights_data = open(heights_file, 'r')

        rows = 0
        cols = 0
        start_lon = 0
        start_lat = 0
        delta_lon = 0
        delta_lat = 0

        heights_matrix = []

        for line in heights_data:
            tmp = line.strip().split(' ')

            if rows == 0:
                rows = float(tmp[0])
                cols = float(tmp[1])
            elif start_lon == 0:
                start_lon = float(tmp[0])
                start_lat = float(tmp[1])
            elif delta_lon == 0:
                delta_lon = float(tmp[0])
                delta_lat = float(tmp[1])
            else:
                row = []
                for cell in tmp:
                    row.append(int(cell)-hasl)
                heights_matrix.append(row)

        #==========================================================================

        maxprogress = 0
        ways = xmlData.getElementsByTagName('way')
        for way in ways:
            tags = way.getElementsByTagName('tag')
            for tag in tags:
                tag_type = str(tag.getAttribute('k'))
                if (tag_type == 'highway'):
                    subtype = str(tag.getAttribute('v'))
                    if not(subtype == 'pedestrian') and not(subtype == 'steps') and not(subtype == 'footway') and not(subtype == 'cycleway'):
                        maxprogress += 1
                if (tag_type == 'building'):
                    maxprogress += 1

        progress = 0
        cmds.progressWindow(title='Generating city', min = 0, max = maxprogress,  progress = progress, status = 'Processing nodes', isInterruptable = False)

        #============================Handle nodes==================================
        nodes = xmlData.getElementsByTagName('node')
        for node in nodes:
            lat = float(node.getAttribute('lat'))
            lon = float(node.getAttribute('lon'))

            if lat < minlat or lat > maxlat or lon < minlon or lon > maxlon:
                continue

            point = convert_coordinates(lon, lat)

            points_ids.append(int(node.getAttribute('id')))
            points.append(point)
            heights.append(heights_matrix[int(math.floor((lon-start_lon)/delta_lon))][int(math.floor((lat-start_lat)/delta_lat))])
        #==========================================================================

        #=============================Handle ways==================================
        roads = 0
        buildings = 0
        emitter = 0

        cmds.particle(n='nParticle')
        cmds.particle('nParticle', e=True, at='mass', order=0, fv=1e-5)
        cmds.setAttr('nParticleShape.lifespanMode', 2)
        cmds.setAttr('nParticleShape.lifespan', 6)
        cmds.setAttr('nParticleShape.lifespanRandom', 2)

        cmds.select('nParticleShape', r=True)
        cmds.addAttr(longName='betterIllumination', at='bool', defaultValue=False )
        cmds.addAttr(longName='surfaceShading', at='float', defaultValue=0, minValue=0, maxValue=1)
        cmds.addAttr(longName='threshold', at='float', defaultValue=0, minValue=0, maxValue=10)
        cmds.addAttr(longName='radius', at='float', defaultValue=1, minValue=0, maxValue=20)
        cmds.addAttr(longName='flatShaded', at='bool', defaultValue=False)

        cmds.setAttr('nParticleShape.particleRenderType', 8)
        cmds.setAttr('nParticleShape.radius', 0.06)

        cmds.setAttr('particleCloud1.transparency', 0.53, 0.53, 0.53, type='double3')
        cmds.setAttr('particleCloud1.color', 1.0, 0.0, 0.483, type='double3')
        cmds.setAttr('particleCloud1.incandescence', 1.0, 0.0, 0.850, type='double3')
        cmds.setAttr('particleCloud1.glowIntensity', 0.111)


        ways = xmlData.getElementsByTagName('way')
        for way in ways:
            waypoints = []
            heights_sum = 0
            nodes = way.getElementsByTagName('nd')
            tags = way.getElementsByTagName('tag')

            for node in nodes:
                ref = int(node.getAttribute('ref'))
                try:
                    index = points_ids.index(ref)
                except ValueError:
                    index = -1

                if index != -1:
                    waypoints.append(points[index])
                    heights_sum += heights[index]

            for tag in tags:
                tag_type = str(tag.getAttribute('k'))
                if tag_type == 'highway':
                    subtype = str(tag.getAttribute('v'))
                    if not(subtype == 'pedestrian') and not(subtype == 'steps') and not(subtype == 'footway') and not(subtype == 'cycleway'):
                        roads += 1
                        progress += 1
                        cmds.progressWindow(edit=True, progress = progress, status='Generating road: ' + str(roads))

                        lanes = 2
                        for tag in tags:
                            tag_type = str(tag.getAttribute('k'))
                            if tag_type == 'lanes':
                                lanes = float(str(tag.getAttribute('v')))

                        if len(waypoints) >= 2:
                            cmds.curve(n='pathcurve_' + str(roads), p=waypoints, d=1)
                            sx = waypoints[0][0]
                            sz = waypoints[0][2]
                            dx = waypoints[0][2]-waypoints[1][2]
                            dz = waypoints[1][0]-waypoints[0][0]
                            ln = math.sqrt(math.pow(2*dx, 2) + math.pow(2*dz, 2))
                            dx /= (ln*size_multiplier)/(3*lanes)
                            dz /= (ln*size_multiplier)/(3*lanes)
                            ln = 0

                            for i in range(0, len(waypoints)-2):
                                ln += math.trunc(math.sqrt(math.pow(waypoints[i+1][0]-waypoints[i][0], 2) + math.pow(waypoints[i+1][2]-waypoints[i][2], 2))) + 1
                            cmds.curve(n='extrudecurve_' + str(roads), p=[(sx-dx, 0, sz-dz), (sx+dx, 0, sz+dz)], d=1)
                            cmds.rebuildCurve('pathcurve_' + str(roads), rt=0, s=200)
                            cmds.nurbsToPolygonsPref(f=2, pt=1, ut=1, un=2, vt=1, vn=ln * 5 + 30)
                            cmds.extrude('extrudecurve_' + str(roads), 'pathcurve_' + str(roads), n='road_' + str(roads), et=2, po=1)
                            cmds.delete('extrudecurve_' + str(roads),)


                            emitter_level = calc_emmiter_level(waypoints)
                            if emitter_level > 0:
                                emitter += 1
                                cmds.select('pathcurve_' + str(roads), r=True)
                                cmds.move(0, 0.03, 0)
                                cmds.emitter(n='emitter_' + str(emitter), type='omni', r=emit_multiplier*emitter_level, spd=0.1, srn=0, sp=0)
                                cmds.connectDynamic('nParticle', em='emitter_' + str(emitter))


                            cmds.select('road_' + str(roads), r=True)
                            cmds.move(0, 0.004, 0)


                elif tag_type == 'building':
                    temp = str(tag.getAttribute('v'))
                    if temp == 'yes':
                        buildings += 1
                        progress += 1
                        cmds.progressWindow(edit=True, progress = progress, status='Generating building: ' + str(buildings))

                        if len(waypoints) >= 3:
                            cmds.polyCreateFacet(n='building_' + str(buildings), p=waypoints)
                            cmds.select('building_' + str(buildings), r=True)
                            normal = cmds.polyInfo(fn=True)[0].partition('0: ')[2].split(' ')[1]
                            if float(normal) < 0:
                                cmds.polyMirrorFace(direction=2, p=(0, 0, 0), mergeMode=0, worldSpace=1)
                                cmds.polyDelFacet('building_' + str(buildings) + '.f[0]')

                            avg_height = heights_sum / len(waypoints)

                            cmds.polyExtrudeFacet('building_' + str(buildings) + '.f[0]',  ltz=(1.0 * avg_height/size_multiplier))

                            cmds.select('building_' + str(buildings), r=True)

                            cmds.collision('building_' + str(buildings), 'nParticle')

        #==========================================================================

        #============================Handle winds==================================
        winds_data = open(winds_file, 'r')
        winds = 0
        cmds.progressWindow(edit=True, progress = progress, status='Setting winds')
        for line in winds_data:
            winds += 1

            tmp = line.split(' ')
            lon = float(tmp[0])
            lat = float(tmp[1])
            x = float(tmp[2])
            y = float(tmp[3])
            z = float(tmp[4])

            magn = math.sqrt(math.pow(x, 2) + math.pow(y, 2) + math.pow(z, 2))
            max_dist = self.coordinates_dist(0, 0, 0.006364, 0.006364)/size_multiplier
            volume_size = self.coordinates_dist(0, 0, 0.0045, 0.0045)/size_multiplier
            position = convert_coordinates(lon, lat)

            cmds.air(n='wind_' + str(winds), pos=position, wns=True, dx=x, dy=y, dz=z, m=magn, s=1, mxd=max_dist)
            cmds.setAttr('wind_' + str(winds) + '.volumeShape', 1)
            cmds.setAttr('wind_' + str(winds) + '.volumeOffsetY', 1)
            cmds.scale(volume_size, volume_size/2, volume_size, 'wind_' + str(winds))
            cmds.connectDynamic('nParticle', f='wind_' + str(winds))
            cmds.select(cl=True)
        #==========================================================================

        cmds.gravity(n='gravity', m=9.8*1e-5)
        cmds.connectDynamic('nParticle', f='gravity')
        cmds.polyPlane(n='ground', sx=(maxlon-minlon), sy=(maxlat-minlat), w=(maxlon-minlon)*norm_lon, h=(maxlat-minlat)*norm_lat)
        cmds.collision('ground', 'nParticle')

        cmds.select('building_*', r=True)
        cmds.select('road_*', tgl=True)
        cmds.select('ground', tgl=True)
        cmds.select('nParticle', tgl=True)
        cmds.editRenderLayerGlobals(currentRenderLayer='AOLayer')
        cmds.editRenderLayerMembers('AOLayer')

        cmds.select('road_*', r=True)
        cmds.group(n='roads')

        cmds.select('building_*', r=True)
        cmds.group(n='buildings')

        cmds.select('pathcurve_*', r=True)
        cmds.group(n='emitters')

        cmds.select('roads', r=True)
        cmds.select('buildings', tgl=True)
        cmds.select('emitters', tgl=True)
        cmds.select('nParticle', tgl=True)
        cmds.select('gravity', tgl=True)
        cmds.select('ground', tgl=True)
        cmds.select('wind_1', tgl=True)
        cmds.group(n='city')

        xmlData.unlink()
        winds_data.close()
        heights_data.close()

        if raw_wrf:
            os.remove(winds_file)

        if raw_dem:
            os.remove(heights_file)

        cmds.progressWindow(endProgress = True)