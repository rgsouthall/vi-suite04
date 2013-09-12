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


import bpy, blf, colorsys, bgl, math, mathutils
from bpy_extras import image_utils
from . import livi_export
from . import vi_func

def li_display(node, geonode):
    scene = bpy.context.scene
    vi_func.clearscened(scene)
    obreslist = []
    obcalclist = []

    if len(bpy.app.handlers.frame_change_pre) == 0:
        bpy.app.handlers.frame_change_pre.append(livi_export.cyfc1)
    o = 0
#    bpy.ops.object.mode_set()
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
                if frame == int(vc.name):
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
            if geo.type == 'MESH' and geo.licalc == 1:
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
                if frame == int(vc.name):
                    vc.active = 1
                    vc.active_render = 1
                    vc.keyframe_insert("active")
                    vc.keyframe_insert("active_render")
                else:
                    vc.active = 0
                    vc.active_render = 0
                    vc.keyframe_insert("active")
                    vc.keyframe_insert("active_render")

#    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.wm.save_mainfile(check_existing = False)
    rendview(1)


#def liextrude():
#    for obj in [obj for obj in bpy.data.objects if obj]


def linumdisplay(disp_op, context, node, geonode):
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

        scene = context.scene

        for f in faces:
            if geonode.cpoint == "0" and node.exported == True:
                vsum = mathutils.Vector((0, 0, 0))
                for v in f.vertices:
                    vsum = ob.active_shape_key.data[v].co + vsum if len(obreslist) > 0 else ob.data.vertices[v].co + vsum
                fc = vsum/len(f.vertices)
                if not f.hide and f.select:
                    loop_index = f.loop_indices[0]
                    if len(set(obm.vertex_colors[fn].data[loop_index].color[:])) > 1:
                        draw_index(0.0, 0.0, 0.0, int(node['minres'][fn] + (1 - (1.333333*colorsys.rgb_to_hsv(obm.vertex_colors[fn].data[loop_index].color[0]/255, obm.vertex_colors[fn].data[loop_index].color[1]/255, obm.vertex_colors[fn].data[loop_index].color[2]/255)[0]))*(node['maxres'][fn] - node['minres'][fn])), fc.to_4d())

            elif geonode.cpoint == "1" and node.exported == True:
                for loop_index in f.loop_indices:
                    v = obm.loops[loop_index].vertex_index
                    vpos = ob.active_shape_key.data[v].co if len(obreslist) > 0 else obm.vertices[v].co
                    if v not in vdone:
                        vdone.append(v)
                        if len(set(obm.vertex_colors[fn].data[loop_index].color[:])) > 1:
                            draw_index(0.0, 0.0, 0.0, int((1 - (1.333333*colorsys.rgb_to_hsv(obm.vertex_colors[fn].data[loop_index].color[0]/255, obm.vertex_colors[fn].data[loop_index].color[1]/255, obm.vertex_colors[fn].data[loop_index].color[2]/255)[0]))*node['maxres'][fn]), vpos.to_4d())

def li3D_legend(self, context, node):
    scene = context.scene
    if scene.li_leg_display != True:
        return
    else:
        resvals = [('{:.0f}', '{:.0f}', '{:.1f}')[int(node.analysismenu)].format(min(node['minres'])+i*(max(node['maxres'])-min(node['minres']))/19) for i in range(20)]
        height = context.region.height
        lenres = len(resvals[-1])
        font_id = 0
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.7)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_POLYGON)
        bgl.glVertex2i(20, height - 520)
        bgl.glVertex2i(70 + lenres*8, height - 520)
        bgl.glVertex2i(70 + lenres*8, height - 40)
        bgl.glVertex2i(20, height - 40)
        bgl.glEnd()
        bgl.glColor4f(0.0, 0.0, 0.0, 0.7)
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
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
        blf.draw(font_id, node.unit)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

        height = context.region.height
        font_id = 0
        if context.scene.frame_current in range(context.scene.frame_start, context.scene.frame_end + 1):
            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
            blf.position(font_id, 22, height - 480, 0)
            blf.size(font_id, 20, 48)
            blf.draw(font_id, "Ave: {:.1f}".format(node['avres'][context.scene.frame_current]))
            blf.position(font_id, 22, height - 495, 0)
            blf.draw(font_id, "Max: {:.1f}".format(node['maxres'][context.scene.frame_current]))
            blf.position(font_id, 22, height - 510, 0)
            blf.draw(font_id, "Min: {:.1f}".format(node['minres'][context.scene.frame_current]))


