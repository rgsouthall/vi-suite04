import bpy, bpy_extras, sys, datetime, mathutils
import bpy_extras.io_utils as io_utils
try:
    import numpy
    np = 1
except:
    np = 0
#from multiprocessing.pool import ThreadPool as Pool
#from multiprocessing import Pool
from collections import OrderedDict
from datetime import datetime as dt
from math import cos, sin, pi, ceil, tan, modf
from numpy import arange
try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    mp = 1
except:
    mp = 0
from .livi_export import radcexport, radgexport, cyfc1
from .livi_calc  import rad_prev, li_calc, li_glare, resapply
from .vi_display import li_display, li_compliance, linumdisplay, spnumdisplay, li3D_legend, viwr_legend
from .envi_export import enpolymatexport, pregeo
from .envi_mat import envi_materials, envi_constructions
from .envi_calc import envi_sim
from .vi_func import processf, livisimacc, solarPosition, retobjs, wr_axes, clearscene, framerange, vcframe, latilongi, nodeinit
from .vi_chart import chart_disp
from .vi_gen import vigen

envi_mats = envi_materials()
envi_cons = envi_constructions()

class NODE_OT_LiGExport(bpy.types.Operator):
    bl_idname = "node.ligexport"
    bl_label = "VI-Suite export"
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        if bpy.data.filepath and " " not in bpy.data.filepath:
            node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
            if node.filepath != bpy.data.filepath:
                nodeinit(node)
            node.reslen = 0
            scene.frame_start, bpy.data.node_groups[self.nodeid.split('@')[1]].use_fake_user = 0, 1
            scene.frame_set(0)
            radgexport(self, node)
            node.exported, node.outputs[1].hide = True, False
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
    bl_label = "Select HDR/VEC file"
    bl_description = "Select the HDR sky image or vector file"
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
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].hdrname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the HDR filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_MtxSelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.mtxselect"
    bl_label = "Select MTX file"
    bl_description = "Select the matrix file"
    filename = ""
    filename_ext = ".MTX;.mtx;"
    filter_glob = bpy.props.StringProperty(default="*.MTX;*.mtx;", options={'HIDDEN'})
    bl_register = True
    bl_undo = True
    nodeid = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import MTX file with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("MTX", "mtx"):
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].mtxname = self.filepath
        if " " in self.filepath:
            self.report({'ERROR'}, "There is a space either in the matrix filename or its directory location. Remove this space and retry opening the file.")
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_SkySelect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "node.skyselect"
    bl_label = "Select RAD file"
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
            bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].skyname = self.filepath
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
        scene = context.scene
        scene.frame_start = 0
        scene.frame_set(0)
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        if node.bl_label == 'LiVi Basic' and node.inputs['Location in'].is_linked and node.inputs['Location in'].links[0].from_node.bl_label == 'VI Location':
            latilongi(scene, node.inputs['Location in'].links[0].from_node)
        node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
        if node.bl_label == 'LiVi Basic':
            node.skynum = int(node.skymenu) if node.analysismenu != "2" else 3
            if str(sys.platform) != 'win32':
                node.simalg = (" |  rcalc  -e '$1=47.4*$1+120*$2+11.6*$3' ", " |  rcalc  -e '$1=$1' ", " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)/100' ", '')[int(node.analysismenu)]
            else:
                node.simalg = (' |  rcalc  -e "$1=47.4*$1+120*$2+11.6*$3" ', ' |  rcalc  -e "$1=$1" ', ' |  rcalc  -e "$1=(47.4*$1+120*$2+11.6*$3)/100" ', '')[int(node.analysismenu)]
