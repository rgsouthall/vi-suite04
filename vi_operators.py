import bpy, bpy_extras, sys, datetime, mathutils
import bpy_extras.io_utils as io_utils
import numpy as np
from collections import OrderedDict
from datetime import date
from datetime import datetime as dt
from math import cos, sin, pi, ceil
from numpy import arange
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from .livi_export import radcexport, radgexport
from .livi_calc  import rad_prev, li_calc
from .vi_display import li_display, li_compliance, linumdisplay, li3D_legend
from .envi_export import enpolymatexport, pregeo
from .envi_mat import envi_materials, envi_constructions
from .envi_calc import envi_sim
from .vi_func import processf, livisimacc, solarPosition, sunpath
from .vi_chart import chart_disp
#from . import windrose

envi_mats = envi_materials()
envi_cons = envi_constructions()

class NODE_OT_LiGExport(bpy.types.Operator):
    bl_idname = "node.ligexport"
    bl_label = "VI-Suite export"
    nodeid = bpy.props.StringProperty()

    def execute(self, context):
        context.scene.vi_display = 0
        if bpy.data.filepath and " " not in bpy.data.filepath:
            node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
            node.reslen = 0
            bpy.data.node_groups[self.nodeid.split('@')[1]].use_fake_user = 1
            radgexport(self, node)
            node.exported = True
            if node.bl_label[0] == '*':
                node.bl_label = node.bl_label[1:]
            node.outputs[0].hide = False
            return {'FINISHED'}

        elif " "  in bpy.data.filepath:
            self.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces and recreate this node")
            bpy.ops.node.delete()
            return {'FINISHED'}

        elif not bpy.data.filepath:
            self.report({'ERROR'},"The Blender file has not been saved. Save the Blender file and recreate this node before exporting")
            bpy.ops.node.delete()
            return {'FINISHED'}

