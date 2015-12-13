import bpy
from collections import OrderedDict
from .vi_func import newrow

from .envi_mat import envi_materials, envi_constructions
envi_mats = envi_materials()
envi_cons = envi_constructions()

class Vi3DPanel(bpy.types.Panel):
    '''VI-Suite 3D view panel'''
    bl_label = "VI-Suite Display"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
        
    def draw(self, context):
        scene = context.scene
        if scene.get('viparams') and scene['viparams'].get('vidisp'):            
            view = context.space_data
            layout = self.layout

            if scene['viparams']['vidisp'] == 'wr' and scene.vi_display:            
                newrow(layout, 'Legend', scene, "vi_leg_display")

            elif scene['viparams']['vidisp'] == 'sp' and scene.vi_display:
                for i in (("Day of year:", "solday"), ("Time of day:", "solhour"), ("Display hours:", "hourdisp"), ("Display time:", "timedisp")):
                    newrow(layout, i[0], scene, i[1])
                if scene.hourdisp or scene.timedisp:
                    for i in (("Font size:", "vi_display_rp_fs"), ("Font colour:", "vi_display_rp_fc"), ("Font shadow:", "vi_display_rp_fsh")):
                        newrow(layout, i[0], scene, i[1])

            elif scene['viparams']['vidisp'] in ('ss', 'li', 'lc', 'sspanel', 'lipanel', 'lcpanel'):
                row = layout.row()
                row.prop(scene, "vi_disp_3d")                
                row = layout.row()
                row.operator("view3d.lidisplay", text="Shadow Display") if scene['viparams']['visimcontext'] == 'Shadow' else row.operator("view3d.lidisplay", text="Radiance Display")

                if scene['viparams']['vidisp'] in ('sspanel', 'lipanel', 'lcpanel') and [o for o in bpy.data.objects if o.lires]:
                    row = layout.row()
                    row.prop(view, "show_only_render")
                    newrow(layout, 'Legend', scene, "vi_leg_display")
                    if not scene.ss_disp_panel:
                        if 'UDI' in scene['liparams']['unit']:
                            newrow(layout, 'UDI type:', scene, "li_disp_udi")
                        if scene['viparams']['visimcontext'] == 'LiVi Compliance':
                            newrow(layout, 'Metric:', scene, 'li_disp_sv')
                        if scene['viparams']['visimcontext'] == 'LiVi Basic':
                            newrow(layout, 'Metric:', scene, 'li_disp_basic')
                        if scene.vi_leg_display:
                            newrow(layout, 'Legend max:', scene, "vi_leg_max")
                            newrow(layout, 'Legend min:', scene, "vi_leg_min")
                            newrow(layout, 'Legend scale', scene, "vi_leg_scale")
                    
                    if context.active_object and context.active_object.type == 'MESH':
                        newrow(layout, 'Draw wire:', scene, 'vi_disp_wire')                    
                    
                    if int(context.scene.vi_disp_3d) == 1:
                        newrow(layout, "3D Level", scene, "vi_disp_3dlevel")                        
                    
                    newrow(layout, "Transparency", scene, "vi_disp_trans")

                    if context.mode != "EDIT":
                        row = layout.row()
                        row.label(text="{:-<48}".format("Point visualisation "))
                        propdict = OrderedDict([('Enable', "vi_display_rp"), ("Selected only:", "vi_display_sel_only"), ("Visible only:", "vi_display_vis_only"), ("Font size:", "vi_display_rp_fs"), ("Font colour:", "vi_display_rp_fc"), ("Font shadow:", "vi_display_rp_fsh"), ("Position offset:", "vi_display_rp_off")])
                        for prop in propdict.items():
                            newrow(layout, prop[0], scene, prop[1])
                        row = layout.row()
                        row.label(text="{:-<60}".format(""))
 
                    if scene['viparams']['vidisp'] == 'lcpanel':
                        propdict = OrderedDict([("Compliance Panel", "li_compliance"), ("Asessment organisation:", "li_assorg"), ("Assesment individiual:", "li_assind"), ("Job number:", "li_jobno"), ("Project name:", "li_projname")])
                        for prop in propdict.items():
                            newrow(layout, prop[0], scene, prop[1])
            
            elif scene['viparams']['vidisp'] in ('en', 'enpanel'):
                resnode = bpy.data.node_groups[scene['viparams']['resnode'].split('@')[1]].nodes[scene['viparams']['resnode'].split('@')[0]]
                rl = resnode['reslists']
                zrl = list(zip(*rl))
                zmetrics = set([zr for zri, zr in enumerate(zrl[3]) if zrl[1][zri] == 'Zone'])
                lmetrics = set([zr for zri, zr in enumerate(zrl[3]) if zrl[1][zri] == 'Linkage'])
                zresdict = {"Temperature (degC)": "reszt_disp", 'Humidity (%)': 'reszh_disp', 'Heating (W)': 'reszhw_disp', 'Cooling (W)': 'reszcw_disp', 'CO2 (ppm)': 'reszco_disp'}
                vresdict = {"Opening Factor": "reszof_disp", "Linkage Flow in": "reszlf_disp"}               
                row = layout.row()               
                row.prop(resnode, '["Start"]')
                row.prop(resnode, '["End"]')
                row = layout.row() 
                row.label(text = 'Ambient')
                row = layout.row() 
                row.prop(scene, 'resaa_disp')
                row.prop(scene, 'resas_disp')
                
                for ri, rname in enumerate(zmetrics):
                    if ri == 0:                    
                        row = layout.row()
                        row.label(text = 'Zone')                    
                    if not ri%2:
                        row = layout.row()                            
                    if rname in zresdict:
                        row.prop(scene, zresdict[rname])
                
                for ri, rname in enumerate(lmetrics):
                    if ri == 0:                    
                        row = layout.row()
                        row.label(text = 'Ventilation')                    
                    if not ri%2:
                        row = layout.row()                            
                    if rname in vresdict:
                        row.prop(scene, vresdict[rname])  
                    
                newrow(layout, 'Link to object', scene, 'envi_flink')  
                newrow(layout, 'Disply type:', scene, 'en_disp')
                row = layout.row()    
                row.operator("view3d.endisplay", text="EnVi Display")
                if scene['viparams']['vidisp'] == 'enpanel':
                    if 'Temperature (degC)' in zmetrics:
                        row = layout.row()
                        row.label('Temperature')
                        row = layout.row()
                        row.prop(scene, 'en_temp_max')
                        row.prop(scene, 'en_temp_min')
                    if 'Humidity (%)' in zmetrics:
                        row = layout.row()
                        row.label('Humidity')
                        row = layout.row()
                        row.prop(scene, 'en_hum_max')
                        row.prop(scene, 'en_hum_min')
                    if 'Heating (W)' in zmetrics:
                        row = layout.row()
                        row.label('Heating')
                        row = layout.row()
                        row.prop(scene, 'en_heat_max')
                        row.prop(scene, 'en_heat_min')
                    if 'Cooling (W)' in zmetrics:
                        row = layout.row()
                        row.label('Cooling')
                        row = layout.row()
                        row.prop(scene, 'en_cool_max')
                        row.prop(scene, 'en_cool_min')   
                    if 'CO2 (ppm)' in zmetrics:
                        row = layout.row()
                        row.label('CO2')
                        row = layout.row()
                        row.prop(scene, 'en_co2_max')
                        row.prop(scene, 'en_co2_min')
                        
            newrow(layout, 'Display active', scene, 'vi_display')

