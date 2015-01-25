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


import bpy, glob, os, inspect, sys, datetime
from subprocess import Popen
from nodeitems_utils import NodeCategory, NodeItem
from .vi_func import objvol, socklink, newrow, epwlatilongi, nodeid, nodeinputs, remlink, rettimes, epentry, sockhide, nodecolour, epschedwrite, retelaarea


class ViNetwork(bpy.types.NodeTree):
    '''A node tree for VI-Suite analysis.'''
    bl_idname = 'ViN'
    bl_label = 'Vi Network'
    bl_icon = 'LAMP_SUN'

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
        (context.scene['latitude'], context.scene['longitude']) = epwlatilongi(context.scene, self) if self.loc == '1' and self.weather else (self.lat, self.long)
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
            self.outputs['Location out']['valid'] = ['Location', 'EnVi Results']
        else:
            self.outputs['Location out']['valid'] = ['Location']
        socklink(self.outputs['Location out'], self['nodeid'].split('@')[1])

    epwpath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))+'/EPFiles/Weather/'
    weatherlist = [((wfile, os.path.basename(wfile).strip('.epw').split(".")[0], 'Weather Location')) for wfile in glob.glob(epwpath+"/*.epw")]
    weather = bpy.props.EnumProperty(items = weatherlist, name="", description="Weather for this project", update = updatelatlong)
    loc = bpy.props.EnumProperty(items = [("0", "Manual", "Manual location"), ("1", "EPW ", "Get location from EPW file")], name = "", description = "Location", default = "0", update = updatelatlong)
    lat = bpy.props.FloatProperty(name="Latitude", description="Site Latitude", min=-90, max=90, default=52, update = updatelatlong)
    long = bpy.props.FloatProperty(name="Longitude", description="Site Longitude (East is positive, West is negative)", min=-180, max=180, default=0, update = updatelatlong)
    maxws = bpy.props.FloatProperty(name="", description="Max wind speed", min=0, max=90, default=0)
    minws = bpy.props.FloatProperty(name="", description="Min wind speed", min=0, max=90, default=0)
    avws = bpy.props.FloatProperty(name="", description="Average wind speed", min=0, max=90, default=0)
    dsdoy = bpy.props.IntProperty(name="", description="", min=1, max=365, default=1)
    dedoy = bpy.props.IntProperty(name="", description="", min=1, max=365, default=365)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        bpy.data.node_groups[nodeid(self).split('@')[1]].use_fake_user = True
        self.outputs.new('ViLoc', 'Location out')
        bpy.context.scene['latitude'], bpy.context.scene['longitude'] = self.lat, self.long

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
            row.prop(self, "lat")
            row = layout.row()
            row.prop(self, "long")

class ViGExLiNode(bpy.types.Node, ViNodes):
    '''Node describing a LiVi geometry export node'''
    bl_idname = 'ViGExLiNode'
    bl_label = 'LiVi Geometry'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.animmenu, self.cpoint, self.offset)])
        if self.inputs['Generative in'].links:
            self.inputs['Generative in'].links[0].from_node.update()

    animtype = [('Static', "Static", "Simple static analysis"), ('Geometry', "Geometry", "Animated geometry analysis"), ('Material', "Material", "Animated material analysis"), ('Lights', "Lights", "Animated artificial lighting analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeupdate)
    cpoint = bpy.props.EnumProperty(items=[("0", "Faces", "Export faces for calculation points"),("1", "Vertices", "Export vertices for calculation points"), ],
            name="", description="Specify the calculation point geometry", default="1", update = nodeupdate)
    offset = bpy.props.FloatProperty(name="", description="Calc point offset", min=0.001, max=1, default=0.01, update = nodeupdate)

    def init(self, context):
        self['exportstate'] = ''
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViLiG', 'Geometry out')
        self.inputs.new('ViGen', 'Generative in')
        bpy.context.scene.gfe = 0
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        newrow(layout, 'Animation:', self, 'animmenu')
        newrow(layout, 'Result point:', self, 'cpoint')
        newrow(layout, 'Offset:', self, 'offset')
        if (self.inputs['Generative in'].links and not self.inputs['Generative in'].links[0].from_node.use_custom_color) or not self.inputs['Generative in'].links:
            row = layout.row()
            row.operator("node.ligexport", text = "Export").nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Geometry out'], self['nodeid'].split('@')[1])

    def export(self, scene):
        nodecolour(self, 0)
        self['exportstate'] = [str(x) for x in (self.animmenu, self.cpoint, self.offset)]
        self['frames'] = {'Material': 0, 'Geometry': 0, 'Lights':0}
        for mglfr in self['frames']:
            self['frames'][mglfr] = scene.frame_end if self.animmenu == mglfr else 0
            scene.gfe = max(self['frames'].values())
        scene['liparams']['cp'], scene.vi_display_rp_off = self.cpoint, self.offset

class ViLiNode(bpy.types.Node, ViNodes):
    '''Node describing a basic LiVi analysis'''
    bl_idname = 'ViLiNode'
    bl_label = 'LiVi Basic'
    bl_icon = 'LAMP'

    analysistype = [('0', "Illuminance", "Lux Calculation"), ('1', "Irradiance", "W/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Factor", "DF (%) Calculation"), ('3', "Glare", "Glare Calculation")]
    unit = bpy.props.StringProperty()
    animtype = [('Static', "Static", "Simple static analysis"), ('Time', "Time", "Animated time analysis")]
    skylist = [("0", "Sunny", "CIE Sunny Sky description"), ("1", "Partly Coudy", "CIE Sunny Sky description"),
               ("2", "Coudy", "CIE Partly Cloudy Sky description"), ("3", "DF Sky", "Daylight Factor Sky description"),
               ("4", "HDR Sky", "HDR file sky"), ("5", "Radiance Sky", "Radiance file sky"), ("6", "None", "No Sky")]

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.analysismenu, self.animmenu, self.skymenu, self.shour, self.sdoy, self.ehour, self.edoy, self.interval, self.hdr, self.hdrname, self.skyname, self.resname)])
        if self.edoy < self.sdoy:
            self.edoy = self.sdoy
        if self.edoy == self.sdoy:
            if self.ehour < self.shour:
                self.ehour = self.shour

    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0', update = nodeupdate)
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeupdate)
    skymenu = bpy.props.EnumProperty(name="", items=skylist, description="Specify the type of sky for the simulation", default="0", update = nodeupdate)
    shour = bpy.props.FloatProperty(name="", description="Hour of simulation", min=1, max=24, default=12, update = nodeupdate)
    sdoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = nodeupdate)
    ehour = bpy.props.FloatProperty(name="", description="Hour of simulation", min=1, max=24, default=12, update = nodeupdate)
    edoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = nodeupdate)
    interval = bpy.props.FloatProperty(name="", description="Site Latitude", min=1/60, max=24, default=1, update = nodeupdate)
    hdr = bpy.props.BoolProperty(name="", description="Export HDR panoramas", default=False, update = nodeupdate)
    hdrname = bpy.props.StringProperty(name="", description="Name of the HDR image file", default="", update = nodeupdate)
    skyname = bpy.props.StringProperty(name="", description="Name of the Radiance sky file", default="", update = nodeupdate)
    resname = bpy.props.StringProperty()
    rp_display = bpy.props.BoolProperty(default = False)
    needloc = bpy.props.BoolProperty(default = True)
    ready = bpy.props.BoolProperty(default = False)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViLoc', 'Location in')
        self.inputs.new('ViTar', 'Target in')
        self.outputs.new('ViLiC', 'Context out')
        self.starttime = datetime.datetime(datetime.datetime.now().year, 1, 1, 12, 0)
        self.endtime = datetime.datetime(datetime.datetime.now().year, 1, 1, 12, 0)
        self['hours'], self['frames'], self['resname'], self['unit'] = 0, {'Time':0}, 'illumout', "Lux"
        self['exportstate'] = ''
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis type:")
        row.prop(self, 'analysismenu')
        row = layout.row()
        if self.analysismenu in ('0', '1', '3'):
            row.label("Sky type:")
            row.prop(self, 'skymenu')
            if self.skymenu in ('0', '1', '2'):
                newrow(layout, "Animation", self, 'animmenu')
                newrow(layout, "Start hour:", self, 'shour')
                newrow(layout, "Start day:", self, 'sdoy')
                if self.animmenu == 'Time':
                    newrow(layout, "End hour:", self, 'ehour')
                    newrow(layout, "End day of year:", self, 'edoy')
                    if self.edoy < self.sdoy:
                        self.edoy = self.sdoy
                    if self.edoy == self.sdoy and self.ehour < self.shour:
                        self.ehour = self.shour
                    newrow(layout, "Interval (hours):", self, 'interval')
            elif self.skymenu == '4':
                row = layout.row()
                row.label("HDR file:")
                row.operator('node.hdrselect', text = 'HDR select')
                row = layout.row()
                row.prop(self, 'hdrname')
            elif self.skymenu == '5':
                row = layout.row()
                row.label("Radiance file:")
                row.operator('node.skyselect', text = 'Sky select')
                row = layout.row()
                row.prop(self, 'skyname')
        row = layout.row()

        if self.skymenu not in ('4', '6'):
            newrow(layout, 'HDR:', self, 'hdr')

        if self.locnodes():
            row = layout.row()
            if context.scene.gfe == 0 or self['frames']['Time'] == 0:
                row.operator("node.liexport", text = "Export").nodeid = self['nodeid']
            else:
                row.label('Cannot have geometry and time animation')

    def update(self):
        for sock in self.outputs:
            socklink(sock, self['nodeid'].split('@')[1])

    def geonodes(self):
        gn = self.outputs['Context out'].links[0].to_node.geonodes() if self.outputs['Context out'].links else 0
        return gn

    def locnodes(self):
        ln = self.inputs['Location in'].links[0].from_node if self.inputs['Location in'].links and not self.inputs['Location in'].links[0].from_node.use_custom_color else 0
        return ln

    def export(self, context):
        self['skynum'] = int(self.skymenu) if self.analysismenu != "2" else 3
        self.starttime = datetime.datetime(datetime.datetime.now().year, 1, 1, int(self.shour), int((self.shour - int(self.shour))*60)) + datetime.timedelta(self.sdoy - 1) if self['skynum'] < 3 else datetime.datetime(2013, 1, 1, 12)
        self.endtime = datetime.datetime(datetime.datetime.now().year, 1, 1, int(self.ehour), int((self.ehour - int(self.ehour))*60)) + datetime.timedelta(self.edoy - 1) if self.animmenu == 'Time' else self.starttime
        self['hours'] = 0 if self.animmenu == 'Static' or int(self.skymenu) > 2  else (self.endtime-self.starttime).days*24 + (self.endtime-self.starttime).seconds/3600
        self['frames']['Time'] = context.scene.cfe = context.scene.fs + int(self['hours']/self.interval)
        self['resname'] = ("illumout", "irradout", "dfout", '')[int(self.analysismenu)]
        quotes = ('"') if sys.platform == 'win32' else ("'")
        self['simalg'] = (" |  rcalc  -e {0}$1=47.4*$1+120*$2+11.6*$3{0} ".format(quotes), " |  rcalc  -e {0}$1=$1{0} ".format(quotes), " |  rcalc  -e {0}$1=(47.4*$1+120*$2+11.6*$3)/100{0} ".format(quotes), '')[int(self.analysismenu)]
        if int(self.skymenu) < 4:
            self['skytypeparams'] = ("+s", "+i", "-c", "-b 22.86 -c")[int(self['skynum'])]
        self['exportstate'] = [str(x) for x in (self.analysismenu, self.animmenu, self.skymenu, self.shour, self.sdoy, self.ehour, self.edoy, self.interval, self.hdr, self.hdrname, self.skyname, self.resname)]
        self.exported = 1
        self.inputs['Location in'].links[0].from_node.exported = 1
        nodecolour(self, 0)

class ViLiCBNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite climate based lighting node'''
    bl_idname = 'ViLiCBNode'
    bl_label = 'LiVi CBDM'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        if self.endmonth < self.startmonth:
            self.endmonth = self.startmonth
        self.sm = (self.sourcemenu, self.sourcemenu2)[int(self.analysismenu) < 2]
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.analysismenu, self.animmenu, self.weekdays, self.cbdm_start_hour, self.cbdm_end_hour, self.dalux, self.damin, self.dasupp,
        self.daauto, self.fromnode, self.sourcemenu, self.sourcemenu2, self.mtxname, self.hdrname, self.hdr, self.startmonth, self.endmonth)])

    analysistype = [('0', "Light Exposure", "LuxHours Calculation"), ('1', "Radiation Exposure", "kWh/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Autonomy", "DA (%) Calculation"), ('3', "Hourly irradiance", "Irradiance for each simulation time step"), ('4', "UDI", "Useful Daylight Illuminance")]
    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0', update = nodeupdate)
    animtype = [('0', "Static", "Simple static analysis"), ('1', "Geometry", "Animated time analysis"), ('2', "Material", "Animated time analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = '0')
    sourcetype = [('0', "EPW", "EnergyPlus weather file"), ('1', "VEC", "Generated vector file")]
    sourcetype2 = [('0', "EPW", "EnergyPlus weather file"), ('2', "HDR", "HDR sky file")]
    sourcemenu = bpy.props.EnumProperty(name="", description="Source type", items=sourcetype, default = '0', update = nodeupdate)
    sourcemenu2 = bpy.props.EnumProperty(name="", description="Source type", items=sourcetype2, default = '0', update = nodeupdate)
    hdrname = bpy.props.StringProperty(
            name="", description="Name of the composite HDR sky file", default="", update = nodeupdate)
    mtxname = bpy.props.StringProperty(
            name="", description="Name of the calculated vector sky file", default="", update = nodeupdate)
    weekdays = bpy.props.BoolProperty(name = '', default = False, update = nodeupdate)
    cbdm_start_hour =  bpy.props.IntProperty(name = '', default = 8, min = 1, max = 24, update = nodeupdate)
    cbdm_end_hour =  bpy.props.IntProperty(name = '', default = 20, min = 1, max = 24, update = nodeupdate)
    dalux =  bpy.props.IntProperty(name = '', default = 300, min = 1, max = 2000, update = nodeupdate)
    damin = bpy.props.IntProperty(name = '', default = 100, min = 1, max = 2000, update = nodeupdate)
    dasupp = bpy.props.IntProperty(name = '', default = 300, min = 1, max = 2000, update = nodeupdate)
    daauto = bpy.props.IntProperty(name = '', default = 3000, min = 1, max = 5000, update = nodeupdate)
    startmonth = bpy.props.IntProperty(name = '', default = 1, min = 1, max = 12, description = 'Start Month', update = nodeupdate)
    endmonth = bpy.props.IntProperty(name = '', default = 12, min = 1, max = 12, description = 'End Month', update = nodeupdate)
    sm = bpy.props.StringProperty(name = '', default = '0')
    exported = bpy.props.BoolProperty(name = '', default = False)
    hdr = bpy.props.BoolProperty(name = '', default = False)
    fromnode = bpy.props.BoolProperty(name = '', default = False)
    num = (("-ab", 2, 3, 5), ("-ad", 512, 2048, 4096), ("-ar", 128, 512, 1024), ("-as", 256, 1024, 2048), ("-aa", 0.0, 0.0, 0.0), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 2, 3), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.001, 0.0002))
    linked = bpy.props.BoolProperty(default=False)

    def init(self, context):
        self.inputs.new('ViLoc', 'Location in')
        self.outputs.new('ViLiC', 'Context out')
        self['nodeid'] = nodeid(self)
        self['frames'] = {'Time':0}
        self['whitesky'] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"
        self['exportstate'] = ''
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis Type:")
        row.prop(self, 'analysismenu')
        newrow(layout, 'Start month:', self, "startmonth")
        newrow(layout, 'End month:', self, "endmonth")
        if self.analysismenu in ('2', '4'):
           newrow(layout, 'Weekdays only:', self, 'weekdays')
           newrow(layout, 'Start hour:', self, 'cbdm_start_hour')
           newrow(layout, 'End hour:', self, 'cbdm_end_hour')
           if self.analysismenu =='2':
               newrow(layout, 'Min Lux level:', self, 'dalux')
           if self.analysismenu =='4':
               newrow(layout, 'Fell short (Max):', self, 'damin')
               newrow(layout, 'Supplementry (Max):', self, 'dasupp')
               newrow(layout, 'Autonomous (Max):', self, 'daauto')

        if self.get('vecvals'):
            newrow(layout, 'From node:', self, 'fromnode')

        if not self.fromnode:
            row = layout.row()
            row.label('Source file:')
            row.prop(self, ('sourcemenu', 'sourcemenu2')[int(self.analysismenu) < 2])
            row = layout.row()
            if self.sm == '1':
                row.operator('node.mtxselect', text = 'Select MTX').nodeid = self['nodeid']
                row = layout.row()
                row.prop(self, 'mtxname')
            elif self.sm == '2':
                row.operator('node.hdrselect', text = 'Select HDR').nodeid = self['nodeid']
                row = layout.row()
                row.prop(self, 'hdrname')
                if self.analysismenu not in ('0', '1'):
                    row = layout.row()
                    row.operator('node.vecselect', text = 'Select MTX').nodeid = self['nodeid']
                    row = layout.row()
                    row.prop(self, 'vecname')

        if int(self.analysismenu) > 1:
            row = layout.row()
            row.label('Export HDR:')
            row.prop(self, 'hdr')

        if self.geonodes() and (self.locnodes() or self.sm != '0'):
            row = layout.row()
            row.operator("node.liexport", text = "Export").nodeid = self['nodeid']

    def update(self):
        if self.outputs.get('Context out') and self.get('nodeid'):
            socklink(self.outputs['Context out'], self['nodeid'].split('@')[1])

    def locnodes(self):
        ln = self.inputs['Location in'].links[0].from_node if self.inputs['Location in'].links and not self.inputs['Location in'].links[0].from_node.use_custom_color else 0
        return ln

    def geonodes(self):
        gn = self.outputs['Context out'].links[0].to_node.geonodes() if self.outputs['Context out'].links else 0
        return gn

    def export(self, context):
        self['skynum'] = 4
        context.scene.cfe = 0
        quotes = ('"') if sys.platform == 'win32' else ("'")
        self['simalg'] = (" |  rcalc  -e {0}$1=(47.4*$1+120*$2+11.6*$3)/1000{0} ".format(quotes), " |  rcalc  -e {0}$1=($1+$2+$3)/3000{0} ".format(quotes),
        " |  rcalc  -e {0}$1=(47.4*$1+120*$2+11.6*$3){0} ".format(quotes), " |  rcalc  -e {0}$1=($1+$2+$3)/3{0} ".format(quotes), " |  rcalc  -e {0}$1=(47.4*$1+120*$2+11.6*$3){0} ".format(quotes))[int(self.analysismenu)]
        self['wd'] = (7, 5)[self.weekdays]
        self['resname'] = ('kluxhours', 'cumwatth', 'dayauto', 'hourrad', 'udi')[int(self.analysismenu)]
        self['exportstate'] = [str(x) for x in (self.analysismenu, self.animmenu, self.weekdays, self.cbdm_start_hour, self.cbdm_end_hour, self.dalux, self.damin, self.dasupp,
        self.daauto, self.fromnode, self.sourcemenu, self.sourcemenu2, self.mtxname, self.hdrname, self.hdr, self.startmonth, self.endmonth)]
        nodecolour(self, 0)

class ViLiCNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite lighting compliance node'''
    bl_idname = 'ViLiCNode'
    bl_label = 'LiVi Compliance'
    bl_icon = 'LAMP'

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.analysismenu, self.bambuildmenu, self.buildstorey, self.animmenu)])

    hdr = bpy.props.BoolProperty(name="HDR", description="Export HDR panoramas", default=False, update = nodeupdate)
    analysistype = [('0', "BREEAM", "BREEAM HEA1 calculation"), ('1', "CfSH", "Code for Sustainable Homes calculation")] #, ('2', "LEED", "LEED EQ8.1 calculation"), ('3', "Green Star", "Green Star Calculation")]
    bambuildtype = [('0', "School", "School lighting standard"), ('1', "Higher Education", "Higher education lighting standard"), ('2', "Healthcare", "Healthcare lighting standard"), ('3', "Residential", "Residential lighting standard"), ('4', "Retail", "Retail lighting standard"), ('5', "Office & other", "Office and other space lighting standard")]
    animtype = [('Static', "Static", "Simple static analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeupdate)
    analysismenu = bpy.props.EnumProperty(name="", description="Type of analysis", items = analysistype, default = '0', update = nodeupdate)
    bambuildmenu = bpy.props.EnumProperty(name="", description="Type of building", items=bambuildtype, default = '0', update = nodeupdate)
    cusacc = bpy.props.StringProperty(name="", description="Custom Radiance simulation parameters", default="", update = nodeupdate)
    buildstorey = bpy.props.EnumProperty(items=[("0", "Single", "Single storey building"),("1", "Multi", "Multi-storey building")], name="", description="Building storeys", default="0", update = nodeupdate)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViLiC', 'Context out')
        nodecolour(self, 1)
        self['frames'], self['unit'], self['skynum'], self['exportstate'], self['export'] = {'Time':0}, "DF %", 3, '', 0

    def draw_buttons(self, context, layout):
        newrow(layout, "Standard:", self, 'analysismenu')
        if self.analysismenu == '0':
            newrow(layout, "Building type:", self, 'bambuildmenu')
            newrow(layout, "Storeys:", self, 'buildstorey')
        newrow(layout, 'Animation:', self, "animmenu")
        row = layout.row()
        row.operator("node.liexport", text = "Export").nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Context out'], self['nodeid'].split('@')[1])

    def export(self, context):
        quotes = ('"') if sys.platform == 'win32' else ("'")
        if self.analysismenu in ('0', '1'):
            self['simalg'] = " |  rcalc  -e {0}$1=(47.4*$1+120*$2+11.6*$3)/100{0} ".format(quotes)# if str(sys.platform) != 'win32' else ' |  rcalc  -e "$1=(47.4*$1+120*$2+11.6*$3)/100" '
        self['resname'] = 'breaamout' if self.analysismenu == '0' else 'cfsh'
        self['skytypeparams'] = "-b 22.86 -c"
        self['exportstate'] = [str(x) for x in (self.analysismenu, self.bambuildmenu, self.buildstorey, self.animmenu)]
        nodecolour(self, 0)
        context.scene.cfe = 0
        context.scene['liparams']['compnode'] = self['nodeid']

class ViLiSNode(bpy.types.Node, ViNodes):
    '''Node describing a LiVi simulation'''
    bl_idname = 'ViLiSNode'
    bl_label = 'LiVi Simulation'
    bl_icon = 'LAMP'

    def nodeupdate(self):
        nodecolour(self, self['exportstate'] != [str(x) for x in (self.cusacc, self.simacc, self.csimacc)])

    simacc = bpy.props.EnumProperty(items=[("0", "Low", "Low accuracy and high speed (preview)"),("1", "Medium", "Medium speed and accuracy"), ("2", "High", "High but slow accuracy"),("3", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0")
    csimacc = bpy.props.EnumProperty(items=[("0", "Custom", "Edit Radiance parameters"), ("1", "Initial", "Initial accuracy for this metric"), ("2", "Final", "Final accuracy for this metric")],
            name="", description="Simulation accuracy", default="1")
    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="")
    rtracebasic = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-as", 128, 512, 2048), ("-aa", 0, 0, 0), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.0001, 0.00001, 0.000002), ("-lr", 2, 3, 4))
    rtraceadvance = (("-ab", 3, 5), ("-ad", 2048, 4096), ("-as", 1024, 2048), ("-aa", 0.0, 0.0), ("-dj", 0.7, 1), ("-ds", 0.5, 0.15), ("-dr", 2, 3), ("-ss", 2, 5), ("-st", 0.75, 0.1), ("-lw", 0.00001, 0.000002), ("-lr", 3, 5))
    rvubasic = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-as", 128, 512, 2048), ("-aa", 0, 0, 0), ("-dj", 0, 0.7, 1), ("-ds", 0.5, 0.15, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.0001, 0.00001, 0.0000002), ("-lr", 3, 3, 4))
    rvuadvance = (("-ab", 3, 5), ("-ad", 2048, 4096), ("-as", 1024, 2048), ("-aa", 0.0, 0.0), ("-dj", 0.7, 1), ("-ds", 0.5, 0.15), ("-dr", 2, 3), ("-ss", 2, 5), ("-st", 0.75, 0.1), ("-lw", 0.00001, 0.000002), ("-lr", 3, 5))

    run = bpy.props.IntProperty(default = 0)
    edit_file = bpy.props.BoolProperty(name = '', default = False)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViLiG', 'Geometry in')
        self.inputs.new('ViLiC', 'Context in')
        self.outputs.new('LiViWOut', 'Data out')
        self.outputs['Data out'].hide = True
        nodecolour(self, 1)
        self['maxres'], self['minres'], self['avres'], self['exportstate'] = {}, {}, {}, ''

    def draw_buttons(self, context, layout):
        geonode = self.geonodes()
        connode = self.connodes()
        if geonode and connode and all([not node.use_custom_color for node in (geonode, connode)]):
            newrow(layout, 'Edit file:', self, 'edit_file')
            row = layout.row()
            row.label("Accuracy:")
            simdict = {'LiVi Basic': 'simacc', 'LiVi Compliance':'csimacc', 'LiVi CBDM':'csimacc'}
            row.prop(self, simdict[connode.bl_label])
            if (self.simacc == '3' and connode.bl_label == 'LiVi Basic') or (self.csimacc == '0' and connode.bl_label in ('LiVi Compliance', 'LiVi CBDM')):
               newrow(layout, "Radiance parameters:", self, 'cusacc')
            if self.run and (connode.bl_label == 'LiVi Basic' and connode.analysismenu == '3'):
                row = layout.row()
                row.label('Calculating'+(self.run%10 *'-'))
            else:
                row = layout.row()
                row.operator("node.radpreview", text = 'Preview').nodeid = self['nodeid']
                if connode.bl_label == 'LiVi Basic' and connode.analysismenu == '3':
                    row.operator("node.liviglare", text = 'Calculate').nodeid = self['nodeid']
                else:
                    row.operator("node.livicalc", text = 'Calculate').nodeid = self['nodeid']

    def update(self):
        if self.outputs.get('Data out'):
            socklink(self.outputs['Data out'], self['nodeid'].split('@')[1])
        self.run = 0

    def geonodes(self):
        gn = self.inputs['Geometry in'].links[0].from_node if self.inputs['Geometry in'].links and not self.inputs['Geometry in'].links[0].from_node.use_custom_color else 0
        return gn

    def connodes(self):
        cn = self.inputs['Context in'].links[0].from_node if self.inputs['Context in'].links and not self.inputs['Context in'].links[0].from_node.use_custom_color else 0
        return cn

    def export(self, op):
        connode = self.connodes()
        geonode = self.geonodes()
        unitdict = {'LiVi Basic': ("Lux", "W/m"+ u'\u00b2', "DF %", '')[int(connode.analysismenu)], 'LiVi Compliance': 'DF (%)', 'LiVi CBDM': ('kLuxHours', 'kWh', 'DA (%)', '', 'UDI-a (%)')[int(connode.analysismenu)]}
        if op == 'LiVi simulation':
            if connode.bl_label == 'LiVi Basic':
                self['radparams'] = self.cusacc if self.simacc == '3' else (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in self.rtracebasic], [n[int(self.simacc)+1] for n in self.rtracebasic]))
            else:
                self['radparams'] = self.cusacc if self.csimacc == '0' else (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in self.rtraceadvance], [n[int(self.csimacc)] for n in self.rtraceadvance]))
        else:
            if connode.bl_label == 'LiVi Basic':
                self['radparams'] = self.cusacc if self.simacc == '3' else (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]}  {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]}".format([n[0] for n in self.rvubasic], [n[int(self.simacc)+1] for n in self.rvubasic]))
            else:
                self['radparams'] = self.cusacc if self.csimacc == '0' else (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]}".format([n[0] for n in self.rvuadvance], [n[int(self.csimacc)] for n in self.rvuadvance]))

        self['exportstate'] = [str(x) for x in (self.cusacc, self.simacc, self.csimacc)]
        bpy.context.scene['liparams']['unit'], bpy.context.scene['liparams']['type'] =  unitdict[connode.bl_label], connode.bl_label
        nodecolour(self, 0)
        return connode, geonode

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

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.inputs.new('ViLoc', 'Location in')
        self['exportstate'] = ''
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
            row.operator("node.shad", text = 'Calculate').nodeid = self['nodeid']

    def export(self, scene):
        nodecolour(self, 0)
        self['exportstate'] = [str(x) for x in (self.animmenu, self.startmonth, self.endmonth, self.starthour, self.endhour, self.interval, self.cpoint, self.offset)]
        self['minres'], self['maxres'], self['avres'] = {}, {}, {}

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
        nodecolour(self, self['exportstate'] != [self.animmenu])
        self.outputs['Geometry out'].hide = True

    animtype = [('Static', "Static", "Simple static analysis"), ('Geometry', "Geometry", "Animated geometry analysis"), ('Material', "Material", "Animated material analysis"), ('Lights', "Lights", "Animated artificial lighting analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeupdate)
    epfiles = []

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self.outputs.new('ViEnG', 'Geometry out')
        self.outputs['Geometry out'].hide = True
        self['exportstate'] = ''
        nodecolour(self, 1)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('Animation:')
        row.prop(self, 'animmenu')
        row = layout.row()
        row.operator("node.engexport", text = "Export").nodeid = self['nodeid']

    def update(self):
        socklink(self.outputs['Geometry out'], self['nodeid'].split('@')[1])

    def export(self):
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
    restype= bpy.props.EnumProperty(items = [("0", "Ambient", "Ambient Conditions"), ("1", "Zone Thermal", "Thermal Results"), ("2", "Comfort", "Comfort Results"), ("3", "Zone Ventilation", "Zone Ventilation Results"), ("4", "Ventilation Link", "ZoneVentilation Results")],
                                   name="", description="Specify the EnVi results category", default="0", update = nodeupdate)
    def resnameunits():
        rnu = {'0': ("Temperature", "Ambient Temperature (K)"),'1': ("Wind Speed", "Ambient Wind Speed (m/s)"), '2': ("Wind Direction", "Ambient Wind Direction (degrees from North)"),
                    '3': ("Humidity", "Ambient Humidity"),'4': ("Direct Solar", u'Direct Solar Radiation (W/m\u00b2K)'), '5': ("Diffuse Solar", u'Diffuse Solar Radiation (W/m\u00b2K)'),
                    '6': ("Temperature", "Zone Temperatures"), '7': ("Heating Watts", "Zone Heating Requirement (Watts)"), '8': ("Cooling Watts", "Zone Cooling Requirement (Watts)"),
                    '9': ("Solar Gain", "Window Solar Gain (Watts)"), '10': ("PPD", "Percentage Proportion Dissatisfied"), '11': ("PMV", "Predicted Mean Vote"),
                    '12': ("Ventilation (l/s)", "Zone Ventilation rate (l/s)"), '13': (u'Ventilation (m\u00b3/h)', u'Zone Ventilation rate (m\u00b3/h)'),
                    '14': (u'Infiltration (m\u00b3)',  u'Zone Infiltration (m\u00b3)'), '15': ('Infiltration (ACH)', 'Zone Infiltration rate (ACH)'), '16': (u'CO\u2082 (ppm)', u'Zone CO\u2082 concentration (ppm)'),
                    '17': ("Heat loss (W)", "Ventilation Heat Loss (W)"), '18': (u'Flow (m\u00b3/s)', u'Linkage flow (m\u00b3/s)'), '19': ('Opening factor', 'Linkage Opening Factor'),
                    '20': ("MRT (K)", "Mean Radiant Temperature (K)"), '21': ('Occupancy', 'Occupancy count'), '22': ("Humidity", "Zone Humidity"),
                    '23': ("Fabric HB (W)", "Fabric convective heat balance"), '24': ("Air Heating", "Zone air heating"), '25': ("Air Cooling", "Zone air cooling")}
        return [bpy.props.BoolProperty(name = rnu[str(rnum)][0], description = rnu[str(rnum)][1], default = False) for rnum in range(len(rnu))]

    (resat, resaws, resawd, resah, resasb, resasd, restt, restwh, restwc, reswsg, rescpp, rescpm, resvls, resvmh, resim, resiach, resco2, resihl, resl12ms,
     reslof, resmrt, resocc, resh, resfhb, ressah, ressac) = resnameunits()

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
        resdict = {'0': (0, "resat", "resaws", 0, "resawd", "resah", 0, "resasb", "resasd"), '1': (0, "restt", "resh", 0, "restwh", "restwc", 0, "ressah", "ressac", 0,"reswsg", "resfhb"),\
        '2': (0, "rescpp", "rescpm", 0, 'resmrt', 'resocc'), '3': (0, "resim", "resiach", 0, "resco2", "resihl"), '4': (0, "resl12ms", "reslof")}
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
        self.outputs.new('ViEnR', 'Results out')
        self['exportstate'] = ''
        nodecolour(self, 1)

    def nodeupdate(self, context):
        nodecolour(self, self['exportstate'] != [self.resname])
        self.outputs['Results out'].hide = True
        if self.inputs['Context in'].is_linked:
            self.resfilename = os.path.join(self.inputs['Context in'].links[0].from_node.newdir, self.resname+'.eso')

    resname = bpy.props.StringProperty(name="", description="Base name for the results files", default="results", update = nodeupdate)
    resfilename = bpy.props.StringProperty(name = "", default = 'results')
    dsdoy, dedoy, run  = bpy.props.IntProperty(), bpy.props.IntProperty(), bpy.props.IntProperty(min = -1, default = -1)

    def draw_buttons(self, context, layout):
        if self.run > -1:
            row = layout.row()
            row.label('Calculating {}%'.format(self.run))
        elif self.inputs['Context in'].links and not self.inputs['Context in'].links[0].from_node.use_custom_color:
            newrow(layout, 'Results name:', self, 'resname')
            row = layout.row()
            row.operator("node.ensim", text = 'Calculate').nodeid = self['nodeid']

    def update(self):
        if self.outputs.get('Results out'):
            socklink(self.outputs['Results out'], self['nodeid'].split('@')[1])

    def sim(self):
        self.dsdoy = self.inputs['Context in'].links[0].from_node.sdoy # (locnode.startmonthnode.sdoy
        self.dedoy = self.inputs['Context in'].links[0].from_node.edoy

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
        self.outputs.new('ViEnR', 'Results out')
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
        Popen('{} {} {}'.format(context.scene['viparams']['cp'], self.idffilename, context.scene['viparams']['idf_file']), shell = True)
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
        self['Start'] = 1
        self['End'] = 365
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
            class ViEnRXIn(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRXIn'
                bl_label = 'X-axis'

                valid = ['EnVi Results']

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)

                def draw(self, context, layout, node, text):
                    layout.label('X-axis')
        else:
            innode = self.inputs['X-axis'].links[0].from_node
            self["_RNA_UI"] = {"Start": {"min":innode.dsdoy, "max":innode.dedoy}, "End": {"min":innode.dsdoy, "max":innode.dedoy}}
            self['Start'], self['End'] = innode.dsdoy, innode.dedoy
            xrtype = [(restype, restype, "Plot "+restype) for restype in innode['rtypes']]
            xctype = [(clim, clim, "Plot "+clim) for clim in innode['ctypes']]
            xztype = [(zone, zone, "Plot "+zone) for zone in innode['ztypes']]
            xzrtype = [(zoner, zoner, "Plot "+zoner) for zoner in innode['zrtypes']]
            xltype = [(link, link, "Plot "+link) for link in innode['ltypes']]
            xlrtype= [(linkr, linkr, "Plot "+linkr) for linkr in innode['lrtypes']]
            xentype = [(en, en, "Plot "+en) for en in innode['entypes']]
            xenrtype= [(enr, enr, "Plot "+enr) for enr in innode['enrtypes']]
            if self.inputs.get('Y-axis 1'):
                self.inputs['Y-axis 1'].hide = False

            class ViEnRXIn(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRXIn'
                bl_label = 'X-axis'

                valid = ['EnVi Results']

                if len(innode['rtypes']) > 0:
                    rtypemenu = bpy.props.EnumProperty(items=xrtype, name="", description="Data type", default = xrtype[0][0])
                    if 'Climate' in innode['rtypes']:
                        climmenu = bpy.props.EnumProperty(items=xctype, name="", description="Climate type", default = xctype[0][0])
                    if 'Zone' in innode['rtypes']:
                        zonemenu = bpy.props.EnumProperty(items=xztype, name="", description="Zone", default = xztype[0][0])
                        zonermenu = bpy.props.EnumProperty(items=xzrtype, name="", description="Zone result", default = xzrtype[0][0])
                    if 'Linkage' in innode['rtypes']:
                        linkmenu = bpy.props.EnumProperty(items=xltype, name="", description="Flow linkage result", default = xltype[0][0])
                        linkrmenu = bpy.props.EnumProperty(items=xlrtype, name="", description="Flow linkage result", default = xlrtype[0][0])
                    if 'External node' in innode['rtypes']:
                        enmenu = bpy.props.EnumProperty(items=xentype, name="", description="External node result", default = xentype[0][0])
                        enrmenu = bpy.props.EnumProperty(items=xenrtype, name="", description="External node result", default = xenrtype[0][0])
                    statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Result statistic", default = 'Average')

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

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)

        bpy.utils.register_class(ViEnRXIn)

        if self.inputs.get('Y-axis 1'):
            if not self.inputs['Y-axis 1'].links:
                class ViEnRY1In(bpy.types.NodeSocket):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY1In'
                    bl_label = 'Y-axis 1'

                    valid = ['EnVi Results']

                    def draw_color(self, context, node):
                        return (0.0, 1.0, 0.0, 0.75)
                    def draw(self, context, layout, node, text):
                        layout.label('Y-axis 1')

                if self.inputs.get('Y-axis 2'):
                    self.inputs['Y-axis 2'].hide = True

            else:
                innode = self.inputs['Y-axis 1'].links[0].from_node
                y1rtype = [(restype, restype, "Plot "+restype) for restype in innode['rtypes']]
                y1ctype = [(clim, clim, "Plot "+clim) for clim in innode['ctypes']]
                y1ztype = [(zone, zone, "Plot "+zone) for zone in innode['ztypes']]
                y1zrtype = [(zoner, zoner, "Plot "+zoner) for zoner in innode['zrtypes']]
                y1ltype = [(link, link, "Plot "+link) for link in innode['ltypes']]
                y1lrtype = [(linkr, linkr, "Plot "+linkr) for linkr in innode['lrtypes']]
                y1entype = [(en, en, "Plot "+en) for en in innode['entypes']]
                y1enrtype = [(enr, enr, "Plot "+enr) for enr in innode['enrtypes']]

                class ViEnRY1In(bpy.types.NodeSocket):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY1In'
                    bl_label = 'Y-axis 1'

                    valid = ['EnVi Results']

                    if innode['rtypes']:
                        rtypemenu = bpy.props.EnumProperty(items=y1rtype, name="", description="Data type", default = y1rtype[0][0])
                        if 'Climate' in innode['rtypes']:
                            climmenu = bpy.props.EnumProperty(items=y1ctype, name="", description="Climate type", default = y1ctype[0][0])
                        if 'Zone' in innode['rtypes']:
                            zonemenu = bpy.props.EnumProperty(items=y1ztype, name="", description="Zone", default = y1ztype[0][0])
                            zonermenu = bpy.props.EnumProperty(items=y1zrtype, name="", description="Zone result", default = y1zrtype[0][0])
                        if 'Linkage' in innode['rtypes']:
                            linkmenu = bpy.props.EnumProperty(items=y1ltype, name="", description="Flow linkage result", default = y1ltype[0][0])
                            linkrmenu = bpy.props.EnumProperty(items=y1lrtype, name="", description="Flow linkage result", default = y1lrtype[0][0])
                        if 'External node' in innode['rtypes']:
                            enmenu = bpy.props.EnumProperty(items=y1entype, name="", description="External node result", default = y1entype[0][0])
                            enrmenu = bpy.props.EnumProperty(items=y1enrtype, name="", description="External node result", default = y1enrtype[0][0])
                        statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Result statistic", default = 'Average')

                    def draw(self, context, layout, node, text):
                        row = layout.row()
                        row.prop(self, "rtypemenu", text = text)
                        if self.links:
                            typedict = {"Time": [], "Climate": ['climmenu'], "Zone": ("zonemenu", "zonermenu"), "Linkage":("linkmenu", "linkrmenu"), "External node":("enmenu", "enrmenu")}
                            for rtype in typedict[self.rtypemenu]:
                                row.prop(self, rtype)
                            if self.node.timemenu in ('1', '2') and self.rtypemenu != 'Time':
                                row.prop(self, "statmenu")

                    def draw_color(self, context, node):
                        return (0.0, 1.0, 0.0, 0.75)

                    def color(self):
                        return (0.0, 1.0, 0.0, 0.75)

                self.inputs['Y-axis 2'].hide = False
            bpy.utils.register_class(ViEnRY1In)

        if self.inputs.get('Y-axis 2'):
            if not self.inputs['Y-axis 2'].links:
                class ViEnRY2In(bpy.types.NodeSocket):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY2In'
                    bl_label = 'Y-axis 2'

                    valid = ['EnVi Results']

                    def draw_color(self, context, node):
                        return (0.0, 1.0, 0.0, 0.75)
                    def draw(self, context, layout, node, text):
                        layout.label('Y-axis 2')

                if self.inputs.get('Y-axis 3'):
                    self.inputs['Y-axis 3'].hide = True
            else:
                innode = self.inputs[2].links[0].from_node
                y2rtype = [(restype, restype, "Plot "+restype) for restype in innode['rtypes']]
                y2ctype = [(clim, clim, "Plot "+clim) for clim in innode['ctypes']]
                y2ztype = [(zone, zone, "Plot "+zone) for zone in innode['ztypes']]
                y2zrtype = [(zoner, zoner, "Plot "+zoner) for zoner in innode['zrtypes']]
                y2ltype = [(link, link, "Plot "+link) for link in innode['ltypes']]
                y2lrtype = [(linkr, linkr, "Plot "+linkr) for linkr in innode['lrtypes']]

                class ViEnRY2In(bpy.types.NodeSocket):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY2In'
                    bl_label = 'Y-axis 2'

                    valid = ['EnVi Results']

                    rtypemenu = bpy.props.EnumProperty(items=y2rtype, name="", description="Result type", default = y2rtype[0][0])
                    if 'Climate' in innode['rtypes']:
                        climmenu = bpy.props.EnumProperty(items=y2ctype, name="", description="Climate type", default = y2ctype[0][0])
                    if 'Zone' in innode['rtypes']:
                        zonemenu = bpy.props.EnumProperty(items=y2ztype, name="", description="Zone", default = y2ztype[0][0])
                        zonermenu = bpy.props.EnumProperty(items=y2zrtype, name="", description="Zone result", default = y2zrtype[0][0])
                    if 'Linkage' in innode['rtypes']:
                        linkmenu = bpy.props.EnumProperty(items=y2ltype, name="", description="Flow linkage result", default = y2ltype[0][0])
                        linkrmenu = bpy.props.EnumProperty(items=y2lrtype, name="", description="Flow linkage result", default = y2lrtype[0][0])
                    statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Zone result", default = 'Average')

                    def draw(self, context, layout, node, text):
                        row = layout.row()
                        row.prop(self, "rtypemenu", text = text)
                        if self.links:
                            typedict = {"Time": [], "Climate": ['climmenu'], "Zone": ("zonemenu", "zonermenu"), "Linkage":("linkmenu", "linkrmenu")}
                            for rtype in typedict[self.rtypemenu]:
                                row.prop(self, rtype)
                            if self.node.timemenu in ('1', '2') and self.rtypemenu != 'Time':
                                row.prop(self, "statmenu")

                    def draw_color(self, context, node):
                        return (0.0, 1.0, 0.0, 0.75)

                    self.inputs['Y-axis 3'].hide = False
            bpy.utils.register_class(ViEnRY2In)

        if self.inputs.get('Y-axis 3'):
            if not self.inputs['Y-axis 3'].links:
                class ViEnRY3In(bpy.types.NodeSocket):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY3In'
                    bl_label = 'Y-axis 3'

                    valid = ['EnVi Results']

                    def draw_color(self, context, node):
                        return (0.0, 1.0, 0.0, 0.75)
                    def draw(self, context, layout, node, text):
                        layout.label('Y-axis 3')
            else:
                innode = self.inputs[3].links[0].from_node
                y3rtype = [(restype, restype, "Plot "+restype) for restype in innode['rtypes']]
                y3ctype = [(clim, clim, "Plot "+clim) for clim in innode['ctypes']]
                y3ztype = [(zone, zone, "Plot "+zone) for zone in innode['ztypes']]
                y3zrtype = [(zoner, zoner, "Plot "+zoner) for zoner in innode['zrtypes']]
                y3ltype = [(link, link, "Plot "+link) for link in innode['ltypes']]
                y3lrtype = [(linkr, linkr, "Plot "+linkr) for linkr in innode['lrtypes']]

                class ViEnRY3In(bpy.types.NodeSocket):
                    '''Energy geometry out socket'''
                    bl_idname = 'ViEnRY3In'
                    bl_label = 'Y-axis 3'

                    valid = ['EnVi Results']

                    rtypemenu = bpy.props.EnumProperty(items=y3rtype, name="", description="Simulation accuracy", default = y3rtype[0][0])
                    if 'Climate' in innode['rtypes']:
                        climmenu = bpy.props.EnumProperty(items=y3ctype, name="", description="Climate type", default = y3ctype[0][0])
                    if 'Zone' in innode['rtypes']:
                        zonemenu = bpy.props.EnumProperty(items=y3ztype, name="", description="Zone", default = y3ztype[0][0])
                        zonermenu = bpy.props.EnumProperty(items=y3zrtype, name="", description="Zone result", default = y3zrtype[0][0])
                    if 'Linkage' in innode['rtypes']:
                        linkmenu = bpy.props.EnumProperty(items=y3ltype, name="", description="Flow linkage result", default = y3ltype[0][0])
                        linkrmenu = bpy.props.EnumProperty(items=y3lrtype, name="", description="Flow linkage result", default = y3lrtype[0][0])
                    statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Zone result", default = 'Average')

                    def draw(self, context, layout, node, text):
                        row = layout.row()
                        row.prop(self, "rtypemenu", text = text)
                        if self.links:
                            typedict = {"Time": [], "Climate": ['climmenu'], "Zone": ("zonemenu", "zonermenu"), "Linkage":("linkmenu", "linkrmenu")}
                            for rtype in typedict[self.rtypemenu]:
                                row.prop(self, rtype)
                            if self.node.timemenu in ('1', '2') and self.rtypemenu != 'Time':
                                row.prop(self, "statmenu")

                    def draw_color(self, context, node):
                        return (0.0, 1.0, 0.0, 0.75)

                    def color(self):
                        return (0.0, 1.0, 0.0, 0.75)

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

class ViLiGSock(bpy.types.NodeSocket):
    '''Lighting geometry socket'''
    bl_idname = 'ViLiG'
    bl_label = 'Geometry'

    valid = ['LiVi Geometry']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.3, 0.17, 0.07, 0.75)

class ViLiCSock(bpy.types.NodeSocket):
    '''Lighting context in socket'''
    bl_idname = 'ViLiC'
    bl_label = 'Context'

    valid = ['LiVi Context']
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

class ViEnR(bpy.types.NodeSocket):
    '''Energy results socket'''
    bl_idname = 'ViEnR'
    bl_label = 'EnVi results'

    valid = ['EnVi Results']
    link_limit = 1

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

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
        self.inputs.new('ViEnR', 'Results in')

    def draw_buttons(self, context, layout):
        if self.inputs['Results in'].links:
            row = layout.row()
            row.operator('node.csvexport', text = 'Export CSV file').nodeid = self['nodeid']

    def update(self):
        pass


####################### Vi Nodes Catagories ##############################

viexnodecat = [NodeItem("ViLoc", label="VI Location"), NodeItem("ViGExLiNode", label="LiVi Geometry"), NodeItem("ViLiNode", label="LiVi Basic"), NodeItem("ViLiCNode", label="LiVi Compliance"), NodeItem("ViLiCBNode", label="LiVi CBDM"), NodeItem("ViGExEnNode", label="EnVi Geometry"), NodeItem("ViExEnNode", label="EnVi Export")]

vinodecat = [NodeItem("ViLiSNode", label="LiVi Simulation"),\
             NodeItem("ViSPNode", label="VI-Suite sun path"), NodeItem("ViSSNode", label="VI-Suite shadow study"), NodeItem("ViWRNode", label="VI-Suite wind rose"), NodeItem("ViEnSimNode", label="EnVi Simulation")]

vigennodecat = [NodeItem("ViGenNode", label="VI-Suite Generative"), NodeItem("ViTarNode", label="VI-Suite Target")]

vidisnodecat = [NodeItem("ViChNode", label="VI-Suite Chart"), NodeItem("ViCSV", label="VI-Suite CSV")]
viinnodecat = [NodeItem("ViEnInNode", label="EnergyPlus input file"), NodeItem("ViEnRFNode", label="EnergyPlus result file"), NodeItem("ViASCImport", label="Import ESRI Grid file")]

vinode_categories = [ViNodeCategory("Input", "Input Nodes", items=viinnodecat), ViNodeCategory("Display", "Display Nodes", items=vidisnodecat), ViNodeCategory("Generative", "Generative Nodes", items=vigennodecat), ViNodeCategory("Analysis", "Analysis Nodes", items=vinodecat), ViNodeCategory("Export", "Export Nodes", items=viexnodecat)]


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
    '''Schedule socket'''
    bl_idname = 'EnViSchedSocket'
    bl_label = 'Schedule socket'
    bl_color = (1.0, 1.0, 0.0, 0.75)

    valid = ['Schedule']

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

class EnViZone(bpy.types.Node, EnViNodes):
    '''Node describing a simulation zone'''
    bl_idname = 'EnViZone'
    bl_label = 'Zone'
    bl_icon = 'SOUND'

    def zupdate(self, context):
        obj = bpy.data.objects[self.zone]
        odm = obj.data.materials
        self.zonevolume = objvol('', obj)
        bsocklist = ['{}_{}_b'.format(odm[face.material_index].name, face.index)  for face in obj.data.polygons if odm[face.material_index].envi_boundary == 1 and odm[face.material_index].name not in [outp.name for outp in self.outputs if outp.bl_idname == 'EnViBoundSocket']]
        ssocklist = ['{}_{}_s'.format(odm[face.material_index].name, face.index) for face in obj.data.polygons if odm[face.material_index].envi_afsurface == 1 and odm[face.material_index].envi_con_type not in ('Window', 'Door') and odm[face.material_index].name not in [outp.name for outp in self.outputs if outp.bl_idname == 'EnViSFlowSocket']]
        sssocklist = ['{}_{}_ss'.format(odm[face.material_index].name, face.index) for face in obj.data.polygons if odm[face.material_index].envi_afsurface == 1 and odm[face.material_index].envi_con_type in ('Window', 'Door') and odm[face.material_index].name not in [outp.name for outp in self.outputs if outp.bl_idname == 'EnViSSFlowSocket']]

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
                self.outputs.new('EnViBoundSocket', sock)
            if not self.inputs.get(sock):
                self.inputs.new('EnViBoundSocket', sock)
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
        self.inputs.new('EnViSchedSocket', 'TSPSchedule')
        self.inputs['TSPSchedule'].hide = True
        self.inputs.new('EnViSchedSocket', 'VASchedule')

    def update(self):
        [bi, si, ssi, bo, so , sso] = [1, 1, 1, 1, 1, 1]
        if self.control != 'Temperature' and self.inputs['TSPSchedule'].is_linked:
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
            print(e)

        nodecolour(self, (self.control == 'Temperature' and not self.inputs['TSPSchedule'].is_linked) or not all((bi, si, ssi, bo, so, sso)))

    def draw_buttons(self, context, layout):
        row=layout.row()
        row.prop(self, "zone")
        yesno = (1, 1, self.control == 'Temperature', self.control == 'Temperature', self.control == 'Temperature')
        vals = (("Volume:", "zonevolume"), ("Control type:", "control"), ("Minimum OF:", "mvof"), ("Lower:", "lowerlim"), ("Upper:", "upperlim"))
        [newrow(layout, val[0], self, val[1]) for v, val in enumerate(vals) if yesno[v]]

    def epwrite(self):
        (tempschedname, mvof, lowerlim, upperlim) = (self.inputs['TSPSchedule'].links[0].from_node.name, self.mvof, self.lowerlim, self.upperlim) if self.inputs['TSPSchedule'].is_linked else ('', '', '', '')
        vaschedname = self.inputs['VASchedule'].links[0].from_node.name if self.inputs['VASchedule'].is_linked else ''
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
        self.inputs['VASchedule'].hide = False if self.linkmenu in ('SO', 'DO', 'HO') else True
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
    amfcc = bpy.props.FloatProperty(default = 0.001, min = 0, max = 1, name = "", description = 'Air Mass Flow Coefficient When Opening is Closed (kg/s-m)')
    amfec = bpy.props.FloatProperty(default = 0.65, min = 0.5, max = 1, name = '', description =  'Air Mass Flow Exponent When Opening is Closed (dimensionless)')
    lvo = bpy.props.EnumProperty(items = [('NonPivoted', 'NonPivoted', 'Non pivoting opening'), ('HorizontallyPivoted', 'HPivoted', 'Horizontally pivoting opening')], name = '', default = 'NonPivoted', description = 'Type of Rectanguler Large Vertical Opening (LVO)')
    ecl = bpy.props.FloatProperty(default = 0.0, min = 0, name = '', description = 'Extra Crack Length or Height of Pivoting Axis (m)')
    noof = bpy.props.IntProperty(default = 2, min = 2, max = 4, name = '', description = 'Number of Sets of Opening Factor Data')
    spa = bpy.props.IntProperty(default = 90, min = 0, max = 90, name = '', description = 'Sloping Plane Angle')
    dcof = bpy.props.FloatProperty(default = 1, min = 0, max = 1, name = '', description = 'Discharge Coefficient')
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
    (of1, of2, of3, of4) =  [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    (dcof1, dcof2, dcof3, dcof4) = [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Discharge Coefficient for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    (wfof1, wfof2, wfof3, wfof4) = [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Width Factor for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    (hfof1, hfof2, hfof3, hfof4) = [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Height Factor for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    (sfof1, sfof2, sfof3, sfof4) = [bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Start Height Factor for Opening Factor {} (dimensionless)'.format(i)) for i in range(4)]
    dcof = bpy.props.FloatProperty(default = 0.2, min = 0, max = 1, name = '', description = 'Discharge Coefficient')
    extnode =  bpy.props.BoolProperty(default = 0)

    def init(self, context):
        self['nodeid'] = nodeid(self)
        self['init'] = 1
        self['ela'] = 1.0
        self.inputs.new('EnViSchedSocket', 'VASchedule')
        self.inputs.new('EnViSchedSocket', 'TSPSchedule')
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
            self.legal()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'linkmenu')
        if self.linkmenu in ('SO', 'DO', 'HO'):
            newrow(layout, 'Win/Door OF:', self, 'wdof1')
            newrow(layout, "Control type:", self, 'controls')
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
            cfparamsv = ('{}_{}'.format(self.name, self.linkmenu), self['ela'], self.dcof, self.rpd, self.amfe)

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
                othersock = (sock.links[0].from_socket, sock.links[0].to_socket)[sock.is_output]
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
        self['scheddict'] = {'TSPSchedule': 'Any Number', 'VASchedule': 'Fraction', 'Fan Schedule': 'Fraction'}
        self.tupdate(context)

    def draw_buttons(self, context, layout):
        uvals, u = (1, self.u1, self.u2, self.u3, self.u4), 0
        tvals = (0, self.t1, self.t2, self.t3, self.t4)
        while uvals[u] and tvals[u] < 365:
            [newrow(layout, v[0], self, v[1]) for v in (('End day {}:'.format(u+1), 't'+str(u+1)), ('Fors:', 'f'+str(u+1)), ('Untils:', 'u'+str(u+1)))]
            u += 1

    def update(self):
        schedtype = ''
        socklink(self.outputs['Schedule'], self['nodeid'].split('@')[1])
        for tosock in [link.to_socket for link in self.outputs['Schedule'].links]:
            nodecolour(self, schedtype and schedtype != self['scheddict'][tosock.name])
            schedtype = self['scheddict'][tosock.name]
        bpy.data.node_groups[self['nodeid'].split('@')[1]].interface_update(bpy.context)

    def epwrite(self):
        schedtext = ''
        for tosock in [link.to_socket for link in self.outputs['Schedule'].links]:
            if not schedtext:
                ths = [self.t1, self.t2, self.t3, self.t4]
                fos = [fs for fs in (self.f1, self.f2, self.f3, self.f4) if fs]
                uns = [us for us in (self.u1, self.u2, self.u3, self.u4) if us]
                ts, fs, us = rettimes(ths, fos, uns)
                schedtext = epschedwrite(self.name, self['scheddict'][tosock.name], ts, fs, us)
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

class EnViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'EnViN'

envinode_categories = [
        EnViNodeCategory("Control", "Control Node", items=[NodeItem("AFNCon", label="Control Node"), NodeItem("EnViWPCA", label="WPCA Node"), NodeItem("EnViCrRef", label="Crack Reference")]),
        EnViNodeCategory("Nodes", "Zone Nodes", items=[NodeItem("EnViZone", label="Zone Node"), NodeItem("EnViExt", label="External Node")]),
        EnViNodeCategory("LinkNodes", "Airflow Link Nodes", items=[
            NodeItem("EnViSSFlow", label="Sub-surface Flow Node"), NodeItem("EnViSFlow", label="Surface Flow Node")]),
        EnViNodeCategory("SchedNodes", "Schedule Nodes", items=[
            NodeItem("EnViSched", label="Schedule")])]

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
