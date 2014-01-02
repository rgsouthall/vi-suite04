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


import bpy, blf, colorsys, bgl, mathutils
from math import cos, sin
from . import livi_export
from . import vi_func

def ss_display():
    pass

def li_display(simnode, connode, geonode):
    cp = '0' if not geonode else geonode.cpoint
    scene = bpy.context.scene
    vi_func.clearscened(scene)
    obreslist = []
    obcalclist = []

    if simnode.bl_label != 'VI Shadow Study' and len(bpy.app.handlers.frame_change_pre) == 0:
        bpy.app.handlers.frame_change_pre.append(livi_export.cyfc1)
        o = 0

        for geo in scene.objects:
            if geo.type == "MESH" and geo.licalc == 1 and geo.hide == False:
                geo.select = True
                if geo.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.object.select_all(action = 'DESELECT')
                obcalclist.append(geo)
                o += 1

        for frame in vi_func.framerange(scene):
            scene.frame_set(frame)
            for obcalc in obcalclist:
                for vc in obcalc.data.vertex_colors:
                    (vc.active, vc.active_render) = (1, 1) if vc.name == str(frame) else (0, 0)
                    vc.keyframe_insert("active")
                    vc.keyframe_insert("active_render")

    scene.frame_set(0)
    bpy.ops.object.select_all(action = 'DESELECT')
    scene.objects.active = None

    if scene.li_disp_3d == 1:
        for i, geo in enumerate(vi_func.retobjs('livic')):
            scene.objects.active = None
            bpy.ops.object.select_all(action = 'DESELECT')
            scene.objects.active = geo
            geo.select = True
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.context.tool_settings.mesh_select_mode = [False, False, True]
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.object.mode_set(mode = 'OBJECT')

            for cf in geo["cfaces"]:
                geo.data.polygons[int(cf)].select = True

            if len(geo["cverts"]) > 0:
                bpy.context.tool_settings.mesh_select_mode = [True, False, False]
                for cv in geo["cverts"]:
                    geo.data.vertices[int(cv)].select = True

            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.duplicate()
            bpy.ops.mesh.separate()
            bpy.ops.object.mode_set(mode = 'OBJECT')
            scene.objects[0].name = geo.name+"res"
            obreslist.append(scene.objects[0])
            scene.objects[0].lires = 1
            bpy.ops.object.select_all(action = 'DESELECT')
            scene.objects.active = None

        for obres in obreslist:
            oreslist = {}
            scene.objects.active = obres
            obres.select = True
            j = []

            if cp == '0':
                if len(obres.data.polygons) > 1:
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.select_all(action = 'SELECT')
                    bpy.ops.mesh.extrude_faces_move()
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    bpy.ops.object.select_all(action = 'DESELECT')

                    for fli in [face.loop_indices for face in obres.data.polygons if face.select == True]:
                        for li in fli:
                            j.append(obres.data.loops[li].vertex_index)
            else:
                for vn in obres['cverts']:
                    j.append([j for j,x in enumerate(obres.data.loops) if vn == x.vertex_index][0])

            bpy.ops.object.shape_key_add(from_mix = False)

            for frame in range(0, scene.frame_end + 1):
                bpy.ops.object.shape_key_add(from_mix = False)
                obres.active_shape_key.name = str(frame)
                if cp == '0' and geonode:
                    oreslist[str(frame)] = [simnode['minres'][frame] + (simnode['maxres'][frame] - simnode['minres'][frame]) * 1/0.75 * vi_func.rgb2h(obres.data.vertex_colors[str(frame)].data[li].color) for li in [face.loop_indices[0] for face in obres.data.polygons if face.select == True]]
                elif not geonode:
                    oreslist[str(frame)] = [simnode['minres'][frame] + (simnode['maxres'][frame] - simnode['minres'][frame]) * obres.data.vertex_colors['SolarShade'].data[li].color[0] for li in [face.loop_indices[0] for face in obres.data.polygons if face.select == True]]
                elif cp == '1':
                    oreslist[str(frame)] = [simnode['minres'][frame] + (simnode['maxres'][frame] - simnode['minres'][frame]) * 1/0.75 * vi_func.rgb2h(obres.data.vertex_colors[str(frame)].data[j].color) for j in range(len(obres.data.vertex_colors[str(frame)].data))]
            print('hi')
            obres['oreslist'] = oreslist
            obres['j'] = j

    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        for obres in obreslist:
            if scene.li_disp_3d == 1:
                for shape in obres.data.shape_keys.key_blocks:
                        if "Basis" not in shape.name:
                            shape.value = 1 if int(shape.name) == frame else 0
                            shape.keyframe_insert("value")

            for vc in obres.data.vertex_colors:
                (vc.active, vc.active_render) = (1, 1) if vc.name == str(frame) else (0, 0)
                vc.keyframe_insert("active")
                vc.keyframe_insert("active_render")

    scene.frame_set(0)
    bpy.ops.wm.save_mainfile(check_existing = False)
    rendview(1)

