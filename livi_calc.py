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
    for frame in vi_func.frameindex(scene, connode['Animation']):
        livi_export.fexport(scene, frame, export_op, connode, geonode)

def rad_prev(prev_op, simnode, connode, geonode, simacc):
    scene = bpy.context.scene
    simacc = simnode.simacc if connode.bl_label == 'LiVi Basic' else simnode.csimacc
    if simacc == ("0", "3")[connode.bl_label == 'LiVi Basic']:
        params = simnode.cusacc
    else:
        num = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-ar", 128, 512, 1024), ("-as", 128, 512, 1024), ("-aa", 0.3, 0.15, 0.08), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.01, 0.002))
        params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(simnode.simacc)+1] for n in num]))

    if os.path.isfile("{}-{}.rad".format(geonode.filebase, scene.frame_current)):
        cam = scene.camera
        if cam != None:
            cang = 180 if 'VI Glare' == connode.bl_label else cam.data.angle*180/pi
            vv = 180 if 'VI Glare' == connode.bl_label else cang * scene.render.resolution_y/scene.render.resolution_x
            rvucmd = "rvu -w -n {0} -vv {1:.3f} -vh {2:.3f} -vd {3[0][2]:.3f} {3[1][2]:.3f} {3[2][2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct &".format(geonode.nproc, vv, cang, -1*cam.matrix_world, cam.location, params, geonode.filebase, scene.frame_current)
            rvurun = Popen(rvucmd, shell = True, stdout=PIPE, stderr=STDOUT)
            for l,line in enumerate(rvurun.stdout):
                if 'octree stale?' in line.decode() or 'truncated octree' in line.decode():
                    radfexport(scene, prev_op, connode, geonode)
                    rad_prev(prev_op, simnode, connode, geonode, simacc)
#                    prev_op.report({'ERROR'},"Radiance octree is incomplete. Re-run geometry and context export")
                    return
        else:
            prev_op.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
    else:
        prev_op.report({'ERROR'},"Missing export file. Make sure you have exported the scene.")

def li_calc(calc_op, simnode, connode, geonode, simacc):
    simnode['Animation'] = connode['Animation']
    os.chdir(geonode.newdir)
    scene = bpy.context.scene
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.context.active_object.mode = 'OBJECT'

    if connode.bl_label == 'LiVi CBDM':
        resname = ('kluxhours', 'cumwatth', 'dayauto', 'hourrad', 'udi')[int(connode.analysismenu)]
    elif connode.bl_label == 'LiVi Basic':
        resname = ("illumout", "irradout", "dfout")[int(connode.analysismenu)]
    elif connode.bl_label == 'LiVi Compliance':
        resname = 'breaamout' if connode.analysismenu == '0' else 'cfsh'

    if os.lstat(geonode.filebase+".rtrace").st_size == 0:
        calc_op.report({'ERROR'},"There are no materials with the livi sensor option enabled")
    else:
        if simacc == ("0", "3")[connode.bl_label == 'LiVi Basic']:
            params = simnode.cusacc
        else:
            if connode.bl_label == 'LiVi CBDM':
                num = (("-ab", 2, 3, 5), ("-ad", 512, 2048, 4096), ("-ar", 128, 512, 1024), ("-as", 256, 1024, 2048), ("-aa", 0.0, 0.0, 0.0), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 2, 3), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.001, 0.0002))
            else:
                num = (("-ab", 2, 3, 5), ("-ad", 512, 2048, 4096), ("-ar", 128, 512, 1024), ("-as", 256, 1024, 2048), ("-aa", 0.3, 0.2, 0.18), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 2, 3), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.001, 0.0002))
            params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(simacc)+1] for n in num]))

        vi_func.clearscened(scene)

        if np == 1:
            res, svres = numpy.zeros([len(vi_func.frameindex(scene, connode['Animation'])), geonode.reslen]), numpy.zeros([len(vi_func.frameindex(scene, connode['Animation'])), geonode.reslen])
        else:
            res, svres = [[[0 for p in range(geonode.reslen)] for x in range(len(vi_func.frameindex(scene, connode['Animation'])))] for x in range(2)]

        for frame in vi_func.framerange(scene, connode['Animation']):
            findex = frame - scene.frame_start
            if connode.bl_label in ('LiVi Basic', 'LiVi Compliance') or (connode.bl_label == 'LiVi CBDM' and int(connode.analysismenu) < 2):
                if os.path.isfile("{}-{}.af".format(geonode.filebase, frame)):
                    subprocess.call("{} {}-{}.af".format(geonode.rm, geonode.filebase, frame), shell=True)
