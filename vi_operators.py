import bpy, bpy_extras
import bpy_extras.io_utils as io_utils
from . import livi_export

class NODE_OT_preview(bpy.types.Operator):
    bl_idname = "node.preview"
    bl_label = "Radiance Preview"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        return {'FINISHED'}

class NODE_OT_calculate(bpy.types.Operator):
    bl_idname = "node.calculate"
    bl_label = "Radiance Export and Simulation"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        return {'FINISHED'}

class NODE_OT_geoexport(bpy.types.Operator):
    bl_idname = "node.geoexport"
    bl_label = "EnVi geometry export"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        return {'FINISHED'}

class NODE_OT_export(bpy.types.Operator):
    bl_idname = "node.export"
    bl_label = "VI-Suite export"
    nodename = bpy.props.StringProperty()
    
    def execute(self, context):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        node.exported = True
#        lexport
        return {'FINISHED'}        

class NODE_OT_epwselect(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
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
        
class NODE_OT_LiExport(bpy.types.Operator, io_utils.ExportHelper):
    bl_idname = "node.liexport"
    bl_label = "Export"
    bl_description = "Export the scene to the Radiance file format"
    bl_register = True
    bl_undo = True
    
    nodename = bpy.props.StringProperty()
    timetype = bpy.props.StringProperty()
    TZ = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        node = bpy.data.node_groups['VI Network'].nodes[self.nodename]
        node.exported = True
        global lexport
        if bpy.data.filepath:
            self.TZ = node.summer if node.daysav == True else node.stamer
            self.timetype = node.animtype if node.analysismenu != '2' else node.dfanimtype

            if bpy.context.object:
                if bpy.context.object.type == 'MESH' and bpy.context.object.hide == False and bpy.context.object.layers[0] == True:
                    bpy.ops.object.mode_set(mode = 'OBJECT')
            
            if " " not in bpy.data.filepath:
                livi_export.LiVi_e(bpy.data.filepath, node, self)   
                node.disp_leg = False
            else:    
                self.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces")
                return {'FINISHED'}
            return {'FINISHED'}
        else:
            self.report({'ERROR'},"Save the Blender file before exporting")
            return {'FINISHED'} 