def spnumdisplay(disp_op, context, simnode):
    scene = context.scene
    leg = 0 if simnode.bl_label == 'VI Sun Path' else 1
    try:
        ob = bpy.data.objects['SPathMesh']
        bgl.glColor3f(0,0,0)
        if scene.hourdisp == True:
            mid_x, mid_y, width, height = vi_func.viewdesc(context)
            view_mat = context.space_data.region_3d.perspective_matrix
            ob_mat = ob.matrix_world
            total_mat = view_mat*ob_mat
            for np in ob['numpos']:
                vi_func.draw_index(context, leg, mid_x, mid_y, width, height, total_mat, np.split('-')[1], mathutils.Vector(ob['numpos'][np]))
        else:
            return

    except Exception as e:
        print(e)
        return

def linumdisplay(disp_op, context, simnode, geonode):
    scene = context.scene
    blf.enable(0, 4)
    blf.shadow(0, 5,scene.li_display_rp_fsh[0], scene.li_display_rp_fsh[1], scene.li_display_rp_fsh[2], scene.li_display_rp_fsh[3])
    bgl.glColor4f(scene.li_display_rp_fc[0], scene.li_display_rp_fc[1], scene.li_display_rp_fc[2], scene.li_display_rp_fc[3])

    try:
        if obcalclist:
            pass
    except:
        obreslist = [ob for ob in scene.objects if ob.type == 'MESH' and 'lightarray' not in ob.name and ob.hide == False and ob.layers[0] == True and ob.licalc == 1 and ob.lires == 1]
        obcalclist = [ob for ob in scene.objects if ob.type == 'MESH' and 'lightarray' not in ob.name and ob.hide == False and ob.layers[0] == True and ob.licalc == 1 and ob.lires == 0]

    if scene.li_display_rp != True or (bpy.context.active_object not in (obcalclist+obreslist) and scene.li_display_sel_only == True)  or scene.frame_current not in range(scene.frame_start, scene.frame_end+1):
        return

    cp = geonode.cpoint if geonode else simnode.cpoint
    fn = context.scene.frame_current
    mid_x, mid_y, width, height = vi_func.viewdesc(context)

    if scene.li_display_sel_only == False:
        obd = obreslist if len(obreslist) > 0 else obcalclist
    else:
        obd = [context.active_object]

    for ob in obd:

        obm = ob.data
        ob_mat = ob.matrix_world
        view_mat = context.space_data.region_3d.perspective_matrix
        view_pos = (view_mat.inverted()[0][3]/5, view_mat.inverted()[1][3]/5, view_mat.inverted()[2][3]/5)
        faces = [f for f in ob.data.polygons if f.select == True and ob.ray_cast(ob_mat*mathutils.Vector((f.center)) - ob.location + 0.2*f.normal, view_pos)[2] == -1] if len(obreslist) > 0 else [f for f in ob.data.polygons]
        print(ob.ray_cast(mathutils.Vector((ob.data.polygons[0].center))+ 0.2*ob.data.polygons[0].normal, view_pos)[2])
        vdone = []
