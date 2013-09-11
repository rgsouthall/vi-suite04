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
from . import vi_func


try:
    import numpy as numpy
    np = 1
except:
    np = 0

def radgexport(export_op, node):
    scene = bpy.context.scene
    scene.li_disp_panel = 0
    scene.vi_display = 0
    if bpy.context.active_object:
        bpy.ops.object.mode_set()
    radfilelist = []

    vi_func.clearscenee(scene)
    vi_func.clearscened(scene)
    scene.frame_start = 0
    scene.frame_end = 0 if node.animmenu == 'Static' else scene.frame_end

    for frame in range(scene.frame_start, node.fe + 1):
        scene.frame_current = frame
        radfile = open(node.filebase+"-{}.rad".format(frame), 'w')
        radfile.write("# Materials \n\n")
        for meshmat in bpy.data.materials:
            diff = [meshmat.diffuse_color[0]*meshmat.diffuse_intensity, meshmat.diffuse_color[1]*meshmat.diffuse_intensity, meshmat.diffuse_color[2]*meshmat.diffuse_intensity]
            if meshmat.livi_sense:
                meshmat.use_vertex_color_paint = 1
            if meshmat.use_shadeless == 1 or meshmat.livi_compliance:
                radfile.write("# Antimatter material\nvoid antimatter " + meshmat.name.replace(" ", "_") +"\n1 void\n0\n0\n\n")

            elif meshmat.emit > 0:
                radfile.write("# Light material\nvoid light " + meshmat.name.replace(" ", "_") +"\n0\n0\n3 {:.2f} {:.2f} {:.2f}\n".format(meshmat.emit * diff[0], meshmat.emit * diff[1], meshmat.emit * diff[2]))
                for o in [o for o in bpy.data.objects if o.type == 'MESH']:
                    if meshmat in [om for om in o.data.materials]:
                        o['merr'] = 1
                        export_op.report({'INFO'}, o.name+" has a emission material. Basic export routine used with no modifiers.")

            elif meshmat.use_transparency == False and meshmat.raytrace_mirror.use == True and meshmat.raytrace_mirror.reflect_factor >= 0.99:
                radfile.write("# Mirror material\nvoid mirror " + meshmat.name.replace(" ", "_") +"\n0\n0\n3 {0[0]} {0[1]} {0[2]}\n\n".format(meshmat.mirror_color))
                for o in [o for o in bpy.data.objects if o.type == 'MESH']:
                    if meshmat in [om for om in o.data.materials]:
                        o['merr'] = 1
                        export_op.report({'INFO'}, o.name+" has a mirror material. Basic export routine used with no modifiers.")

            elif meshmat.use_transparency == True and meshmat.transparency_method == 'RAYTRACE' and meshmat.alpha < 1.0 and meshmat.translucency == 0:
                if "{:.2f}".format(meshmat.raytrace_transparency.ior) == "1.52":
                    radfile.write("# Glass material\nvoid glass " + meshmat.name.replace(" ", "_") +"\n0\n0\n3 {:.3f} {:.3f} {:.3f}\n\n".format((1.0 - meshmat.alpha)*diff[0], (1.0 - meshmat.alpha)*diff[1], (1.0 - meshmat.alpha)*diff[2]))
                else:
                    radfile.write("# Glass material\nvoid glass " + meshmat.name.replace(" ", "_") +"\n0\n0\n4 {0:.3f} {1:.3f} {2:.3f} {3}\n\n".format((1.0 - meshmat.alpha)*diff[0], (1.0 - meshmat.alpha)*diff[1], (1.0 - meshmat.alpha)*diff[2], meshmat.raytrace_transparency.ior))

            elif meshmat.use_transparency == True and meshmat.transparency_method == 'RAYTRACE' and meshmat.alpha < 1.0 and meshmat.translucency > 0.001:
                radfile.write("# Translucent material\nvoid trans " + meshmat.name.replace(" ", "_")+"\n0\n0\n7 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1} {2} {3} {4}\n\n".format(diff, meshmat.specular_intensity, 1.0 - meshmat.specular_hardness/511.0, 1.0 - meshmat.alpha, 1.0 - meshmat.translucency))

            elif meshmat.use_transparency == False and meshmat.raytrace_mirror.use == True and meshmat.raytrace_mirror.reflect_factor < 0.99:
                radfile.write("# Metal material\nvoid metal " + meshmat.name.replace(" ", "_") +"\n0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1} {2}\n\n".format(diff, meshmat.specular_intensity, 1.0-meshmat.specular_hardness/511.0))
            else:
                radfile.write("# Plastic material\nvoid plastic " + meshmat.name.replace(" ", "_") +"\n0\n0\n5 {0[0]:.2f} {0[1]:.2f} {0[2]:.2f} {1:.2f} {2:.2f}\n\n".format(diff, meshmat.specular_intensity, 1.0-meshmat.specular_hardness/511.0))

        bpy.ops.object.select_all(action='DESELECT')
        radfile.close()

