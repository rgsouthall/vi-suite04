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
try:
    import numpy
    np = 1
except:
    np = 0
    

def rad_prev(lexport, node, prev_op):
    if node.simacc == "3":
        params = node.cusacc
    else:
        num = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-ar", 128, 512, 1024), ("-as", 128, 512, 1024), ("-aa", 0.3, 0.15, 0.08), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.01, 0.002))
        params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(node.simacc)+1] for n in num]))

    if os.path.isfile(lexport.filebase+"-0.poly"):
        cam = lexport.scene.camera
        if cam != None:
            if 'VI Glare' in node.name:
                cang = 180
                vv = 180
            else:
                cang = cam.data.angle*180/pi
                vv = cang * lexport.scene.render.resolution_y/lexport.scene.render.resolution_x
            subprocess.call("rvu -w -n {0} -vv {1:.3f} -vh {2:.3f} -vd {3[0][2]:.3f} {3[1][2]:.3f} {3[2][2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct &".format(lexport.nproc, vv, cang, -1*cam.matrix_world, cam.location, params, lexport.filebase, lexport.scene.frame_current), shell = True)
        else:
            prev_op.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
    else:
        prev_op.report({'ERROR'},"Missing export file. Make sure you have exported the scene.")


        
def li_calc(lexport, node, calc_op):
    if node.simacc == "3":
        params = node.cusacc
    else:
        num = (("-ab", 2, 3, 4), ("-ad", 256, 1024, 4096), ("-ar", 128, 512, 1024), ("-as", 128, 512, 1024), ("-aa", 0.3, 0.15, 0.08), ("-dj", 0, 0.7, 1), ("-ds", 0, 0.5, 0.15), ("-dr", 1, 3, 5), ("-ss", 0, 2, 5), ("-st", 1, 0.75, 0.1), ("-lw", 0.05, 0.01, 0.002))
        params = (" {0[0]} {1[0]} {0[1]} {1[1]} {0[2]} {1[2]} {0[3]} {1[3]} {0[4]} {1[4]} {0[5]} {1[5]} {0[6]} {1[6]} {0[7]} {1[7]} {0[8]} {1[8]} {0[9]} {1[9]} {0[10]} {1[10]} ".format([n[0] for n in num], [n[int(node.simacc)+1] for n in num]))

    lexport.clearscened()
    res = [[] for frame in range(0, bpy.context.scene.frame_end+1)]
    for frame in range(0, bpy.context.scene.frame_end+1):
        if os.path.isfile("{}-{}.af".format(lexport.filebase, frame)):
            subprocess.call("{} {}-{}.af".format(lexport.rm, lexport.filebase, frame), shell=True)
        rtcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(lexport.nproc, params, lexport.filebase, frame, node.simalg) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res" 
        rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)
        resfile = open(lexport.newdir+lexport.fold+node.resname+"-"+str(frame)+".res", 'w')
        for line in rtrun.stdout:
            res[frame].append(float(line.decode()))
        resfile.write("{}".format(res[frame]).strip("]").strip("["))
        resfile.close()
    resapply(res, lexport, node)
    calc_op.report({'INFO'}, "Calculation is finished.")

def resapply(res, lexport, node):
    scene = bpy.context.scene
    node.maxres = []
    node.minres = []
    node.avres = []
    
    for frame in range(0, lexport.scene.frame_end+1):
        node.maxres.append(max(res[frame]))
        node.minres.append(min(res[frame]))
        node.avres.append(sum(res[frame])/len(res[frame]))
        
