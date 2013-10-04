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

import bpy, os, subprocess, colorsys, sys, datetime
from math import pi
from subprocess import PIPE, Popen, STDOUT
from . import vi_func
from . import livi_export

try:
    import numpy
    np = 1
except:
    np = 0

def radfexport(scene, export_op, connode, geonode):
    for frame in range(scene.frame_start, scene.frame_end + 1):
        livi_export.fexport(scene, frame, export_op, connode, geonode)

def rad_prev(prev_op, simnode, connode, geonode, simacc):
    scene = bpy.context.scene
    if simnode.simacc == ("1", "3")[connode.bl_label == 'LiVi Basic']:
        params = simnode.cusacc
    else:
        num = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-ar", 128, 512, 1024), ("-as", 128, 512, 1024), ("-aa", 0.3, 0.15, 0.08), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.01, 0.002))
        params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(simnode.simacc)+1] for n in num]))

    if os.path.isfile(geonode.filebase+"-0.rad"):
        cam = scene.camera
        if cam != None:
            cang = 180 if 'VI Glare' == connode.bl_label else cam.data.angle*180/pi
            vv = 180 if 'VI Glare' == connode.bl_label else cang * scene.render.resolution_y/scene.render.resolution_x
            rvucmd = "rvu -w -n {0} -vv {1:.3f} -vh {2:.3f} -vd {3[0][2]:.3f} {3[1][2]:.3f} {3[2][2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct &".format(geonode.nproc, vv, cang, -1*cam.matrix_world, cam.location, params, geonode.filebase, scene.frame_current)
            rvurun = Popen(rvucmd, shell = True, stdout=PIPE, stderr=STDOUT)
            for l,line in enumerate(rvurun.stdout):
                if 'octree stale?' in line.decode():
                    radfexport(scene, prev_op, simnode, connode, geonode)
                    rad_prev(prev_op, simnode, connode, geonode)
                    return
        else:
            prev_op.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
    else:
        prev_op.report({'ERROR'},"Missing export file. Make sure you have exported the scene.")

def li_calc(calc_op, simnode, connode, geonode, simacc):
    scene = bpy.context.scene
    if os.lstat(geonode.filebase+".rtrace").st_size == 0:
        calc_op.report({'ERROR'},"There are no materials with the livi sensor option enabled")
    else:
        if simacc == ("0", "3")[connode.bl_label == 'LiVi Basic']:
            params = simnode.cusacc
        else:
            num = (("-ab", 2, 3, 4), ("-ad", 256, 512, 2048), ("-ar", 128, 256, 512), ("-as", 128, 256, 512), ("-aa", 0.3, 0.15, 0.08), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 2, 3), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.01, 0.002))
            params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(simacc)+1] for n in num]))
        vi_func.clearscened(scene)
        res = svres = [[0 for p in range(geonode.reslen)] for x in range(scene.frame_end + 1 - scene.frame_start)]
        for frame in range(scene.frame_start, scene.frame_end+1):
            if os.path.isfile("{}-{}.af".format(geonode.filebase, frame)):
                subprocess.call("{} {}-{}.af".format(geonode.rm, geonode.filebase, frame), shell=True)
            rtcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, params, geonode.filebase, frame, connode.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
            print(rtcmd, '-af {2}-{3}.af '.format('','','','',''))
            rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)
            resfile = open(os.path.join(geonode.newdir, connode.resname+"-"+str(frame)+".res"), 'w')
            for l,line in enumerate(rtrun.stdout):
                if 'octree stale?' in line.decode():
                    resfile.close()
                    radfexport(scene, calc_op, connode, geonode)
                    li_calc(calc_op, simnode, connode, geonode)
                    return
                res[frame][l] = float(line.decode())
            resfile.write("{}".format(res[frame]).strip("]").strip("["))
            resfile.close()
            if connode.bl_label == 'LiVi Compliance':
                if connode.analysismenu in ('0', '1'):
                    svcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, '-ab 1 -ad 512 -aa 0.15 -ar 256 -as 256', geonode.filebase, frame, connode.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                    svrun = Popen(svcmd, shell = True, stdout=PIPE, stderr=STDOUT)
                    svresfile = open(os.path.join(geonode.newdir,'skyview'+"-"+str(frame)+".res"), 'w')
                    for sv,line in enumerate(svrun.stdout):
                        svres[frame][sv] = float(line.decode())
                    svresfile.write("{}".format(svres[frame]).strip("]").strip("["))
                    svresfile.close()

        simnode['maxres'] = [max(res[i]) for i in range(scene.frame_end + 1 - scene.frame_start)]
        simnode['minres'] = [min(res[i]) for i in range(scene.frame_end + 1 - scene.frame_start)]
        simnode['avres'] = [sum(res[i])/len(res[i]) for i in range(scene.frame_end + 1 - scene.frame_start)]
        resapply(res, svres, simnode, connode, geonode)
        calc_op.report({'INFO'}, "Calculation is finished.")