#                rtcmd = "rtrace -n {0} -w {1} -faa -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, params, geonode.filebase, frame, connode.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                rtcmd = "rtrace -n {0} -w {1} -faa -h -ov -I {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, params, geonode.filebase, frame, connode.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                print(rtcmd)
                rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)
                with open(os.path.join(geonode.newdir, resname+"-"+str(frame)+".res"), 'w') as resfile:
                    for l,line in enumerate(rtrun.stdout):
                        if 'octree stale?' in line.decode() or 'truncated octree' in line.decode():
                            resfile.close()
                            radfexport(scene, calc_op, connode, geonode)
                            li_calc(calc_op, simnode, connode, geonode, simacc)
                            return
                        res[findex][l] = float(line.decode())
                    resfile.write("{}".format(res[findex]).strip("]").strip("["))

            if connode.bl_label == 'LiVi Compliance' and connode.analysismenu in ('0', '1'):
                if connode.analysismenu in ('0', '1'):
                    svcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, '-ab 1 -ad 8192 -aa 0 -ar 512 -as 1024 -lw 0.0002', geonode.filebase, frame, connode.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                    svrun = Popen(svcmd, shell = True, stdout=PIPE, stderr=STDOUT)
                    with open(os.path.join(geonode.newdir,'skyview'+"-"+str(frame)+".res"), 'w') as svresfile:
                        for sv,line in enumerate(svrun.stdout):
                            svres[findex][sv] = float(line.decode())
                        svresfile.write("{}".format(svres[findex]).strip("]").strip("["))

            if connode.bl_label == 'LiVi CBDM' and int(connode.analysismenu) > 1:
                if connode.sourcemenu == '2':
                    if not connode.get('whitesky'):
                        connode['whitesky'] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"
                    connode['vecvals'], vals = vi_func.mtx2vals(open(connode.vecname, "r"), datetime.datetime(2010, 1, 1).weekday())

                for frame in vi_func.framerange(scene, connode['Animation']):
                    hours = 0
                    sensarray = [[0 for x in range(146)] for y in range(geonode.reslen)] if np == 0 else numpy.zeros([geonode.reslen, 146])
                    if connode.analysismenu == '3':
                        wattres = [[0 for p in range(len(connode['vecvals']))] for x in range(len(vi_func.frameindex(scene, connode['Animation'])))] if np == 0 else numpy.zeros([len(vi_func.frameindex(scene, connode['Animation'])), len(connode['vecvals']), geonode.reslen])
                    oconvcmd = "oconv -w - > {0}-ws.oct".format(geonode.filebase)
                    Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = (connode['whitesky']+geonode['radfiles'][frame]).encode('utf-8'))
                    senscmd = geonode.cat+geonode.filebase+".rtrace | rcontrib -w  -h -I -fo -bn 146 "+params+" -n "+geonode.nproc+" -f tregenza.cal -b tbin -m sky_glow "+geonode.filebase+"-ws.oct"
                    sensrun = Popen(senscmd, shell = True, stdout=PIPE)

                    for l, line in enumerate(sensrun.stdout):
                        decline = [float(ld) for ld in line.decode().split('\t') if ld != '\n']
                        for v in range(0, 438, 3):
                            if connode.analysismenu in ('2', '4'):
                                sensarray[l][v/3] = 179*((decline[v]*0.265)+ (decline[v+1]*0.67) + (decline[v+2]*0.065))
                            elif connode.analysismenu == '3':
                                sensarray[l][v/3] = sum(decline[v:v+3])

                    for l, readings in enumerate(connode['vecvals']):
                        if connode.analysismenu == '3' or (connode.cbdm_start_hour <= readings[:][0] < connode.cbdm_end_hour and readings[:][1] < connode['wd']):
                            finalillu = [0 for x in range(geonode.reslen)] if np == 0 else numpy.zeros((geonode.reslen))
                            for f, fi in enumerate(finalillu):
                                finalillu[f] = numpy.sum([numpy.multiply(sensarray[f], readings[2:])]) if np == 1 else sum([a*b for a,b in zip(sensarray[f],readings[2:])])
                            hours += 1

                            if connode.analysismenu == '2':
                                if np == 1:
                                    target = [reading >= connode.dalux for reading in finalillu]
                                    res[frame] = numpy.sum([res[frame], target], axis = 0)
                                else:
                                    res[frame] = [res[frame][k] + (0, 1)[finalillu[k] >= connode.dalux] for k in range(len(finalillu))]

                            elif connode.analysismenu == '3':
                                wattres[frame][l] = finalillu

                            elif connode.analysismenu == '4':
                                res[frame] = [res[frame][k] + (0, 1)[connode.daauto >= finalillu[k] >= connode.dasupp] for k in range(len(finalillu))]

                    if connode.analysismenu in ('2', '4'):
                        res[frame] = [rf*100/hours for rf in res[frame] if hours != 0]

                        with open(os.path.join(geonode.newdir, resname+"-"+str(frame)+".res"), "w") as daresfile:
                            [daresfile.write("{:.2f}\n".format(r)) for r in res[frame]]

        if connode.analysismenu != '3' or connode.bl_label != 'LiVi CBDM':
            if np == 1:
                simnode['maxres'] = [numpy.amax(res[i]) for i in vi_func.frameindex(scene, connode['Animation'])]
                simnode['minres'] = [numpy.amin(res[i]) for i in vi_func.frameindex(scene, connode['Animation'])]
                simnode['avres'] = [numpy.average(res[i]) for i in vi_func.frameindex(scene, connode['Animation'])]
            else:
                simnode['maxres'] = [max(res[i]) for i in vi_func.frameindex(scene, connode['Animation'])]
                simnode['minres'] = [min(res[i]) for i in vi_func.frameindex(scene, connode['Animation'])]
                simnode['avres'] = [sum(res[i])/len(res[i]) for i in vi_func.frameindex(scene, connode['Animation'])]
            resapply(res, svres, simnode, connode, geonode)

        else:
            resapply(wattres, svres, simnode, connode, geonode)

        calc_op.report({'INFO'}, "Calculation is finished.")

