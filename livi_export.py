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

import bpy, os, math, subprocess, datetime, multiprocessing, sys
import time as ti
from math import sin, cos, acos, asin, pi
from mathutils import Vector
from subprocess import PIPE, Popen
 

try:
    import numpy as numpy
    np = 1
except:
    np = 0
   
class LiVi_bc(object):
    '''Base settings class for LiVi'''
    def __init__(self, filepath):
        if str(sys.platform) != 'win32':
            self.nproc = str(multiprocessing.cpu_count())
            self.rm = "rm "
            self.cat = "cat "
            self.fold = "/"
        else:
            self.nproc = "1"
            self.rm = "del "
            self.cat = "type "
            self.fold = "\\"
        self.filepath = filepath
        self.filename = os.path.splitext(os.path.basename(self.filepath))[0]
        self.filedir = os.path.dirname(self.filepath)
        if not os.path.isdir(self.filedir+self.fold+self.filename):
            os.makedirs(self.filedir+self.fold+self.filename)        
        self.newdir = self.filedir+self.fold+self.filename
        self.filebase = self.newdir+self.fold+self.filename
        self.scene = bpy.context.scene
        self.scene['newdir'] = self.newdir
            
class LiVi_e(LiVi_bc):
    '''Export settings class for LiVi'''
    def __init__(self, filepath, node, export_op):
        LiVi_bc.__init__(self, filepath)
        self.simtimes = []
