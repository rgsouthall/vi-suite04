import bpy

#from . import vi_operators
#scene = bpy.context.scene

#class ViNodeGen(bpy.types.Operator):
#    '''Initial node network registration and creation'''
#    bl_idname = "scene.ving"
#    bl_label = "Generate VI Nodes"
#    bl_options = {'REGISTER', 'UNDO'}
#    bl_register = True
#    bl_undo = True
#    
#    def invoke(self, context, event):
#        vi_node.vinodegen()
#        return{'FINISHED'}
from .envi_mat import *
envi_mats = envi_materials()
envi_cons = envi_constructions()
    
class Vi3DPanel(bpy.types.Panel):
    '''VI-Suite 3D view panel'''
    bl_label = "VI-Suite"    
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"    

    def draw(self, context):
        view = context.space_data
        scene = context.scene
          
        if scene.li_disp_panel == 1:
            layout = self.layout
            row = layout.row()
            row.prop(view, "show_only_render")
            row = layout.row()
            row.prop(scene, "li_disp_3d")
            if int(context.scene.li_disp_3d) == 1:
                row.prop(scene, "li_disp_3dlevel")
            row = layout.row()
            row.operator("view3d.lidisplay", text="Radiance Display")
#            try:
#                if lexport.node.rp_display == False:
#                    pass
#                else:
            if context.mode == "OBJECT":
                row = layout.row()
                row.label(text="{:-<48}".format("Point visualisation "))
                row = layout.row()
                row.label(text = "Enable:")
                row.prop(scene, "li_display_rp")
                row = layout.row()
                row.label(text = "Selected only:")
                row.prop(scene, "li_display_sel_only")
                row = layout.row()
                row.label(text = "Font size:")
                row.prop(scene, "li_display_rp_fs")
                row = layout.row()
                row.label(text="{:-<60}".format(""))
        if scene.li_disp_panel == 2:
            pass
#            except:
#                pass

