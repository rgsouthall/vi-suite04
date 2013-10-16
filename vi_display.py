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
from . import livi_export
from . import vi_func

def li_display(simnode, connode, geonode):
    scene = bpy.context.scene
    vi_func.clearscened(scene)
    obreslist = []
    obcalclist = []

    if len(bpy.app.handlers.frame_change_pre) == 0:
        bpy.app.handlers.frame_change_pre.append(livi_export.cyfc1)
    o = 0

    for geo in scene.objects:
        if geo.type == "MESH" and geo.licalc == 1:
            geo.select = True
            if geo.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.select_all(action = 'DESELECT')
            obcalclist.append(geo)
            o += 1

    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        for obcalc in obcalclist:
            for vc in obcalc.data.vertex_colors:
                if vc.name == str(frame):
                    vc.active = 1
                    vc.active_render = 1
                else:
                    vc.active = 0
                    vc.active_render = 0
                vc.keyframe_insert("active")
                vc.keyframe_insert("active_render")

    scene.frame_set(0)
    bpy.ops.object.select_all(action = 'DESELECT')
    scene.objects.active = None

    if scene.li_disp_3d == 1:
        for i, geo in enumerate(scene.objects):
            if geo.type == 'MESH' and geo.licalc == 1 and geo.lires == 0:
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

            if geonode.cpoint == '0':
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
                if geonode.cpoint == '0':
                    oreslist[str(frame)] = [vi_func.rgb2h(obres.data.vertex_colors[str(frame)].data[li].color) for li in [face.loop_indices[0] for face in obres.data.polygons if face.select == True]]
                else:
                    oreslist[str(frame)] = [vi_func.rgb2h(obres.data.vertex_colors[str(frame)].data[j].color) for j in range(len(obres.data.vertex_colors[str(frame)].data))]
            obres['oreslist'] = oreslist
            obres['j'] = j

    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        for obres in obreslist:
            if scene.li_disp_3d == 1:
                for shape in obres.data.shape_keys.key_blocks:
                        if "Basis" not in shape.name:
                            if int(shape.name) == frame:
                                shape.value = 1
                                shape.keyframe_insert("value")
                            else:
                                shape.value = 0
                                shape.keyframe_insert("value")

            for vc in obres.data.vertex_colors:
                if vc.name == str(frame):
                    vc.active = 1
                    vc.active_render = 1
                    vc.keyframe_insert("active")
                    vc.keyframe_insert("active_render")
                else:
                    vc.active = 0
                    vc.active_render = 0
                    vc.keyframe_insert("active")
                    vc.keyframe_insert("active_render")

    bpy.ops.wm.save_mainfile(check_existing = False)
    rendview(1)

