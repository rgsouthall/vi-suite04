# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy, glob, os, inspect, datetime, shutil
from nodeitems_utils import NodeCategory, NodeItem
from .vi_func import objvol, socklink, newrow, epwlatilongi, nodeid, nodeinputs, remlink, rettimes, epentry, sockhide, selobj, cbdmhdr, cbdmmtx
from .vi_func import hdrsky, nodecolour, epschedwrite, facearea, retelaarea, retrmenus, resnameunits, enresprops, iprop, bprop, eprop, fprop, sunposlivi
from .livi_export import sunexport, skyexport, hdrexport

class ViNetwork(bpy.types.NodeTree):
    '''A node tree for VI-Suite analysis.'''
    bl_idname = 'ViN'
    bl_label = 'Vi Network'
    bl_icon = 'LAMP_SUN'
    viparams = {}

class ViNodes:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ViN'

class ViLoc(bpy.types.Node, ViNodes):
    '''Node describing a geographical location manually or with an EPW file'''
    bl_idname = 'ViLoc'
    bl_label = 'VI Location'
    bl_icon = 'LAMP'

    def updatelatlong(self, context):
        scene = context.scene
        (scene.latitude, scene.longitude) = epwlatilongi(context.scene, self) if self.loc == '1' and self.weather else (scene.latitude, scene.longitude)
        nodecolour(self, any([link.to_node.bl_label in ('LiVi CBDM', 'EnVi Export') and self.loc != "1" for link in self.outputs['Location out'].links]))
        if self.loc == '1' and self.weather:
            resdict, allresdict, self['rtypes'], self['dos'], ctypes = {}, {}, ['Time', 'Climate'], '0', []
            resdict['0'] = ['Day of Simulation']
            for d in range(1, 366):
                resdict['0'] += [str(d) for x in range(1,25)]
            for rtype in ('ztypes', 'zrtypes', 'ltypes', 'lrtypes', 'entypes', 'enrtypes'):
                self[rtype] = []
            with open(self.weather, 'r') as epwfile:
                epwlines = epwfile.readlines()[8:]
                epwcolumns = list(zip(*[epwline.split(',') for epwline in epwlines]))
                allresdict['Month'], allresdict['Day'], allresdict['Hour'] = [epwcolumns[c] for c in range(1,4)]
                allresdict['dos'] = [int(d/24) + 1 for d in range(len(epwlines))]
                for c in {"Temperature ("+ u'\u00b0'+"C)": 6, 'Humidity (%)': 8, "Direct Solar (W/m"+u'\u00b2'+")": 14, "Diffuse Solar (W/m"+u'\u00b2'+")": 15,
                          'Wind Direction (deg)': 20, 'Wind Speed (m/s)': 21}.items():
                    resdict[str(c[1])] = ['Climate', c[0]]
                    allresdict[str(c[1])] = list(epwcolumns[c[1]])
                    ctypes.append(c[0])
                self['resdict'], self['allresdict'], self['ctypes'] = resdict, allresdict, ctypes
                self.outputs['Location out']['epwtext'] = epwfile.read()
            self.outputs['Location out']['valid'] = ['Location', 'Vi Results']
        else:
            self.outputs['Location out']['epwtext'] = ''
            self.outputs['Location out']['valid'] = ['Location']
        socklink(self.outputs['Location out'], self['nodeid'].split('@')[1])

    epwpath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+'/EPFiles/Weather/'
    weatherlist = [((wfile, os.path.basename(wfile).strip('.epw').split(".")[0], 'Weather Location')) for wfile in glob.glob(epwpath+"/*.epw")]
    weather = bpy.props.EnumProperty(items = weatherlist, name="", description="Weather for this project", update = updatelatlong)
    loc = bpy.props.EnumProperty(items = [("0", "Manual", "Manual location"), ("1", "EPW ", "Get location from EPW file")], name = "", description = "Location", default = "0", update = updatelatlong)
    maxws = bpy.props.FloatProperty(name="", description="Max wind speed", min=0, max=90, default=0)
    minws = bpy.props.FloatProperty(name="", description="Min wind speed", min=0, max=90, default=0)
    avws = bpy.props.FloatProperty(name="", description="Average wind speed", min=0, max=90, default=0)
    dsdoy = bpy.props.IntProperty(name="", description="", min=1, max=365, default=1)
    dedoy = bpy.props.IntProperty(name="", description="", min=1, max=365, default=365)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        bpy.data.node_groups[nodeid(self).split('@')[1]].use_fake_user = True
        self.outputs.new('ViLoc', 'Location out')

    def update(self):
        socklink(self.outputs['Location out'], self['nodeid'].split('@')[1])
        nodecolour(self, any([link.to_node.bl_label in ('LiVi CBDM', 'EnVi Export') and self.loc != "1" for link in self.outputs['Location out'].links]))
        
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label(text = 'Source:')
        row.prop(self, "loc")
        if self.loc == "1":
            row = layout.row()
            row.prop(self, "weather")
        else:
            row = layout.row()
            row.prop(context.scene, "latitude")
            row = layout.row()
            row.prop(context.scene, "longitude")

class ViGExLiNode(bpy.types.Node, ViNodes):
    '''Node describing a LiVi geometry export node'''
    bl_idname = 'ViGExLiNode'
    bl_label = 'LiVi Geometry'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.animated, self.startframe, self.endframe, self.cpoint, self.offset)])

    cpoint = bpy.props.EnumProperty(items=[("0", "Faces", "Export faces for calculation points"),("1", "Vertices", "Export vertices for calculation points"), ],
            name="", description="Specify the calculation point geometry", default="1", update = nodeupdate)
    offset = bpy.props.FloatProperty(name="", description="Calc point offset", min = 0.001, max = 1, default = 0.01, update = nodeupdate)
    animated = bpy.props.BoolProperty(name="", description="Animated analysis", default = 0, update = nodeupdate)
    startframe = bpy.props.IntProperty(name="", description="Start frame for animation", min = 0, default = 0, update = nodeupdate)
    endframe = bpy.props.IntProperty(name="", description="End frame for animation", min = 0, default = 0, update = nodeupdate)
    
    def init(self, context):
        self['exportstate'] = ''
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViLiG', 'Geometry out')
 #       self.inputs.new('ViGen', 'Generative in')
        self.outputs['Geometry out']['Text'] = {}
        self.outputs['Geometry out']['Text'] = {}
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, 'Animated:', self, 'animated')
        if self.animated:
            row = layout.row()
            row.label(text = 'Frames:')
            col = row.column()
            subrow = col.row(align=True)
            subrow.prop(self, 'startframe')
            subrow.prop(self, 'endframe')

        newrow(layout, 'Result point:', self, 'cpoint')
        newrow(layout, 'Offset:', self, 'offset')
        row = layout.row()
        row.operator("node.ligexport", text = "Export").nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Geometry out'], self['nodeid'].split('@')[1])

    def preexport(self, scene):
        self.outputs['Geometry out']['Text'] = {}
        self.outputs['Geometry out']['Options'] = {'offset': self.offset, 'fs': (scene.frame_current, self.startframe)[self.animated], 'fe': (scene.frame_current, self.endframe)[self.animated], 'cp': self.cpoint, 'anim': self.animated}
        
    def postexport(self, scene):
        bpy.data.node_groups[self['nodeid'].split('@')[1]].use_fake_user = 1
        self['exportstate'] = [str(x) for x in (self.animated, self.startframe, self.endframe, self.cpoint, self.offset)]
        nodecolour(self, 0)

class LiViNode(bpy.types.Node, ViNodes):
    '''Node for creating a LiVi analysis'''
    bl_idname = 'LiViNode'
    bl_label = 'LiVi Context'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        scene = context.scene
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.contextmenu, self.banalysismenu, self.canalysismenu, self.cbanalysismenu, 
                   self.animated, self.skymenu, self.shour, self.sdoy, self.startmonth, self.endmonth, self.damin, self.dasupp, self.dalux, self.daauto,
                   self.ehour, self.edoy, self.interval, self.hdr, self.hdrname, self.skyname, self.resname, self.turb, self.mtxname, self.cbdm_start_hour,
                   self.cbdm_end_hour, self.bambuildmenu)])
        if self.edoy < self.sdoy:
            self.edoy = self.sdoy
        if self.edoy == self.sdoy:
            if self.ehour < self.shour:
                self.ehour = self.shour
        
        self['skynum'] = int(self.skymenu)         
        suns = [ob for ob in scene.objects if ob.type == 'LAMP' and ob.data.type == 'SUN'] 
        
        if self.contextmenu == 'Basic' and self['skynum'] < 2:
            starttime = datetime.datetime(datetime.datetime.now().year, 1, 1, int(self.shour), int((self.shour - int(self.shour))*60)) + datetime.timedelta(self.sdoy - 1) if self['skynum'] < 3 else datetime.datetime(2013, 1, 1, 12)                                       
            self['endframe'] = self.startframe + int(((24 * (self.edoy - self.sdoy) + self.ehour - self.shour)/self.interval)) if self.animated else [scene.frame_current]
            frames = range(self.startframe, self['endframe']) if self.animated else [scene.frame_current]
            scene.frame_start, scene.frame_end = self.startframe, frames[-1]
            if suns:
                sun = suns[0]
                sun['VIType'] = 'Sun'
                [scene.objects.unlink(o) for o in suns[1:]]
#                if len(suns) > 1:
#                    for so in suns[1:]:
#                        selobj(scene, so)
#                        bpy.ops.object.delete()
            else:
                bpy.ops.object.lamp_add(type='SUN')
                sun = bpy.context.object
                sun['VIType'] = 'Sun'

            if self.inputs['Location in'].links and suns:
                sunposlivi(scene, self, frames, sun, starttime)
        else:
            for so in suns:
                selobj(scene, so)
                bpy.ops.object.delete()
                                
    banalysistype = [('0', "Illu/Irrad/DF", "Illumninance/Irradiance/Daylight Factor Calculation"), ('1', "Glare", "Glare Calculation")]
    skylist = [("0", "Sunny", "CIE Sunny Sky description"), ("1", "Partly Coudy", "CIE Sunny Sky description"),
               ("2", "Coudy", "CIE Partly Cloudy Sky description"), ("3", "DF Sky", "Daylight Factor Sky description"),
               ("4", "HDR Sky", "HDR file sky"), ("5", "Radiance Sky", "Radiance file sky"), ("6", "None", "No Sky")]

    contexttype = [('Basic', "Basic", "Basic analysis"), ('Compliance', "Compliance", "Compliance analysis"), ('CBDM', "CBDM", "Climate based daylight modelling")]
    contextmenu = bpy.props.EnumProperty(name="", description="Contexttype type", items=contexttype, default = 'Basic', update = nodeupdate)
    animated = bpy.props.BoolProperty(name="", description="Animated sky", default=False, update = nodeupdate)
    offset = bpy.props.FloatProperty(name="", description="Calc point offset", min=0.001, max=1, default=0.01, update = nodeupdate)
    banalysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = banalysistype, default = '0', update = nodeupdate)
    skymenu = bpy.props.EnumProperty(name="", items=skylist, description="Specify the type of sky for the simulation", default="0", update = nodeupdate)
    shour = bpy.props.FloatProperty(name="", description="Hour of simulation", min=0, max=23.99, default=12, subtype='TIME', unit='TIME', update = nodeupdate)
    sdoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = nodeupdate)
    ehour = bpy.props.FloatProperty(name="", description="Hour of simulation", min=0, max=23.99, default=12, update = nodeupdate)
    edoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = nodeupdate)
    interval = bpy.props.FloatProperty(name="", description="Site Latitude", min=1/60, max=24, default=1, update = nodeupdate)
    hdr = bpy.props.BoolProperty(name="", description="Export HDR panoramas", default=False, update = nodeupdate)
    skyname = bpy.props.StringProperty(name="", description="Name of the Radiance sky file", default="", update = nodeupdate)
    resname = bpy.props.StringProperty()
    turb = bpy.props.FloatProperty(name="", description="Sky Turbidity", min=1.0, max=5.0, default=2.75, update = nodeupdate)
    canalysistype = [('0', "BREEAM", "BREEAM HEA1 calculation"), ('1', "CfSH", "Code for Sustainable Homes calculation"), ('2', "LEED", "LEED EQ8.1 calculation")]#, ('3', "Green Star", "Green Star Calculation")]
    bambuildtype = [('0', "School", "School lighting standard"), ('1', "Higher Education", "Higher education lighting standard"), ('2', "Healthcare", "Healthcare lighting standard"), ('3', "Residential", "Residential lighting standard"), ('4', "Retail", "Retail lighting standard"), ('5', "Office & other", "Office and other space lighting standard")]
    canalysismenu = bpy.props.EnumProperty(name="", description="Type of analysis", items = canalysistype, default = '0', update = nodeupdate)
    bambuildmenu = bpy.props.EnumProperty(name="", description="Type of building", items=bambuildtype, default = '0', update = nodeupdate)
    cusacc = bpy.props.StringProperty(name="", description="Custom Radiance simulation parameters", default="", update = nodeupdate)
    buildstorey = bpy.props.EnumProperty(items=[("0", "Single", "Single storey building"),("1", "Multi", "Multi-storey building")], name="", description="Building storeys", default="0", update = nodeupdate)
    cbanalysistype = [('0', "Light Exposure", "LuxHours Calculation"), ('1', "Radiation Exposure", "kWh/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Autonomy", "DA (%) Calculation"), ('3', "Hourly irradiance", "Irradiance for each simulation time step"), ('4', "UDI", "Useful Daylight Illuminance")]
    cbanalysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = cbanalysistype, default = '0', update = nodeupdate)
    sourcetype = [('0', "EPW", "EnergyPlus weather file"), ('1', "HDR", "HDR sky file")]
    sourcetype2 = [('0', "EPW", "EnergyPlus weather file"), ('1', "VEC", "Generated vector file")]
    sourcemenu = bpy.props.EnumProperty(name="", description="Source type", items=sourcetype, default = '0', update = nodeupdate)
    sourcemenu2 = bpy.props.EnumProperty(name="", description="Source type", items=sourcetype2, default = '0', update = nodeupdate)
    hdrname = bpy.props.StringProperty(name="", description="Name of the composite HDR sky file", default="", update = nodeupdate)
    mtxname = bpy.props.StringProperty(name="", description="Name of the calculated vector sky file", default="", update = nodeupdate)
    weekdays = bpy.props.BoolProperty(name = '', default = False, update = nodeupdate)
    cbdm_start_hour =  bpy.props.IntProperty(name = '', default = 8, min = 1, max = 24, update = nodeupdate)
    cbdm_end_hour =  bpy.props.IntProperty(name = '', default = 20, min = 1, max = 24, update = nodeupdate)
    dalux =  bpy.props.IntProperty(name = '', default = 300, min = 1, max = 2000, update = nodeupdate)
    damin = bpy.props.IntProperty(name = '', default = 100, min = 1, max = 2000, update = nodeupdate)
    dasupp = bpy.props.IntProperty(name = '', default = 300, min = 1, max = 2000, update = nodeupdate)
    daauto = bpy.props.IntProperty(name = '', default = 3000, min = 1, max = 5000, update = nodeupdate)
    startmonth = bpy.props.IntProperty(name = '', default = 1, min = 1, max = 12, description = 'Start Month', update = nodeupdate)
    endmonth = bpy.props.IntProperty(name = '', default = 12, min = 1, max = 12, description = 'End Month', update = nodeupdate)
    startframe = bpy.props.IntProperty(name = '', default = 0, min = 0, description = 'Start Frame', update = nodeupdate)

    def init(self, context):
        self['exportstate'], self['skynum'], self['watts'] = '', 0, 0
        self['nodeid'] = nodeid(self)
        self['whitesky'] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"
        self.outputs.new('ViLiC', 'Context out')
        self.inputs.new('ViLoc', 'Location in')
        self.outputs['Context out']['Text'] = {}
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, 'Context:', self, 'contextmenu')
        if self.contextmenu == 'Basic':
            newrow(layout, "Standard:", self, 'banalysismenu')
            newrow(layout, "Sky type:", self, 'skymenu')
            if self.skymenu in ('0', '1', '2'):
                newrow(layout, "Start hour:", self, 'shour')
                newrow(layout, "Start day:", self, 'sdoy')
                newrow(layout, "Animation;", self, 'animated')
                if self.animated:
                    newrow(layout, "Start frame:", self, 'startframe')
                    row = layout.row()
                    row.label(text = 'End frame:')
                    row.label(text = '{}'.format(self['endframe']))
                    newrow(layout, "End hour:", self, 'ehour')
                    newrow(layout, "End day of year:", self, 'edoy')
                    newrow(layout, "Interval (hours):", self, 'interval')
                newrow(layout, "Turbidity", self, 'turb')
            elif self.skymenu == '4':
                row = layout.row()
                row.label("HDR file:")
                row.operator('node.hdrselect', text = 'HDR select').nodeid = self['nodeid']
                row = layout.row()
                row.prop(self, 'hdrname')
            elif self.skymenu == '5':
                row = layout.row()
                row.label("Radiance file:")
                row.operator('node.skyselect', text = 'Sky select').nodeid = self['nodeid']
                row = layout.row()
                row.prop(self, 'skyname')
            row = layout.row()

            if self.skymenu not in ('4', '6'):
                newrow(layout, 'HDR:', self, 'hdr')

        elif self.contextmenu == 'Compliance':
            newrow(layout, "Standard:", self, 'canalysismenu')
            if self.canalysismenu == '0':
                newrow(layout, "Building type:", self, 'bambuildmenu')
                newrow(layout, "Storeys:", self, 'buildstorey')
                newrow(layout, 'HDR:', self, 'hdr')
                
        elif self.contextmenu == 'CBDM':
            row = layout.row()
            row.label("Analysis Type:")
            row.prop(self, 'cbanalysismenu')
            newrow(layout, 'Start month:', self, "startmonth")
            newrow(layout, 'End month:', self, "endmonth")
            if self.cbanalysismenu in ('2', '4'):
               newrow(layout, 'Weekdays only:', self, 'weekdays')
               newrow(layout, 'Start hour:', self, 'cbdm_start_hour')
               newrow(layout, 'End hour:', self, 'cbdm_end_hour')
               if self.cbanalysismenu =='2':
                   newrow(layout, 'Min Lux level:', self, 'dalux')
               if self.cbanalysismenu =='4':
                   newrow(layout, 'Fell short (Max):', self, 'damin')
                   newrow(layout, 'Supplementry (Max):', self, 'dasupp')
                   newrow(layout, 'Autonomous (Max):', self, 'daauto')
                   
            if self.cbanalysismenu in ('0', '1'):
                newrow(layout, 'Source file:', self, 'sourcemenu')
            else:
                newrow(layout, 'Source file:', self, 'sourcemenu2')
            row = layout.row()
            row.label('Source file:')
            row = layout.row()
            if self.sourcemenu2 == '1' and self.cbanalysismenu in ('2', '3', '4'):
                row.operator('node.mtxselect', text = 'Select MTX').nodeid = self['nodeid']
                row = layout.row()
                row.prop(self, 'mtxname')
            if self.sourcemenu == '1' and self.cbanalysismenu in ('0', '1'):
                row.operator('node.hdrselect', text = 'Select HDR').nodeid = self['nodeid']
                row = layout.row()
                row.prop(self, 'hdrname')
            else:
                newrow(layout, 'HDR:', self, 'hdr')
        
        if self.contextmenu == 'Basic':
            if int(self.skymenu) > 2 or (int(self.skymenu) < 3 and self.inputs['Location in'].links):
                row = layout.row()
                row.operator("node.liexport", text = "Export").nodeid = self['nodeid']
        elif self.contextmenu == 'Compliance':
            row = layout.row()
            row.operator("node.liexport", text = "Export").nodeid = self['nodeid']
        elif (self.contextmenu == 'CBDM' and self.sourcemenu == '1') or \
            (self.contextmenu == 'CBDM' and self.sourcemenu == '0' and self.inputs['Location in'].links and self.inputs['Location in'].links[0].from_node.loc == '1'):
            row = layout.row()
            row.operator("node.liexport", text = "Export").nodeid = self['nodeid']            
    
    def update(self):
        socklink(self.outputs['Context out'], self['nodeid'].split('@')[1])
        if self.inputs.get('Location in'):
            self.nodeupdate(bpy.context) 
    
    def preexport(self):
        self.starttime = datetime.datetime(datetime.datetime.now().year, 1, 1, int(self.shour), int((self.shour - int(self.shour))*60)) + datetime.timedelta(self.sdoy - 1) if self['skynum'] < 3 else datetime.datetime(datetime.datetime.now().year, 1, 1, 12)
        self.endtime = datetime.datetime(2013, 1, 1, int(self.ehour), int((self.ehour - int(self.ehour))*60)) + datetime.timedelta(self.edoy - 1) if self.animated and self['skynum'] < 3 else self.starttime
        self['skynum'] = int(self.skymenu)
        self['hours'] = 0 if not self.animated or int(self.skymenu) > 2  else (self.endtime-self.starttime).seconds/3600
        self['epwbase'] = os.path.splitext(os.path.basename(self.inputs['Location in'].links[0].from_node.weather))
        self.outputs['Context out']['Text'] = {}
        
    def export(self, scene, export_op):        
        self.startframe = self.startframe if self.animated and self.contextmenu == 'Basic' and self.banalysismenu in ('0', '1', '2') else scene.frame_current 
        self['endframe'] = self.startframe + int(((24 * (self.edoy - self.sdoy) + self.ehour - self.shour)/self.interval)) if self.contextmenu == 'Basic' and self.banalysismenu in ('0', '1', '2') and self.animated else scene.frame_current
        self['mtxfile'] = ''
        if self.contextmenu == "Basic":        
            if self['skynum'] < 4:
                locnode = self.inputs['Location in'].links[0].from_node if self['skynum'] < 3  else 0
                self['skytypeparams'] = ("+s", "+i", "-c", "-b 22.86 -c")[self['skynum']]
                for f, frame in enumerate(range(self.startframe, self['endframe'] + 1)):
                    if self['skynum'] < 2:
                        if frame == self.startframe:
                            if 'SUN' in [ob.data.type for ob in scene.objects if ob.type == 'LAMP' and ob.get('VIType')]:
                                sun = [ob for ob in scene.objects if ob.get('VIType') == 'Sun'][0]
                            else:
                                bpy.ops.object.lamp_add(type='SUN')
                                sun = bpy.context.object
                                sun['VIType'] = 'Sun'
                    if self.hdr == True:
                        hdrexport(scene, f, frame, self, sunexport(scene, self, locnode, f) + skyexport(self['skynum']))
                    self.outputs['Context out']['Text'][str(frame)] = sunexport(scene, self, locnode, f) + skyexport(self['skynum'])

            elif self['skynum'] == 4:
                if self.hdrname not in bpy.data.images:
                    bpy.data.images.load(self.hdrname)
                self.outputs['Context out']['Text'][str(scene['liparams']['fs'])] = hdrsky(self.hdrname)
            elif self['skynum'] == 5:
                shutil.copyfile(self.radname, "{}-0.sky".format(scene['viparams']['filebase']))
                with open(self.radname, 'r') as radfiler:
                    self.outputs['Context out']['Text'][str(scene['liparams']['fs'])] =  [radfiler.read()]
                hdrexport(scene, 0, 0, self, self['skyfiles'][0])
            elif self['skynum'] == 6:
                self.outputs['Context out']['Text'][str(scene.frame_current)] = ''
        
        elif self.contextmenu == "CBDM":
            if (self.cbanalysismenu in ('0', '1') and self.sourcemenu == '0') or (self.cbanalysismenu in ('2', '3', '4') and self.sourcemenu2 == '0'):
                self['mtxfile'] = cbdmmtx(self, scene, self.inputs['Location in'].links[0].from_node, export_op)
            elif self.cbanalysismenu in ('2', '3', '4') and self.sourcemenu == '1':
                self['mtxfile'] = self.mtxname

            if self.cbanalysismenu in ('0', '1'):
                self.outputs['Context out']['Text'][str(scene['liparams']['fs'])] = cbdmhdr(self, scene)
            else:
                self.outputs['Context out']['Text'][str(scene['liparams']['fs'])] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"

                if self.sourcemenu2 == '0':
                    with open("{}.mtx".format(os.path.join(scene['viparams']['newdir'], self['epwbase'][0])), 'r') as mtxfile:
                        self.outputs['Context out']['Options']['MTX'] = mtxfile.read()
                else:
                    with open(self.mtxname, 'r') as mtxfile:
                        self.outputs['Context out']['Text'][str(scene['liparams']['fs'])] = mtxfile.read()

        elif self.contextmenu == "Compliance":
            self['skytypeparams'] = ("-b 22.86 -c", "-b 22.86 -c", "+s")[int(self.canalysismenu)]
            if self.canalysismenu in ('0', '1'):
                self.starttime = datetime.datetime(datetime.datetime.now().year, 1, 1, 12)
                locnode = 0
                if self.hdr == True:
                    hdrexport(scene, 0, 0, self, self['skyfiles'][0])
            else:
                self.starttime = datetime.datetime(datetime.datetime.now().year, 9, 11, 9)
            self.outputs['Context out']['Text'][str(scene['liparams']['fs'])] = sunexport(scene, self, locnode, 0) + skyexport(self['skynum'])
    
    def postexport(self):    
        typedict = {'Basic': self.banalysismenu, 'Compliance': self.canalysismenu, 'CBDM': self.cbanalysismenu}
        unitdict = {'Basic': ("Lux", '')[int(self.banalysismenu)], 'Compliance': ('DF (%)', 'DF (%)')[int(self.canalysismenu)], 'CBDM': ('kLuxHours', 'kWh/m'+ u'\u00b2', 'DA (%)', 'kW', 'UDI-a (%)')[int(self.cbanalysismenu)]}
        self.outputs['Context out']['Options'] = {'Context': self.contextmenu, 'Type': typedict[self.contextmenu], 'fs': self.startframe, 'fe': self['endframe'],
                    'anim': self.animated, 'shour': self.shour, 'sdoy': self.sdoy, 'interval': self.interval, 'bambuild': self.bambuildmenu, 'canalysis': self.canalysismenu, 'storey': self.buildstorey,
                    'cbanalysis': self.cbanalysismenu, 'unit': unitdict[self.contextmenu], 'damin': self.damin, 'dalux': self.dalux, 'dasupp': self.dasupp, 'daauto': self.daauto, 'cbdm_sh': self.cbdm_start_hour, 
                    'cbdm_eh': self.cbdm_end_hour, 'weekdays': (7, 5)[self.weekdays], 'sourcemenu': (self.sourcemenu, self.sourcemenu2)[self.cbanalysismenu not in ('2', '3', '4')],
                    'mtxfile': self['mtxfile']}
        nodecolour(self, 0)
        self['exportstate'] = [str(x) for x in (self.contextmenu, self.banalysismenu, self.canalysismenu, self.cbanalysismenu, 
                   self.animated, self.skymenu, self.shour, self.sdoy, self.startmonth, self.endmonth, self.damin, self.dasupp, self.dalux, self.daauto,
                   self.ehour, self.edoy, self.interval, self.hdr, self.hdrname, self.skyname, self.resname, self.turb, self.mtxname, self.cbdm_start_hour,
                   self.cbdm_end_hour, self.bambuildmenu)]

