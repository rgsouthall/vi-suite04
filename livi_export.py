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
solarPosition, mtx2vals, retobjs, radmat, selobj

try:
    import numpy
    np = 1
except:
    np = 0

def radgexport(export_op, node, **kwargs):
    scene = bpy.context.scene
    radfiles = []

    if export_op.nodeid.split('@')[0] == 'LiVi Geometry':
        clearscene(scene, export_op)
        scene.fs = scene.frame_start if node.animmenu != 'Static' else 0
    else:
        (scene.fs, scene.gfe, node['frames']['Material'], node['frames']['Geometry'], node['frames']['Lights']) = [kwargs['genframe']] * 5 if kwargs.get('genframe') else (0, 0, 0, 0, 0)
        scene.cfe = 0
        
    for frame in range(scene.fs, scene.gfe + 1):        
        if export_op.nodeid.split('@')[0] == 'LiVi Geometry':
            scene.frame_set(frame)
        
        if frame in range(node['frames']['Material'] + 1):
            mradfile = "# Materials \n\n"
            for meshmat in bpy.data.materials:
                radname, matname, radnums = radmat(meshmat, scene)
                mradfile += '# {0} material\nvoid {0} {1}\n0\n0\n{2}\n\n'.format(radname, matname, radnums) if radname != 'antimatter' \
                    else '# {0} material\nvoid {0} {1}\n1 void\n0\n0\n\n'.format(radname, matname)
                if radname in ('light', 'mirror'):
                    for o in retobjs('livig'):
                        if meshmat in list(o.data.materials):
                            o['merr'] = 1 
                        export_op.report({'INFO'}, o.name+" has a emission or mirror material. Basic export routine used with no modifiers.")
                meshmat['RadMat'] = {radname: (matname, radnums)}
                meshmat.use_vertex_color_paint = 1 if meshmat.livi_sense else 0
            bpy.ops.object.select_all(action='DESELECT')
            
            tempmatfilename = node.filebase+".tempmat"
            with open(tempmatfilename, "w") as tempmatfile:
                tempmatfile.write(mradfile)
                
        # Geometry export routine
        
        if frame in range(max(node['frames']['Geometry'], node['frames']['Material']) + 1):
            gframe = scene.frame_current if node['frames']['Geometry'] > 0 else 0
            mframe = scene.frame_current if node['frames']['Material'] > 0 else 0
            gradfile = "# Geometry \n\n"
            for o in retobjs('livig'):
                if not kwargs.get('mo') or (kwargs.get('mo') and o in kwargs['mo']):
                    selobj(scene, o)
                    if o.get('merr') != 1:
                        if node.animmenu in ('Geometry'' Material'):# or export_op.nodeid.split('@')[0] == 'LiVi Simulation':
                            bpy.ops.export_scene.obj(filepath=retobj(o.name, gframe, node, scene), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=False, use_nurbs=True, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                            objcmd = "obj2mesh -w -a {} {} {}".format(tempmatfilename, retobj(o.name, gframe, node, scene), retmesh(o.name, max(gframe, mframe), node, scene)) 
                        elif export_op.nodeid.split('@')[0] == 'LiVi Simulation':
                            bpy.ops.export_scene.obj(filepath=retobj(o.name, scene.frame_start, node, scene), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=False, use_nurbs=True, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                            objcmd = "obj2mesh -w -a {} {} {}".format(retmat(scene.frame_start, node, scene), retobj(o.name, scene.frame_start, node), retmesh(o.name, scene.frame_start, node, scene))
                        else:
                            if frame == scene.fs:                        
                                bpy.ops.export_scene.obj(filepath=retobj(o.name, scene.frame_current, node, scene), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=False, use_nurbs=True, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                                objcmd = "obj2mesh -w -a {} {} {}".format(retmat(frame, node, scene), retobj(o.name, scene.frame_current, node, scene), retmesh(o.name, scene.frame_current, node, scene))
                            else:
                                objcmd = ''
                        objrun = Popen(objcmd, shell = True, stdout = PIPE, stderr=STDOUT)
                        
                        for line in objrun.stdout:
                            if 'non-triangle' in line.decode():
                                export_op.report({'INFO'}, o.name+" has an incompatible mesh. Doing a simplified export")
                                o['merr'] = 1
                                break

                        o.select = False
    
                if o.get('merr') != 1:
                    gradfile += "void mesh id \n1 "+retmesh(o.name, max(gframe, mframe), node, scene)+"\n0\n0\n\n"
                else:
                    export_op.report({'INFO'}, o.name+" could not be converted into a Radiance mesh and simpler export routine has been used. No un-applied object modifiers will be exported.")
                    if o.get('merr'):
                        del o['merr']
                    geomatrix = o.matrix_world
                    for face in o.data.polygons:
                        try:
                            vertices = face.vertices[:]
                            gradfile += "# Polygon \n{} polygon poly_{}_{}\n0\n0\n{}\n".format(o.data.materials[face.material_index].name.replace(" ", "_"), o.data.name.replace(" ", "_"), face.index, 3*len(face.vertices))
                            if o.data.shape_keys and o.data.shape_keys.key_blocks[0] and o.data.shape_keys.key_blocks[1]:
                                for vertindex in vertices:
                                    sk0, sk1 = o.data.shape_keys.key_blocks[0:2]
                                    sk0co, sk1co = geomatrix*sk0.data[vertindex].co, geomatrix*sk1.data[vertindex].co
                                    gradfile += " {} {} {}\n".format(sk0co[0]+(sk1co[0]-sk0co[0])*sk1.value, sk0co[1]+(sk1co[1]-sk0co[1])*sk1.value, sk0co[2]+(sk1co[2]-sk0co[2])*sk1.value)
                            else:
                                for vertindex in vertices:
                                    gradfile += " {0[0]} {0[1]} {0[2]}\n".format(geomatrix*o.data.vertices[vertindex].co)
                            gradfile += "\n"
                        except:
                            export_op.report({'ERROR'},"Make sure your object "+o.name+" has an associated material")

        # Lights export routine
        if frame in range(node['frames']['Lights'] + 1):
            lradfile = "# Lights \n\n"
    
            for geo in retobjs('livil'):
                if geo.ies_name != "":
                    iesname = os.path.splitext(os.path.basename(geo.ies_name))[0]
                    subprocess.call("ies2rad -t default -m {0} -c {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} -l / -p {2} -d{3} -o {4}-{5} {6}".format(geo.ies_strength, geo.ies_colour, node.newdir, geo.ies_unit, iesname, frame, geo.ies_name), shell=True)
                    if geo.type == 'LAMP':
                        if geo.parent:
                            geo = geo.parent
                        lradfile += "!xform -rx {0} -ry {1} -rz {2} -t {3[0]} {3[1]} {3[2]} {4}.rad\n\n".format((180/pi)*geo.rotation_euler[0] - 180, (180/pi)*geo.rotation_euler[1], (180/pi)*geo.rotation_euler[2], geo.location, node.newdir+os.path.sep+iesname+"-"+str(frame))
                    if 'lightarray' in geo.name:
                        spotmatrix, rotation = geo.matrix_world, geo.rotation_euler
                        for face in geo.data.polygons:
                            fx = sum([(spotmatrix*v.co)[0] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                            fy = sum([(spotmatrix*v.co)[1] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                            fz = sum([(spotmatrix*v.co)[2] for v in geo.data.vertices if v.index in face.vertices])/len(face.vertices)
                            lradfile += "!xform -rx {:.3f} -ry {:.3f} -rz {:.3f} -t {:.3f} {:.3f} {:.3f} {}\n".format((180/pi)*rotation[0], (180/pi)*rotation[1], (180/pi)*rotation[2], fx, fy, fz, node.newdir+os.path.sep+iesname+"-"+str(frame)+".rad")
        sradfile = "# Sky \n\n"
        radfiles.append(mradfile+gradfile+lradfile+sradfile)
    
    node['radfiles'] = radfiles
    connode = node.outputs['Geometry out'].links[0].to_node if node.outputs['Geometry out'].is_linked else 0

    for frame in range(scene.fs, scene.gfe + 1):
        fexport(scene, frame, export_op, node, connode)

# rtrace export routine
    
    reslen, rtpoints = 0, ''
    geos = retobjs('livig') if export_op.nodeid.split('@')[0] == 'LiVi Geometry' else retobjs('livic')
    
    for o, geo in enumerate(geos):
        if len(geo.data.materials) > 0:
            if len([f for f in geo.data.polygons if geo.data.materials[f.material_index].livi_sense]) > 0:
                geo['licalc'], cverts, csfi, scene.objects.active, geo['cfaces'] = 1, [], [], geo, []
                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                mesh = geo.to_mesh(scene, True, 'PREVIEW', calc_tessface=False)
                mesh.transform(geo.matrix_world)
                scene.objects.active = geo
                csf = [face for face in mesh.polygons if mesh.materials[face.material_index].livi_sense]
                csfi = [f.index for f in csf]
                if node.cpoint == '0':  
                    reslen += len(csfi)
                    for f in csf:
                        fc = f.center
                        rtpoints += '{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(fc, f.normal.normalized()[:])
                elif node.cpoint == '1':        
                    csfvi = [item for sublist in [face.vertices[:] for face in mesh.polygons if mesh.materials[face.material_index].livi_sense] for item in sublist]
                    cverts = [v for (i,v) in enumerate(csfvi) if v not in csfvi[0:i]]
                    reslen += len(cverts)
                    for vert in cverts:
                        rtpoints += '{0[0]} {0[1]} {0[2]} {1[0]} {1[1]} {1[2]} \n'.format(mesh.vertices[vert].co[:], (mesh.vertices[vert].normal*geo.matrix_world.inverted()).normalized()[:])

                (geo['cverts'], geo['cfaces']) = (cverts, csfi) if node.cpoint == '1' else ([], csfi)                   
                bpy.data.meshes.remove(mesh)
            else:
                if geo.get('licalc'):
                    del geo['licalc']
                for mat in geo.material_slots:
                    mat.material.use_transparent_shadows = True
        else:
            node.export = 0
            export_op.report({'ERROR'},"Make sure your object "+geo.name+" has an associated material")
        node['reslen'] = reslen
    
    with open(scene['viparams']['filebase']+".rtrace", "w") as rtrace:
        rtrace.write(rtpoints)
    
    scene.fe = max(scene.cfe, scene.gfe)
    node.export = 1

def radcexport(export_op, node):
    skyfileslist, scene, scene.li_disp_panel, scene.vi_display = [], bpy.context.scene, 0, 0
    clearscene(scene, export_op)
    geonode = node.inputs['Geometry in'].links[0].from_node

    if 'LiVi CBDM' not in node.bl_label:
        if node['skynum'] < 4:
            locnode = 0 if node['skynum'] == 3 else node.inputs['Location in'].links[0].from_node            
            for frame in range(scene.fs, scene.cfe + 1):
                sunexport(scene, node, geonode, locnode, frame - scene.fs)
                if node['skynum'] < 2 and node.analysismenu != '2':
                    if frame == scene.frame_start:
                        if 'Sun' in [ob for ob in scene.objects if ob.get('VIType')]:
                            sun = [ob for ob in scene.objects if ob.get('VIType')][0]
                        else:
                            bpy.ops.object.lamp_add(type='SUN')
                            sun = bpy.context.object
                            sun['VIType'] = 'Sun'
                    blsunexport(scene, node, locnode, frame - scene.fs, sun)
                with open("{}-{}.sky".format(scene['viparams']['filebase'], frame), 'a') as skyfilea:
                    skyexport(node, skyfilea)
                with open("{}-{}.sky".format(scene['viparams']['filebase'], frame), 'r') as skyfiler:
                    skyfileslist.append(skyfiler.read())
                if node.hdr == True:
                    hdrexport(scene, frame, node, geonode)
            node['skyfiles'] = skyfileslist
            
        elif node['skynum'] == 4:
            if node.hdrname not in bpy.data.images:
                bpy.data.images.load(node.hdrname)
            node['skyfiles'] = [hdrsky(node.hdrname)]

        elif node['skynum'] == 5:
            subprocess.call("cp {} {}-0.sky".format(node.radname, scene['viparams']['filebase']), shell = True)
            with open(node.radname, 'r') as radfiler:
                node['skyfiles'] =  [radfiler.read()]

        elif node['skynum'] == 6:
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
                os.chdir(scene['viparams']['newdir'])
                pcombfiles = ""
                for i in range(0, 146):
                    pcombfiles = pcombfiles + "ps{}.hdr ".format(i)
                epwbase = os.path.splitext(os.path.basename(locnode.weather))
                if epwbase[1] in (".epw", ".EPW"):
                    with open(locnode.weather, "r") as epwfile:
                        epwlines = epwfile.readlines()
                        epwyear = epwlines[8].split(",")[0]
                        with open(os.path.join(scene['viparams']['newdir'], "{}.wea".format(epwbase[0]), "w")) as wea:
                            wea.write("place {0[1]}\nlatitude {0[6]}\nlongitude {0[7]}\ntime_zone {0[8]}\nsite_elevation {0[9]}weather_data_file_units 1\n".format(epwlines[0].split(",")))
                            for epwline in epwlines[8:]:
                                if int(epwline.split(",")[1]) in range(locnode.startmonth, locnode.endmonth + 1):
                                    wea.write("{0[1]} {0[2]} {0[3]} {0[14]} {0[15]} \n".format(epwline.split(",")))
                        subprocess.call("gendaymtx -m 1 {0} {1}.wea > {1}.mtx".format(('', '-O1')[node.analysismenu in ('1', '3')], scene['viparams']['newdir']+os.path.sep+epwbase[0]), shell=True)                       
                else:
                    export_op.report({'ERROR'}, "Not a valid EPW file")
                    return
    
                mtxfile = open(scene['viparams']['newdir']+os.path.sep+epwbase[0]+".mtx", "r")
            
            elif node['source'] == '1' and int(node.analysismenu) > 1:
                mtxfile = open(node.mtxname, "r")
    
            if node['source'] == '0':
                if node.inputs['Location in'].is_linked:
                    mtxlines = mtxfile.readlines()
                    vecvals, vals = mtx2vals(mtxlines, datetime.datetime(int(epwyear), 1, 1).weekday(), locnode)
                    mtxfile.close()
                    node['vecvals'] = vecvals
                    node['whitesky'] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"
                    oconvcmd = "oconv -w - > {0}-whitesky.oct".format(scene['viparams']['filebase'])
                    Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = node['whitesky'].encode('utf-8'))
                    if int(node.analysismenu) < 2 or node.hdr:
                        subprocess.call("vwrays -ff -x 600 -y 600 -vta -vp 0 0 0 -vd 0 1 0 -vu 0 0 1 -vh 360 -vv 360 -vo 0 -va 0 -vs 0 -vl 0 | rcontrib -bn 146 -fo -ab 0 -ad 1 -n {} -ffc -x 600 -y 600 -ld- -V+ -f tregenza.cal -b tbin -o p%d.hdr -m sky_glow {}-whitesky.oct".format(scene['viparams']['nproc'], scene['viparams']['filename']), shell = True)
                        for j in range(0, 146):
                            subprocess.call("pcomb -s {0} p{1}.hdr > ps{1}.hdr".format(vals[j], j), shell = True)
                            subprocess.call("{0}  p{1}.hdr".format(scene['viparams']['rm'], j), shell = True)        
                        subprocess.call("pcomb -h  "+pcombfiles+" > "+os.path.join(scene['viparams']['newdir'], epwbase[0]+".hdr"), shell = True)
                        subprocess.call(scene['viparams']['rm']+" ps*.hdr" , shell = True)
                        node.hdrname = os.path.join(scene['viparams']['newdir'], epwbase[0]+".hdr")
                    
                    if node.hdr:
                        Popen("oconv -w - > {}.oct".format(os.path.join(scene['viparams']['newdir'], epwbase[0])), shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = hdrsky(os.path.join(scene['viparams']['newdir'], epwbase[0]+".hdr").encode('utf-8')))
                        subprocess.call('cnt 750 1500 | rcalc -f "'+os.path.join(scene.vipath, 'lib', 'latlong.cal')+'" -e "XD=1500;YD=750;inXD=0.000666;inYD=0.001333" | rtrace -af pan.af -n {} -x 1500 -y 750 -fac "{}{}{}.oct" > '.format(scene['viparams']['nproc'], os.path.join(scene['viparams']['newdir'], epwbase[0])) + '"'+os.path.join(scene['viparams']['newdir'], epwbase[0]+'p.hdr')+'"', shell=True)
                else:
                    export_op.report({'ERROR'}, "No location node connected")
                    return
            if node.hdrname not in bpy.data.images:
                bpy.data.images.load(node.hdrname)
            
            if int(node.analysismenu) < 2:
                node['skyfiles'] = [hdrsky(node.hdrname)]
    
    scene.fe = max(scene.cfe, scene.gfe)
    for frame in range(scene.fs, scene.fe + 1):
        fexport(scene, frame, export_op, node, geonode)
    scene.frame_set(scene.fs)
    node.export = 1

def sunexport(scene, node, geonode, locnode, frame): 
    if locnode:
        simtime = node.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
        solalt, solazi, beta, phi = solarPosition(simtime.timetuple()[7], simtime.hour + (simtime.minute)*0.016666, scene['latitude'], scene['longitude'])
        subprocess.call("gensky -ang {} {} {} > {}".format(solalt, solazi, node['skytypeparams'], retsky(frame, node, scene)), shell = True)
    else:
        subprocess.call("gensky -ang {} {} {} > {}".format(45, 0, node['skytypeparams'], retsky(0, node, scene)), shell = True)

def hdrexport(scene, frame, node, geonode):
#    if locnode:
    subprocess.call("oconv {} > {}-{}sky.oct".format(retsky(frame, node, scene), scene['viparams']['filebase'], frame), shell=True)
    subprocess.call("rpict -vta -vp 0 0 0 -vd 0 1 0 -vu 0 0 1 -vh 360 -vv 360 -x 1500 -y 1500 {0}-{1}sky.oct > ".format(scene['viparams']['filebase'], frame) + os.path.join(scene['viparams']['newdir'], str(frame)+".hdr"), shell=True)
    subprocess.call('cnt 750 1500 | rcalc -f "'+os.path.join(scene.vipath, 'lib', 'latlong.cal"')+' -e "XD=1500;YD=750;inXD=0.000666;inYD=0.001333" | rtrace -af pan.af -n {0} -x 1500 -y 750 -fac "{1}-{2}sky.oct" > '.format(scene['viparams']['nproc'], scene['viparams']['filebase'], frame) + '"'+os.path.join(scene['viparams']['newdir'], str(frame)+'p.hdr')+'"', shell=True)
    if '{}p.hdr'.format(frame) not in bpy.data.images:
        bpy.data.images.load(os.path.join(scene['viparams']['newdir'], "{}p.hdr".format(frame)))
    else:
        bpy.data.images['{}p.hdr'.format(frame)].reload()

def blsunexport(scene, node, locnode, frame, sun):
    simtime = node.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
    solalt, solazi, beta, phi = solarPosition(simtime.timetuple()[7], simtime.hour + (simtime.minute)*0.016666, scene['latitude'], scene['longitude'])
    if node['skynum'] < 2:
        if frame == 0:
            sun.data.shadow_method = 'RAY_SHADOW'
            sun.data.shadow_ray_samples = 8
            sun.data.sky.use_sky = 1
            if node['skynum'] == 0:
                sun.data.shadow_soft_size = 0.1
                sun.data.energy = 5
            elif node['skynum'] == 1:
                sun.data.shadow_soft_size = 3
                sun.data.energy = 3
        sun.location = [x*20 for x in (-sin(phi), -cos(phi), tan(beta))]
        sun.rotation_euler = (math.pi/2) - beta, 0, -phi
        if scene.render.engine == 'CYCLES' and bpy.data.worlds['World'].get('node_tree'):
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
    rad_sky.write("4 .8 .8 1 0\n\n") if node['skynum'] < 3 else rad_sky.write("4 1 1 1 0\n\n")
    rad_sky.write("skyglow source sky\n0\n0\n4 0 0 1  180\n\n")

def hdrsky(skyfile):
    return("# Sky material\nvoid colorpict hdr_env\n7 red green blue {} angmap.cal sb_u sb_v\n0\n0\n\nhdr_env glow env_glow\n0\n0\n4 1 1 1 0\n\nenv_glow bubble sky\n0\n0\n4 0 0 0 5000\n\n".format(skyfile))

def fexport(scene, frame, export_op, node, othernode, **kwargs):
    pt = 0.2 if not kwargs.get('pause') else 0.5
    (geonode, connode) = (node, othernode) if 'LiVi Geometry' in node.bl_label else (othernode, node)
    
    if not connode or not connode.get('skyfiles'):
        radtext = geonode['radfiles'][0] if scene.gfe == 0 else geonode['radfiles'][frame]
    elif connode:
        skyframe = frame if scene.cfe > 0 else 0
        radtext = geonode['radfiles'][0] + connode['skyfiles'][skyframe] if len(geonode['radfiles']) == 1 else geonode['radfiles'][frame] + connode['skyfiles'][0]

    with open("{}-{}.rad".format(scene['viparams']['filebase'], frame), 'w') as radfile:
        radfile.write(radtext)
        
    if not bpy.data.texts.get('Radiance input-{}'.format(frame)):
        bpy.data.texts.new('Radiance input-{}'.format(frame))
    bpy.data.texts['Radiance input-{}'.format(frame)].clear()
    bpy.data.texts['Radiance input-{}'.format(frame)].write(radtext)
    
    oconvcmd = "oconv -w {0}-{1}.rad > {0}-{1}.oct".format(scene['viparams']['filebase'], frame)
    
#    This next line allows the radiance scene description to be piped into the oconv command.
#   oconvcmd = "oconv -w - > {0}-{1}.oct".format(geonode.filebase, frame).communicate(input = radtext.encode('utf-8'))
    ti.sleep(pt)
    oconvrun = Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT)#.communicate(input = radtext.encode('utf-8'))

    for line in oconvrun.stdout:
        if 'incompatible' in line.decode():
            export_op.report({'ERROR'}, line.decode() + " Try increasing the sleep period in ti.sleep in the livi_export.py file")
    ti.sleep(pt)
    export_op.report({'INFO'},"Export is finished")

def cyfc1(self):
    scene = bpy.context.scene
    if 'LiVi' in scene.resnode or 'Shadow' in scene.resnode:
        for material in bpy.data.materials:
            if material.use_nodes == 1:
                try:
                    if material.livi_sense or material.vi_shadow and material.node_tree.nodes.get('Attribute'):
                        material.node_tree.nodes["Attribute"].attribute_name = str(scene.frame_current)
                except Exception as e:
                    print(e, 'Something wrong with changing the material attribute name')

    if scene.resnode == 'VI Sun Path':
        spoblist = {ob.get('VIType'):ob for ob in scene.objects if ob.get('VIType') in ('Sun', 'SPathMesh')}
        beta, phi = solarPosition(scene.solday, scene.solhour, scene['latitude'], scene['longitude'])[2:]
        if bpy.data.worlds.get('World'):
            if bpy.data.worlds["World"].use_nodes == False:
                bpy.data.worlds["World"].use_nodes = True
            nt = bpy.data.worlds[0].node_tree
            if nt and nt.nodes.get('Sky Texture'):
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)
        for ob in scene.objects:
            if ob.get('VIType') == 'Sun':
                ob.rotation_euler = pi * 0.5 - beta, 0, -phi
                if ob.data.node_tree:
                    for blnode in [blnode for blnode in ob.data.node_tree.nodes if blnode.bl_label == 'Blackbody']:
                        blnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5
                    for emnode in [emnode for emnode in ob.data.node_tree.nodes if emnode.bl_label == 'Emission']:
                        emnode.inputs[1].default_value = 5 * sin(beta)
            
            elif ob.get('VIType') == 'SPathMesh':
                ob.scale = 3 * [scene.soldistance/100]
            
            elif ob.get('VIType') == 'SkyMesh':
                ont = ob.data.materials['SkyMesh'].node_tree
                if ont and ont.nodes.get('Sky Texture'):
                    ont.nodes['Sky Texture'].sun_direction = sin(phi), -cos(phi), sin(beta)
            
            elif ob.get('VIType') == 'SunMesh':
                ob.scale = 3*[scene.soldistance/100]
                ob.location.z = spoblist['Sun'].location.z = spoblist['SPathMesh'].location.z + scene.soldistance * sin(beta)
                ob.location.x = spoblist['Sun'].location.x = spoblist['SPathMesh'].location.x -(scene.soldistance**2 - (spoblist['Sun'].location.z-spoblist['SPathMesh'].location.z)**2)**0.5  * sin(phi)
                ob.location.y = spoblist['Sun'].location.y = spoblist['SPathMesh'].location.y -(scene.soldistance**2 - (spoblist['Sun'].location.z-spoblist['SPathMesh'].location.z)**2)**0.5 * cos(phi)
                if ob.data.materials[0].node_tree:
                    for smblnode in [smblnode for smblnode in ob.data.materials[0].node_tree.nodes if ob.data.materials and smblnode.bl_label == 'Blackbody']:
                        smblnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5
                
#        bpy.data.worlds[0].use_nodes = 0
#        ti.sleep(0.1)
#        bpy.data.worlds[0].use_nodes = 1
    else:
        return