def linumdisplay(disp_op, context, simnode, geonode):
    scene = context.scene
    try:
        if obcalclist:
            pass
    except:
        obreslist = [ob for ob in bpy.data.objects if ob.type == 'MESH' and 'lightarray' not in ob.name and ob.hide == False and ob.layers[0] == True and ob.licalc == 1 and ob.lires == 1]
        obcalclist = [ob for ob in bpy.data.objects if ob.type == 'MESH' and 'lightarray' not in ob.name and ob.hide == False and ob.layers[0] == True and ob.licalc == 1 and ob.lires == 0]

    if scene.li_display_rp != True or (bpy.context.active_object not in (obcalclist+obreslist) and scene.li_display_sel_only == True)  or scene.frame_current not in range(scene.frame_start, scene.frame_end+1):
        return

    region = context.region
    mid_x = region.width / 2
    mid_y = region.height / 2
    width = region.width
    height = region.height
    fn = scene.frame_current

    if scene.li_display_sel_only == False:
        obd = obreslist if len(obreslist) > 0 else obcalclist
    else:
        obd = [context.active_object]

    for ob in obd:
        faces = [f for f in ob.data.polygons if f.select == True] if len(obreslist) > 0 else [f for f in ob.data.polygons]
        vdone = []
        obm = ob.data
        view_mat = context.space_data.region_3d.perspective_matrix
        ob_mat = ob.matrix_world
        total_mat = view_mat * ob_mat
        blf.size(0, context.scene.li_display_rp_fs, 72)

        def draw_index(r, g, b, index, center):
            vec = total_mat * center
            vec = mathutils.Vector((vec[0] / vec[3], vec[1] / vec[3], vec[2] / vec[3]))
            x = int(mid_x + vec[0] * width / 2)
            y = int(mid_y + vec[1] * height / 2)
            bgl.glColor3f(r, g, b)
            blf.position(0, x, y, 0)
            if x > 100 or y < height - 530:
                blf.draw(0, str(index))

        for f in faces:
            if geonode.cpoint == "0":
                vsum = mathutils.Vector((0, 0, 0))
                for v in f.vertices:
                    vsum = ob.active_shape_key.data[v].co + vsum if len(obreslist) > 0 else ob.data.vertices[v].co + vsum
                fc = vsum/len(f.vertices)
                if not f.hide and f.select:
                    loop_index = f.loop_indices[0]
                    if len(set(obm.vertex_colors[fn].data[loop_index].color[:])) > 1:
                        draw_index(0.0, 0.0, 0.0, int(simnode['minres'][fn] + (1 - (1.333333*colorsys.rgb_to_hsv(obm.vertex_colors[fn].data[loop_index].color[0]/255, obm.vertex_colors[fn].data[loop_index].color[1]/255, obm.vertex_colors[fn].data[loop_index].color[2]/255)[0]))*(simnode['maxres'][fn] - simnode['minres'][fn])), fc.to_4d())

            elif geonode.cpoint == "1":
                for loop_index in f.loop_indices:
                    v = obm.loops[loop_index].vertex_index
                    vpos = ob.active_shape_key.data[v].co if len(obreslist) > 0 else obm.vertices[v].co
                    if v not in vdone:
                        vdone.append(v)
                        if len(set(obm.vertex_colors[fn].data[loop_index].color[:])) > 1:
                            draw_index(0.0, 0.0, 0.0, int((1 - (1.333333*colorsys.rgb_to_hsv(obm.vertex_colors[fn].data[loop_index].color[0]/255, obm.vertex_colors[fn].data[loop_index].color[1]/255, obm.vertex_colors[fn].data[loop_index].color[2]/255)[0]))*simnode['maxres'][fn]), vpos.to_4d())

def li3D_legend(self, context, simnode, connode):
    scene = context.scene
    if scene.li_leg_display != True or scene.vi_display == 0:
        return
    else:
        if connode.bl_label == 'LiVi CBDM':
            resvals = ['{:.1f}'.format(min(simnode['minres'])+i*(max(simnode['maxres'])-min(simnode['minres']))/19) for i in range(20)]
        else:
            resvals = [('{:.0f}', '{:.0f}', '{:.1f}')[int(connode.analysismenu)].format(min(simnode['minres'])+i*(max(simnode['maxres'])-min(simnode['minres']))/19) for i in range(20)]
        height = context.region.height
        lenres = len(resvals[-1])
        font_id = 0
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_POLYGON)
        bgl.glVertex2i(20, height - 520)
        bgl.glVertex2i(70 + lenres*8, height - 520)
        bgl.glVertex2i(70 + lenres*8, height - 40)
        bgl.glVertex2i(20, height - 40)
        bgl.glEnd()
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINE_LOOP)
        bgl.glVertex2i(19, height - 520)
        bgl.glVertex2i(70 + lenres*8, height - 520)
        bgl.glVertex2i(70 + lenres*8, height - 40)
        bgl.glVertex2i(19, height - 40)
        bgl.glEnd()

        for i in range(20):
            h = 0.75 - 0.75*(i/19)
            bgl.glColor4f(colorsys.hsv_to_rgb(h, 1.0, 1.0)[0], colorsys.hsv_to_rgb(h, 1.0, 1.0)[1], colorsys.hsv_to_rgb(h, 1.0, 1.0)[2], 1.0)
            bgl.glBegin(bgl.GL_POLYGON)
            bgl.glVertex2i(20, (i*20)+height - 460)
            bgl.glVertex2i(60, (i*20)+height - 460)
            bgl.glVertex2i(60, (i*20)+height - 440)
            bgl.glVertex2i(20, (i*20)+height - 440)
            bgl.glEnd()
            blf.position(font_id, 65, (i*20)+height - 455, 0)
            blf.size(font_id, 20, 48)
            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
            blf.draw(font_id, "  "*(lenres - len(resvals[i]) ) + resvals[i])

        blf.position(font_id, 25, height - 57, 0)
        blf.size(font_id, 20, 56)
        blf.draw(font_id, connode.unit)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)

        height = context.region.height
        font_id = 0
        if context.scene.frame_current in range(context.scene.frame_start, context.scene.frame_end + 1):
            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
            blf.position(font_id, 22, height - 480, 0)
            blf.size(font_id, 20, 48)
            blf.draw(font_id, "Ave: {:.1f}".format(simnode['avres'][context.scene.frame_current]))
            blf.position(font_id, 22, height - 495, 0)
            blf.draw(font_id, "Max: {:.1f}".format(simnode['maxres'][context.scene.frame_current]))
            blf.position(font_id, 22, height - 510, 0)
            blf.draw(font_id, "Min: {:.1f}".format(simnode['minres'][context.scene.frame_current]))