def resapply(res, svres, simnode, connode, geonode):
    crits = []
    scene = bpy.context.scene
    dfpass = [0 for f in range(scene.frame_start, scene.frame_end+1)]

    for frame in range(scene.frame_start, scene.frame_end+1):
        dftotarea = dfpassarea = 0
        rgb = []
        lcol_i = []
        mcol_i = 0
        f = 0
        for i in range(0, len(res[frame])):
            h = 0.75*(1-(res[frame][i]-min(simnode['minres']))/(max(simnode['maxres']) + 0.01 - min(simnode['minres'])))
            rgb.append(colorsys.hsv_to_rgb(h, 1.0, 1.0))
        if bpy.context.active_object and bpy.context.active_object.hide == 'False':
            bpy.ops.object.mode_set()

        for geo in [geo for geo in scene.objects if geo.type == 'MESH']:
            bpy.ops.object.select_all(action = 'DESELECT')
            scene.objects.active = None
            if geo.licalc == 1:
                geoarea = sum([vi_func.triarea(geo, face) for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense])
#                totarea += geoarea
                passarea = 0
                scene.objects.active = geo
                geo.select = True
                if frame == 0:
                    while len(geo.data.vertex_colors) > 0:
                        bpy.ops.mesh.vertex_color_remove()
                    while geo.data.shape_keys:
                        bpy.ops.mesh.shape_keys_remove()

                bpy.ops.mesh.vertex_color_add()
                geo.data.vertex_colors[frame].name = str(frame)
                vertexColour = geo.data.vertex_colors[frame]

                mat = [matslot.material for matslot in geo.material_slots if matslot.material.livi_sense][0]
                mcol_i = len(tuple(set(lcol_i)))

                for face in geo.data.polygons:
                    if geo.data.materials[face.material_index].livi_sense:
                        if geonode.cpoint == '1':
                            cvtup = tuple(geo['cverts'])
                            for loop_index in face.loop_indices:
                                v = geo.data.loops[loop_index].vertex_index
                                if v in cvtup:
                                    col_i = cvtup.index(v)
                                lcol_i.append(col_i)
                                vertexColour.data[loop_index].color = rgb[col_i+mcol_i]

                        if geonode.cpoint == '0':
                            for loop_index in face.loop_indices:
                                vertexColour.data[loop_index].color = rgb[f]
                            f += 1

                if connode.bl_label == 'LiVi Compliance':
                    if frame == 0:
                        geo['crit'] = crit = []
                        comps = [[] * f for f in range(scene.frame_start, scene.frame_end+1)]