class RadMatPanel(bpy.types.Panel):
    bl_label = "LiVi Radiance material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    @classmethod 
    def poll(cls, context): 
        return context.material 

    def draw(self, context):
        cm = context.material
        layout = self.layout
        row = layout.row()
        row.label('Radiance type:')
        if cm.use_shadeless == True:
            row.label('Shadeless')
        elif cm.emit > 0:
            row.label('Emission')
            row = layout.row()
            row.label('RGB emission:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(cm.emit * cm.diffuse_color[0], cm.emit * cm.diffuse_color[1], cm.emit * cm.diffuse_color[2]))
        elif cm.raytrace_mirror.use == True and cm.raytrace_mirror.reflect_factor > 0.99:
            row.label('Mirror')
            row = layout.row()
            row.label('RGB refelectance:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.mirror_color))
        elif cm.use_transparency == True and cm.transparency_method == 'RAYTRACE' and cm.alpha < 1.0 and cm.translucency == 0:
            row.label('Glass')
            row = layout.row()
            row.label('RGB transparency:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format((1.0 - cm.alpha)*cm.diffuse_color[0], (1.0 - cm.alpha)*cm.diffuse_color[1], (1.0 - cm.alpha)*cm.diffuse_color[2]))
            row = layout.row()
            row.label('IOR:')
            row.label('{:.2f}'.format(cm.raytrace_transparency.ior))
        elif cm.use_transparency == True and cm.transparency_method == 'RAYTRACE' and cm.alpha < 1.0 and cm.translucency > 0:
            row.label('Translucent')
            row = layout.row()
            row.label('RGB transmission:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color))
            row = layout.row()
            row.label('Specularity')
            row.label('{:.2f}'.format(cm.specular_intensity))
            row = layout.row()
            row.label('Roughness:') 
            row.label('{:.2f}'.format(1.0 - cm.specular_hardness/511.0))
            row = layout.row()
            row.label('Transmissivity')
            row.label('{:.2f}'.format(1.0 - cm.alpha))
            row = layout.row()
            row.label('Transmitted Specular')
            row.label('{:.2f}'.format(1.0 - cm.translucency))
        elif cm.raytrace_mirror.use == True and cm.raytrace_mirror.reflect_factor <= 0.99:
            row.label('Metal')
            row = layout.row()
            row.label('RGB refelectance:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color))
            row = layout.row()
            row.label('Specularity:')
            row.label('{:.2f}'.format(cm.specular_intensity))
            row = layout.row()
            row.label('Roughness:')
            row.label('{:.2f}'.format(1.0-cm.specular_hardness/511.0))
        else:
            row.label('Plastic')
            row = layout.row()
            row.label('RGB refelectance:')
            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color))
            row = layout.row()
            row.label('Specularity:')
            row.label('{:.2f}'.format(cm.specular_intensity))
            row = layout.row()
            row.label('Roughness:')
            row.label('{:.2f}'.format(1.0-cm.specular_hardness/511.0))
            
     
class IESPanel(bpy.types.Panel):
    bl_label = "LiVi IES file"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        if context.lamp or 'lightarray' in context.object.name:
            return True

    def draw(self, context):
        layout = self.layout
        lamp = bpy.context.active_object
        row = layout.row()
        row.operator("livi.ies_select") 
        row.prop(lamp, "ies_name")
        row = layout.row()
        row.label('IES Dimension:')
        row.prop(lamp, "ies_unit")
        row = layout.row()
        row.label('IES Strength:')
        row.prop(lamp, "ies_strength")
        row = layout.row()
        row.prop(lamp, "ies_colour")
        
class EnZonePanel(bpy.types.Panel):
    bl_label = "EnVi Zone Definition"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        if context.object and context.object.type == 'MESH':
            return len(context.object.data.materials)
    
    def draw(self, context):
        object = bpy.context.active_object
        layout = self.layout
        row = layout.row()        
        row.prop(object, "envi_type")
        row = layout.row()
        if object.envi_type == '1':
            row = layout.row()
            row.label('Heating:')
            row.prop(object, "envi_heats1c")
            row = layout.row()
            row.prop(object, "envi_heats1")
            if object.envi_heats1 == True:
                row.prop(object, "envi_heats1d")
                row = layout.row()
                row.prop(object, "envi_heats1p1st")
                row.prop(object, "envi_heats1p1et")
                row.prop(object, "envi_heats1sp1")
                row = layout.row()
                row.prop(object, "envi_heats1p2st")
                row.prop(object, "envi_heats1p2et")
                row.prop(object, "envi_heats1sp2")
                row = layout.row()
                row.prop(object, "envi_heats1p3st")
                row.prop(object, "envi_heats1p3et")
                row.prop(object, "envi_heats1sp3")
                
                if object.envi_heats1d != "0":
                    row = layout.row()
                    row.prop(object, "envi_heats2")
                    if object.envi_heats2 == True:
                        if object.envi_heats1d == "1":
                            row.prop(object, "envi_heats2dwe")
                        else:
                            row.prop(object, "envi_heats2dwd")
                        row = layout.row()
                        row.prop(object, "envi_heats2p1st")
                        row.prop(object, "envi_heats2p1et")
                        row.prop(object, "envi_heats2sp1")
                        row = layout.row()
                        row.prop(object, "envi_heats2p2st")
                        row.prop(object, "envi_heats2p2et")
                        row.prop(object, "envi_heats2sp2")
                        row = layout.row()
                        row.prop(object, "envi_heats2p3st")
                        row.prop(object, "envi_heats2p3et")
                        row.prop(object, "envi_heats2sp3")
                        
            row = layout.row()
            row.label('-------------------------------------')
            
            row = layout.row()
            row.label('Cooling:')
            row.prop(object, "envi_cools1c")
            row = layout.row()
            row.prop(object, "envi_cools1")

            if object.envi_cools1 == True:
                row.prop(object, "envi_cools1d")
                row = layout.row()
                row.prop(object, "envi_cools1p1st")
                row.prop(object, "envi_cools1p1et")
                row.prop(object, "envi_cools1sp1")
                row = layout.row()
                row.prop(object, "envi_cools1p2st")
                row.prop(object, "envi_cools1p2et")
                row.prop(object, "envi_cools1sp2")
                row = layout.row()
                row.prop(object, "envi_cools1p3st")
                row.prop(object, "envi_cools1p3et")
                row.prop(object, "envi_cools1sp3")

                if object.envi_cools1d != "0":
                    row = layout.row()
                    row.prop(object, "envi_cools2")
                    if object.envi_cools2 == True:
                        if object.envi_cools1d == "1":
                            row.prop(object, "envi_cools2dwe")
                        else:
                            row.prop(object, "envi_cools2dwd")
                        row = layout.row()
                        row.prop(object, "envi_cools2p1st")
                        row.prop(object, "envi_cools2p1et")
                        row.prop(object, "envi_cools2sp1")
                        row = layout.row()
                        row.prop(object, "envi_cools2p2st")
                        row.prop(object, "envi_cools2p2et")
                        row.prop(object, "envi_cools2sp2")
                        row = layout.row()
                        row.prop(object, "envi_cools2p3st")
                        row.prop(object, "envi_cools2p3et")
                        row.prop(object, "envi_cools2sp3")
                    
            row = layout.row()
            row.label('------------------------------------------------------------')
            
            row = layout.row()
            row.label('Occupancy:')
            row.prop(object, "envi_occtype")
            if object.envi_occtype != "0":
                row.prop(object, "envi_occsmax")
                row.prop(object, "envi_occs1d")
                row = layout.row()
                row.prop(object, "envi_occs1p1st")
                row.prop(object, "envi_occs1p1et")
                row.prop(object, "envi_occs1p1level")
                row = layout.row()
                row.prop(object, "envi_occs1p2st")
                row.prop(object, "envi_occs1p2et")
                row.prop(object, "envi_occs1p2level")
                row = layout.row()
                row.prop(object, "envi_occs1p3st")
                row.prop(object, "envi_occs1p3et")
                row.prop(object, "envi_occs1p3level")
                row = layout.row()
                row.prop(object, "envi_occs1watts")
                
                row = layout.row()
                if object.envi_occs1d != "0":
                    row.prop(object, "envi_occs2")
                    if object.envi_occs2 == True:
                        if object.envi_occs1d == "1":
                            row.prop(object, "envi_occs2dwe")
                        else:
                            row.prop(object, "envi_occs2dwd")

                        row = layout.row()
                        row.prop(object, "envi_occs2p1st")
                        row.prop(object, "envi_occs2p1et")
                        row.prop(object, "envi_occs2p1level")
                        row = layout.row()
                        row.prop(object, "envi_occs2p2st")
                        row.prop(object, "envi_occs2p2et")
                        row.prop(object, "envi_occs2p2level")
                        row = layout.row()
                        row.prop(object, "envi_occs2p3st")
                        row.prop(object, "envi_occs2p3et")
                        row.prop(object, "envi_occs2p3level")
                        row = layout.row()
                        row.prop(object, "envi_occs2watts")
            
            row = layout.row()
            row.label('---------------------------------------------------------')
            
            row = layout.row()
            row.label('Infiltration:')
            if object.envi_occtype != "0":
                row.prop(object, "envi_occinftype")
            else:
                row.prop(object, "envi_inftype")
            row.prop(object, "envi_inflevel")
            if object.envi_occinftype == "1" and object.envi_occtype != "0":
                row = layout.row()
                row.label('Base Infiltration:')
                row.prop(object, "envi_infbasetype")
                row.prop(object, "envi_infbaselevel")
                
                        
class EnMatPanel(bpy.types.Panel):
    bl_label = "EnVi Construction"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    @classmethod
    def poll(cls, context):
        if context.object and context.object.type == 'MESH':
            return len(context.object.data.materials)
   
    def draw(self, context):
        if bpy.context.active_object.active_material == None:
            return
        else:
            material = bpy.context.active_object.active_material
        layout = self.layout
        row = layout.row()
        row.label("Construction Type:")
        row.prop(material, "envi_con_type")
        row = layout.row()
        if material.envi_con_type not in ("Aperture", "Shading", "None"):
            row = layout.row()
            row.prop(material, "envi_boundary")
            row = layout.row()
            row.label("Construction Make-up:")
            row.prop(material, "envi_con_makeup")

            if material.envi_con_makeup == '1':
                row = layout.row()
                row.label("Outside layer:")
                row.prop(material, "envi_layero")
                row = layout.row()
                if material.envi_layero == '1':
                    row = layout.row()
                    if material.envi_con_type == "Window":
                        row.label("Glass Type:")
                        row.prop(material, ("envi_export_glasslist_lo"))
                    elif material.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                        row.label("Outer layer type:")
                        row.prop(material, "envi_layeroto")
                        row = layout.row()
                        row.label("Outer layer material:")
                        row.prop(material, ("envi_export_bricklist_lo", "envi_export_concretelist_lo", "envi_export_metallist_lo", "envi_export_stonelist_lo", "envi_export_woodlist_lo", "envi_export_gaslist_lo", "envi_export_insulationlist_lo")[int(material.envi_layeroto)])
                        row = layout.row()
                        row.prop(material, "envi_export_lo_thi")
    
                elif material.envi_layero == '2' and material.envi_con_type != 'Window':
                    row.prop(material, "envi_export_lo_name")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_thi")
                    row.prop(material, "envi_export_lo_tc")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_rho")
                    row.prop(material, "envi_export_lo_shc")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_tab")
                    row.prop(material, "envi_export_lo_sab")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_vab")
                    row.prop(material, "envi_export_lo_rough")
                    
                elif material.envi_layero == '2' and material.envi_con_type == 'Window':
                    row.prop(material, "envi_export_lo_name")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_thi")
                    row.prop(material, "envi_export_lo_tc")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_odt")
                    row.prop(material, "envi_export_lo_sds")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_stn")
                    row.prop(material, "envi_export_lo_fsn")
                    row.prop(material, "envi_export_lo_bsn")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_vtn")
                    row.prop(material, "envi_export_lo_fvrn")
                    row.prop(material, "envi_export_lo_bvrn")
                    row = layout.row()
                    row.prop(material, "envi_export_lo_itn")
                    row.prop(material, "envi_export_lo_fie")
                    row.prop(material, "envi_export_lo_bie")
                        
                if material.envi_layero != '0':
                    row = layout.row()
                    row.label("2nd layer:")
                    row.prop(material, "envi_layer1")
                    row = layout.row()
                    if material.envi_layer1 == '1':
                        if material.envi_con_type == "Window":
                            row.label("Gas Type:")
                            row.prop(material, ("envi_export_wgaslist_l1"))
                            row.prop(material, "envi_export_l1_thi")
                        elif material.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                            row.label("2nd layer type:")
                            row.prop(material, "envi_layer1to")
                            row = layout.row()
                            row.label("2nd layer material:")
                            row.prop(material, ("envi_export_bricklist_l1", "envi_export_concretelist_l1", "envi_export_metallist_l1", "envi_export_stonelist_l1", "envi_export_woodlist_l1", "envi_export_gaslist_l1", "envi_export_insulationlist_l1")[int(material.envi_layer1to)])
                            row = layout.row()
                            row.prop(material, "envi_export_l1_thi")
                    elif material.envi_layer1 == '2' and material.envi_con_type != 'Window':
                        row.prop(material, "envi_export_l1_name")
                        row = layout.row()
                        row.prop(material, "envi_export_l1_thi")
                        row.prop(material, "envi_export_l1_tc")
                        row = layout.row()
                        row.prop(material, "envi_export_l1_rho")
                        row.prop(material, "envi_export_l1_shc")
                        row = layout.row()
                        row.prop(material, "envi_export_l1_tab")
                        row.prop(material, "envi_export_l1_sab")
                        row = layout.row()
                        row.prop(material, "envi_export_l1_vab")
                        row.prop(material, "envi_export_l1_rough")
                    elif material.envi_layer1 == '2' and material.envi_con_type == 'Window':
                        row.prop(material, "envi_export_l1_name")
                        row = layout.row()
                        row.label("Gas Type:")
                        row.prop(material, "envi_export_wgaslist_l1")
                        row.prop(material, "envi_export_l1_thi")
                            
                    if material.envi_layer1 != '0':
                        row = layout.row()
                        row.label("3rd layer:")
                        row.prop(material, "envi_layer2")
                        row = layout.row()
                        if material.envi_layer2 == '1':
                            if material.envi_con_type == "Window":
                                row.label("Glass Type:")
                                row.prop(material, ("envi_export_glasslist_l2"))
                            elif material.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                row.label("3rd layer type:")
                                row.prop(material, "envi_layer2to")
                                row = layout.row()
                                row.label("3rd layer material:")
                                row.prop(material, ("envi_export_bricklist_l2", "envi_export_concretelist_l2", "envi_export_metallist_l2", "envi_export_stonelist_l2", "envi_export_woodlist_l2", "envi_export_gaslist_l2", "envi_export_insulationlist_l2")[int(material.envi_layer2to)])
                                row = layout.row()
                                row.prop(material, "envi_export_l2_thi")
                        
                        elif material.envi_layer2 == '2'and material.envi_con_type != 'Window':
                            row.prop(material, "envi_export_l2_name")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_thi")
                            row.prop(material, "envi_export_l2_tc")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_rho")
                            row.prop(material, "envi_export_l2_shc")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_tab")
                            row.prop(material, "envi_export_l2_sab")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_vab")
                            row.prop(material, "envi_export_l2_rough")
                            
                        elif material.envi_layer2 == '2' and material.envi_con_type == 'Window':
                            row.prop(material, "envi_export_l2_name")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_thi")
                            row.prop(material, "envi_export_l2_tc")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_odt")
                            row.prop(material, "envi_export_l2_sds")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_stn")
                            row.prop(material, "envi_export_l2_fsn")
                            row.prop(material, "envi_export_l2_bsn")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_vtn")
                            row.prop(material, "envi_export_l2_fvrn")
                            row.prop(material, "envi_export_l2_bvrn")
                            row = layout.row()
                            row.prop(material, "envi_export_l2_itn")
                            row.prop(material, "envi_export_l2_fie")
                            row.prop(material, "envi_export_l2_bie")
                        
                        if material.envi_layer2 != '0':
                            row = layout.row()
                            row.label("4th layer:")
                            row.prop(material, "envi_layer3")
                            row = layout.row()
                            if material.envi_layer3 == '1':
                                if material.envi_con_type == "Window":
                                    row.label("Gas Type:")
                                    row.prop(material, ("envi_export_wgaslist_l3"))
                                    row.prop(material, "envi_export_l3_thi")
                                elif material.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                    row.label("4th layer type:")
                                    row.prop(material, "envi_layer3to")
                                    row = layout.row()
                                    row.label("4th layer material:")
                                    row.prop(material, ("envi_export_bricklist_l3", "envi_export_concretelist_l3", "envi_export_metallist_l3", "envi_export_stonelist_l3", "envi_export_woodlist_l3", "envi_export_gaslist_l3", "envi_export_insulationlist_l3")[int(material.envi_layer3to)])
                                    row = layout.row()
                                    row.prop(material, "envi_export_l3_thi")
                                
                            elif material.envi_layer3 == '2'and material.envi_con_type != 'Window':
                                row.prop(material, "envi_export_l3_name")
                                row = layout.row()
                                row.prop(material, "envi_export_l3_thi")
                                row.prop(material, "envi_export_l3_tc")
                                row = layout.row()
                                row.prop(material, "envi_export_l3_rho")
                                row.prop(material, "envi_export_l3_shc")
                                row = layout.row()
                                row.prop(material, "envi_export_l3_tab")
                                row.prop(material, "envi_export_l3_sab")
                                row = layout.row()
                                row.prop(material, "envi_export_l3_vab")
                                row.prop(material, "envi_export_l3_rough")
                            
                            elif material.envi_layer3 == '2' and material.envi_con_type == 'Window':
                                row.prop(material, "envi_export_l1_name")
                                row = layout.row()
                                row.label("Gas Type:")
                                row.prop(material, "envi_export_wgaslist_l3")
                                row.prop(material, "envi_export_l3_thi")
                                
                            if material.envi_layer3 != '0':
                                row = layout.row()
                                row.label("5th layer:")
                                row.prop(material, "envi_layer4")
                                row = layout.row()
                                if material.envi_layer4 == '1':
                                    if material.envi_con_type == "Window":
                                        row.label("Glass Type:")
                                        row.prop(material, ("envi_export_glasslist_l4"))
                                    elif material.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                        row.label("5th layer type:")
                                        row.prop(material, "envi_layer4to")
                                        row = layout.row()
                                        row.label("5th layer material:")
                                        row.prop(material, ("envi_export_bricklist_l4", "envi_export_concretelist_l4", "envi_export_metallist_l4", "envi_export_stonelist_l4", "envi_export_woodlist_l4", "envi_export_gaslist_l4", "envi_export_insulationlist_l4")[int(material.envi_layer4to)])
                                        row = layout.row()
                                        row.prop(material, "envi_export_l4_thi")
                                
                                elif material.envi_layer4 == '2' and material.envi_con_type != 'Window':
                                    row.prop(material, "envi_export_l4_name")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_thi")
                                    row.prop(material, "envi_export_l4_tc")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_rho")
                                    row.prop(material, "envi_export_l4_shc")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_tab")
                                    row.prop(material, "envi_export_l4_sab")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_vab")
                                    row.prop(material, "envi_export_l4_rough")
                                
                                elif material.envi_layer4 == '2' and material.envi_con_type == 'Window':
                                    row.prop(material, "envi_export_l4_name")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_thi")
                                    row.prop(material, "envi_export_l4_tc")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_odt")
                                    row.prop(material, "envi_export_l4_sds")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_stn")
                                    row.prop(material, "envi_export_l4_fsn")
                                    row.prop(material, "envi_export_l4_bsn")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_vtn")
                                    row.prop(material, "envi_export_l4_fvrn")
                                    row.prop(material, "envi_export_l4_bvrn")
                                    row = layout.row()
                                    row.prop(material, "envi_export_l4_itn")
                                    row.prop(material, "envi_export_l4_fie")
                                    row.prop(material, "envi_export_l4_bie")

        
            elif material.envi_con_makeup == '0':
                thicklist = ("envi_export_lo_thi", "envi_export_l1_thi", "envi_export_l2_thi", "envi_export_l3_thi", "envi_export_l4_thi")
                row = layout.row()
                if material.envi_con_type == 'Wall':
                    row.prop(material, "envi_export_wallconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.wall_con[material.envi_export_wallconlist]):
                        row.label(text = layername)
                        if layername not in envi_mats.gas_dat:
                            row.prop(material, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()
                elif material.envi_con_type == 'Floor':
                    row.prop(material, "envi_export_floorconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.floor_con[material.envi_export_floorconlist]):
                        row.label(text = layername)
                        if layername not in envi_mats.gas_dat:
                            row.prop(material, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()
                
                elif material.envi_con_type == 'Roof':
                    row.prop(material, "envi_export_roofconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.roof_con[material.envi_export_roofconlist]):
                        row.label(text = layername)
                        if layername not in envi_mats.gas_dat:
                            row.prop(material, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()
                
                elif material.envi_con_type == 'Door':
                    row.prop(material, "envi_export_doorconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.door_con[material.envi_export_doorconlist]):
                        row.label(text = layername)
                        if layername not in envi_mats.gas_dat:
                            row.prop(material, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()
                
                elif material.envi_con_type == 'Window':
                    row.prop(material, "envi_export_glazeconlist")