def li_compliance(self, context, connode):
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

    height = context.region.height
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_POLYGON)
    bgl.glVertex2i(100, height - 65)
    bgl.glVertex2i(900, height - 65)
    bgl.glVertex2i(900, height - 40)
    bgl.glVertex2i(100, height - 40)
    bgl.glEnd()
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    horpos = (100, 317, 633, 900)
    widths = (100, 450, 600, 750, 900)

    for p in range(3):
        bgl.glBegin(bgl.GL_LINE_LOOP)
        bgl.glVertex2i(horpos[p], height - 65)
        bgl.glVertex2i(horpos[p+1], height - 65)
        bgl.glVertex2i(horpos[p+1], height - 40)
        bgl.glVertex2i(horpos[p], height - 40)
        bgl.glEnd()

    font_id = 0
    blf.position(font_id, 110, height - 58, 0)
    blf.size(font_id, 20, 54)

    blf.draw(font_id, 'Standard: '+('BREEAM HEA1', 'CfSH', 'LEED EQ8.1', 'Green Star')[int(connode.analysismenu)])
    blf.position(font_id, 643, height - 58, 0)
    blf.draw(font_id, 'Project Name: '+scene.li_projname)
    blf.size(font_id, 20, 40)

    def space_compliance(geos):
        frame = scene.frame_current
        buildspace =''
        pfs = []
        epfs = []
        lencrit = 0
        for geo in geos:
            mat = [m for m in geo.data.materials if m.livi_sense][0]