#            node.TZ = node.summer if node.daysav == True else node.stamer

        elif node.bl_label == 'LiVi Compliance':
            if node.analysismenu in ('0', '1'):
                if str(sys.platform) != 'win32':
                    node.simalg = " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)/100' "
                else:
                    node.simalg = ' |  rcalc  -e "$1=(47.4*$1+120*$2+11.6*$3)/100" '

        elif node.bl_label == 'LiVi CBDM':
            node.skynum = 4
            node.simalg = (" |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)/1000' ", " |  rcalc  -e '$1=($1+$2+$3)/3000' ", " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)' ", " |  rcalc  -e '$1=($1+$2+$3)/3' ", " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)' ")[int(node.analysismenu)]
            node['wd'] = (7, 5)[node.weekdays]

        if bpy.data.filepath:
            if bpy.context.object:
                if bpy.context.object.type == 'MESH' and bpy.context.object.hide == False and bpy.context.object.layers[0] == True:
                    bpy.ops.object.mode_set(mode = 'OBJECT')

            if " " not in bpy.data.filepath:
                if (node.bl_label == 'LiVi CBDM' and node.inputs['Geometry in'].is_linked and (node.inputs['Location in'].is_linked or node.sm != '0')) \
                or (node.bl_label != 'LiVi CBDM' and node.inputs['Geometry in'].is_linked):
                    radcexport(self, node)
#                    node.disp_leg = False
                    node.exported = True
                    node.outputs['Context out'].hide = False
                else:
                    self.report({'ERROR'},"Required input nodes are not linked")
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
        scene = context.scene
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        connode = simnode.inputs['Context in'].links[0].from_node
        geonode = connode.inputs['Geometry in'].links[0].from_node
        
        for geo in retobjs('livig'):
            geo.licalc = any([m.livi_sense for m in geo.data.materials])
        geogennode = geonode.outputs['Generative out'].links[0].to_node if geonode.outputs['Generative out'].is_linked else 0  
        
        if connode.bl_label == 'LiVi Basic':                  
            tarnode = connode.outputs['Target out'].links[0].to_node if connode.outputs['Target out'].is_linked else 0
#        if connode.bl_label == 'LiVi Basic':
            if geogennode and tarnode: 
                simnode['Animation'] = 'Animated'
#                scene.fs, scene.fe = scene.frame_start, scene.frame_end
                vigen(self, li_calc, resapply, geonode, connode, simnode, geogennode, tarnode)     
                scene.vi_display = 1
            elif connode.analysismenu != '3':
                simnode['Animation'] = connode['Animation']
#                scene.fs = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_start
#                scene.fe = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_end
                li_calc(self, simnode, connode, geonode, livisimacc(simnode, connode))
                scene.vi_display = 1
            else:
                simnode['Animation'] = connode['Animation']
#                scene.fs = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_start
#                scene.fe = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_end
                li_glare(self, simnode, connode, geonode)
                scene.vi_display = 0
        else:
            simnode['Animation'] = connode['Animation']
            scene.fs = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_start
            scene.fe = scene.frame_current if simnode['Animation'] == 'Static' else scene.frame_end
            li_calc(self, simnode, connode, geonode, livisimacc(simnode, connode))
            scene.vi_display = 1
        context.scene.fe = framerange(context.scene, simnode['Animation'])[-1]
        (scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel) = (0, 1, 1, 0, 0, 0) if connode.bl_label == 'LiVi Compliance'  else (0, 1, 0, 0, 0, 0)
        context.scene.resnode = simnode.name
        context.scene.restree = self.nodeid.split('@')[1]
        return {'FINISHED'}