#        t = (matrix[0][3], matrix[1][3], matrix[2][3])
#        r = (
#          (matrix[0][0], matrix[0][1], matrix[0][2]),
#          (matrix[1][0], matrix[1][1], matrix[1][2]),
#          (matrix[2][0], matrix[2][1], matrix[2][2])
#        )
#        rp = (
#          (-r[0][0], -r[1][0], -r[2][0]),
#          (-r[0][1], -r[1][1], -r[2][1]),
#          (-r[0][2], -r[1][2], -r[2][2])
#        )
#        output = (
#          rp[0][0] * t[0] + rp[0][1] * t[1] + rp[0][2] * t[2],
#          rp[1][0] * t[0] + rp[1][1] * t[1] + rp[1][2] * t[2],
#          rp[2][0] * t[0] + rp[2][1] * t[1] + rp[2][2] * t[2],
#        )
#        view_pos = -1.0*view_mat.translation_part()*view_mat.rotation_part()


        total_mat = view_mat*ob_mat

        for f in faces:
            if cp == "0" or not geonode:
                vsum = mathutils.Vector((0, 0, 0))
                for v in f.vertices:
                    vsum = ob.active_shape_key.data[v].co + vsum if len(obreslist) > 0 else ob.data.vertices[v].co + vsum
                fc = vsum/len(f.vertices)
                if not f.hide:
                    loop_index = f.loop_indices[0]
                    if len(set(obm.vertex_colors[fn].data[loop_index].color[:])) > 0:
                        if geonode:
                            vi_func.draw_index(context, 1, mid_x, mid_y, width, height, total_mat, int(simnode['minres'][fn] + (1 - (1.333333*colorsys.rgb_to_hsv(obm.vertex_colors[fn].data[loop_index].color[0]/255, obm.vertex_colors[fn].data[loop_index].color[1]/255, obm.vertex_colors[fn].data[loop_index].color[2]/255)[0]))*(simnode['maxres'][fn] - simnode['minres'][fn])), fc.to_4d())
                        else:
                            vi_func.draw_index(context, 1, mid_x, mid_y, width, height, total_mat, int(simnode['minres'][fn] + (100 - (obm.vertex_colors[fn].data[loop_index].color[0])*(simnode['maxres'][fn] - simnode['minres'][fn]))), fc.to_4d())
            elif cp == "1":
                for loop_index in f.loop_indices:
                    v = obm.loops[loop_index].vertex_index
                    vpos = ob.active_shape_key.data[v].co if len(obreslist) > 0 else obm.vertices[v].co
                    if v not in vdone:
                        vdone.append(v)
                        if len(set(obm.vertex_colors[fn].data[loop_index].color[:])) > 0:
                            vi_func.draw_index(context, 1, mid_x, mid_y, width, height, total_mat, int((1 - (1.333333*colorsys.rgb_to_hsv(obm.vertex_colors[fn].data[loop_index].color[0]/255, obm.vertex_colors[fn].data[loop_index].color[1]/255, obm.vertex_colors[fn].data[loop_index].color[2]/255)[0]))*simnode['maxres'][fn]), vpos.to_4d())
    blf.disable(0, 4)