def resapply(res, svres, simnode, connode, geonode):
    crits = []
    scene = bpy.context.scene
    dfpass = [0 for f in vi_func.framerange(scene, connode['Animation'])]

    for frame in vi_func.frameindex(scene, connode['Animation']):
        dftotarea, dfpassarea, edftotarea, mcol_i, f, fstart, fsv, sof, eof = 0, 0, 0, 0, 0, 0, 0, 0, 0
        rgb, lcol_i = [], []
        if connode.bl_label != 'LiVi CBDM' or connode.analysismenu != '3':
            for i in range(0, len(res[frame])):
                h = 0.75*(1-(res[frame][i]-min(simnode['minres']))/(max(simnode['maxres']) + 0.01 - min(simnode['minres'])))
                rgb.append(colorsys.hsv_to_rgb(h, 1.0, 1.0))

        if bpy.context.active_object and bpy.context.active_object.hide == 'False':
            bpy.ops.object.mode_set()

        for geo in vi_func.retobjs('livig'):
            if geo.get('licalc') == 1:
                geo['oave'], geo['omax'], geo['omin'], geo['oreslist'] = {}, {}, {}, {}
                weightres = 0
                bpy.ops.object.select_all(action = 'DESELECT')
                scene.objects.active = None
                geofaces = [face for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense]

                if connode.bl_label == 'LiVi CBDM' and connode.analysismenu == '3':
                    if not geo.get('wattres'):
                        geo['wattres'] = {}
                    geo['wattres'][str(frame)] = [sum(res[frame][i][sof:eof+len(geofaces)]*[vi_func.triarea(geo, f) for f in geofaces[sof:eof+len(geofaces)]]) for i in range(len(res[0]))]
                    sof = len(geofaces)
                    eof += len(geofaces)
                else:
                    if geo.get('wattres'):
                        del geo['wattres']

                    geoarea = sum([vi_func.triarea(geo, face) for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense])
                    fend = f + len(geofaces)
                    passarea = 0
                    scene.objects.active = geo
                    geo.select = True
                    if frame == 0:
                        while geo.data.vertex_colors:
                            bpy.ops.mesh.vertex_color_remove()
                        while geo.data.shape_keys:
                            bpy.ops.mesh.shape_keys_remove()

                    bpy.ops.mesh.vertex_color_add()
                    geo.data.vertex_colors[frame].name = str(frame + scene.frame_start)
                    vertexColour = geo.data.vertex_colors[frame]

                    mat = [matslot.material for matslot in geo.material_slots if matslot.material.livi_sense][0]
                    mcol_i = len(tuple(set(lcol_i)))

                    for face in geofaces:
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
                            weightres += vi_func.triarea(geo, face) * res[frame][f]/geoarea
                            f += 1
                    geo['oave'][str(frame+scene.frame_start)] = weightres
                    geo['omax'][str(frame+scene.frame_start)] = max(res[frame])
                    geo['omin'][str(frame+scene.frame_start)] = min(res[frame])
                    geo['oreslist'][str(frame+scene.frame_start)] = res[frame]

                    if connode.bl_label == 'LiVi Compliance':
                        if connode.analysismenu == '1':
                            bpy.ops.mesh.vertex_color_add()
                            geo.data.vertex_colors[frame+1].name = '{}sv'.format(frame)
                            vertexColour = geo.data.vertex_colors[frame+1]
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

                                    elif geonode.cpoint == '0':
                                        for loop_index in face.loop_indices:
                                            vertexColour.data[loop_index].color = (0, 1, 0) if svres[frame][fsv] > 0 else (1, 0, 0)
                                        fsv += 1

                        if frame == 0:
                            crit, ecrit = [], []
                            comps, ecomps =  [[[] * f for f in range(scene.frame_start, scene.frame_end+1)] for x in range(2)]
