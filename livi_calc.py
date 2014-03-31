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

import bpy, os, subprocess, colorsys, datetime
from math import pi
from subprocess import PIPE, Popen, STDOUT
from . import vi_func
from . import livi_export

try:
    import numpy
    np = 1
except:
    np = 0

def radfexport(scene, export_op, connode, geonode, frames):
    for frame in frames:
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
            cang = '180 -vth' if connode.analysismenu == '3' else cam.data.angle*180/pi
            vv = 180 if connode.analysismenu == '3' else cang * scene.render.resolution_y/scene.render.resolution_x
            rvucmd = "rvu -w -n {0} -vv {1} -vh {2} -vd {3[0][2]:.3f} {3[1][2]:.3f} {3[2][2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct &".format(geonode.nproc, vv, cang, -1*cam.matrix_world, cam.location, params, geonode.filebase, scene.frame_current)
            rvurun = Popen(rvucmd, shell = True, stdout=PIPE, stderr=STDOUT)
            for l,line in enumerate(rvurun.stdout):
                if 'octree' in line.decode() or 'mesh' in line.decode():
                    print(line.decode())
                    radfexport(scene, prev_op, connode, geonode, [scene.frame_current])
                    rad_prev(prev_op, simnode, connode, geonode, simacc)
                    return
        else:
            prev_op.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
    else:
        prev_op.report({'ERROR'},"Missing export file. Make sure you have exported the scene.")