def li3D_legend(self, context, simnode, connode):
    scene = context.scene
    if scene.li_leg_display != True or scene.vi_display == 0:
        return
    else:
        if not connode or (connode and connode.bl_label == 'LiVi CBDM'):
            resvals = ['{:.1f}'.format(min(simnode['minres'])+i*(max(simnode['maxres'])-min(simnode['minres']))/19) for i in range(20)]
        else:
            resvals = [('{:.0f}', '{:.0f}', '{:.1f}')[int(connode.analysismenu)].format(min(simnode['minres'])+i*(max(simnode['maxres'])-min(simnode['minres']))/19) for i in range(20)]

        height = context.region.height
        lenres = len(resvals[-1])
        font_id = 0
        vi_func.drawpoly(20, height - 40, 70 + lenres*8, height - 520)
        vi_func.drawloop(19, height - 40, 70 + lenres*8, height - 520)

        for i in range(20):
            h = 0.75 - 0.75*(i/19)
            if connode:
                bgl.glColor4f(colorsys.hsv_to_rgb(h, 1.0, 1.0)[0], colorsys.hsv_to_rgb(h, 1.0, 1.0)[1], colorsys.hsv_to_rgb(h, 1.0, 1.0)[2], 1.0)
            else:
                bgl.glColor4f((19-i)/19, (19-i)/19, (19-i)/19, 1)
            bgl.glBegin(bgl.GL_POLYGON)
            bgl.glVertex2i(20, (i*20)+height - 460)
            bgl.glVertex2i(60, (i*20)+height - 460)
            bgl.glVertex2i(60, (i*20)+height - 440)
            bgl.glVertex2i(20, (i*20)+height - 440)
            bgl.glEnd()
            blf.size(font_id, 20, 48)
            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
            blf.position(font_id, 65, (i*20)+height - 455, 0)
            blf.draw(font_id, "  "*(lenres - len(resvals[i]) ) + resvals[i])

        blf.size(font_id, 20, 56)
        cu = connode.unit if connode else '% Shadow'

        vi_func.drawfont(cu, font_id, 0, height, 25, 57)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        height = context.region.height
        font_id = 0
        if context.scene.frame_current in vi_func.framerange(context.scene):
            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
            blf.size(font_id, 20, 48)
            if hasattr(context.active_object, 'lires') and context.active_object.lires:
                vi_func.drawfont("Ave: {:.1f}".format(context.active_object['avres'][context.scene.frame_current]), font_id, 0, height, 22, 480)
                vi_func.drawfont("Max: {:.1f}".format(context.active_object['maxres'][context.scene.frame_current]), font_id, 0, height, 22, 495)
                vi_func.drawfont("Min: {:.1f}".format(context.active_object['minres'][context.scene.frame_current]), font_id, 0, height, 22, 510)
            else:
                vi_func.drawfont("Ave: {:.1f}".format(simnode['avres'][context.scene.frame_current]), font_id, 0, height, 22, 480)
                vi_func.drawfont("Max: {:.1f}".format(simnode['maxres'][context.scene.frame_current]), font_id, 0, height, 22, 495)
                vi_func.drawfont("Min: {:.1f}".format(simnode['minres'][context.scene.frame_current]), font_id, 0, height, 22, 510)

def li_compliance(self, context, connode):
    height = context.region.height
    scene = context.scene
    try:
        if not scene.li_compliance or scene.frame_current not in range(scene.frame_start, scene.frame_end + 1) or scene.vi_display == 0:
            return
    except:
        return

    if connode.analysismenu == '0':
        buildtype = ('School', 'Higher Education', 'Healthcare', 'Residential', 'Retail', 'Office & Other')[int(connode.bambuildmenu)]
    elif connode.analysismenu == '1':
        buildtype = 'Residential'
        cfshpfsdict = {'totkit': 0, 'kitdf': 0, 'kitsv': 0, 'totliv': 0, 'livdf': 0, 'livsv': 0}

    vi_func.drawpoly(100, height - 40, 900, height - 65)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    horpos = (100, 317, 633, 900)
    widths = (100, 450, 600, 750, 900)

    for p in range(3):
        vi_func.drawloop(horpos[p], height - 40, horpos[p+1], height - 65)

    font_id = 0
    blf.size(font_id, 20, 54)
    vi_func.drawfont('Standard: '+('BREEAM HEA1', 'CfSH', 'LEED EQ8.1', 'Green Star')[int(connode.analysismenu)], font_id, 0, height, 110, 58)
    vi_func.drawfont('Project Name: '+scene.li_projname, font_id, 0, height, 643, 58)
    blf.size(font_id, 20, 40)

    def space_compliance(geos):
        frame = scene.frame_current
        buildspace =''
        pfs = []
        epfs = []
        lencrit = 0
        for geo in geos:
            mat = [m for m in geo.data.materials if m.livi_sense][0]