class VIEW3D_OT_LiDisplay(bpy.types.Operator):
    bl_idname = "view3d.lidisplay"
    bl_label = "Radiance Results Display"
    bl_description = "Display the results on the sensor surfaces"
    bl_register = True
    bl_undo = True

    _handle = None

    def modal(self, context, event):
        if context.scene.li_disp_panel != 2 and context.scene.ss_disp_panel != 2:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_leg, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_pointres, 'WINDOW')
            if context.scene.get('LiViContext') == 'LiVi Compliance':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle_comp, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scene = bpy.context.scene
        simnode = bpy.data.node_groups[scene.restree].nodes[scene.resnode]
        connode = 0 if simnode.bl_label == 'VI Shadow Study' else simnode.inputs['Context in'].links[0].from_node
        geonode = 0 if simnode.bl_label == 'VI Shadow Study' else connode.inputs['Geometry in'].links[0].from_node
        li_display(simnode, connode, geonode)
        scene.li_disp_panel, scene.ss_disp_panel = 2, 2
        self._handle_pointres = bpy.types.SpaceView3D.draw_handler_add(linumdisplay, (self, context, simnode, connode, geonode), 'WINDOW', 'POST_PIXEL')
        self._handle_leg = bpy.types.SpaceView3D.draw_handler_add(li3D_legend, (self, context, simnode, connode, geonode), 'WINDOW', 'POST_PIXEL')
        if context.scene.get('LiViContext') == 'LiVi Compliance':
            self._handle_comp = bpy.types.SpaceView3D.draw_handler_add(li_compliance, (self, context, connode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

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

    nodeid = bpy.props.StringProperty()
    
    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Open an eso results file with the file browser", icon='WORLD_DATA')

    def execute(self, context):
        bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]].resfilename = self.filepath
        return {'FINISHED'}

    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_EnGExport(bpy.types.Operator):
    bl_idname = "node.engexport"
    bl_label = "VI-Suite export"
    bl_context = "scene"
    
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        pregeo(self)
        node.exported = True
        node.outputs[0].hide = False
        return {'FINISHED'}

class NODE_OT_EnExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.enexport"
    bl_label = "Export"
    bl_description = "Export the scene to the EnergyPlus file format"
    bl_register = True
    bl_undo = True
    
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 0, 0, 0, 0, 0, 0, 0
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        locnode = node.inputs['Location in'].links[0].from_node
        if bpy.data.filepath:
            if bpy.context.object:
                if bpy.context.object.type == 'MESH':
                    bpy.ops.object.mode_set(mode = 'OBJECT')
            if " " not in str(node.filedir) and " " not in str(node.filename):
                enpolymatexport(self, node, locnode, envi_mats, envi_cons)
                node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
                node.exported = True
                node.outputs['Context out'].hide = False
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
    
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        connode = node.inputs['Context in'].links[0].from_node
        envi_sim(self, node, connode)
        node.outputs['Results out'].hide = False
        if node.outputs[0].is_linked:
            socket1, socket2  = node.outputs[0], node.outputs[0].links[0].to_socket
            bpy.data.node_groups[self.nodeid.split('@')[1]].links.remove(node.outputs[0].links[0])
            bpy.data.node_groups[self.nodeid.split('@')[1]].links.new(socket1, socket2)
        scene = context.scene
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 2, 0, 0, 0, 0
        return {'FINISHED'}