def li_calc(calc_op, simnode, connode, geonode, simacc, **kwargs): 
    scene = bpy.context.scene
    frames = range(scene.fs, scene.fe + 1) if not kwargs.get('genframe') else [kwargs['genframe']]
    os.chdir(geonode.newdir)
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode = 'OBJECT')

    if connode.bl_label == 'LiVi CBDM':
        resname = ('kluxhours', 'cumwatth', 'dayauto', 'hourrad', 'udi')[int(connode.analysismenu)]
    elif connode.bl_label == 'LiVi Basic':
        resname = ("illumout", "irradout", "dfout", '')[int(connode.analysismenu)]
    elif connode.bl_label == 'LiVi Compliance':
        resname = 'breaamout' if connode.analysismenu == '0' else 'cfsh'

    if os.lstat(geonode.filebase+".rtrace").st_size == 0:
        calc_op.report({'ERROR'},"There are no materials with the livi sensor option enabled")
    else:
        if simacc == ("0", "3")[connode.bl_label == 'LiVi Basic']:
            simnode['params'] = simnode.cusacc
        else:
            if connode.bl_label == 'LiVi CBDM':
                num = (("-ab", 2, 3, 5), ("-ad", 512, 2048, 4096), ("-ar", 128, 512, 1024), ("-as", 256, 1024, 2048), ("-aa", 0.0, 0.0, 0.0), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 2, 3), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.001, 0.0002))
            else:
                num = (("-ab", 2, 3, 5), ("-ad", 512, 2048, 4096), ("-ar", 128, 512, 1024), ("-as", 256, 1024, 2048), ("-aa", 0.3, 0.2, 0.18), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 2, 3), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.001, 0.0002))
            simnode['params'] = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(simacc)+1] for n in num]))

        if np == 1:
            res, svres = numpy.zeros([len(frames), geonode.reslen]), numpy.zeros([len(frames), geonode.reslen])
        else:
            res, svres = [[[0 for p in range(geonode.reslen)] for x in range(len(frames))] for x in range(2)]

        for frame in frames:            
            findex = frame - scene.fs if not kwargs.get('genframe') else 0
            if connode.bl_label in ('LiVi Basic', 'LiVi Compliance') or (connode.bl_label == 'LiVi CBDM' and int(connode.analysismenu) < 2):
                if os.path.isfile("{}-{}.af".format(geonode.filebase, frame)):
                    subprocess.call("{} {}-{}.af".format(geonode.rm, geonode.filebase, frame), shell=True)
                rtcmd = "rtrace -n {0} -w {1} -faa -h -ov -I {2}-{3}.oct  < {2}.rtrace {4}".format(geonode.nproc, simnode['params'], geonode.filebase, frame, connode.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res"
                rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)
                with open(os.path.join(geonode.newdir, resname+"-"+str(frame)+".res"), 'w') as resfile:
                    for l,line in enumerate(rtrun.stdout):
                        if 'octree' in line.decode() or 'mesh' in line.decode():
                            resfile.close()
                            radfexport(scene, calc_op, connode, geonode, frames)
                            if kwargs.get('genframe'):
                                res = li_calc(calc_op, simnode, connode, geonode, simacc, genframe = kwargs.get('genframe'))
                                return(res)                                
                            else:
                                li_calc(calc_op, simnode, connode, geonode, simacc)
                                return
                        res[findex][l] = float(line.decode())
                    resfile.write("{}".format(res).strip("]").strip("["))
                
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
                hours = 0
                sensarray = [[0 for x in range(146)] for y in range(geonode.reslen)] if np == 0 else numpy.zeros([geonode.reslen, 146])
                oconvcmd = "oconv -w - > {0}-ws.oct".format(geonode.filebase)
                Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = (connode['whitesky']+geonode['radfiles'][frame]).encode('utf-8'))
                senscmd = geonode.cat+geonode.filebase+".rtrace | rcontrib -w  -h -I -fo -bn 146 "+simnode['params']+" -n "+geonode.nproc+" -f tregenza.cal -b tbin -m sky_glow "+geonode.filebase+"-ws.oct"
                sensrun = Popen(senscmd, shell = True, stdout=PIPE)

                for li, line in enumerate(sensrun.stdout):
                    decline = [float(ld) for ld in line.decode().split('\t') if ld != '\n']
                    for v in range(0, 438, 3):
                        if connode.analysismenu in ('2', '4'):
                            sensarray[li][v/3] = 179*((decline[v]*0.265)+ (decline[v+1]*0.67) + (decline[v+2]*0.065))
                        elif connode.analysismenu == '3':
                            sensarray[li][v/3] = sum(decline[v:v+3])

                for l, readings in enumerate(connode['vecvals']):
                    if connode.analysismenu == '3' or (connode.cbdm_start_hour <= readings[:][0] < connode.cbdm_end_hour and readings[:][1] < connode['wd']):
                        finalillu = [0 for x in range(geonode.reslen)] if np == 0 else numpy.zeros((geonode.reslen))
                        for f, fi in enumerate(finalillu):
                            finalillu[f] = numpy.sum([numpy.multiply(sensarray[f], readings[2:])]) if np == 1 else sum([a*b for a,b in zip(sensarray[f],readings[2:])])
                        hours += 1

                        if connode.analysismenu == '2':
                            if np == 1:
                                target = [reading >= connode.dalux for reading in finalillu]
                                res[findex] = numpy.sum([res[findex], target], axis = 0)
                            else:
                                res[findex] = [res[findex][k] + (0, 1)[finalillu[k] >= connode.dalux] for k in range(len(finalillu))]

                        elif connode.analysismenu == '3':
                            if np ==1:
                                if hours == 1:
                                    reswatt = numpy.zeros((len(frames), len(connode['vecvals']), geonode.reslen)) 
                                reswatt[findex][l] = finalillu
                                for i in range(len(finalillu)):
                                    numpy.append(res[findex][i], finalillu[i])                                
                            else:
                                res[findex].append(finalillu)
                            
                        elif connode.analysismenu == '4':
                            if np == 1:
                                target = [connode.daauto >= reading >= connode.dasupp for reading in finalillu]
                                res[findex] = numpy.sum([res[findex], target], axis = 0)
                            else:
                                res[findex] = [res[findex][k] + (0, 1)[connode.daauto >= finalillu[k] >= connode.dasupp] for k in range(len(finalillu))]
                if connode.analysismenu in ('2', '4'):
                    if np == 1 and hours != 0:
                        res[findex] = res[frame]*100/hours
                    elif  np == 0 and hours != 0:
                        res[findex] = [rf*100/hours for rf in res[findex][0]]
                    with open(os.path.join(geonode.newdir, resname+"-"+str(frame)+".res"), "w") as daresfile:
                        [daresfile.write("{:.2f}\n".format(r)) for r in res[findex]]
                
                if connode.analysismenu == '3':
                    res = reswatt

            if connode.analysismenu != '3' or connode.bl_label != 'LiVi CBDM':
                fi, vi = 0, 0       
                for geo in vi_func.retobjs('livic'):
                    obcalcverts, obres = [], []
                    weightres = 0
                    geoarea = sum([vi_func.triarea(geo, face) for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense])
                    for face in [face for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense]:
                        if geonode.cpoint == '1':
                            for v,vert in enumerate(face.vertices):
                                if geo.data.vertices[vert] not in obcalcverts:
                                    weightres += res[findex][vi] 
                                    obres.append(res[findex][vi])
                                    obcalcverts.append(geo.data.vertices[vert])
                                    vi += 1
                        else:
                            weightres += vi_func.triarea(geo, face) * res[findex][fi]/geoarea
                            obres.append(res[findex][fi])
                            fi += 1
        
                    if (frame == scene.fs and not kwargs.get('genframe')) or (kwargs.get('genframe') and kwargs['genframe'] == scene.frame_start):
                        geo['oave'], geo['omax'], geo['omin'], geo['oreslist'] = {}, {}, {}, {}
                    
                    geo['oave'][str(frame)] = weightres
                    geo['omax'][str(frame)] = max(obres)
                    geo['omin'][str(frame)] = min(obres)
                    geo['oreslist'][str(frame)] = obres 
                    
                
        if not kwargs:
            resapply(calc_op, res, svres, simnode, connode, geonode)
            vi_func.vcframe('', scene, [ob for ob in scene.objects if ob.get('licalc')] , simnode['Animation'])
        else:
            return(res[0])
   