#            if connode.analysismenu == '0':
#                if connode.bambuildmenu == '
            crit = geo['crit']
            cr4 = [('fail', 'pass')[int(com)] for com in geo['comps'][frame][:][::2]]
            cr6 = [cri[4] for cri in crit]
            if 'fail' in [c for i, c in enumerate(cr4) if cr6[i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                pf = 'FAIL'
            elif 'pass' not in [c for i, c in enumerate(cr4) if cr6[i] == '0.75'] and len([c for i, c in enumerate(cr4) if cr6[i] == '0.75']) > 0:
                if 'pass' not in [c for i, c in enumerate(cr4) if cr6[i] == '0.5'] and len([c for i, c in enumerate(cr4) if cr6[i] == '0.5']) > 0:
                    pf = 'FAIL'
                else:
                    pf = 'PASS'
            else:
                pf = 'PASS'
            pfs.append(pf)

            if connode.analysismenu == '1':
                cfshpfsdict[('totkit', 'totliv')[mat.rspacemenu == '1']] += 1
                if cr4[0] == 'pass':
                    cfshpfsdict[('kitdf', 'livdf')[mat.rspacemenu == '1']] += 1
                if cr4[1] == 'pass':
                    cfshpfsdict[('kitsv', 'livsv')[mat.rspacemenu == '1']] += 1


            if connode.analysismenu == '0':
                ecrit = geo['ecrit']
                ecr4 = [('fail', 'pass')[int(com)] for com in geo['ecomps'][frame][:][::2]]
                ecr6 = [cri[4] for cri in ecrit]
                if 'fail' in [c for i, c in enumerate(ecr4) if ecr6[i] == '1'] or bpy.context.scene['dfpass'][frame] == 1:
                    epf = 'FAIL'
                elif 'pass' not in [c for i, c in enumerate(ecr4) if ecr6[i] == '0.75'] and len([c for i, c in enumerate(ecr4) if ecr6[i] == '0.75']) > 0:
                    if 'pass' not in [c for i, c in enumerate(ecr4) if ecr6[i] == '0.5'] and len([c for i, c in enumerate(ecr4) if ecr6[i] == '0.5']) > 0:
                        epf = 'FAIL'
                    else:
                        epf = 'EXEMPLARY'
                else:
                    epf = 'EXEMPLARY'
                epfs.append(epf)

            if geo == bpy.context.active_object:
                lencrit = 1 + len(geo['crit'])
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
                bgl.glBegin(bgl.GL_POLYGON)
                bgl.glVertex2i(100, height - 70 - (lencrit)*25)
                bgl.glVertex2i(900, height - 70 - (lencrit)*25)
                bgl.glVertex2i(900, height - 70)
                bgl.glVertex2i(100, height - 70)
                bgl.glEnd()

                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                bgl.glLineWidth(1)
                bgl.glBegin(bgl.GL_LINE_LOOP)
                bgl.glVertex2i(100, height - 70 - (lencrit)*25)
                bgl.glVertex2i(900, height - 70 - (lencrit)*25)
                bgl.glVertex2i(900, height - 70)
                bgl.glVertex2i(100, height - 70)
                bgl.glEnd()
                bgl.glDisable(bgl.GL_BLEND)

                mat = [m for m in bpy.context.active_object.data.materials if m.livi_sense][0]
                if connode.analysismenu == '0':
                    if connode.bambuildmenu == '2':
                        buildspace = (' - Public/Staff', ' - Patient')[int(mat.hspacemenu)]
                    elif connode.bambuildmenu == '3':
                        buildspace = (' - Kitchen', ' - Living/Dining/Study', ' - Communal')[int(mat.rspacemenu)]
                    elif connode.bambuildmenu == '4':
                        buildspace = (' - Sales', ' - Office')[int(mat.respacemenu)]
                elif connode.analysismenu == '1':
                    buildspace = (' - Kitchen', ' - Living/Dining/Study')[int(mat.rspacemenu)]


                titles = ('Zone Metric', 'Target', 'Achieved', 'PASS/FAIL')
                tables = [[] for c in range(lencrit -1 )]
                etables = [[] for e in range(len(geo['ecrit']))]
                for c, cr in enumerate(crit):
                    if cr[0] == 'Percent':
                        tables[c] = ('{} (%)'.format(('Percentage area with Skyview', 'Average{}Daylight Factor'.format((' ', ' Point ')[cr[2] == 'PDF']))[cr[2] in ('DF', 'PDF')]), (cr[1],cr[3])[cr[2] in ('PDF','DF')], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), cr4[c].upper())
                    elif cr[0] == 'Ratio':
                        tables[c] = ('Uniformity ratio', cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), cr4[c].upper())
                    elif cr[0] == 'Min':
                        tables[c] = ('Minimum {} (%)'.format('Point Daylight Factor'), cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), cr4[c].upper())
                    elif cr[0] == 'Average':
                        tables[c] = ('Average {} (%)'.format('Daylight Factor'), cr[3], '{:.2f}'.format(geo['comps'][frame][:][c*2 + 1]), cr4[c].upper())
                if connode.analysismenu == '0':
                    for e, ecr in enumerate(ecrit):
                        if ecr[0] == 'Percent':
                            etables[e] = ('{} (%)'.format('Average Daylight Factor'), ecr[3], '{:.2f}'.format(geo['ecomps'][frame][:][e*2 + 1]), ecr4[e].upper())
                        elif ecr[0] == 'Min':
                            etables[e] = ('Minimum {} (%)'.format('Point Daylight Factor'), ecr[3], '{:.2f}'.format(geo['ecomps'][frame][:][e*2 + 1]), ecr4[e].upper())

                for j in range(4):
                    bgl.glBegin(bgl.GL_LINE_LOOP)
                    bgl.glVertex2i(widths[j], height - 95)
                    bgl.glVertex2i(widths[j+1], height - 95)
                    bgl.glVertex2i(widths[j+1], height - 70)
                    bgl.glVertex2i(widths[j], height - 70)
                    bgl.glEnd()

                bgl.glEnable(bgl.GL_LINE_STIPPLE)
                for t, tab in enumerate(tables):
                    for j in range(4):
                        bgl.glBegin(bgl.GL_LINE_LOOP)
                        bgl.glVertex2i(widths[j], height - 120 - t*25)
                        bgl.glVertex2i(widths[j+1], height - 120 - t*25)
                        bgl.glVertex2i(widths[j+1], height - 95 - t*25)
                        bgl.glVertex2i(widths[j], height - 95 - t*25)
                        bgl.glEnd()
                        if tab[j] == 'FAIL':
                            bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                        elif tab[j] == 'PASS':
                            bgl.glColor4f(0.0, 0.7, 0.0, 1.0)
                        blf.size(font_id, 20, 44)
                        blf.position(font_id, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], height - 113 - t*25, 0)
                        blf.draw(font_id, tab[j])
                        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                        if t == 0:
                            blf.size(font_id, 20, 48)
                            blf.position(font_id, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], height - 88, 0)
                            blf.draw(font_id, titles[j])
                bgl.glDisable(bgl.GL_LINE_STIPPLE)
            else:
                etables = []
                lencrit = -2

        tpf = 'FAIL' if 'FAIL' in pfs or 'FAIL*' in pfs else 'PASS'
        if connode.analysismenu == '0':
            (tpf, lencrit) = ('EXEMPLARY', lencrit + len(geo['ecrit'])) if tpf == 'PASS' and ('FAIL' not in epfs or 'FAIL*' not in epfs) else (tpf, lencrit)

        return(tpf, lencrit, buildspace, etables)

    build_compliance, lencrit, bs, etables = space_compliance([geo for geo in bpy.data.objects if geo.type == 'MESH' and True in [m.livi_sense for m in geo.data.materials]])

    if build_compliance == 'EXEMPLARY':

        for t, tab in enumerate(etables):
            if t == 0:
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
                bgl.glBegin(bgl.GL_POLYGON)
                bgl.glVertex2i(100, height - 70 - ((lencrit - len(etables)) * 25))
                bgl.glVertex2i(900, height - 70 - ((lencrit - len(etables)) * 25))
                bgl.glVertex2i(900, height - 70 - (lencrit * 25))
                bgl.glVertex2i(100, height - 70 - (lencrit * 25))
                bgl.glEnd()
                bgl.glBegin(bgl.GL_LINE_LOOP)
                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
                bgl.glVertex2i(100, height - 70 - (lencrit * 25))
                bgl.glVertex2i(900, height - 70 - (lencrit * 25))
                bgl.glVertex2i(900, height - 70 - ((lencrit - len(etables)) * 25))
                bgl.glVertex2i(100, height - 70 - ((lencrit - len(etables)) * 25))
                bgl.glEnd()
                bgl.glDisable(bgl.GL_BLEND)

            for j in range(4):
                bgl.glEnable(bgl.GL_LINE_STIPPLE)
                bgl.glBegin(bgl.GL_LINE_LOOP)
                bgl.glVertex2i(widths[j], height - 120 - (lencrit - len(etables) + t - 1) * 25)
                bgl.glVertex2i(widths[j+1], height - 120 - (lencrit - len(etables) + t - 1) * 25)
                bgl.glVertex2i(widths[j+1], height - 95 - (lencrit - len(etables) + t - 1) * 25)
                bgl.glVertex2i(widths[j], height - 95 - (lencrit - len(etables) + t - 1) * 25)
                bgl.glEnd()
                if tab[j] == 'FAIL':
                    bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
                elif tab[j] == 'PASS':
                    bgl.glColor4f(0.0, 1.0, 0.0, 1.0)
                blf.size(font_id, 20, 44)
                blf.position(font_id, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], height - 113 - (lencrit - len(etables) + t - 1) * 25, 0)
                bgl.glColor4f(0.0, 0.7, 0.0, 1.0)
                blf.draw(font_id, tab[j])
                bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#                if t == 0:
