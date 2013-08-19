import bpy, bpy_extras, sys, datetime
import bpy_extras.io_utils as io_utils
from collections import OrderedDict
from datetime import date
from datetime import datetime as dt
from . import livi_export
from . import livi_calc
from . import vi_display
from . import envi_export
from . import envi_mat
from . import envi_calc
from . import vi_func
from . import vi_chart

envi_mats = envi_mat.envi_materials()
envi_cons = envi_mat.envi_constructions()

class NODE_OT_GeoExport(bpy.types.Operator):
    bl_idname = "node.geoexport"
    bl_label = "EnVi geometry export"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        return {'FINISHED'}

class NODE_OT_LiGExport(bpy.types.Operator):
    bl_idname = "node.ligexport"
    bl_label = "VI-Suite export"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        livi_export.radgexport(self, node)
        node.exported = True
        node.outputs[0].hide = False
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
    nodename = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import EPW File with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("epw", "EPW", "HDR", "hdr"):
            bpy.data.node_groups['VI Network'].nodes[self.nodename].epwname = self.filepath
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
    nodename = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import HDR image file with FileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("HDR", "hdr"):
            bpy.data.node_groups['VI Network'].nodes[self.nodename].hdrname = self.filepath
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
    nodename = bpy.props.StringProperty()

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Import a Radiance sky file with the fileBrowser", icon='WORLD_DATA')
        row = layout.row()

    def execute(self, context):
        if self.filepath.split(".")[-1] in ("RAD", "rad"):
            bpy.data.node_groups['VI Network'].nodes[self.nodename].skyname = self.filepath
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
    
    nodename = bpy.props.StringProperty()
        
    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        node.resname = ("illumout", "irradout", "dfout")[int(node.analysismenu)]
        node.unit = ("Lux", "W/m"+ u'\u00b2', "DF %")[int(node.analysismenu)]
        node.skynum = int(node.skymenu)
        
        if str(sys.platform) != 'win32':
            node.simalg = (" |  rcalc  -e '$1=47.4*$1+120*$2+11.6*$3' ", " |  rcalc  -e '$1=$1' ", " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)/100' ")[int(node.analysismenu)]
        else:
            node.simalg = (' |  rcalc  -e "$1=47.4*$1+120*$2+11.6*$3" ', ' |  rcalc  -e "$1=$1" ', ' |  rcalc  -e "$1=(47.4*$1+120*$2+11.6*$3)/100" ')[int(node.analysismenu)]
    
        if bpy.data.filepath:
            node.TZ = node.summer if node.daysav == True else node.stamer

            if bpy.context.object:
                if bpy.context.object.type == 'MESH' and bpy.context.object.hide == False and bpy.context.object.layers[0] == True:
                    bpy.ops.object.mode_set(mode = 'OBJECT')
            
            if " " not in bpy.data.filepath:
                if node.inputs['Geometry in'].is_linked:
                    livi_export.radcexport(self, node)   
                    node.disp_leg = False
                    node.exported = True
                else:
                    self.report({'ERROR'},"No geometry node is linked")
            else:    
                self.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces")
                return {'FINISHED'}
            return {'FINISHED'}
        else:
            self.report({'ERROR'},"Save the Blender file before exporting")
            return {'FINISHED'} 

class NODE_OT_RadPreview(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.radpreview"
    bl_label = "Preview"
    bl_description = "Prevew the scene with Radiance"
    bl_register = True
    bl_undo = True
    
    nodename = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        geonode = node.inputs[0].links[0].from_node
        livi_calc.rad_prev(self, node, geonode)
        return {'FINISHED'}
        
class NODE_OT_Calculate(bpy.types.Operator):
    bl_idname = "node.calculate"
    bl_label = "Radiance Export and Simulation"
    
    nodename = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        geonode = node.inputs[0].links[0].from_node
        livi_calc.li_calc(self, node, geonode)
        context.scene.li_disp_panel = 1
        context.scene.resnode = self.nodename
        return {'FINISHED'}
        
class VIEW3D_OT_LiDisplay(bpy.types.Operator):
    bl_idname = "view3d.lidisplay"
    bl_label = "Radiance Results Display"
    bl_description = "Display the results on the sensor surfaces"
    bl_register = True
    bl_undo = True
    nodename = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[bpy.context.scene.resnode]
        geonode = node.inputs[0].links[0].from_node
        try:
            vi_display.li_display(node, geonode)
            bpy.ops.view3d.linumdisplay()
        except:
            self.report({'ERROR'},"No results available for display. Try re-running the calculation.")
            raise
        return {'FINISHED'}
    
class VIEW3D_OT_LiNumDisplay(bpy.types.Operator):
    '''Display results legend and stats in the 3D View'''
    bl_idname = "view3d.linumdisplay"
    bl_label = "Display results legend and stats in the 3D View"
    bl_options = {'REGISTER'}
    
    def modal(self, context, event):
        context.area.tag_redraw()
        if context.scene.li_display == 0:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_leg, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_stat, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_pointres, 'WINDOW')
#            context.scene.rp_display = False
            return {'CANCELLED'}
        return {'PASS_THROUGH'} 
    
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            node = bpy.data.node_groups['VI Network'].nodes[bpy.context.scene.resnode]
            geonode = node.inputs[0].links[0].from_node
            self._handle_leg = bpy.types.SpaceView3D.draw_handler_add(vi_display.li3D_legend, (self, context, node), 'WINDOW', 'POST_PIXEL')
            self._handle_stat = bpy.types.SpaceView3D.draw_handler_add(vi_display.lires_stat, (self, context, node), 'WINDOW', 'POST_PIXEL')
            self._handle_pointres = bpy.types.SpaceView3D.draw_handler_add(vi_display.linumdisplay, (self, context, node, geonode), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            context.scene.li_display = 1
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
        envi_export.pregeo()
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
            
                envi_export.enpolymatexport(self, node, envi_mats, envi_cons)    
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
        envi_calc.envi_sim(self, node) 
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
        vi_chart.chart_disp(self, node, innodes, Sdate, Edate) 
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
        vi_func.processf(self, node) 
        if not node.outputs:
            node.outputs.new('ViEnROut', 'Results out')
        return {'FINISHED'}