def resapply(calc_op, res, svres, simnode, connode, geonode):
    scene = bpy.context.scene    
    if connode.analysismenu != '3' or connode.bl_label != 'LiVi CBDM':
        if np == 1:
            simnode['maxres'] = [numpy.amax(res[i]) for i in range(scene.fs, scene.fe + 1)]
            simnode['minres'] = [numpy.amin(res[i]) for i in range(scene.fs, scene.fe + 1)]
            simnode['avres'] = [numpy.average(res[i]) for i in range(scene.fs, scene.fe + 1)]
        else:
            simnode['maxres'] = [max(res[i]) for i in range(scene.fs, scene.fe + 1)]
            simnode['minres'] = [min(res[i]) for i in range(scene.fs, scene.fe + 1)]
            simnode['avres'] = [sum(res[i])/len(res[i]) for i in range(scene.fs, scene.fe + 1)]
    
        crits = []
    #    fs, fc = scene.frame_start, scene.frame_current
        dfpass = [0 for f in range(scene.fs, scene.fe + 1)]
    #    frames = vi_func.framerange(scene, simnode['Animation'])
    #    frameisg = frameis if not gen else range(gen, gen + 1)
    #    
        for fr, frame in enumerate(range(scene.fs, scene.fe + 1)):
            scene.frame_set(frame)
            fi = 0
            dftotarea, dfpassarea, edftotarea, mcol_i, f, fstart, fsv, sof, eof = 0, 0, 0, 0, 0, 0, 0, 0, 0
            rgb, lcol_i = [], []
            if connode.bl_label != 'LiVi CBDM' or connode.analysismenu != '3':
                for i in range(len(res[fr])):
                    h = 0.75*(1-(res[fr][i]-min(simnode['minres']))/(max(simnode['maxres']) + 0.01 - min(simnode['minres'])))
                    rgb.append(colorsys.hsv_to_rgb(h, 1.0, 1.0))
        
            if bpy.context.active_object and bpy.context.active_object.hide == 'False':
                bpy.ops.object.mode_set()
        
            for geo in vi_func.retobjs('livic'):
                bpy.ops.object.select_all(action = 'DESELECT')
                scene.objects.active = None
                geoarea = sum([vi_func.triarea(geo, face) for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense])
                geofaces = [face for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense]

                if geo.get('wattres'):
                    del geo['wattres']
                
                fend = f + len(geofaces)
                passarea = 0
                vi_func.selobj(scene, geo)
                bpy.ops.mesh.vertex_color_add()
                geo.data.vertex_colors[-1].name = str(frame)
                vertexColour = geo.data.vertex_colors[-1]
                mat = [matslot.material for matslot in geo.material_slots if matslot.material.livi_sense][0]
                mcol_i = len(tuple(set(lcol_i)))

                for face in [face for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense]:
                    if geonode.cpoint == '1':
                        cvtup = tuple(geo['cverts'])
                        for loop_index in face.loop_indices:
                            v = geo.data.loops[loop_index].vertex_index
                            if v in cvtup:
                                col_i = cvtup.index(v)
                            lcol_i.append(col_i)
                            vertexColour.data[loop_index].color = rgb[col_i+mcol_i]