class NODE_OT_Chart(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.chart"
    bl_label = "Chart"
    bl_description = "Create a 2D graph from the results file"
    bl_register = True
    bl_undo = True
    
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
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
    
    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        processf(self, node)
        node.outputs['Results out'].hide = False
        node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label
        return {'FINISHED'}

class NODE_OT_SunPath(bpy.types.Operator):
    bl_idname = "node.sunpath"
    bl_label = "Sun Path"
    bl_description = "Create a Sun Path"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        solringnum, sd, numpos, ordinals = 0, 100, {}, []
        node = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        locnode = node.inputs[0].links[0].from_node
        scene, scene.resnode, scene.restree = context.scene, node.name, self.nodeid.split('@')[1]
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 1, 0, 0, 0, 0, 0

        if 'SolEquoRings' not in [mat.name for mat in bpy.data.materials]:
            bpy.data.materials.new('SolEquoRings')
            bpy.data.materials['SolEquoRings'].diffuse_color = (1, 0, 0)
        if 'HourRings' not in [mat.name for mat in bpy.data.materials]:
            bpy.data.materials.new('HourRings')
            bpy.data.materials['HourRings'].diffuse_color = (1, 1, 0)
        if 'SPBase' not in [mat.name for mat in bpy.data.materials]:
            bpy.data.materials.new('SPBase')
            bpy.data.materials['SPBase'].diffuse_color = (1, 1, 1)
        if 'Sun' not in [mat.name for mat in bpy.data.materials]:
            bpy.data.materials.new('Sun')
            bpy.data.materials['Sun'].diffuse_color = (1, 1, 1)

        if locnode.loc == "1":
            with open(locnode.weather, "r") as epwfile:
               fl = epwfile.readline()
               scene.latitude, scene.longitude = float(fl.split(",")[6]), float(fl.split(",")[7])
        
        if 'SUN' in [ob.data.type for ob in context.scene.objects if ob.data == 'LAMP' and ob.hide == False]:
            [ob.data.type for ob in context.scene.objects if ob.data == 'LAMP' and ob.data.type == 'SUN'][0]['VIType'] = 'Sun'
            
        elif 'Sun' not in [ob.get('VIType') for ob in context.scene.objects]:
            bpy.ops.object.lamp_add(type = "SUN")
            sun = context.active_object
            sun['VIType'] = 'Sun'
        else:
            sun = [ob for ob in context.scene.objects if ob.get('VIType') == 'Sun'][0]
            sun.animation_data_clear()

        if scene.render.engine == 'CYCLES' and bpy.data.worlds['World'].get('node_tree') and 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
            bpy.data.worlds['World'].node_tree.animation_data_clear()

        sun['solhour'], sun['solday'], sun['soldistance'] = scene.solhour, scene.solday, scene.soldistance

        if "SunMesh" not in [ob.get('VIType') for ob in context.scene.objects]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=12, size=1)
            sunob = context.active_object
            sunob.name = "SunMesh"
            sunob['VIType'] = 'SunMesh'
        else:
            sunob = [ob for ob in context.scene.objects if ob.get('VIType') == "SunMesh"][0]

        if len(sunob.material_slots) == 0:
             bpy.ops.object.material_slot_add()
             sunob.material_slots[0].material = bpy.data.materials['Sun']

        for ob in context.scene.objects:
            if ob.get('VIType') == "SPathMesh":
                context.scene.objects.unlink(ob)
                ob.name = 'oldspathmesh'

        bpy.ops.object.add(type = "MESH")
        spathob = context.active_object
        spathob.name = "SPathMesh"
        spathob['VIType'] = 'SPathMesh'
        spathmesh = spathob.data

        for doy in range(0, 363):
            if (doy-4)%7 == 0:
                for hour in range(1, 25):
                    ([solalt, solazi]) = solarPosition(doy, hour, scene.latitude, scene.longitude)[2:]
                    spathmesh.vertices.add(1)
                    spathmesh.vertices[-1].co = [-(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]

        for v in range(24, len(spathmesh.vertices)):
            if spathmesh.vertices[v].co.z > 0 or spathmesh.vertices[v - 24].co.z > 0:
                spathmesh.edges.add(1)
                spathmesh.edges[-1].vertices[0] = v
                spathmesh.edges[-1].vertices[1] = v - 24
            if v in range(1224, 1248):
                if spathmesh.vertices[v].co.z > 0 or spathmesh.vertices[v - 1224].co.z > 0:
                    spathmesh.edges.add(1)
                    spathmesh.edges[-1].vertices[0] = v
                    spathmesh.edges[-1].vertices[1] = v - 1224

        for doy in (79, 172, 355):
            for hour in range(1, 25):
                ([solalt, solazi]) = solarPosition(doy, hour, scene.latitude, scene.longitude)[2:]
                spathmesh.vertices.add(1)
                spathmesh.vertices[-1].co = [-(sd-(sd-(sd*cos(solalt))))*sin(solazi), -(sd-(sd-(sd*cos(solalt))))*cos(solazi), sd*sin(solalt)]
                if spathmesh.vertices[-1].co.z >= 0 and doy in (172, 355):
                    numpos['{}-{}'.format(doy, hour)] = spathmesh.vertices[-1].co[:]
                if hour != 1:
                    if spathmesh.vertices[-2].co.z > 0 or spathmesh.vertices[-1].co.z > 0:
                        spathmesh.edges.add(1)
                        solringnum += 1
                        spathmesh.edges[-1].vertices[0] = spathmesh.vertices[-2].index
                        spathmesh.edges[-1].vertices[1] = spathmesh.vertices[-1].index
                if hour == 24:
                    if spathmesh.vertices[-24].co.z > 0 or spathmesh.vertices[-1].co.z > 0:
                        spathmesh.edges.add(1)
                        solringnum += 1
                        spathmesh.edges[-1].vertices[0] = spathmesh.vertices[-24].index
                        spathmesh.edges[-1].vertices[1] = spathmesh.vertices[-1].index

        for edge in spathmesh.edges:
            intersect = mathutils.geometry.intersect_line_plane(spathmesh.vertices[edge.vertices[0]].co, spathmesh.vertices[edge.vertices[1]].co, mathutils.Vector((0,0,0)), mathutils.Vector((0,0,1)))

            if spathmesh.vertices[edge.vertices[0]].co.z < 0:
                spathmesh.vertices[edge.vertices[0]].co = intersect
            if spathmesh.vertices[edge.vertices[1]].co.z < 0:
                spathmesh.vertices[edge.vertices[1]].co = intersect

        bpy.ops.object.convert(target='CURVE')
        spathob.data.bevel_depth = 0.08
        spathob.data.bevel_resolution = 6
        bpy.context.object.data.fill_mode = 'FULL'
        bpy.ops.object.convert(target='MESH')

        bpy.ops.object.material_slot_add()
        spathob.material_slots[0].material = bpy.data.materials['HourRings']
        spathob['numpos'] = numpos

        for vert in spathob.data.vertices[0:16 * (solringnum + 3)]:
            vert.select = True

        bpy.ops.object.material_slot_add()
        spathob.material_slots[-1].material = bpy.data.materials['SolEquoRings']
        spathob.active_material_index = 1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = [True, False, False]
        bpy.ops.object.material_slot_assign()
        bpy.ops.object.material_slot_add()
        spathob.material_slots[-1].material = bpy.data.materials['SPBase']
        spathob.active_material_index = 2

        for i in range(1, 6):
            bpy.ops.mesh.primitive_torus_add(major_radius=i*sd*0.2, minor_radius=i*0.1*0.2, major_segments=64, minor_segments=8, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0))
            bpy.ops.object.material_slot_assign()
        for j in range(5):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=(2-j%2)*0.04, depth=2.05*sd, end_fill_type='NGON', view_align=False, location=(0.0, 0.0, 0.0), rotation=(pi/2, 0.0, j*pi/4))
            bpy.ops.object.material_slot_assign()
        bpy.ops.object.mode_set(mode='OBJECT')

        for c in range(8):
            bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=((-4, -8)[c%2], sd*1.025, 0.0), rotation=(0.0, 0.0, 0.0))
            txt = bpy.context.active_object
            txt.scale = (10, 10, 10)
            txt.data.extrude = 0.1
            txt.data.body = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')[c]
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.material_slot_add()
            txt.material_slots[0].material = bpy.data.materials['SPBase']
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            txt.rotation_euler=(0, 0, -c*pi*0.25)
            ordinals.append(txt)

        for o in ordinals:
            o.select = True
        spathob.select = True
        bpy.context.scene.objects.active = spathob
        bpy.ops.object.join()

        for ob in (spathob, sunob):
            spathob.cycles_visibility.diffuse = False
            spathob.cycles_visibility.shadow = False
            spathob.cycles_visibility.glossy = False
            spathob.cycles_visibility.transmission = False

        if cyfc1 not in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(cyfc1)
        bpy.ops.view3d.spnumdisplay('INVOKE_DEFAULT')
        return {'FINISHED'}

