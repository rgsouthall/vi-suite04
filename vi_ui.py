import bpy
from .vi_func import radmat

def newrow(layout, s1, root, s2):
    row = layout.row()
    row.label(s1)
    row.prop(root, s2)

from .envi_mat import envi_materials, envi_constructions
envi_mats = envi_materials()
envi_cons = envi_constructions()

class Vi3DPanel(bpy.types.Panel):
    '''VI-Suite 3D view panel'''
    bl_label = "VI-Suite"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        if context.scene.vi_display == 1:
            view = context.space_data
            scene = context.scene
            layout = self.layout

            if scene.wr_disp_panel == 1:
                row = layout.row()
                row.prop(scene, "vi_leg_display")

            if scene.sp_disp_panel == 1:
                for i in (("Day of year", "solday"), ("Hour of year", "solhour"), ("Sunpath scale", "soldistance"), ("Display hours", "hourdisp")):
                    newrow(layout, i[0], scene, i[1])
#                newrow(layout, "Hour of day", scene, "solhour")
#                newrow(layout, "Sunpath scale", scene, "soldistance")
#                newrow(layout, "Display hours", scene, "hourdisp")
                if scene.hourdisp:
                    newrow(layout, "Font size", scene, "vi_display_rp_fs")
                    newrow(layout, "Font colour:", scene, "vi_display_rp_fc")
                    newrow(layout, "Font shadow:", scene, "vi_display_rp_fsh")

            if scene.ss_disp_panel in (1,2) or scene.li_disp_panel in (1,2):
                row = layout.row()
                row.prop(scene, "vi_disp_3d")
                row = layout.row()
                if scene.resnode == 'VI Shadow Study':
                    row.operator("view3d.lidisplay", text="Shadow Display")
                else:
                    row.operator("view3d.lidisplay", text="Radiance Display")

                if scene.ss_disp_panel == 2 or scene.li_disp_panel == 2:
                    row = layout.row()
                    row.prop(view, "show_only_render")
                    row = layout.row()
                    row.prop(scene, "vi_leg_display")

                    if int(context.scene.vi_disp_3d) == 1:
                        newrow(layout, "3D Level", scene, "vi_disp_3dlevel")

                    if context.mode == "OBJECT":
                        row = layout.row()
                        row.label(text="{:-<48}".format("Point visualisation "))
                        newrow(layout, "Enable:", scene, "vi_display_rp")
                        newrow(layout, "Selected only:", scene, "vi_display_sel_only")
                        newrow(layout, "Visible only:", scene, "vi_display_vis_only")
                        newrow(layout, "Font size:", scene, "vi_display_rp_fs")
                        newrow(layout, "Font colour:", scene, "vi_display_rp_fc")
                        newrow(layout, "Font shadow:", scene, "vi_display_rp_fsh")
                        row = layout.row()
                        row.label(text="{:-<60}".format(""))

                    if scene.lic_disp_panel == 1:
                        newrow(layout, "Compliance Panel", scene, "li_compliance")
                        newrow(layout, "Asessment organisation:", scene, "li_assorg")
                        newrow(layout, "Assesment individiual:", scene, "li_assind")
                        newrow(layout, "Job number:", scene, "li_jobno")
                        newrow(layout, "Project name:", scene, "li_projname")


class VIMatPanel(bpy.types.Panel):
    bl_label = "VI-Suite Material Panel"
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
        row.prop(cm, "vi_shadow")
        row = layout.row()
        row.prop(cm, "livi_sense")
        row = layout.row()
        for ng in bpy.data.node_groups:
            if ng.bl_idname == 'ViN':
                if 'LiVi Compliance' in [node.bl_label for node in ng.nodes]:
                    node = [node for node in ng.nodes if node.bl_label == 'LiVi Compliance'][0]