def li_compliance(self, context, node):
    scene = context.scene
    try:
        if not scene.li_compliance or not bpy.context.active_object['crit']:
            print('hi')
            return
    except:
        print('hi2')
        return

    crit = bpy.context.active_object['crit']
    height = context.region.height
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.7)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_POLYGON)
    bgl.glVertex2i(100, height - 50 - len(crit)*50)
    bgl.glVertex2i(750, height - 50 - len(crit)*50)
    bgl.glVertex2i(750, height - 40)
    bgl.glVertex2i(100, height - 40)
    bgl.glEnd()
    bgl.glColor4f(0.0, 0.0, 0.0, 0.7)
    bgl.glLineWidth(1)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2i(100, height - 50 - len(crit)*50)
    bgl.glVertex2i(750, height - 50 - len(crit)*50)
    bgl.glVertex2i(750, height - 40)
    bgl.glVertex2i(100, height - 40)
    bgl.glEnd()

    buildtype = ('School', 'Higher Education', 'Healthcare', 'Residential', 'Retails')[int(node.bambuildtype)]
    if buildtype == 'School':
        buildspace = 'Classroom'
    elif buildtype == 'Higher Education':
        buildspace = 'General'
#    elif buildtype == 'Healthcare':
#        buildspace = ('Public/Staff', 'Patient')[int(mat.hspacemenu)]
#    elif buildtype == 'Residential':
#        buildspace = ('Kitchen', 'Living/Dining/Study', 'Communal')[int(mat.rspacemenu)]









#        resvals = [('{:.0f}', '{:.0f}', '{:.1f}')[int(node.analysismenu)].format(min(node['minres'])+i*(max(node['maxres'])-min(node['minres']))/19) for i in range(20)]
#        height = context.region.height
#        lenres = len(resvals[-1])
#        font_id = 0
#        bgl.glEnable(bgl.GL_BLEND)
#        bgl.glColor4f(1.0, 1.0, 1.0, 0.7)
#        bgl.glLineWidth(2)
#        bgl.glBegin(bgl.GL_POLYGON)
#        bgl.glVertex2i(20, height - 520)
#        bgl.glVertex2i(70 + lenres*8, height - 520)
#        bgl.glVertex2i(70 + lenres*8, height - 40)
#        bgl.glVertex2i(20, height - 40)
#        bgl.glEnd()
#        bgl.glColor4f(0.0, 0.0, 0.0, 0.7)
#        bgl.glLineWidth(2)
#        bgl.glBegin(bgl.GL_LINE_LOOP)
#        bgl.glVertex2i(19, height - 520)
#        bgl.glVertex2i(70 + lenres*8, height - 520)
#        bgl.glVertex2i(70 + lenres*8, height - 40)
#        bgl.glVertex2i(19, height - 40)
#        bgl.glEnd()
#
#        for i in range(20):
#            h = 0.75 - 0.75*(i/19)
#            bgl.glColor4f(colorsys.hsv_to_rgb(h, 1.0, 1.0)[0], colorsys.hsv_to_rgb(h, 1.0, 1.0)[1], colorsys.hsv_to_rgb(h, 1.0, 1.0)[2], 1.0)
#            bgl.glBegin(bgl.GL_POLYGON)
#            bgl.glVertex2i(20, (i*20)+height - 460)
#            bgl.glVertex2i(60, (i*20)+height - 460)
#            bgl.glVertex2i(60, (i*20)+height - 440)
#            bgl.glVertex2i(20, (i*20)+height - 440)
#            bgl.glEnd()
#            blf.position(font_id, 65, (i*20)+height - 455, 0)
#            blf.size(font_id, 20, 48)
#            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#            blf.draw(font_id, "  "*(lenres - len(resvals[i]) ) + resvals[i])
#        blf.position(font_id, 25, height - 57, 0)
#        blf.size(font_id, 20, 56)
#        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#        blf.draw(font_id, node.unit)
#        bgl.glLineWidth(1)
#        bgl.glDisable(bgl.GL_BLEND)
#        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#
#        height = context.region.height
#        font_id = 0
#        if context.scene.frame_current in range(context.scene.frame_start, context.scene.frame_end + 1):
#            bgl.glColor4f(0.0, 0.0, 0.0, 0.8)
#            blf.position(font_id, 22, height - 480, 0)
#            blf.size(font_id, 20, 48)
#            blf.draw(font_id, "Ave: {:.1f}".format(node['avres'][context.scene.frame_current]))
#            blf.position(font_id, 22, height - 495, 0)
#            blf.draw(font_id, "Max: {:.1f}".format(node['maxres'][context.scene.frame_current]))
#            blf.position(font_id, 22, height - 510, 0)
#            blf.draw(font_id, "Min: {:.1f}".format(node['minres'][context.scene.frame_current]))

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