#class ViCombine(bpy.types.Node, ViNodes):
#    '''Node for input combination'''
#    bl_idname = 'ViCombine'
#    bl_label = 'VI Combine'
#    bl_icon = 'LAMP'
#
#    def init(self, context):
#        self.inputs.new('ViText', 'Input 1')
#        self.inputs.new('ViText', 'Input 2')
#        self.outputs.new('ViText', 'Out')
#    
#    def update(self):
#        frange = []
#        links = (list(self.inputs['Input 1'].links[:]) + list(self.inputs['Input 2'].links[:]))
#        for link in links:
#            frange += [int(k) for k in link.from_socket['Text'].keys()]
#        self.outputs['Out']['Text'] = {str(f): '' for f in set(frange)}
#
#        for frame in set(frange):
#            for link in links:
#                if str(frame) in link.from_socket['Text']:
#                    self.outputs['Out']['Text'][str(frame)] += link.from_socket['Text'][str(frame)]
#                elif frame < min([int(k) for k in link.from_socket['Text'].keys()]):
#                    self.outputs['Out']['Text'][str(frame)] += link.from_socket['Text'][str(min([int(k) for k in link.from_socket['Text'].keys()]))]
#                elif frame > max([int(k) for k in link.from_socket['Text'].keys()]):
#                    self.outputs['Out']['Text'][str(frame)] += link.from_socket['Text'][str(max([int(k) for k in link.from_socket['Text'].keys()]))]
#                                   
class ViLiSNode(bpy.types.Node, ViNodes):
    '''Node describing a LiVi simulation'''
    bl_idname = 'ViLiSNode'
    bl_label = 'LiVi Simulation'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.cusacc, self.simacc, self.csimacc, self.pmap, self.pmapcno, self.pmapgno)])
        
    simacc = bpy.props.EnumProperty(items=[("0", "Low", "Low accuracy and high speed (preview)"),("1", "Medium", "Medium speed and accuracy"), ("2", "High", "High but slow accuracy"),("3", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0", update = nodeupdate)
    csimacc = bpy.props.EnumProperty(items=[("0", "Custom", "Edit Radiance parameters"), ("1", "Initial", "Initial accuracy for this metric"), ("2", "Final", "Final accuracy for this metric")],
            name="", description="Simulation accuracy", default="1", update = nodeupdate)
    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="", update = nodeupdate)
    rtracebasic = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-as", 128, 512, 2048), ("-aa", 0, 0, 0), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.0001, 0.00001, 0.000002), ("-lr", 2, 3, 4))
    rtraceadvance = (("-ab", 3, 5), ("-ad", 2048, 4096), ("-as", 1024, 2048), ("-aa", 0.0, 0.0), ("-dj", 0.7, 1), ("-ds", 0.5, 0.15), ("-dr", 2, 3), ("-ss", 2, 5), ("-st", 0.75, 0.1), ("-lw", 0.00001, 0.000002), ("-lr", 3, 5))
    rvubasic = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-as", 128, 512, 2048), ("-aa", 0, 0, 0), ("-dj", 0, 0.7, 1), ("-ds", 0.5, 0.15, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.0001, 0.00001, 0.0000002), ("-lr", 3, 3, 4))
    rvuadvance = (("-ab", 3, 5), ("-ad", 2048, 4096), ("-as", 1024, 2048), ("-aa", 0.0, 0.0), ("-dj", 0.7, 1), ("-ds", 0.5, 0.15), ("-dr", 2, 3), ("-ss", 2, 5), ("-st", 0.75, 0.1), ("-lw", 0.00001, 0.000002), ("-lr", 3, 5))
    pmap = bpy.props.BoolProperty(name = '', default = False)
    pmapgno = bpy.props.IntProperty(name = '', default = 50000)
    pmapcno = bpy.props.IntProperty(name = '', default = 0)
    run = bpy.props.IntProperty(default = 0)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self['simdict'] = {'Basic': 'simacc', 'Compliance':'csimacc', 'CBDM':'csimacc'}
        self.inputs.new('ViLiG', 'Geometry in')
        self.inputs.new('ViLiC', 'Context in')
        self.outputs.new('ViR', 'Results out')
        self.outputs.new('ViText', 'File out')
        self.outputs['Results out'].hide = True
        nodecolour(self, 1)
        self['maxres'], self['minres'], self['avres'], self['exportstate'] = {}, {}, {}, ''
        
    def draw_buttons(self, context, layout): 
        scene = context.scene
        if self.inputs['Geometry in'].links and self.inputs['Context in'].links:
            row = layout.row()
            row.label(text = 'Frames: {} - {}'.format(min([c['fs'] for c in (self.inputs['Context in'].links[0].from_socket['Options'], self.inputs['Geometry in'].links[0].from_socket['Options'])]), max([c['fe'] for c in (self.inputs['Context in'].links[0].from_socket['Options'], self.inputs['Geometry in'].links[0].from_socket['Options'])])))
            cinsock = self.inputs['Context in'].links[0].from_socket
            newrow(layout, 'Photon map:', self, 'pmap')
            if self.pmap:
               newrow(layout, 'Global photons:', self, 'pmapgno')
               newrow(layout, 'Caustic photons:', self, 'pmapcno')
            row = layout.row()
            row.label("Accuracy:")
            
            row.prop(self, self['simdict'][cinsock['Options']['Context']])
            if (self.simacc == '3' and cinsock['Options']['Context'] == 'Basic') or (self.csimacc == '0' and cinsock['Options']['Context'] in ('Compliance', 'CBDM')):
               newrow(layout, "Radiance parameters:", self, 'cusacc')
            if self.run and (self['coptions']['Context'] == 'Basic' and cinsock['Options']['Type'] == '1'):
                row = layout.row()
                row.label('Calculating'+(self.run%10 *'-'))
            else:
                row = layout.row()
                row.operator("node.radpreview", text = 'Preview').nodeid = self['nodeid']
                if cinsock['Options']['Context'] == 'Basic' and cinsock['Options']['Type'] == '1':
                    row.operator("node.liviglare", text = 'Calculate').nodeid = self['nodeid']
                elif [o.name for o in scene.objects if o.name in scene['liparams']['livic']]:
                    row.operator("node.livicalc", text = 'Calculate').nodeid = self['nodeid']

    def update(self):
        if self.outputs.get('Data out'):
            socklink(self.outputs['Data out'], self['nodeid'].split('@')[1])
        self.run = 0
    
    def preexport(self):
        self['coptions'] = self.inputs['Context in'].links[0].from_socket['Options']
        self['goptions'] = self.inputs['Geometry in'].links[0].from_socket['Options']
        self['resdict'], self['allresdict'], self['radfiles'] = {}, {}, {}
        if self['coptions']['Context'] == 'Basic':
            self['radparams'] = self.cusacc if self.simacc == '3' else (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in self.rtracebasic], [n[int(self.simacc)+1] for n in self.rtracebasic]))
        else:
            self['radparams'] = self.cusacc if self.csimacc == '0' else (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in self.rtraceadvance], [n[int(self.csimacc)] for n in self.rtraceadvance]))
           
    def postexport(self):
        self['exportstate'] = [str(x) for x in (self.cusacc, self.simacc, self.csimacc, self.pmap, self.pmapcno, self.pmapgno)]
        self.outputs['Results out'].hide = False
        nodecolour(self, 0)

class ViSPNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite sun path'''
    bl_idname = 'ViSPNode'
    bl_label = 'VI Sun Path'
    bl_icon = 'LAMP'

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViLoc', 'Location in')
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        if self.inputs['Location in'].links:
            row = layout.row()
            row.operator("node.sunpath", text="Create Sun Path").nodeid = self['nodeid']

    def export(self):
        nodecolour(self, 0)

class ViSSNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite shadow study'''
    bl_idname = 'ViSSNode'
    bl_label = 'VI Shadow Study'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.animmenu, self.startmonth, self.endmonth, self.starthour, self.endhour, self.interval, self.cpoint, self.offset)])

    animtype = [('Static', "Static", "Simple static analysis"), ('Geometry', "Geometry", "Animated geometry analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeupdate)
    starthour = bpy.props.IntProperty(name = '', default = 1, min = 1, max = 24, description = 'Start hour')
    endhour = bpy.props.IntProperty(name = '', default = 24, min = 1, max = 24, description = 'End hour')
    interval = bpy.props.FloatProperty(name = '', default = 1, min = 0.1, max = 24, description = 'Interval')
    startmonth = bpy.props.IntProperty(name = '', default = 1, min = 1, max = 12, description = 'Start Month', update = nodeupdate)
    endmonth = bpy.props.IntProperty(name = '', default = 12, min = 1, max = 12, description = 'End Month', update = nodeupdate)
    cpoint = bpy.props.EnumProperty(items=[("0", "Faces", "Export faces for calculation points"),("1", "Vertices", "Export vertices for calculation points"), ],
            name="", description="Specify the calculation point geometry", default="0", update = nodeupdate)
    offset = bpy.props.FloatProperty(name="", description="Calc point offset", min=0.001, max=1, default=0.01, update = nodeupdate)
#    running = bpy.props.IntProperty(name = '', default = 0, min = 0, max = 100, description = '')

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViLoc', 'Location in')
        self['exportstate'] = ''
        self['goptions'] = {}
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        if nodeinputs(self):
            newrow(layout, 'Animation:', self, "animmenu")
            newrow(layout, 'Start month:', self, "startmonth")
            newrow(layout, 'End month:', self, "endmonth")
            newrow(layout, 'Start hour:', self, "starthour")
            newrow(layout, 'End hour:', self, "endhour")
            newrow(layout, 'Interval:', self, "interval")
            newrow(layout, 'Result point:', self, "cpoint")
            newrow(layout, 'Offset:', self, 'offset')
            row = layout.row()
#            if not self.running:
            row.operator("node.shad", text = 'Calculate').nodeid = self['nodeid']
#            else:
#                row.label('{}% Completed'.format(self.running))

    def preexport(self):
#        self['minres'], self['maxres'], self['avres'] = {}, {}, {}
        self['goptions']['offset'] = self.offset

    def postexport(self, scene):
        nodecolour(self, 0)
        self['exportstate'] = [str(x) for x in (self.animmenu, self.startmonth, self.endmonth, self.starthour, self.endhour, self.interval, self.cpoint, self.offset)]
        

class ViWRNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite wind rose generator'''
    bl_idname = 'ViWRNode'
    bl_label = 'VI Wind Rose'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.wrtype, self.startmonth, self.endmonth)])
        if self.startmonth > self.endmonth:
            self.endmonth = self.startmonth

    wrtype = bpy.props.EnumProperty(items = [("0", "Hist 1", "Stacked histogram"), ("1", "Hist 2", "Stacked Histogram 2"), ("2", "Cont 1", "Filled contour"), ("3", "Cont 2", "Edged contour"), ("4", "Cont 3", "Lined contour")], name = "", default = '0', update = nodeupdate)
    startmonth = bpy.props.IntProperty(name = '', default = 1, min = 1, max = 12, description = 'Start Month', update = nodeupdate)
    endmonth = bpy.props.IntProperty(name = '', default = 12, min = 1, max = 12, description = 'End Month', update = nodeupdate)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViLoc', 'Location in')
        self['exportstate'] = ''
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        if nodeinputs(self) and self.inputs[0].links[0].from_node.loc == '1':
            newrow(layout, 'Type:', self, "wrtype")
            newrow(layout, 'Start month :', self, "startmonth")
            newrow(layout, 'End month:', self, "endmonth")
            row = layout.row()
            row.operator("node.windrose", text="Create Wind Rose").nodeid = self['nodeid']
        else:
            row = layout.row()
            row.label('Location node error')

    def export(self):
        nodecolour(self, 0)
        self['exportstate'] = [str(x) for x in (self.wrtype, self.startmonth, self.endmonth)]

class ViGExEnNode(bpy.types.Node, ViNodes):
    '''Node describing an EnVi Geometry Export'''
    bl_idname = 'ViGExEnNode'
    bl_label = 'EnVi Geometry'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in [self.animated]])

    animated = bpy.props.BoolProperty(name="", description="Animated analysis", update = nodeupdate)
    fs = bpy.props.IntProperty(name="", description="Start frame", default = 0, min = 0, update = nodeupdate)
    fe = bpy.props.IntProperty(name="", description="Start frame", default = 0, min = 0, update = nodeupdate)
#    epfiles = []

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViEnG', 'Geometry out')
        self['exportstate'] = ''
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
#        row = layout.row()
#        row.label('Animation:')
#        row.prop(self, 'animated')
#        if self.animated:
#            newrow(layout, 'Start frame:', self, 'fs')
#            newrow(layout, 'End frame:', self, 'fe')
        row = layout.row()
        row.operator("node.engexport", text = "Export").nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Geometry out'], self['nodeid'].split('@')[1])
        
    def preexport(self, scene):
        scene.frame_start = self.fs if self.animated else scene.frame_current
        scene.frame_end = self.fe if self.animated else scene.frame_current
        scene['enparams']['fs'] = scene.frame_start
        scene['enparams']['fe'] = scene.frame_end
                
    def postexport(self):
        self['exportstate'] = [str(x) for x in [self.animated]]
        nodecolour(self, 0)

class ViExEnNode(bpy.types.Node, ViNodes):
    '''Node describing an EnergyPlus export'''
    bl_idname = 'ViExEnNode'
    bl_label = 'EnVi Export'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.loc, self.terrain, self.timesteps)])

    loc = bpy.props.StringProperty(name="", description="Identifier for this project", default="", update = nodeupdate)
    terrain = bpy.props.EnumProperty(items=[("0", "City", "Towns, city outskirts, centre of large cities"),
                   ("1", "Urban", "Urban, Industrial, Forest"),("2", "Suburbs", "Rough, Wooded Country, Suburbs"),
                    ("3", "Country", "Flat, Open Country"),("4", "Ocean", "Ocean, very flat country")],
                    name="", description="Specify the surrounding terrain", default="0", update = nodeupdate)

    addonpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
    matpath = addonpath+'/EPFiles/Materials/Materials.data'
    startmonth = bpy.props.IntProperty(name = '', default = 1, min = 1, max = 12, description = 'Start Month', update = nodeupdate)
    endmonth = bpy.props.IntProperty(name = '', default = 12, min = 1, max = 12, description = 'End Month', update = nodeupdate)
    sdoy = bpy.props.IntProperty(name = "", description = "Day of simulation", min = 1, max = 365, default = 1, update = nodeupdate)
    edoy = bpy.props.IntProperty(name = "", description = "Day of simulation", min = 1, max = 365, default = 365, update = nodeupdate)
    timesteps = bpy.props.IntProperty(name = "", description = "Time steps per hour", min = 1, max = 60, default = 1, update = nodeupdate)
    restype= bpy.props.EnumProperty(items = [("0", "Zone Thermal", "Thermal Results"), ("1", "Comfort", "Comfort Results"), ("2", "Zone Ventilation", "Zone Ventilation Results"), ("3", "Ventilation Link", "ZoneVentilation Results")],
                                   name="", description="Specify the EnVi results category", default="0", update = nodeupdate)

    (resaam, resaws, resawd, resah, resasm, restt, resh, restwh, restwc, reswsg, rescpp, rescpm, resvls, resvmh, resim, resiach, resco2, resihl, resl12ms,
     reslof, resmrt, resocc, resh, resfhb, ressah, ressac, reshrhw) = resnameunits()

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViEnC', 'Context out')
        self.inputs.new('ViEnG', 'Geometry in')
        self.inputs.new('ViLoc', 'Location in')
        self['exportstate'] = ''
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, "Name/location", self, "loc")
        row = layout.row()
        row.label(text = 'Terrain:')
        col = row.column()
        col.prop(self, "terrain")
        newrow(layout, 'Start month:', self, "startmonth")
        newrow(layout, 'End month:', self, "endmonth")
        newrow(layout, 'Time-steps/hour', self, "timesteps")
        row = layout.row()
        row.label(text = 'Results Category:')
        col = row.column()
        col.prop(self, "restype")
        resdict = enresprops('')
        for rprop in resdict[self.restype]:
            if not rprop:
                row = layout.row()
            else:
                row.prop(self, rprop)
        if all([s.links for s in self.inputs]) and not any([s.links[0].from_node.use_custom_color for s in self.inputs]):
            row = layout.row()
            row.operator("node.enexport", text = 'Export').nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Context out'], self['nodeid'].split('@')[1])

    def export(self):
        nodecolour(self, 0)
        self['exportstate'] = [str(x) for x in (self.loc, self.terrain, self.timesteps)]

class ViEnSimNode(bpy.types.Node, ViNodes):
    '''Node describing an EnergyPlus simulation'''
    bl_idname = 'ViEnSimNode'
    bl_label = 'EnVi Simulation'
    bl_icon = 'LAMP'

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViEnC', 'Context in')
        self.outputs.new('ViR', 'Results out')
        self['exportstate'] = ''
        self['Start'], self['End'] = 1, 365
        nodecolour(self, 1)

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [self.resname])
        if self.inputs['Context in'].is_linked:
            self.resfilename = os.path.join(self.inputs['Context in'].links[0].from_node.newdir, self.resname+'.eso')

    resname = bpy.props.StringProperty(name="", description="Base name for the results files", default="results", update = nodeupdate)
    resfilename = bpy.props.StringProperty(name = "", default = 'results')
    dsdoy, dedoy, run  = bpy.props.IntProperty(), bpy.props.IntProperty(), bpy.props.IntProperty(min = -1, default = -1)
#    animated = bpy.props.BoolProperty(name = '', description = 'Enable EnergyPlus animation', default = 0)

    def draw_buttons(self, context, layout):
        if self.run > -1:
            row = layout.row()
            row.label('Calculating {}%'.format(self.run))
        elif self.inputs['Context in'].links and not self.inputs['Context in'].links[0].from_node.use_custom_color:
#            newrow(layout, 'Animation:', self, 'animated')
            newrow(layout, 'Results name:', self, 'resname')
            row = layout.row()
            row.operator("node.ensim", text = 'Calculate').nodeid = self['nodeid']

    def update(self):
        if self.outputs.get('Results out'):
            socklink(self.outputs['Results out'], self['nodeid'].split('@')[1])

    def sim(self):
        innode = self.inputs['Context in'].links[0].from_node
        self.dsdoy = innode.sdoy # (locnode.startmonthnode.sdoy
        self.dedoy = innode.edoy
#        self.dsdoy.min =  self.dsdoy
#        self.dsdoy.max =  self.dedoy
#        self["_RNA_UI"] = {"Start": {"min":resnode.dsdoy, "max":resnode.dedoy}, "End": {"min":resnode.dsdoy, "max":resnode.dedoy}}
        self["_RNA_UI"] = {"Start": {"min":innode.sdoy, "max":innode.edoy}, "End": {"min":innode.sdoy, "max":innode.edoy}}
        self['Start'], self['End'] = innode.sdoy, innode.edoy

class ViEnRFNode(bpy.types.Node, ViNodes):
    '''Node for EnergyPlus results file selection'''
    bl_idname = 'ViEnRFNode'
    bl_label = 'EnVi Results File'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [self.resfilename])

    resfilename = bpy.props.StringProperty(name="", description="Name of the EnVi results file", default="", update = nodeupdate)
    dsdoy, dedoy = bpy.props.IntProperty(), bpy.props.IntProperty()

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViR', 'Results out')
        self['exportstate'] = ''
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('ESO file:')
        row.operator('node.esoselect', text = 'Select file').nodeid = self['nodeid']
        row = layout.row()
        row.prop(self, 'resfilename')
        row.operator("node.fileprocess", text = 'Process file').nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Results out'], self['nodeid'].split('@')[1])

    def export(self):
        self['exportstate'] = [self.resfilename]
        nodecolour(self, 0)

class ViEnInNode(bpy.types.Node, ViNodes):
    '''Node for EnergyPlus input file selection'''
    bl_idname = 'ViEnInNode'
    bl_label = 'EnVi Input File'

    def nodeupdate(self, context):
        oblist = []
        self.outputs['Context out'].hide = False
        shutil.copyfile(self.idffilename, context.scene['viparams']['idf_file'])
#        Popen('{} {} {}'.format(context.scene['viparams']['cp'], self.idffilename, context.scene['viparams']['idf_file']), shell = True)
        with open(self.idffilename, 'r', errors='ignore') as idff:
            idfflines = idff.readlines()
            for l, line in enumerate(idfflines):
                if line.split(',')[0].lstrip(' ').upper() == 'ZONE' and not line.split(',')[1].strip('\n'):
                    oblist.append(idfflines[l+1].split(',')[0].lstrip(' '))
                if line.split(',')[0].lstrip(' ').upper() == 'RUNPERIOD':
                    self.sdoy = datetime.datetime(datetime.datetime.now().year, int(idfflines[l+2].split(',')[0].lstrip(' ')), int(idfflines[l+3].split(',')[0].lstrip(' '))).timetuple().tm_yday
                    self.edoy = datetime.datetime(datetime.datetime.now().year, int(idfflines[l+4].split(',')[0].lstrip(' ')), int(idfflines[l+5].split(',')[0].lstrip(' '))).timetuple().tm_yday
        self.newdir = bpy.context.scene['viparams']['newdir']
        self['oblist'] = oblist

    idffilename = bpy.props.StringProperty(name="", description="Name of the EnVi results file", default="", update = nodeupdate)
    sdoy = bpy.props.IntProperty(name = '', default = 1, min = 1, max = 365)
    edoy = bpy.props.IntProperty(name = '', default = 365, min = 1, max = 365)
    newdir = bpy.props.StringProperty()

    def init(self, context):
        self.outputs.new('ViEnC', 'Context out')
        self.outputs['Context out'].hide = True
        self['nodeid'] = nodeid(self)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('ESO file:')
        row.operator('node.idfselect', text = 'Select IDF file').nodeid = self['nodeid']
        row = layout.row()
        row.prop(self, 'idffilename')

    def update(self):
        socklink(self.outputs['Context out'], self['nodeid'].split('@')[1])

class ViResSock(bpy.types.NodeSocket):
    '''Results socket'''
    bl_idname = 'ViEnRIn'
    bl_label = 'Results axis'
    valid = ['Vi Results']

    def draw(self, context, layout, node, text):
        row = layout.row()
        row.prop(self, "rtypemenu", text = text)
        if self.links:
            typedict = {"Time": [], "Climate": ['climmenu'], "Zone": ("zonemenu", "zonermenu"), "Linkage":("linkmenu", "linkrmenu"), "External node":("enmenu", "enrmenu")}
            for rtype in typedict[self.rtypemenu]:
                row.prop(self, rtype)
            if self.node.timemenu in ('1', '2') and self.rtypemenu !='Time':
                row = layout.row()
                row.prop(self, "statmenu")
            if self.rtypemenu != 'Time':
                row.prop(self, 'multfactor')

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

class ViResUSock(bpy.types.NodeSocket):
    '''Vi unlinked esults socket'''
    bl_idname = 'ViEnRInU'
    bl_label = 'Axis'
    valid = ['Vi Results']

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

    def draw(self, context, layout, node, text):
        layout.label(self.bl_label)

class ViEnRNode(bpy.types.Node, ViNodes):
    '''Node for 2D results plotting'''
    bl_idname = 'ViChNode'
    bl_label = 'VI Chart'

    ctypes = [("0", "Line/Scatter", "Line/Scatter Plot"), ("1", "Bar", "Bar Chart")]
    dsh = bpy.props.IntProperty(name = "Start", description = "", min = 1, max = 24, default = 1)
    deh = bpy.props.IntProperty(name = "End", description = "", min = 1, max = 24, default = 24)
    charttype = bpy.props.EnumProperty(items = ctypes, name = "Chart Type", default = "0")
    timemenu = bpy.props.EnumProperty(items=[("0", "Hourly", "Hourly results"),("1", "Daily", "Daily results"), ("2", "Monthly", "Monthly results")],
                name="", description="Results frequency", default="0")
    bl_width_max = 800

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new("ViEnRXIn", "X-axis")
        self.inputs.new("ViEnRY1In", "Y-axis 1")
        self.inputs["Y-axis 1"].hide = True
        self.inputs.new("ViEnRY2In", "Y-axis 2")
        self.inputs["Y-axis 2"].hide = True
        self.inputs.new("ViEnRY3In", "Y-axis 3")
        self.inputs["Y-axis 3"].hide = True
        self['Start'], self['End'] = 1, 365
        self.update()

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Day:")
        row.prop(self, '["Start"]')
        row.prop(self, '["End"]')
        row = layout.row()
        row.label("Hour:")
        row.prop(self, "dsh")
        row.prop(self, "deh")
        row = layout.row()
        row.prop(self, "charttype")
        row.prop(self, "timemenu")

        if self.inputs['X-axis'].links and self.inputs['Y-axis 1'].links and 'NodeSocketUndefined' not in [sock.bl_idname for sock in self.inputs if sock.links]:
            layout.operator("node.chart", text = 'Create plot').nodeid = self['nodeid']
        row = layout.row()
        row.label("------------------")

    def update(self):
        if not self.inputs['X-axis'].links:
            class ViEnRXIn(ViResUSock):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRXIn'
                bl_label = 'X-axis'

                valid = ['Vi Results']
        else:
            innode = self.inputs['X-axis'].links[0].from_node
            self["_RNA_UI"] = {"Start": {"min":innode.dsdoy, "max":innode.dedoy}, "End": {"min":innode.dsdoy, "max":innode.dedoy}}
            self['Start'], self['End'] = innode.dsdoy, innode.dedoy

            if self.inputs.get('Y-axis 1'):
                self.inputs['Y-axis 1'].hide = False

            class ViEnRXIn(ViResSock):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRXIn'
                bl_label = 'X-axis'

                if innode['rtypes']:
                    (valid, statmenu, rtypemenu, climmenu, zonemenu, zonermenu, linkmenu, linkrmenu, enmenu, enrmenu, multfactor) = retrmenus(innode)

        bpy.utils.register_class(ViEnRXIn)

        if self.inputs.get('Y-axis 1'):
            if not self.inputs['Y-axis 1'].links:
                class ViEnRY1In(ViResUSock):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY1In'
                    bl_label = 'Y-axis 1'

                if self.inputs.get('Y-axis 2'):
                    self.inputs['Y-axis 2'].hide = True
            else:
                innode = self.inputs['Y-axis 1'].links[0].from_node

                class ViEnRY1In(ViResSock):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY1In'
                    bl_label = 'Y-axis 1'
                    (valid, statmenu, rtypemenu, climmenu, zonemenu, zonermenu, linkmenu, linkrmenu, enmenu, enrmenu, multfactor) = retrmenus(innode)

                self.inputs['Y-axis 2'].hide = False
            bpy.utils.register_class(ViEnRY1In)

        if self.inputs.get('Y-axis 2'):
            if not self.inputs['Y-axis 2'].links:
                class ViEnRY2In(ViResUSock):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY2In'
                    bl_label = 'Y-axis 2'

                if self.inputs.get('Y-axis 3'):
                    self.inputs['Y-axis 3'].hide = True
            else:
                innode = self.inputs[2].links[0].from_node

                class ViEnRY2In(ViResSock):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY2In'
                    bl_label = 'Y-axis 2'

                    (valid, statmenu, rtypemenu, climmenu, zonemenu, zonermenu, linkmenu, linkrmenu, enmenu, enrmenu, multfactor) = retrmenus(innode)

                self.inputs['Y-axis 3'].hide = False

            bpy.utils.register_class(ViEnRY2In)

        if self.inputs.get('Y-axis 3'):
            if not self.inputs['Y-axis 3'].links:
                class ViEnRY3In(ViResUSock):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY3In'
                    bl_label = 'Y-axis 3'
            else:
                innode = self.inputs[3].links[0].from_node

                class ViEnRY3In(ViResSock):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY3In'
                    bl_label = 'Y-axis 3'

                    (valid, statmenu, rtypemenu, climmenu, zonemenu, zonermenu, linkmenu, linkrmenu, enmenu, enrmenu, multfactor) = retrmenus(innode)

            bpy.utils.register_class(ViEnRY3In)

class ViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ViN'

class ViLocSock(bpy.types.NodeSocket):
    '''Vi Location socket'''
    bl_idname = 'ViLoc'
    bl_label = 'Location socket'
    valid = ['Location']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

class ViLiWResOut(bpy.types.NodeSocket):
    '''LiVi irradiance out socket'''
    bl_idname = 'LiViWOut'
    bl_label = 'LiVi W/m2 out'

    valid = ['LiViWatts']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)
        
class ViLiCBDMSock(bpy.types.NodeSocket):
    '''LiVi irradiance out socket'''
    bl_idname = 'ViLiCBDM'
    bl_label = 'LiVi CBDM context socket'

    valid = ['CBDM']
#    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 1.0, 0.75)
    

class ViLiGSock(bpy.types.NodeSocket):
    '''Lighting geometry socket'''
    bl_idname = 'ViLiG'
    bl_label = 'Geometry'

    valid = ['LiVi Geometry', 'text']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.3, 0.17, 0.07, 0.75)

class ViLiCSock(bpy.types.NodeSocket):
    '''Lighting context in socket'''
    bl_idname = 'ViLiC'
    bl_label = 'Context'

    valid = ['LiVi Context', 'text']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 0.0, 0.75)
        
class ViGen(bpy.types.NodeSocket):
    '''VI Generative geometry socket'''
    bl_idname = 'ViGen'
    bl_label = 'Generative geometry'

    valid = ['LiVi GeoGen']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 1.0, 0.75)

class ViTar(bpy.types.NodeSocket):
    '''VI Generative target socket'''
    bl_idname = 'ViTar'
    bl_label = 'Generative target'

    valid = ['LiVi TarGen']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.0, 1.0, 0.75)

class ViEnG(bpy.types.NodeSocket):
    '''Energy geometry out socket'''
    bl_idname = 'ViEnG'
    bl_label = 'EnVi Geometry'

    valid = ['EnVi Geometry']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 0.0, 1.0, 0.75)

class ViR(bpy.types.NodeSocket):
    '''Vi results socket'''
    bl_idname = 'ViR'
    bl_label = 'Vi results'

    valid = ['Vi Results']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

class ViText(bpy.types.NodeSocket):
    '''VI text socket'''
    bl_idname = 'ViText'
    bl_label = 'VI text export'

    valid = ['text']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.2, 1.0, 0.0, 0.75)

class ViEnC(bpy.types.NodeSocket):
    '''EnVi context socket'''
    bl_idname = 'ViEnC'
    bl_label = 'EnVi context'

    valid = ['EnVi Context']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 1.0, 0.75)

class EnViDataIn(bpy.types.NodeSocket):
    '''EnVi data in socket'''
    bl_idname = 'EnViDIn'
    bl_label = 'EnVi data in socket'

    valid = ['EnVi data']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

# Generative nodes
class ViGenNode(bpy.types.Node, ViNodes):
    '''Generative geometry manipulation node'''
    bl_idname = 'ViGenNode'
    bl_label = 'VI Generative'
    bl_icon = 'LAMP'

    geotype = [('Object', "Object", "Object level manipulation"), ('Mesh', "Mesh", "Mesh level manipulation")]
    geomenu = bpy.props.EnumProperty(name="", description="Geometry type", items=geotype, default = 'Mesh')
    seltype = [('All', "All", "All geometry"), ('Selected', "Selected", "Only selected geometry"), ('Not selected', "Not selected", "Only unselected geometry")]
    oselmenu = bpy.props.EnumProperty(name="", description="Object selection", items=seltype, default = 'Selected')
    mselmenu = bpy.props.EnumProperty(name="", description="Mesh selection", items=seltype, default = 'Selected')
    omantype = [('0', "Move", "Move geometry"), ('1', "Rotate", "Only unselected geometry"), ('2', "Scale", "Scale geometry")]
    omanmenu = bpy.props.EnumProperty(name="", description="Manipulation type", items=omantype, default = '0')
    mmantype = [('0', "Move", "Move geometry"), ('1', "Rotate", "Only unselected geometry"), ('2', "Scale", "Scale geometry"), ('3', "Extrude", "Extrude geometry")]
    mmanmenu = bpy.props.EnumProperty(name="", description="Manipulation type", items=mmantype, default = '0')
    (x, y, z) = [bpy.props.FloatProperty(name = i, min = -1, max = 1, default = 1) for i in ('X', 'Y', 'Z')]
    normal = bpy.props.BoolProperty(name = '', default = False)
    extent = bpy.props.FloatProperty(name = '', min = -360, max = 360, default = 0)
    steps = bpy.props.IntProperty(name = '', min = 1, max = 100, default = 1)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViGen', 'Generative out')

    def draw_buttons(self, context, layout):
        newrow(layout, 'Geometry:', self, 'geomenu')
        newrow(layout, 'Object Selection:', self, 'oselmenu')
        if self.geomenu == 'Object':
           newrow(layout, 'Manipulation:', self, 'omanmenu')
           row = layout.row()
           col = row.column()
           subrow = col.row(align=True)
           subrow.prop(self, 'x')
           subrow.prop(self, 'y')
           subrow.prop(self, 'z')
        else:
           newrow(layout, 'Mesh Selection:', self, 'mselmenu')
           newrow(layout, 'Manipulation:', self, 'mmanmenu')
           newrow(layout, 'Normal:', self, 'normal')
           if not self.normal:
               row = layout.row()
               col = row.column()
               subrow = col.row(align=True)
               subrow.prop(self, 'x')
               subrow.prop(self, 'y')
               subrow.prop(self, 'z')

        newrow(layout, 'Extent:', self, 'extent')
        newrow(layout, 'Increment:', self, 'steps')

    def update(self):
        socklink(self.outputs['Generative out'], self['nodeid'].split('@')[1])
        if self.outputs['Generative out'].links:
            nodecolour(self, self.outputs['Generative out'].links[0].to_node.animmenu != 'Static')

class ViTarNode(bpy.types.Node, ViNodes):
    '''Target Node'''
    bl_idname = 'ViTarNode'
    bl_label = 'VI Target'
    bl_icon = 'LAMP'

    ab = bpy.props.EnumProperty(items=[("0", "Above", "Target is above level"),("1", "Below", "Target is below level")],  name="", description="Whether target is to go above or below a specified level", default="0")
    stat = bpy.props.EnumProperty(items=[("0", "Average", "Average of data points"),("1", "Max", "Maximum of data points"),("2", "Min", "Minimum of data points"),("3", "Tot", "Total of data points")],  name="", description="Metric statistic", default="0")
    value = bpy.props.FloatProperty(name = '', min = 0, max = 100000, default = 0, description="Desired value")

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViTar', 'Target out')

    def draw_buttons(self, context, layout):
        newrow(layout, 'Statistic:', self, 'stat')
        newrow(layout, 'Above/Below:', self, 'ab')
        newrow(layout, 'Value:', self, 'value')

class ViCSVExport(bpy.types.Node, ViNodes):
    '''CSV Export Node'''
    bl_idname = 'ViCSV'
    bl_label = 'VI CSV Export'
    bl_icon = 'LAMP'

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViR', 'Results in')

    def draw_buttons(self, context, layout):
        if self.inputs['Results in'].links:
            row = layout.row()
            row.operator('node.csvexport', text = 'Export CSV file').nodeid = self['nodeid']

    def update(self):
        pass

class ViTextEdit(bpy.types.Node, ViNodes):
    '''Text Export Node'''
    bl_idname = 'ViTextEdit'
    bl_label = 'VI Text Edit'
    bl_icon = 'LAMP'
    
    contextmenu = bpy.props.StringProperty(name = '')

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self['bt'] = ''
        self.outputs.new('ViText', 'Text out')
        self.inputs.new('ViText', 'Text in')
        self.outputs['Text out']['Text'] = {}
        self.outputs['Text out']['Options'] = {}
        
    def draw_buttons(self, context, layout):
        if self.inputs['Text in'].links:
            inodename = self.inputs['Text in'].links[0].from_node.name
            row = layout.row()
            row.label(text = 'Text name: {}'.format(inodename))            
            if inodename in [im.name for im in bpy.data.texts] and self['bt'] != bpy.data.texts[inodename].as_string():
                row = layout.row()
                row.operator('node.textupdate', text = 'Update').nodeid = self['nodeid']

    def update(self):
        if self.inputs and self.inputs['Text in'].links:
            self.outputs['Text out']['Options'] = self.inputs['Text in'].links[0].from_socket['Options']
            self.outputs['Text out']['Text'] = self.inputs['Text in'].links[0].from_socket['Text']
            inodename = self.inputs['Text in'].links[0].from_node.name
            sframes = sorted([int(frame) for frame in self.inputs['Text in'].links[0].from_socket['Text'].keys()])
            t = ''.join(['# Frame {}\n{}\n\n'.format(f, self.inputs['Text in'].links[0].from_socket['Text'][str(f)]) for f in sframes])
            bt = bpy.data.texts.new(inodename) if inodename not in [im.name for im in bpy.data.texts] else bpy.data.texts[inodename]
            bt.from_string(t)
            self['bt'] = bt.as_string()
        else:
            self.outputs['Text out']['Text'] = {}

    def textupdate(self, bt):
        inodename = self.inputs['Text in'].links[0].from_node.name
        bt = bpy.data.texts.new(inodename) if inodename not in [im.name for im in bpy.data.texts] else bpy.data.texts[inodename]
        btlines = [line.body for line in bt.lines]
        self['bt'] = bt.as_string()
        btheads = [line for line in btlines if '# Frame' in line]
        btstring = ''.join([self['bt'].replace(bth, '***') for bth in btheads])
        btbodies = btstring.split('***\n')[1:]
        btframes = [head.split()[2] for head in btheads]
        self.outputs['Text out']['Text'] = {bthb[0]:bthb[1] for bthb in zip(btframes, btbodies)}

class ViTextExport(bpy.types.Node, ViNodes):
    '''Text Export Node'''
    bl_idname = 'ViText'
    bl_label = 'VI Text Export'
    bl_icon = 'LAMP'

    etoggle = bpy.props.BoolProperty(name = '', default = False)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViText', 'Text in')

    def draw_buttons(self, context, layout):
        if self.inputs['Text in'].links:
            newrow(layout, 'Edit:', self, 'etoggle')
            row = layout.row()
            row.operator('node.textexport', text = 'Export text file').nodeid = self['nodeid']

    def update(self):
        pass

# Openfoam nodes

class VIOfM(bpy.types.NodeSocket):
    '''FloVi mesh socket'''
    bl_idname = 'VIOfM'
    bl_label = 'FloVi Mesh socket'

    valid = ['FloVi mesh']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.5, 1.0, 0.0, 0.75)

class VIOFCDS(bpy.types.NodeSocket):
    '''FloVi ControlDict socket'''
    bl_idname = 'VIOFCD'
    bl_label = 'FloVi ControlDict socket'

    valid = ['FloVi Control']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.5, 1.0, 0.0, 0.75)

class ViFloCdNode(bpy.types.Node, ViNodes):
    '''Openfoam Controldict export node'''
    bl_idname = 'VIOFCdn'
    bl_label = 'FloVi ControlDict'
    bl_icon = 'LAMP'
    controlD = bpy.props.StringProperty()

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.solver)])

    solver = bpy.props.EnumProperty(items = [('simpleFoam', 'SimpleFoam', 'Steady state turbulence solver'), ('icoFoam', 'IcoFoam', 'Transient laminar solver'),
                                               ('pimpleFoam', 'PimpleFoam', 'Transient turbulence solver') ], name = "", default = 'simpleFoam', update = nodeupdate)

    def init(self, context):
        self['exportstate'] = ''
        self['nodeid'] = nodeid(self)
        self.outputs.new('VIOFCDS', 'Control out')
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, 'Solver', self, 'solver')

class ViBMExNode(bpy.types.Node, ViNodes):
    '''Openfoam blockmesh export node'''
    bl_idname = 'ViBMExNode'
    bl_label = 'FloVi BlockMesh'
    bl_icon = 'LAMP'

    solver = bpy.props.EnumProperty(items = [('icoFoam', 'IcoFoam', 'Transient laminar solver')], name = "", default = 'icoFoam')
    turbulence  = bpy.props.StringProperty()

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.bm_xres, self.bm_yres, self.bm_zres, self.bm_xgrad, self.bm_ygrad, self.bm_zgrad)])

    bm_xres = bpy.props.IntProperty(name = "X", description = "Blockmesh X resolution", min = 0, max = 1000, default = 10, update = nodeupdate)
    bm_yres = bpy.props.IntProperty(name = "Y", description = "Blockmesh Y resolution", min = 0, max = 1000, default = 10, update = nodeupdate)
    bm_zres = bpy.props.IntProperty(name = "Z", description = "Blockmesh Z resolution", min = 0, max = 1000, default = 10, update = nodeupdate)
    bm_xgrad = bpy.props.FloatProperty(name = "X", description = "Blockmesh X simple grading", min = 0, max = 10, default = 1, update = nodeupdate)
    bm_ygrad = bpy.props.FloatProperty(name = "Y", description = "Blockmesh Y simple grading", min = 0, max = 10, default = 1, update = nodeupdate)
    bm_zgrad = bpy.props.FloatProperty(name = "Z", description = "Blockmesh Z simple grading", min = 0, max = 10, default = 1, update = nodeupdate)
    existing =  bpy.props.BoolProperty(name = '', default = 0)

    def init(self, context):
        self['exportstate'] = ''
        self['nodeid'] = nodeid(self)
        self.outputs.new('VIOfM', 'Mesh out')
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        split = layout.split()
        col = split.column(align=True)
        col.label(text="Cell resolution:")
        col.prop(self, "bm_xres")
        col.prop(self, "bm_yres")
        col.prop(self, "bm_zres")
        col = split.column(align=True)
        col.label(text="Cell grading:")
        col.prop(self, "bm_xgrad")
        col.prop(self, "bm_ygrad")
        col.prop(self, "bm_zgrad")
        row = layout.row()
        row.operator("node.blockmesh", text = "Export").nodeid = self['nodeid']
        if not self.use_custom_color:
            newrow(layout, 'Use existing', self, 'existing')

    def update(self):
        socklink(self.outputs['Mesh out'], self['nodeid'].split('@')[1])

    def export(self):
        self.exportstate = [str(x) for x in (self.bm_xres, self.bm_yres, self.bm_zres, self.bm_xgrad, self.bm_ygrad, self.bm_zgrad)]
        nodecolour(self, 0)

class ViSHMExNode(bpy.types.Node, ViNodes):
    '''Openfoam blockmesh export node'''
    bl_idname = 'ViSHMExNode'
    bl_label = 'FloVi SnappyHexMesh'
    bl_icon = 'LAMP'
    laytypedict = {'0': (('First', 'frlayer'), ('Overall', 'olayer')), '1': (('First', 'frlayer'), ('Expansion', 'expansion')), '2': (('Final', 'fnlayer'), ('Expansion', 'expansion')),
                     '3': (('Final', 'fnlayer'), ('Overall', 'olayer')), '4': (('Final:', 'fnlayer'), ('Expansion:', 'expansion')), '5': (('Overall:', 'olayer'), ('Expansion:', 'expansion'))}

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.lcells, self.gcells)])

    lcells = bpy.props.IntProperty(name = "", description = "SnappyhexMesh local cells", min = 0, max = 100000, default = 1000, update = nodeupdate)
    gcells = bpy.props.IntProperty(name = "", description = "SnappyhexMesh global cells", min = 0, max = 1000000, default = 10000, update = nodeupdate)
    level = bpy.props.IntProperty(name = "", description = "SnappyhexMesh level", min = 0, max = 6, default = 2, update = nodeupdate)
    surflmin = bpy.props.IntProperty(name = "", description = "SnappyhexMesh level", min = 0, max = 6, default = 2, update = nodeupdate)
    surflmax = bpy.props.IntProperty(name = "", description = "SnappyhexMesh level", min = 0, max = 6, default = 2, update = nodeupdate)
    ncellsbl = bpy.props.IntProperty(name = "", description = "Number of cells between levels", min = 0, max = 6, default = 2, update = nodeupdate)
    layers = bpy.props.IntProperty(name = "", description = "Layer number", min = 0, max = 10, default = 0, update = nodeupdate)

    layerspec = bpy.props.EnumProperty(items = [('0', 'First & overall', 'First layer thickness and overall thickness'), ('1', 'First & ER', 'First layer thickness and expansion ratio'),
                                               ('2', 'Final & ER', 'Final layer thickness and expansion ratio'), ('3', 'Final & overall', 'Final layer thickness and overall thickness'),
                                                ('4', 'Final & ER', 'Final layer thickness and expansion ratio'), ('5', 'Overall & ER', 'Overall thickness and expansion ratio')], name = "", default = '0', update = nodeupdate)
    expansion = bpy.props.FloatProperty(name = "", description = "Exapnsion ratio", min = 1.0, max = 3.0, default = 1.0, update = nodeupdate)
    llayer = bpy.props.FloatProperty(name = "", description = "Last layer thickness", min = 0.01, max = 3.0, default = 1.0, update = nodeupdate)
    frlayer = bpy.props.FloatProperty(name = "", description = "First layer thickness", min = 0.01, max = 3.0, default = 1.0, update = nodeupdate)
    fnlayer = bpy.props.FloatProperty(name = "", description = "First layer thickness", min = 0.01, max = 3.0, default = 1.0, update = nodeupdate)
    olayer = bpy.props.FloatProperty(name = "", description = "Overall layer thickness", min = 0.01, max = 3.0, default = 1.0, update = nodeupdate)

    def init(self, context):
        self['exportstate'] = ''
        self['nodeid'] = nodeid(self)
        self.inputs.new('VIOfM', 'Mesh in')
        self.outputs.new('VIOfM', 'Mesh out')
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, 'Local cells:', self, 'lcells')
        newrow(layout, 'Global cells:', self, 'gcells')
        newrow(layout, 'Level:', self, 'level')
        newrow(layout, 'Max level:', self, 'surflmax')
        newrow(layout, 'Min level:', self, 'surflmin')
        newrow(layout, 'CellsBL:', self, 'ncellsbl')
        newrow(layout, 'Layers:', self, 'layers')
        if self.layers:
            newrow(layout, 'Layer spec:', self, 'layerspec')
            [newrow(layout, laytype[0], self, laytype[1]) for laytype in self.laytypedict[self.layerspec]]
#                newrow(layout, laytype[0], self, laytype[1])
        row = layout.row()
        row.operator("node.snappy", text = "Export").nodeid = self['nodeid']

    def export(self):
        self.exportstate = [str(x) for x in (self.lcells, self.gcells)]
        nodecolour(self, 0)

class ViFVSimNode(bpy.types.Node, ViNodes):
    '''Openfoam blockmesh export node'''
    bl_idname = 'ViFVSimNode'
    bl_label = 'FloVi Simulationh'
    bl_icon = 'LAMP'

    p = bpy.props.StringProperty()
    U = bpy.props.StringProperty()
    k = bpy.props.StringProperty()
    episilon = bpy.props.StringProperty()
    omega = bpy.props.StringProperty()
    nut = bpy.props.StringProperty()
    nuTilda = bpy.props.StringProperty()

    def nodeupdate(self, context):
        context.scene['viparams']['fvsimnode'] = nodeid(self)
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.solver, self.dt, self.et, self.bouyancy, self.radiation, self.turbulence)])

    solver = bpy.props.EnumProperty(items = [('simpleFoam', 'SimpleFoam', 'Steady state turbulence solver'),
                                              ('icoFoam', 'IcoFoam', 'Transient laminar solver'),
                                               ('pimpleFoam', 'PimpleFoam', 'Transient turbulence solver') ], name = "", default = 'simpleFoam', update = nodeupdate)
    dt = bpy.props.FloatProperty(name = "", description = "Simulation delta T", min = 0.001, max = 500, default = 50, update = nodeupdate)
    et = bpy.props.FloatProperty(name = "", description = "Simulation end time", min = 0.001, max = 5000, default = 500, update = nodeupdate)
    pval = bpy.props.FloatProperty(name = "", description = "Simulation delta T", min = -500, max = 500, default = 0.0, update = nodeupdate)
    uval = bpy.props.FloatVectorProperty(size = 3, name = '', attr = 'Velocity', default = [0, 0, 0], unit = 'VELOCITY', subtype = 'VELOCITY', min = -100, max = 100)
    bouyancy =  bpy.props.BoolProperty(name = '', default = 0, update=nodeupdate)
    radiation =  bpy.props.BoolProperty(name = '', default = 0, update=nodeupdate)
    turbulence =  bpy.props.EnumProperty(items = [('laminar', 'Laminar', 'Steady state turbulence solver'),
                                              ('kEpsilon', 'k-Epsilon', 'Transient laminar solver'),
                                               ('kOmega', 'k-Omega', 'Transient turbulence solver'), ('SpalartAllmaras', 'Spalart-Allmaras', 'Spalart-Allmaras turbulence solver')], name = "", default = 'laminar', update = nodeupdate)
    nutval = bpy.props.FloatProperty(name = "", description = "Simulation delta T", min = 0.0, max = 500, default = 0.0, update = nodeupdate)
    nutildaval = bpy.props.FloatProperty(name = "", description = "Simulation delta T", min = 0.0, max = 500, default = 0.0, update = nodeupdate)
    kval = bpy.props.FloatProperty(name = "", description = "Simulation delta T", min = 0.1, max = 500, default = 0.0, update = nodeupdate)
    epval = bpy.props.FloatProperty(name = "", description = "Simulation delta T", min = 0.1, max = 500, default = 0.1, update = nodeupdate)
    oval = bpy.props.FloatProperty(name = "", description = "Simulation delta T", min = 0.1, max = 500, default = 0.1, update = nodeupdate)
    convergence = bpy.props.FloatProperty(name = "", description = "Convergence criteria", min = 0.0001, max = 0.01, default = 0.0001, update = nodeupdate)

    def init(self, context):
        self['exportstate'] = ''
        self['nodeid'] = nodeid(self)
        self.inputs.new('VIOfM', 'Mesh in')
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, 'Solver:', self, 'solver')
        newrow(layout, 'deltaT:', self, 'dt')
        newrow(layout, 'End time:', self, 'et')
        newrow(layout, 'Pressure:', self, 'pval')
        newrow(layout, 'Velocity:', self, 'uval')
        if self.solver in ('simpleFoam', 'pimpleFoam'):
            newrow(layout, 'Turbulence:', self, 'turbulence')
            newrow(layout, 'Bouyancy:', self, 'bouyancy')
            newrow(layout, 'Radiation:', self, 'radiation')
            if self.turbulence != 'laminar':
                newrow(layout, 'nut value:', self, 'nutval')
                if self.turbulence == 'SpalartAllmaras':
                    newrow(layout, 'nuTilda value:', self, 'nutildaval')
                elif self.turbulence == 'kEpsilon':
                    newrow(layout, 'k value:', self, 'kval')
                    newrow(layout, 'epsilon value:', self, 'epval')
                elif self.turbulence == 'kOmega':
                    newrow(layout, 'k value:', self, 'kval')
                    newrow(layout, 'omega value:', self, 'oval')
        newrow(layout, 'Convergence:', self, 'convergence')

        row = layout.row()
        row.operator("node.fvsolve", text = "Calculate").nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Mesh out'], self['nodeid'].split('@')[1])

    def export(self):
        self.exportstate = [str(x) for x in (self.solver, self.dt, self.et, self.bouyancy, self.radiation, self.turbulence)]
        nodecolour(self, 0)
####################### Vi Nodes Catagories ##############################

viexnodecat = [NodeItem("ViLoc", label="VI Location"), NodeItem("ViGExLiNode", label="LiVi Geometry"), NodeItem("LiViNode", label="LiVi Context"),
                NodeItem("ViGExEnNode", label="EnVi Geometry"), NodeItem("ViExEnNode", label="EnVi Export"), NodeItem("ViFloCdNode", label="FloVi Control"),
                 NodeItem("ViBMExNode", label="FloVi BlockMesh"), NodeItem("ViSHMExNode", label="FloVi SnappyHexMesh")]
                
vifilenodecat = [NodeItem("ViTextEdit", label="Text Edit"), NodeItem("ViCombine", label="Combine inputs")]
vinodecat = [NodeItem("ViLiSNode", label="LiVi Simulation"), NodeItem("ViFVSimNode", label="FloVi Simulation"),\
             NodeItem("ViSPNode", label="VI-Suite sun path"), NodeItem("ViSSNode", label="VI-Suite shadow study"), NodeItem("ViWRNode", label="VI-Suite wind rose"), NodeItem("ViEnSimNode", label="EnVi Simulation")]

vigennodecat = [NodeItem("ViGenNode", label="VI-Suite Generative"), NodeItem("ViTarNode", label="VI-Suite Target")]

vidisnodecat = [NodeItem("ViChNode", label="VI-Suite Chart"), NodeItem("ViCSV", label="VI-Suite CSV"), NodeItem("ViText", label="VI-Suite Text")]
viinnodecat = [NodeItem("ViEnInNode", label="EnergyPlus input file"), NodeItem("ViEnRFNode", label="EnergyPlus result file"), NodeItem("ViASCImport", label="Import ESRI Grid file")]

vinode_categories = [ViNodeCategory("Edit", "Edit Nodes", items=vifilenodecat), ViNodeCategory("Input", "Input Nodes", items=viinnodecat), ViNodeCategory("Display", "Display Nodes", items=vidisnodecat), ViNodeCategory("Generative", "Generative Nodes", items=vigennodecat), ViNodeCategory("Analysis", "Analysis Nodes", items=vinodecat), ViNodeCategory("Export", "Export Nodes", items=viexnodecat)]


####################### EnVi ventilation network ##############################

class EnViNetwork(bpy.types.NodeTree):
    '''A node tree for the creation of EnVi advanced ventilation networks.'''
    bl_idname = 'EnViN'
    bl_label = 'EnVi Network'
    bl_icon = 'FORCE_WIND'
    nodetypes = {}

class EnViNodes:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'EnViN'

class EnViBoundSocket(bpy.types.NodeSocket):
    '''A plain zone boundary socket'''
    bl_idname = 'EnViBoundSocket'
    bl_label = 'Plain zone boundary socket'
    bl_color = (1.0, 1.0, 0.2, 0.5)

    valid = ['Boundary']
    sn = bpy.props.StringProperty()

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.5, 0.2, 0.0, 0.75)

class EnViSchedSocket(bpy.types.NodeSocket):
    '''Fraction schedule socket'''
    bl_idname = 'EnViSchedSocket'
    bl_label = 'Schedule socket'
    bl_color = (1.0, 1.0, 0.0, 0.75)

    valid = ['Schedule']
    schedule = ['Fraction']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 0.0, 0.75)

class EnViTSchedSocket(bpy.types.NodeSocket):
    '''Temperature schedule socket'''
    bl_idname = 'EnViTSchedSocket'
    bl_label = 'Schedule socket'
    bl_color = (1.0, 1.0, 0.0, 0.75)

    valid = ['Schedule']
    schedule = ['Temperature']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 0.0, 0.75)

class EnViSSFlowSocket(bpy.types.NodeSocket):
    '''A sub-surface flow socket'''
    bl_idname = 'EnViSSFlowSocket'
    bl_label = 'Sub-surface flow socket'

    sn = bpy.props.StringProperty()
    valid = ['Sub-surface']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.1, 1.0, 0.2, 0.75)

class EnViSFlowSocket(bpy.types.NodeSocket):
    '''A surface flow socket'''
    bl_idname = 'EnViSFlowSocket'
    bl_label = 'Surface flow socket'

    sn = bpy.props.StringProperty()
    valid = ['Surface']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class EnViSSSFlowSocket(bpy.types.NodeSocket):
    '''A surface or sub-surface flow socket'''
    bl_idname = 'EnViSSSFlowSocket'
    bl_label = '(Sub-)Surface flow socket'

    sn = bpy.props.StringProperty()
    valid = ['(Sub)Surface']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 0.2, 0.75)

class EnViCrRefSocket(bpy.types.NodeSocket):
    '''A plain zone airflow component socket'''
    bl_idname = 'EnViCrRefSocket'
    bl_label = 'Plain zone airflow component socket'

    sn = bpy.props.StringProperty()

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.0, 0.75)

class EnViOccSocket(bpy.types.NodeSocket):
    '''An EnVi zone occupancy socket'''
    bl_idname = 'EnViOccSocket'
    bl_label = 'Zone occupancy socket'

    sn = bpy.props.StringProperty()
    valid = ['Occupancy']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class EnViEqSocket(bpy.types.NodeSocket):
    '''An EnVi zone equipment socket'''
    bl_idname = 'EnViEqSocket'
    bl_label = 'Zone equipment socket'

    sn = bpy.props.StringProperty()
    valid = ['Equipment']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class EnViInfSocket(bpy.types.NodeSocket):
    '''An EnVi zone infiltration socket'''
    bl_idname = 'EnViInfSocket'
    bl_label = 'Zone infiltration socket'

    valid = ['Infiltration']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class EnViHvacSocket(bpy.types.NodeSocket):
    '''An EnVi zone HVAC socket'''
    bl_idname = 'EnViHvacSocket'
    bl_label = 'Zone HVAC socket'

    sn = bpy.props.StringProperty()
    valid = ['HVAC']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class EnViWPCSocket(bpy.types.NodeSocket):
    '''An EnVi external node WPC socket'''
    bl_idname = 'EnViWPCSocket'
    bl_label = 'External node WPC'

    sn = bpy.props.StringProperty()
    valid = ['WPC']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.2, 0.2, 0.2, 0.75)

class EnViActSocket(bpy.types.NodeSocket):
    '''An EnVi actuator socket'''
    bl_idname = 'EnViActSocket'
    bl_label = 'EnVi actuator socket'

    sn = bpy.props.StringProperty()
    valid = ['Actuator']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.2, 0.9, 0.9, 0.75)

class EnViSenseSocket(bpy.types.NodeSocket):
    '''An EnVi sensor socket'''
    bl_idname = 'EnViSenseSocket'
    bl_label = 'EnVi sensor socket'

    sn = bpy.props.StringProperty()
    valid = ['Sensor']

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.9, 0.9, 0.2, 0.75)

class AFNCon(bpy.types.Node, EnViNodes):
    '''Node defining the overall airflow network simulation'''
    bl_idname = 'AFNCon'
    bl_label = 'Control'
    bl_icon = 'SOUND'

    def wpcupdate(self, context):
        if self.wpctype == 'SurfaceAverageCalculation':
            if self.inputs['WPC Array'].is_linked:
                remlink(self, self.inputs['WPC Array'].links)
            self.inputs['WPC Array'].hide = True
        elif self.wpctype == 'Input':
            self.inputs['WPC Array'].hide = False
        self.legal()

    afnname = bpy.props.StringProperty(name = '')
    afntype = bpy.props.EnumProperty(items = [('MultizoneWithDistribution', 'MultizoneWithDistribution', 'Include a forced airflow system in the model'),
                                              ('MultizoneWithoutDistribution', 'MultizoneWithoutDistribution', 'Exclude a forced airflow system in the model'),
                                              ('MultizoneWithDistributionOnlyDuringFanOperation', 'MultizoneWithDistributionOnlyDuringFanOperation', 'Apply forced air system only when in operation'),
                                              ('NoMultizoneOrDistribution', 'NoMultizoneOrDistribution', 'Only zone infiltration controls are modelled')], name = "", default = 'MultizoneWithoutDistribution')

    wpctype = bpy.props.EnumProperty(items = [('SurfaceAverageCalculation', 'SurfaceAverageCalculation', 'Calculate wind pressure coefficients based on oblong building assumption'),
                                              ('Input', 'Input', 'Input wind pressure coefficients from an external source')], name = "", default = 'SurfaceAverageCalculation', update = wpcupdate)
    wpcaname = bpy.props.StringProperty()
    wpchs = bpy.props.EnumProperty(items = [('OpeningHeight', 'OpeningHeight', 'Calculate wind pressure coefficients based on opening height'),
                                              ('ExternalNode', 'ExternalNode', 'Calculate wind pressure coefficients based on external node height')], name = "", default = 'OpeningHeight')
    buildtype = bpy.props.EnumProperty(items = [('LowRise', 'Low Rise', 'Height is less than 3x the longest wall'),
                                              ('HighRise', 'High Rise', 'Height is more than 3x the longest wall')], name = "", default = 'LowRise')

    maxiter = bpy.props.IntProperty(default = 500, description = 'Maximum Number of Iterations', name = "")

    initmet = bpy.props.EnumProperty(items = [('ZeroNodePressures', 'ZeroNodePressures', 'Initilisation type'),
                                              ('LinearInitializationMethod', 'LinearInitializationMethod', 'Initilisation type')], name = "", default = 'ZeroNodePressures')
    rcontol = bpy.props.FloatProperty(default = 0.0001, description = 'Relative Airflow Convergence Tolerance', name = "")
    acontol = bpy.props.FloatProperty(min = 0.000001, max = 0.1, default = 0.000001, description = 'Absolute Airflow Convergence Tolerance', name = "")
    conal = bpy.props.FloatProperty(default = -0.1, max = 1, min = -1, description = 'Convergence Acceleration Limit', name = "")
    aalax = bpy.props.IntProperty(default = 0, max = 180, min = 0, description = 'Azimuth Angle of Long Axis of Building', name = "")
    rsala = bpy.props.FloatProperty(default = 1, max = 1, min = 0, description = 'Ratio of Building Width Along Short Axis to Width Along Long Axis', name = "")

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('EnViWPCSocket', 'WPC Array')

    def draw_buttons(self, context, layout):
        yesno = (1, 1, 1, self.wpctype == 'Input', self.wpctype != 'Input' and self.wpctype == 'SurfaceAverageCalculation', 1, 1, 1, 1, 1, self.wpctype == 'SurfaceAverageCalculation', self.wpctype == 'SurfaceAverageCalculation')
        vals = (('Name:', 'afnname'), ('Type:', 'afntype'), ('WPC type:', 'wpctype'), ('WPC height', 'wpchs'), ('Build type:', 'buildtype'), ('Max iter:','maxiter'), ('Init method:', 'initmet'),
         ('Rel Converge:', 'rcontol'), ('Abs Converge:', 'acontol'), ('Converge Lim:', 'conal'), ('Azimuth:', 'aalax'), ('Axis ratio:', 'rsala'))
        [newrow(layout, val[0], self, val[1]) for v, val in enumerate(vals) if yesno[v]]

    def epwrite(self, exp_op, enng):
        wpcaentry = ''
        if self.wpctype == 'Input' and not self.inputs['WPC Array'].is_linked:
            exp_op.report({'ERROR'},"WPC array input has been selected in the control node, but no WPC array node is attached")
            return 'ERROR'

        wpcaname = 'WPC Array' if not self.wpcaname else self.wpcaname
        self.afnname = 'default' if not self.afnname else self.afnname
        wpctype = 1 if self.wpctype == 'Input' else 0
        paramvs = (self.afnname, self.afntype,
                     self.wpctype, ("", wpcaname)[wpctype], ("", self.wpchs)[wpctype], (self.buildtype, "")[wpctype], self.maxiter, self.initmet,
                    '{:.3E}'.format(self.rcontol), '{:.3E}'.format(self.acontol), '{:.3E}'.format(self.conal), (self.aalax, "")[wpctype], (self.rsala, "")[wpctype])

        params = ('Name', 'AirflowNetwork Control', 'Wind Pressure Coefficient Type', 'AirflowNetwork Wind Pressure Coefficient Array Name', \
        'Height Selection for Local Wind Pressure Calculation', 'Building Type', 'Maximum Number of Iterations (dimensionless)', 'Initialization Type', \
        'Relative Airflow Convergence Tolerance (dimensionless)', 'Absolute Airflow Convergence Tolerance (kg/s)', 'Convergence Acceleration Limit (dimensionless)', \
        'Azimuth Angle of Long Axis of Building (deg)', 'Ratio of Building Width Along Short Axis to Width Along Long Axis')

        simentry = epentry('AirflowNetwork:SimulationControl', params, paramvs)

        if self.inputs['WPC Array'].is_linked:
            (wpcaentry, enng['enviparams']['wpcn']) = self.inputs['WPC Array'].links[0].from_node.epwrite() if wpctype == 1 else ('', 0)
            enng['enviparams']['wpca'] = 1
        self.legal()
        return simentry + wpcaentry

    def update(self):
        self.legal()

    def legal(self):
        bpy.data.node_groups[self['nodeid'].split('@')[1]]['enviparams']['wpca'] = 1 if self.wpctype == 'Input' and self.inputs['WPC Array'].is_linked else 0
        nodecolour(self, self.wpctype == 'Input' and not self.inputs['WPC Array'].is_linked)
        for node in [node for node in bpy.data.node_groups[self['nodeid'].split('@')[1]].nodes if node.bl_idname in ('EnViSFlow', 'EnViSSFlow')]:
            node.legal()

class EnViWPCA(bpy.types.Node, EnViNodes):
    '''Node describing Wind Pressure Coefficient array'''
    bl_idname = 'EnViWPCA'
    bl_label = 'Envi WPCA'
    bl_icon = 'SOUND'

    (ang1, ang2, ang3, ang4, ang5, ang6, ang7, ang8, ang9, ang10, ang11, ang12) = [bpy.props.IntProperty(name = '', default = 0, min = 0, max = 360) for x in range(12)]

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViWPCSocket', 'WPC values')

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('WPC Angles')
        for w in range(1, 13):
            row = layout.row()
            row.prop(self, 'ang{}'.format(w))

    def update(self):
        socklink(self.outputs['WPC values'], self['nodeid'].split('@')[1])
        bpy.data.node_groups[self['nodeid'].split('@')[1]].interface_update(bpy.context)

    def epwrite(self):
        angs = (self.ang1,self.ang2, self.ang3, self.ang4, self.ang5, self.ang6, self.ang7, self.ang8, self.ang9, self.ang10, self.ang11, self.ang12)
        aparamvs = ['WPC Array'] + [wd for w, wd in enumerate(angs) if wd not in angs[:w]]
        aparams = ['Name'] + ['Wind Direction {} (deg)'.format(w + 1) for w in range(len(aparamvs) - 1)]
        return (epentry('AirflowNetwork:MultiZone:WindPressureCoefficientArray', aparams, aparamvs), len(aparamvs) - 1)

class EnViCrRef(bpy.types.Node, EnViNodes):
    '''Node describing reference crack conditions'''
    bl_idname = 'EnViCrRef'
    bl_label = 'ReferenceCrackConditions'
    bl_icon = 'SOUND'

    reft = bpy.props.FloatProperty(name = '', min = 0, max = 30, default = 20, description = 'Reference Temperature ('+u'\u00b0C)')
    refp = bpy.props.IntProperty(name = '', min = 100000, max = 105000, default = 101325, description = 'Reference Pressure (Pa)')
    refh = bpy.props.FloatProperty(name = '', min = 0, max = 10, default = 0, description = 'Reference Humidity Ratio (kgWater/kgDryAir)')

    def draw_buttons(self, context, layout):
        vals = (('Temperature:' ,'reft'), ('Pressure:', 'refp'), ('Humidity', 'refh'))
        [newrow(layout, val[0], self, val[1]) for val in vals]

    def epwrite(self):
        params = ('Name', 'Reference Temperature', 'Reference Pressure', 'Reference Humidity Ratio')
        paramvs = ('ReferenceCrackConditions', self.reft, self.refp, self.refh)
        return epentry('AirflowNetwork:MultiZone:ReferenceCrackConditions', params, paramvs)

class EnViOcc(bpy.types.Node, EnViNodes):
    '''Zone occupancy node'''
    bl_idname = 'EnViOcc'
    bl_label = 'Occupancy'
    bl_icon = 'SOUND'

    def oupdate(self, context):
        (self.inputs['OSchedule'].hide, self.inputs['ASchedule'].hide) = (True, True) if self.envi_occtype == '0' else (False, False)
        (self.inputs['WSchedule'].hide, self.inputs['VSchedule'].hide, self.inputs['CSchedule'].hide) = (False, False, False) if self.envi_comfort and self.envi_occtype != '0' else (True, True, True)
        ssocks = [sock for sock in self.inputs if sock.bl_idname == 'EnViSenseSocket']
        if self.envi_occtype != '0' and self.outputs['Occupancy'].links:
            ssocks[0].hide = False
            znode = self.outputs['Occupancy'].links[0].to_node
            ssocks[0].name = '{}_{}'.format(znode.zone, self.sensordict[self.sensortype][0])
        else:
            ssocks[0].hide = True

    envi_occwatts = bpy.props.IntProperty(name = "W/p", description = "Watts per person", min = 1, max = 800, default = 90)
    envi_weff = bpy.props.FloatProperty(name = "", description = "Work efficiency", min = 0, max = 1, default = 0.0)
    envi_airv = bpy.props.FloatProperty(name = "", description = "Average air velocity", min = 0, max = 1, default = 0.1)
    envi_cloth = bpy.props.FloatProperty(name = "", description = "Clothing level", min = 0, max = 10, default = 0.5)
    envi_occtype = bpy.props.EnumProperty(items = [("0", "None", "No occupancy"),("1", "Occupants", "Actual number of people"), ("2", "Person/m"+ u'\u00b2', "Number of people per squared metre floor area"),
                                              ("3", "m"+ u'\u00b2'+"/Person", "Floor area per person")], name = "", description = "The type of zone occupancy specification", default = "0", update = oupdate)
    envi_occsmax = bpy.props.FloatProperty(name = "", description = "Maximum level of occupancy that will occur in this schedule", min = 1, max = 500, default = 1)
    envi_comfort = bpy.props.BoolProperty(name = "", description = "Enable comfort calculations for this space", default = False, update = oupdate)
    envi_co2 = bpy.props.BoolProperty(name = "", description = "Enable CO2 concentration calculations", default = False)
    sensorlist = [("0", "Zone CO2", "Sense the zone CO2"), ("1", "Zone Occupancy", "Sense the zone occupancy")]
    sensortype = bpy.props.EnumProperty(name="", description="Linkage type", items=sensorlist, default='0', update = oupdate)
    sensordict = {'0': ('CO2', 'AFN Node CO2 Concentration'), '1': ('Occ', 'Zone Occupancy')}

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViOccSocket', 'Occupancy')
        self.inputs.new('EnViSchedSocket', 'OSchedule')
        self.inputs.new('EnViSchedSocket', 'ASchedule')
        self.inputs.new('EnViSchedSocket', 'WSchedule')
        self.inputs.new('EnViSchedSocket', 'VSchedule')
        self.inputs.new('EnViSchedSocket', 'CSchedule')
        self.inputs['OSchedule'].hide = True
        self.inputs['ASchedule'].hide = True
        self.inputs['WSchedule'].hide = True
        self.inputs['VSchedule'].hide = True
        self.inputs['CSchedule'].hide = True

    def draw_buttons(self, context, layout):
        newrow(layout, 'Type:', self, "envi_occtype")
        if self.envi_occtype != '0':
            newrow(layout, 'Max level:', self, "envi_occsmax")
            if not self.inputs['ASchedule'].links:
                newrow(layout, 'Activity level:', self, 'envi_occwatts')
            newrow(layout, 'Comfort calc:', self, 'envi_comfort')
            if self.envi_comfort:
                if not self.inputs['WSchedule'].links:
                    newrow(layout, 'Work efficiency:', self, 'envi_weff')
                if not self.inputs['VSchedule'].links:
                    newrow(layout, 'Air velocity:', self, 'envi_airv')
                if not self.inputs['CSchedule'].links:
                    newrow(layout, 'Clothing:', self, 'envi_cloth')
                newrow(layout, 'CO2:', self, 'envi_co2')

    def update(self):
        if self.inputs.get('CSchedule'):
            for sock in self.inputs[:] + self.outputs[:]:
                socklink(sock, self['nodeid'].split('@')[1])

    def epwrite(self, zn):
        pdict = {'0': '', '1':'People', '2': 'People/Area', '3': 'Area/Person'}
        plist = ['', '', '']
        plist[int(self.envi_occtype) - 1] = self.envi_occsmax
        params =  ['Name', 'Zone or ZoneList Name', 'Number of People Schedule Name', 'Number of People Calculation Method', 'Number of People', 'People per Zone Floor Area (person/m2)',
        'Zone Floor Area per Person (m2/person)', 'Fraction Radiant', 'Sensible Heat Fraction', 'Activity Level Schedule Name']
        paramvs = [zn + "_occupancy", zn, zn + '_occsched', pdict[self.envi_occtype]] + plist + [0.3, '', zn + '_actsched']
        if self.envi_comfort:
            params += ['Carbon Dioxide Generation Rate (m3/s-W)', 'Enable ASHRAE 55 Comfort Warnings',
                       'Mean Radiant Temperature Calculation Type', 'Surface Name/Angle Factor List Name', 'Work Efficiency Schedule Name', 'Clothing Insulation Calculation Method', 'Clothing Insulation Calculation Method Schedule Name',
                       'Clothing Insulation Schedule Name', 'Air Velocity Schedule Name', 'Thermal Comfort Model 1 Type']
            paramvs += [3.82E-8, 'No', 'zoneaveraged', '', zn + '_wesched', 'ClothingInsulationSchedule', '', zn + '_closched', zn + '_avsched', 'FANGER']
        return epentry('People', params, paramvs)

class EnViEq(bpy.types.Node, EnViNodes):
    '''Zone equipment node'''
    bl_idname = 'EnViEq'
    bl_label = 'Equipment'
    bl_icon = 'SOUND'

    def zupdate(self, context):
        self.inputs['Schedule'].hide = True if self.envi_equiptype == '0' else False
        ssocks = [sock for sock in self.inputs if sock.bl_idname == 'EnViSenseSocket']
        if self.envi_equiptype != '0' and self.outputs['Equipment'].links:
            ssocks[0].hide = False
            znode = self.outputs['Equipment'].links[0].to_node
            ssocks[0].name = '{}_{}'.format(znode.zone, self.sensordict[self.sensortype][0])
        else:
            ssocks[0].hide = True


    envi_equiptype = bpy.props.EnumProperty(items = [("0", "None", "No equipment"),("1", "EquipmentLevel", "Overall equpiment gains"), ("2", "Watts/Area", "Equipment gains per square metre floor area"),
                                              ("3", "Watts/Person", "Equipment gains per occupant")], name = "", description = "The type of zone equipment gain specification", default = "0", update = zupdate)
    envi_equipmax = bpy.props.FloatProperty(name = "", description = "Maximum level of equipment gain", min = 1, max = 50000, default = 1)
    sensorlist = [("0", "Zone Equipment", "Sense the equipment level")]
    sensortype = bpy.props.EnumProperty(name="", description="Linkage type", items=sensorlist, default='0', update = zupdate)
    sensordict = {'0': ('Equip', 'Equipment level')}

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViEqSocket', 'Equipment')
        self.inputs.new('EnViSchedSocket', 'Schedule')
        self.inputs['Schedule'].hide = True

    def draw_buttons(self, context, layout):
        newrow(layout, 'Type:', self, "envi_equiptype")
        if self.envi_equiptype != '0':
            newrow(layout, 'Max level:', self, "envi_equipmax")

    def update(self):
        for sock in [sock for sock in self.inputs[:] + self.outputs[:] if sock.links]:
            socklink(sock, self['nodeid'].split('@')[1])

    def oewrite(self, zn):
        edict = {'0': '', '1':'EquipmentLevel', '2': 'Watts/Area', '3': 'Watts/Person'}
        elist = ['', '', '']
        elist[int(self.envi_equiptype) - 1] = self.envi_equipmax
        params = ('Name', 'Zone Name', 'SCHEDULE Name', 'Design Level calculation method', 'Design Level (W)', 'Power per Zone Floor Area (Watts/m2)', 'Power per Person (Watts/person)', \
        'Fraction Latent', 'Fraction Radiant', 'Fraction Lost')
        paramvs = [zn + "_equip", zn, zn + "_eqsched", edict[self.envi_equiptype]] + elist + ['0', '0', '0']
        return epentry('OtherEquipment', params, paramvs)

class EnViInf(bpy.types.Node, EnViNodes):
    '''Zone infiltration node'''
    bl_idname = 'EnViInf'
    bl_label = 'Infiltration'
    bl_icon = 'SOUND'

    def zupdate(self, context):
        self.inputs['Schedule'].hide = True if self.envi_inftype == '0' else False

    envi_inftype = bpy.props.EnumProperty(items = [("0", "None", "No infiltration"), ("1", 'Flow/Zone', "Absolute flow rate in m{}/s".format(u'\u00b3')), ("2", "Flow/Area", 'Flow in m{}/s per m{} floor area'.format(u'\u00b3', u'\u00b2')),
                                 ("3", "Flow/ExteriorArea", 'Flow in m{}/s per m{} external surface area'.format(u'\u00b3', u'\u00b2')), ("4", "Flow/ExteriorWallArea", 'Flow in m{}/s per m{} external wall surface area'.format(u'\u00b3', u'\u00b2')),
                                 ("4", "ACH", "ACH flow rate")], name = "", description = "The type of zone infiltration specification", default = "0", update = zupdate)
    envi_inflevel = bpy.props.FloatProperty(name = "Level", description = "Level of Infiltration", min = 0, max = 500, default = 0.001)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViInfSocket', 'Infiltration')
        self.inputs.new('EnViSchedSocket', 'Schedule')
        self.inputs['Schedule'].hide = True

    def draw_buttons(self, context, layout):
        newrow(layout, 'Type:', self, "envi_inftype")
        if self.envi_inftype != '0':
            newrow(layout, 'Level:', self, "envi_inflevel")

    def update(self):
        for sock in [sock for sock in self.inputs[:] + self.outputs[:] if sock.links]:
            socklink(sock, self['nodeid'].split('@')[1])

    def epwrite(self, zn):
#        self.infiltype = self.envi_inftype
        infildict = {'0': '', '1': 'Flow/Zone', '2': 'Flow/Area', '3': 'Flow/ExteriorArea', '4': 'Flow/ExteriorWallArea',
                          '5': 'AirChanges/Hour', '6': 'Flow/Zone'}
        inflist = ['', '', '', '']
        infdict = {'1': '0', '2': '1', '3':'2', '4':'2', '5': '3', '6': '0'}
#        inflevel = self.envi_inflevel if self.envi_occtype != '1' or self.envi_occinftype != '6' else self.envi_inflevel * 0.001 * self.envi_occsmax
        inflist[int(infdict[self.envi_inftype])] = '{:.4f}'.format(self.envi_inflevel)
        params = ('Name', 'Zone or ZoneList Name', 'Schedule Name', 'Design Flow Rate Calculation Method', 'Design Flow Rate {m3/s}', 'Flow per Zone Floor Area {m3/s-m2}',
               'Flow per Exterior Surface Area {m3/s-m2}', 'Air Changes per Hour {1/hr}', 'Constant Term Coefficient', 'Temperature Term Coefficient',
                'Velocity Term Coefficient', 'Velocity Squared Term Coefficient')
        paramvs = [zn + '_infiltration', zn, zn + '_infsched', infildict[self.envi_inftype]] + inflist + [1, 0, 0, 0]
        return epentry('ZoneInfiltration:DesignFlowRate', params, paramvs)

class EnViHvac(bpy.types.Node, EnViNodes):
    '''Zone HVAC node'''
    bl_idname = 'EnViHvac'
    bl_label = 'HVAC'
    bl_icon = 'SOUND'

    envi_hvact = bprop("", "", False)
    envi_hvacht = fprop("", "Heating temperature:", 1, 99, 50)
    envi_hvacct = fprop("", "Cooling temperature:", -10, 20, 13)
    envi_hvachlt = eprop([('0', 'LimitFlowRate', 'LimitFlowRate'), ('1', 'LimitCapacity', 'LimitCapacity'), ('2', 'LimitFlowRateAndCapacity', 'LimitFlowRateAndCapacity'), ('3', 'NoLimit', 'NoLimit'), ('4', 'None', 'No heating')], '', "Heating limit type", '4')
    envi_hvachaf = bpy.props.FloatProperty(name = "", description = "Heating air flow rate", min = 0, max = 60, default = 1, precision = 4)
    envi_hvacshc = fprop("", "Sensible heating capacity", 0, 10000, 1000)
    envi_hvacclt = eprop([('0', 'LimitFlowRate', 'LimitFlowRate'), ('1', 'LimitCapacity', 'LimitCapacity'), ('2', 'LimitFlowRateAndCapacity', 'LimitFlowRateAndCapacity'), ('3', 'NoLimit', 'NoLimit'), ('4', 'None', 'No cooling')], '', "Cooling limit type", '4')
    envi_hvaccaf = bpy.props.FloatProperty(name = "", description = "Cooling air flow rate", min = 0, max = 60, default = 1, precision = 4)
    envi_hvacscc = fprop("", "Sensible cooling capacity", 0, 10000, 1000)
    envi_hvacoam = eprop([('0', 'None', 'None'), ('1', 'Flow/Zone', 'Flow/Zone'), ('2', 'Flow/Person', 'Flow/Person'), ('3', 'Flow/Area', 'Flow/Area'), ('4', 'Sum', 'Sum'), ('5', 'Maximum ', 'Maximum'), ('6', 'ACH/Detailed', 'ACH/Detailed')], '', "Cooling limit type", '2')
    envi_hvacfrp = fprop("", "Flow rate per person", 0, 1, 0.008)
    envi_hvacfrzfa = fprop("", "Flow rate per zone area", 0, 1, 0.008)
    envi_hvacfrz = fprop('m{}/s'.format(u'\u00b3'), "Flow rate per zone", 0, 100, 0.1)
    envi_hvacfach = fprop("", "ACH", 0, 10, 1)
    envi_hvachr = eprop([('0', 'None', 'None'), ('1', 'Sensible', 'Flow/Zone')], '', "Heat recovery type", '0')
    envi_hvachre = fprop("", "Heat recovery efficiency", 0, 1, 0.7)
    h = iprop('', '', 0, 1, 0)
    c = iprop('', '', 0, 1, 0)
    actlist = [("0", "Air supply temp", "Actuate an ideal air load system supply temperature"), ("1", "Air supply flow", "Actuate an ideal air load system flow rate"),
               ("2", "Outdoor Air supply flow", "Actuate an ideal air load system outdoor air flow rate")]
    acttype = bpy.props.EnumProperty(name="", description="Actuator type", items=actlist, default='0')
    compdict = {'0': 'AirFlow Network Window/Door Opening'}
    actdict =  {'0': ('Venting Opening Factor', 'of')}
    envi_heat = bpy.props.BoolProperty(name = "Heating", description = 'Turn on zone heating', default = 0)
    envi_htsp = bpy.props.FloatProperty(name = u'\u00b0'+"C", description = "Temperature", min = 0, max = 50, default = 20)
    envi_cool = bpy.props.BoolProperty(name = "Cooling", description = "Turn on zone cooling", default = 0)
    envi_ctsp = bpy.props.FloatProperty(name = u'\u00b0'+"C", description = "Temperature", min = 0, max = 50, default = 20)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViHvacSocket', 'HVAC')
        self.inputs.new('EnViTSchedSocket', 'HSchedule')
        self.inputs.new('EnViTSchedSocket', 'CSchedule')
        self.inputs.new('EnViActSocket', 'Actuator')
        self.inputs['HSchedule'].hide = True
        self.inputs['CSchedule'].hide = True
        self.inputs['Actuator'].hide = True

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('HVAC Template:')
        row.prop(self, 'envi_hvact')
        row = layout.row()
        row.label('Heating -----------')
        newrow(layout, 'Heating limit:', self, 'envi_hvachlt')
        if self.envi_hvachlt != '4':
            newrow(layout, 'Heating temp:', self, 'envi_hvacht')
            if self.envi_hvachlt in ('0', '2',):
                newrow(layout, 'Heating airflow:', self, 'envi_hvachaf')
            if self.envi_hvachlt in ('1', '2'):
                newrow(layout, 'Heating capacity:', self, 'envi_hvacshc')
            if not self.inputs['HSchedule'].links:
                newrow(layout, 'Thermostat level:', self, 'envi_htsp')
            newrow(layout, 'Heat recovery:', self, 'envi_hvachr')
            if self.envi_hvachr != '0':
                newrow(layout, 'HR eff.:', self, 'envi_hvachre')

        row = layout.row()
        row.label('Cooling ------------')
        newrow(layout, 'Cooling limit:', self, 'envi_hvacclt')
        if self.envi_hvacclt != '4':
            newrow(layout, 'Cooling temp:', self, 'envi_hvacct')
            if self.envi_hvacclt in ('0', '2'):
                newrow(layout, 'Cooling airflow:', self, 'envi_hvaccaf')
            if self.envi_hvacclt in ('1', '2'):
                newrow(layout, 'Cooling capacity:', self, 'envi_hvacscc')
            if not self.inputs['CSchedule'].links:
                newrow(layout, 'Thermostat level:', self, 'envi_ctsp')

        if (self.envi_hvachlt, self.envi_hvacclt) != ('4', '4'):
            row = layout.row()
            row.label('Outdoor air --------------')
            newrow(layout, 'Outdoor air:', self, 'envi_hvacoam')
            if self.envi_hvacoam in ('2', '4', '5'):
                newrow(layout, 'Flow/person (m3/s.p:', self, 'envi_hvacfrp')
            if self.envi_hvacoam in ('1', '4', '5'):
                newrow(layout, 'Zone flow (m3/s):', self, 'envi_hvacfrz')
            if self.envi_hvacoam in ('3', '4', '5'):
                newrow(layout, 'Flow/area (m3/s.a):', self, 'envi_hvacfrzfa')
            if self.envi_hvacoam in ('4', '5', '6') and not self.envi_hvact:
                newrow(layout, 'ACH', self, 'envi_hvacfach')
            newrow(layout, 'Actuator', self, 'acttype')

    def update(self):
        for sock in [sock for sock in self.inputs[:] + self.outputs[:] if sock.links]:
            socklink(sock, self['nodeid'].split('@')[1])

    def hupdate(self):
        self.inputs['HSchedule'].hide = True if self.envi_hvachlt == '4' else False
        self.inputs['CSchedule'].hide = True if self.envi_hvacclt == '4' else False
        self.h = 1 if self.envi_hvachlt != '4' else 0
        self.c = 1 if self.envi_hvacclt != '4' else 0
        self['hc'] = ('', 'SingleHeating', 'SingleCooling', 'DualSetpoint')[(not self.h and not self.c, self.h and not self.c, not self.h and self.c, self.h and self.c).index(1)]
        self['ctdict'] = {'DualSetpoint': 4, 'SingleHeating': 1, 'SingleCooling': 2}
        self['limittype'] = {'0': 'LimitFlowRate', '1': 'LimitCapacity', '2': 'LimitFlowRateAndCapacity', '3': 'NoLimit', '4': ''}

    def eptcwrite(self, zn):
        return epschedwrite(zn + '_thermocontrol', 'Control Type', ['Through: 12/31'], [['For: Alldays']], [[[['Until: 24:00,{}'.format(self['ctdict'][self['hc']])]]]])

    def ephspwrite(self, zn):
        params = ['Name', 'Setpoint Temperature Schedule Name']
        if self['hc'] ==  'DualSetpoint':
            params += ['Setpoint Temperature Schedule Name 2']
            paramvs = [zn +'_tsp', zn + '_htspsched', zn + '_ctspsched']
        elif self['hc'] == 'SingleHeating':
            paramvs = [zn +'_tsp', zn + '_htspsched']
        elif self['hc'] == 'SingleCooling':
            paramvs = [zn +'_tsp', zn + '_ctspsched']

        params2 = ('Name', 'Zone or Zonelist Name', 'Control Type Schedule Name', 'Control 1 Object Type', 'Control 1 Name')
        paramvs2 = (zn+'_thermostat', zn, zn +'_thermocontrol', 'ThermostatSetpoint:{}'.format(self['hc']), zn + '_tsp')
        return epentry('ThermostatSetpoint:{}'.format(self['hc']), params, paramvs) + epentry('ZoneControl:Thermostat', params2, paramvs2)

    def ephwrite(self, zn):
        self.hupdate()
        params = ('Name', 'Availability Schedule Name', 'Zone Supply Air Node Name', 'Zone Exhaust Air Node Name',
              "Maximum Heating Supply Air Temperature (degC)", "Minimum Cooling Supply Air Temperature (degC)",
              'Maximum Heating Supply Air Humidity Ratio (kgWater/kgDryAir)', 'Minimum Cooling Supply Air Humidity Ratio (kgWater/kgDryAir)',
              'Heating Limit', 'Maximum Heating Air Flow Rate (m3/s)', 'Maximum Sensible Heating Capacity (W)',
              'Cooling limit', 'Maximum Cooling Air Flow Rate (m3/s)', 'Maximum Total Cooling Capacity (W)', 'Heating Availability Schedule Name',
              'Cooling Availability Schedule Name', 'Dehumidification Control Type', 'Cooling Sensible Heat Ratio (dimensionless)', 'Humidification Control Type',
              'Design Specification Outdoor Air Object Name', 'Outdoor Air Inlet Node Name', 'Demand Controlled Ventilation Type', 'Outdoor Air Economizer Type',
              'Heat Recovery Type', 'Sensible Heat Recovery Effectiveness (dimensionless)', 'Latent Heat Recovery Effectiveness (dimensionless)')
        paramvs = ('{}_Air'.format(zn), zn + '_hvacsched', '{}_supairnode'.format(zn), '', self.envi_hvacht, self.envi_hvacct, 0.015, 0.009, self['limittype'][self.envi_hvachlt],
                   '{:.4f}'.format(self.envi_hvachaf) if self.envi_hvachlt in ('0', '2') else '', self.envi_hvacshc if self.envi_hvachlt in ('1', '2') else '', self['limittype'][self.envi_hvacclt],
                   '{:.4f}'.format(self.envi_hvaccaf) if self.envi_hvacclt in ('0', '2') else '', self.envi_hvacscc if self.envi_hvacclt in ('1', '2') else '',
                   '', '', 'ConstantSupplyHumidityRatio', '', 'ConstantSupplyHumidityRatio', (zn + ' Outdoor Air', '')[self.envi_hvacoam == '0'], '', '', '', ('None', 'Sensible')[int(self.envi_hvachr)], self.envi_hvachre, '')
        entry = epentry('ZoneHVAC:IdealLoadsAirSystem', params, paramvs)

        if self.envi_hvacoam != '0':
            oam = {'0':'None', '1':'Flow/Zone', '2':'Flow/Person', '3':'Flow/Area', '4':'Sum', '5':'Maximum', '6':'AirChanges/Hour'}
            params2 = ('Name', 'Outdoor Air  Method', 'Outdoor Air Flow per Person (m3/s)', 'Outdoor Air Flow per Zone Floor Area (m3/s-m2)', 'Outdoor Air  Flow per Zone',
            'Outdoor Air Flow Air Changes per Hour', 'Outdoor Air Flow Rate Fraction Schedule Name')
            paramvs2 =(zn + ' Outdoor Air', oam[self.envi_hvacoam], '{:.4f}'.format(self.envi_hvacfrp) if self.envi_hvacoam in ('2', '4', '5') else '',
                        '{:.4f}'.format(self.envi_hvacfrzfa) if self.envi_hvacoam in ('3', '4', '5') else '', '{:.4f}'.format(self.envi_hvacfrz) if self.envi_hvacoam in ('1', '4', '5') else '',
                        '{:.4f}'.format(self.envi_hvacfach) if self.envi_hvacoam in ('4', '5', '6') else '', '')
            entry += epentry('DesignSpecification:OutdoorAir', params2, paramvs2)
        return entry

    def hvactwrite(self, zn):
        self.hupdate()
        oam = {'0':'None', '1':'Flow/Zone', '2':'Flow/Person', '3':'Flow/Area', '4':'Sum', '5':'Maximum', '6':'DetailedSpecification'}
        params = ('Zone Name' , 'Thermostat Name', 'System Availability Schedule Name', 'Maximum Heating Supply Air Temperature', 'Minimum Cooling Supply Air Temperature',
                'Maximum Heating Supply Air Humidity Ratio (kgWater/kgDryAir)', 'Minimum Cooling Supply Air Humidity Ratio (kgWater/kgDryAir)', 'Heating Limit', 'Maximum Heating Air Flow Rate (m3/s)',
                'Maximum Sensible Heating Capacity (W)', 'Cooling Limit', 'Maximum Cooling Air Flow Rate (m3/s)', 'Maximum Total Cooling Capacity (W)', 'Heating Availability Schedule Name',
                'Cooling Availability Schedule Name', 'Dehumidification Control Type', 'Cooling Sensible Heat Ratio', 'Dehumidification Setpoint (percent)', 'Humidification Control Type',
                'Humidification Setpoint (percent)', 'Outdoor Air Method', 'Outdoor Air Flow Rate per Person (m3/s)', 'Outdoor Air Flow Rate per Zone Floor (m3/s-m2)', 'Outdoor Air Flow Rate per Zone (m3/s)',
                'Design Specification Outdoor Air Object', 'Demand Controlled Ventilation Type', 'Outdoor Air Economizer Type', 'Heat Recovery Type', 'Sensible Heat Recovery Effectiveness',
                'Latent Heat Recovery Effectiveness')
        paramvs = (zn, '', zn + '_hvacsched', self.envi_hvacht, self.envi_hvacct, 0.015, 0.009, self['limittype'][self.envi_hvachlt], self.envi_hvachaf if self.envi_hvachlt in ('0', '2') else '',
                   self.envi_hvacshc if self.envi_hvachlt in ('1', '2') else '', self['limittype'][self.envi_hvacclt], self.envi_hvaccaf if self.envi_hvacclt in ('0', '2') else '',
                    self.envi_hvacscc if self.envi_hvacclt in ('1', '2') else '', '', '', 'None', '', '', 'None', '', oam[self.envi_hvacoam], '{:.4f}'.format(self.envi_hvacfrp) if self.envi_hvacoam in ('2', '4', '5') else '',
                    '{:.4f}'.format(self.envi_hvacfrzfa) if self.envi_hvacoam in ('3', '4', '5') else '', '{:.4f}'.format(self.envi_hvacfrz) if self.envi_hvacoam in ('1', '4', '5') else '', '', 'None', 'NoEconomizer', ('None', 'Sensible')[int(self.envi_hvachr)], self.envi_hvachre, 0.65)
        bpy.context.scene['enparams']['hvactemplate'] = 1
        return epentry('HVACTemplate:Zone:IdealLoadsAirSystem', params, paramvs)

    def epewrite(self, zn):
        params = ('Zone Name', 'Zone Conditioning Equipment List Name', 'Zone Air Inlet Node or NodeList Name', 'Zone Air Exhaust Node or NodeList Name',
                  'Zone Air Node Name', 'Zone Return Air Node Name')
        paramvs = (zn, zn + '_Equipment', zn + '_supairnode', '', zn + '_airnode', zn + '_retairnode')
        params2 = ('Name', 'Zone Equipment 1 Object Type', 'Zone Equipment 1 Name', 'Zone Equipment 1 Cooling Sequence', 'Zone Equipment 1 Heating or No-Load Sequence')
        paramvs2 = (zn + '_Equipment', 'ZoneHVAC:IdealLoadsAirSystem', zn + '_Air', 1, 1)
        return epentry('ZoneHVAC:EquipmentConnections', params, paramvs) + epentry('ZoneHVAC:EquipmentList', params2, paramvs2)

    def schedwrite(self, zn):
        pass

class EnViZone(bpy.types.Node, EnViNodes):
    '''Node describing a simulation zone'''
    bl_idname = 'EnViZone'
    bl_label = 'Zone'
    bl_icon = 'SOUND'

    def zupdate(self, context):
        obj = bpy.data.objects[self.zone]
        odm = obj.data.materials
        self.zonevolume = objvol('', obj)
        bsocklist = ['{}_{}_b'.format(odm[face.material_index].name, face.index)  for face in obj.data.polygons if odm[face.material_index].envi_boundary == 1 and odm[face.material_index].name not in [outp.sn for outp in self.outputs if outp.bl_idname == 'EnViBoundSocket']]
        ssocklist = ['{}_{}_s'.format(odm[face.material_index].name, face.index) for face in obj.data.polygons if odm[face.material_index].envi_afsurface == 1 and odm[face.material_index].envi_con_type not in ('Window', 'Door')]
        sssocklist = ['{}_{}_ss'.format(odm[face.material_index].name, face.index) for face in obj.data.polygons if odm[face.material_index].envi_afsurface == 1 and odm[face.material_index].envi_con_type in ('Window', 'Door')]

        for oname in [outputs for outputs in self.outputs if outputs.name not in bsocklist and outputs.bl_idname == 'EnViBoundSocket']:
            self.outputs.remove(oname)
        for oname in [outputs for outputs in self.outputs if outputs.name not in ssocklist and outputs.bl_idname == 'EnViSFlowSocket']:
            self.outputs.remove(oname)
        for oname in [outputs for outputs in self.outputs if outputs.name not in sssocklist and outputs.bl_idname == 'EnViSSFlowSocket']:
            self.outputs.remove(oname)
        for iname in [inputs for inputs in self.inputs if inputs.name not in bsocklist and inputs.bl_idname == 'EnViBoundSocket']:
            self.inputs.remove(iname)
        for iname in [inputs for inputs in self.inputs if inputs.name not in ssocklist and inputs.bl_idname == 'EnViSFlowSocket']:
            self.inputs.remove(iname)
        for iname in [inputs for inputs in self.inputs if inputs.name not in sssocklist and inputs.bl_idname == 'EnViSSFlowSocket']:
            self.inputs.remove(iname)

        for sock in sorted(set(bsocklist)):
            if not self.outputs.get(sock):
                self.outputs.new('EnViBoundSocket', sock).sn = sock.split('_')[-2]
            if not self.inputs.get(sock):
                self.inputs.new('EnViBoundSocket', sock).sn = sock.split('_')[-2]
        for sock in sorted(set(ssocklist)):
            if not self.outputs.get(sock):
                self.outputs.new('EnViSFlowSocket', sock).sn = sock.split('_')[-2]
            if not self.inputs.get(sock):
                self.inputs.new('EnViSFlowSocket', sock).sn = sock.split('_')[-2]
        for sock in sorted(set(sssocklist)):
            if not self.outputs.get(sock):
                self.outputs.new('EnViSSFlowSocket', sock).sn = sock.split('_')[-2]
            if not self.inputs.get(sock):
                self.inputs.new('EnViSSFlowSocket', sock).sn = sock.split('_')[-2]

    def supdate(self, context):
        for sock in [sock for sock in self.inputs if sock.bl_idname == 'EnViSenseSocket']:
            sock.name = '{}_{}'.format(self.zone, self.sensordict[self.sensortype][0])
        self.update()

    zone = bpy.props.StringProperty(update = zupdate)
    controltype = [("NoVent", "None", "No ventilation control"), ("Constant", "Constant", "From vent availability schedule"), ("Temperature", "Temperature", "Temperature control")]
    control = bpy.props.EnumProperty(name="", description="Ventilation control type", items=controltype, default='NoVent', update = supdate)
    zonevolume = bpy.props.FloatProperty(name = '')
    mvof = bpy.props.FloatProperty(default = 0, name = "", min = 0, max = 1)
    lowerlim = bpy.props.FloatProperty(default = 0, name = "", min = 0, max = 100)
    upperlim = bpy.props.FloatProperty(default = 50, name = "", min = 0, max = 100)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self['tsps'] = 1
        self.inputs.new('EnViHvacSocket', 'HVAC')
        self.inputs.new('EnViOccSocket', 'Occupancy')
        self.inputs.new('EnViEqSocket', 'Equipment')
        self.inputs.new('EnViInfSocket', 'Infiltration')
        self.inputs.new('EnViSchedSocket', 'TSPSchedule')
        self.inputs['TSPSchedule'].hide = True
        self.inputs.new('EnViSchedSocket', 'VASchedule')

    def update(self):
        if self.inputs.get('VASchedule'):
            [bi, si, ssi, bo, so , sso] = [1, 1, 1, 1, 1, 1]
            if self.control != 'Temperature' and self.inputs['TSPSchedule'].links:
                remlink(self, self.inputs['TSPSchedule'].links)
            self.inputs['TSPSchedule'].hide = False if self.control == 'Temperature' else True
            try:
                for inp in [inp for inp in self.inputs if inp.bl_idname in ('EnViBoundSocket', 'EnViSFlowSocket', 'EnViSSFlowSocket')]:
                    self.outputs[inp.name].hide = True if inp.is_linked and self.outputs[inp.name].bl_idname == inp.bl_idname else False

                for outp in [outp for outp in self.outputs if outp.bl_idname in ('EnViBoundSocket', 'EnViSFlowSocket', 'EnViSSFlowSocket')]:
                    self.inputs[outp.name].hide = True if outp.is_linked and self.inputs[outp.name].bl_idname == outp.bl_idname else False

                for inp in [inp for inp in self.inputs if inp.bl_idname in ('EnViBoundSocket', 'EnViSFlowSocket', 'EnViSSFlowSocket')]:
                    if inp.bl_idname == 'EnViBoundSocket' and not inp.hide and not inp.links:
                        bi = 0
                    if inp.bl_idname == 'EnViSFlowSocket' and not inp.hide and not inp.links:
                        si = 0
                    if inp.bl_idname == 'EnViSSFlowSocket' and not inp.hide and not inp.links:
                        ssi = 0

                for outp in [outp for outp in self.outputs if outp.bl_idname in ('EnViBoundSocket', 'EnViSFlowSocket', 'EnViSSFlowSocket')]:
                    if outp.bl_idname == 'EnViBoundSocket' and not outp.hide and not outp.links:
                        bo = 0
                    if outp.bl_idname == 'EnViSFlowSocket' and not outp.hide and not outp.links:
                        so = 0
                    if outp.bl_idname == 'EnViSSFlowSocket' and not outp.hide and not outp.links:
                        sso = 0

            except Exception as e:
                print('Tuple', e)

            nodecolour(self, (self.control == 'Temperature' and not self.inputs['TSPSchedule'].is_linked) or not all((bi, si, ssi, bo, so, sso)))

    def draw_buttons(self, context, layout):
        row=layout.row()
        row.prop(self, "zone")
        yesno = (1, 1, self.control == 'Temperature', self.control == 'Temperature', self.control == 'Temperature')
        vals = (("Volume:", "zonevolume"), ("Control type:", "control"), ("Minimum OF:", "mvof"), ("Lower:", "lowerlim"), ("Upper:", "upperlim"))
        [newrow(layout, val[0], self, val[1]) for v, val in enumerate(vals) if yesno[v]]

    def epwrite(self):
        (tempschedname, mvof, lowerlim, upperlim) = (self.zone + '_tspsched', self.mvof, self.lowerlim, self.upperlim) if self.inputs['TSPSchedule'].is_linked else ('', '', '', '')
        vaschedname = self.zone + '_vasched' if self.inputs['VASchedule'].is_linked else ''
        params = ('Zone Name',
        'Ventilation Control Mode', 'Ventilation Control Zone Temperature Setpoint Schedule Name',
        'Minimum Venting Open Factor (dimensionless)',
        'Indoor and Outdoor Temperature Diffeence Lower Limit for Maximum Venting Opening Factor (deltaC)',
        'Indoor and Outdoor Temperature Diffeence Upper Limit for Minimum Venting Opening Factor (deltaC)',
        'Indoor and Outdoor Enthalpy Difference Lower Limit For Maximum Venting Open Factor (deltaJ/kg)',
        'Indoor and Outdoor Enthalpy Difference Upper Limit for Minimun Venting Open Factor (deltaJ/kg)',
        'Venting Availability Schedule Name')

        paramvs = (self.zone, self.control, tempschedname, mvof, lowerlim, upperlim, '0.0', '300000.0', vaschedname)
        return epentry('AirflowNetwork:MultiZone:Zone', params, paramvs)


class EnViTC(bpy.types.Node, EnViNodes):
    '''Zone Thermal Chimney node'''
    bl_idname = 'EnViTC'
    bl_label = 'Chimney'
    bl_icon = 'SOUND'

    def zupdate(self, context):
        zonenames= []
        obj = bpy.data.objects[self.zone]
        odm = obj.data.materials
        bsocklist = ['{}_{}_b'.format(odm[face.material_index].name, face.index)  for face in obj.data.polygons if odm[face.material_index].envi_boundary == 1 and odm[face.material_index].name not in [outp.name for outp in self.outputs if outp.bl_idname == 'EnViBoundSocket']]

        for oname in [outputs for outputs in self.outputs if outputs.name not in bsocklist and outputs.bl_idname == 'EnViBoundSocket']:
            self.outputs.remove(oname)
        for iname in [inputs for inputs in self.inputs if inputs.name not in bsocklist and inputs.bl_idname == 'EnViBoundSocket']:
            self.inputs.remove(iname)
        for sock in sorted(set(bsocklist)):
            if not self.outputs.get(sock):
                self.outputs.new('EnViBoundSocket', sock).sn = sock.split('_')[-2]
            if not self.inputs.get(sock):
                self.inputs.new('EnViBoundSocket', sock).sn = sock.split('_')[-2]
        for sock in (self.inputs[:] + self.outputs[:]):
            if sock.bl_idname == 'EnViBoundSocket' and sock.links:
                zonenames += [(link.from_node.zone, link.to_node.zone)[sock.is_output] for link in sock.links]

        self['zonenames'] = zonenames

    def supdate(self, context):
        self.inputs.new['Schedule'].hide = False if self.sched == 'Sched' else True

    zone = bpy.props.StringProperty(default = "en_Chimney")
    sched = bpy.props.EnumProperty(name="", description="Ventilation control type", items=[('On', 'On', 'Always on'), ('Off', 'Off', 'Always off'), ('Sched', 'Schedule', 'Scheduled operation')], default='On', update = supdate)
    waw = bpy.props.FloatProperty(name = '', min = 0.001, default = 1)
    ocs = bpy.props.FloatProperty(name = '', min = 0.001, default = 1)
    odc = bpy.props.FloatProperty(name = '', min = 0.001, default = 0.6)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViBoundSocket', 'Boundary')
        self.inputs.new('EnViSchedSocket', 'Schedule')
        self.inputs.new['Schedule'].hide = True
        self['zonenames'] = []

    def draw_buttons(self, context, layout):
        newrow(layout, 'Schedule:', self, 'sched')
        newrow(layout, 'Width Absorber:', self, 'waw')
        newrow(layout, 'Outlet area:', self, 'ocs')
        newrow(layout, 'Outlet DC:', self, 'odc')

        for z, zn in enumerate(self['zonenames']):
            row=layout.row()
            row.label(zn)
            row=layout.row()
            row.prop(self, '["Distance {}"]'.format(z))
            row=layout.row()
            row.prop(self, '["Relative Ratio {}"]'.format(z))
            row=layout.row()
            row.prop(self, '["Cross Section {}"]'.format(z))

    def update(self):
        zonenames, fheights, fareas = [], [], []
        bsock = self.outputs['Boundary']

        if bsock.links:
            zonenames += [link.to_node.zone for link in bsock.links]
            fheights += [max([(bpy.data.objects[self.zone].matrix_world * vert.co)[2] for vert in bpy.data.objects[self.zone].data.vertices]) - (bpy.data.objects[link.to_node.zone].matrix_world * bpy.data.objects[link.to_node.zone].data.polygons[int(link.to_socket.sn)].center)[2] for link in bsock.links]
            fareas += [facearea(bpy.data.objects[link.to_node.zone], bpy.data.objects[link.to_node.zone].data.polygons[int(link.to_socket.sn)]) for link in bsock.links]

        self['zonenames'] = zonenames
        for z, zn in enumerate(self['zonenames']):
            self['Distance {}'.format(z)] = fheights[z]
            self['Relative Ratio {}'.format(z)] = 1.0
            self['Cross Section {}'.format(z)] = fareas[z]
        for sock in [sock for sock in self.inputs[:] + self.outputs[:] if sock.links]:
            socklink(sock, self['nodeid'].split('@')[1])

    def epwrite(self):
        scheduled = 1 if self.inputs['Schedule'].links and not self.inputs['Schedule'].links[0].to_node.use_custom_color else 0
        paramvs = ('{}_TC'.fromat(self.zone), self.zone, (self.sched, '{}_TCSched'.format(self.zone))[scheduled], self.waw, self.ocs, self.odc)
        params = ('Name of Thermal Chimney System', 'Name of Thermal Chimney Zone', 'Availability Schedule Name', 'Width of the Absorber Wall',
                  'Cross Sectional Area of Air Channel Outlet', 'Discharge Coefficient')

        for z, zn in enumerate(self['zonenames']):
            params += (' Zone Name {}'.format(z + 1), 'Distance from the Top of the Thermal Chimney to Inlet {}'.format(z + 1), 'Relative Ratios of Air Flow Rates Passing through Zone {}'.format(z + 1),
                       'Cross Sectional Areas of Air Channel Inlet {}'.format(z + 1))
            paramvs += (zn, self['Distance {}'.format(z)], self['Relative Ratio {}'.format(z)], self['Cross Section {}'.format(z)])

        return epentry('ZoneThermalChimney', params, paramvs)

class EnViSSFlowNode(bpy.types.Node, EnViNodes):
    '''Node describing a sub-surface airflow component'''
    bl_idname = 'EnViSSFlow'
    bl_label = 'Envi sub-surface flow'
    bl_icon = 'SOUND'

    def supdate(self, context):
        if self.linkmenu in ('Crack', 'EF', 'ELA') or self.controls != 'Temperature':
            if self.inputs['TSPSchedule'].is_linked:
                remlink(self, self.inputs['TSPSchedule'].links)
        if self.linkmenu in ('Crack', 'EF', 'ELA') or self.controls in ('ZoneLevel', 'NoVent'):
            if self.inputs['VASchedule'].is_linked:
                remlink(self, self.inputs['VASchedule'].links)


        self.inputs['TSPSchedule'].hide = False if self.linkmenu in ('SO', 'DO', 'HO') and self.controls == 'Temperature' else True
        (self.inputs['VASchedule'].hide, self.inputs['Actuator'].hide) = (False, False) if self.linkmenu in ('SO', 'DO', 'HO') else (True, True)
        self.legal()

    linktype = [("SO", "Simple Opening", "Simple opening element"),("DO", "Detailed Opening", "Detailed opening element"),
        ("HO", "Horizontal Opening", "Horizontal opening element"),("Crack", "Crack", "Crack aperture used for leakage calculation"),
        ("ELA", "ELA", "Effective leakage area")]

    linkmenu = bpy.props.EnumProperty(name="Type", description="Linkage type", items=linktype, default='SO', update = supdate)

    wdof1 = bpy.props.FloatProperty(default = 0.1, min = 0.001, max = 1, name = "", description = 'Opening Factor 1 (dimensionless)')
    controltype = [("ZoneLevel", "ZoneLevel", "Zone level ventilation control"), ("NoVent", "None", "No ventilation control"),
                   ("Constant", "Constant", "From vent availability schedule"), ("Temperature", "Temperature", "Temperature control")]
    controls = bpy.props.EnumProperty(name="", description="Ventilation control type", items=controltype, default='ZoneLevel', update = supdate)
    mvof = bpy.props.FloatProperty(default = 0, min = 0, max = 1, name = "", description = 'Minimium venting open factor')
    lvof = bpy.props.FloatProperty(default = 0, min = 0, max = 100, name = "", description = 'Indoor and Outdoor Temperature Difference Lower Limit For Maximum Venting Open Factor (deltaC)')
    uvof = bpy.props.FloatProperty(default = 1, min = 1, max = 100, name = "", description = 'Indoor and Outdoor Temperature Difference Upper Limit For Minimum Venting Open Factor (deltaC)')
    amfcc = bpy.props.FloatProperty(default = 0.001, min = 0.00001, max = 1, name = "", description = 'Air Mass Flow Coefficient When Opening is Closed (kg/s-m)')
    amfec = bpy.props.FloatProperty(default = 0.65, min = 0.5, max = 1, name = '', description =  'Air Mass Flow Exponent When Opening is Closed (dimensionless)')
    lvo = bpy.props.EnumProperty(items = [('NonPivoted', 'NonPivoted', 'Non pivoting opening'), ('HorizontallyPivoted', 'HPivoted', 'Horizontally pivoting opening')], name = '', default = 'NonPivoted', description = 'Type of Rectanguler Large Vertical Opening (LVO)')
    ecl = bpy.props.FloatProperty(default = 0.0, min = 0, name = '', description = 'Extra Crack Length or Height of Pivoting Axis (m)')
    noof = bpy.props.IntProperty(default = 2, min = 2, max = 4, name = '', description = 'Number of Sets of Opening Factor Data')
    spa = bpy.props.IntProperty(default = 90, min = 0, max = 90, name = '', description = 'Sloping Plane Angle')
    dcof = bpy.props.FloatProperty(default = 1, min = 0.01, max = 1, name = '', description = 'Discharge Coefficient')
    ddtw = bpy.props.FloatProperty(default = 0.0001, min = 0, max = 10, name = '', description = 'Minimum Density Difference for Two-way Flow')
    amfc = bpy.props.FloatProperty(min = 0.001, max = 1, default = 0.01, name = "")
    amfe = bpy.props.FloatProperty(min = 0.5, max = 1, default = 0.65, name = "")
    dlen = bpy.props.FloatProperty(default = 2, name = "")
    dhyd = bpy.props.FloatProperty(default = 0.1, name = "")
    dcs = bpy.props.FloatProperty(default = 0.1, name = "")
    dsr = bpy.props.FloatProperty(default = 0.0009, name = "")
    dlc = bpy.props.FloatProperty(default = 1.0, name = "")
    dhtc = bpy.props.FloatProperty(default = 0.772, name = "")
    dmtc = bpy.props.FloatProperty(default = 0.0001, name = "")
    fe = bpy.props.FloatProperty(default = 0.6, min = 0, max = 1, name = "")
    rpd = bpy.props.FloatProperty(default = 4, min = 0.1, max = 50, name = "")
    of1 = bpy.props.FloatProperty(default = 0.0, min = 0.0, max = 0, name = '', description = 'Opening Factor {} (dimensionless)')
    (of2, of3, of4) =  [bpy.props.FloatProperty(default = 1.0, min = 0.01, max = 1, name = '', description = 'Opening Factor {} (dimensionless)'.format(i)) for i in range(3)]
    (dcof1, dcof2, dcof3, dcof4) = [bpy.props.FloatProperty(default = 0.0, min = 0.01, max = 1, name = '', description = 'Discharge Coefficient for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    (wfof1, wfof2, wfof3, wfof4) = [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Width Factor for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    (hfof1, hfof2, hfof3, hfof4) = [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Height Factor for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    (sfof1, sfof2, sfof3, sfof4) = [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Start Height Factor for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    dcof = bpy.props.FloatProperty(default = 0.2, min = 0.01, max = 1, name = '', description = 'Discharge Coefficient')
    extnode =  bpy.props.BoolProperty(default = 0)
    actlist = [("0", "Opening factor", "Actuate the opening factor")]
    acttype = bpy.props.EnumProperty(name="", description="Actuator type", items=actlist, default='0')
    compdict = {'0': 'AirFlow Network Window/Door Opening'}
    actdict =  {'0': ('Venting Opening Factor', 'of')}
    adict = {'Window': 'win', 'Door': 'door'}

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self['init'] = 1
        self['ela'] = 1.0
        self.inputs.new('EnViSchedSocket', 'VASchedule')
        self.inputs.new('EnViSchedSocket', 'TSPSchedule')
        self.inputs.new('EnViActSocket', 'Actuator')
        self.inputs['TSPSchedule'].hide = True
        self.inputs.new('EnViSSFlowSocket', 'Node 1', identifier = 'Node1_s')
        self.inputs.new('EnViSSFlowSocket', 'Node 2', identifier = 'Node2_s')
        self.outputs.new('EnViSSFlowSocket', 'Node 1', identifier = 'Node1_s')
        self.outputs.new('EnViSSFlowSocket', 'Node 2', identifier = 'Node2_s')
        self.color = (1.0, 0.3, 0.3)
        self['layoutdict'] = {'SO':(('Closed FC', 'amfcc'), ('Closed FE', 'amfec'), ('Density diff', 'ddtw'), ('DC', 'dcof')), 'DO':(('Closed FC', 'amfcc'), ('Closed FE', 'amfec'),
                           ('Opening type', 'lvo'), ('Crack length', 'ecl'), ('OF Number', 'noof'), ('OF1', 'of1'), ('DC1', 'dcof1'), ('Width OF1', 'wfof1'), ('Height OF1', 'hfof1'),
                            ('Start height OF1', 'sfof1'), ('OF2', 'of2'), ('DC2', 'dcof2'), ('Width OF2', 'wfof2'), ('Height OF2', 'hfof2'), ('Start height OF2', 'sfof2')),
                            'OF3': (('OF3', 'of3'), ('DC3', 'dcof3'), ('Width OF3', 'wfof3'), ('Height OF3', 'hfof3'), ('Start height OF3', 'sfof3')),
                            'OF4': (('OF4', 'of4'), ('DC4', 'dcof4'), ('Width OF4', 'wfof4'), ('Height OF4', 'hfof4'), ('Start height OF4', 'sfof4')),
                            'HO': (('Closed FC', 'amfcc'), ('Closed FE', 'amfec'), ('Slope', 'spa'), ('DC', 'dcof')), 'Crack': (('Coefficient', 'amfc'), ('Exponent', 'amfe')),
                            'ELA': (('ELA', '["ela"]'), ('DC', 'dcof'), ('PA diff', 'rpd'), ('FE', 'fe'))}

    def update(self):
        if self.get('layoutdict'):
            for sock in self.inputs[:] + self.outputs[:]:
                socklink(sock, self['nodeid'].split('@')[1])
            if self.linkmenu == 'ELA':
                retelaarea(self)
            self.extnode = 0
            for sock in self.inputs[:] + self.outputs[:]:
                for l in sock.links:
                    if (l.from_node, l.to_node)[sock.is_output].bl_idname == 'EnViExt':
                        self.extnode = 1
            if self.outputs.get('Node 2'):
                sockhide(self, ('Node 1', 'Node 2'))
            znodes =  [(sock.links[0].from_node, sock.links[0].to_node)[sock.is_output] for sock in self.inputs[:] + self.outputs[:] if sock.links and sock.bl_idname == 'EnViSSFlowSocket' and (sock.links[0].from_node, sock.links[0].to_node)[sock.is_output].bl_idname == 'EnViZone']

            if znodes:
                for sock in self.inputs:
                    if sock.bl_idname == 'EnViActSocket':
                        obj = bpy.data.objects[znodes[0].zone]
                        odm = obj.data.materials
                        sock.name = ['{}_{}_{}'.format(self.adict[odm[face.material_index].envi_con_type], znodes[0].zone, face.index) for face in obj.data.polygons if odm[face.material_index].envi_afsurface == 1 and odm[face.material_index].envi_con_type in ('Window', 'Door')][0]
            self.legal()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'linkmenu')
        if self.linkmenu in ('SO', 'DO', 'HO'):
            newrow(layout, 'Win/Door OF:', self, 'wdof1')
            newrow(layout, "Control type:", self, 'controls')
            newrow(layout, "Actuator:", self, 'acttype')
            if self.linkmenu in ('SO', 'DO') and self.controls == 'Temperature':
                newrow(layout, "Limit OF:", self, 'mvof')
                newrow(layout, "Lower OF:", self, 'lvof')
                newrow(layout, "Upper OF:", self, 'uvof')

        row = layout.row()
        row.label('Component options:')

        for vals in self['layoutdict'][self.linkmenu]:
            newrow(layout, vals[0], self, vals[1])
        if self.noof > 2:
            for of3vals in self['layoutdict']['OF3']:
                newrow(layout, of3vals[0], self, of3vals[1])
            if self.noof > 3:
                for of4vals in self['layoutdict']['OF4']:
                    newrow(layout, of4vals[0], self, of4vals[1])

    def epwrite(self, exp_op, enng):
        surfentry, en, snames = '', '', []
        tspsname =  self.inputs['TSPSchedule'].links[0].from_node.name if self.inputs['TSPSchedule'].is_linked and self.linkmenu in ('SO', 'DO', 'HO') and self.controls == 'Temperature' else ''
        vasname = self.inputs['VASchedule'].links[0].from_node.name if self.inputs['VASchedule'].is_linked and self.linkmenu in ('SO', 'DO', 'HO') else ''
        for sock in (self.inputs[:] + self.outputs[:]):
            for link in sock.links:
                othernode = (link.from_node, link.to_node)[sock.is_output]
                if othernode.bl_idname == 'EnViExt' and enng['enviparams']['wpca'] == 1:
                    en = othernode.name

        if self.linkmenu == 'DO':
            cfparams = ('Name', 'Air Mass Flow Coefficient When Opening is Closed (kg/s-m)', 'Air Mass Flow Exponent When Opening is Closed (dimensionless)',
                       'Type of Rectanguler Large Vertical Opening (LVO)', 'Extra Crack Length or Height of Pivoting Axis (m)', 'Number of Sets of Opening Factor Data',
                        'Opening Factor 1 (dimensionless)', 'Discharge Coefficient for Opening Factor 1 (dimensionless)', 'Width Factor for Opening Factor 1 (dimensionless)',
                        'Height Factor for Opening Factor 1 (dimensionless)', 'Start Height Factor for Opening Factor 1 (dimensionless)', 'Opening Factor 2 (dimensionless)',
                        'Discharge Coefficient for Opening Factor 2 (dimensionless)', 'Width Factor for Opening Factor 2 (dimensionless)', 'Height Factor for Opening Factor 2 (dimensionless)',
                        'Start Height Factor for Opening Factor 2 (dimensionless)', 'Opening Factor 3 (dimensionless)', 'Discharge Coefficient for Opening Factor 3 (dimensionless)',
                        'Width Factor for Opening Factor 3 (dimensionless)', 'Height Factor for Opening Factor 3 (dimensionless)', 'Start Height Factor for Opening Factor 3 (dimensionless)',
                        'Opening Factor 4 (dimensionless)', 'Discharge Coefficient for Opening Factor 4 (dimensionless)', 'Width Factor for Opening Factor 4 (dimensionless)',
                        'Height Factor for Opening Factor 4 (dimensionless)', 'Start Height Factor for Opening Factor 4 (dimensionless)')
            cfparamsv = ('{}_{}'.format(self.name, self.linkmenu), self.amfcc, self.amfec, self.lvo, self.ecl, self.noof, '{:3f}'.format(self.of1), self.dcof1,self.wfof1, self.hfof1, self.sfof1,
                         self.of2, self.dcof2,self.wfof2, self.hfof2, self.sfof2, self.of3, self.dcof3,self.wfof3, self.hfof3, self.sfof3, self.of4, self.dcof4,self.wfof4, self.hfof4, self.sfof4)

        elif self.linkmenu == 'SO':
            cfparams = ('Name', 'Air Mass Flow Coefficient When Opening is Closed (kg/s-m)', 'Air Mass Flow Exponent When Opening is Closed (dimensionless)', 'Minimum Density Difference for Two-Way Flow (kg/m3)', 'Discharge Coefficient (dimensionless)')
            cfparamsv = ('{}_{}'.format(self.name, self.linkmenu), self.amfcc, self.amfec, self.ddtw, self.dcof)

        elif self.linkmenu == 'HO':
            if not (self.inputs['Node 1'].is_linked or self.inputs['Node 2'].is_linked and self.outputs['Node 1'].is_linked or self.outputs['Node 2'].is_linked):
                exp_op.report({'ERROR'}, 'All horizonal opening surfaces must sit on the boundary between two thermal zones')

            cfparams = ('Name', 'Air Mass Flow Coefficient When Opening is Closed (kg/s-m)', 'Air Mass Flow Exponent When Opening is Closed (dimensionless)', 'Sloping Plane Angle (deg)', 'Discharge Coefficient (dimensionless)')
            cfparamsv = ('{}_{}'.format(self.name, self.linkmenu), self.amfcc, self.amfec, self.spa, self.dcof)

        elif self.linkmenu == 'ELA':
            cfparams = ('Name', 'Effective Leakage Area (m2)', 'Discharge Coefficient (dimensionless)', 'Reference Pressure Difference (Pa)', 'Air Mass Flow Exponent (dimensionless)')
            cfparamsv = ('{}_{}'.format(self.name, self.linkmenu), '{:5f}'.format(self['ela']), '{:2f}'.format(self.dcof), '{:1f}'.format(self.rpd), '{:3f}'.format(self.amfe))

        elif self.linkmenu == 'Crack':
            crname = 'ReferenceCrackConditions' if enng['enviparams']['crref'] == 1 else ''
            cfparams = ('Name', 'Air Mass Flow Coefficient at Reference Conditions (kg/s)', 'Air Mass Flow Exponent (dimensionless)', 'Reference Crack Conditions')
            cfparamsv = ('{}_{}'.format(self.name, self.linkmenu), self.amfc, self.amfe, crname)

        cftypedict = {'DO':'Component:DetailedOpening', 'SO':'Component:SimpleOpening', 'HO':'Component:HorizontalOpening', 'Crack':'Surface:Crack', 'ELA':'Surface:EffectiveLeakageArea'}
        cfentry = epentry('AirflowNetwork:MultiZone:{}'.format(cftypedict[self.linkmenu]), cfparams, cfparamsv)

        for sock in (self.inputs[:] + self.outputs[:]):
            for link in sock.links:
                othersock = (link.from_socket, link.to_socket)[sock.is_output]
                othernode = (link.from_node, link.to_node)[sock.is_output]

                if sock.bl_idname == 'EnViSSFlowSocket' and othernode.bl_idname == 'EnViZone':
                    zn = othernode.zone
                    sn = othersock.sn
                    snames.append(('win-', 'door-')[bpy.data.materials[othersock.name[:-len(sn)-4]].envi_con_type == 'Door']+zn+'_'+sn)
                    params = ('Surface Name', 'Leakage Component Name', 'External Node Name', 'Window/Door Opening Factor')
                    paramvs = (snames[-1], '{}_{}'.format(self.name, self.linkmenu), en, self.wdof1)
                    if self.linkmenu in ('SO', 'DO'):
                        params += ('Ventilation Control Mode', 'Vent Temperature Schedule Name', 'Limit  Value on Multiplier for Modulating Venting Open Factor (dimensionless)', \
                        'Lower Value on Inside/Outside Temperature Difference for Modulating the Venting Open Factor (deltaC)', 'Upper Value on Inside/Outside Temperature Difference for Modulating the Venting Open Factor (deltaC)',\
                        'Lower Value on Inside/Outside Enthalpy Difference for Modulating the Venting Open Factor (J/kg)', 'Upper Value on Inside/Outside Enthalpy Difference for Modulating the Venting Open Factor (J/kg)', 'Venting Availability Schedule Name')
                        paramvs += (self.controls if self.linkmenu in ('SO', 'DO', 'HO') else '', tspsname, '{:.2f}'.format(self.mvof), self.lvof, self.uvof, '', '', vasname)
                    surfentry += epentry('AirflowNetwork:MultiZone:Surface', params, paramvs)
        self['sname'] = snames
        self.legal()
        return surfentry + cfentry

    def legal(self):
        nodecolour(self, 1) if (self.controls == 'Temperature' and not self.inputs['TSPSchedule'].is_linked) or (bpy.data.node_groups[self['nodeid'].split('@')[1]]['enviparams']['wpca'] and not self.extnode) else nodecolour(self, 0)
        for sock in self.inputs[:] + self.outputs[:]:
            sock.hide = sock.hide
        bpy.data.node_groups[self['nodeid'].split('@')[1]].interface_update(bpy.context)

class EnViSFlowNode(bpy.types.Node, EnViNodes):
    '''Node describing a surface airflow component'''
    bl_idname = 'EnViSFlow'
    bl_label = 'Envi surface flow'
    bl_icon = 'SOUND'

    linktype = [("Crack", "Crack", "Crack aperture used for leakage calculation"),
        ("ELA", "ELA", "Effective leakage area")]

    linkmenu = bpy.props.EnumProperty(name="Type", description="Linkage type", items=linktype, default='ELA')
    of = bpy.props.FloatProperty(default = 0.1, min = 0.001, max = 1, name = "", description = 'Opening Factor 1 (dimensionless)')
    ecl = bpy.props.FloatProperty(default = 0.0, min = 0, name = '', description = 'Extra Crack Length or Height of Pivoting Axis (m)')
    dcof = bpy.props.FloatProperty(default = 1, min = 0, max = 1, name = '', description = 'Discharge Coefficient')
    amfc = bpy.props.FloatProperty(min = 0.001, max = 1, default = 0.01, name = "")
    amfe = bpy.props.FloatProperty(min = 0.5, max = 1, default = 0.65, name = "")
    dlen = bpy.props.FloatProperty(default = 2, name = "")
    dhyd = bpy.props.FloatProperty(default = 0.1, name = "")
    dcs = bpy.props.FloatProperty(default = 0.1, name = "")
    dsr = bpy.props.FloatProperty(default = 0.0009, name = "")
    dlc = bpy.props.FloatProperty(default = 1.0, name = "")
    dhtc = bpy.props.FloatProperty(default = 0.772, name = "")
    dmtc = bpy.props.FloatProperty(default = 0.0001, name = "")
    cf = bpy.props.FloatProperty(default = 1, min = 0, max = 1, name = "")
    rpd = bpy.props.FloatProperty(default = 4, min = 0.1, max = 50, name = "")
    fe = bpy.props.FloatProperty(default = 4, min = 0.1, max = 1, name = "", description = 'Fan Efficiency')
    pr = bpy.props.IntProperty(default = 500, min = 1, max = 10000, name = "", description = 'Fan Pressure Rise')
    mf = bpy.props.FloatProperty(default = 0.1, min = 0.001, max = 5, name = "", description = 'Maximum Fan Flow Rate (m3/s)')
    extnode =  bpy.props.BoolProperty(default = 0)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self['ela'] = 1.0
        self.inputs.new('EnViSFlowSocket', 'Node 1')
        self.inputs.new('EnViSFlowSocket', 'Node 2')
        self.outputs.new('EnViSFlowSocket', 'Node 1')
        self.outputs.new('EnViSFlowSocket', 'Node 2')

    def update(self):
        for sock in (self.inputs[:] + self.outputs[:]):
            socklink(sock, self['nodeid'].split('@')[1])
        if self.linkmenu == 'ELA':
            retelaarea(self)
        self.extnode = 0
        for sock in self.inputs[:] + self.outputs[:]:
            for l in sock.links:
                if (l.from_node, l.to_node)[sock.is_output].bl_idname == 'EnViExt':
                    self.extnode = 1
        if self.outputs.get('Node 2'):
            sockhide(self, ('Node 1', 'Node 2'))
        self.legal()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'linkmenu')
        layoutdict = {'Crack':(('Coefficient', 'amfc'), ('Exponent', 'amfe')), 'ELA':(('ELA', '["ela"]'), ('DC', 'dcof'), ('PA diff', 'rpd'), ('FE', 'amfe')),
        'EF':(('Off FC', 'amfc'), ('Off FE', 'amfe'), ('Efficiency', 'fe'), ('PA rise', 'pr'), ('Max flow', 'mf'))}
        for vals in layoutdict[self.linkmenu]:
            newrow(layout, '{}:'.format(vals[0]), self, vals[1])

    def epwrite(self, exp_op, enng):
        fentry, crentry, zn, en, surfentry, crname, snames = '', '', '', '', '', '', []
        for sock in (self.inputs[:] + self.outputs[:]):
            for link in sock.links:
                othernode = (link.from_node, link.to_node)[sock.is_output]
                if othernode.bl_idname == 'EnViExt' and enng['enviparams']['wpca'] == 1:
                    en = othernode.name

        if self.linkmenu == 'ELA':
            cfparams = ('Name', 'Effective Leakage Area (m2)', 'Discharge Coefficient (dimensionless)', 'Reference Pressure Difference (Pa)', 'Air Mass Flow Exponent (dimensionless)')
            cfparamvs = ('{}_{}'.format(self.name, self.linkmenu), self['ela'], self.dcof, self.rpd, self.amfe)

        elif self.linkmenu == 'Crack':
            crname = 'ReferenceCrackConditions' if enng['enviparams']['crref'] == 1 else ''
            cfparams = ('Name', 'Air Mass Flow Coefficient at Reference Conditions (kg/s)', 'Air Mass Flow Exponent (dimensionless)', 'Reference Crack Conditions')
            cfparamvs = ('{}_{}'.format(self.name, self.linkmenu), self.amfc, self.amfe, crname)

        elif self.linkmenu == 'EF':
            cfparams = ('Name', 'Air Mass Flow Coefficient When the Zone Exhaust Fan is Off at Reference Conditions (kg/s)', 'Air Mass Flow Exponent When the Zone Exhaust Fan is Off (dimensionless)')
            cfparamvs = ('{}_{}'.format(self.name, self.linkmenu), self.amfc, self.amfe)
            schedname = self.inputs['Fan Schedule'].links[0].from_node.name if self.inputs['Fan Schedule'].is_linked else ''
            for sock in [inp for inp in self.inputs if 'Node' in inp.name and inp.is_linked] + [outp for outp in self.outputs if 'Node' in outp.name and outp.is_linked]:
                zname = (sock.links[0].from_node, sock.links[0].to_node)[sock.is_output].zone
            fparams = ('Name', 'Availability Schedule Name', 'Fan Efficiency', 'Pressure Rise (Pa)', 'Maximum Flow Rate (m3/s)', 'Air Inlet Node Name', 'Air Outlet Node Name', 'End-Use Subcategory')
            fparamvs = ('{}_{}'.format(self.name,  self.linkmenu), schedname, self.fe, self.pr, self.mf, '{} Exhaust Node'.format(zname), '{} Exhaust Fan Outlet Node'.format(zname), '{} Exhaust'.format(zname))
            fentry = epentry('Fan:ZoneExhaust', fparams, fparamvs)

        cftypedict = {'Crack':'Surface:Crack', 'ELA':'Surface:EffectiveLeakageArea', 'EF': 'Component:ZoneExhaustFan'}
        cfentry = epentry('AirflowNetwork:MultiZone:{}'.format(cftypedict[self.linkmenu]), cfparams, cfparamvs)

        for sock in self.inputs[:] + self.outputs[:]:
            for link in sock.links:
                othersock = (link.from_socket, link.to_socket)[sock.is_output]
                othernode = (link.from_node, link.to_node)[sock.is_output]
                if sock.bl_idname == 'EnViSFlowSocket' and othernode.bl_idname == 'EnViZone':
                    sn = othersock.sn
                    zn = othernode.zone
                    snames.append(zn+'_'+sn)
                    params = ('Surface Name', 'Leakage Component Name', 'External Node Name', 'Window/Door Opening Factor, or Crack Factor (dimensionless)')
                    paramvs = (snames[-1], '{}_{}'.format(self.name, self.linkmenu), en, self.of)
                    surfentry += epentry('AirflowNetwork:MultiZone:Surface', params, paramvs)

        self['sname'] = snames
        self.legal()
        return surfentry + cfentry + crentry + fentry

    def legal(self):
        nodecolour(self, 1) if not self.extnode and bpy.data.node_groups[self['nodeid'].split('@')[1]]['enviparams']['wpca'] else nodecolour(self, 0)
        bpy.data.node_groups[self['nodeid'].split('@')[1]].interface_update(bpy.context)

class EnViExtNode(bpy.types.Node, EnViNodes):
    '''Node describing an EnVi external node'''
    bl_idname = 'EnViExt'
    bl_label = 'Envi External Node'
    bl_icon = 'SOUND'

    height = bpy.props.FloatProperty(default = 1.0)
    (wpc1, wpc2, wpc3, wpc4, wpc5, wpc6, wpc7, wpc8, wpc9, wpc10, wpc11, wpc12) = [bpy.props.FloatProperty(name = '', default = 0, min = -1, max = 1) for x in range(12)]
    enname = bpy.props.StringProperty()

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('EnViSSFlowSocket', 'Sub surface')
        self.inputs.new('EnViSFlowSocket', 'Surface')
        self.outputs.new('EnViSSFlowSocket', 'Sub surface')
        self.outputs.new('EnViSFlowSocket', 'Surface')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'height')
        row= layout.row()
        row.label('WPC Values')
        for w in range(1, 13):
            row = layout.row()
            row.prop(self, 'wpc{}'.format(w))

    def update(self):
        for sock in self.inputs[:] + self.outputs[:]:
            socklink(sock, self['nodeid'].split('@')[1])
        sockhide(self, ('Sub surface', 'Surface'))


    def epwrite(self, enng):
        enentry, wpcname, wpcentry = '', '', ''
        for sock in self.inputs[:] + self.outputs[:]:
            for link in sock.links:
                wpcname = self.name+'_wpcvals'
                wpcs = (self.wpc1, self.wpc2, self.wpc3, self.wpc4, self.wpc5, self.wpc6, self.wpc7, self.wpc8, self.wpc9, self.wpc10, self.wpc11, self.wpc12)
                wparams = ['Name', 'AirflowNetwork:MultiZone:WindPressureCoefficientArray Name'] + ['Wind Pressure Coefficient Value {} (dimensionless)'.format(w + 1) for w in range(enng['enviparams']['wpcn'])]
                wparamvs =  ['{}_wpcvals'.format(self.name), 'WPC Array'] + [wpcs[wp] for wp in range(len(wparams))]
                wpcentry = epentry('AirflowNetwork:MultiZone:WindPressureCoefficientValues', wparams, wparamvs)
                params = ['Name', 'External Node Height (m)', 'Wind Pressure Coefficient Values Object Name']
                paramvs = [self.name, self.height, wpcname]
                enentry = epentry('AirflowNetwork:MultiZone:ExternalNode', params, paramvs)
        return enentry + wpcentry

class EnViSched(bpy.types.Node, EnViNodes):
    '''Node describing a schedule'''
    bl_idname = 'EnViSched'
    bl_label = 'Schedule'
    bl_icon = 'SOUND'

    def tupdate(self, context):
        try:
            err = 0
            if self.t2 <= self.t1 and self.t1 < 365:
                self.t2 = self.t1 + 1
                if self.t3 <= self.t2 and self.t2 < 365:
                    self.t3 = self.t2 + 1
                    if self.t4 != 365:
                        self.t4 = 365

            tn = (self.t1, self.t2, self.t3, self.t4).index(365) + 1
            if max((self.t1, self.t2, self.t3, self.t4)[:tn]) != 365:
                err = 1
            if any([not f for f in (self.f1, self.f2, self.f3, self.f4)[:tn]]):
                err = 1
            if any([not u or len(u.split(';')) != len((self.f1, self.f2, self.f3, self.f4)[i].split(' ')) for i, u in enumerate((self.u1, self.u2, self.u3, self.u4)[:tn])]):
                err = 1

            for f in (self.f1, self.f2, self.f3, self.f4)[:tn]:
                for fd in f.split(' '):
                    if not fd or (fd and fd.upper() not in ("ALLDAYS", "WEEKDAYS", "WEEKENDS", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", "ALLOTHERDAYS")):
                        err = 1

            for u in (self.u1, self.u2, self.u3, self.u4)[:tn]:
                for uf in u.split(';'):
                    for ud in uf.split(','):
                        if len(ud.split()[0].split(':')) != 2 or int(ud.split()[0].split(':')[0]) not in range(1, 25) or len(ud.split()[0].split(':')) != 2 or not ud.split()[0].split(':')[1].isdigit() or int(ud.split()[0].split(':')[1]) not in range(0, 60):
                            err = 1
            nodecolour(self, err)

        except:
            nodecolour(self, 1)

    (u1, u2, u3, u4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (; separated for each 'For', comma separated for each day, space separated for each time value pair)", update = tupdate)] * 4
    (f1, f2, f3, f4) =  [bpy.props.StringProperty(name = "", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays", update = tupdate)] * 4
    (t1, t2, t3, t4) = [bpy.props.IntProperty(name = "", default = 365, min = 1, max = 365, update = tupdate)] * 4

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViSchedSocket', 'Schedule')
        self['scheddict'] = {'TSPSchedule': 'Any Number', 'VASchedule': 'Fraction', 'Fan Schedule': 'Fraction', 'HSchedule': 'Temperature', 'CSchedule': 'Temperature'}
        self.tupdate(context)
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        uvals, u = (1, self.u1, self.u2, self.u3, self.u4), 0
        tvals = (0, self.t1, self.t2, self.t3, self.t4)
        while uvals[u] and tvals[u] < 365:
            [newrow(layout, v[0], self, v[1]) for v in (('End day {}:'.format(u+1), 't'+str(u+1)), ('Fors:', 'f'+str(u+1)), ('Untils:', 'u'+str(u+1)))]
            u += 1

    def update(self):
        for sock in [sock for sock in self.inputs[:] + self.outputs[:] if sock.links]:
            socklink(sock, self['nodeid'].split('@')[1])
        bpy.data.node_groups[self['nodeid'].split('@')[1]].interface_update(bpy.context)

    def epwrite(self, name, stype):
        schedtext = ''
        for tosock in [link.to_socket for link in self.outputs['Schedule'].links]:
            if not schedtext:
                ths = [self.t1, self.t2, self.t3, self.t4]
                fos = [fs for fs in (self.f1, self.f2, self.f3, self.f4) if fs]
                uns = [us for us in (self.u1, self.u2, self.u3, self.u4) if us]
                ts, fs, us = rettimes(ths, fos, uns)
                schedtext = epschedwrite(name, stype, ts, fs, us)
                return schedtext
        return schedtext

class EnViFanNode(bpy.types.Node, EnViNodes):
    '''Node describing a fan component'''
    bl_idname = 'EnViFan'
    bl_label = 'Envi Fan'
    bl_icon = 'SOUND'

    fantype = [("Volume", "Constant Volume", "Constant volume flow fan component")]
    fantypeprop = bpy.props.EnumProperty(name="Type", description="Linkage type", items=fantype, default='Volume')
    fname = bpy.props.StringProperty(default = "", name = "")
    (feff, fpr, fmfr, fmeff, fmaf) = [bpy.props.FloatProperty(default = d, name = "") for d in (0.7, 600.0, 1.9, 0.9, 1.0)]

    def init(self, context):
        self.inputs.new('EnViCAirSocket', 'Extract from')
        self.inputs.new('EnViCAirSocket', 'Supply to')
        self.outputs.new('NodeSocket', 'Schedule')
        self.outputs.new('EnViCAirSocket', 'Extract from')
        self.outputs.new('EnViCAirSocket', 'Supply to')

    def update(self):
        try:
            fsocknames = ('Extract from', 'Supply to')
            for ins in [insock for insock in self.inputs if insock.name in fsocknames]:
                self.outputs[ins.name].hide = True if ins.is_linked else False
            for outs in [outsock for outsock in self.outputs if outsock.name in fsocknames]:
                self.inputs[outs.name].hide = True if outs.is_linked else False
        except:
            pass

    def draw_buttons(self, context, layout):
        layout.prop(self, 'fantypeprop')
        if self.fantypeprop == "Volume":
            vals = (("Name:", 'fname'), ("Efficiency:", 'feff'), ("Pressure Rise (Pa):", 'fpr'), ("Max flow rate:", 'fmfr'), ("Motor efficiency:", 'fmeff'), ("Airstream fraction:",'fmaf'))
            [newrow(layout, val[0], self, val[1]) for val in vals]

class EnViProgNode(bpy.types.Node, EnViNodes):
    '''Node describing an EMS Program'''
    bl_idname = 'EnViProg'
    bl_label = 'Envi Program'
    bl_icon = 'SOUND'

    text_file = bpy.props.StringProperty(description="Textfile to show")

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('EnViSenseSocket', 'Sensor')
        self.outputs.new('EnViActSocket', 'Actuator')
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        layout.prop_search(self, 'text_file', bpy.data, 'texts', text='File', icon='TEXT')

    def update(self):
        for sock in [sock for sock in self.inputs if sock.links]:
            socklink(sock, self['nodeid'].split('@')[1])
        nodecolour(self, not all([sock.links for sock in self.outputs]))

    def epwrite(self):
        sentries = ''
        for slink in self.outputs['Sensor'].links:
            snode = slink.to_node
            sparams = ('Name', 'Output:Variable or Output:Meter Index Key Name', 'EnergyManagementSystem:Sensor')
            if snode.bl_idname == 'EnViEMSZone':
                sparamvs = ('{}_{}'.format(snode.emszone, snode.sensordict[snode.sensortype][0]), '{}'.format(snode.emszone), snode.sensordict[snode.sensortype][1])
#                sentries += epentry('EnergyManagementSystem:Sensor', sparams, sparamvs)
            elif snode.bl_label == 'EnViOcc':
                for zlink in snode.outputs['Occupancy'].links:
                    znode = zlink.to_node
                    sparamvs = ('{}_{}'.format(znode.zone, snode.sensordict[snode.sensortype][0]), '{}'.format(znode.zone), snode.sensordict[snode.sensortype][1])
            sentries += epentry('EnergyManagementSystem:Sensor', sparams, sparamvs)

        aentries = ''
        for alink in self.outputs['Actuator'].links:
            anode, asocket = alink.to_node, alink.to_socket
            aparams = ('Name', 'Actuated Component Unique Name', 'Actuated Component Type', 'Actuated Component Control Type')
            aparamvs = ('{}_{}'.format(asocket.name, anode.actdict[anode.acttype][1]), asocket.sn, anode.compdict[anode.acttype], anode.actdict[anode.acttype][0])
            aentries += epentry('EnergyManagementSystem:Actuator', aparams, aparamvs)

        cmparams = ('Name', 'EnergyPlus Model Calling Point', 'Program Name 1')
        cmparamvs = (self.name.replace(' ', '_').replace('.', '_'), 'BeginTimestepBeforePredictor', '{}_controller'.format(self.name.replace(' ', '_').replace('.', '_')))
        cmentry = epentry('EnergyManagementSystem:ProgramCallingManager', cmparams, cmparamvs)
        pparams = ['Name'] + ['line{}'.format(l) for l, line in enumerate(bpy.data.texts[self.text_file].lines) if line.body and line.body.strip()[0] != '!']
        pparamvs = ['{}_controller'.format(self.name.replace(' ', '_').replace('.', '_'))] + [line.body.strip() for line in bpy.data.texts[self.text_file].lines if line.body and line.body.strip()[0] != '!']
        pentry = epentry('EnergyManagementSystem:Program', pparams, pparamvs)
        return sentries + aentries + cmentry + pentry

class EnViEMSZoneNode(bpy.types.Node, EnViNodes):
    '''Node describing a simulation zone'''
    bl_idname = 'EnViEMSZone'
    bl_label = 'EMS Zone'
    bl_icon = 'SOUND'

    def supdate(self, context):
        self.inputs[0].name = '{}_{}'.format(self.emszone, self.sensordict[self.sensortype][0])

    def zupdate(self, context):
        adict = {'Window': 'win', 'Door': 'door'}
        self.supdate(context)
        try:
            obj = bpy.data.objects[self.emszone]
            odm = obj.data.materials
            sssocklist = ['{}_{}_{}'.format(adict[odm[face.material_index].envi_con_type], self.emszone, face.index) for face in obj.data.polygons if odm[face.material_index].envi_afsurface == 1 and odm[face.material_index].envi_con_type in ('Window', 'Door')]
            self.inputs[0].hide = False
            nodecolour(self, 0)
        except:
            sssocklist = []
            self.inputs[0].hide = True
            nodecolour(self, 1)

        for iname in [inputs for inputs in self.inputs if inputs.name not in sssocklist and inputs.bl_idname == 'EnViActSocket']:
            try: self.inputs.remove(iname)
            except: pass

        for sock in sorted(set(sssocklist)):
            if not self.inputs.get(sock):
                try: self.inputs.new('EnViActSocket', sock).sn = '{0[0]}-{0[1]}_{0[2]}_{0[3]}'.format(sock.split('_'))
                except Exception as e: print(e)

    emszone = bpy.props.StringProperty(name = '', update = zupdate)
    sensorlist = [("0", "Zone Temperature", "Sense the zone temperature"), ("1", "Zone Humidity", "Sense the zone humidity"), ("2", "Zone CO2", "Sense the zone CO2"),
                  ("3", "Zone Occupancy", "Sense the zone occupancy"), ("4", "Zone Equipment", "Sense the equipment level")]
    sensortype = bpy.props.EnumProperty(name="", description="Linkage type", items=sensorlist, default='0', update = supdate)
    sensordict = {'0':  ('Temp', 'Zone Mean Air Temperature'), '1': ('RH', 'Zone Air Relative Humidity'), '2': ('CO2', 'AFN Node CO2 Concentration')}
    actlist = [("0", "Opening factor", "Actuate the opening factor"), ("1", "Air supply temp", "Actuate an ideal air load system supply temperature"),
               ("2", "Air supply flow", "Actuate an ideal air load system flow rate"), ("3", "Outdoor Air supply flow", "Actuate an ideal air load system outdoor air flow rate")]
    acttype = bpy.props.EnumProperty(name="", description="Actuator type", items=actlist, default='0')
    compdict = {'0': 'AirFlow Network Window/Door Opening'}
    actdict =  {'0': ('Venting Opening Factor', 'of')}

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('EnViSenseSocket', 'Sensor')
        self.inputs[0].hide = True
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, 'Zone:', self, "emszone")
        if self.emszone in [o.name for o in bpy.data.objects]:
            newrow(layout, 'Sensor', self, 'sensortype')
        if len(self.inputs) > 1:
            newrow(layout, 'Actuator', self, 'acttype')

class EnViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'EnViN'

envinode_categories = [
        EnViNodeCategory("Control", "Control Node", items=[NodeItem("AFNCon", label="Control Node"), NodeItem("EnViWPCA", label="WPCA Node"), NodeItem("EnViCrRef", label="Crack Reference")]),
        EnViNodeCategory("Nodes", "Zone Nodes", items=[NodeItem("EnViZone", label="Zone Node"), NodeItem("EnViExt", label="External Node"), NodeItem("EnViOcc", label="Ocupancy Node")
        , NodeItem("EnViEq", label="Equipment Node"), NodeItem("EnViHvac", label="HVAC Node"), NodeItem("EnViInf", label="Infiltration Node"), NodeItem("EnViTC", label="Thermal Chimney Node")]),
        EnViNodeCategory("LinkNodes", "Airflow Link Nodes", items=[
            NodeItem("EnViSSFlow", label="Sub-surface Flow Node"), NodeItem("EnViSFlow", label="Surface Flow Node")]),
        EnViNodeCategory("SchedNodes", "Schedule Nodes", items=[NodeItem("EnViSched", label="Schedule")]),
        EnViNodeCategory("EMSNodes", "EMS Nodes", items=[NodeItem("EnViProg", label="Program"), NodeItem("EnViEMSZone", label="Zone")])]

class ViASCImport(bpy.types.Node, ViNodes):
    '''Node describing a LiVi geometry export node'''
    bl_idname = 'ViASCImport'
    bl_label = 'Vi ASC Import'
    bl_icon = 'LAMP'

    splitmesh = bpy.props.BoolProperty()
    single = bpy.props.BoolProperty(default = False)
    ascfile = bpy.props.StringProperty()

    def init(self, context):
        self['nodeid'] = nodeid(self)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'single')
        if not self.single:
            row = layout.row()
            row.prop(self, 'splitmesh')
        row = layout.row()
        row.operator('node.ascimport', text = 'Import ASC').nodeid = self['nodeid']