#                            weightres = res
        
                    if geonode.cpoint == '0':
                        for loop_index in face.loop_indices:
                            vertexColour.data[loop_index].color = rgb[fi]
#                            weightres += vi_func.triarea(geo, face) * res[frame][fi]/geoarea
                        fi += 1

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

                    if fr == 0:
                        crit, ecrit = [], []
                        comps, ecomps =  [[[] * f for f in range(scene.fs, scene.fe + 1)] for x in range(2)]
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
                                    crit.append(['Percent', 80, 'DF', 2, '1'])
#                                    crit.append(['Percent', 80, 'DF', 2, '1'])
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
#                                    crit.append(['Percent', 80, 'DF', 2, '1'])
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
                                    crit.append(['Percent', 80, 'DF', 2, '1'])
#                                    crit.append(['Percent', 80, 'DF', 2, '1'])
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
                                if sum(res[frame][fstart:fend])/(fend - fstart) > c[3]:
                                    dfpassarea += geoarea
                                    comps[frame].append(1)
                                else:
                                    comps[frame].append(0)
                                comps[frame].append(sum(res[frame][fstart:fend])/(fend - fstart))
                                dftotarea += geoarea

#                            elif c[2] == 'PDF':
#                                dfpass[frame] = 1
#                                if sum(svres[frame][fstart:fend])/(fend - fstart) > c[3]:
#                                    dfpassarea += geoarea
#                                    comps[frame].append(1)
#                                else:
#                                    comps[frame].append(0)
#                                comps[frame].append(sum(svres[frame][fstart:fend])/(fend -fstart))
#                                dftotarea += geoarea

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
                            if min(res[frame][fstart:fend]) > c[3]:
                                comps[frame].append(1)
                            else:
                                comps[frame].append(0)
                            comps[frame].append(min(res[frame][fstart:fend]))

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
                            if e[2] == 'DF':
#                                r = res if e[2] == 'DF' else svres
                                dfpass[frame] = 1
                                if sum(res[frame][fstart:fend])/(fend - fstart) > e[3]:
                                    dfpassarea += geoarea
#                                            ecomps[frame].append(1)
#                                        else:
#                                            ecomps[frame].append(0)
                                ecomps[frame].append((0, 1)[sum(res[frame][fstart:fend])/(fend - fstart) > e[3]])
                                ecomps[frame].append(sum(res[frame][fstart:fend])/(fend - fstart))
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

                                if passarea >= e[1] * geoarea/100:
                                    ecomps[frame].append(1)
                                else:
                                    ecomps[frame].append(0)
                                ecomps[frame].append(100*passarea/geoarea)
                                passarea = 0

                        elif e[0] == 'Min':
                            if min(res[frame][fstart:fend]) > e[3]:
                                ecomps[frame].append(1)
                            else:
                                ecomps[frame].append(0)
                            ecomps[frame].append(min(res[frame][fstart:fend]))

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
    
        if connode.bl_label == 'LiVi Compliance': 
            if dfpass[frame] == 1:
                dfpass[frame] = 2 if dfpassarea/dftotarea >= 0.8 else dfpass[frame]
            scene['crits'] = crits
            scene['dfpass'] = dfpass