#    self.scene['resav'] = avres
#    self.scene['resmax'] = maxres
#    self.scene['resmin'] = minres

    for frame in range(0, lexport.scene.frame_end+1):
        rgb = []
        lcol_i = []
        mcol_i = 0
        f = 0
        for i in range(0, len(res[frame])):
            h = 0.75*(1-(res[frame][i]-min(node.minres))/(max(node.maxres) + 0.01 - min(node.minres)))
            rgb.append(colorsys.hsv_to_rgb(h, 1.0, 1.0))

        for geo in [geo for geo in scene.objects if geo.type == 'MESH']:
            bpy.ops.object.select_all(action = 'DESELECT')
            scene.objects.active = None
            try:
                if hasattr(geo, 'calc') and geo['calc'] == 1:
                    scene.objects.active = geo
                    geo.select = True
                    if frame == 0:
                        while len(geo.data.vertex_colors) > 0:
                            bpy.ops.mesh.vertex_color_remove()
                        
                    bpy.ops.mesh.vertex_color_add()
                    geo.data.vertex_colors[frame].name = str(frame)
                    vertexColour = geo.data.vertex_colors[frame]
             
                    for face in geo.data.polygons:
                        if "calcsurf" in str(geo.data.materials[face.material_index].name):
                            if node.cpoint == '1':
                                for loop_index in face.loop_indices:
                                    v = geo.data.loops[loop_index].vertex_index
                                    col_i = [vi for vi, vval in enumerate(geo['cverts']) if v == geo['cverts'][vi]][0]
                                    lcol_i.append(col_i)
                                    vertexColour.data[loop_index].color = rgb[col_i+mcol_i]
                                
                            if node.cpoint == '0':
                                for loop_index in face.loop_indices:
                                    vertexColour.data[loop_index].color = rgb[f]
                                f += 1
                       
                    mcol_i = len(tuple(set(lcol_i)))   
    
            except Exception as e:
                print(e)

            if geo.licalc == 1:
                scene.objects.active = geo
                geo.select = True
                if frame == 0:
                    while len(geo.data.vertex_colors) > 0:
                        bpy.ops.mesh.vertex_color_remove()
                    
                bpy.ops.mesh.vertex_color_add()
                geo.data.vertex_colors[frame].name = str(frame)
                vertexColour = geo.data.vertex_colors[frame]
         
                for face in geo.data.polygons:
                    if "calcsurf" in str(geo.data.materials[face.material_index].name):
                        if node.cpoint == '1':
                            cvtup = tuple(geo['cverts'])
                            for loop_index in face.loop_indices:
                                v = geo.data.loops[loop_index].vertex_index
                                if v in cvtup:
                                    col_i = cvtup.index(v) 
                                lcol_i.append(col_i)
                                vertexColour.data[loop_index].color = rgb[col_i+mcol_i]

                        if node.cpoint == '0':
                            for loop_index in face.loop_indices:
                                vertexColour.data[loop_index].color = rgb[f]
                            f += 1
                mcol_i = len(list(set(lcol_i)))
    lexport.scene.lidisplay = 1
    
    for frame in range(0, scene.frame_end+1):
        bpy.context.scene.frame_set(frame)
#        bpy.ops.anim.change_frame(frame = frame)
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
       
    bpy.ops.wm.save_mainfile(check_existing = False)