#            row.prop(cm, "livi_compliance")
                    if cm.livi_sense:
                        if node.analysismenu == '0':
                            if node.bambuildmenu == '2':
                                newrow(layout, "Space type:", cm, 'hspacemenu')
                            elif node.bambuildmenu == '3':
                                newrow(layout, "Space type:", cm, 'rspacemenu')
                                if cm.rspacemenu == '2':
                                    row = layout.row()
                                    row.prop(cm, 'gl_roof')
                            elif node.bambuildmenu == '4':
                                newrow(layout, "Space type:", cm, 'respacemenu')
                        elif node.analysismenu == '1':
                            newrow(layout, "Space type:", cm, 'rspacemenu')
                            if cm.rspacemenu == '2':
                                row = layout.row()
                                row.label('Warning: Not an assessable CfSH space')
        row = layout.row()
        row.label('LiVi Radiance type:')
        
        radname, matname, radnum = radmat(cm, context.scene)
        row.label(radname.capitalize())
#        if cm.use_shadeless == True:
#            row.label('Anti-matter')
#        elif cm.emit > 0:
#            row.label('Emission')
#            row = layout.row()
#            row.label('RGB emission:')
#            row.label('({:.2f}, {:.2f}, {:.2f})'.format(cm.emit * cm.diffuse_color[0], cm.emit * cm.diffuse_color[1], cm.emit * cm.diffuse_color[2]))
#        elif cm.raytrace_mirror.use == True and cm.raytrace_mirror.reflect_factor > 0.99:
#            row.label('Mirror')
#            row = layout.row()
#            row.label('RGB refelectance:')
#            row.label('({:.2f}, {:.2f}, {:.2f})'.format(*cm.mirror_color))
#        elif cm.use_transparency == True and cm.transparency_method == 'RAYTRACE' and cm.alpha < 1.0 and cm.translucency == 0:
#            row.label('Glass')
#            row = layout.row()
#            row.label('RGB transparency:')
#            row.label('({:.2f}, {:.2f}, {:.2f})'.format((1.0 - cm.alpha)*cm.diffuse_color[0], (1.0 - cm.alpha)*cm.diffuse_color[1], (1.0 - cm.alpha)*cm.diffuse_color[2]))
#            row = layout.row()
#            row.label('IOR:')
#            row.label('{:.2f}'.format(cm.raytrace_transparency.ior))
#        elif cm.use_transparency == True and cm.transparency_method == 'RAYTRACE' and cm.alpha < 1.0 and cm.translucency > 0:
#            for matprop in ('Translucent', 0, 'RGB transmission:', '({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color), 0, 'Specularity', '{:.2f}'.format(cm.specular_intensity), 0, 'Roughness:', '{:.2f}'.format(1.0-cm.specular_hardness/511.0), 0, 'Transmissivity', '{:.2f}'.format(1.0 - cm.alpha), 0, 'Transmitted Specular', '{:.2f}'.format(1.0 - cm.translucency)):
#                if matprop:
#                    row.label(matprop)  
#                else:
#                    row = layout.row()
#
#        elif cm.raytrace_mirror.use == True and cm.raytrace_mirror.reflect_factor <= 0.99:
#            for matprop in ('Metal', 0, 'RGB refelectance:', '({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color), 0, 'Specularity', '{:.2f}'.format(cm.specular_intensity), 0, 'Roughness:', '{:.2f}'.format(1.0-cm.specular_hardness/511.0)):
#                if matprop:
#                    row.label(matprop) 
#                else:
#                    row = layout.row()
#        else:
#            for matprop in ('Plastic', 0, 'RGB refelectance:', '({:.2f}, {:.2f}, {:.2f})'.format(*cm.diffuse_color), 0, 'Specularity', '{:.2f}'.format(cm.specular_intensity), 0, 'Roughness:', '{:.2f}'.format(1.0-cm.specular_hardness/511.0)):
#                if matprop:
#                    row.label(matprop) 
#                else:
#                    row = layout.row()

        layout = self.layout
        row = layout.row()
        row.label("-----------------------------------------")
        newrow(layout, "EnVi Construction Type:", cm, "envi_con_type")
        row = layout.row()
        if cm.envi_con_type not in ("Aperture", "Shading", "None"):
            row = layout.row()
            row.prop(cm, "envi_boundary")
            row = layout.row()
            row.prop(cm, "afsurface")
            newrow(layout, "Construction Make-up:", cm, "envi_con_makeup")

            if cm.envi_con_makeup == '1':
                newrow(layout, "Outside layer:", cm, "envi_layero")
                row = layout.row()
                if cm.envi_layero == '1':                    
                    if cm.envi_con_type == "Window":
                        newrow(layout, "Glass Type:", cm, "envi_export_glasslist_lo")
                    elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                        newrow(layout, "Outer layer type:", cm, "envi_layeroto")
                        newrow(layout, "Outer layer cm:", cm, ("envi_export_bricklist_lo", "envi_export_claddinglist_lo", "envi_export_concretelist_lo", "envi_export_metallist_lo", "envi_export_stonelist_lo", "envi_export_woodlist_lo", "envi_export_gaslist_lo", "envi_export_insulationlist_lo")[int(cm.envi_layeroto)])
                        row = layout.row()
                        row.prop(cm, "envi_export_lo_thi")

                elif cm.envi_layero == '2' and cm.envi_con_type != 'Window':
                    for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                        if end:
                            row.prop(cm, '{}{}'.format("envi_export_l0_", end)) 
                        else: 
                            row = layout.row()

                elif cm.envi_layero == '2' and cm.envi_con_type == 'Window':
                    for end in ('name', 0, 'thi', 'tc', 0, 'odt', 'sds', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                        if end:
                            row.prop(cm, '{}{}'.format("envi_export_l0_", end))  
                        else:
                            row = layout.row()

                if cm.envi_layero != '0':
                    newrow(layout, "2nd layer:", cm, "envi_layer1")
                    row = layout.row()
                    if cm.envi_layer1 == '1':
                        if cm.envi_con_type == "Window":
                            row.label("Gas Type:")
                            row.prop(cm, ("envi_export_wgaslist_l1"))
                            row.prop(cm, "envi_export_l1_thi")
                        elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                            row.label("2nd layer type:")
                            row.prop(cm, "envi_layer1to")
                            newrow(layout, "2nd layer cm:", cm, ("envi_export_bricklist_l1", "envi_export_claddinglist_l1", "envi_export_concretelist_l1", "envi_export_metallist_l1", "envi_export_stonelist_l1", "envi_export_woodlist_l1", "envi_export_gaslist_l1", "envi_export_insulationlist_l1")[int(cm.envi_layer1to)])
                            row = layout.row()
                            row.prop(cm, "envi_export_l1_thi")
                    elif cm.envi_layer1 == '2' and cm.envi_con_type != 'Window':
                        for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                            if end:
                                row.prop(cm, '{}{}'.format("envi_export_l1_", end))  
                            else:
                                row = layout.row()

                    elif cm.envi_layer1 == '2' and cm.envi_con_type == 'Window':
                        row.prop(cm, "envi_export_l1_name")
                        newrow(layout, "Gas Type:", cm, "envi_export_wgaslist_l1")
                        row.prop(cm, "envi_export_l1_thi")

                    if cm.envi_layer1 != '0':
                        row = layout.row()
                        row.label("3rd layer:")
                        row.prop(cm, "envi_layer2")
                        if cm.envi_layer2 == '1':
                            if cm.envi_con_type == "Window":
                                newrow(layout, "Glass Type:", cm, ("envi_export_glasslist_l2"))
                            elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                newrow(layout, "3rd layer type:", cm, "envi_layer2to")
                                newrow(layout, "3rd layer cm:", cm, ("envi_export_bricklist_l2", "envi_export_claddinglist_l2", "envi_export_concretelist_l2", "envi_export_metallist_l2", "envi_export_stonelist_l2", "envi_export_woodlist_l2", "envi_export_gaslist_l2", "envi_export_insulationlist_l2")[int(cm.envi_layer2to)])
                                row = layout.row()
                                row.prop(cm, "envi_export_l2_thi")

                        elif cm.envi_layer2 == '2'and cm.envi_con_type != 'Window':
                            for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                if end:
                                    row.prop(cm, '{}{}'.format("envi_export_l2_", end))  
                                else: 
                                    row = layout.row()

                        elif cm.envi_layer2 == '2' and cm.envi_con_type == 'Window':
                            for end in ('name', 0, 'thi', 'tc', 0, 'odt', 'sds', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                                if end:
                                    row.prop(cm, '{}{}'.format("envi_export_l2_", end))  
                                else:
                                    row = layout.row()

                        if cm.envi_layer2 != '0':
                            row = layout.row()
                            row.label("4th layer:")
                            row.prop(cm, "envi_layer3")
                            row = layout.row()
                            if cm.envi_layer3 == '1':
                                if cm.envi_con_type == "Window":
                                    row.label("Gas Type:")
                                    row.prop(cm, ("envi_export_wgaslist_l3"))
                                    row.prop(cm, "envi_export_l3_thi")
                                elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                    row.label("4th layer type:")
                                    row.prop(cm, "envi_layer3to")
                                    row = layout.row()
                                    row.label("4th layer cm:")
                                    row.prop(cm, ("envi_export_bricklist_l3", "envi_export_claddinglist_l3", "envi_export_concretelist_l3", "envi_export_metallist_l3", "envi_export_stonelist_l3", "envi_export_woodlist_l3", "envi_export_gaslist_l3", "envi_export_insulationlist_l3")[int(cm.envi_layer3to)])
                                    row = layout.row()
                                    row.prop(cm, "envi_export_l3_thi")

                            elif cm.envi_layer3 == '2'and cm.envi_con_type != 'Window':
                                for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                    if end:
                                        row.prop(cm, '{}{}'.format("envi_export_l3_", end))  
                                    else:
                                        row = layout.row()

                            elif cm.envi_layer3 == '2' and cm.envi_con_type == 'Window':
                                row.prop(cm, "envi_export_l1_name")
                                row = layout.row()
                                row.label("Gas Type:")
                                row.prop(cm, "envi_export_wgaslist_l3")
                                row.prop(cm, "envi_export_l3_thi")

                            if cm.envi_layer3 != '0':
                                row = layout.row()
                                row.label("5th layer:")
                                row.prop(cm, "envi_layer4")
                                row = layout.row()
                                if cm.envi_layer4 == '1':
                                    if cm.envi_con_type == "Window":
                                        row.label("Glass Type:")
                                        row.prop(cm, ("envi_export_glasslist_l4"))
                                    elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                        row.label("5th layer type:")
                                        row.prop(cm, "envi_layer4to")
                                        row = layout.row()
                                        row.label("5th layer cm:")
                                        row.prop(cm, ("envi_export_bricklist_l4", "envi_export_claddinglist_l4", "envi_export_concretelist_l4", "envi_export_metallist_l4", "envi_export_stonelist_l4", "envi_export_woodlist_l4", "envi_export_gaslist_l4", "envi_export_insulationlist_l4")[int(cm.envi_layer4to)])
                                        row = layout.row()
                                        row.prop(cm, "envi_export_l4_thi")

                                elif cm.envi_layer4 == '2' and cm.envi_con_type != 'Window':
                                    for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                        if end:
                                            row.prop(cm, '{}{}'.format("envi_export_l4_", end))  
                                        else:
                                            row = layout.row()

                                elif cm.envi_layer4 == '2' and cm.envi_con_type == 'Window':
                                    for end in ('name', 0, 'thi', 'tc', 0, 'odt', 'sds', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                                        if end:
                                            row.prop(cm, '{}{}'.format("envi_export_l4_", end)) 
                                        else:
                                            row = layout.row()

            elif cm.envi_con_makeup == '0':
                thicklist = ("envi_export_lo_thi", "envi_export_l1_thi", "envi_export_l2_thi", "envi_export_l3_thi", "envi_export_l4_thi")
                row = layout.row()
                if cm.envi_con_type == 'Wall':
                    row.prop(cm, "envi_export_wallconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.wall_con[cm.envi_export_wallconlist]):
                        row.label(text = layername)
                        if layername not in envi_mats.gas_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()
                
                elif cm.envi_con_type == 'Floor':
                    row.prop(cm, "envi_export_floorconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.floor_con[cm.envi_export_floorconlist]):
                        row.label(text = layername)
                        if layername not in envi_mats.gas_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()

                elif cm.envi_con_type == 'Roof':
                    row.prop(cm, "envi_export_roofconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.roof_con[cm.envi_export_roofconlist]):
                        row.label(text = layername)
                        if layername not in envi_mats.gas_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()

                elif cm.envi_con_type == 'Door':
                    row.prop(cm, "envi_export_doorconlist")
                    row = layout.row()
                    for l, layername in enumerate(envi_cons.door_con[cm.envi_export_doorconlist]):
                        row.label(text = layername)
#                        if layername not in envi_mats.door_dat:
                        row.prop(cm, thicklist[l])
                        row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
                        row = layout.row()

                elif cm.envi_con_type == 'Window':
                    row.prop(cm, "envi_export_glazeconlist")

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
        layout, lamp = self.layout, context.active_object
        row = layout.row()
        row.operator("livi.ies_select")
        row.prop(lamp, "ies_name")
        newrow(layout, 'IES Dimension:', lamp, "ies_unit")
        newrow(layout, 'IES Strength:', lamp, "ies_strength")
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
            newrow(layout, 'Heating:', object, "envi_heats1c")
            row = layout.row()
            row.prop(object, "envi_heats1")
            if object.envi_heats1 == True:
                for end in ('s1d', 0, 'p1st', 'p1et', 'sp1', 0, 'p2st', 'p2et', 'sp2', 0, 'p3st', 'p3et', 'sp3'):
                    if end:
                        row.prop(object, '{}{}'.format("envi_heats1", end))  
                    else:
                        row = layout.row()
                if object.envi_heats1d != "0":
                    row = layout.row()
                    row.prop(object, "envi_heats2")
                    if object.envi_heats2 == True:
                        if object.envi_heats1d == "1":
                            row.prop(object, "envi_heats2dwe")
                        else:
                            row.prop(object, "envi_heats2dwd")
                        for end in (0, 'p1st', 'p1et', 'sp1', 0, 'p2st', 'p2et', 'sp2', 0, 'p3st', 'p3et', 'sp3'):
                            if end:
                                row.prop(object, '{}{}'.format("envi_heats2", end))  
                            else:
                                row = layout.row()

            row = layout.row()
            row.label('-------------------------------------')

            row = layout.row()
            row.label('Cooling:')
            row.prop(object, "envi_cools1c")
            row = layout.row()
            row.prop(object, "envi_cools1")

            if object.envi_cools1 == True:
                for end in ('s1d', 0, 'p1st', 'p1et', 'sp1', 0, 'p2st', 'p2et', 'sp2', 0, 'p3st', 'p3et', 'sp3'):
                    if end:
                        row.prop(object, '{}{}'.format("envi_cools1", end))  
                    else:
                        row = layout.row()

                if object.envi_cools1d != "0":
                    row = layout.row()
                    row.prop(object, "envi_cools2")
                    if object.envi_cools2 == True:
                        if object.envi_cools1d == "1":
                            row.prop(object, "envi_cools2dwe")
                        else:
                            row.prop(object, "envi_cools2dwd")
                        for end in (0, 'p1st', 'p1et', 'sp1', 0, 'p2st', 'p2et', 'sp2', 0, 'p3st', 'p3et', 'sp3'):
                            if end:
                                row.prop(object, '{}{}'.format("envi_cools2", end))  
                            else:
                                row = layout.row()

            row = layout.row()
            row.label('------------------------------------------------------------')

            row = layout.row()
            row.label('Occupancy:')
            row.prop(object, "envi_occtype")
            if object.envi_occtype != "0":
                for end in ('max', '1d', 0, '1p1st', '1p1et', '1p1level', 0, '1p2st', '1p2et', '1p2level', 0, '1p3st', '1p3et', '1p3level', 0, '1watts'):
                    if end:
                        row.prop(object, '{}{}'.format("envi_occs", end))  
                    else:
                        row = layout.row()
                row = layout.row()
                if object.envi_occs1d != "0":
                    row.prop(object, "envi_occs2")
                    if object.envi_occs2 == True:
                        if object.envi_occs1d == "1":
                            row.prop(object, "envi_occs2dwe")
                        else:
                            row.prop(object, "envi_occs2dwd")
                        for end in ('2p1st', '2p1et', '2p1level', 0, '2p2st', '2p2et', '2p2level', 0, '2p3st', '2p3et', '2p3level', 0, '2watts'):
                            if end:
                                row.prop(object, '{}{}'.format("envi_occs", end))  
                            else:
                                row = layout.row()

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
                newrow(layout, 'Base Infiltration:', object, "envi_infbasetype")
                row.prop(object, "envi_infbaselevel")

#
#class EnMatPanel(bpy.types.Panel):