class VIEW3D_OT_SPNumDisplay(bpy.types.Operator):
    '''Display results legend and stats in the 3D View'''
    bl_idname = "view3d.spnumdisplay"
    bl_label = "Point numbers"
    bl_description = "Display the times and solstices on the sunpath"
    bl_register = True
    bl_undo = True

    def modal(self, context, event):
        context.area.tag_redraw()
        if context.scene.vi_display == 0 or not context.scene.sp_disp_panel:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_spnum, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[context.scene.restree].nodes[context.scene.resnode]
        self._handle_spnum = bpy.types.SpaceView3D.draw_handler_add(spnumdisplay, (self, context, simnode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        context.scene.vi_display = 1
        return {'RUNNING_MODAL'}

class NODE_OT_WindRose(bpy.types.Operator):
    bl_idname = "node.windrose"
    bl_label = "Wind Rose"
    bl_description = "Create a Wind Rose"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        if mp == 1:
            simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
            locnode = simnode.inputs[0].links[0].from_node
            scene, scene.resnode, scene.restree = context.scene, simnode.name, self.nodeid.split('@')[1]
            scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 0, 0, 0, 0, 1
    
            with open(locnode.weather, "r") as epwfile:
                if locnode.startmonth > locnode.endmonth:
                    self.report({'ERROR'},"Start month is later than end month")
                    return
                else:
                    wvals = [line.split(",")[20:22] for l, line in enumerate(epwfile.readlines()) if l > 7 and locnode.startmonth <= int(line.split(",")[1]) < locnode.endmonth]
                    simnode['maxres'], simnode['minres'],  simnode['avres']= max([float(w[1]) for w in wvals]), min([float(w[1]) for w in wvals]), sum([float(w[1]) for w in wvals])/len(wvals)
    
            awd, aws, ax = [float(val[0]) for val in wvals], [float(val[1]) for val in wvals], wr_axes()
            binvals = arange(0,int(ceil(max(aws))),2)
            simnode['nbins'] = len(binvals)
    
            if simnode.wrtype == '0':
                ax.bar(awd, aws, bins=binvals, normed=True, opening=0.8, edgecolor='white')
            if simnode.wrtype == '1':
                ax.box(awd, aws, bins=binvals, normed=True)
            if simnode.wrtype == '2':
                ax.contourf(awd, aws, bins=binvals, normed=True, cmap=cm.hot)
            if simnode.wrtype == '3':
                ax.contourf(awd, aws, bins=binvals, normed=True, cmap=cm.hot)
                ax.contour(awd, aws, bins=binvals, normed=True, colors='black')
            if simnode.wrtype == '4':
                ax.contour(awd, aws, bins=binvals, normed=True, cmap=cm.hot)
    
            if locnode.newdir:
                plt.savefig(locnode.newdir+'/disp_wind.png', dpi = (300), transparent=False)
                plt.savefig(locnode.newdir+'/disp_wind.svg')
            else:
                self.report({'ERROR'},"No project directory. Save the Blender file and recreate the VI Location node.")
                return {'CANCELLED'}
    
            if 'disp_wind.png' not in [im.name for im in bpy.data.images]:
                bpy.data.images.load(locnode.newdir+'/disp_wind.png')
            else:
                bpy.data.images['disp_wind.png'].filepath = locnode.newdir+'/disp_wind.png'
                bpy.data.images['disp_wind.png'].reload()
    
            if 'Wind_Plane' not in [ob.get('VIType') for ob in bpy.context.scene.objects]:
                bpy.ops.mesh.primitive_plane_add(enter_editmode=False, location=(0.0, 0.0, 0.0))
                bpy.context.active_object['VIType'] = 'Wind_Plane'
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
                wind_mat.use_transparency = False
                wind_mat.transparency_method = 'Z_TRANSPARENCY'
                wind_mat.alpha = 0.0
            bpy.ops.view3d.wrlegdisplay('INVOKE_DEFAULT')
            return {'FINISHED'}
        else:
            return {'FINISHED'}

class VIEW3D_OT_WRLegDisplay(bpy.types.Operator):
    '''Display results legend and stats in the 3D View'''
    bl_idname = "view3d.wrlegdisplay"
    bl_label = "Wind rose legend"
    bl_description = "Display Wind Rose legend"
    bl_register = True
    bl_undo = True

    def modal(self, context, event):
        context.area.tag_redraw()
        if context.scene.vi_display == 0 or context.scene.wr_disp_panel != 1:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_spnum, 'WINDOW')
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        simnode = bpy.data.node_groups[context.scene.restree].nodes[context.scene.resnode]
        self._handle_spnum = bpy.types.SpaceView3D.draw_handler_add(viwr_legend, (self, context, simnode), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class NODE_OT_Shadow(bpy.types.Operator):
    bl_idname = "node.shad"
    bl_label = "Shadow Study"
    bl_description = "Undertake a shadow study"
    bl_register = True
    bl_undo = True

    nodeid = bpy.props.StringProperty()

    def invoke(self, context, event):
        scene = context.scene
        scene.restree = self.nodeid.split('@')[1]
        scene.vi_display, scene.sp_disp_panel, scene.li_disp_panel, scene.lic_disp_panel, scene.en_disp_panel, scene.ss_disp_panel, scene.wr_disp_panel = 1, 0, 0, 0, 0, 1, 0
        clearscene(scene, self)
        simnode = bpy.data.node_groups[self.nodeid.split('@')[1]].nodes[self.nodeid.split('@')[0]]
        (scene.fs, scene.fe) = (scene.frame_current, scene.frame_current) if simnode.animmenu == 'Static' else (scene.frame_start, scene.frame_end)

        if simnode.starthour > simnode.endhour:
            self.report({'ERROR'},"End hour is before start hour.")
            return{'FINISHED'}
        scene.resnode = simnode.name
        direcs, obcalclist = [], []
        simnode['Animation'] = simnode.animmenu
        if simnode['Animation'] == 'Static':
            scmaxres, scminres, scavres, scene.fs = [0], [100], [0], scene.frame_current
        else:
            scmaxres = [0 for f in range(scene.frame_end - scene.frame_start + 1)]
            scminres = [100 for f in range(scene.frame_end - scene.frame_start + 1)]
            scavres = [0 for f in range(scene.frame_end - scene.frame_start + 1)]

        fdiff =  1 if simnode['Animation'] == 'Static' else scene.frame_end - scene.frame_start + 1
        locnode = simnode.inputs[0].links[0].from_node
        latilongi(scene, locnode)
        time = datetime.datetime(datetime.datetime.now().year, locnode.startmonth, 1, simnode.starthour - 1)
        y =  datetime.datetime.now().year if locnode.endmonth >= locnode.startmonth else datetime.datetime.now().year + 1
        endtime = datetime.datetime(y, locnode.endmonth, (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[locnode.endmonth - 1], simnode.endhour - 1)
        interval = datetime.timedelta(hours = modf(simnode.interval)[0], minutes = 60 * modf(simnode.interval)[1])
        while time <= endtime:
            if simnode.starthour <= time.hour <= simnode.endhour:
                beta, phi = solarPosition(time.timetuple().tm_yday, time.hour+time.minute/60, scene.latitude, scene.longitude)[2:]
                if beta > 0:
                    direcs.append(mathutils.Vector((-sin(phi), -cos(phi), tan(beta))))
            time += interval

        for ob in [ob for ob in scene.objects if ob.type == 'MESH' and not ob.hide]:
            obavres, shadfaces, shadcentres = [0] * (fdiff), [[] for f in range(fdiff)], [[] for f in range(fdiff)]
            [obsumarea, obmaxres, obminres] = [[0 for f in range(fdiff)] for x in range(3)]
            if len([mat for mat in ob.data.materials if mat.vi_shadow]) > 0:
                obcalclist.append(ob)
                scene.objects.active, ob.licalc = ob, 1
                obm = ob.matrix_world
                ob['cfaces'], ob['cverts'] = [face.index for face in ob.data.polygons if ob.data.materials[face.material_index].vi_shadow], []

                while ob.data.vertex_colors:
                    bpy.ops.mesh.vertex_color_remove()
                for frame in range(scene.fs, scene.fe + 1):
                    scene.frame_set(frame)
                    findex = frame - scene.fs
#                    if '{}'.format(frame) not in [vc.name for vc in ob.data.vertex_colors]:
                    bpy.ops.mesh.vertex_color_add()
                    ob.data.vertex_colors[-1].name = '{}'.format(frame)
                    vertexColor = ob.data.vertex_colors[-1]
                    obsumarea[findex] = sum([face.area for face in ob.data.polygons if ob.data.materials[face.material_index].vi_shadow])

                    shadfaces = [face for face in ob.data.polygons if ob.data.materials[face.material_index].vi_shadow]
                    shadcentres[findex] = [[obm*mathutils.Vector((face.center)) + 0.05*face.normal, obm*mathutils.Vector((face.center)), 1] for face in shadfaces]
                    for fa, face in enumerate(shadfaces):
                        for li in face.loop_indices:
                            vertexColor.data[li].color = (1, 1, 1)
                        for direc in direcs:
                            if bpy.data.scenes[0].ray_cast(shadcentres[findex][fa][0], shadcentres[findex][fa][1] + 10000*direc)[0]:
                                shadcentres[findex][fa][2] -= 1/(len(direcs))
                        if shadcentres[findex][fa][2] < 1:
                            for li in face.loop_indices:
                                vertexColor.data[li].color = [shadcentres[findex][fa][2]]*3

                        obavres[findex] += face.area * 100 * (shadcentres[findex][fa][2])/obsumarea[findex]
                        obmaxres[findex] = 100* (max([sh[2] for sh in shadcentres[findex]]))
                        obminres[findex] = 100* (min([sh[2] for sh in shadcentres[findex]]))

                    scmaxres[findex] = obmaxres[findex] if obmaxres[findex] > scmaxres[findex] else scmaxres[findex]
                    scminres[findex] = obminres[findex] if obminres[findex] < scminres[findex] else scminres[findex]
                    scavres[findex] += obavres[findex]

                ob['omax'] = {str(f):obmaxres[f - scene.fs] for f in framerange(scene, simnode.animmenu)}
                ob['omin'] = {str(f):obminres[f - scene.fs] for f in framerange(scene, simnode.animmenu)}
                ob['oave'] = {str(f):obavres[f - scene.fs] for f in framerange(scene, simnode.animmenu)}
                ob['oreslist'] = {str(f):[sh[2] for sh in shadcentres[f - scene.fs]] for f in framerange(scene, simnode.animmenu)}
            
            else:
               ob.licalc = 0
        vcframe('', scene, obcalclist, simnode.animmenu)
        try:
            simnode['maxres'], simnode['minres'], simnode['avres'] = scmaxres, scminres, [scavres[f]/len([ob for ob in scene.objects if ob.licalc]) for f in range(fdiff)]
        except ZeroDivisionError:
            self.report({'ERROR'},"No objects have a VI Shadow material attached.")

        scene.frame_set(scene.fs)
        if simnode.bl_label[0] == '*':
            simnode.bl_label = simnode.bl_label[1:]
        return {'FINISHED'}
