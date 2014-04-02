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

import bpy, os, math, subprocess, datetime
import time as ti
from math import sin, cos, tan, pi
from mathutils import Vector
from subprocess import PIPE, Popen, STDOUT
from .vi_func import retsky, retmat, retobj, retmesh, clearscene, \
solarPosition, mtx2vals, retobjs, radmat

try:
    import numpy
    np = 1
except:
    np = 0

def radgexport(export_op, node, **kwargs):
    scene = bpy.context.scene
    
    if bpy.context.active_object and bpy.context.active_object.type == 'MESH' and bpy.context.active_object.hide == 0:
        bpy.ops.object.mode_set()
    radfilelist = []

    if export_op.nodeid.split('@')[0] == 'LiVi Geometry':
        clearscene(scene, export_op)
        (scene.fs, scene.gfe, scene.cfe) = (scene.frame_start, scene.frame_end, scene.frame_start) if node.animmenu != 'Static' else (0, 0, 0)
    else:
        (scene.fs, scene.gfe, scene.cfe) = [kwargs['genframe']] * 3 if kwargs.get('genframe') else (0, 0, 0)

    for frame in range(scene.fs, scene.gfe + 1):        
        if export_op.nodeid.split('@')[0] == 'LiVi Geometry':
            scene.frame_set(frame)

        radfile = "# Materials \n\n"
        for meshmat in bpy.data.materials:
            radname, matname, radnums = radmat(meshmat, scene)
            radfile += '# {0} material\nvoid {0} {1}\n0\n0\n{2}\n\n'.format(radname, matname, radnums) if radname != 'antimatter' \
                else '# {0} material\nvoid {0} {1}\n1 void\n0\n0\n\n'.format(radname, matname)
            if radname in ('light', 'mirror'):
                for o in retobjs('livig'):
                    if meshmat in list(o.data.materials):
                        o['merr'] = 1 
                    export_op.report({'INFO'}, o.name+" has a emission or mirror material. Basic export routine used with no modifiers.")
            meshmat['RadMat'] = {radname: (matname, radnums)}
            meshmat.use_vertex_color_paint = 1 if meshmat.livi_sense else 0
        bpy.ops.object.select_all(action='DESELECT')

        with open(node.filebase+"-{}.rad".format(frame), 'w') as radmatfile:
            radmatfile.write(radfile)

        # Geometry export routine

        radfile += "# Geometry \n\n"
        for o in retobjs('livig'):
            o.select = True
            if o.get('merr') != 1:
                if node.animmenu == 'Geometry':# or export_op.nodeid.split('@')[0] == 'LiVi Simulation':
                    bpy.ops.export_scene.obj(filepath=retobj(o.name, scene.frame_current, node), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=True, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=True, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                    objcmd = "obj2mesh -w -a {} {} {}".format(retmat(frame, node), retobj(o.name, scene.frame_current, node), retmesh(o.name, scene.frame_current, node))
                    objrun = Popen(objcmd, shell = True, stdout = PIPE)                
                elif export_op.nodeid.split('@')[0] == 'LiVi Simulation':
                    bpy.ops.export_scene.obj(filepath=retobj(o.name, scene.frame_start, node), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=True, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=True, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                    objcmd = "obj2mesh -w -a {} {} {}".format(retmat(scene.frame_start, node), retobj(o.name, scene.frame_start, node), retmesh(o.name, scene.frame_start, node))
                    objrun = Popen(objcmd, shell = True, stdout = PIPE)
                else:
                    if frame == scene.fs:                        
                        bpy.ops.export_scene.obj(filepath=retobj(o.name, scene.frame_current, node), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=True, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=True, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                        objcmd = "obj2mesh -w -a {} {} {}".format(retmat(frame, node), retobj(o.name, scene.frame_current, node), retmesh(o.name, scene.frame_current, node))
                        objrun = Popen(objcmd, shell = True, stdout = PIPE)

                for line in objrun.stdout:
                    if 'fatal' in str(line):
                        print('Mesh export error: '+ line)
                        o['merr'] = 1
                        break
                o.select = False

            if o.get('merr') != 1:
                radfile += "void mesh id \n1 "+retmesh(o.name, frame, node)+"\n0\n0\n\n"
            else:
                export_op.report({'INFO'}, o.name+" could not be converted into a Radiance mesh and simpler export routine has been used. No un-applied object modifiers will be exported.")
                if o.get('merr'):
                    del o['merr']
                geomatrix = o.matrix_world
                for face in o.data.polygons:
                    try:
                        vertices = face.vertices[:]
                        radfile += "# Polygon \n{} polygon poly_{}_{}\n0\n0\n{}\n".format(o.data.materials[face.material_index].name.replace(" ", "_"), o.data.name.replace(" ", "_"), face.index, 3*len(face.vertices))
                        if o.data.shape_keys and o.data.shape_keys.key_blocks[0] and o.data.shape_keys.key_blocks[1]:
                            for vertindex in vertices:
                                sk0, sk1 = o.data.shape_keys.key_blocks[0:2]
                                sk0co, sk1co = geomatrix*sk0.data[vertindex].co, geomatrix*sk1.data[vertindex].co
                                radfile += " {} {} {}\n".format(sk0co[0]+(sk1co[0]-sk0co[0])*sk1.value, sk0co[1]+(sk1co[1]-sk0co[1])*sk1.value, sk0co[2]+(sk1co[2]-sk0co[2])*sk1.value)
                        else:
                            for vertindex in vertices:
                                radfile += " {0[0]} {0[1]} {0[2]}\n".format(geomatrix*o.data.vertices[vertindex].co)
                        radfile += "\n"
                    except:
                        export_op.report({'ERROR'},"Make sure your object "+o.name+" has an associated material")

        # Lights export routine

        radfile += "# Lights \n\n"

        for geo in retobjs('livil'):
            if geo.ies_name != "":
                iesname = os.path.splitext(os.path.basename(geo.ies_name))[0]
                subprocess.call("ies2rad -t default -m {0} -c {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} -l / -p {2} -d{3} -o {4}-{5} {6}".format(geo.ies_strength, geo.ies_colour, node.newdir, geo.ies_unit, iesname, frame, geo.ies_name), shell=True)
                if geo.type == 'LAMP':
                    if geo.parent:
                        geo = geo.parent
                    radfile += "!xform -rx {0} -ry {1} -rz {2} -t {3[0]} {3[1]} {3[2]} {4}.rad\n\n".format((180/pi)*geo.rotation_euler[0] - 180, (180/pi)*geo.rotation_euler[1], (180/pi)*geo.rotation_euler[2], geo.location, node.newdir+os.path.sep+iesname+"-"+str(frame))
                if 'lightarray' in geo.name:
                    spotmatrix, rotation = geo.matrix_world, geo.rotation_euler
                    for face in geo.data.polygons:
                        fx = sum([(spotmatrix*v.co)[0] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        fy = sum([(spotmatrix*v.co)[1] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        fz = sum([(spotmatrix*v.co)[2] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                        radfile += "!xform -rx {:.3f} -ry {:.3f} -rz {:.3f} -t {:.3f} {:.3f} {:.3f} {}\n".format((180/pi)*rotation[0], (180/pi)*rotation[1], (180/pi)*rotation[2], fx, fy, fz, node.newdir+os.path.sep+iesname+"-"+str(frame)+".rad")
        radfile += "# Sky \n\n"
        radfilelist.append(radfile)

    node['radfiles'] = radfilelist
    connode = node.outputs['Geometry out'].links[0].to_node if node.outputs['Geometry out'].is_linked else 0

    node.bl_label = node.bl_label[1:] if node.bl_label[0] == '*' else node.bl_label

    for frame in range(scene.fs, scene.gfe + 1):
        fexport(scene, frame, export_op, node, connode)

# rtrace export routine
    with open(node.filebase+".rtrace", "w") as rtrace:
        reslen = 0
        geos = retobjs('livig') if export_op.nodeid.split('@')[0] == 'LiVi Geometry' else retobjs('livic')
        for o, geo in enumerate(geos):
            if len(geo.data.materials) > 0:
                if len([mat for mat in geo.material_slots if mat.material.livi_sense]) > 0:
                    geo['licalc'], cverts, obcalcverts, csv, csf, scene.objects.active = 1, [], [], [], [], geo
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    mesh = geo.to_mesh(scene, True, 'PREVIEW', calc_tessface=False)
                    mesh.transform(geo.matrix_world)
                    scene.objects.active = geo
                    for face in mesh.polygons:
                        if mesh.materials[face.material_index].livi_sense:
                            face.select, vsum,  = True, Vector((0, 0, 0))
                            csf.append(face.index)
                            reslen += 1

                            if node.cpoint == '0':
                                for v in face.vertices:
                                    vsum += mesh.vertices[v].co
                                fc = vsum/len(face.vertices)
                                rtrace.write('{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(fc, face.normal.normalized()[:]))
                            else:
                                for v,vert in enumerate(face.vertices):
                                    if vert not in cverts:
                                        vcentx, vcenty, vcentz = mesh.vertices[vert].co[:]
                                        vnormx, vnormy, vnormz = (mesh.vertices[vert].normal*geo.matrix_world.inverted())[:]
                                        reslen += 1
                                        rtrace.write('{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(mesh.vertices[vert].co[:], (mesh.vertices[vert].normal*geo.matrix_world.inverted()).normalized()[:]))
                                        cverts.append(vert)
                    (geo['cverts'], geo['cfaces']) = (cverts, csf) if node.cpoint == '1' else ([], csf)                    
                    bpy.data.meshes.remove(mesh)
                else:
                    if geo.get('licalc'):
                        del geo['licalc']
                    for mat in geo.material_slots:
                        mat.material.use_transparent_shadows = True
            else:
                node.export = 0
                export_op.report({'ERROR'},"Make sure your object "+geo.name+" has an associated material")
        node.reslen = reslen
    scene.fe = max(scene.cfe, scene.gfe)
    node.export = 1

def radcexport(export_op, node):
    skyfileslist, scene, scene.li_disp_panel, scene.vi_display = [], bpy.context.scene, 0, 0
    scene['LiViContext'] = node.bl_label
    clearscene(scene, export_op)
    geonode = node.inputs['Geometry in'].links[0].from_node

    if node.bl_label != 'LiVi CBDM':
        node['Animation'] = ('Static', '', 'TAnimated', 'Animated', 'GAnimated')[(geonode.animmenu == 'Static' and (node.animmenu == 'Static' or node.skynum > 2), \
        geonode.animmenu != 'Static' and node.animmenu != 'Static', node.animmenu == 'Time' and node.skynum < 3, geonode.animmenu != 'Static').index(1)]
        if not node['Animation']:
            export_op.report({'ERROR'},"You cannot run a geometry and time based animation at the same time")
            return
        scene.cfe = 0

        if node.skynum < 4:
            starttime = datetime.datetime(2013, 1, 1, int(node.shour), int((node.shour - int(node.shour))*60)) + datetime.timedelta(node.sdoy - 1) if node.skynum < 3 else datetime.datetime(2013, 1, 1, 12)
            if node.animmenu == 'Time' and node.skynum < 3:
                endtime = datetime.datetime(2013, 1, 1, int(node.ehour), int((node.ehour - int(node.ehour))*60)) + datetime.timedelta(node.edoy - 1)
                hours = (endtime-starttime).days*24 + (endtime-starttime).seconds/3600
                scene.cfe = scene.frame_end = scene.fs + int(hours/node.interval) 

            for frame in range(scene.fs, scene.cfe + 1):
                sunexport(scene, node, geonode, starttime, frame - scene.fs)
                if node.skynum < 2 and node.analysismenu != '2':
                    if frame == scene.frame_start:
                        if 'Sun' in [ob for ob in scene.objects if ob.get('VIType')]:
                            sun = [ob for ob in scene.objects if ob.get('VIType')][0]
                        else:
                            bpy.ops.object.lamp_add(type='SUN')
                            sun = bpy.context.object
                            sun['VIType'] = 'Sun'
                    blsunexport(scene, node, starttime, frame - scene.fs, sun)
                with open(geonode.filebase+"-{}.sky".format(frame), 'a') as skyfilea:
                    skyexport(node, skyfilea)
                with open(geonode.filebase+"-{}.sky".format(frame), 'r') as skyfiler:
                    skyfileslist.append(skyfiler.read())
                if node.hdr == True:
                    hdrexport(scene, frame, node, geonode)

            node['skyfiles'] = skyfileslist

        elif node.skynum == 4:
            if node.hdrname not in bpy.data.images:
                bpy.data.images.load(node.hdrname)
            node['skyfiles'] = [hdrsky(node.hdrname)]

        elif node.skynum == 5:
            subprocess.call("cp {} {}".format(node.radname, geonode.filebase+"-0.sky"), shell = True)
            with open(node.radname, 'r') as radfiler:
                node['skyfiles'] =  [radfiler.read()]

        elif node.skynum == 6:
            node['skyfiles'] = ['']

    elif node.bl_label == 'LiVi CBDM':
        node['Animation'] = 'Static' if geonode.animmenu == 'Static' else 'Animated'
        if not node.fromnode:            
            node['source'] = node.sourcemenu if int(node.analysismenu) > 1 else node.sourcemenu2
            if node['source'] == '0' and node.inputs['Location in'].is_linked:
                locnode = node.inputs['Location in'].links[0].from_node
                if locnode.endmonth < locnode.startmonth:
                    export_op.report({'ERROR'}, "End month is earlier than start month")
                    return
                os.chdir(geonode.newdir)
                pcombfiles = ""
                for i in range(0, 146):
                    pcombfiles = pcombfiles + "ps{}.hdr ".format(i)
                epwbase = os.path.splitext(os.path.basename(locnode.weather))
                if epwbase[1] in (".epw", ".EPW"):
                    with open(locnode.weather, "r") as epwfile:
                        epwlines = epwfile.readlines()
                        epwyear = epwlines[8].split(",")[0]
                        with open(geonode.newdir+os.path.sep+epwbase[0]+".wea", "w") as wea:
                            wea.write("place {0[1]}\nlatitude {0[6]}\nlongitude {0[7]}\ntime_zone {0[8]}\nsite_elevation {0[9]}weather_data_file_units 1\n".format(epwlines[0].split(",")))
                            for epwline in epwlines[8:]:
                                if int(epwline.split(",")[1]) in range(locnode.startmonth, locnode.endmonth + 1):
                                    wea.write("{0[1]} {0[2]} {0[3]} {0[14]} {0[15]} \n".format(epwline.split(",")))
                        subprocess.call("gendaymtx -m 1 {0} {1}.wea > {1}.mtx".format(('', '-O1')[node.analysismenu in ('1', '3')], geonode.newdir+os.path.sep+epwbase[0]), shell=True)                       
                else:
                    export_op.report({'ERROR'}, "Not a valid EPW file")
                    return
    
                mtxfile = open(geonode.newdir+os.path.sep+epwbase[0]+".mtx", "r")
            
            elif node['source'] == '1' and int(node.analysismenu) > 1:
                mtxfile = open(node.mtxname, "r")
    
            if node['source'] == '0':
                if node.inputs['Location in'].is_linked:
                    mtxlines = mtxfile.readlines()
                    vecvals, vals = mtx2vals(mtxlines, datetime.datetime(int(epwyear), 1, 1).weekday(), locnode)
                    mtxfile.close()
                    node['vecvals'] = vecvals
                    node['whitesky'] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"
                    oconvcmd = "oconv -w - > {0}-whitesky.oct".format(geonode.filebase)
                    Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = node['whitesky'].encode('utf-8'))
                    subprocess.call("vwrays -ff -x 600 -y 600 -vta -vp 0 0 0 -vd 0 1 0 -vu 0 0 1 -vh 360 -vv 360 -vo 0 -va 0 -vs 0 -vl 0 | rcontrib -bn 146 -fo -ab 0 -ad 1 -n {} -ffc -x 600 -y 600 -ld- -V+ -f tregenza.cal -b tbin -o p%d.hdr -m sky_glow {}-whitesky.oct".format(geonode.nproc, geonode.filename), shell = True)
                    if int(node.analysismenu) < 2:
                        for j in range(0, 146):
                            subprocess.call("pcomb -s {0} p{1}.hdr > ps{1}.hdr".format(vals[j], j), shell = True)
                            subprocess.call("{0}  p{1}.hdr".format(geonode.rm, j), shell = True)        
                        subprocess.call("pcomb -h  "+pcombfiles+" > "+geonode.newdir+os.path.sep+epwbase[0]+".hdr", shell = True)
                        subprocess.call(geonode.rm+" ps*.hdr" , shell = True)
                        node.hdrname = geonode.newdir+os.path.sep+epwbase[0]+".hdr"
                    
                    if node.sourcemenu == '0' and node.hdr:
                        Popen("oconv -w - > {}{}{}.oct".format(geonode.newdir, os.path.sep, epwbase[0]), shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = hdrsky(geonode.newdir+os.path.sep+epwbase[0]+".hdr").encode('utf-8'))
                        subprocess.call('cnt 750 1500 | rcalc -f "'+os.path.join(scene.vipath, 'lib', 'latlong.cal"')+' -e "XD=1500;YD=750;inXD=0.000666;inYD=0.001333" | rtrace -af pan.af -n {} -x 1500 -y 750 -fac "{}{}{}.oct" > '.format(geonode.nproc, geonode.newdir, os.path.sep, epwbase[0]) + '"'+os.path.join(geonode.newdir, epwbase[0]+'p.hdr')+'"', shell=True)
                else:
                    export_op.report({'ERROR'}, "No location node connected")
                    return
            if node.hdrname not in bpy.data.images:
                bpy.data.images.load(node.hdrname)
            node['skyfiles'] = [hdrsky(node.hdrname)]
    scene.fe = max(scene.cfe, scene.gfe)
    for frame in range(scene.fs, scene.fe + 1):
        fexport(scene, frame, export_op, node, geonode)
    scene.frame_set(scene.fs)
    node.export = 1

def sunexport(scene, node, geonode, starttime, frame):
    if node.skynum < 3:        
        simtime = starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
        solalt, solazi, beta, phi = solarPosition(simtime.timetuple()[7], simtime.hour + (simtime.minute)*0.016666, scene.latitude, scene.longitude)
        subprocess.call("gensky -ang {} {} {} > {}".format(solalt, solazi, node.skytypeparams, retsky(frame, node, geonode)), shell = True)
    elif node.skynum == 3:
        subprocess.call("gensky -ang {} {} {} > {}".format(45, 0, node.skytypeparams, retsky(frame, node, geonode)), shell = True)

def hdrexport(scene, frame, node, geonode):
    subprocess.call("oconv {} > {}-{}sky.oct".format(retsky(frame, node, geonode), geonode.filebase, frame), shell=True)
    subprocess.call("rpict -vta -vp 0 0 0 -vd 0 1 0 -vu 0 0 1 -vh 360 -vv 360 -x 1500 -y 1500 {0}-{1}sky.oct > ".format(geonode.filebase, frame) + os.path.join(geonode.newdir, str(frame)+".hdr"), shell=True)
    subprocess.call('cnt 750 1500 | rcalc -f "'+os.path.join(scene.vipath, 'lib', 'latlong.cal"')+' -e "XD=1500;YD=750;inXD=0.000666;inYD=0.001333" | rtrace -af pan.af -n {0} -x 1500 -y 750 -fac "{1}-{2}sky.oct" > '.format(geonode.nproc, geonode.filebase, frame) + '"'+os.path.join(geonode.newdir, str(frame)+'p.hdr')+'"', shell=True)
    if '{}p.hdr'.format(frame) not in bpy.data.images:
        bpy.data.images.load(os.path.join(geonode.newdir, str(frame)+"p.hdr"))
    else:
        bpy.data.images['{}p.hdr'.format(frame)].reload()

def blsunexport(scene, node, starttime, frame, sun):
    simtime = starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
    solalt, solazi, beta, phi = solarPosition(simtime.timetuple()[7], simtime.hour + (simtime.minute)*0.016666, scene.latitude, scene.longitude)
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
        sun.location = [x*20 for x in (-sin(phi), -cos(phi), tan(beta))]
        sun.rotation_euler = (math.pi/2) - beta, 0, -phi
        if scene.render.engine == 'CYCLES':# and bpy.data.worlds['World'].get('node_tree'):
            if 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)#sin(phi), -cos(phi), -2* beta/math.pi
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].keyframe_insert(data_path = 'sun_direction', frame = frame)
        sun.keyframe_insert(data_path = 'location', frame = frame)
        sun.keyframe_insert(data_path = 'rotation_euler', frame = frame)
        sun.data.cycles.use_multiple_importance_sampling = True
        sun.data.shadow_soft_size = 0.01
    bpy.ops.object.select_all()

def skyexport(node, rad_sky):
    rad_sky.write("\nskyfunc glow skyglow\n0\n0\n")
    rad_sky.write("4 .8 .8 1 0\n\n") if node.skynum < 3 else rad_sky.write("4 1 1 1 0\n\n")
    rad_sky.write("skyglow source sky\n0\n0\n4 0 0 1  180\n\n")

def hdrsky(skyfile):
    return("# Sky material\nvoid colorpict hdr_env\n7 red green blue {} angmap.cal sb_u sb_v\n0\n0\n\nhdr_env glow env_glow\n0\n0\n4 1 1 1 0\n\nenv_glow bubble sky\n0\n0\n4 0 0 0 5000\n\n".format(skyfile))

def fexport(scene, frame, export_op, node, othernode):
    (geonode, connode) = (node, othernode) if 'LiVi Geometry' in node.bl_label else (othernode, node)
    if not connode or not connode.get('Animation'):
        radtext = geonode['radfiles'][0] if len(geonode['radfiles']) == 1 else geonode['radfiles'][frame]
    else:
        skyframe = frame if connode and connode['Animation'] == 'TAnimated' else 0
        radtext = geonode['radfiles'][0] + connode['skyfiles'][skyframe] if len(geonode['radfiles']) == 1 else geonode['radfiles'][frame] + connode['skyfiles'][0]

    with open(geonode.filebase+"-{}.rad".format(frame), 'w') as radfile:
        radfile.write(radtext)
        
    if not bpy.data.texts.get('Radiance input-{}'.format(frame)):
        bpy.data.texts.new('Radiance input-{}'.format(frame))
    bpy.data.texts['Radiance input-{}'.format(frame)].clear()
    bpy.data.texts['Radiance input-{}'.format(frame)].write(radtext)
    
    oconvcmd = "oconv -w {0}-{1}.rad > {0}-{1}.oct".format(geonode.filebase, frame)
#    This next line allows the radiance scene description to be piped into the oconv command.
#   oconvcmd = "oconv -w - > {0}-{1}.oct".format(geonode.filebase, frame).communicate(input = radtext.encode('utf-8'))
    Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT)#.communicate(input = radtext.encode('utf-8'))
    
    export_op.report({'INFO'},"Export is finished")

def cyfc1(self):
    if bpy.data.scenes[0].render.engine == "CYCLES":
        scene = bpy.context.scene
        for material in bpy.data.materials:
            if material.use_nodes == 1:
                try:
                    if material.livi_sense or material.vi_shadow and material.node_tree.nodes.get('Attribute'):
                        material.node_tree.nodes["Attribute"].attribute_name = str(scene.frame_current)
                except Exception as e:
                    print(e, 'Something wrong with changing the material attribute name')

        if bpy.data.worlds.get('World'):
            if bpy.data.worlds["World"].use_nodes == False:
                bpy.data.worlds["World"].use_nodes = True
            nt = bpy.data.worlds[0].node_tree

        for ob in scene.objects:
            if ob.get('VIType') == 'Sun':
                sun = ob
            if scene.resnode == 'VI Sun Path':
                if ob.get('VIType') == 'SunMesh':
                    sunob = ob
                if ob.get('VIType') == 'SPathMesh':
                    spathob = ob
        
        if scene.resnode == 'VI Sun Path':
            beta, phi = solarPosition(scene.solday, scene.solhour, scene.latitude, scene.longitude)[2:]
            if nt.nodes.get('Sky Texture'):
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)
            spathob.scale = 3 * [scene.soldistance/100]
            sunob.scale = 3*[scene.soldistance/100]
            sunob.location.z = sun.location.z = spathob.location.z + scene.soldistance * sin(beta)
            sunob.location.x = sun.location.x = spathob.location.x -(scene.soldistance**2 - (sun.location.z-spathob.location.z)**2)**0.5  * sin(phi)
            sunob.location.y = sun.location.y = spathob.location.y -(scene.soldistance**2 - (sun.location.z-spathob.location.z)**2)**0.5 * cos(phi)
            sun.rotation_euler = pi * 0.5 - beta, 0, -phi

            if sun.data.node_tree:
                for blnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Blackbody']:
                    blnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5
                for emnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Emission']:
                    emnode.inputs[1].default_value = 5 * sin(beta)

            if sunob.data.materials[0].node_tree:
                for smblnode in [node for node in sunob.data.materials[0].node_tree.nodes if sunob.data.materials and node.bl_label == 'Blackbody']:
                    smblnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5

        bpy.data.worlds[0].use_nodes = 0
        ti.sleep(0.1)
        bpy.data.worlds[0].use_nodes = 1
    else:
        return