class LiVi_c(object):  
    def __init__(self, lexport, node, prev_op):
        self.acc = node.simacc
        self.scene = bpy.context.scene
        
        if str(sys.platform) != 'win32':
            if lexport.scene.livi_export_time_type == "0" or lexport.scene.livi_anim == "1":
                self.simlistn = ("illumout", "irradout", "dfout")
                self.simlist = (" |  rcalc  -e '$1=47.4*$1+120*$2+11.6*$3' ", " |  rcalc  -e '$1=$1' ", " |  rcalc  -e '$1=(47.4*$1+120*$2+11.6*$3)/100' ")
                self.unit = ("Lux", "W/m"+ u'\u00b2', "DF %", "Glare")
            else:
                self.simlistn = ("cumillumout", "cumirradout", "", "", "daout")
                self.simlist = (" |  rcalc  -e '$1=47.4*$1+120*$2+11.6*$3' ", " |  rcalc  -e '$1=$1' ")
                self.unit = ("Luxhours", "Wh/m"+ u'\u00b2', "", "", "DA %")
        
        if str(sys.platform) == 'win32':
            if lexport.scene.livi_export_time_type == "0"  or lexport.scene.livi_anim == "1":
                self.simlistn = ("illumout", "irradout", "dfout")
                self.simlist = (' |  rcalc  -e "$1=47.4*$1+120*$2+11.6*$3" ', ' |  rcalc  -e "$1=$1" ', ' |  rcalc  -e "$1=(47.4*$1+120*$2+11.6*$3)/100" ')
                self.unit = ("Lux", "W/m"+ u'\u00b2', "DF %", "Glare")
            else:
                self.simlistn = ("cumillumout", "cumirradout", "", "", "daout")
                self.simlist = (' |  rcalc  -e "$1=47.4*$1+120*$2+11.6*$3" ', ' |  rcalc  -e "$1=$1" ')
                self.unit = ("Luxhours", "Wh/m"+ u'\u00b2', "", "", "DA %")
        try:
            if os.lstat(lexport.filebase+".rtrace").st_size == 0:
                prev_op.report({'ERROR'},"There are no calcsurf materials. Associate a 'calcsurf' material with an object.")
            else:
                if lexport.metric == "3":
                    self.rad_glare(lexport, prev_op)
                elif lexport.metric == "4":
                    self.dayavail(lexport ,prev_op)
                else:
                    self.rad_calc(lexport, prev_op)
        except:
            pass
        
    def rad_prev(self, lexport, prev_op):
        if os.path.isfile(lexport.filebase+"-0.poly"):
            cam = lexport.scene.camera
            if cam != None:
                cang = cam.data.angle*180/pi
                vv = cang * lexport.scene.render.resolution_y/lexport.scene.render.resolution_x
                subprocess.call("rvu -w -n {0} -vv {1:.3f} -vh {2:.3f} -vd {3[0][2]:.3f} {3[1][2]:.3f} {3[2][2]:.3f} -vp {4[0]:.3f} {4[1]:.3f} {4[2]:.3f} {5} {6}-{7}.oct &".format(lexport.nproc, vv, cang, -1*cam.matrix_world, cam.location, lexport.pparams(lexport.scene.livi_calc_acc), lexport.filebase, lexport.scene.frame_current), shell = True)
            else:
                prev_op.report({'ERROR'}, "There is no camera in the scene. Radiance preview will not work")
        else:
            prev_op.report({'ERROR'},"Missing export file. Make sure you have exported the scene.")
    
    def rad_calc(self, lexport, calc_op):
        lexport.clearscened()
        res = [[] for frame in range(0, bpy.context.scene.frame_end+1)]
        for frame in range(0, bpy.context.scene.frame_end+1):
            if os.path.isfile("{}-{}.af".format(lexport.filebase, frame)):
                subprocess.call("{} {}-{}.af".format(lexport.rm, lexport.filebase, frame), shell=True)
            rtcmd = "rtrace -n {0} -w {1} -h -ov -I -af {2}-{3}.af {2}-{3}.oct  < {2}.rtrace {4}".format(lexport.nproc, lexport.sparams(self.acc), lexport.filebase, frame, self.simlist[int(lexport.metric)]) #+" | tee "+lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res" 
            rtrun = Popen(rtcmd, shell = True, stdout=PIPE, stderr=STDOUT)
            resfile = open(lexport.newdir+lexport.fold+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res", 'w')
            for line in rtrun.stdout:
                res[frame].append(float(line.decode()))
            resfile.write("{}".format(res[frame]).strip("]").strip("["))
            resfile.close()
        self.resapply(res, lexport)
        calc_op.report({'INFO'}, "Calculation is finished.")
        
    def rad_glare(self, lexport, calc_op):
        scene = bpy.context.scene
        cam = scene.camera
        if cam:
            gfiles=[]
            for frame in range(0, scene.frame_end+1):
                glarecmd = "rpict -w -vth -vh 180 -vv 180 -x 800 -y 800 -vd {0[0][2]} {0[1][2]} {0[2][2]} -vp {1[0]} {1[1]} {1[2]} {2} {3}-{4}.oct | evalglare -c glare{4}.hdr".format(-1*cam.matrix_world, cam.location, lexport.sparams(self.acc), lexport.filename, frame)               
                glarerun = Popen(glarecmd, shell = True, stdout = PIPE)
                for line in glarerun.stdout:
                    if line.decode().split(",")[0] == 'dgp':
                        glaretext = line.decode().replace(',', ' ').replace("#INF", "").split(' ')
                        glaretf = open(lexport.filebase+".glare", "w")
                        glaretf.write("{0:0>2d}/{1:0>2d} {2:0>2d}:{3:0>2d}\ndgp: {4:.3f}\ndgi: {5:.3f}\nugr: {6:.3f}\nvcp: {7:.3f}\ncgi: {8:.3f}\nLveil: {9:.3f}\n".format(lexport.simtimes[frame].day, lexport.simtimes[frame].month, lexport.simtimes[frame].hour, lexport.simtimes[frame].minute, *[float(x) for x in glaretext[6:12]]))
                        glaretf.close()
                subprocess.call("pcond -u 300 glare{0}.hdr > glaretm{0}.hdr".format(frame), shell=True)
                subprocess.call("{0} {1}.glare | psign -h 32 -cb 0 0 0 -cf 40 40 40 | pcompos glaretm{2}.hdr 0 0 - 800 550 > glare{2}.hdr" .format(lexport.cat, lexport.filename, frame), shell=True)
                subprocess.call("{} glaretm{}.hdr".format(lexport.rm, frame), shell=True)                    
                     
                gfile={"name":"glare"+str(frame)+".hdr"}
                gfiles.append(gfile)
            try:
                bpy.data.scenes['Scene'].sequence_editor.sequences_all["glare0.hdr"]
                bpy.ops.sequencer.refresh_all()
            except:
                bpy.ops.sequencer.image_strip_add( directory = lexport.newdir, \
                    files = gfiles, \
                    frame_start=0, \
                    channel=2, \
                    filemode=9)
        else:
            calc_op.report({'ERROR'}, "There is no camera in the scene. Create one for glare analysis")
        
        lexport.scene.livi_display_panel = 0
   
    def dayavail(self, lexport, calc_op):
        lexport.clearscened()
        res = [[0] * lexport.reslen for frame in range(0, bpy.context.scene.frame_end+1)]
        wd = (7, 5)[int(lexport.scene.livi_calc_da_weekdays)]
        fwd = datetime.datetime(2010, 1, 1).weekday()
        vecvals = [[x%24, (fwd+x)%7] for x in range(0,8760)] if np == 0 else numpy.array([[x%24, (fwd+x)%7] + [0 for p in range(146)] for x in range(0,8760)])
        patch = 2
        if os.path.splitext(os.path.basename(lexport.scene.livi_export_epw_name))[1] in (".hdr", ".HDR"):
            skyrad = open(lexport.filebase+".whitesky", "w")    
            skyrad.write("void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n")
            skyrad.close() 
            mtx = open(lexport.scene.livi_calc_mtx_name, "r")
            hour = 0
            mtxlines = mtx.readlines()
            mtx.close() 
            for fvals in mtxlines:
                linevals = fvals.split(" ")
                try:
                    sumvals = round(float(linevals[0]) +  float(linevals[1]) + float(linevals[2]), 4) 
                    if sumvals > 0:
                        if np == 1:
                            vecvals[hour,patch] = sumvals
                        else:
                            vecvals[hour][patch] = sumvals
                    hour += 1
                except:
                    if fvals != "\n":
                        hour += 1 
                    else:
                        patch += 1
                        hour = 0
            
        else:
            vecvals = lexport.vecvals 

        for frame in range(0, bpy.context.scene.frame_end+1):
            hours = 0
            sensarray = [[0 for x in range(lexport.reslen)] for y in range(146)] if np == 0 else numpy.zeros([146, lexport.reslen])
            subprocess.call("oconv -w "+lexport.lights(frame)+" "+lexport.filename+".whitesky "+lexport.mat(frame)+" "+lexport.poly(frame)+" > "+lexport.filename+"-"+str(frame)+"ws.oct", shell = True)
            if not os.path.isdir(lexport.newdir+lexport.fold+"s_data"):
                os.makedirs(lexport.newdir+lexport.fold+"s_data")
            subprocess.call(lexport.cat+lexport.filebase+".rtrace | rcontrib -w -h -I -fo -bn 146 -ab 3 -ad 4096 -lw 0.0003 -n "+lexport.nproc+" -f tregenza.cal -b tbin -o "+lexport.newdir+lexport.fold+"s_data/"+str(frame)+"-sensor%d.dat -m sky_glow "+lexport.filename+"-"+str(frame)+"ws.oct", shell = True)

            for i in range(0, 146):
                sensfile = open(lexport.newdir+"/s_data/"+str(frame)+"-sensor"+str(i)+".dat", "r")
                for s,sens in enumerate(sensfile.readlines()):
                    sensfloat = [float(x) for x in (sens.split("\t")[0:-1])]
                    if np == 1:
                        sensarray[i,s] = 179 * (0.265*sensfloat[0] + 0.67*sensfloat[1]+0.065*sensfloat[2])
                    elif np == 0:
                        sensarray[i][s] = 179 * (0.265*sensfloat[0] + 0.67*sensfloat[1]+0.065*sensfloat[2])
                sensfile.close()

            for l, readings in enumerate(vecvals):
                finalillu = [0 for x in range(0, lexport.reslen)] if np == 0 else numpy.zeros((lexport.reslen))
                for i in range(0, 146):
                    if lexport.scene.livi_calc_dastart_hour <= float(readings[0]) < lexport.scene.livi_calc_daend_hour and float(readings[1]) < wd:
                        for j, senreading in enumerate(sensarray[i]):
                            if i == 0:
                                finalillu[j] = senreading*readings[i+2]
                                if j == 0:
                                    hours += 1
                            else:
                                finalillu[j] += senreading*readings[i+2]
                for k, reading in enumerate(finalillu):
                    if reading > lexport.scene.livi_calc_min_lux:
                        res[frame][k] += 1
            finalillu = [0 for x in range(0, lexport.reslen)] if np == 0 else numpy.zeros((lexport.reslen))
                        
            for r in range(0, len(res[frame])):
                if hours != 0:
                    res[frame][r] = res[frame][r]*100/hours
            daresfile = open(lexport.newdir+"/"+self.simlistn[int(lexport.metric)]+"-"+str(frame)+".res", "w")
            daresfile.write("{:.2f}\n".format(*res[frame]))
            daresfile.close()
        
        calc_op.report({'INFO'}, "Calculation is finished.") 
        self.resapply(res, lexport) 
        
    def resapply(self, res, lexport):
        maxres = []
        minres = []
        avres = []
        
        for frame in range(0, lexport.scene.frame_end+1):
            maxres.append(max(res[frame]))
            minres.append(min(res[frame]))
            avres.append(sum(res[frame])/len(res[frame]))
            
        self.scene['resav'] = avres
        self.scene['resmax'] = maxres
        self.scene['resmin'] = minres

        for frame in range(0, lexport.scene.frame_end+1):
            rgb = []
            lcol_i = []
            mcol_i = 0
            f = 0
            for i in range(0, len(res[frame])):
                h = 0.75*(1-(res[frame][i]-min(lexport.scene['resmin']))/(max(lexport.scene['resmax']) + 0.01 - min(lexport.scene['resmin'])))
                rgb.append(colorsys.hsv_to_rgb(h, 1.0, 1.0))

            for geo in [geo for geo in self.scene.objects if geo.type == 'MESH']:
                bpy.ops.object.select_all(action = 'DESELECT')
                self.scene.objects.active = None
                try:
                    if hasattr(geo, 'calc') and geo['calc'] == 1:
                        self.scene.objects.active = geo
                        geo.select = True
                        if frame == 0:
                            while len(geo.data.vertex_colors) > 0:
                                bpy.ops.mesh.vertex_color_remove()
                            
                        bpy.ops.mesh.vertex_color_add()
                        geo.data.vertex_colors[frame].name = str(frame)
                        vertexColour = geo.data.vertex_colors[frame]
                 
                        for face in geo.data.polygons:
                            if "calcsurf" in str(geo.data.materials[face.material_index].name):
                                if self.scene['cp'] == 1:
                                    for loop_index in face.loop_indices:
                                        v = geo.data.loops[loop_index].vertex_index
                                        col_i = [vi for vi, vval in enumerate(geo['cverts']) if v == geo['cverts'][vi]][0]
                                        lcol_i.append(col_i)
                                        vertexColour.data[loop_index].color = rgb[col_i+mcol_i]
                                    
                                if self.scene['cp'] == 0:
                                    for loop_index in face.loop_indices:
                                        vertexColour.data[loop_index].color = rgb[f]
                                    f += 1
                           
                        mcol_i = len(tuple(set(lcol_i)))   
        
                except Exception as e:
                    print(e)

                if geo.livi_calc == 1:
                    self.scene.objects.active = geo
                    geo.select = True
                    if frame == 0:
                        while len(geo.data.vertex_colors) > 0:
                            bpy.ops.mesh.vertex_color_remove()
                        
                    bpy.ops.mesh.vertex_color_add()
                    geo.data.vertex_colors[frame].name = str(frame)
                    vertexColour = geo.data.vertex_colors[frame]
             
                    for face in geo.data.polygons:
                        if "calcsurf" in str(geo.data.materials[face.material_index].name):
                            if self.scene['cp'] == 1:
                                cvtup = tuple(geo['cverts'])
                                for loop_index in face.loop_indices:
                                    v = geo.data.loops[loop_index].vertex_index
                                    if v in cvtup:
                                        col_i = cvtup.index(v) 
                                    lcol_i.append(col_i)
                                    vertexColour.data[loop_index].color = rgb[col_i+mcol_i]

                            if self.scene['cp'] == 0:
                                for loop_index in face.loop_indices:
                                    vertexColour.data[loop_index].color = rgb[f]
                                f += 1
                    mcol_i = len(list(set(lcol_i)))
        lexport.scene.livi_display_panel = 1
        
        for frame in range(0, self.scene.frame_end+1):
            bpy.ops.anim.change_frame(frame = frame)
            for geo in self.scene.objects:
                if geo.livi_calc == 1:
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
           
        bpy.ops.wm.save_mainfile(check_existing = False)