class NODE_OT_EpwSelect(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.epwselect"
    bl_label = "Select EPW file"
    bl_description = "Select the EnergyPlus weather file"
    filename = ""
    filename_ext = ".HDR;.hdr;.epw;.EPW;"
    filter_glob = bpy.props.StringProperty(default="*.HDR;*.hdr;*.epw;*.EPW;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import EPW File with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("epw", "EPW", "HDR", "hdr"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].epwname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the EPW filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_HdrSelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.hdrselect"
    bl_label = "Select EPW file"
    bl_description = "Select the HDR image file"
    filename = ""
    filename_ext = ".HDR;.hdr;"
    filter_glob = bpy.props.StringProperty(default="*.HDR;*.hdr;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import HDR image file with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("HDR", "hdr"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodename].hdrname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the HDR filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_SkySelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.skyselect"
    bl_label = "Select EPW file"
    bl_description = "Select the Radiance sky file"
    filename = ""
    filename_ext = ".rad;.RAD;"
    filter_glob = bpy.props.StringProperty(default="*.RAD;*.rad;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import a Radiance sky file with the fileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("RAD", "rad"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodename].skyname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the Radiance sky filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_LiExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.liexport"
    bl_label = "Export"
    bl_description = "Export the scene to the Radiance file format"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        context.scene.li_disp_panel = 0
        context.scene.lic_disp_panel = 0
        context.scene.vi_display = 0
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
        if node.bl_label == 'LiVi Basic':
            node.resname = ("illumout", "irradout", "dfout")[int(node.analysismenu)]
            node.unit = ("Lux", "W/m"+ u'\u00b2', "DF %")[int(node.analysismenu)]
            node.skynum = int(node.skymenu) if node.analysismenu != "2" else 3
            if str(sys.platform) != 'win32':
                node.simalg = (" |  rcalc  -e '$1=47.4*$1+120*$2+11.6*$3' ", " |  rcalc  -e '$1=$1' ", " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)/100' ")[int(node.analysismenu)]
            else:
                node.simalg = (' |  rcalc  -e "$1=47.4*$1+120*$2+11.6*$3" ', ' |  rcalc  -e "$1=$1" ', ' |  rcalc  -e "$1=(47.4*$1+120*$2+11.6*$3)/100" ')[int(node.analysismenu)]
            node.TZ = node.summer if node.daysav == True else node.stamer

        elif node.bl_label == 'LiVi Compliance':
            if node.analysismenu in ('0', '1'):
                node.unit = "DF %"
                if str(sys.platform) != 'win32':
                    node.simalg = " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)/100' "
                else:
                    node.simalg = ' |  rcalc  -e "$1=(47.4*$1+120*$2+11.6*$3)/100" '

                if node.analysismenu == '0':
                    node.resname = 'breaamout'

                elif node.analysismenu == '1':
                    node.resname = 'cfsh'

        elif node.bl_label == 'LiVi CBDM':
            node.resname = ('luxhours', 'cumwatth', 'dayauto', 'hourrad', 'udi')[int(node.analysismenu)]
            node.unit = ('LuxHours', 'Annual Wh', 'DA (%)', '', 'UDI-a (%)')[int(node.analysismenu)]

        if bpy.data.filepath:
            if bpy.context.object:
                if bpy.context.object.type == 'MESH' and bpy.context.object.hide == False and bpy.context.object.layers[0] == True:
                    bpy.ops.object.mode_set(mode = 'OBJECT')

            if " " not in bpy.data.filepath:
                if node.inputs['Geometry in'].is_linked:
                    radcexport(self, node)
                    node.disp_leg = False
                    node.exported = True
                    node.outputs['Context out'].hide = False
                else:
                    self.report({'ERROR'},"No geometry node is linked")
                    node.outputs['Context out'].hide = True
            else:
                node.outputs['Context out'].hide = True
                self.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces")
                return {'FINISHED'}
            return {'FINISHED'}
        else:
            node.outputs['Context out'].hide = True
            self.report({'ERROR'},"Save the Blender file before exporting")
            return {'FINISHED'}

class NODE_OT_RadPreview(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.radpreview"
    bl_label = "Preview"
    bl_description = "Prevew the scene with Radiance"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        connode = simnode.inputs['Context in'].links[0].from_node
        geonode = connode.inputs['Geometry in'].links[0].from_node
        rad_prev(self, simnode, connode, geonode, livisimacc(simnode, connode))
        return {'FINISHED'}

class NODE_OT_Calculate(bpy.types.Operator):
    bl_idname = "node.calculate"
    bl_label = "Radiance Export and Simulation"

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        connode = simnode.inputs['Context in'].links[0].from_node
        geonode = connode.inputs['Geometry in'].links[0].from_node

        li_calc(self, simnode, connode, geonode, livisimacc(simnode, connode))
        context.scene.vi_display = 0
        context.scene.li_disp_panel = 1
        context.scene.lic_disp_panel = 1 if connode.bl_label == 'LiVi Compliance' else 0
        context.scene.resnode = simnode.name
        context.scene.restree = self.nodeid.split('@')[1]
        return {'FINISHED'}

class VIEW3D_OT_LiDisplay(bpy.types.Operator):
    bl_idname = "view3d.lidisplay"
    bl_label = "Radiance Results Display"
    bl_description = "Display the results on the sensor surfaces"
    bl_register = True
    bl_undo = True

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[context.scene.restree].nodes[context.scene.resnode]
        connode = simnode.inputs['Context in'].links[0].from_node
        geonode = connode.inputs['Geometry in'].links[0].from_node
        try:
            li_display(simnode, connode, geonode)
            bpy.ops.view3d.linumdisplay()
        except:
            self.report({'ERROR'},"No results available for display. Try re-running the calculation.")
#            raise
        return {'FINISHED'}

class VIEW3D_OT_LiNumDisplay(bpy.types.Operator):
    '''Display results legend and stats in the 3D View'''
    bl_idname = "view3d.linumdisplay"
    bl_label = "Point numbers"
    bl_description = "Display the point results on the sensor surfaces"
    bl_register = True
    bl_undo = True

    def modal(self, context, event):
        context.area.tag_redraw()
        if context.scene.vi_display == 0:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_leg, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_pointres, 'WINDOW')
            if bpy.context.scene.resnode == 'LiVi Compliance':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle_comp, 'WINDOW')
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        simnode = bpy.data.node_groups[context.scene.restree].nodes[context.scene.resnode]
        connode = simnode.inputs['Context in'].links[0].from_node
        geonode = connode.inputs['Geometry in'].links[0].from_node

        if context.area.type == 'VIEW_3D':
            self._handle_leg = bpy.types.SpaceView3D.draw_handler_add(li3D_legend, (self, context, simnode, connode), 'WINDOW', 'POST_PIXEL')
            self._handle_pointres = bpy.types.SpaceView3D.draw_handler_add(linumdisplay, (self, context, simnode, geonode), 'WINDOW', 'POST_PIXEL')
            if connode.bl_label == 'LiVi Compliance':
                self._handle_comp = bpy.types.SpaceView3D.draw_handler_add(li_compliance, (self, context, connode), 'WINDOW', 'POST_PIXEL')
            context.scene.vi_display = 1
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

class IES_Select(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "livi.ies_select"
    bl_label = "Select IES file"
    bl_description = "Select the lamp IES file"
    filename = ""
    filename_ext = ".ies; .IES"
    filter_glob = bpy.props.StringProperty(default="*.ies; *.IES", options={'HIDDEN'})
    bl_register = True
    bl_undo = True

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Open an IES File with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        lamp = bpy.context.active_object
        lamp['ies_name'] = self.filepath if " " not in self.filepath else self.report({'ERROR'}, "There is a space either in the IES filename or directory location. Rename or move the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_ESOSelect(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = "node.esoselect"
    bl_label = "Select EnVi results file"
    bl_description = "Select the EnVi results file to process"
    filename = ""
    filename_ext = ".eso"
    filter_glob = bpy.props.StringProperty(default="*.eso", options={'HIDDEN'})
    bl_register = True
    bl_undo = True

    nodename = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Open an eso results file with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        bpy.data.node_groups['VI Network'].nodes[self.nodename].resfilename = self.filepath
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_EnGExport(bpy.types.Operator):
    bl_idname = "node.engexport"
    bl_label = "VI-Suite export"
    bl_context = "scene"
    nodename = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        pregeo()
        node.exported = True
        node.outputs[0].hide = False
        return {'FINISHED'}

class NODE_OT_EnExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.enexport"
    bl_label = "Export"
    bl_description = "Export the scene to the EnergyPlus file format"
    bl_register = True
    bl_undo = True
    nodename = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        if bpy.data.filepath:
            if bpy.context.object:
                if bpy.context.object.type == 'MESH':
                    bpy.ops.object.mode_set(mode = 'OBJECT')
            if " " not in str(node.filedir) and " " not in str(node.filename):
#                if not os.path.isdir(envi_settings.filedir+"/"+envi_settings.filename):
#                    os.makedirs(envi_settings.filedir+"/"+envi_settings.filename)

                enpolymatexport(self, node, envi_mats, envi_cons)
                node.exported = True
            elif " " in str(node.filedir):
                self.report({'ERROR'},"The directory path containing the Blender file has a space in it.")
                return {'FINISHED'}
            elif " " in str(node.filename):
                self.report({'ERROR'},"The Blender filename has a space in it.")
                return {'FINISHED'}
            return {'FINISHED'}
        else:
            self.report({'ERROR'},"Save the Blender file before exporting")
            return {'FINISHED'}

class NODE_OT_EnSim(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.ensim"
    bl_label = "Simulate"
    bl_description = "Run EnergyPlus"
    bl_register = True
    bl_undo = True
    nodename = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        envi_sim(self, node)
        if not node.outputs:
            node.outputs.new('ViEnROut', 'Results out')
        if node.outputs[0].is_linked:
            socket1 = node.outputs[0]
            socket2 = node.outputs[0].links[0].to_socket
            bpy.data.node_groups['VI Network'].links.remove(node.outputs[0].links[0])
            bpy.data.node_groups['VI Network'].links.new(socket1, socket2)

        context.scene.li_disp_panel = 2
        return {'FINISHED'}

class NODE_OT_Chart(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.chart"
    bl_label = "Chart"
    bl_description = "Create a 2D graph from the results file"
    bl_register = True
    bl_undo = True
    nodename = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        Sdate = dt.fromordinal(dt(dt.now().year, 1, 1).toordinal() + node['Start'] -1) + datetime.timedelta(hours = node.dsh - 1)
        Edate = dt.fromordinal(dt(dt.now().year, 1, 1).toordinal() + node['End'] -1 ) + datetime.timedelta(hours = node.deh - 1)

        innodes = list(OrderedDict.fromkeys([inputs.links[0].from_node for inputs in node.inputs if inputs.is_linked]))
        chart_disp(self, node, innodes, Sdate, Edate)
        return {'FINISHED'}

class NODE_OT_FileProcess(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.fileprocess"
    bl_label = "Process"
    bl_description = "Process EnergyPlus results file"
    bl_register = True
    bl_undo = True
    nodename = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        processf(self, node)
        if not node.outputs:
            node.outputs.new('ViEnROut', 'Results out')
        return {'FINISHED'}

class NODE_OT_SunPath(bpy.types.Operator):
    bl_idname = "node.sunpath"
    bl_label = "Sun Path"
    bl_description = "Create a Sun Path"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        sd = 100
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        locnode = node.inputs[0].links[0].from_node
        scene = context.scene
        scene.resnode = node.name
        scene.restree = self.nodeid.split('@')[1]

        if locnode.loc == "1":
            with open(locnode.weather, "r") as epwfile:
               fl = epwfile.readline()
               scene.latitude, scene.longitude = float(fl.split(",")[6]), float(fl.split(",")[7])

        if len([ob for ob in context.scene.objects if ob.spob == 1]) == 0:
            bpy.ops.object.lamp_add(type = "SUN")
            sun = context.active_object
        else:
            sun = [ob for ob in context.scene.objects if ob.spob == 1][0]
        sun.spob = 1
        sun['solhour'], sun['solday'], sun['soldistance'] = scene.solhour, scene.solday, scene.soldistance

        if len([ob for ob in context.scene.objects if ob.spob == 2]) == 0:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=12, size=1)
            sunob = context.active_object
            sunob.name = "SunMesh"
        else:
            sunob = [ob for ob in context.scene.objects if ob.spob == 2][0]
        sunob.spob = 2

        if len([ob for ob in context.scene.objects if ob.spob == 3]) != 0:
            context.scene.objects.unlink([ob for ob in context.scene.objects if ob.spob == 3][0])
            [ob for ob in bpy.data.objects if ob.type == "CURVE" and ob.name == "SPathMesh"][0].name = 'oldspathmesh'
        bpy.ops.object.add(type = "MESH")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.wireframe(thickness=0.005)
        bpy.ops.object.mode_set(mode='OBJECT')
        spathob = context.active_object
        spathob.name = "SPathMesh"
        spathob.spob = 3

        spathmesh = spathob.data
        for v in spathmesh.vertices:
            v.remove()

        for doy in range(0, 363):
            if (doy-4)%7 == 0:
                for hour in range(1, 25):
                    ([solalt, solazi]) = solarPosition(doy, hour, scene.latitude, scene.longitude)[2:]

                    spathmesh.vertices.add(1)
                    spathmesh.vertices[-1].co = [(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]

        for v in range(24, len(spathmesh.vertices)):

            spathmesh.edges.add(1)
            spathmesh.edges[-1].vertices[0] = v
            spathmesh.edges[-1].vertices[1] = v - 24
            if v in range(1224, 1248):

                spathmesh.edges.add(1)
                spathmesh.edges[-1].vertices[0] = v
                spathmesh.edges[-1].vertices[1] = v - 1224

            if v in (1200, 96, 192, 264, 360, 456, 576):
                for e in range(v, v+23):

                    spathmesh.edges.add(1)
                    spathmesh.edges[-1].vertices[0] = e
                    spathmesh.edges[-1].vertices[1] = e + 1

                spathmesh.edges.add(1)
                spathmesh.edges[-1].vertices[0] = v
                spathmesh.edges[-1].vertices[1] = v + 23
        bpy.ops.object.convert(target='CURVE')
        bpy.data.objects['SPathMesh'].data.bevel_depth = 0.1

        for edge in spathmesh.edges:
            if spathmesh.vertices(edge.vertices[0]).co.z < 0
            if len([spathmesh.vertices(edges.vertices[0:2]) for edges in spathmesh.edges

#        sunpath(context, sun, sunob, spathob)
        if node.modal == 1:
            bpy.ops.view3d.sunpath()
        context.scene.sp_disp_panel = 1
        context.scene.li_disp_panel = 0
        return {'FINISHED'}

class VIEW3D_OT_SunPath(bpy.types.Operator):
    bl_idname = "view3d.sunpath"
    bl_label = "Sun Path"
    bl_description = "Modify a Sun Path"
    bl_register = True
    bl_undo = True

    def modal(self, context, event):
        if context.scene.vi_display == 0:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_sp, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._handle_sp = bpy.types.SpaceView3D.draw_handler_add(sunpath, (self, context), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

class NODE_OT_WindRose(bpy.types.Operator):
    bl_idname = "node.windrose"
    bl_label = "Wind Rose"
    bl_description = "Create a Wind Rose"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
#        aws, awd = [], []
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        locnode = node.inputs[0].links[0].from_node
        with open(locnode.weather, "r") as epwfile:
            wvals = [line.split(",")[20:22] for l, line in enumerate(epwfile.readlines()) if l > 7 and node.startmonth <= int(line.split(",")[1]) < node.endmonth]

        awd = [float(val[0]) for val in wvals]
        aws = [float(val[1]) for val in wvals]

#            aws = [float(line.split(",")[21]) for l, line in enumerate(epwfile.readlines()) if l > 7 and node.startmonth <= int(line.split(",")[1]) < node.endmonth]
#            for l, line in enumerate(epwfile.readlines()):
#                if l > 7 and int(line.split(",")[1]) >= node.startmonthm and int(line.split(",")[1]) <= node.endmonth:
#                    if line.split(",")[21] != "" and line.split(",")[20] != "":
#                        aws.append(float(line.split(",")[21]))
#                        awd.append(float(line.split(",")[20]))
#def envi_wind(epwfile, sm, em):
#    filepath = bpy.data.filepath
#    filename = os.path.splitext(os.path.basename(filepath))[0]
#    filedir = os.path.dirname(filepath)
#    if not os.path.isdir(filedir+"/envi_"+filename):
#        os.makedirs(filedir+"/envi_"+filename)
#    newdir = filedir+"/envi_"+filename
#    aws = []
#    awd = []
#    epwfile = open(epwfile)
        print(aws, awd)
        ax = plt.subplot(111, polar=True)
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
#        theta = np.linspace(0.0, 2 * np.pi, 20, endpoint=False)
#        radii = 10 * np.random.rand(N)
    #    ax.contourf(awd, aws, bins=arange(0,int(math.ceil(max(aws))),1), normed = 1, cmap=cm.hot)
    #    ax.contour(awd, aws, bins=arange(0,int(math.ceil(max(aws))),1), normed = 1, colors='black')
#        bars = ax.bar(theta, radii, width=width, bottom=0.0)
        ax.hist(awd, aws, bins=arange(0,int(ceil(max(aws))),2))
     #   ax.box(awd, aws, bins=arange(0,int(math.ceil(max(aws))),1), normed = 1)
#        set_legend(ax)
        plt.savefig(locnode.newdir+'/disp_wind.png', dpi = (300), transparent=True)
        plt.savefig(locnode.newdir+'/disp_wind.svg')

        if 'disp_wind.png' not in [im.name for im in bpy.data.images]:
            bpy.data.images.load(locnode.newdir+'/disp_wind.png')
        else:
            bpy.data.images['disp_wind.png'].filepath = locnode.newdir+'/disp_wind.png'
            bpy.data.images['disp_wind.png'].reload()

        if 'Wind_Plane' not in [wp.name for wp in bpy.data.objects]:

            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, location=(0.0, 0.0, 0.0))

            wind_mat = bpy.data.materials.new('Wind_Rose')
            tex = bpy.data.textures.new(type = 'IMAGE', name = 'Wind_Tex')
            tex.image = bpy.data.images['disp_wind.png']
            wind_mat.texture_slots.add()
            wind_mat.texture_slots[0].texture = tex
            wind_mat.texture_slots[0].use_map_alpha = True

            bpy.context.active_object.name = "Wind_Plane"
            bpy.ops.object.material_slot_add()
            bpy.context.active_object.material_slots[0].material = wind_mat
            bpy.context.active_object.data.uv_textures.new()
            bpy.context.active_object.data.uv_textures[0].data[0].image = bpy.data.images['disp_wind.png']
            bpy.context.active_object.scale = (100, 100, 100)
            wind_mat.use_transparency = True
            wind_mat.transparency_method = 'Z_TRANSPARENCY'
            wind_mat.alpha = 0.0

def new_axes():
    fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
    rect = [0.1, 0.1, 0.8, 0.8]
    ax = windrose.WindroseAxes(fig, rect, axisbg='w')
    fig.add_axes(ax)
    return ax

def set_legend(ax):
    l = ax.legend(axespad=-0.10)
    plt.setp(l.get_texts(), fontsize=8)