class VIMatPanel(bpy.types.Panel):
    bl_label = "VI-Suite Material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material

    def draw(self, context):
        cm, scene = context.material, context.scene
        layout = self.layout
        newrow(layout, 'Material type', cm, "mattype")
        if cm.mattype != '3':
            try:
                if scene.get('viparams') and scene['viparams'].get('visimcontext') and scene['viparams']['visimcontext'] == 'LiVi Compliance':
                    simnode = bpy.data.node_groups[scene['viparams']['restree']].nodes[scene['viparams']['resnode']]
                    coptions = simnode.inputs['Context in'].links[0].from_socket['Options']
                    if cm.mattype == '1':
                        if coptions['canalysis'] == '0':
                            if coptions['bambuild'] == '2':
                                newrow(layout, "Space type:", cm, 'hspacemenu')
                            elif coptions['bambuild'] == '3':
                                newrow(layout, "Space type:", cm, 'brspacemenu')
                                if cm.brspacemenu == '2':
                                    row = layout.row()
                                    row.prop(cm, 'gl_roof')
                            elif coptions['bambuild'] == '4':
                                newrow(layout, "Space type:", cm, 'respacemenu')
                        elif coptions['canalysis'] == '1':
                            newrow(layout, "Space type:", cm, 'crspacemenu')
            except Exception as e:
                print('Compliance specification problem', e)
    
            row = layout.row()
            row.label('LiVi Radiance type:')
            row.prop(cm, 'radmatmenu')
            row = layout.row()

            for prop in cm.radmatdict[cm.radmatmenu]:
                if prop:
                     row.prop(cm, prop)
                else:
                    row = layout.row()
                    
            newrow(layout, 'BSDF:', cm, 'BSDF')
            newrow(layout, 'Photon Port:', cm, 'pport')
            row = layout.row()
            row.label("-----------------------------------------")
            newrow(layout, "EnVi Construction Type:", cm, "envi_con_type")
            row = layout.row()
            if cm.envi_con_type not in ("Aperture", "Shading", "None"):
                newrow(layout, 'Intrazone Boundary', cm, "envi_boundary")
                newrow(layout, 'Airflow surface:', cm, "envi_afsurface")
                if not cm.envi_boundary and not cm.envi_afsurface:
                    newrow(layout, 'Thermal mass:', cm, "envi_thermalmass")
                newrow(layout, "Construction Make-up:", cm, "envi_con_makeup")
                if cm.envi_con_makeup == '1':
                    newrow(layout, "Outside layer:", cm, "envi_layero")
                    row = layout.row()
                    if cm.envi_layero == '1':
                        if cm.envi_con_type == "Window":
                            newrow(layout, "Glass Type:", cm, "envi_export_glasslist_lo")
                        elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                            newrow(layout, "Outer layer type:", cm, "envi_layeroto")
                            newrow(layout, "Outer layer material:", cm, ("envi_export_bricklist_lo", "envi_export_claddinglist_lo", "envi_export_concretelist_lo", "envi_export_metallist_lo", "envi_export_stonelist_lo", "envi_export_woodlist_lo", "envi_export_gaslist_lo", "envi_export_insulationlist_lo")[int(cm.envi_layeroto)])
                            newrow(layout, "Outer layer thickness:", cm, "envi_export_lo_thi")
    
                    elif cm.envi_layero == '2' and cm.envi_con_type != 'Window':
                        for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                            if end:
                                row.prop(cm, '{}{}'.format("envi_export_lo_", end))
                            else:
                                row = layout.row()
    
                    elif cm.envi_layero == '2' and cm.envi_con_type == 'Window':
                        newrow(layout, "Name:", cm, "envi_export_lo_name")
                        newrow(layout, "Optical data type:", cm, "envi_export_lo_odt")
                        newrow(layout, "Construction Make-up:", cm, "envi_export_lo_sds")
                        newrow(layout, "Translucent:", cm, "envi_export_lo_sdiff")
                        for end in (0, 'thi', 'tc', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                            if end:
                                row.prop(cm, '{}{}'.format("envi_export_lo_", end))
                            else:
                                row = layout.row()
    
                    if cm.envi_layero != '0':
                        row = layout.row()
                        row.label("----------------")
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
                                newrow(layout, "2nd layer material:", cm, ("envi_export_bricklist_l1", "envi_export_claddinglist_l1", "envi_export_concretelist_l1", "envi_export_metallist_l1", "envi_export_stonelist_l1", "envi_export_woodlist_l1", "envi_export_gaslist_l1", "envi_export_insulationlist_l1")[int(cm.envi_layer1to)])
                                newrow(layout, "2nd layer thickness:", cm, "envi_export_l1_thi")
                        
                        elif cm.envi_layer1 == '2' and cm.envi_con_type != 'Window':
                            for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                if end:
                                    row.prop(cm, '{}{}'.format("envi_export_l1_", end))
                                else:
                                    row = layout.row()
    
                        elif cm.envi_layer1 == '2' and cm.envi_con_type == 'Window':
                            newrow(layout, "Name:", cm, "envi_export_l1_name")
                            newrow(layout, "Gas Type:", cm, "envi_export_wgaslist_l1")
                            newrow(layout, "Gas thickness:", cm, "envi_export_l1_thi")
    
                        if cm.envi_layer1 != '0':
                            row = layout.row()
                            row.label("----------------")
                            row = layout.row()
                            row.label("3rd layer:")
                            row.prop(cm, "envi_layer2")
                            if cm.envi_layer2 == '1':
                                if cm.envi_con_type == "Window":
                                    newrow(layout, "Glass Type:", cm, ("envi_export_glasslist_l2"))
                                elif cm.envi_con_type in ("Wall", "Roof", "Floor", "Door"):
                                    newrow(layout, "3rd layer type:", cm, "envi_layer2to")
                                    newrow(layout, "3rd layer material:", cm, ("envi_export_bricklist_l2", "envi_export_claddinglist_l2", "envi_export_concretelist_l2", "envi_export_metallist_l2", "envi_export_stonelist_l2", "envi_export_woodlist_l2", "envi_export_gaslist_l2", "envi_export_insulationlist_l2")[int(cm.envi_layer2to)])
                                    newrow(layout, "3rd layer thickness:", cm, "envi_export_l2_thi")
    
                            elif cm.envi_layer2 == '2'and cm.envi_con_type != 'Window':
                                for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                    if end:
                                        row.prop(cm, '{}{}'.format("envi_export_l2_", end))
                                    else:
                                        row = layout.row()
    
                            elif cm.envi_layer2 == '2' and cm.envi_con_type == 'Window':
                                newrow(layout, "Name:", cm, "envi_export_l2_name")
                                newrow(layout, "Optical data type:", cm, "envi_export_l2_odt")
                                newrow(layout, "Construction Make-up:", cm, "envi_export_l2_sds")
                                newrow(layout, "Translucent:", cm, "envi_export_l2_sdiff")
                                for end in (0, 'thi', 'tc', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                                    if end:
                                        row.prop(cm, '{}{}'.format("envi_export_l2_", end))
                                    else:
                                        row = layout.row()
    
                            if cm.envi_layer2 != '0':
                                row = layout.row()
                                row.label("----------------")
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
                                        row.label("4th layer material:")
                                        row.prop(cm, ("envi_export_bricklist_l3", "envi_export_claddinglist_l3", "envi_export_concretelist_l3", "envi_export_metallist_l3", "envi_export_stonelist_l3", "envi_export_woodlist_l3", "envi_export_gaslist_l3", "envi_export_insulationlist_l3")[int(cm.envi_layer3to)])
                                        newrow(layout, "3rd layer thickness:", cm, "envi_export_l3_thi")
    
                                elif cm.envi_layer3 == '2'and cm.envi_con_type != 'Window':
                                    for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                        if end:
                                            row.prop(cm, '{}{}'.format("envi_export_l3_", end))
                                        else:
                                            row = layout.row()
    
                                elif cm.envi_layer3 == '2' and cm.envi_con_type == 'Window':
                                    newrow(layout, "Name:", cm, "envi_export_l3_name")
                                    row = layout.row()
                                    row.label("Gas Type:")
                                    row.prop(cm, "envi_export_wgaslist_l3")
                                    newrow(layout, "3rd layer thickness:", cm, "envi_export_l3_thi")
    
                                if cm.envi_layer3 != '0':
                                    row = layout.row()
                                    row.label("----------------")
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
                                            row.label("5th layer material:")
                                            row.prop(cm, ("envi_export_bricklist_l4", "envi_export_claddinglist_l4", "envi_export_concretelist_l4", "envi_export_metallist_l4", "envi_export_stonelist_l4", "envi_export_woodlist_l4", "envi_export_gaslist_l4", "envi_export_insulationlist_l4")[int(cm.envi_layer4to)])
                                            newrow(layout, "4th layer thickness:", cm, "envi_export_l4_thi")
    
                                    elif cm.envi_layer4 == '2' and cm.envi_con_type != 'Window':
                                        for end in ('name', 0, 'thi', 'tc', 0, 'rho', 'shc', 0, 'tab', 'sab', 0, 'vab', 'rough'):
                                            if end:
                                                row.prop(cm, '{}{}'.format("envi_export_l4_", end))
                                            else:
                                                row = layout.row()
    
                                    elif cm.envi_layer4 == '2' and cm.envi_con_type == 'Window':
                                        newrow(layout, "Name:", cm, "envi_export_l4_name")
                                        newrow(layout, "Optical data type:", cm, "envi_export_l4_odt")
                                        newrow(layout, "Construction Make-up:", cm, "envi_export_l4_sds")
                                        newrow(layout, "Translucent:", cm, "envi_export_l4_sdiff")
                                        for end in (0, 'thi', 'tc', 0, 'stn', 'fsn', 'bsn', 0, 'vtn', 'fvrn', 'bvrn', 0, 'itn', 'fie', 'bie'):
                                            if end:
                                                row.prop(cm, '{}{}'.format("envi_export_l4_", end))
                                            else:
                                                row = layout.row()
    
                elif cm.envi_con_makeup == '0':
                    thicklist = ("envi_export_lo_thi", "envi_export_l1_thi", "envi_export_l2_thi", "envi_export_l3_thi", "envi_export_l4_thi")
                    propdict = {'Wall': (envi_cons.wall_con, 'envi_export_wallconlist', cm.envi_export_wallconlist), 'Floor': (envi_cons.floor_con, 'envi_export_floorconlist', cm.envi_export_floorconlist), 
                    'Roof': (envi_cons.roof_con, 'envi_export_roofconlist', cm.envi_export_roofconlist), 'Door': (envi_cons.door_con, 'envi_export_doorconlist', cm.envi_export_doorconlist), 'Window': (envi_cons.glaze_con, 'envi_export_glazeconlist', cm.envi_export_glazeconlist)} 
                    
                    row = layout.row()                
                    row.prop(cm, propdict[cm.envi_con_type][1])
                    
                    for l, layername in enumerate(propdict[cm.envi_con_type][0][propdict[cm.envi_con_type][2]]):
                        row = layout.row()
                        row.label(text = layername)
                        if layername in envi_mats.wgas_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: 14mm")
                        elif layername in envi_mats.gas_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: 20-50mm")
                        elif layername in envi_mats.glass_dat:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: "+str(float(envi_mats.matdat[layername][3])*1000)+"mm")
                        else:
                            row.prop(cm, thicklist[l])
                            row.label(text = "default: "+str(envi_mats.matdat[layername][7])+"mm")
        
        elif cm.mattype == '3':
            fvsimnode = bpy.data.node_groups[scene['viparams']['fvsimnode'].split('@')[1]].nodes[scene['viparams']['fvsimnode'].split('@')[0]] if 'fvsimnode' in scene['viparams'] else 0
            newrow(layout, "Type:", cm, "flovi_bmb_type")
            if cm.flovi_bmb_type == '0':
                newrow(layout, "Pressure type:", cm, "flovi_bmwp_type")
                if cm.flovi_bmwp_type == 'fixedValue':
                    newrow(layout, "Pressure value:", cm, "flovi_b_sval")
                    
                newrow(layout, "Velocity type:", cm, "flovi_bmwu_type")
                newrow(layout, "Field value:", cm, "flovi_u_field")
                if not cm.flovi_u_field:
                    newrow(layout, 'Velocity:', cm, 'flovi_b_vval')
#                split = layout.split()
#                col = split.column(align=True)
#                col.label(text="Velocity:")
#                col.prop(cm, "flovi_bmu_x")
#                col.prop(cm, "flovi_bmu_y")
#                col.prop(cm, "flovi_bmu_z")
                
                if fvsimnode and fvsimnode.solver != 'icoFoam':
                    newrow(layout, "nut type:", cm, "flovi_bmwnut_type")
                    if fvsimnode.turbulence == 'SpalartAllmaras':                        
                        newrow(layout, "nuTilda type:", cm, "flovi_bmwnutilda_type")
                    elif fvsimnode.turbulence == 'kEpsilon':
                        newrow(layout, "k type:", cm, "flovi_bmwk_type")
                        newrow(layout, "Epsilon type:", cm, "flovi_bmwe_type")
                    elif fvsimnode.turbulence == 'komega':
                        newrow(layout, "k type:", cm, "flovi_bmwk_type")
                        newrow(layout, "Omega type:", cm, "flovi_bmwe_type")
                    if fvsimnode.bouyancy:
                        newrow(layout, "Temperature:", cm, "temperature")
#                newrow(layout, "nuTilda:", cm, "flovi_bmnutilda")
#                split = layout.split()
#                col = split.column(align=True)
#                col.label(text="nuTilda:")
#                col.prop(cm, "flovi_bmnut")
#                col.prop(cm, "flovi_bmwnut_y")
#                col.prop(cm, "flovi_bmwnut_z")
            elif cm.flovi_bmb_type == '1':
                newrow(layout, "Pressure sub-type:", cm, "flovi_bmip_type")
                if cm.flovi_bmip_type == 'fixedValue':
                    newrow(layout, "Pressure value:", cm, "flovi_b_sval")
                newrow(layout, "Velocity sub-type:", cm, "flovi_bmiu_type")
                newrow(layout, "Field value:", cm, "flovi_u_field")
                if not cm.flovi_u_field:
                    newrow(layout, 'Velocity:', cm, 'flovi_b_vval')
                if fvsimnode and fvsimnode.solver != 'icoFoam':
                    newrow(layout, "nut type:", cm, "flovi_bminut_type")
                    if fvsimnode.turbulence == 'SpalartAllmaras':                        
                        newrow(layout, "nuTilda type:", cm, "flovi_bminutilda_type")
                    elif fvsimnode.turbulence == 'kEpsilon':
                        newrow(layout, "k type:", cm, "flovi_bmik_type")
                        newrow(layout, "Epsilon type:", cm, "flovi_bmie_type")
                    elif fvsimnode.turbulence == 'kOmega':
                        newrow(layout, "k type:", cm, "flovi_bmik_type")
                        newrow(layout, "Omega type:", cm, "flovi_bmio_type")
            elif cm.flovi_bmb_type == '2':
                newrow(layout, "Pressure sub-type:", cm, "flovi_bmop_type")
                if cm.flovi_bmop_type == 'fixedValue':
                    newrow(layout, "Pressure value:", cm, "flovi_b_sval")
                newrow(layout, "Velocity sub-type:", cm, "flovi_bmou_type")
                newrow(layout, "Field value:", cm, "flovi_u_field")
                if not cm.flovi_u_field:
                    newrow(layout, 'Velocity:', cm, 'flovi_b_vval')
                if fvsimnode and fvsimnode.solver != 'icoFoam':
                    newrow(layout, "nut type:", cm, "flovi_bmonut_type")
                    if fvsimnode.turbulence == 'SpalartAllmaras':                        
                        newrow(layout, "nuTilda type:", cm, "flovi_bmonutilda_type")
                    elif fvsimnode.turbulence == 'kEpsilon':
                        newrow(layout, "k type:", cm, "flovi_bmok_type")
                        newrow(layout, "Epsilon type:", cm, "flovi_bmoe_type")
                    elif fvsimnode.turbulence == 'kOmega':
                        newrow(layout, "k type:", cm, "flovi_bmok_type")
                        newrow(layout, "Omega type:", cm, "flovi_bmoo_type")
                
class IESPanel(bpy.types.Panel):
    bl_label = "VI Object Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        if context.lamp or context.mesh:
            return True

    def draw(self, context):
        layout, lamp = self.layout, context.active_object
        if context.mesh: 
            if [mat for mat in lamp.data.materials if mat.BSDF]:
                row = layout.row()
                row.label('Generate BSDF')
                newrow(layout, 'Direction:', context.scene, 'li_bsdf_direc')
                newrow(layout, 'Tensor:', context.scene, 'li_bsdf_tensor')
                newrow(layout, 'resolution:', context.scene, 'li_bsdf_res')
                newrow(layout, 'Samples:', context.scene, 'li_bsdf_samp')
                row.operator("object.gen_bsdf", text="BSDF")
                if lamp.get('bsdf'):
                    row = layout.row()
                    row.label('Delete BSDF')
                    row.operator("object.del_bsdf", text="Delete BSDF")
            newrow(layout, 'Light Array', lamp, 'lila')
        if (lamp.type == 'LAMP' and lamp.data.type != 'SUN') or lamp.lila: 
            row = layout.row()
            row.operator("livi.ies_select")
            row.prop(lamp, "ies_name")
            newrow(layout, 'IES Dimension:', lamp, "ies_unit")
            newrow(layout, 'IES Strength:', lamp, "ies_strength")
            row = layout.row()
            row.prop(lamp, "ies_colour")
                
class VIZonePanel(bpy.types.Panel):
    bl_label = "VI-Suite Zone Definition"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        if context.object and context.object.type == 'MESH':
            return True

    def draw(self, context):
        obj = bpy.context.active_object
        layout = self.layout
        row = layout.row()
        row.prop(obj, "vi_type")
        if obj.vi_type == '1':
            row = layout.row()
            row.prop(obj, "envi_type")