#            crit = geo['crit']
            geo['cr4'] = [('fail', 'pass')[int(com)] for com in geo['comps'][frame][:][::2]]
            geo['cr6'] = [cri[4] for cri in geo['crit']]
            if 'fail' in [c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                pf = 'FAIL'
            elif 'pass' not in [c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.75'] and len([c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.75']) > 0:
                if 'pass' not in [c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.5'] and len([c for i, c in enumerate(geo['cr4']) if geo['cr6'][i] == '0.5']) > 0:
                    pf = 'FAIL'
                else:
                    pf = 'PASS'
            else:
                pf = 'PASS'
            pfs.append(pf)

            if connode.analysismenu == '1':
                cfshpfsdict[('totkit', 'totliv')[mat.rspacemenu == '1']] += 1
                if geo['cr4'][0] == 'pass':
                    cfshpfsdict[('kitdf', 'livdf')[mat.rspacemenu == '1']] += 1
                if geo['cr4'][1] == 'pass':
                    cfshpfsdict[('kitsv', 'livsv')[mat.rspacemenu == '1']] += 1

            if connode.analysismenu == '0':
                ecrit = geo['ecrit']
                geo['ecr4'] = [('fail', 'pass')[int(com)] for com in geo['ecomps'][frame][:][::2]]
                geo['ecr6'] = [ecri[4] for ecri in ecrit]
                if 'fail' in [c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                    epf = 'FAIL'
                elif 'pass' not in [c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.75'] and len([c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.75']) > 0:
                    if 'pass' not in [c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.5'] and len([c for i, c in enumerate(geo['ecr4']) if geo['ecr6'][i] == '0.5']) > 0:
                        epf = 'FAIL'
                    else:
                        epf = 'EXEMPLARY'
                else:
                    epf = 'EXEMPLARY'
                epfs.append(epf)

        if bpy.context.active_object in geos:
            geo = bpy.context.active_object
            lencrit = 1 + len(geo['crit'])
            vi_func.drawpoly(100, height - 70, 900, height - 70  - (lencrit)*25)
            vi_func.drawloop(100, height - 70, 900, height - 70  - (lencrit)*25)
            mat = [m for m in bpy.context.active_object.data.materials if m.livi_sense][0]
            if connode.analysismenu == '0':
                buildspace = ('', '', (' - Public/Staff', ' - Patient')[int(mat.hspacemenu)], (' - Kitchen', ' - Living/Dining/Study', ' - Communal')[int(mat.rspacemenu)], (' - Sales', ' - Office')[int(mat.respacemenu)])[int(connode.bambuildmenu)]
#                if connode.bambuildmenu == '2':
#                    buildspace = (' - Public/Staff', ' - Patient')[int(mat.hspacemenu)]
#                elif connode.bambuildmenu == '3':
#                    buildspace = (' - Kitchen', ' - Living/Dining/Study', ' - Communal')[int(mat.rspacemenu)]
#                elif connode.bambuildmenu == '4':
#                    buildspace = (' - Sales', ' - Office')[int(mat.respacemenu)]
            elif connode.analysismenu == '1':
                buildspace = (' - Kitchen', ' - Living/Dining/Study')[int(mat.rspacemenu)]


            titles = ('Zone Metric', 'Target', 'Achieved', 'PASS/FAIL')
            tables = [[] for c in range(lencrit -1)]
            etables = [[] for e in range(len(geo['ecrit']))]
            for c, cr in enumerate(geo['crit']):
                if cr[0] == 'Percent':
                    tables[c] = ('{} (%)'.format(('Percentage area with Skyview', 'Average{}Daylight Factor'.format((' ', ' Point ')[cr[2] == 'PDF']))[cr[2] in ('DF', 'PDF')]), (cr[1],cr[3])[cr[2] in ('PDF','DF')], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
                elif cr[0] == 'Ratio':
                    tables[c] = ('Uniformity ratio', cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
                elif cr[0] == 'Min':
                    tables[c] = ('Minimum {} (%)'.format('Point Daylight Factor'), cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
                elif cr[0] == 'Average':
                    tables[c] = ('Average {} (%)'.format('Daylight Factor'), cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), geo['cr4'][c].upper())
            if connode.analysismenu == '0':
                for e, ecr in enumerate(ecrit):
                    if ecr[0] == 'Percent':
                        etables[e] = ('{} (%)'.format('Average Daylight Factor'), ecr[3], '{:.2f}'.format(geo['ecomps'][frame][:][e*2 + 1]), geo['ecr4'][e].upper())
                    elif ecr[0] == 'Min':
                        etables[e] = ('Minimum {} (%)'.format('Point Daylight Factor'), ecr[3], '{:.2f}'.format(geo['ecomps'][frame][:][e*2 + 1]), geo['ecr4'][e].upper())

            for j in range(4):
                vi_func.drawloop(widths[j], height - 70, widths[j+1], height - 95)

            bgl.glEnable(bgl.GL_LINE_STIPPLE)
            for t, tab in enumerate(tables):
                for j in range(4):
                    vi_func.drawloop(widths[j], height - 95 - t*25, widths[j+1], height - 120 - t*25)
                    if tab[j] == 'FAIL':
                        bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                    elif tab[j] == 'PASS':
                        bgl.glColor4f(0.0, 0.7, 0.0, 1.0)
                    blf.size(font_id, 20, 44)
                    vi_func.drawfont(tab[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 113 + t*25)
                    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                    if t == 0:
                        blf.size(font_id, 20, 48)
                        vi_func.drawfont(titles[j], 0, 0, height, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], 88)
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        else:
            etables = []
            lencrit = 0

        tpf = 'FAIL' if 'FAIL' in pfs or 'FAIL*' in pfs else 'PASS'
        if connode.analysismenu == '0':
            (tpf, lencrit) = ('EXEMPLARY', lencrit + len(geo['ecrit'])) if tpf == 'PASS' and ('FAIL' not in epfs or 'FAIL*' not in epfs) else (tpf, lencrit)

        return(tpf, lencrit, buildspace, etables)

    build_compliance, lencrit, bs, etables = space_compliance(vi_func.retobjs('livir'))

    if build_compliance == 'EXEMPLARY':
        for t, tab in enumerate(etables):
            if t == 0:
                vi_func.drawpoly(100, height - 70 - (lencrit * 25), 900, height - 70 - ((lencrit - len(etables)) * 25))
                vi_func.drawloop(100, height - 70 - (lencrit * 25), 900, height - 70 - ((lencrit - len(etables)) * 25))

            for j in range(4):
                bgl.glEnable(bgl.GL_LINE_STIPPLE)
                vi_func.drawloop(widths[j], height - 95 - (lencrit - len(etables) + t - 1) * 25, widths[j+1], height - 120 - (lencrit - len(etables) + t - 1) * 25)
                if tab[j] == 'FAIL':
                    bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                elif tab[j] == 'PASS':
                    bgl.glColor4f(0.0, 1.0, 0.0, 1.0)
                blf.size(font_id, 20, 44)
                blf.position(font_id, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], height - 113 - (lencrit - len(etables) + t - 1) * 25, 0)
                bgl.glColor4f(0.0, 0.7, 0.0, 1.0)
                blf.draw(font_id, tab[j])
                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                bgl.glDisable(bgl.GL_LINE_STIPPLE)

    blf.position(font_id, 327, height - 58, 0)
    blf.size(font_id, 20, 54)
    blf.draw(font_id, 'Buildtype: '+buildtype+bs)

    blf.size(font_id, 20, 52)
    blf.position(font_id, 110, height - 87 - lencrit*26, 0)
    if connode.analysismenu == '0':
        vi_func.drawpoly(100, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
        vi_func.drawloop(100, height - 70 - lencrit*26, 350, height - 95 - lencrit*26)
        vi_func.drawloop(100, height - 70 - lencrit*26, 350, height - 95 - lencrit*26)
        vi_func.drawloop(350, height - 70 - lencrit*26, 525, height - 95 - lencrit*26)
        blf.draw(font_id, 'Building Compliance:')
        vi_func.drawfont(build_compliance, 0, lencrit, height, 250, 87)
        blf.position(font_id, 360, height - 87 - lencrit*26, 0)
        blf.draw(font_id, 'Credits achieved:')
        blf.position(font_id, 480, height - 87 - lencrit*26, 0)
        if build_compliance == 'PASS':
           blf.draw(font_id,  ('1', '2', '2', '1', '1', '1')[int(connode.bambuildmenu)])
        elif build_compliance == 'EXEMPLARY':
            blf.draw(font_id,  ('2', '3', '3', '2', '2', '2')[int(connode.bambuildmenu)])
        else:
            blf.draw(font_id, '0')

    elif connode.analysismenu == '1':
        vi_func.drawpoly(100, height - 70 - lencrit*26, 300, height - 95 - lencrit*26)
        vi_func.drawloop(100, height - 70 - lencrit*26, 300, height - 95 - lencrit*26)
        vi_func.drawfont('Credits achieved:', 0, lencrit, height, 110, 87)
        cfshcred = 0
        if cfshpfsdict['kitdf'] == cfshpfsdict['totkit'] and cfshpfsdict['totkit'] != 0:
            cfshcred += 1
        if cfshpfsdict['livdf'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0:
            cfshcred += 1
        if (cfshpfsdict['kitsv'] == cfshpfsdict['totkit'] and  cfshpfsdict['totkit'] != 0) or (cfshpfsdict['livsv'] == cfshpfsdict['totliv'] and cfshpfsdict['totliv'] != 0):
            cfshcred += 1
        blf.position(font_id, 250, height - 87 - lencrit*26, 0)
        blf.draw(font_id, '{} of {}'.format(cfshcred, '3' if 0 not in (cfshpfsdict['totkit'], cfshpfsdict['totliv']) else '2'))

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    bgl.glLineWidth(1)
    sw = 8

    aolen, ailen, jnlen = len(scene.li_assorg), len(scene.li_assind), len(scene.li_jobno)
    vi_func.drawpoly(100, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    vi_func.drawloop(100, 50, 260 + aolen*sw, 25)
    vi_func.drawloop(260 + aolen*sw, 50, 400 + aolen*sw + ailen*sw, 25)
    vi_func.drawloop(400 + aolen*sw + ailen*sw, 50, 500 + aolen*sw + ailen*sw + jnlen*sw, 25)
    blf.size(font_id, 20, 44)
    blf.position(font_id, 110, 32, 0)
    blf.draw(font_id, 'Assessing Organisation:')
    blf.position(font_id, 250, 32, 0)
    blf.draw(font_id, scene.li_assorg)
    blf.position(font_id, 270 + aolen*sw, 32, 0)
    blf.draw(font_id, 'Assessing Individual:')
    blf.position(font_id, 395 + aolen*sw, 32, 0)
    blf.draw(font_id, scene.li_assind)
    blf.position(font_id, 410 + aolen*sw + ailen*sw, 32, 0)
    blf.draw(font_id, 'Job Number:')
    blf.position(font_id, 490 + aolen*sw + ailen*sw, 32, 0)
    blf.draw(font_id, scene.li_jobno)

def rendview(i):
    for scrn in bpy.data.screens:
        if scrn.name == 'Default':
            bpy.context.window.screen = scrn
            for area in scrn.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.viewport_shade = 'SOLID'
                            if i ==  1:
                                space.show_textured_solid = 1
                            else:
                                space.show_textured_solid = 0