#                    blf.size(font_id, 20, 48)
#                    blf.position(font_id, widths[j]+(25, 50)[j != 0]+(0, 10)[j in (1, 3)], height - 88, 0)
#                    blf.draw(font_id, titles[j])
                bgl.glDisable(bgl.GL_LINE_STIPPLE)

    blf.position(font_id, 327, height - 58, 0)
    blf.size(font_id, 20, 54)
    blf.draw(font_id, 'Buildtype: '+buildtype+bs)

    vi_func.drawpoly(lencrit, height, 100, 50, 525, 75)
    vi_func.drawloop(lencrit, height, 100, 50, 350, 75)
    vi_func.drawloop(lencrit, height, 350, 50, 525, 75)
#    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
#    bgl.glVertex2i(100, height - 75 - (1+lencrit)*25)
#    bgl.glVertex2i(350, height - 75 - (1+lencrit)*25)
#    bgl.glVertex2i(350, height - 50 - (1+lencrit)*25)
#    bgl.glVertex2i(100, height - 50 - (1+lencrit)*25)
#    bgl.glEnd()
#    bgl.glBegin(bgl.GL_LINE_LOOP)
#    bgl.glVertex2i(350, height - 75 - (1+lencrit)*25)
#    bgl.glVertex2i(525, height - 75 - (1+lencrit)*25)
#    bgl.glVertex2i(525, height - 50 - (1+lencrit)*25)
#    bgl.glVertex2i(350, height - 50 - (1+lencrit)*25)
#    bgl.glEnd()

    blf.size(font_id, 20, 52)
    blf.position(font_id, 110, height - 67 - (1+lencrit)*25, 0)
    blf.draw(font_id, 'Building Compliance:')
    blf.position(font_id, 250, height - 67 - (1+lencrit)*25, 0)
    blf.draw(font_id,  build_compliance)
    blf.position(font_id, 360, height - 67 - (1+lencrit)*25, 0)
    blf.draw(font_id, 'Credits achieved:')
    blf.position(font_id, 480, height - 67 - (1+lencrit)*25, 0)

    if connode.analysismenu == '0':
        if build_compliance == 'PASS':
           blf.draw(font_id,  ('1', '2', '2', '1', '1', '1')[int(connode.bambuildmenu)])
        elif build_compliance == 'EXEMPLARY':
            blf.draw(font_id,  ('2', '3', '3', '2', '2', '2')[int(connode.bambuildmenu)])
        else:
            blf.draw(font_id, '0')

    if connode.analysismenu == '1':
        cfshcred = 0
        if cfshpfsdict['kitdf'] == cfshpfsdict['totkit']:
            cfshcred += 1
        if cfshpfsdict['livdf'] == cfshpfsdict['totliv']:
            cfshcred += 1
        if cfshpfsdict['kitsv'] == cfshpfsdict['totkit'] and cfshpfsdict['livsv'] == cfshpfsdict['totliv']:
            cfshcred += 1
        blf.draw(font_id, '{} of {}'.format(cfshcred, '3' if 0 not in (cfshpfsdict['totkit'], cfshpfsdict['totliv']) else '2'))


    elif connode.analysismenu == '1':
        if build_compliance == 'PASS':
            blf.draw(font_id,  '3')
        else:
            blf.draw(font_id,  '0')

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    bgl.glLineWidth(1)

    bgl.glBegin(bgl.GL_POLYGON)
    bgl.glVertex2i(100, 25)
    bgl.glVertex2i(900, 25)
    bgl.glVertex2i(900, 50)
    bgl.glVertex2i(100, 50)
    bgl.glEnd()
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2i(100, 50)
    bgl.glVertex2i(387, 50)
    bgl.glVertex2i(387, 25)
    bgl.glVertex2i(100, 25)
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2i(387, 50)
    bgl.glVertex2i(693, 50)
    bgl.glVertex2i(693, 25)
    bgl.glVertex2i(387, 25)
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2i(693, 50)
    bgl.glVertex2i(900, 50)
    bgl.glVertex2i(900, 25)
    bgl.glVertex2i(693, 25)
    bgl.glEnd()
    blf.size(font_id, 20, 44)
    blf.position(font_id, 110, 32, 0)
    blf.draw(font_id, 'Assessing Organisation:')
    blf.position(font_id, 265, 32, 0)
    blf.draw(font_id, scene.li_assorg)
    blf.position(font_id, 397, 32, 0)
    blf.draw(font_id, 'Assessing Individual:')
    blf.position(font_id, 527, 32, 0)
    blf.draw(font_id, scene.li_assind)
    blf.position(font_id, 703, 32, 0)
    blf.draw(font_id, 'Job Number:')
    blf.position(font_id, 785, 32, 0)
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