#        scene['dfpass'] = 2 if dfpassarea/dftotarea >= 0.8 else scene['dfpass']
        simnode.outputs['Data out'].hide = True
    else:
        for fr, frame in enumerate(range(scene.fs, scene.fe + 1)):
            scene.frame_set(frame)
            sof, eof = 0, 0
            for geo in vi_func.retobjs('livic'):
                bpy.ops.object.select_all(action = 'DESELECT')
                scene.objects.active = None
                geoarea = sum([vi_func.triarea(geo, face) for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense])
                geofaces = [face for face in geo.data.polygons if geo.data.materials[face.material_index].livi_sense]
                geo['wattres'] = {str(frame):[0 for x in range(len(res[0]))]}
                faceareas = [vi_func.triarea(geo, fa) for fa in geofaces[sof:eof+len(geofaces)]]
                for i in range(len(res[0])):
                    geo['wattres'][str(frame)][i] = sum([res[fr][i][sof:eof+len(geofaces)][j] * faceareas[j] for j in range(sof, eof+len(geofaces))])
                sof = len(geofaces)
                eof += len(geofaces)
        simnode.outputs['Data out'].hide = False
            
    calc_op.report({'INFO'}, "Calculation is finished.")
    bpy.ops.wm.save_mainfile(check_existing = False)

def li_glare(calc_op, simnode, connode, geonode):
    scene = bpy.context.scene
    cam = scene.camera
    if cam:
        gfiles=[]
        num = (("-ab", 2, 3, 5), ("-ad", 512, 2048, 4096), ("-ar", 128, 512, 1024), ("-as", 256, 1024, 2048), ("-aa", 0.3, 0.2, 0.18), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 2, 3), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.001, 0.0002))
        params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(simnode.simacc)+1] for n in num]))
        
        for frame in range(scene.fs, scene.fe + 1):
            time = datetime.datetime(2014, 1, 1, connode.shour, 0) + datetime.timedelta(connode.sdoy - 1) if connode.animmenu == '0' else \
            datetime.datetime(2014, 1, 1, connode.shour, 0) + datetime.timedelta(connode.sdoy - 1) + datetime.timedelta(hours = connode.interval*(frame-scene.frame_start))
            glarecmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} {3}-{5}.oct | evalglare -c {4}.hdr".format(-1*cam.matrix_world, cam.location, params, geonode.filebase, os.path.join(geonode.newdir, 'glare'+str(frame)), frame)               
            glarerun = Popen(glarecmd, shell = True, stdout = PIPE)
            glaretf = open(geonode.filebase+".glare", "w")
            for line in glarerun.stdout:
                if line.decode().split(",")[0] == 'dgp':
                    glaretext = line.decode().replace(',', ' ').replace("#INF", "").split(' ')                    
                    glaretf.write("{0:0>2d}/{1:0>2d} {2:0>2d}:{3:0>2d}\ndgp: {4:.3f}\ndgi: {5:.3f}\nugr: {6:.3f}\nvcp: {7:.3f}\ncgi: {8:.3f}\nLveil: {9:.3f}\n".format(time.day, time.month, time.hour, time.minute, *[float(x) for x in glaretext[6:12]]))
                    glaretf.close()
            subprocess.call("pcond -u 300 {0}.hdr > {0}.temphdr".format(os.path.join(geonode.newdir, 'glare'+str(frame))), shell=True)
            subprocess.call("{0} {1}.glare | psign -h 32 -cb 0 0 0 -cf 40 40 40 | pcompos {3}.temphdr 0 0 - 800 550 > {3}.hdr" .format(geonode.cat, geonode.filebase, frame, os.path.join(geonode.newdir, 'glare'+str(frame))), shell=True)
            subprocess.call("{} {}.temphdr".format(geonode.rm, os.path.join(geonode.newdir, 'glare'+str(frame))), shell=True)                    
                 
            gfile={"name":"glare"+str(frame)+".hdr"}
            gfiles.append(gfile)
        try:
            scene.sequence_editor.sequences_all["glare{}.hdr".format(scene.fs)]
            bpy.ops.sequencer.refresh_all()
        except:
            bpy.ops.sequencer.image_strip_add( directory = geonode.newdir, \
                files = gfiles, \
                frame_start=0, \
                channel=2, \
                filemode=9)
    else:
        calc_op.report({'ERROR'}, "There is no camera in the scene. Create one for glare analysis")