#                            ecomps = [[] * f for f in range(scene.frame_start, scene.frame_end+1)]

                            if connode.analysismenu == '0':
                                ecrit = []
                                if connode.bambuildmenu in ('0', '5'):
                                    if not mat.gl_roof:
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                        crit.append(['Ratio', 100, 'Uni', 0.4, '0.5'])
                                        crit.append(['Min', 100, 'PDF', 0.8, '0.5'])
                                        crit.append(['Percent', 80, 'Skyview', 1, '0.75'])

                                        if geonode.buildstorey == '0':
                                            ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.6, '0.75'])

                                        elif geonode.buildstorey == '1':
                                            ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.2, '0.75'])
                                    else:
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                        crit.append(['Ratio', 100, 'Uni', 0.7, '0.5'])
                                        crit.append(['Min', 100, 'PDF', 1.4, '0.5'])
                                        crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                                        if geonode.buildstorey == '0':
                                            ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 2.8, '0.75'])

                                        elif geonode.buildstorey == '1':
                                            ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 2.1, '0.75'])

                                elif connode.bambuildmenu == '1':
                                    if not mat.gl_roof:
                                        crit.append(['Percent', 60, 'DF', 2, '1'])
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                        crit.append(['Ratio', 100, 'Uni', 0.4, '0.5'])
                                        crit.append(['Min', 100, 'PDF', 0.8, '0.5'])
                                        crit.append(['Percent', 80, 'Skyview', 1, '0.75'])

                                        if geonode.buildstorey == '0':
                                            ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.6, '0.75'])

                                        elif geonode.buildstorey == '1':
                                            ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.2, '0.75'])
                                    else:
                                        crit.append(['Percent', 60, 'DF', 2, '1'])
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                        crit.append(['Ratio', 100, 'Uni', 0.7, '0.5'])
                                        crit.append(['Min', 100, 'PDF', 1.4, '0.5'])
                                        crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                                        if geonode.buildstorey == '0':
                                            ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 2.8, '0.75'])

                                        elif geonode.buildstorey == '1':
                                            ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 2.1, '0.75'])

                                elif connode.bambuildmenu == '2':
                                    if mat.hspacemenu == '0':
                                        crit.append(['Percent', 60, 'DF', 2, '1'])
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                    else:
                                        crit.append(['Percent', 80, 'DF', 3, '2'])

                                    if geonode.buildstorey == '0':
                                        ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                        ecrit.append(['Min', 100, 'PDF', 1.6, '0.75'])

                                    elif geonode.buildstorey == '1':
                                        ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                        ecrit.append(['Min', 100, 'PDF', 1.2, '0.75'])

                                elif connode.bambuildmenu == '3':
                                    if mat.rspacemenu == '0':
                                        crit.append(['Percent', 80, 'DF', 2, '1'])
                                        crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                                        if geonode.buildstorey == '0':
                                            ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.6, '0.75'])

                                        elif geonode.buildstorey == '1':
                                            ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.2, '0.75'])

                                    elif mat.rspacemenu == '1':
                                        crit.append(['Percent', 80, 'DF', 1.5, '1'])
                                        crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                                        if geonode.buildstorey == '0':
                                            ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.6, '0.75'])

                                        elif geonode.buildstorey == '1':
                                            ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                            ecrit.append(['Min', 100, 'PDF', 1.2, '0.75'])

                                    elif mat.rspacemenu == '2':
                                        if not mat.gl_roof:
                                            crit.append(['Percent', 80, 'DF', 2, '1'])
                                            crit.append(['Ratio', 100, 'Uni', 0.4, '0.5'])
                                            crit.append(['Min', 100, 'PDF', 0.8, '0.5'])
                                            crit.append(['Percent', 80, 'Skyview', 1, '0.75'])

                                            if geonode.buildstorey == '0':
                                                ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 1.6, '0.75'])

                                            elif geonode.buildstorey == '1':
                                                ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 1.2, '0.75'])
                                        else:
                                            crit.append(['Percent', 80, 'DF', 2, '1'])
                                            crit.append(['Ratio', 100, 'Uni', 0.7, '0.5'])
                                            crit.append(['Min', 100, 'PDF', 1.4, '0.5'])
                                            crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                                            if geonode.buildstorey == '0':
                                                ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 2.8, '0.75'])

                                            elif geonode.buildstorey == '1':
                                                ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 2.1, '0.75'])

                                elif connode.bambuildmenu == '4':
                                    if mat.respacemenu == '0':
                                        crit.append(['Percent', 35, 'PDF', 2, '1'])
                                        ecrit.append(['Percent', 50, 'PDF', 2, '1'])

                                    if mat.respacemenu == '1':
                                        if not mat.gl_roof:
                                            crit.append(['Percent', 80, 'DF', 2, '1'])
                                            crit.append(['Ratio', 100, 'Uni', 0.4, '0.5'])
                                            crit.append(['Min', 100, 'PDF', 0.8, '0.5'])
                                            crit.append(['Percent', 80, 'Skyview', 1, '0.75'])

                                            if geonode.buildstorey == '0':
                                                ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 1.6, '0.75'])

                                            elif geonode.buildstorey == '1':
                                                ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 1.2, '0.75'])
                                        else:
                                            crit.append(['Percent', 80, 'DF', 2, '1'])
                                            crit.append(['Ratio', 100, 'Uni', 0.7, '0.5'])
                                            crit.append(['Min', 100, 'PDF', 1.4, '0.5'])
                                            crit.append(['Percent', 100, 'Skyview', 1, '0.75'])

                                            if geonode.buildstorey == '0':
                                                ecrit.append(['Percent', 80, 'DF', 4, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 2.8, '0.75'])

                                            elif geonode.buildstorey == '1':
                                                ecrit.append(['Percent', 80, 'DF', 3, '1'])
                                                ecrit.append(['Min', 100, 'PDF', 2.1, '0.75'])

                            elif connode.analysismenu == '1':
                                if mat.rspacemenu == '0':
                                    crit.append(['Average', 100, 'DF', 2, '1'])
                                    crit.append(['Percent', 80, 'Skyview', 1, '0.75'])
                                elif mat.rspacemenu == '1':
                                    crit.append(['Average', 100, 'DF', 1.5, '1'])
                                    crit.append(['Percent', 80, 'Skyview', 1, '0.75'])

                            elif connode.analysismenu == '2':
                                crit.append(['Percent', 75, 'FC', 108, '1'])
                                crit.append(['Percent', 75, 'FC', 5400, '1'])
                                crit.append(['Percent', 90, 'FC', 108, '1'])
                                crit.append(['Percent', 90, 'FC', 5400, '1'])

                            for c in crit:
                                if c[0] == 'Percent':
                                    if c[2] == 'DF':
                                        dfpass[frame] = 1
                                        if sum(res[frame][fstart:fend])/(fend -fstart) > c[3]:
                                            dfpassarea += geoarea
                                            comps[frame].append(1)
                                        else:
                                            comps[frame].append(0)
                                        comps[frame].append(sum(res[frame][fstart:fend])/(fend - fstart))
                                        dftotarea += geoarea

                                    elif c[2] == 'PDF':
                                        dfpass[frame] = 1
                                        if sum(svres[frame][fstart:fend])/(fend - fstart) > c[3]:
                                            dfpassarea += geoarea
                                            comps[frame].append(1)
                                        else:
                                            comps[frame].append(0)
                                        comps[frame].append(sum(svres[frame][fstart:fend])/(fend -fstart))
                                        dftotarea += geoarea

                                    elif c[2] == 'Skyview':
                                        for fa, face in enumerate(geofaces):
                                           if svres[frame][fa + fstart] > 0:
                                                passarea += vi_func.triarea(geo, face)
                                        if passarea >= c[1]*geoarea/100:
                                            comps[frame].append(1)
                                        else:
                                            comps[frame].append(0)
                                        comps[frame].append(100*passarea/geoarea)
                                        passarea = 0

                                elif c[0] == 'Min':
                                    if min(svres[frame][fstart:fend]) > c[3]:
                                        comps[frame].append(1)
                                    else:
                                        comps[frame].append(0)
                                    comps[frame].append(min(svres[frame][fstart:fend]))

                                elif c[0] == 'Ratio':
                                    if min(res[frame])/(sum(res[frame][fstart:fend])/len(res[frame])) >= c[3]:
                                        comps[frame].append(1)
                                    else:
                                        comps[frame].append(0)
                                    comps[frame].append(min(res[frame][fstart:fend])/(sum(res[frame])/(fend - fstart)))

                                elif c[0] == 'Average':
                                    if sum([vi_func.triarea(geo, face) * res[frame][fa+fstart] for fa, face in enumerate(geofaces)])/geoarea > c[3]:
                                        comps[frame].append(1)
                                    else:
                                        comps[frame].append(0)
                                    comps[frame].append(sum([vi_func.triarea(geo, face) * res[frame][fa+fstart] for fa, face in enumerate(geofaces)])/geoarea)

                            for e in ecrit:
                                if e[0] == 'Percent':
                                    if e[2] in ('DF', 'PDF'):
                                        r = res if e[2] == 'DF' else svres
                                        dfpass[frame] = 1
                                        if sum(res[frame][fstart:fend])/(fend - fstart) > e[3]:
                                            dfpassarea += geoarea