#        self.scene.livi_display_legend = -1
        self.clearscenee()
        self.clearscened()
        self.skytype = int(node.skymenu)
        self.merr = 0
        self.rtrace = self.filebase+".rtrace"
        self.metric = ""
        self.scene = bpy.context.scene
        self.node  = node
        
        for a in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(a)
        
        if node.timetype == 'Static': 
            self.scene.frame_start = 0
            self.scene.frame_end = 0
        
        elif node.timetype == 'Time': 
            self.endtime = datetime.datetime(2013, 1, 1, node.ehour) + datetime.timedelta(node.edoy - 1)
            self.hours = (self.endtime-self.starttime).days*24 + (self.endtime-self.starttime).seconds/3600
            self.scene.frame_start = 0
            self.scene.frame_end = int(self.hours/node.interval)
      
        if self.skytype < 4:
            self.skytypeparams = ("+s", "+i", "-c", "-b 22.86 -c")[self.skytype]
            if self.skytype < 3 and node.analysismenu != '2':
                self.starttime = datetime.datetime(2013, 1, 1, node.shour) + datetime.timedelta(node.sdoy - 1)
               
            self.radskyhdrexport(node)
            
            if self.skytype < 2 and node.analysismenu != '2':
                self.sunexport(node)
        
        elif self.skytype == 4:
            if node.hdrname not in bpy.data.images:
                bpy.data.images.load(node.hdrname)
        
        elif self.skytype == 5:
            subprocess.call("cp {} {}".format(node.radname, self.sky(0)), shell = True)
        
        elif self.skytype == 6:
            for frame in range(self.scene.frame_start, self.scene.frame_end + 1):
                rad_sky = open(self.sky(frame), "w")
                rad_sky.close()
            
        for frame in range(self.scene.frame_start, self.scene.frame_end + 1):
            if node.timetype == 'Lights':
                self.radlights(frame, node)
            elif frame == 0:
                self.radlights(frame, node)
            
            if node.timetype == "Material":
                self.radmat(frame, export_op, node)
            elif frame == 0:
                self.radmat(frame, export_op, node)
        
        self.rtexport(export_op, node)
        
        if self.export != 0:    
            for frame in range(self.scene.frame_start, self.scene.frame_end + 1):  
                self.merr = 0
                if node.animmenu == "Geometry":
                    self.obexport(frame, [geo for geo in self.scene.objects if geo.type == 'MESH' and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True], 0, export_op, node) 
                elif node.animmenu == "Material":
                    self.obmexport(frame, [geo for geo in self.scene.objects if geo.type == 'MESH' and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True], 0, export_op, node) 
                elif frame == 0:
                    self.obexport(frame, [geo for geo in self.scene.objects if geo.type == 'MESH' and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True], 0, export_op, node)
            
                self.fexport(frame, export_op, node)
        
    def poly(self, fr, node):
        if node.animmenu == "Geometry" or (node.animmenu == "3" and self.merr == 0):
            return(self.filebase+"-"+str(fr)+".poly")   
        else:
            return(self.filebase+"-0.poly")
     
    def obj(self, name, fr, node):
        if node.animmenu == "Geometry":
            return(self.filebase+"-{}-{}.obj".format(name.replace(" ", "_"), fr))
        else:
            return(self.filebase+"-{}-0.obj".format(name.replace(" ", "_")))
    
    def mesh(self, name, fr, node):
        if node.animmenu in ("Geometry", "Material"):
            return(self.filebase+"-{}-{}.mesh".format(name.replace(" ", "_"), fr))
        else:
            return(self.filebase+"-{}-0.mesh".format(name.replace(" ", "_")))
    
    def mat(self, fr, node):
        if node.animmenu == "Material":
            return(self.filebase+"-"+str(fr)+".mat")
        else:
            return(self.filebase+"-0.mat")
    
    def lights(self, fr, node):
        if node.animmenu == "Lights":
            return(self.filebase+"-"+str(fr)+".lights")
        else:
            return(self.filebase+"-0.lights")
    
    def sky(self, fr, node):
        if node.animmenu == "Time":
            return(self.filebase+"-"+str(fr)+".sky")
        else:
            return(self.filebase+"-0.sky")
    
    def clearscenee(self):
        for sunob in [ob for ob in self.scene.objects if ob.type == 'LAMP' and ob.data.type == 'SUN']:
            self.scene.objects.unlink(sunob)
        
        for ob in [ob for ob in self.scene.objects if ob.type == 'MESH']:
            self.scene.objects.active = ob
            for vcol in ob.data.vertex_colors:
                bpy.ops.mesh.vertex_color_remove()
    
    def clearscened(self):    
        for ob in [ob for ob in self.scene.objects if ob.type == 'MESH']:
            if ob.lires == 1:
                self.scene.objects.unlink(ob)
       
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        
        for lamp in bpy.data.lamps:
            if lamp.users == 0:
                bpy.data.lamps.remove(lamp)
        
        for oldgeo in bpy.data.objects:
            if oldgeo.users == 0:
                bpy.data.objects.remove(oldgeo)
                
        for sk in bpy.data.shape_keys:
            if sk.users == 0:
                for keys in sk.keys():
                    keys.animation_data_clear()
                    
    def radskyhdrexport(self, node):
        for frame in range(self.scene.frame_start, self.scene.frame_end + 1):
            simtime = self.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
            self.simtimes.append(simtime)
            subprocess.call("gensky {} {} {}:{:0>2d}{} -a {} -o {} {} > {}".format(simtime.month, simtime.day, simtime.hour, simtime.minute, node.TZ, node.lati, node.longi, self.skytypeparams, self.sky(frame, node)), shell = True)
            self.skyexport(open(self.sky(frame, node), "a"))           
            subprocess.call("oconv {} > {}-{}sky.oct".format(self.sky(frame, node), self.filebase, frame), shell=True)
            subprocess.call("cnt 250 500 | rcalc -f {}/lib/latlong.cal -e 'XD=500;YD=250;inXD=0.002;inYD=0.004' | rtrace -af pan.af -n {} -x 500 -y 250 -fac {}-{}sky.oct > {}/{}p.hdr".format(self.scene.vipath, self.nproc, self.filebase, frame, self.newdir, frame), shell=True)
            subprocess.call("rpict -vta -vp 0 0 0 -vd 1 0 0 -vu 0 0 1 -vh 360 -vv 360 -x 1000 -y 1000 {}-{}sky.oct > {}/{}.hdr".format(self.filebase, frame, self.newdir, frame), shell=True)
                
    def sunexport(self, node):
        for frame in range(self.scene.frame_start, self.scene.frame_end + 1):
            simtime = self.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
            deg2rad = 2*math.pi/360
            DS = 1 if node.daysav else 0
            ([solalt, solazi]) = solarPosition(simtime.timetuple()[7], simtime.hour - DS + (simtime.minute)*0.016666, node.lati, node.longi) 
            if self.skytype < 2:
                if frame == 0:
                    bpy.ops.object.lamp_add(type='SUN')
                    sun = bpy.context.object
                    sun.data.shadow_method = 'RAY_SHADOW'
                    sun.data.shadow_ray_samples = 8
                    sun.data.sky.use_sky = 1
                    if self.skytype == 0:
                        sun.data.shadow_soft_size = 0.1
                        sun.data.energy = 5
                    elif self.skytype == 1:
                        sun.data.shadow_soft_size = 3
                        sun.data.energy = 3
                    sun.location = (0,0,10)
                sun.rotation_euler = (90-solalt)*deg2rad, 0, solazi*deg2rad
                sun.keyframe_insert(data_path = 'location', frame = frame)
                sun.keyframe_insert(data_path = 'rotation_euler', frame = frame)
                sun.data.cycles.use_multiple_importance_sampling = True
                sun.data.shadow_soft_size = 0.01
            
            bpy.ops.object.select_all()
            
