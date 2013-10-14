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


import bpy, glob, os, inspect
from nodeitems_utils import NodeCategory, NodeItem
from .vi_func import nodeinit, objvol, triarea, socklink

try:
    import numpy
    np =1
except:
    np = 0

class ViNetwork(bpy.types.NodeTree):
    '''A node tree for VI-Suite analysis.'''
    bl_idname = 'ViN'
    bl_label = 'Vi Network'
    bl_icon = 'LAMP_SUN'

    def __init__(self):
        self.name = 'VI Network'
        print(self.name)

class ViNodes:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ViN'

class ViGExLiNode(bpy.types.Node, ViNodes):
    '''Node describing a LiVi geometry export node'''
    bl_idname = 'ViGExLiNode'
    bl_label = 'LiVi Geometry'
    bl_icon = 'LAMP'

    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    filedir = bpy.props.StringProperty()
    newdir = bpy.props.StringProperty()
    filebase = bpy.props.StringProperty()
    objfilebase = bpy.props.StringProperty()
    nodetree = bpy.props.StringProperty()
    reslen = bpy.props.IntProperty(default = 0)
    exported = bpy.props.BoolProperty()
    nproc = bpy.props.StringProperty()
    rm = bpy.props.StringProperty()
    cp = bpy.props.StringProperty()
    cat = bpy.props.StringProperty()
    fold = bpy.props.StringProperty()

    def nodeexported(self, context):
        self.exported = False
        if self.bl_label[0] != '*':
            self.bl_label = '*'+self.bl_label
        if self.outputs[0].is_linked:
            link = self.outputs[0].links[0]
            bpy.data.node_groups[self['nodeid'].split('@')[1]].links.remove(link)
        self.outputs[0].hide = True

    animtype = [('Static', "Static", "Simple static analysis"), ('Geometry', "Geometry", "Animated geometry analysis"), ('Material', "Material", "Animated material analysis"), ('Lights', "Lights", "Animated artificial lighting analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeexported)
    cpoint = bpy.props.EnumProperty(items=[("0", "Faces", "Export faces for calculation points"),("1", "Vertices", "Export vertices for calculation points"), ],
            name="", description="Specify the calculation point geometry", default="1", update = nodeexported)
    buildstorey = bpy.props.EnumProperty(items=[("0", "Single", "Single storey building"),("1", "Multi", "Multi-storey building")], name="", description="Building storeys", default="0", update = nodeexported)

    radfiles = []

    def init(self, context):
        self.outputs.new('ViLiG', 'Geometry out')
        self.outputs[0].hide = True
        if bpy.data.filepath:
            nodeinit(self)
        for ng in bpy.data.node_groups:
            if self in ng.nodes[:]:
                self['nodeid'] = self.name+'@'+ng.name

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('Storeys:')
        row.prop(self, 'buildstorey')
        row = layout.row()
        row.label('Animation:')
        row.prop(self, 'animmenu')
        row = layout.row()
        row.label('Calculation point:')
        row.prop(self, 'cpoint')
        row = layout.row()
        row.operator("node.ligexport", text = "Export").nodeid = self['nodeid']

    def update(self):
        if self.exported == False:
            if self.outputs[0].is_linked:
                link = self.outputs[0].links[0]
                bpy.data.node_groups[self['nodeid'].split('@')[1]].links.remove(link)
        else:
            socklink(self.outputs[0], self['nodeid'].split('@')[1])
            if self.outputs[0].is_linked and self.outputs[0].links[0].to_node.name == 'LiVi Compliance' and self.cpoint == '1':
                self.cpoint = '0'

class ViLiNode(bpy.types.Node, ViNodes):
    '''Node describing a basic LiVi analysis'''
    bl_idname = 'ViLiNode'
    bl_label = 'LiVi Basic'
    bl_icon = 'LAMP'

    analysistype = [('0', "Illuminance", "Lux Calculation"), ('1', "Irradiance", "W/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Factor", "DF (%) Calculation"),]
    unit = bpy.props.StringProperty()
    animtype = [('Static', "Static", "Simple static analysis"), ('Time', "Time", "Animated time analysis")]
    skylist = [    ("0", "Sunny", "CIE Sunny Sky description"),
                   ("1", "Partly Coudy", "CIE Sunny Sky description"),
                   ("2", "Coudy", "CIE Partly Cloudy Sky description"),
                   ("3", "DF Sky", "Daylight Factor Sky description"),
                   ("4", "HDR Sky", "HDR file sky"),
                   ("5", "Radiance Sky", "Radiance file sky"),
                   ("6", "None", "No Sky")]

    def nodeexported(self, context):
        self.exported = False
        self.outputs['Context out'].hide = True
        self.bl_label = '*LiVi Basic'

    def edupdate(self, context):
        if self.edoy < self.sdoy:
            self.edoy = self.sdoy
        self.bl_label = '*LiVi Basic'
        self.exported = False
        self.outputs['Context out'].hide = True

    def ehupdate(self, context):
        if self.edoy == self.sdoy:
            if self.ehour < self.shour:
                self.ehour = self.shour
        self.bl_label = '*LiVi Basic'
        self.exported = False
        self.outputs['Context out'].hide = True

    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0', update = nodeexported)
    simalg = bpy.props.StringProperty(name="", description="Algorithm to run on the radiance results", default="")
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeexported)
    skymenu = bpy.props.EnumProperty(items=skylist, name="", description="Specify the type of sky for the simulation", default="0", update = nodeexported)
    shour = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=24, default=12, update = ehupdate)
    sdoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = edupdate)
    ehour = bpy.props.IntProperty(name="", description="Hour of simulation", min=1, max=24, default=12, update = ehupdate)
    edoy = bpy.props.IntProperty(name="", description="Day of simulation", min=1, max=365, default=1, update = edupdate)
    daysav = bpy.props.BoolProperty(name="", description="Enable daylight saving clock", default=False, update = nodeexported)
    lati = bpy.props.FloatProperty(name="", description="Site Latitude", min=-90, max=90, default=52, update = nodeexported)
    longi = bpy.props.FloatProperty(name="", description="Site Longitude relative to local meridian", min=-15, max=15, default=0, update = nodeexported)

    stamer = bpy.props.EnumProperty(
            items=[("0", "YST", ""),("1", "PST", ""),("2", "MST", ""),("3", "CST", ""),("4", "EST", ""),("GMT", "GMT", ""),("6", "CET", ""),("7", "EET", ""),
                   ("8", "AST", ""),("9", "GST", ""),("10", "IST", ""),("11", "JST", ""),("12", "NZST", ""), ],
            name="", description="Specify the local meridian", default="GMT")

    summer = bpy.props.EnumProperty(
            items=[("0", "YDT", ""),("1", "PDT", ""),("2", "MDT", ""),("3", "CDT", ""),("4", "EDT", ""),("BST", "BST", ""),("6", "CEST", ""),
                   ("7", "EEST", ""),("8", "ADT", ""),("9", "GDT", ""),("10", "IDT", ""),("11", "JDT", ""),("12", "NZDT", ""),],
            name="", description="Specify the local Summertime meridian", default="BST")

    interval = bpy.props.FloatProperty(name="", description="Site Latitude", min=0.25, max=24, default=1, update = nodeexported)
    exported = bpy.props.BoolProperty(default=False)
    hdr = bpy.props.BoolProperty(name="HDR", description="Export HDR panoramas", default=False, update = nodeexported)
    hdrname = bpy.props.StringProperty(name="", description="Name of the HDR image file", default="", update = nodeexported)
    skyname = bpy.props.StringProperty(name="", description="Name of the Radiance sky file", default="", update = nodeexported)
    skynum = bpy.props.IntProperty()
    timetype = bpy.props.StringProperty()
    TZ = bpy.props.StringProperty()
    resname = bpy.props.StringProperty()
    rp_display = bpy.props.BoolProperty(default = False)

    def init(self, context):
        self.inputs.new('ViLiG', 'Geometry in')
        self.outputs.new('ViLiC', 'Context out')
        self.outputs['Context out'].hide = True
        for ng in bpy.data.node_groups:
            if self in ng.nodes[:]:
                self['nodeid'] = self.name+'@'+ng.name

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis type:")
        row.prop(self, 'analysismenu')
        row = layout.row()
        if self.analysismenu in ('0', '1'):
            row.label("Sky type:")
            row.prop(self, 'skymenu')
            if self.skymenu in ('0', '1', '2'):
                row = layout.row()
                row.label("Animation:")
                row.prop(self, 'animmenu')
                row = layout.row()
                row.label("Daylight saving:")
                row.prop(self, 'daysav')
                row = layout.row()
                row.label("Local meridian:")
                row.prop(self, 'stamer') if self.daysav == False else row.prop(self, 'summer')
                row = layout.row()
                row.label("Latitude:")
                row.prop(self, 'lati')
                row = layout.row()
                row.label("Longitude:")
                row.prop(self, 'longi')
                row = layout.row()
                row.label("Start hour:")
                row.prop(self, 'shour')
                row = layout.row()
                row.label("Start day of year:")
                row.prop(self, 'sdoy')
                if self.animmenu == 'Time':
                    row = layout.row()
                    row.label("End hour:")
                    row.prop(self, 'ehour')
                    row = layout.row()
                    row.label("End day of year:")
                    row.prop(self, 'edoy')
                    if self.edoy < self.sdoy:
                        self.edoy = self.sdoy
                    if self.edoy == self.sdoy and self.ehour < self.shour:
                        self.ehour = self.shour
                    row = layout.row()
                    row.label("Interval (hours):")
                    row.prop(self, 'interval')
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
        if self.skymenu != '6':
            row.prop(self, 'hdr')
        if self.inputs['Geometry in'].is_linked and self.inputs['Geometry in'].links[0].from_node.bl_label == 'LiVi Geometry':
            row = layout.row()
            row.operator("node.liexport", text = "Export").nodeid = self['nodeid']

class ViLiCBNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite climate based lighting node'''
    bl_idname = 'ViLiCBNode'
    bl_label = 'LiVi CBDM'
    bl_icon = 'LAMP'

    def nodeexported(self, context):
        self.exported = False

    analysistype = [('0', "Annual Light Exposure", "LuxHours Calculation"), ('1', "Annual Radiation Exposure", "kWh/m"+ u'\u00b2' + " Calculation"), ('2', "Daylight Autonomy", "DA (%) Calculation"), ('3', "Hourly irradiance", "Irradiance for each simulation time step"), ('4', "UDI", "Useful Daylight Illuminance")]
    analysismenu = bpy.props.EnumProperty(name="", description="Type of lighting analysis", items = analysistype, default = '0', update = nodeexported)
    animtype = [('0', "Static", "Simple static analysis"), ('1', "Geometry", "Animated time analysis"), ('2', "Material", "Animated time analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = '0', update = nodeexported)
    simalg = bpy.props.StringProperty(name="", description="Algorithm to run on the radiance results", default="")
    simacc = bpy.props.EnumProperty(items=[("0", "Low", "Low accuracy and high speed (preview)"),("1", "Medium", "Medium speed and accuracy"), ("2", "High", "High but slow accuracy"),("3", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0", update = nodeexported)
    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="", update = nodeexported)
    epwname = bpy.props.StringProperty(
            name="", description="Name of the EnergyPlus weather file", default="", update = nodeexported)
    weekdays = bpy.props.BoolProperty(default = False)
    cbdm_start_hour =  bpy.props.IntProperty(name = '', default = 8, min = 1, max = 24)
    cbdm_end_hour =  bpy.props.IntProperty(name = '', default = 20, min = 1, max = 24)
    dalux =  bpy.props.IntProperty(name = '', default = 300, min = 1, max = 2000)
    damin = bpy.props.IntProperty(name = '', default = 100, min = 1, max = 2000)
    dasupp = bpy.props.IntProperty(name = '', default = 300, min = 1, max = 2000)
    daauto = bpy.props.IntProperty(name = '', default = 3000, min = 1, max = 5000)
    exported = bpy.props.BoolProperty(name = '', default = False)
    resname = bpy.props.StringProperty()
    unit = bpy.props.StringProperty()
#    fwd = datetime.datetime(int(epwyear), 1, 1).weekday()
#    if np == 0:
#        vecvals = [[x%24, (fwd+x)%7] + [0 for p in range(146)] for x in range(0,8760)]
##        vals = [0 for x in range(146)]
#    else:
#        vecvals = numpy.array([[x%24, (fwd+x)%7] + [0 for p in range(146)] for x in range(0,8760)])
##        vals = numpy.zeros((146))

    def init(self, context):
        self.inputs.new('ViLiG', 'Geometry in')
        self.outputs.new('ViLiC', 'Context out')
        self.outputs['Context out'].hide = True
        for ng in bpy.data.node_groups:
            if self in ng.nodes[:]:
                self['nodeid'] = self.name+'@'+ng.name
        self.outputs.new('ViLiWResOut', 'Data out')
        self.outputs['Data out'].hide = True

    def update(self):
        if self.outputs['Data out'].is_linked:
            self.analysismenu = '3'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Analysis Type:")
        row.prop(self, 'analysismenu')
        if self.analysismenu in ('2', '4'):
           row = layout.row()
           row.label('Weekdays only:')
           row.prop(self, 'weekdays')
           row = layout.row()
           row.label('Start hour::')
           row.prop(self, 'cbdm_start_hour')
           row = layout.row()
           row.label('End hour:')
           row.prop(self, 'cbdm_end_hour')
           if self.analysismenu =='2':
               row = layout.row()
               row.label('Min Lux level::')
               row.prop(self, 'dalux')
           if self.analysismenu =='4':
               row = layout.row()
               row.label('Fell short (Max):')
               row.prop(self, 'damin')
               row = layout.row()
               row.label('Supplementry (Max):')
               row.prop(self, 'dasupp')
               row = layout.row()
               row.label('Autonomous (Max):')
               row.prop(self, 'daauto')

        row = layout.row()
        row.label('EPW file:')
        row.operator('node.epwselect', text = 'Select EPW').nodeid = self['nodeid']
        row = layout.row()
        row.prop(self, "epwname")
        row = layout.row()
        row.label('Animation:')
        row.prop(self, "animmenu")
        if self.inputs['Geometry in'].is_linked and self.inputs['Geometry in'].links[0].from_node.bl_label == 'LiVi Geometry':
            row = layout.row()
            row.operator("node.liexport", text = "Export").nodeid = self['nodeid']

class ViLiCNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite lighting compliance node'''
    bl_idname = 'ViLiCNode'
    bl_label = 'LiVi Compliance'
    bl_icon = 'LAMP'

    def nodeexported(self, context):
        self.exported = False
        self.bl_label = '*LiVi Compliance'
        self.skynum = 3

    interval = 0
    exported = bpy.props.BoolProperty(default=False)
    TZ = bpy.props.StringProperty(default = 'GMT')
    skynum = bpy.props.IntProperty(default = 3)
    simalg = bpy.props.StringProperty(name="", description="Calculation algorithm", default="")
    resname = bpy.props.StringProperty()
    unit = bpy.props.StringProperty()
    hdr = bpy.props.BoolProperty(name="HDR", description="Export HDR panoramas", default=False, update = nodeexported)
    analysistype = [('0', "BREEAM", "BREEAM HEA1 calculation"), ('1', "CfSH", "Code for Sustainable Homes calculation"), ('2', "LEED", "LEED EQ8.1 calculation"), ('3', "Green Star", "Green Star Calculation")]
    bambuildtype = [('0', "School", "School lighting standard"), ('1', "Higher Education", "Higher education lighting standard"), ('2', "Healthcare", "Healthcare lighting standard"), ('3', "Residential", "Residential lighting standard"), ('4', "Retail", "Retail lighting standard"), ('5', "Office & other", "Office and other space lighting standard")]


    animtype = [('Static', "Static", "Simple static analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeexported)
    analysismenu = bpy.props.EnumProperty(name="", description="Type of analysis", items = analysistype, default = '0', update = nodeexported)
    bambuildmenu = bpy.props.EnumProperty(name="", description="Type of building", items=bambuildtype, default = '0', update = nodeexported)
    cusacc = bpy.props.StringProperty(name="", description="Custom Radiance simulation parameters", default="", update = nodeexported)

    def init(self, context):
        self.inputs.new('ViLiG', 'Geometry in')
        self.outputs.new('ViLiC', 'Context out')
        self.outputs['Context out'].hide = True
        for ng in bpy.data.node_groups:
            if self in ng.nodes[:]:
                self['nodeid'] = self.name+'@'+ng.name

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Compliance standard:")
        row.prop(self, 'analysismenu')

        if self.analysismenu == '0':
            row = layout.row()
            row.label("Building type:")
            row.prop(self, 'bambuildmenu')

        row = layout.row()
        row.label('Animation:')
        row.prop(self, "animmenu")
        if self.inputs['Geometry in'].is_linked and self.inputs['Geometry in'].links[0].from_node.bl_label == 'LiVi Geometry':
            row = layout.row()
            row.operator("node.liexport", text = "Export").nodeid = self['nodeid']

class ViLiSNode(bpy.types.Node, ViNodes):
    '''Node describing a LiVi simulation'''
    bl_idname = 'ViLiSNode'
    bl_label = 'LiVi Simulation'
    bl_icon = 'LAMP'

    simacc = bpy.props.EnumProperty(items=[("0", "Low", "Low accuracy and high speed (preview)"),("1", "Medium", "Medium speed and accuracy"), ("2", "High", "High but slow accuracy"),("3", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="0")
    csimacc = bpy.props.EnumProperty(items=[("1", "Standard", "Standard accuracy for this metric"),("0", "Custom", "Edit Radiance parameters"), ],
            name="", description="Simulation accuracy", default="1")
    cusacc = bpy.props.StringProperty(
            name="", description="Custom Radiance simulation parameters", default="")

    def init(self, context):
        self.inputs.new('ViLiC', 'Context in')
        for ng in bpy.data.node_groups:
            if self in ng.nodes[:]:
                self['nodeid'] = self.name+'@'+ng.name

    def draw_buttons(self, context, layout):
        if self.inputs['Context in'].is_linked and self.inputs['Context in'].links[0].from_node.exported and self.inputs['Context in'].links[0].from_node.inputs[0].is_linked and self.inputs['Context in'].links[0].from_node.inputs['Geometry in'].links[0].from_node.exported:
            row = layout.row()
            row.label("Accuracy:")
            if self.inputs['Context in'].links[0].from_node.bl_label == 'LiVi Basic':
                row.prop(self, 'simacc')
            elif self.inputs['Context in'].links[0].from_node.bl_label == 'LiVi Compliance':
                row.prop(self, 'csimacc')
            elif self.inputs['Context in'].links[0].from_node.bl_label == 'LiVi CBDM':
                row.prop(self, 'csimacc')

            if (self.simacc == '3' and self.inputs['Context in'].links[0].from_node.bl_label == 'LiVi Basic') or (self.csimacc == '0' and self.inputs['Context in'].links[0].from_node.bl_label == 'LiVi Compliance'):
               row = layout.row()
               row.label("Radiance parameters:")
               row.prop(self, 'cusacc')

            row = layout.row()
            row.operator("node.radpreview", text = 'Preview').nodeid = self['nodeid']
            row.operator("node.calculate", text = 'Calculate').nodeid = self['nodeid']

class ViSPNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite sun path'''
    bl_idname = 'ViSPNode'
    bl_label = 'VI Sun Path'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate')

class ViSSNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite sun path'''
    bl_idname = 'ViSPNode'
    bl_label = 'VI Sun Path'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate')

class ViWRNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite wind rose generator'''
    bl_idname = 'ViWRNode'
    bl_label = 'VI Wind Rose'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate')

class ViGNode(bpy.types.Node, ViNodes):
    '''Node describing a glare analysis'''
    bl_idname = 'ViGNode'
    bl_label = 'VI Glare'
    bl_icon = 'LAMP'

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.operator("node.calculate", text = 'Calculate')

class ViGExEnNode(bpy.types.Node, ViNodes):
    '''Node describing a VI-Suite export type'''
    bl_idname = 'ViGExEnNode'
    bl_label = 'VI EP geometry conversion'

    exported = bpy.props.BoolProperty()

    def nodeexported(self, context):
        self.exported = False

    animtype = [('Static', "Static", "Simple static analysis"), ('Geometry', "Geometry", "Animated geometry analysis"), ('Material', "Material", "Animated material analysis"), ('Lights', "Lights", "Animated artificial lighting analysis")]
    animmenu = bpy.props.EnumProperty(name="", description="Animation type", items=animtype, default = 'Static', update = nodeexported)
    epfiles = []

    def init(self, context):
        self.outputs.new('ViEnGOut', 'Geometry out')
        self.outputs[0].hide = True

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('Animation:')
        row.prop(self, 'animmenu')
        row = layout.row()
        row.operator("node.engexport", text = "Export").nodename = self.name

    def update(self):
        if self.outputs[0].is_linked:
            if self.outputs[0].links[0].to_socket.color() != self.outputs[0].color():
                link = self.outputs[0].links[0]
                bpy.data.node_groups['VI Network'].links.remove(link)

class ViExEnNode(bpy.types.Node, ViNodes):
    '''Node describing an EnergyPlus export'''
    bl_idname = 'ViExEnNode'
    bl_label = 'VI EnergyPLus analysis'
    bl_icon = 'LAMP'

    nproc = bpy.props.StringProperty()
    rm = bpy.props.StringProperty()
    cat = bpy.props.StringProperty()
    fold = bpy.props.StringProperty()
    cp = bpy.props.StringProperty()
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    filedir = bpy.props.StringProperty()
    newdir = bpy.props.StringProperty()
    filebase = bpy.props.StringProperty()
    idf_file = bpy.props.StringProperty()
    exported = bpy.props.BoolProperty()
    resname = bpy.props.StringProperty(name="Results Name", description="Base name for the results files", default="results")
    dsdoy = bpy.props.IntProperty()
    dedoy = bpy.props.IntProperty()

    def nodeexported(self, context):
        self.exported = False
        self.bl_label = '*VI EnergyPLus analysis'


    loc = bpy.props.StringProperty(name="", description="Identifier for this project", default="", update = nodeexported)
    terrain = bpy.props.EnumProperty(items=[("0", "City", "Towns, city outskirts, centre of large cities"),
                   ("1", "Urban", "Urban, Industrial, Forest"),("2", "Suburbs", "Rough, Wooded Country, Suburbs"),
                    ("3", "Country", "Flat, Open Country"),("4", "Ocean", "Ocean, very flat country")],
                    name="", description="Specify the surrounding terrain", default="0", update = nodeexported)

    addonpath = os.path.dirname(inspect.getfile(inspect.currentframe()))
    matpath = addonpath+'/EPFiles/Materials/Materials.data'
    epwpath = addonpath+'/EPFiles/Weather/'
    weatherlist = [((wfile, os.path.basename(wfile).strip('.epw').split(".")[0], 'Weather Location')) for wfile in glob.glob(epwpath+"/*.epw")]
    weather = bpy.props.EnumProperty(items = weatherlist, name="", description="Weather for this project")
    sdoy = bpy.props.IntProperty(name = "", description = "Day of simulation", min = 1, max = 365, default = 1, update = nodeexported)
    edoy = bpy.props.IntProperty(name = "", description = "Day of simulation", min = 1, max = 365, default = 365, update = nodeexported)
    timesteps = bpy.props.IntProperty(name = "", description = "Time steps per hour", min = 1, max = 4, default = 1, update = nodeexported)
    resfilename = bpy.props.StringProperty(name = "", default = 'results')
    restype= bpy.props.EnumProperty(items = [("0", "Ambient", "Ambient Conditions"), ("1", "Zone Thermal", "Thermal Results"), ("2", "Comfort", "Comfort Results"), ("3", "Zone Ventilation", "Zone Ventilation Results"), ("4", "Ventilation Link", "ZoneVentilation Results")],
                                   name="", description="Specify the EnVi results catagory", default="0", update = nodeexported)

    resat = bpy.props.BoolProperty(name = "Temperature", description = "Ambient Temperature (K)", default = False, update = nodeexported)
    resaws = bpy.props.BoolProperty(name = "Wind Speed", description = "Ambient Wind Speed (m/s)", default = False, update = nodeexported)
    resawd = bpy.props.BoolProperty(name = "Wind Direction", description = "Ambient Wind Direction (degrees from North)", default = False, update = nodeexported)
    resah = bpy.props.BoolProperty(name = "Humidity", description = "Ambient Humidity", default = False, update = nodeexported)
    resasb = bpy.props.BoolProperty(name = "Direct Solar", description = u'Direct Solar Radiation (W/m\u00b2K)', default = False, update = nodeexported)
    resasd = bpy.props.BoolProperty(name = "Diffuse Solar", description = u'Diffuse Solar Radiation (W/m\u00b2K)', default = False, update = nodeexported)
    restt = bpy.props.BoolProperty(name = "Temperature", description = "Zone Temperatures", default = False, update = nodeexported)
    restwh = bpy.props.BoolProperty(name = "Heating Watts", description = "Zone Heating Requirement (Watts)", default = False, update = nodeexported)
    restwc = bpy.props.BoolProperty(name = "Cooling Watts", description = "Zone Cooling Requirement (Watts)", default = False, update = nodeexported)
    reswsg = bpy.props.BoolProperty(name = "Solar Gain", description = "Window Solar Gain (Watts)", default = False, update = nodeexported)
#    resthm = BoolProperty(name = "kWh/m2 Heating", description = "Zone Heating kilo Watt hours of heating per m2 floor area", default = False)
#    restcm = BoolProperty(name = "kWh/m2 Cooling", description = "Zone Cooling kilo Watt hours of cooling per m2 floor area", default = False)
    rescpp = bpy.props.BoolProperty(name = "PPD", description = "Percentage Proportion Dissatisfied", default = False, update = nodeexported)
    rescpm = bpy.props.BoolProperty(name = "PMV", description = "Predicted Mean Vote", default = False, update = nodeexported)
    resvls = bpy.props.BoolProperty(name = "Ventilation (l/s)", description = "Zone Ventilation rate (l/s)", default = False, update = nodeexported)
    resvmh = bpy.props.BoolProperty(name = u'Ventilation (m3/h)', description = u'Zone Ventilation rate (m\u00b3/h)', default = False, update = nodeexported)
#    resims = bpy.props.BoolProperty(name = u'Infiltration (m3/s)', description = u'Zone Infiltration rate (m\u00b3/s)', default = False, update = nodeexported)
    resim = bpy.props.BoolProperty(name = u'Infiltration (m\u00b3)', description = u'Zone Infiltration (m\u00b3)', default = False, update = nodeexported)
    resiach = bpy.props.BoolProperty(name = 'Infiltration (ACH)', description = 'Zone Infiltration rate (ACH)', default = False, update = nodeexported)
    resco2 = bpy.props.BoolProperty(name = u'CO\u2082 concentration (ppm)', description = u'Zone CO\u2082 concentration (ppm)', default = False, update = nodeexported)
    resihl = bpy.props.BoolProperty(name = "Heat loss (W)", description = "Ventilation Heat Loss (W)", default = False, update = nodeexported)
    resl12ms = bpy.props.BoolProperty(name = u'Flow (m\u00b3/s)', description = u'Linkage flow (m\u00b3/s)', default = False, update = nodeexported)
    reslof = bpy.props.BoolProperty(name = 'Opening factor', description = 'Linkage Opening Factor', default = False, update = nodeexported)
#u'\u00b0C)'
    def init(self, context):
        self.inputs.new('ViEnGIn', 'Geometry in')
        nodeinit(self)
        self['xtypes']

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label("Project name/location")
        row.prop(self, "loc")
        row = layout.row()
        row.label("Weather file:")
        row.prop(self, "weather")
        row = layout.row()
        row.label(text = 'Terrain:')
        col = row.column()
        col.prop(self, "terrain")
        row = layout.row()
        row.label(text = 'Start day:')
        col = row.column()
        col.prop(self, "sdoy")
        row = layout.row()
        row.label(text = 'End day:')
        col = row.column()
        col.prop(self, "edoy")
        row = layout.row()
        row.label(text = 'Time-steps/hour)')
        row.prop(self, "timesteps")
        row = layout.row()
        row.label(text = 'Results Catagory:')
        col = row.column()
        col.prop(self, "restype")
        if self.restype == "0":
            row = layout.row()
            row.prop(self, "resat")
            row.prop(self, "resaws")
            row = layout.row()
            row.prop(self, "resawd")
            row.prop(self, "resah")
            row = layout.row()
            row.prop(self, "resasb")
            row.prop(self, "resasd")
        elif self.restype == "1":
            row = layout.row()
            row.prop(self, "restt")
            row.prop(self, "restwh")
            row = layout.row()
            row.prop(self, "restwc")
            row.prop(self, "reswsg")
        elif self.restype == "2":
            row = layout.row()
            row.prop(self, "rescpp")
            row.prop(self, "rescpm")
        elif self.restype == "3":
            row = layout.row()
            row.prop(self, "resim")
            row.prop(self, "resiach")
            row = layout.row()
            row.prop(self, "resco2")
            row.prop(self, "resihl")
        elif self.restype == "4":
            row = layout.row()
            row.prop(self, "resl12ms")
            row.prop(self, "reslof")

        if self.inputs[0].is_linked == True:
            row = layout.row()
            row.operator("node.enexport", text = 'Export').nodename = self.name

        if self.inputs[0].is_linked == True and self.exported == True and self.inputs[0].links[0].from_node.exported == True:
            row = layout.row()
            row.label(text = 'Results name:')
            row.prop(self, 'resname')
            row = layout.row()
            row.operator("node.ensim", text = 'Calculate').nodename = self.name

class ViEnRFNode(bpy.types.Node, ViNodes):
    '''Node for EnergyPlus results file selection'''
    bl_idname = 'ViEnRFNode'
    bl_label = 'VI EnergyPLus results file selection'

    resfilename = bpy.props.StringProperty(name="", description="Name of the EnVi results file", default="")
    dsdoy = bpy.props.IntProperty()
    dedoy = bpy.props.IntProperty()

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('ESO file:')
        row.operator('node.esoselect', text = 'Select ESO file').nodename = self.name
        row = layout.row()
        row.prop(self, 'resfilename')
        row.operator("node.fileprocess", text = 'Process file').nodename = self.name


#class ViEnRNode(bpy.types.Node, ViNodes):
#    '''Node for EnergyPlus 2D results analysis'''
#    bl_idname = 'ViEnRNode'
#    bl_label = 'VI EnergyPLus results'
#
#    ctypes = [("0", "Line", "Line Chart"), ("1", "Bar", "Bar Chart")]
#    dsh = bpy.props.IntProperty(name = "Start", description = "", min = 1, max = 24, default = 1)
#    deh = bpy.props.IntProperty(name = "End", description = "", min = 1, max = 24, default = 24)
#    charttype = bpy.props.EnumProperty(items = ctypes, name = "Chart Type", default = "0")
#    timemenu = bpy.props.EnumProperty(items=[("0", "Hourly", "Hourly results"),("1", "Daily", "Daily results"), ("2", "Monthly", "Monthly results")],
#                                                      name="", description="Results frequency", default="0")
#
#
#    class ViEnRXIn(bpy.types.NodeSocket):
#        '''Energy geometry out socket'''
#        bl_idname = 'ViEnRXIn'
#        bl_label = 'X-axis'
#
#        def draw_color(self, context, node):
#            return (0.0, 1.0, 0.0, 0.75)
#        def draw(self, context, layout, node, text):
#            row = layout.row()
#
#    def init(self, context):
#
#        self.inputs.new("ViEnRXIn", "X-axis")
#        self['Start'] = 1
#        self['End'] = 365


class ViEnRNode(bpy.types.Node, ViNodes):
    '''Node for EnergyPlus 2D results analysis'''
    bl_idname = 'ViEnRNode'
    bl_label = 'VI EnergyPLus results'

    ctypes = [("0", "Line", "Line Chart"), ("1", "Bar", "Bar Chart")]
    dsh = bpy.props.IntProperty(name = "Start", description = "", min = 1, max = 24, default = 1)
    deh = bpy.props.IntProperty(name = "End", description = "", min = 1, max = 24, default = 24)
    charttype = bpy.props.EnumProperty(items = ctypes, name = "Chart Type", default = "0")
    timemenu = bpy.props.EnumProperty(items=[("0", "Hourly", "Hourly results"),("1", "Daily", "Daily results"), ("2", "Monthly", "Monthly results")],
                                                      name="", description="Results frequency", default="0")

    def init(self, context):
        self.inputs.new("ViEnRXIn", "X-axis")
        self['Start'] = 1
        self['End'] = 365
        self.inputs.new("ViEnRY1In", "Y-axis 1")
        self.inputs[1].hide = True
        self.inputs.new("ViEnRY2In", "Y-axis 2")
        self.inputs[2].hide = True
        self.inputs.new("ViEnRY3In", "Y-axis 3")
        self.inputs[3].hide = True

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

        if self.inputs['X-axis'].is_linked and self.inputs['Y-axis 1'].is_linked:
            layout.operator("node.chart", text = 'Create plot').nodename = self.name

    def update(self):
        if self.inputs['X-axis'].is_linked == False:
            class ViEnRXIn(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRXIn'
                bl_label = 'X-axis'

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)
                def draw(self, context, layout, node, text):
                    layout.label('X-axis')

        else:
            xrtype, xctype, xztype, xzrtype, xltype, xlrtype = [], [], [], [], [], []
            try:
                innode = self.inputs['X-axis'].links[0].from_node
            except:
                return
            self["_RNA_UI"] = {"Start": {"min":innode.dsdoy, "max":innode.dedoy}, "End": {"min":innode.dsdoy, "max":innode.dedoy}}
            self['Start'], self['End'] = innode.dsdoy, innode.dedoy
            for restype in innode['rtypes']:
                xrtype.append((restype, restype, "Plot "+restype))
            for clim in innode['ctypes']:
                xctype.append((clim, clim, "Plot "+clim))
            for zone in innode['ztypes']:
                xztype.append((zone, zone, "Plot "+zone))
            for zoner in innode['zrtypes']:
                xzrtype.append((zoner, zoner, "Plot "+zoner))
            for link in innode['ltypes']:
                xltype.append((link, link, "Plot "+link))
            for linkr in innode['lrtypes']:
                xlrtype.append((linkr, linkr, "Plot "+linkr))
            self.inputs['Y-axis 1'].hide = False

            class ViEnRXIn(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRXIn'
                bl_label = 'X-axis'

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
                    statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Result statistic", default = 'Average')


                def draw(self, context, layout, node, text):
                    row = layout.row()
                    row.label('--')
                    row = layout.row()
                    row.prop(self, "rtypemenu", text = text)
                    if self.is_linked == True:
                        row = layout.row()
                        if self.rtypemenu == "Climate":
                            row.prop(self, "climmenu")
                        elif self.rtypemenu == "Zone":
                            row.prop(self, "zonemenu")
                            row = layout.row()
                            row.prop(self, "zonermenu")
                        elif self.rtypemenu == "Linkage":
                            row.prop(self, "linkmenu")
                            row = layout.row()
                            row.prop(self, "linkrmenu")
                        if self.node.timemenu in ('1', '2') and self.rtypemenu !='Time':
                            row.prop(self, "statmenu")
                    row = layout.row()
                    row.label('--')
                    row = layout.row()

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)

                def color(self):
                    return (0.0, 1.0, 0.0, 0.75)

        if self.inputs['Y-axis 1'].is_linked == False:
            class ViEnRY1In(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRY1In'
                bl_label = 'Y-axis 1'

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)
                def draw(self, context, layout, node, text):
                    layout.label('Y-axis 1')
            self.inputs['Y-axis 2'].hide = True

        else:
            y1rtype, y1ctype, y1ztype, y1zrtype, y1ltype, y1lrtype = [], [], [], [], [], []
            innode = self.inputs[1].links[0].from_node
            for restype in innode['rtypes']:
                y1rtype.append((restype, restype, "Plot "+restype))
            for clim in innode['ctypes']:
                y1ctype.append((clim, clim, "Plot "+clim))
            for zone in innode['ztypes']:
                y1ztype.append((zone, zone, "Plot "+zone))
            for zoner in innode['zrtypes']:
                y1zrtype.append((zoner, zoner, "Plot "+zoner))
            for link in innode['ltypes']:
                y1ltype.append((link, link, "Plot "+link))
            for linkr in innode['lrtypes']:
                y1lrtype.append((linkr, linkr, "Plot "+linkr))


            class ViEnRY1In(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRY1In'
                bl_label = 'Y-axis1'
                if len(innode['rtypes']) > 0:
                    rtypemenu = bpy.props.EnumProperty(items=y1rtype, name="", description="Data type", default = y1rtype[0][0])
                    if 'Climate' in innode['rtypes']:
                        climmenu = bpy.props.EnumProperty(items=y1ctype, name="", description="Climate type", default = y1ctype[0][0])
                    if 'Zone' in innode['rtypes']:
                        zonemenu = bpy.props.EnumProperty(items=y1ztype, name="", description="Zone", default = y1ztype[0][0])
                        zonermenu = bpy.props.EnumProperty(items=y1zrtype, name="", description="Zone result", default = y1zrtype[0][0])
                    if 'Linkage' in innode['rtypes']:
                        linkmenu = bpy.props.EnumProperty(items=y1ltype, name="", description="Flow linkage result", default = y1ltype[0][0])
                        linkrmenu = bpy.props.EnumProperty(items=y1lrtype, name="", description="Flow linkage result", default = y1lrtype[0][0])
                    statmenu = bpy.props.EnumProperty(items=[('Average', 'Average', 'Average Value'), ('Maximum', 'Maximum', 'Maximum Value'), ('Minimum', 'Minimum', 'Minimum Value')], name="", description="Result statistic", default = 'Average')


                def draw(self, context, layout, node, text):
                    row = layout.row()
                    row.prop(self, "rtypemenu", text = text)
                    if self.is_linked:
                        row = layout.row()
                        if self.rtypemenu == "Climate":
                            row.prop(self, "climmenu")
                        elif self.rtypemenu == "Zone":
                            row.prop(self, "zonemenu")
                            row = layout.row()
                            row.prop(self, "zonermenu")
                        elif self.rtypemenu == "Linkage":
                            row.prop(self, "linkmenu")
                            row = layout.row()
                            row.prop(self, "linkrmenu")
                        if self.node.timemenu in ('1', '2') and self.rtypemenu != 'Time':
                            row.prop(self, "statmenu")
                    row = layout.row()
                    row.label('--')
                    row = layout.row()

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)

                def color(self):
                    return (0.0, 1.0, 0.0, 0.75)

            self.inputs['Y-axis 2'].hide = False

        if self.inputs['Y-axis 2'].is_linked == False:
            class ViEnRY2In(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRY2In'
                bl_label = 'Y-axis 2'

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)
                def draw(self, context, layout, node, text):
                    layout.label('Y-axis 2')
            self.inputs['Y-axis 3'].hide = True

        else:
            y2rtype, y2ctype, y2ztype, y2zrtype, y2ltype, y2lrtype = [], [], [], [], [], []
            innode = self.inputs[2].links[0].from_node
            for restype in innode['rtypes']:
                y2rtype.append((restype, restype, "Plot "+restype))
            for clim in innode['ctypes']:
                y2ctype.append((clim, clim, "Plot "+clim))
            for zone in innode['ztypes']:
                y2ztype.append((zone, zone, "Plot "+zone))
            for zoner in innode['zrtypes']:
                y2zrtype.append((zoner, zoner, "Plot "+zoner))
            for link in innode['ltypes']:
                y2ltype.append((link, link, "Plot "+link))
            for linkr in innode['lrtypes']:
                y2lrtype.append((linkr, linkr, "Plot "+linkr))

            class ViEnRY2In(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRY2In'
                bl_label = 'Y-axis 2'

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
                    if self.is_linked:
                        row = layout.row()
                        if self.rtypemenu == "Climate":
                            row.prop(self, "climmenu")
                        elif self.rtypemenu == "Zone":
                            row.prop(self, "zonemenu")
                            row = layout.row()
                            row.prop(self, "zonermenu")
                        if self.node.timemenu in ('1', '2') and self.rtypemenu != 'Time':
                            row.prop(self, "statmenu")
                    row = layout.row()
                    row.label('--')
                    row = layout.row()

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)

                def color(self):
                    return (0.0, 1.0, 0.0, 0.75)

                self.inputs['Y-axis 3'].hide = False

        if self.inputs['Y-axis 3'].is_linked == False:
            class ViEnRY3In(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRY3In'
                bl_label = 'Y-axis 3'

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)
                def draw(self, context, layout, node, text):
                    layout.label('Y-axis 3')
        else:
            y3rtype, y3ctype, y3ztype, y3zrtype, y3ltype, y3lrtype = [], [], [], [], [], []
            innode = self.inputs[3].links[0].from_node
            for restype in innode['rtypes']:
                y3rtype.append((restype, restype, "Plot "+restype))
            for clim in innode['ctypes']:
                y3ctype.append((clim, clim, "Plot "+clim))
            for zone in innode['ztypes']:
                y3ztype.append((zone, zone, "Plot "+zone))
            for zoner in innode['zrtypes']:
                y3zrtype.append((zoner, zoner, "Plot "+zoner))
            for link in innode['ltypes']:
                y3ltype.append((link, link, "Plot "+link))
            for linkr in innode['lrtypes']:
                y3lrtype.append((linkr, linkr, "Plot "+linkr))

            class ViEnRY3In(bpy.types.NodeSocket):
                '''Energy geometry out socket'''
                bl_idname = 'ViEnRY3In'
                bl_label = 'Y-axis 3'

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
                    if self.is_linked:
                        row = layout.row()
                        if self.rtypemenu == "Climate":
                            row.prop(self, "climmenu")
                        elif self.rtypemenu == "Zone":
                            row.prop(self, "zonemenu")
                            row = layout.row()
                            row.prop(self, "zonermenu")
                        if self.node.timemenu in ('1', '2') and self.rtypemenu != 'Time':
                            row.prop(self, "statmenu")

                def draw_color(self, context, node):
                    return (0.0, 1.0, 0.0, 0.75)

                def color(self):
                    return (0.0, 1.0, 0.0, 0.75)


        bpy.utils.register_class(ViEnRXIn)
        bpy.utils.register_class(ViEnRY1In)
        bpy.utils.register_class(ViEnRY2In)
        bpy.utils.register_class(ViEnRY3In)

class ViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ViN'

class ViLiWResOut(bpy.types.NodeSocket):
    '''LiVi irradiance out socket'''
    bl_idname = 'LiViWOut'
    bl_label = 'LiVi W/m2 out'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class ViLiGIn(bpy.types.NodeSocket):
    '''Lighting geometry socket'''
    bl_idname = 'ViLiG'
    bl_label = 'Geometry'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.3, 0.17, 0.07, 0.75)

    def color(self):
        return (0.3, 0.17, 0.07, 0.75)

class ViLiC(bpy.types.NodeSocket):
    '''Lighting context in socket'''
    bl_idname = 'ViLiC'
    bl_label = 'Context'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 0.0, 0.75)

    def color(self):
        return (1.0, 1.0, 0.0, 0.75)


class ViEnGOut(bpy.types.NodeSocket):
    '''Energy geometry out socket'''
    bl_idname = 'ViEnGOut'
    bl_label = 'Geometry out'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 0.0, 1.0, 0.75)

    def color(self):
        return (0.0, 0.0, 1.0, 0.75)

class ViEnROut(bpy.types.NodeSocket):
    '''Energy geometry out socket'''
    bl_idname = 'ViEnROut'
    bl_label = 'results out'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

    def color(self):
        return (0.0, 1.0, 0.0, 0.75)

class ViEnGIn(bpy.types.NodeSocket):
    '''Energy geometry out socket'''
    bl_idname = 'ViEnGIn'
    bl_label = 'Geometry in'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 0.0, 1.0, 0.75)

    def color(self):
        return (0.0, 0.0, 1.0, 0.75)

class EnViDataIn(bpy.types.NodeSocket):
    '''EnVi data in socket'''
    bl_idname = 'EnViDIn'
    bl_label = 'EnVi data in socket'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 0.75)

viexnodecat = [NodeItem("ViGExLiNode", label="LiVi Geometry"), NodeItem("ViLiNode", label="LiVi Basic"), NodeItem("ViLiCNode", label="LiVi Compliance"), NodeItem("ViLiCBNode", label="LiVi Climate Based"), NodeItem("ViGExEnNode", label="EnVi Export")]

vinodecat = [NodeItem("ViLiSNode", label="LiVi Simulation"),\
             NodeItem("ViSPNode", label="VI-Suite sun path"), NodeItem("ViSSNode", label="VI-Suite shadow study"), NodeItem("ViWRNode", label="VI-Suite wind rose"), NodeItem("ViGNode", label="VI-Suite glare"), NodeItem("ViExEnNode", label="EnVi Simulation")]

vidisnodecat = [NodeItem("ViEnRNode", label="VI-Suite chart display"), NodeItem("ViEnRFNode", label="EnergyPlus result file")]

vinode_categories = [ViNodeCategory("Display", "Display Nodes", items=vidisnodecat), ViNodeCategory("Analysis", "Analysis Nodes", items=vinodecat), ViNodeCategory("Export", "Export Nodes", items=viexnodecat)]


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
    sn = bpy.props.StringProperty()
    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.5, 0.2, 0.0, 0.75)

class EnViSchedSocket(bpy.types.NodeSocket):
    '''Schedule socket'''
    bl_idname = 'EnViSchedSocket'
    bl_label = 'Schedule socket'

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 1.0, 0.0, 0.75)

class EnViSAirSocket(bpy.types.NodeSocket):
    '''A plain zone surface airflow socket'''
    bl_idname = 'EnViSAirSocket'
    bl_label = 'Plain zone surface airflow socket'
    sn = bpy.props.StringProperty()

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.1, 1.0, 0.2, 0.75)

class EnViCAirSocket(bpy.types.NodeSocket):
    '''A plain zone airflow component socket'''
    bl_idname = 'EnViCAirSocket'
    bl_label = 'Plain zone airflow component socket'
    sn = bpy.props.StringProperty()

    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.2, 0.2, 0.75)

class EnViCrRefSocket(bpy.types.NodeSocket):
    '''A plain zone airflow component socket'''
    bl_idname = 'EnViCrRefSocket'
    bl_label = 'Plain zone airflow component socket'
    sn = bpy.props.StringProperty()
    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.0, 0.75)

class AFNCon(bpy.types.Node, EnViNodes):
    '''Node defining the overall airflow network simulation'''
    bl_idname = 'AFNCon'
    bl_label = 'Control'
    bl_icon = 'SOUND'

    afnname = bpy.props.StringProperty()
    afntype = bpy.props.EnumProperty(items = [('MultizoneWithDistribution', 'MultizoneWithDistribution', 'Include a forced airflow system in the model'),
                                              ('MultizoneWithoutDistribution', 'MultizoneWithoutDistribution', 'Exclude a forced airflow system in the model'),
                                              ('MultizoneWithDistributionOnlyDuringFanOperation', 'MultizoneWithDistributionOnlyDuringFanOperation', 'Apply forced air system only when in operation'),
                                              ('NoMultizoneOrDistribution', 'NoMultizoneOrDistribution', 'Only zone infiltration controls are modelled')], name = "", default = 'MultizoneWithoutDistribution')

    wpctype = bpy.props.EnumProperty(items = [('SurfaceAverageCalculation', 'SurfaceAverageCalculation', 'Calculate wind pressure coefficients based on oblong building assumption'),
                                              ('Input', 'Input', 'Input wind pressure coefficients from an external source')], name = "", default = 'SurfaceAverageCalculation')
    wpcaname = bpy.props.StringProperty()
    wpchs = bpy.props.EnumProperty(items = [('OpeningHeight', 'OpeningHeight', 'Calculate wind pressure coefficients based on opening height'),
                                              ('ExternalNode', 'ExternalNode', 'Calculate wind pressure coefficients based on external node height')], name = "", default = 'OpeningHeight')
    buildtype = bpy.props.EnumProperty(items = [('LowRise', 'Low Rise', 'Height is less than 3x the longest wall'),
                                              ('HighRise', 'High Rise', 'Height is more than 3x the longest wall')], name = "", default = 'LowRise')

    maxiter = bpy.props.IntProperty(default = 500, description = 'Maximum Number of Iterations')

    initmet = bpy.props.EnumProperty(items = [('ZeroNodePressures', 'ZeroNodePressures', 'Initilisation type'),
                                              ('LinearInitializationMethod', 'LinearInitializationMethod', 'Initilisation type')], name = "", default = 'ZeroNodePressures')

    rcontol = bpy.props.FloatProperty(default = 0.0001, description = 'Relative Airflow Convergence Tolerance')

    acontol = bpy.props.FloatProperty(default = 0.000001, description = 'Absolute Airflow Convergence Tolerance')

    conal = bpy.props.FloatProperty(default = -0.1, max = 1, min = -1, description = 'Convergence Acceleration Limit')
    aalax = bpy.props.IntProperty(default = 0, max = 180, min = 0, description = 'Azimuth Angle of Long Axis of Building')
    rsala = bpy.props.FloatProperty(default = 1, max = 1, min = 0, description = 'Ratio of Building Width Along Short Axis to Width Along Long Axis')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'afnname')
        row = layout.row()
        row.prop(self, 'afntype')
        row = layout.row()
        row.prop(self, 'wpctype')
        if self.wpctype == 'Input':
            row = layout.row()
            row.prop(self, 'wpcaname')
            row = layout.row()
            row.prop(self, 'wpchs')
        elif self.wpctype == 'SurfaceAverageCalculation':
            row = layout.row()
            row.prop(self, 'buildtype')
        row = layout.row()
        row.prop(self, 'maxiter')
        row = layout.row()
        row.prop(self, 'initmet')
        row = layout.row()
        row.prop(self, 'rcontol')
        row = layout.row()
        row.prop(self, 'acontol')
        row = layout.row()
        row.prop(self, 'conal')
        if self.wpctype == 'SurfaceAverageCalculation':
            row = layout.row()
            row.prop(self, 'aalax')
            row = layout.row()
            row.prop(self, 'rsala')

class EnViZone(bpy.types.Node, EnViNodes):
    '''Node describing a simulation zone'''
    bl_idname = 'EnViZone'
    bl_label = 'Zone'
    bl_icon = 'SOUND'

    def zupdate(self, context):
        obj = bpy.data.objects[self.zone]
        odm = obj.data.materials
        omw = obj.matrix_world
        self.location = (50 * (omw*obj.location)[0], ((omw*obj.location)[2] + (omw*obj.location)[1])*25)
        self.zonevolume = objvol(obj)
        for oname in [outputs for outputs in self.outputs if outputs.name not in [mat.name for mat in odm if mat.envi_boundary == True] and outputs.bl_idname == 'EnViBoundSocket']:
            self.outputs.remove(oname)
        for oname in [outputs for outputs in self.outputs if outputs.name not in [mat.name for mat in odm if mat.afsurface == True] and outputs.bl_idname == 'EnViCAirSocket']:
            self.outputs.remove(oname)
        for iname in [inputs for inputs in self.inputs if inputs.name not in [mat.name for mat in odm if mat.envi_boundary == True] and inputs.bl_idname == 'EnViBoundSocket']:
            self.inputs.remove(iname)
        for iname in [inputs for inputs in self.inputs if inputs.name not in [mat.name for mat in odm if mat.afsurface == True] and inputs.bl_idname == 'EnViCAirSocket']:
            self.inputs.remove(iname)

        socklist = [odm[face.material_index].name for face in obj.data.polygons if odm[face.material_index].envi_boundary == 1 and odm[face.material_index].name not in [outp.name for outp in self.outputs if outp.bl_idname == 'EnViBoundSocket']]
        for sock in sorted(set(socklist)):
            self.outputs.new('EnViBoundSocket', sock+'_b')
            self.inputs.new('EnViBoundSocket', sock+'_b')
        socklist = [(odm[face.material_index].name, face.index) for face in obj.data.polygons if odm[face.material_index].afsurface == 1 and odm[face.material_index].envi_con_type not in ('Window', 'Door') and odm[face.material_index].name not in [outp.name for outp in self.outputs if outp.bl_idname == 'EnViCAirSocket']]
        for sock in sorted(set(socklist)):
            self.outputs.new('EnViCAirSocket', sock[0]+'_c').sn = str(sock[1])
            self.inputs.new('EnViCAirSocket', sock[0]+'_c').sn = str(sock[1])
        socklist = [(odm[face.material_index].name, face.index) for face in obj.data.polygons if odm[face.material_index].afsurface == 1 and odm[face.material_index].envi_con_type in ('Window', 'Door') and odm[face.material_index].name not in [outp.name for outp in self.outputs if outp.bl_idname == 'EnViSAirSocket']]
        for sock in sorted(set(socklist)):
            self.outputs.new('EnViSAirSocket', sock[0]+'_s').sn = str(sock[1])
            self.inputs.new('EnViSAirSocket', sock[0]+'_s').sn = str(sock[1])

    def supdate(self, context):
        self.outputs['TSPSchedule'].hide = False if self.control == 'Temperature' else True

    zone = bpy.props.StringProperty(update = zupdate)
    controltype = [("NoVent", "None", "No ventilation control"), ("Temperature", "Temperature", "Temperature control")]
    control = bpy.props.EnumProperty(name="", description="Ventilation control type", items=controltype, default='NoVent', update = supdate)
    zonevolume = bpy.props.FloatProperty(name = '')
    mvof = bpy.props.FloatProperty(default = 0, name = "", min = 0, max = 1)
    lowerlim = bpy.props.FloatProperty(default = 0, name = "", min = 0, max = 100)
    upperlim = bpy.props.FloatProperty(default = 50, name = "", min = 0, max = 100)

    def init(self, context):
        self.outputs.new('EnViSchedSocket', 'TSPSchedule')
        self.outputs['TSPSchedule'].hide = True
        self.outputs.new('EnViSchedSocket', 'VASchedule')
#        self.outputs['VASchedule'].hide = True

    def update(self):
        try:
            for inp in [inp for inp in self.inputs if inp.bl_idname in ('EnViBoundSocket', 'EnViCAirSocket')]:
                self.outputs[inp.name].hide = True if inp.is_linked and self.outputs[inp.name].bl_idname == inp.bl_idname else False
            for outp in [outp for outp in self.outputs if outp.bl_idname in ('EnViBoundSocket', 'EnViCAirSocket')]:
                self.inputs[outp.name].hide = True if outp.is_linked and self.inputs[outp.name].bl_idname == outp.bl_idname else False
        except Exception as e:
            print(e)

    def draw_buttons(self, context, layout):
        row=layout.row()
        row.prop(self, "zone")
        row=layout.row()
        row.label("Volume:")
        row.prop(self, "zonevolume")
        row=layout.row()
        row.label("Control type:")
        row.prop(self, "control")
        if self.control == 'Temperature':
            row = layout.row()
            row.label('Minimum OF')
            row.prop(self, 'mvof')
            row = layout.row()
            row.label('Lower')
            row.prop(self, 'lowerlim')
            row = layout.row()
            row.label('Upper')
            row.prop(self, 'upperlim')

class EnViSLinkNode(bpy.types.Node, EnViNodes):
    '''Node describing an surface airflow component'''
    bl_idname = 'EnViSLink'
    bl_label = 'Envi urface airflow Component'
    bl_icon = 'SOUND'

    def supdate(self, context):
        self.outputs['Reference'].hide = False if self.linkmenu in ('Crack', 'EF') else True
        self.outputs['TSPSchedule'].hide = False if self.linkmenu in ('SO', 'DO', 'HO') else True
        if self.linkmenu in ('SO', 'DO', 'HO'):
            for sock in [sock for sock in [outs for outs in self.outputs]+[ins for ins in self.inputs] if sock.bl_idname == 'EnViCAirSocket']:
                if sock.is_linked == True:
                    bpy.data.node_groups['EnVi Network'].links.remove(sock.links[0])
                sock.hide = True
            for sock in [sock for sock in [outs for outs in self.outputs]+[ins for ins in self.inputs] if sock.bl_idname == 'EnViSAirSocket']:
                sock.hide = False
        else:
            for sock in [sock for sock in [outs for outs in self.outputs]+[ins for ins in self.inputs] if sock.bl_idname == 'EnViSAirSocket']:
                if sock.is_linked == True:
                    bpy.data.node_groups['EnVi Network'].links.remove(sock.links[0])
                sock.hide = True
            for sock in [sock for sock in [outs for outs in self.outputs]+[ins for ins in self.inputs] if sock.bl_idname == 'EnViCAirSocket']:
                sock.hide = False

    linktype = [("SO", "Simple Opening", "Simple opening element"),("DO", "Detailed Opening", "Detailed opening element"),
        ("HO", "Horizontal Opening", "Horizontal opening element"),("Crack", "Crack", "Crack aperture used for leakage calculation"),
        ("ELA", "ELA", "Effective leakage area"), ("EF", "Exhaust fan", "Exhaust fan")]

    linkmenu = bpy.props.EnumProperty(name="Type", description="Linkage type", items=linktype, default='SO', update = supdate)

    wdof = bpy.props.FloatProperty(default = 1, min = 0, max = 1, name = "")
    controltype = [("ZoneLevel", "ZoneLevel", "Zone level ventilation control"), ("NoVent", "None", "No ventilation control"),
                   ("Temperature", "Temperature", "Temperature control")]
    controls = bpy.props.EnumProperty(name="", description="Ventilation control type", items=controltype, default='ZoneLevel')
    controlc = bpy.props.EnumProperty(name="", description="Ventilation control type", items=controltype[:-1], default='ZoneLevel')
    mvof = bpy.props.FloatProperty(default = 0, min = 0, max = 1, name = "", description = 'Minimium venting open factor')
    lvof = bpy.props.FloatProperty(default = 0, min = 0, max = 100, name = "", description = 'Indoor and Outdoor Temperature Difference Lower Limit For Maximum Venting Open Factor (deltaC)')
    uvof = bpy.props.FloatProperty(default = 1, min = 1, max = 100, name = "", description = 'Indoor and Outdoor Temperature Difference Upper Limit For Minimum Venting Open Factor (deltaC)')
    amfcc = bpy.props.FloatProperty(default = 0.001, min = 0, max = 1, name = "", description = 'Air Mass Flow Coefficient When Opening is Closed (kg/s-m)')
    amfec = bpy.props.FloatProperty(default = 0.65,min = 0.5, max = 1, name = '', description =  'Air Mass Flow Exponent When Opening is Closed (dimensionless)')
    lvo = bpy.props.EnumProperty(items = [('NonPivoted', 'NonPivoted', 'Non pivoting opening'), ('HorizontallyPivoted', 'HPivoted', 'Horizontally pivoting opening')], default = 'NonPivoted', description = 'Type of Rectanguler Large Vertical Opening (LVO)')
    ecl = bpy.props.FloatProperty(default = 0.0, min = 0, name = '', description = 'Extra Crack Length or Height of Pivoting Axis (m)')
    noof = bpy.props.IntProperty(default = 2, min = 2, max = 4, name = '', description = 'Number of Sets of Opening Factor Data')
    spa = bpy.props.IntProperty(default = 90, min = 0, max = 90, name = '', description = 'Sloping Plane Angle')
    dcof = bpy.props.FloatProperty(default = 0.2, min = 0, max = 1, name = '', description = 'Discharge Coefficient')
    ddtw = bpy.props.FloatProperty(default = 0.1, min = 0, max = 10, name = '', description = 'Mimum Density Difference for Two-way Flow')
    amfc = bpy.props.FloatProperty(default = 1.0, name = "")
    amfe = bpy.props.FloatProperty(default = 0.6, name = "")
    dlen = bpy.props.FloatProperty(default = 2, name = "")
    dhyd = bpy.props.FloatProperty(default = 0.1, name = "")
    dcs = bpy.props.FloatProperty(default = 0.1, name = "")
    dsr = bpy.props.FloatProperty(default = 0.0009, name = "")
    dlc = bpy.props.FloatProperty(default = 1.0, name = "")
    dhtc = bpy.props.FloatProperty(default = 0.772, name = "")
    dmtc = bpy.props.FloatProperty(default = 0.0001, name = "")
    cf = bpy.props.FloatProperty(default = 1, min = 0, max = 1, name = "")
    ela = bpy.props.FloatProperty(default = 0.1, min = 0, max = 1, name = "")
    rpd = bpy.props.FloatProperty(default = 4, min = 0.1, max = 50, name = "")
    dcof1 = bpy.props.FloatProperty(default = 0.001, min = 0, max = 1, name = '', description = 'Discharge Coefficient for Opening Factor 1 (dimensionless)')
    wfof1 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Width Factor for Opening Factor 1 (dimensionless)')
    hfof1 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Height Factor for Opening Factor 1 (dimensionless)')
    sfof1 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Start Height Factor for Opening Factor 1 (dimensionless)')
    of2 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Opening Factor 2 (dimensionless)')
    dcof2 = bpy.props.FloatProperty(default = 0.001, min = 0, max = 1, name = '', description = 'Discharge Coefficient for Opening Factor 2 (dimensionless)')
    wfof2 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Width Factor for Opening Factor 2 (dimensionless)')
    hfof2 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Height Factor for Opening Factor 2 (dimensionless)')
    sfof2 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Start Height Factor for Opening Factor 2 (dimensionless)')
    of3 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Opening Factor 3 (dimensionless)')
    dcof3 = bpy.props.FloatProperty(default = 0.001, min = 0, max = 1, name = '', description = 'Discharge Coefficient for Opening Factor 3 (dimensionless)')
    wfof3 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Width Factor for Opening Factor 3 (dimensionless)')
    hfof3 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Height Factor for Opening Factor 3 (dimensionless)')
    sfof3 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Start Height Factor for Opening Factor 3 (dimensionless)')
    of4 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Opening Factor 4 (dimensionless)')
    dcof4 = bpy.props.FloatProperty(default = 0.001, min = 0, max = 1, name = '', description = 'Discharge Coefficient for Opening Factor 4 (dimensionless)')
    wfof4 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Width Factor for Opening Factor 4 (dimensionless)')
    hfof4 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Height Factor for Opening Factor 4 (dimensionless)')
    sfof4 = bpy.props.FloatProperty(default = 0.0, min = 0, max = 1, name = '', description = 'Start Height Factor for Opening Factor 4 (dimensionless)')
    dcof = bpy.props.FloatProperty(default = 0.2, min = 0, max = 1, name = '', description = 'Discharge Coefficient')

    def init(self, context):
        self.inputs.new('EnViSAirSocket', 'Node 1', identifier = 'Node1_s')
        self.inputs.new('EnViSAirSocket', 'Node 2', identifier = 'Node2_s')
        self.outputs.new('EnViSAirSocket', 'Node 1', identifier = 'Node1_s')
        self.outputs.new('EnViSAirSocket', 'Node 2', identifier = 'Node2_s')
        self.outputs.new('EnViSchedSocket', 'VASchedule')
        self.outputs.new('EnViSchedSocket', 'TSPSchedule')
        self.outputs.new('EnViCrRefSocket', 'Reference')
        self.outputs['Reference'].hide = True
        self.inputs.new('EnViCAirSocket', 'Node 1', identifier = 'Node1_c')
        self.inputs.new('EnViCAirSocket', 'Node 2', identifier = 'Node2_c')
        self.outputs.new('EnViCAirSocket', 'Node 1', identifier = 'Node1_c')
        self.outputs.new('EnViCAirSocket', 'Node 2', identifier = 'Node2_c')
        for sock in [sock for sock in [outs for outs in self.outputs]+[ins for ins in self.inputs] if sock.identifier[-1] == 'c']:
            sock.hide = True

    def update(self):
        for sock in [sock for sock in self.inputs]+[sock for sock in self.outputs]:
            socklink(sock)
        try:


            lsockids = [('Node1_s', 'Node2_s'), ('Node1_c', 'Node2_c')][self.linkmenu not in ('SO', 'DO', 'HO')]
            for ins in [ins for ins in self.inputs if ins.identifier in lsockids]:
                if ins.is_linked == True and ins.bl_idname == ins.links[0].from_socket.bl_idname:
                    for outs in self.outputs:
                        if outs.name == ins.name and outs.identifier == ins.identifier:
                            outs.hide = True
                elif ins.hide == False:
                    for outs in self.outputs:
                        if outs.name == ins.name and outs.identifier == ins.identifier:
                            outs.hide = False

            for outs in [outs for outs in self.outputs if outs.identifier in lsockids]:
                if outs.is_linked == True:
                    for ins in self.inputs:
                        if ins.name == outs.name and ins.identifier == outs.identifier:
                            ins.hide = True
                elif outs.hide == False:
                    for outs in self.outputs:
                        if ins.name == outs.name and ins.identifier == outs.identifier:
                            ins.hide = False
        except:
            pass

        for sock in self.inputs:
            if self.linkmenu == 'ELA' and sock.is_linked:
                try:
                    self.ela = triarea(bpy.data.objects[sock.links[0].from_node.zone], bpy.data.objects[sock.links[0].from_node.zone].data.polygons[int(sock.links[0].from_socket.sn)])
                except:
                    pass

    def draw_buttons(self, context, layout):
        layout.prop(self, 'linkmenu')
        row = layout.row()
        row.label("Opening factor:")
        row.prop(self, 'wdof')
        row = layout.row()
        row.label("Control type:")
        if self.linkmenu in ('SO', 'DO', 'HO'):
            row.prop(self, 'controls')
        else:
            row.prop(self, 'controlc')
        if self.linkmenu == "SO":
            row = layout.row()
            row.label('Closed FC:')
            row.prop(self, 'amfcc')
            row = layout.row()
            row.label('Closed FE:')
            row.prop(self, 'amfec')
            row = layout.row()
            row.label('Density diff:')
            row.prop(self, 'ddtw')
            row = layout.row()
            row.label('DC')
            row.prop(self, 'dcof')
        elif self.linkmenu == "DO":
            row = layout.row()
            row.label("OF Number:")
            row.prop(self, 'noof')
            row = layout.row()
            row.label('DC1')
            row.prop(self, 'dcof1')
            row = layout.row()
            row.prop(self, 'wfof1')
            row = layout.row()
            row.prop(self, 'hfof1')
            row = layout.row()
            row.prop(self, 'sfof1')
            row = layout.row()
            row.prop(self, 'of2')
            row = layout.row()
            row.label('DC2')
            row.prop(self, 'dcof2')
            row = layout.row()
            row.prop(self, 'wfof2')
            row = layout.row()
            row.prop(self, 'hfof2')
            row = layout.row()
            row.prop(self, 'sfof2')
            if self.noof > 2:
                row = layout.row()
                row.prop(self, 'of3')
                row = layout.row()
                row.label('DC3')
                row.prop(self, 'dcof3')
                row = layout.row()
                row.prop(self, 'wfof3')
                row = layout.row()
                row.prop(self, 'hfof3')
                row = layout.row()
                row.prop(self, 'sfof3')
                if self.noof > 3:
                    row = layout.row()
                    row.prop(self, 'of4')
                    row = layout.row()
                    row.label('DC4')
                    row.prop(self, 'dcof4')
                    row = layout.row()
                    row.prop(self, 'wfof4')
                    row = layout.row()
                    row.prop(self, 'hfof4')
                    row = layout.row()
                    row.prop(self, 'sfof4')
        elif self.linkmenu == 'HO':
            row = layout.row()
            row.label('Closed FC')
            row.prop(self, 'amfcc')
            row = layout.row()
            row.label('Closed FE')
            row.prop(self, 'amfec')
            row = layout.row()
            row.label('Slope')
            row.prop(self, 'spa')
            row = layout.row()
            row.label('Discharge Coeff')
            row.prop(self, 'dcof')

        if self.linkmenu in ('SO', 'DO', 'HO') and self.controls == 'Temperature':
            row = layout.row()
            row.label('Minimum OF')
            row.prop(self, 'mvof')
            row = layout.row()
            row.label('Lower OF')
            row.prop(self, 'lvof')
            row = layout.row()
            row.label('Upper OF')
            row.prop(self, 'uvof')

        if self.linkmenu == "Crack":
            row = layout.row()
            row.label("Coefficient:")
            row.prop(self, 'amfc')
            row = layout.row()
            row.label("Exponent:")
            row.prop(self, 'amfe')
            row = layout.row()
            row.label("Crack factor:")
            row.prop(self, 'cf')

#        if self.linkmenu == "Duct":
#            row = layout.row()
#            row.label("Length:")
#            row.prop(self, 'dlen')
#            row = layout.row()
#            row.label("Hydraulic diameter:")
#            row.prop(self, 'dhyd')
#            row = layout.row()
#            row.label("Cross Section:")
#            row.prop(self, 'dcs')
#            row = layout.row()
#            row.label("Surface Roughness:")
#            row.prop(self, 'dsr')
#            row = layout.row()
#            row.label("Loss coefficient:")
#            row.prop(self, 'dlc')
#            row = layout.row()
#            row.label("U-Factor:")
#            row.prop(self, 'dhtc')
#            row = layout.row()
#            row.label("Moisture coefficient:")
#            row.prop(self, 'dmtc')

        if self.linkmenu == "ELA":
            row = layout.row()
            row.label("ELA:")
            row.prop(self, 'ela')
            row = layout.row()
            row.label("Discharge Coeff:")
            row.prop(self, 'dcof')
            row = layout.row()
            row.label("PA diff:")
            row.prop(self, 'rpd')
            row = layout.row()
            row.label("FE:")
            row.prop(self, 'amfe')

        if self.linkmenu == "EF":
            row = layout.row()
            row.label("Off FC:")
            row.prop(self, 'amfc')
            row = layout.row()
            row.label("Off FE:")
            row.prop(self, 'amfe')

class EnViCLinkNode(bpy.types.Node, EnViNodes):
    '''Node describing an airflow component'''
    bl_idname = 'EnViCLink'
    bl_label = 'Envi Component'
    bl_icon = 'SOUND'

    def supdate(self, context):
        self.outputs['Reference'].hide = False if self.linkmenu in ('Crack', 'EF') else True

    linktype = [("Crack", "Crack", "Crack aperture used for leakage calculation"),
        ("ELA", "ELA", "Effective leakage area"),
        ("EF", "Exhaust fan", "Exhaust fan")]

    linkmenu = bpy.props.EnumProperty(name="Type", description="Linkage type", items=linktype, default='ELA', update = supdate)

    ecl = bpy.props.FloatProperty(default = 0.0, min = 0, name = '', description = 'Extra Crack Length or Height of Pivoting Axis (m)')
    dcof = bpy.props.FloatProperty(default = 0.2, min = 0, max = 1, name = '', description = 'Discharge Coefficient')
    amfc = bpy.props.FloatProperty(default = 1.0, name = "")
    amfe = bpy.props.FloatProperty(default = 0.6, name = "")
    dlen = bpy.props.FloatProperty(default = 2, name = "")
    dhyd = bpy.props.FloatProperty(default = 0.1, name = "")
    dcs = bpy.props.FloatProperty(default = 0.1, name = "")
    dsr = bpy.props.FloatProperty(default = 0.0009, name = "")
    dlc = bpy.props.FloatProperty(default = 1.0, name = "")
    dhtc = bpy.props.FloatProperty(default = 0.772, name = "")
    dmtc = bpy.props.FloatProperty(default = 0.0001, name = "")
    cf = bpy.props.FloatProperty(default = 1, min = 0, max = 1, name = "")
    ela = bpy.props.FloatProperty(default = 0.1, min = 0, max = 1, name = "")
    rpd = bpy.props.FloatProperty(default = 4, min = 0.1, max = 50, name = "")

    def init(self, context):
        self.inputs.new('EnViCAirSocket', 'Node 1')
        self.inputs.new('EnViCAirSocket', 'Node 2')
        self.outputs.new('EnViCrRefSocket', 'Reference')
        self.outputs['Reference'].hide = True
        self.outputs.new('EnViCAirSocket', 'Node 1')
        self.outputs.new('EnViCAirSocket', 'Node 2')

    def update(self):
        try:
            lsocknames = ('Node 1', 'Node 2')
            for ins in [insock for insock in self.inputs if insock.name in lsocknames]:
                self.outputs[ins.name].hide = True if ins.is_linked else False
            for outs in [outsock for outsock in self.outputs if outsock.name in lsocknames]:
                self.inputs[outs.name].hide = True if outs.is_linked else False
        except:
            pass

        for sock in self.inputs:
            if self.linkmenu == 'ELA' and sock.is_linked:
                try:
                    self.ela = triarea(bpy.data.objects[sock.links[0].from_node.zone], bpy.data.objects[sock.links[0].from_node.zone].data.polygons[int(sock.links[0].from_socket.sn)])
                except:
                    pass

    def draw_buttons(self, context, layout):
        layout.prop(self, 'linkmenu')
        if self.linkmenu == "Crack":
            row = layout.row()
            row.label("Coefficient:")
            row.prop(self, 'amfc')
            row = layout.row()
            row.label("Exponent:")
            row.prop(self, 'amfe')
            row = layout.row()
            row.label("Crack factor:")
            row.prop(self, 'cf')

#        if self.linkmenu == "Duct":
#            row = layout.row()
#            row.label("Length:")
#            row.prop(self, 'dlen')
#            row = layout.row()
#            row.label("Hydraulic diameter:")
#            row.prop(self, 'dhyd')
#            row = layout.row()
#            row.label("Cross Section:")
#            row.prop(self, 'dcs')
#            row = layout.row()
#            row.label("Surface Roughness:")
#            row.prop(self, 'dsr')
#            row = layout.row()
#            row.label("Loss coefficient:")
#            row.prop(self, 'dlc')
#            row = layout.row()
#            row.label("U-Factor:")
#            row.prop(self, 'dhtc')
#            row = layout.row()
#            row.label("Moisture coefficient:")
#            row.prop(self, 'dmtc')

        if self.linkmenu == "ELA":
            row = layout.row()
            row.label("ELA:")
            row.prop(self, 'ela')
            row = layout.row()
            row.label("Discharge Coeff:")
            row.prop(self, 'dcof')
            row = layout.row()
            row.label("PA diff:")
            row.prop(self, 'rpd')
            row = layout.row()
            row.label("FE:")
            row.prop(self, 'amfe')

        if self.linkmenu == "EF":
            row = layout.row()
            row.label("Off FC:")
            row.prop(self, 'amfc')
            row = layout.row()
            row.label("Off FE:")
            row.prop(self, 'amfe')



class EnViCrRef(bpy.types.Node, EnViNodes):
    '''Node describing reference crack conditions'''
    bl_idname = 'EnViCrRef'
    bl_label = 'Envi Reference Crack Node'
    bl_icon = 'SOUND'

    reft = bpy.props.FloatProperty(name = '', min = 0, max = 30, default = 20, description = 'Reference Temperature ('+u'\u00b0C)')
    refp = bpy.props.IntProperty(name = '', min = 100000, max = 105000, default = 101325, description = 'Reference Pressure (Pa)')
    refh = bpy.props.FloatProperty(name = '', min = 0, max = 10, default = 0, description = 'Reference Humidity Ratio (kgWater/kgDryAir)')

    def init(self, context):
        self.inputs.new('EnViCrRefSocket', 'Reference', type = 'CUSTOM')

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.label('Temperature:')
        row.prop(self, 'reft')
        row = layout.row()
        row.label('Pressure:')
        row.prop(self, 'refp')
        row = layout.row()
        row.label('Humidity:')
        row.prop(self, 'refh')

class EnViFanNode(bpy.types.Node, EnViNodes):
    '''Node describing a fan component'''
    bl_idname = 'EnViFan'
    bl_label = 'Envi Fan'
    bl_icon = 'SOUND'

    fantype = [("Volume", "Constant Volume", "Constant volume flow fan component")]
    fantypeprop = bpy.props.EnumProperty(name="Type", description="Linkage type", items=fantype, default='Volume')
    fname = bpy.props.StringProperty(default = "", name = "")
    feff = bpy.props.FloatProperty(default = 0.7, name = "")
    fpr = bpy.props.FloatProperty(default = 600.0, name = "")
    fmfr = bpy.props.FloatProperty(default = 1.9, name = "")
    fmeff = bpy.props.FloatProperty(default = 0.9, name = "")
    fmaf = bpy.props.FloatProperty(default = 1.0, name = "")

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
            row = layout.row()
            row.label("Name:")
            row.prop(self, 'fname')
            row = layout.row()
            row.label("Efficiency:")
            row.prop(self, 'feff')
            row = layout.row()
            row.label("Pressure Rise (Pa):")
            row.prop(self, 'fpr')
            row = layout.row()
            row.label("Max flow rate:")
            row.prop(self, 'fmfr')
            row = layout.row()
            row.label("Motor efficiency:")
            row.prop(self, 'fmeff')
            row = layout.row()
            row.label("Airstream fraction:")
            row.prop(self, 'fmaf')

class EnViExtNode(bpy.types.Node, EnViNodes):
    '''Node describing a linkage component'''
    bl_idname = 'EnViExt'
    bl_label = 'Envi External Node'
    bl_icon = 'SOUND'

    height = bpy.props.FloatProperty(default = 1.0)
    azimuth = bpy.props.FloatProperty(default = 30)

    def init(self, context):
        self.inputs.new('EnViSAirSocket', 'External')
        self.outputs.new('EnViSAirSocket', 'External')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'linktypeprop')
        if self.linktypeprop == "Crack":
            layout.prop(self, 'amfc')
            layout.prop(self, 'amfe')



class EnViSched(bpy.types.Node, EnViNodes):
    '''Node describing a schedule'''
    bl_idname = 'EnViSched'
    bl_label = 'Schedule'
    bl_icon = 'SOUND'

#    def supdate(self):
#        self.inputs.new['Fraction'].hide = False if self.typemenu == 'Fraction' else True
#        self.inputs.new['Any Number'].hide = False if self.typemenu == 'Any Number' else True

#    typemenu = bpy.props.enumProperty(name = "", default = 'Fraction', items=[('Fraction', 'Fraction', 'Fraction'), ('Any Number', 'Any Number', 'Any Number')])
    t1 = bpy.props.IntProperty(name = "", default = 365)
    f1 = bpy.props.StringProperty(name = "Fors", description = "Valid entries (space separated): AllDays, Weekdays, Weekends, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, AllOtherDays")
    u1 = bpy.props.StringProperty(name = "Untils", description = "Valid entries (; separated for each 'For', comma separated for each day)")
    t2 = bpy.props.IntProperty(name = "")
    f2 = bpy.props.StringProperty(name = "Fors")
    u2 = bpy.props.StringProperty(name = "Untils")
    t3 = bpy.props.IntProperty(name = "")
    f3 = bpy.props.StringProperty(name = "Fors")
    u3 = bpy.props.StringProperty(name = "Untils")
    t4 = bpy.props.IntProperty(name = "")
    f4 = bpy.props.StringProperty(name = "Fors")
    u4 = bpy.props.StringProperty(name = "Untils")

    def init(self, context):
        self.inputs.new('EnViSchedSocket', 'Schedule')
#        self.inputs.new('ANSchSocket', 'Any Number')
#        self.inputs['Any Number'].hide = True

    def draw_buttons(self, context, layout):
#        layout.prop(self, 'typemenu')
        row = layout.row()
        row.label('End day 1:')
        row.prop(self, 't1')
        row = layout.row()
        row.prop(self, 'f1')
        row = layout.row()
        row.prop(self, 'u1')
        if self.u1 != '':
            row = layout.row()
            row.label('End day 2:')
            row.prop(self, 't2')
            row = layout.row()
            row.prop(self, 'f2')
            row = layout.row()
            row.prop(self, 'u2')
            if self.u2 != '':
                row = layout.row()
                row.label('End day 3:')
                row.prop(self, 't3')
                row = layout.row()
                row.prop(self, 'f3')
                row = layout.row()
                row.prop(self, 'u3')
                if self.u3 != '':
                    row = layout.row()
                    row.label('End day 4:')
                    row.prop(self, 't4')
                    row = layout.row()
                    row.prop(self, 'f4')
                    row = layout.row()
                    row.prop(self, 'u4')


#    def draw_buttons(self, context, layout):
#        layout.prop(self, 'linktypeprop')
#        if self.linktypeprop == "Crack":
#            layout.prop(self, 'amfc')
#            layout.prop(self, 'amfe')

class EnViNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'EnViN'

envinode_categories = [
        # identifier, label, items list
        EnViNodeCategory("Control", "Control Node", items=[NodeItem("AFNCon", label="Control Node")]),
        EnViNodeCategory("ZoneNodes", "Zone Nodes", items=[NodeItem("EnViZone", label="Zone Node"), NodeItem("EnViExt", label="External Node")]),
#        EnViNodeCategory("SLinkNodes", "Surface Link Nodes", items=[
#            NodeItem("EnViSLink", label="Surface Link Node")]),
        EnViNodeCategory("CLinkNodes", "Airflow Link Nodes", items=[
            NodeItem("EnViSLink", label="Surface Link Node"), NodeItem("EnViCLink", label="Component Link Node"), NodeItem("EnViCrRef", label="Crack Reference")]),
        EnViNodeCategory("SchedNodes", "Schedule Nodes", items=[
            NodeItem("EnViSched", label="Schedule")]),
        EnViNodeCategory("PlantNodes", "Plant Nodes", items=[
            NodeItem("EnViFan", label="EnVi fan node")])]