#                                            ecomps[frame].append(1)
#                                        else:
#                                            ecomps[frame].append(0)
                                        ecomps[frame].append((0, 1)[sum(r[frame][fstart:fend])/(fend - fstart) > e[3]])
                                        ecomps[frame].append(sum(r[frame][fstart:fend])/(fend - fstart))
                                        edftotarea += geoarea


#                                    elif e[2] == 'PDF':
#                                        dfpass[frame] = 1
#                                        if sum(svres[frame][fstart:fend])/(fend - fstart) > e[3]:
#                                            dfpassarea += geoarea
#                                            ecomps[frame].append(1)
#                                        else:
#                                            ecomps[frame].append(0)
#                                        ecomps[frame].append(sum(svres[frame][fstart:fend])/(fend - fstart))
#                                        edftotarea += geoarea


                                    elif e[2] == 'Skyview':
                                        for fa, face in enumerate(geofaces):
                                            if svres[frame][fa] > 0:
                                                passarea += vi_func.triarea(geo, face)

                                        if passarea >= e[1] * geoarea /100:
                                            ecomps[frame].append(1)
                                        else:
                                            ecomps[frame].append(0)
                                        ecomps[frame].append(100*passarea/geoarea)
                                        passarea = 0

                                elif e[0] == 'Min':
                                    if min(svres[frame][fstart:fend]) > e[3]:
                                        ecomps[frame].append(1)
                                    else:
                                        ecomps[frame].append(0)
                                    ecomps[frame].append(min(svres[frame][fstart:fend]))

                                elif e[0] == 'Ratio':
                                    if min(res[frame][fstart:fend])/(sum(res[frame][fstart:fend])/(fend - fstart)) >= e[3]:
                                        ecomps[frame].append(1)
                                    else:
                                        ecomps[frame].append(0)
                                    ecomps[frame].append(min(res[frame][fstart:fend])/(sum(res[frame][fstart:fend])/(fend - fstart)))

                                elif e[0] == 'Average':
                                    if sum(res[frame][fstart:fend])/(fend - fstart) > e[3]:
                                        ecomps[frame].append(1)
                                    else:
                                        ecomps[frame].append(0)
                                    ecomps[frame].append(sum(res[frame][fstart:fend])/(fend - fstart))

                        geo['crit'] = [[c[0], str(c[1]), c[2], str(c[3]), c[4]] for c in crit[:]]
                        geo['ecrit'] = [[c[0], str(c[1]), c[2], str(c[3]), c[4]] for c in ecrit[:]]
                        geo['comps'] = comps
                        geo['ecomps'] = ecomps
                        crits.append(geo['crit'])
                        fstart = fend

        if connode.bl_label == 'LiVi Compliance' and dfpass[frame] == 1:
            dfpass[frame] = 2 if dfpassarea/dftotarea >= 0.8 else dfpass[frame]
    vi_func.vcframe(scene, [ob for ob in scene.objects is ob.get('licalc')] , simnode['Animation'])
#    for frame in vi_func.framerange(scene, simnode['Animation']):
#        scene.frame_set(frame)
#        for geo in scene.objects:
#            if geo.get('licalc') == 1:
#                for vc in geo.data.vertex_colors:
#                    if vc.name == str(frame):
#                        vc.active = 1
#                        vc.active_render = 1
#                        vc.keyframe_insert("active")
#                        vc.keyframe_insert("active_render")
#                    else:
#                        vc.active = 0
#                        vc.active_render = 0
#                        vc.keyframe_insert("active")
#                        vc.keyframe_insert("active_render")


    if connode.bl_label == 'LiVi Compliance':
        scene['crits'] = crits
        scene['dfpass'] = dfpass
#        scene['dfpass'] = 2 if dfpassarea/dftotarea >= 0.8 else scene['dfpass']
    if connode.bl_label == 'LiVi CBDM' and connode.analysismenu == '3':
        simnode.outputs['Data out'].hide = False

    bpy.ops.wm.save_mainfile(check_existing = False)