# geometry export routine

        obs = [geo for geo in scene.objects if geo.type == 'MESH' and not geo.children  and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True]

        for o in obs:
            o.select = True
            if node.animmenu == '1':
                bpy.ops.export_scene.obj(filepath=vi_func.obj(o.name, frame, node), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=True, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                objcmd = "obj2mesh -a {} {} {}".format(vi_func.mat(frame, node), vi_func.obj(o.name, frame, node), vi_func.mesh(o.name, frame, node))
            else:
                if frame == 0:
                    bpy.ops.export_scene.obj(filepath=vi_func.obj(o.name, frame, node), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=True, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                    objcmd = "obj2mesh -a {} {} {}".format(vi_func.mat(frame, node), vi_func.obj(o.name, frame, node), vi_func.mesh(o.name, frame, node))
            objrun = Popen(objcmd, shell = True, stderr = PIPE)
            o.select = False

            for line in objrun.stderr:
                if 'fatal' in str(line):
                    o.limerr = 1

            radfile = open(node.filebase+"-{}.rad".format(frame), 'a')
            radfile.write("# Geometry \n\n")
            if o.limerr == 0:
                radfile.write("void mesh id \n1 "+vi_func.mesh(o.name, frame, node)+"\n0\n0\n\n")

            else:
                export_op.report({'INFO'}, o.name+" could not be converted into a Radiance mesh and simpler export routine has been used. No un-applied object modifiers will be exported.")
                o.limerr = 0
                geomatrix = o.matrix_world
                for face in o.data.polygons:
                    try:
                        vertices = face.vertices[:]
                        radfile.write("# Polygon \n{} polygon poly_{}_{}\n0\n0\n{}\n".format(o.data.materials[face.material_index].name.replace(" ", "_"), o.data.name.replace(" ", "_"), face.index, 3*len(face.vertices)))
                        try:
                            if o.data.shape_keys and o.data.shape_keys.key_blocks[0] and o.data.shape_keys.key_blocks[1]:
                                for vertindex in vertices:
                                    sk0 = o.data.shape_keys.key_blocks[0]
                                    sk0co = geomatrix*sk0.data[vertindex].co
                                    sk1 = o.data.shape_keys.key_blocks[1]
                                    sk1co = geomatrix*sk1.data[vertindex].co
                                    radfile.write(" {} {} {}\n".format(sk0co[0]+(sk1co[0]-sk0co[0])*sk1.value, sk0co[1]+(sk1co[1]-sk0co[1])*sk1.value, sk0co[2]+(sk1co[2]-sk0co[2])*sk1.value))
                        except:
                            for vertindex in vertices:
                                radfile.write(" {0[0]} {0[1]} {0[2]}\n".format(geomatrix*o.data.vertices[vertindex].co))
                        radfile.write("\n")
                    except:
                        export_op.report({'ERROR'},"Make sure your object "+o.name+" has an associated material")

        radfile.write("# Lights \n\n")

        for geo in [geo for geo in scene.objects if (geo.ies_name != "" or 'lightarray' in geo.name) and geo.hide == False and geo.layers[0] == True]:
            if geo.ies_name != "":
                iesname = os.path.splitext(os.path.basename(geo.ies_name))[0]
                subprocess.call("ies2rad -t default -m {0} -c {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} -l / -p {2} -d{3} -o {4}-{5} {6}".format(geo.ies_strength, geo.ies_colour, node.newdir, geo.ies_unit, iesname, frame, geo.ies_name), shell=True)
                if geo.type == 'LAMP':
                    if geo.parent:
                        geo = geo.parent
                    radfile.write("!xform -rx {0} -ry {1} -rz {2} -t {3[0]} {3[1]} {3[2]} {4}.rad\n\n".format((180/pi)*geo.rotation_euler[0] - 180, (180/pi)*geo.rotation_euler[1], (180/pi)*geo.rotation_euler[2], geo.location, node.newdir+"/"+iesname+"-"+str(frame)))
                if 'lightarray' in geo.name:
                    spotmatrix = geo.matrix_world
                    rotation = geo.rotation_euler
                    for face in geo.data.polygons:
                        fx = sum([(spotmatrix*v.co)[0] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        fy = sum([(spotmatrix*v.co)[1] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        fz = sum([(spotmatrix*v.co)[2] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        radfile.write("!xform -rx {:.3f} -ry {:.3f} -rz {:.3f} -t {:.3f} {:.3f} {:.3f} {}\n".format((180/pi)*rotation[0], (180/pi)*rotation[1], (180/pi)*rotation[2], fx, fy, fz, node.newdir+"/"+iesname+"-"+str(frame)+".rad"))
        node.radfiles.append(radfile.name)
        radfile.write("# Sky \n\n")
        radfile.close()
        radfilelist.append(open(node.filebase+"-{}.rad".format(frame), 'r').read())

    node['radfiles'] = radfilelist

# rtrace export routine

    rtrace = open(node.filebase+".rtrace", "w")
    calcsurfverts = []
    calcsurffaces = []
    if 0 not in [len(geo.data.materials) for geo in bpy.data.objects if geo.type == 'MESH' and not geo.children and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True ]:
        for o, geo in enumerate(scene.objects):
            csf = []
            cverts = []
            if geo.type == 'MESH' and not geo.children and 'lightarray' not in geo.name and geo.hide == False and geo.layers[0] == True:
                if len([mat for mat in geo.material_slots if mat.material.livi_sense]) != 0:
                    obcalcverts = []
                    scene.objects.active = geo
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    mesh = geo.to_mesh(scene, True, 'PREVIEW', calc_tessface=False)
                    mesh.transform(geo.matrix_world)

                    for face in mesh.polygons:
                        if mesh.materials[face.material_index].livi_sense:
                            csf.append(face.index)
                            geo.licalc = 1
                            vsum = Vector((0, 0, 0))
                            scene.objects.active = geo
                            geo.select = True
                            bpy.ops.object.mode_set(mode = 'OBJECT')
                            for vc in geo.data.vertex_colors:
                                bpy.ops.mesh.vertex_color_remove()

                            if node.cpoint == '0':
                                for v in face.vertices:
                                    vsum += mesh.vertices[v].co
                                fc = vsum/len(face.vertices)
                                rtrace.write('{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(fc, face.normal[:]))
                                calcsurffaces.append((o, face))
                            else:

                                for v,vert in enumerate(face.vertices):
                                    if (mesh.vertices[vert]) not in obcalcverts:
                                        vcentx, vcenty, vcentz = mesh.vertices[vert].co[:]
                                        vnormx, vnormy, vnormz = (mesh.vertices[vert].normal*geo.matrix_world.inverted())[:]

                                        rtrace.write('{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(mesh.vertices[vert].co[:], (mesh.vertices[vert].normal*geo.matrix_world.inverted())[:]))
                                        obcalcverts.append(mesh.vertices[vert])
                                        cverts.append(vert)
                                calcsurfverts += obcalcverts
                    if node.cpoint == '1':
                        geo['cverts'] = cverts
                        geo['cfaces'] = []
                        node.reslen = len(calcsurfverts)

                    elif node.cpoint == '0':
                        geo['cverts'] = []
                        geo['cfaces'] = csf
                        node.reslen = len(calcsurffaces)
                    bpy.data.meshes.remove(mesh)
                else:
                    geo.licalc = 0
                    for mat in geo.material_slots:
                        mat.material.use_transparent_shadows = True

        rtrace.close()
        node.export = 1
    else:
        node.export = 0
        for geo in scene.objects:
            if geo.type == 'MESH' and geo.name != 'lightarray' and geo.hide == False and geo.layers[0] == True and not geo.data.materials:
                export_op.report({'ERROR'},"Make sure your object "+geo.name+" has an associated material")

def radcexport(export_op, node):
    skyfileslist = []
    scene = bpy.context.scene
    scene.li_disp_panel = 0
    scene.vi_display = 0
    vi_func.clearscenee(scene)
    vi_func.clearscened(scene)
    geonode = node.inputs[0].links[0].from_node
    if geonode.animmenu != 'Static' and node.animmenu != 'Static':
        export_op.report({'ERROR'},"You cannot run a geometry and time based animation at the same time")
    else:
        if node.skynum < 4:
            node.skytypeparams = ("+s", "+i", "-c", "-b 22.86 -c")[node.skynum]
            if node.skynum < 3:
                starttime = datetime.datetime(2013, 1, 1, node.shour) + datetime.timedelta(node.sdoy - 1)
            else:
                starttime = datetime.datetime(2013, 1, 1, 12)
            if node.animmenu == 'Time':
                endtime = datetime.datetime(2013, 1, 1, node.ehour) + datetime.timedelta(node.edoy - 1)
                hours = (endtime-starttime).days*24 + (endtime-starttime).seconds/3600
                scene.frame_end = int(hours/node.interval)
                geonode.fe = int(hours/node.interval)

#            geonode.fe = 0 if geonode.animmenu != 'Static' else scene.frame_end
            for frame in range(scene.frame_start, geonode.fe + 1):
                radskyhdrexport(scene, node, geonode, starttime, frame)
                if node.skynum < 2 and node.analysismenu != '2':
                    if frame == 0:
                        bpy.ops.object.lamp_add(type='SUN')
                        sun = bpy.context.object
                    sunexport(scene, node, starttime, frame, sun)

                skyexport(node, open(geonode.filebase+"-{}.sky".format(frame), 'a'))
                skyfileslist.append(open(geonode.filebase+"-{}.sky".format(frame), 'r').read())
            node['skyfiles'] = skyfileslist

        elif node.skynum == 4:
            if node.hdrname not in bpy.data.images:
                bpy.data.images.load(node.hdrname)
            hdrsky(open(geonode.filebase+"-0.sky", "w"), node.hdrname)
            node['skyfiles'] =  open(geonode.filebase+"-0.sky", 'r').read()

        elif node.skynum == 5:
            subprocess.call("cp {} {}".format(node.radname, geonode.filebase+"-0.sky"), shell = True)
            node['skyfiles'] =  open(node.radname, 'r').read()
            
        elif node.skynum == 6:
            node['skyfiles'] = ['']

    for frame in range(scene.frame_start, scene.frame_end + 1):
        fexport(scene, frame, export_op, node, geonode)

def radskyhdrexport(scene, node, geonode, starttime, frame):
    if node.skynum < 3:
        simtime = starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
        subprocess.call("gensky {} {} {}:{:0>2d}{} -a {} -o {} {} > {}".format(simtime.month, simtime.day, simtime.hour, simtime.minute, node.TZ, node.lati, node.longi, node.skytypeparams, vi_func.sky(frame, node, geonode)), shell = True)
    elif node.skynum == 3:
        subprocess.call("gensky {} {} {}:{:0>2d}{} -a {} -o {} {} > {}".format(1, 1, 12, 0, node.TZ, 50, 0, node.skytypeparams, vi_func.sky(frame, node, geonode)), shell = True)
    if node.hdr == True:
        subprocess.call("oconv {} > {}-{}sky.oct".format(vi_func.sky(frame, node, geonode), geonode.filebase, frame), shell=True)
        subprocess.call("cnt 250 500 | rcalc -f {}/lib/latlong.cal -e 'XD=500;YD=250;inXD=0.002;inYD=0.004' | rtrace -af pan.af -n {} -x 500 -y 250 -fac {}-{}sky.oct > {}/{}p.hdr".format(scene.vipath, geonode.nproc, geonode.filebase, frame, geonode.newdir, frame), shell=True)
        subprocess.call("rpict -vta -vp 0 0 0 -vd 1 0 0 -vu 0 0 1 -vh 360 -vv 360 -x 1000 -y 1000 {}-{}sky.oct > {}/{}.hdr".format(geonode.filebase, frame, geonode.newdir, frame), shell=True)

def sunexport(scene, node, starttime, frame, sun):
    simtime = starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
    deg2rad = 2*math.pi/360
    DS = 1 if node.daysav else 0
    ([solalt, solazi]) = vi_func.solarPosition(simtime.timetuple()[7], simtime.hour - DS + (simtime.minute)*0.016666, node.lati, node.longi)
    if node.skynum < 2:
        if frame == 0:
            sun.data.shadow_method = 'RAY_SHADOW'
            sun.data.shadow_ray_samples = 8
            sun.data.sky.use_sky = 1
            if node.skynum == 0:
                sun.data.shadow_soft_size = 0.1
                sun.data.energy = 5
            elif node.skynum == 1:
                sun.data.shadow_soft_size = 3
                sun.data.energy = 3
            sun.location = (0,0,10)
        sun.rotation_euler = (90-solalt)*deg2rad, 0, solazi*deg2rad
        sun.keyframe_insert(data_path = 'location', frame = frame)
        sun.keyframe_insert(data_path = 'rotation_euler', frame = frame)
        sun.data.cycles.use_multiple_importance_sampling = True
        sun.data.shadow_soft_size = 0.01

    bpy.ops.object.select_all()

def skyexport(node, rad_sky):
    rad_sky.write("\nskyfunc glow skyglow\n0\n0\n")
    rad_sky.write("4 .8 .8 1 0\n\n") if node.skynum < 3 else rad_sky.write("4 1 1 1 0\n\n")
    rad_sky.write("skyglow source sky\n0\n0\n4 0 0 1  180\n\n")
    rad_sky.write("skyfunc glow groundglow\n0\n0\n4 .8 1.1 .8  0\n\n")
    rad_sky.write("groundglow source ground\n0\n0\n4 0 0 -1  180\n\n")
    rad_sky.close()

def hdrsky(rad_sky, skyfile):
    rad_sky.write("# Sky material\nvoid colorpict hdr_env\n7 red green blue {} angmap.cal sb_u sb_v\n0\n0\n\nhdr_env glow env_glow\n0\n0\n4 1 1 1 0\n\nenv_glow bubble sky\n0\n0\n4 0 0 0 500\n\n".format(skyfile))
    rad_sky.close()

def fexport(scene, frame, export_op, node, geonode):
    radfile = open(geonode.filebase+"-{}.rad".format(frame), 'w')
    radfile.write(geonode['radfiles'][0] + node['skyfiles'][frame]) if len(geonode['radfiles']) == 1 else radfile.write(geonode['radfiles'][frame] + node['skyfiles'][0])
    radfile.close()
    try:
        subprocess.call("oconv -w {0}-{1}.rad > {0}-{1}.oct".format(geonode.filebase, frame), shell=True)
        node.export = 1
    except:
        export_op.report({'ERROR'},"There is a problem with geometry export. If created in another package simplify the geometry, and turn off smooth shading")
        node.export = 0
    export_op.report({'INFO'},"Export is finished")
    scene.frame_set(0)

def cyfc1(self):
    if bpy.data.scenes[0].render.engine == "CYCLES":
        for materials in bpy.data.materials:
            if materials.use_nodes == 1:
                try:
                    if materials.livi_sense:
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