#    def skyhdrexport(self, hdr_skies):
#        render = self.scene.render
#        w = bpy.data.worlds['World']
#        if self.skytype > 1 or self.scene.livi_export_time_type == "1":
#            imgPath = hdr_skies
#            img = bpy.data.images.load(imgPath)
#            if self.scene.world.texture_slots[0] == None or self.scene.world.texture_slots[0] == "":
#                
#                imtex = bpy.data.textures.new('Radsky', type = 'IMAGE')
#                imtex.image = img
#                
#                slot = w.texture_slots.add()
#                slot.texture = imtex
#                slot.use_map_horizon = True
#                slot.use_map_blend = False
#                slot.texture_coords = 'EQUIRECT'
#                bpy.data.textures['Radsky'].image_user.use_auto_refresh = True
#                
#                self.scene.world.light_settings.use_environment_light = True
#                self.scene.world.light_settings.use_indirect_light = False
#                self.scene.world.light_settings.use_ambient_occlusion = True
#                self.scene.world.light_settings.environment_energy = 1
#                self.scene.world.light_settings.environment_color = 'SKY_TEXTURE'
#                self.scene.world.light_settings.gather_method = 'APPROXIMATE'
#                self.scene.world.light_settings.passes = 1
#                self.scene.world.use_sky_real = True
#                self.scene.world.use_sky_paper = False
#                self.scene.world.use_sky_blend = False
#                
#                self.scene.world.horizon_color = (0, 0, 0)
#                self.scene.world.zenith_color = (0, 0, 0)
#                
#                render.use_raytrace = True
#                render.use_textures = True
#                render.use_shadows = True
#                render.use_envmaps = True
#                bpy.ops.images.reload
#            else:
#                bpy.data.worlds['World'].texture_slots[0].texture.image.filepath = hdr_skies
#                bpy.data.worlds['World'].texture_slots[0].texture.image.reload()
#            
#            if self.scene.livi_anim != '1':
#                bpy.data.worlds['World'].texture_slots[0].texture.image.source = 'FILE'
#            else:
#                bpy.data.worlds['World'].texture_slots[0].texture.image.source = 'SEQUENCE'
#            
#            self.scene.world.ambient_color = (0.04, 0.04, 0.04) if self.scene.livi_export_time_type == "0" else (0.000001, 0.000001, 0.000001)
#                
#            bpy.data.worlds['World'].texture_slots[0].texture.factor_red = (0.05, 0.000001)[int(self.scene.livi_export_time_type)]
#            bpy.data.worlds['World'].texture_slots[0].texture.factor_green = (0.05, 0.000001)[int(self.scene.livi_export_time_type)]
#            bpy.data.worlds['World'].texture_slots[0].texture.factor_blue = (0.05, 0.000001)[int(self.scene.livi_export_time_type)]
#            
#            if self.sky_type == 4:
#                self.hdrsky(open(self.sky(0), "w"), self.scene.livi_export_hdr_name)
#            elif self.time_type == 1:
#                self.hdrsky(open(self.sky(0), "w"), hdr_skies)
#            
#            if self.scene.render.engine == "CYCLES" and bpy.data.worlds['World'].use_nodes == False:
#                bpy.data.worlds['World'].use_nodes = True
#                nt = bpy.data.worlds['World'].node_tree
#                try:
#                    if nt.nodes['Environment Texture']:
#                        pass
#                except:
#                    nt.nodes.new("TEX_ENVIRONMENT")
#                    nt.nodes['Environment Texture'].image = bpy.data.images[os.path.basename(hdr_skies)]
#                    nt.nodes['Environment Texture'].image.name = "World"
#                    nt.nodes['Environment Texture'].image.source = 'FILE'
#                    if self.scene.livi_export_time_type == "1":
#                        nt.nodes['Environment Texture'].projection = 'MIRROR_BALL'
#                    else:
#                        nt.nodes['Environment Texture'].projection = 'EQUIRECTANGULAR'
#            bpy.app.handlers.frame_change_pre.append(cyfc1) 
#        else:
#            self.scene.world.use_sky_real = False
#            self.scene.world.use_sky_paper = False
#            self.scene.world.use_sky_blend = False
#            self.scene.world.light_settings.use_environment_light = True
#            self.scene.world.light_settings.use_indirect_light = False
#            self.scene.world.light_settings.use_ambient_occlusion = False
#            self.scene.world.light_settings.environment_energy = 1
#            self.scene.world.light_settings.environment_color = 'SKY_COLOR'
#            self.scene.world.light_settings.gather_method = 'APPROXIMATE'
#            self.scene.world.light_settings.passes = 1
#            self.scene.render.alpha_mode = "SKY"
#            render.use_raytrace = True
#            render.use_textures = True
#            render.use_shadows = True
#            render.use_envmaps = False
#            try:
#                w.texture_slots[0].use_map_horizon = False
#            except:
#                pass
#
#            for sun in [s for s in bpy.data.objects if s.type == "LAMP" and s.data.type == "SUN"]:
#                sun.data.shadow_method = "RAY_SHADOW"
#                sun.data.shadow_soft_size = 0.01
#                sun.data.cycles.cast_shadow = True
#                sun.data.cycles.use_multiple_importance_sampling = True
#                sun.data.sky.use_sky = True
#                sun.hide = False   
#                sun.data.sky.use_atmosphere = False
#                sun.data.energy = 1
                
    def skyexport(self, rad_sky):
        rad_sky.write("\nskyfunc glow skyglow\n0\n0\n")
        rad_sky.write("4 .8 .8 1 0\n\n") if self.skytype < 3 else rad_sky.write("4 1 1 1 0\n\n") 
        rad_sky.write("skyglow source sky\n0\n0\n4 0 0 1  180\n\n")
        rad_sky.write("skyfunc glow groundglow\n0\n0\n4 .8 1.1 .8  0\n\n")
        rad_sky.write("groundglow source ground\n0\n0\n4 0 0 -1  180\n\n")
        rad_sky.close()
        

        
    def hdrsky(self, rad_sky, skyfile):
        rad_sky.write("# Sky material\nvoid colorpict hdr_env\n7 red green blue "+skyfile+" angmap.cal sb_u sb_v\n0\n0\n\nhdr_env glow env_glow\n0\n0\n4 1 1 1 0\n\nenv_glow bubble sky\n0\n0\n4 0 0 0 500\n\n")
        rad_sky.close()
        
    def radmat(self, frame, export_op, node):
        self.scene.frame_set(frame)
        rad_mat = open(self.mat(frame, node), "w")
        for meshmat in bpy.data.materials:
            diff = [meshmat.diffuse_color[0]*meshmat.diffuse_intensity, meshmat.diffuse_color[1]*meshmat.diffuse_intensity, meshmat.diffuse_color[2]*meshmat.diffuse_intensity]
            if "calcsurf" in meshmat.name:
                meshmat.use_vertex_color_paint = 1
            if meshmat.use_shadeless == 1:
                rad_mat.write("# Antimatter material\nvoid antimatter " + meshmat.name.replace(" ", "_") +"\n1 void\n0\n0\n\n")
                
            elif meshmat.emit > 0:
                rad_mat.write("# Light material\nvoid light " + meshmat.name.replace(" ", "_") +"\n0\n0\n3 {:.2f} {:.2f} {:.2f}\n".format(meshmat.emit * diff[0], meshmat.emit * diff[1], meshmat.emit * diff[2]))
                for o in [o for o in bpy.data.objects if o.type == 'MESH']:
                    if meshmat in [om for om in o.data.materials]:
                        o['merr'] = 1
                        export_op.report({'INFO'}, o.name+" has a emission material. Basic export routine used with no modifiers.")
                        
            elif meshmat.use_transparency == False and meshmat.raytrace_mirror.use == True and meshmat.raytrace_mirror.reflect_factor >= 0.99:
                rad_mat.write("# Mirror material\nvoid mirror " + meshmat.name.replace(" ", "_") +"\n0\n0\n3 {0[0]} {0[1]} {0[2]}\n\n".format(meshmat.mirror_color))
                for o in [o for o in bpy.data.objects if o.type == 'MESH']:
                    if meshmat in [om for om in o.data.materials]:
                        o['merr'] = 1
                        export_op.report({'INFO'}, o.name+" has a mirror material. Basic export routine used with no modifiers.")
            
            elif meshmat.use_transparency == True and meshmat.transparency_method == 'RAYTRACE' and meshmat.alpha < 1.0 and meshmat.translucency == 0:
                if "{:.2f}".format(meshmat.raytrace_transparency.ior) == "1.52":
                    rad_mat.write("# Glass material\nvoid glass " + meshmat.name.replace(" ", "_") +"\n0\n0\n3 {:.3f} {:.3f} {:.3f}\n\n".format((1.0 - meshmat.alpha)*diff[0], (1.0 - meshmat.alpha)*diff[1], (1.0 - meshmat.alpha)*diff[2]))
                else:
                    rad_mat.write("# Glass material\nvoid glass " + meshmat.name.replace(" ", "_") +"\n0\n0\n4 {0:.3f} {1:.3f} {2:.3f} {3}\n\n".format((1.0 - meshmat.alpha)*diff[0], (1.0 - meshmat.alpha)*diff[1], (1.0 - meshmat.alpha)*diff[2], meshmat.raytrace_transparency.ior))
                 
            elif meshmat.use_transparency == True and meshmat.transparency_method == 'RAYTRACE' and meshmat.alpha < 1.0 and meshmat.translucency > 0.001:
                rad_mat.write("# Translucent material\nvoid trans " + meshmat.name.replace(" ", "_")+"\n0\n0\n7 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1} {2} {3} {4}\n\n".format(diff, meshmat.specular_intensity, 1.0 - meshmat.specular_hardness/511.0, 1.0 - meshmat.alpha, 1.0 - meshmat.translucency))
            
            elif meshmat.use_transparency == False and meshmat.raytrace_mirror.use == True and meshmat.raytrace_mirror.reflect_factor < 0.99:
                rad_mat.write("# Metal material\nvoid metal " + meshmat.name.replace(" ", "_") +"\n0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1} {2}\n\n".format(diff, meshmat.specular_intensity, 1.0-meshmat.specular_hardness/511.0))
            else:
                rad_mat.write("# Plastic material\nvoid plastic " + meshmat.name.replace(" ", "_") +"\n0\n0\n5 {0[0]:.2f} {0[1]:.2f} {0[2]:.2f} {1:.2f} {2:.2f}\n\n".format(diff, meshmat.specular_intensity, 1.0-meshmat.specular_hardness/511.0))
        rad_mat.close()

    def obexport(self,frame, obs, obno, export_op, node):
        self.scene.frame_current = frame
        rad_poly = open(self.poly(frame, node), 'w')
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:
            o.select = True
            bpy.ops.export_scene.obj(filepath=self.obj(o.name, frame, node), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=True, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
            o.select = False
            objcmd = "obj2mesh -w -a "+self.mat(frame, node)+" "+self.obj(o.name, frame, node)+" "+self.mesh(o.name, frame, node)
            objrun = Popen(objcmd, shell = True, stderr = PIPE)
            for line in objrun.stderr:
                if 'fatal' in str(line):
                    o.livi_merr = 1

            if o.livi_merr == 0:
                rad_poly.write("void mesh id \n1 "+self.mesh(o.name, frame, node)+"\n0\n0\n\n")
    
            else:
                export_op.report({'INFO'}, o.name+" could not be converted into a Radiance mesh and simpler export routine has been used. No un-applied object modifiers will be exported.")
                o.livi_merr = 0
                geomatrix = o.matrix_world
                for face in o.data.polygons:
                    try:
                        vertices = face.vertices[:]
                        rad_poly.write("# Polygon \n{} polygon poly_{}_{}\n0\n0\n{}\n".format(o.data.materials[face.material_index].name.replace(" ", "_"), o.data.name.replace(" ", "_"), face.index, 3*len(face.vertices)))                   
                        try:
                            if o.data.shape_keys and o.data.shape_keys.key_blocks[0] and o.data.shape_keys.key_blocks[1]:
                                for vertindex in vertices:
                                    sk0 = o.data.shape_keys.key_blocks[0]
                                    sk0co = geomatrix*sk0.data[vertindex].co
                                    sk1 = o.data.shape_keys.key_blocks[1]
                                    sk1co = geomatrix*sk1.data[vertindex].co
                                    rad_poly.write(" {} {} {}\n".format(sk0co[0]+(sk1co[0]-sk0co[0])*sk1.value, sk0co[1]+(sk1co[1]-sk0co[1])*sk1.value, sk0co[2]+(sk1co[2]-sk0co[2])*sk1.value))
                        except:
                            for vertindex in vertices:
                                rad_poly.write(" {0[0]} {0[1]} {0[2]}\n".format(geomatrix*o.data.vertices[vertindex].co))
                        rad_poly.write("\n")
                    except:
                        export_op.report({'ERROR'},"Make sure your object "+o.name+" has an associated material")
        rad_poly.close()

    def obmexport(self, frame, obs, ob, export_op, node):
        self.scene.frame_current = frame
        rad_poly = open(self.poly(frame, node), 'w')
        for o in obs:
            if frame == 0:
                o.select = True
                bpy.ops.export_scene.obj(filepath=self.obj(o.name, frame, node), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=True, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                o.select = False
#                bpy.ops.export_scene.obj(filepath=self.obj(obs.name, frame), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_apply_modifiers=True, use_edges=False, use_normals=True, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
            objcmd = "obj2mesh -w -a "+self.mat(frame, node)+" "+self.obj(o.name, 0, node)+" "+self.mesh(o.name, frame, node)
            objrun = Popen(objcmd, shell = True, stderr = PIPE)
        
            for line in objrun.stderr:
                if 'fatal' in str(line):
                    o.livi_merr = 1
       
            if o.livi_merr == 0 and ob == 0:
                rad_poly.write("void mesh id \n1 "+self.mesh(o.name, frame, node)+"\n0\n0\n")
        
            elif o.livi_merr == 1:        
                if frame == 0:
                    for geo in obs:
                        geomatrix = geo.matrix_world
                        for face in geo.data.polygons:
                            try:
                                vertices = face.vertices[:]
                                rad_poly.write("# Polygon \n"+geo.data.materials[face.material_index].name.replace(" ", "_") + " polygon " + "poly_"+geo.data.name.replace(" ", "_")+"_"+str(face.index) + "\n0\n0\n"+str(3*len(face.vertices))+"\n")
                                try:
                                    if geo.data.shape_keys.key_blocks[0] and geo.data.shape_keys.key_blocks[1]:
                                        for vertindex in vertices:
                                            sk0 = geo.data.shape_keys.key_blocks[0]
                                            sk0co = geomatrix*sk0.data[vertindex].co
                                            sk1 = geo.data.shape_keys.key_blocks[1]
                                            sk1co = geomatrix*sk1.data[vertindex].co
                                            rad_poly.write(" {} {} {}\n".format(sk0co[0]+(sk1co[0]-sk0co[0])*sk1.value, sk0co[1]+(sk1co[1]-sk0co[1])*sk1.value, sk0co[2]+(sk1co[2]-sk0co[2])*sk1.value))
                                except:
                                    for vertindex in vertices:
                                        rad_poly.write(" {0[0]} {0[1]} {0[2]}\n".format(geomatrix*o.data.vertices[vertindex].co))
                                rad_poly.write("\n")
                            except:
                                export_op.report({'ERROR'},"Make sure your object "+geo.name+" has an associated material")
        rad_poly.close()
        
    def radlights(self, frame, node):
        os.chdir(self.newdir)
        self.scene.frame_set(frame)
        rad_lights = open(self.lights(frame, node), "w")
        for geo in bpy.context.scene.objects:
            if geo.ies_name != "":
                iesname = os.path.splitext(os.path.basename(geo.ies_name))[0]
                subprocess.call("ies2rad -t default -m {} -l / -p {} -d{} -o {}-{} {}".format(geo.ies_strength, self.newdir, geo.ies_unit, iesname, frame, geo.ies_name), shell=True)
                if geo.type == 'LAMP':
                    if geo.parent:
                        geo = geo.parent                    
                    rad_lights.write("!xform -rx {0} -ry {1} -rz {2} -t {3[0]} {3[1]} {3[2]} {4}.rad\n\n".format((180/pi)*geo.rotation_euler[0], (180/pi)*geo.rotation_euler[1], (180/pi)*geo.rotation_euler[2], geo.location, self.newdir+"/"+iesname+"-"+str(frame)))    
                if 'lightarray' in geo.name:
                    spotmatrix = geo.matrix_world
                    rotation = geo.rotation_euler                    
                    for face in geo.data.polygons:
                        fx = sum([(spotmatrix*v.co)[0] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        fy = sum([(spotmatrix*v.co)[1] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        fz = sum([(spotmatrix*v.co)[2] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        rad_lights.write("!xform -rx {:.3f} -ry {:.3f} -rz {:.3f} -t {:.3f} {:.3f} {:.3f} {}\n".format((180/pi)*rotation[0], (180/pi)*rotation[1], (180/pi)*rotation[2], fx, fy, fz, self.newdir+"/"+iesname+"-"+str(frame)+".rad"))
        rad_lights.close()
        
    def rtexport(self, export_op, node):
    # Function for the exporting of Blender geometry and materials to Radiance files
        rtrace = open(self.rtrace, "w")       
        calcsurfverts = []
        calcsurffaces = []
        if 0 not in [len(geo.data.materials) for geo in bpy.data.objects if geo.type == 'MESH' and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True ]:
            for o, geo in enumerate(self.scene.objects):
                csf = []
                cverts = []
                
                if geo.type == 'MESH' and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True:
                    if len([mat.name for mat in geo.material_slots if 'calcsurf' in mat.name]) != 0:
                        self.scene.objects.active = geo
                        bpy.ops.object.mode_set(mode = 'EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.object.mode_set(mode = 'OBJECT')
                        mesh = geo.to_mesh(self.scene, True, 'PREVIEW', calc_tessface=False)
                        mesh.transform(geo.matrix_world)
                        
                        for face in mesh.polygons:
                            if "calcsurf" in str(mesh.materials[face.material_index].name):
                                csf.append(face.index)
                                geo.licalc = 1
                                vsum = Vector((0, 0, 0))
                                self.scene.objects.active = geo
                                geo.select = True
                                bpy.ops.object.mode_set(mode = 'OBJECT')                        
                                for vc in geo.data.vertex_colors:
                                    bpy.ops.mesh.vertex_color_remove()
                                
                                if node.cpoint == '0':                            
                                    for v in face.vertices:
                                        vsum = mesh.vertices[v].co + vsum
                                    fc = vsum/len(face.vertices)
                                    rtrace.write('{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(fc, face.normal[:]))
                                    calcsurffaces.append((o, face))
                                    
                                for vert in face.vertices:
                                    if (mesh.vertices[vert]) not in calcsurfverts:
                                        vcentx, vcenty, vcentz = mesh.vertices[vert].co[:]
                                        vnormx, vnormy, vnormz = (mesh.vertices[vert].normal*geo.matrix_world.inverted())[:]
                                        
                                        if node.cpoint == '1':
                                            rtrace.write('{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(mesh.vertices[vert].co[:], (mesh.vertices[vert].normal*geo.matrix_world.inverted())[:]))
                                            calcsurfverts.append(mesh.vertices[vert])
                                            cverts.append(vert)
                                
                                if node.cpoint == '1':        
                                    geo['cverts'] = cverts
                                    geo['cfaces'] = csf
                                    self.reslen = len(calcsurfverts)

                                elif node.cpoint == '0':
                                    geo['cfaces'] = csf
                                    self.reslen = len(calcsurffaces)
                        bpy.data.meshes.remove(mesh)
                    else:
                        geo.licalc = 0
                        for mat in geo.material_slots:
                            mat.material.use_transparent_shadows = True

            rtrace.close()    
            self.export = 1            
        else:
            self.export = 0
            for geo in self.scene.objects:
                if geo.type == 'MESH' and geo.name != 'lightarray' and geo.hide == False and geo.layers[0] == True and not geo.data.materials:
                    export_op.report({'ERROR'},"Make sure your object "+geo.name+" has an associated material") 
    
    def fexport(self, frame, export_op, node):
        try:
            subprocess.call("oconv -w "+self.lights(frame, node)+" "+self.sky(frame, node)+" "+self.mat(frame, node)+" "+self.poly(frame, node)+" > "+self.filebase+"-"+str(frame)+".oct", shell=True)
            self.export = 1
        except:
            export_op.report({'ERROR'},"There is a problem with geometry export. If created in another package simplify the geometry, and turn off smooth shading")
            self.export = 0
        self.scene.li_disp_panel = 0   
        self.scene.li_display = 0
        export_op.report({'INFO'},"Export is finished")
        self.scene.frame_set(0)                      

    def ddsskyexport(self, node):
        os.chdir(self.newdir)
        pcombfiles = ""
        for i in range(0, 146):
            pcombfiles = pcombfiles + "ps{}.hdr ".format(i)
        epwbase = os.path.splitext(os.path.basename(node.epwname))
        if epwbase[1] in (".epw", ".EPW"):
            epw = open(self.scene.livi_export_epw_name, "r")
            epwlines = epw.readlines()
            epw.close()
            epwyear = epwlines[8].split(",")[0]
            if not os.path.isfile(self.newdir+"/"+epwbase[0]+".wea"):
                wea = open(self.newdir+"/"+epwbase[0]+".wea", "w")
                wea.write("place {0[1]}\nlatitude {0[6]}\nlongitude {0[7]}\ntime_zone {0[8]}\nsite_elevation {0[9]}weather_data_file_units 1\n".format(epwlines[0].split(",")))
                for epwline in epwlines[8:]:
                    wea.write("{0[1]} {0[2]} {0[3]} {0[14]} {0[15]} \n".format(epwline.split(",")))
                wea.close()
            if not os.path.isfile(self.newdir+"/"+epwbase[0]+".mtx"):
                subprocess.call("gendaymtx -r -90 -m 1 {0}.wea > {0}.mtx".format(self.newdir+"/"+epwbase[0]), shell=True) 

            patch = 2
            hour = 0
            fwd = datetime.datetime(int(epwyear), 1, 1).weekday()
            if np == 0:
                self.vecvals = [[x%24, (fwd+x)%7] + [0 for p in range(146)] for x in range(0,8760)]
                vals = [0 for x in range(146)]
            else:
                self.vecvals = numpy.array([[x%24, (fwd+x)%7] + [0 for p in range(146)] for x in range(0,8760)])
                vals = numpy.zeros((146))

            mtx = open(self.newdir+"/"+epwbase[0]+".mtx", "r") 
            mtxlines = mtx.readlines()
            mtx.close()   
            
            for fvals in mtxlines:
                linevals = fvals.split(" ")
                try:
                    sumvals = float(linevals[0]) +  float(linevals[1]) + float(linevals[2]) 
                    if sumvals > 0:
                        vals[patch - 2] += sumvals
                        if np == 1:
                            self.vecvals[hour,patch] = sumvals
                        else:
                            self.vecvals[hour][patch] = sumvals
                    hour += 1
                except:
                    if fvals != "\n":
                        hour += 1 
                    else:
                        patch += 1
                        hour = 0
                        
            skyrad = open(self.filename+".whitesky", "w")    
            skyrad.write("void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n")
            skyrad.close()
            subprocess.call("oconv {0}.whitesky > {0}-whitesky.oct".format(self.filename), shell=True)
            subprocess.call("vwrays -ff -x 600 -y 600 -vta -vp 0 0 0 -vd 1 0 0 -vu 0 0 1 -vh 360 -vv 360 -vo 0 -va 0 -vs 0 -vl 0 | rcontrib -bn 146 -fo -ab 0 -ad 512 -n {} -ffc -x 600 -y 600 -ld- -V+ -f tregenza.cal -b tbin -o p%d.hdr -m sky_glow {}-whitesky.oct".format(self.nproc, self.filename), shell = True)
            
            for j in range(0, 146):
                subprocess.call("pcomb -s {0} p{1}.hdr > ps{1}.hdr".format(vals[j], j), shell = True)
                subprocess.call("{0}  p{1}.hdr".format(self.rm, j), shell = True) 
            subprocess.call("pcomb -h  "+pcombfiles+" > "+self.newdir+"/"+epwbase[0]+".hdr", shell = True)    
            subprocess.call(self.rm+" ps*.hdr" , shell = True)            
#            self.skyhdrexport(self.newdir+"/"+epwbase[0]+".hdr")
#        elif epwbase[-1] in (".hdr", ".HDR"):
#            self.skyhdrexport(self.scene.livi_export_epw_name)
            
            
#Compute solar position (altitude and azimuth in degrees) based on day of year (doy; integer), local solar time (lst; decimal hours), latitude (lat; decimal degrees), and longitude (lon; decimal degrees).
def solarPosition(doy, lst, lat, lon):
    #Set the local standard time meridian (lsm) (integer degrees of arc)
    lsm = int(lon/15)*15
    #Approximation for equation of time (et) (minutes) comes from the Wikipedia article on Equation of Time
    b = 2*math.pi*(doy-81)/364
    et = 9.87 * math.sin(2*b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    #The following formulas adapted from the 2005 ASHRAE Fundamentals, pp. 31.13-31.16
    #Conversion multipliers
    degToRad = 2*math.pi/360
    radToDeg = 1/degToRad
    #Apparent solar time (ast)
    ast = lst + et/60 + (lsm-lon)/15
    #Solar declination (delta) (radians)
    delta = degToRad*23.45 * math.sin(2*math.pi*(284+doy)/365)
    #Hour angle (h) (radians)
    h = degToRad*15 * (ast-12)
     #Local latitude (l) (radians)
    l = degToRad*lat
    #Solar altitude (beta) (radians)
    beta = asin(cos(l) * cos(delta) * cos(h) + sin(l) * sin(delta))
    #Solar azimuth phi (radians)
    phi = acos((sin(beta) * sin(l) - sin(delta))/(cos(beta) * cos(l)))                                                                         
    #Convert altitude and azimuth from radians to degrees, since the Spatial Analyst's Hillshade function inputs solar angles in degrees
    altitude = radToDeg*beta
    azimuth = radToDeg*phi if ast<=12 else 360 - radToDeg*phi
    return([altitude, azimuth])         
    
def negneg(x):
    if float(x) < 0:
        x = 0
    return float(x)
    
def cyfc1(self):
    if bpy.data.scenes[0].render.engine == "CYCLES":
        for materials in bpy.data.materials:
            if materials.use_nodes == 1:
                try:
                    if 'calcsurf' in materials.name:
                        nt = materials.node_tree
                        nt.nodes["Attribute"].attribute_name = str(bpy.context.scene.frame_current)
                except Exception as e:
                    print(e, 'Something wrong with changing the material attribute name')  
        if hasattr(bpy.data.worlds, 'World'):
            if bpy.data.worlds["World"].use_nodes == False:
                bpy.data.worlds["World"].use_nodes = True
        nt = bpy.data.worlds[0].node_tree
        if hasattr(nt.nodes, 'Environment Texture'):    
            nt.nodes['Environment Texture'].image.filepath = bpy.context.scene['newdir']+"/%sp.hdr" %(bpy.context.scene.frame_current)
            nt.nodes['Environment Texture'].image.reload()  
        if hasattr(bpy.data.worlds[0].node_tree.nodes, 'Background'):
            try:
                bpy.data.worlds[0].node_tree.nodes["Background"].inputs[1].keyframe
            except:
                bpy.data.worlds[0].node_tree.nodes["Background"].inputs[1].keyframe_insert('default_value')
        bpy.data.worlds[0].use_nodes = 0
        ti.sleep(0.1)
        bpy.data.worlds[0].use_nodes = 1
    
def radexport():
    radmat()
    radpol