#                        crit = ['foo']
                        if connode.analysismenu == '0':
                            if connode.bambuildmenu in ('0', '5'):
                                crit.append(['Percent', 80, 'DF', 2, '1'])
                                crit.append(['Ratio', 100, 'Uni', 0.4, '0.5'])
                                crit.append(['Min', 100, 'PDF', 0.8, '0.5'])
                                crit.append(['Percent', 100, 'Skyview', 1, '0.75'])
                            elif connode.bambuildmenu == '1':
                                crit.append(['Percent', 60, 'DF', 2, '1'])
                                crit.append(['Percent', 80, 'DF', 2, '1'])
                            elif connode.bambuildmenu == '2':
                                if mat.hspacemenu == '0':
                                    crit.append(['Percent', 60, 'DF', 2, '1'])
                                    crit.append(['Percent', 80, 'DF', 2, '1'])
                                else:
                                    crit.append(['Percent', 80, 'DF', 3, '2'])

                            elif connode.bambuildmenu == '3':
                                if mat.rspacemenu == '0':
                                    crit.append(['Percent', 80, 'DF', 2, '1'])
                                    crit.append(['Percent', 100, 'Skyview', 1, '0.75'])
                                elif mat.rspacemenu == '1':
                                    crit.append(['Percent', 80, 'DF', 1.5, '1'])
                                    crit.append(['Percent', 100, 'Skyview', 1, '0.75'])
                                elif mat.rspacemenu == '2':
                                    if not mat.gl_roof:
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                        crit.append(['Ratio', 100, 'Uni', 0.4, '0.5'])
                                        crit.append(['Min', 100, 'PDF', 0.8, '0.5'])
                                        crit.append(['Percent', 80, 'Skyview', 1, '0.75'])
                                    else:
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                        crit.append(['Ratio', 100, 'Uni', 0.7, '0.5'])
                                        crit.append(['Min', 100, 'PDF', 1.4, '0.5'])
                                        crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                            elif connode.bambuildmenu == '4':
                                if mat.respacemenu == '0':
                                    crit.append(['Percent', 35, 'PDF', 2, '1'])
                                if mat.respacemenu == '1':
                                    crit.append(['Percent', 80, 'DF', 2, '0.5'])
                                    crit.append(['Ratio', 100, 'Uni', 0.4, '0.5'])
                                    crit.append(['Min', 100, 'PDF', 0.8, '0.5'])
                                    crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                        elif connode.analysismenu == '1':
                            if mat.rspacemenu == '0':
                                crit.append(['Percent', 80, 'DF', 2, '1'])
                                crit.append(['Percent', 100, 'Skyview', 1, '0.75'])
                            elif mat.rspacemenu == '1':
                                crit.append(['Percent', 80, 'DF', 1.5, '1'])
                                crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                        for c in crit:
                            if c[0] == 'Percent':
                                if c[2] == 'DF':
                                    dfpass[frame] = 1
                                    if sum(res[frame])/len(res[frame]) > c[3]:
                                        dfpassarea += geoarea
                                        comps[frame].append(1)
                                    else:
                                        comps[frame].append(0)
                                    comps[frame].append(sum(res[frame])/len(res[frame]))
                                    dftotarea += geoarea

                            for fa, face in enumerate(geo.data.polygons):
                                if geo.data.materials[face.material_index].livi_sense:
                                    if c[0] == 'Percent':
                                        if c[2] == 'Skyview':
                                            if svres[frame][fa] > 0:
                                                passarea += vi_func.triarea(geo, face)


                            if c[0] == 'Percent' and c[2] == 'Skyview':
                                if passarea == geoarea:
                                    comps[frame].append(1)
                                else:
                                    comps[frame].append(0)
                                comps[frame].append(100*passarea/geoarea)
                                passarea = 0

                            if c[0] == 'Min':
                                if min(svres[frame]) > c[3]:
                                    comps[frame].append(1)
                                else:
                                    comps[frame].append(0)
                                comps[frame].append(min(svres[frame]))

                            if c[0] == 'Ratio':
                                if min(res[frame])/(sum(res[frame])/len(res[frame])) >= c[3]:
                                    comps[frame].append(1)
                                else:
                                    comps[frame].append(0)
                                comps[frame].append(min(res[frame])/(sum(res[frame])/len(res[frame])))

                    geo['crit'] = [[c[0], str(c[1]), c[2], str(c[3]), c[4]] for c in crit[:]]
                    geo['comps'] = comps
                    crits.append(geo['crit'])


        if connode.bl_label == 'LiVi Compliance':
            dfpass[frame] = 2 if dfpassarea/dftotarea >= 0.8 else dfpass[frame]

    for frame in range(scene.frame_start, scene.frame_end+1):
        scene.frame_set(frame)
        for geo in scene.objects:
            if geo.licalc == 1:
                for vc in geo.data.vertex_colors:
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


    if connode.bl_label == 'LiVi Compliance':
        scene['crits'] = crits
        scene['dfpass'] = dfpass
#        scene['dfpass'] = 2 if dfpassarea/dftotarea >= 0.8 else scene['dfpass']

    bpy.ops.wm.save_mainfile(check_existing = False)

