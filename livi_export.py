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
from math import sin, cos, tan, pi
from subprocess import PIPE, Popen, STDOUT
from .vi_func import retsky, retobj, retmesh, clearscene, solarPosition, mtx2vals, retobjs, selobj, face_centre, selmesh, vertarea, facearea, li_calcob

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
            mradfile, matnames = "# Materials \n\n", []
            for o in retobjs('livig'): 
                for mat in [m for m in o.data.materials if m.name not in matnames]:
                    mradfile += mat.radmat(scene)
                    matnames.append(mat.name)
                    mat.use_vertex_color_paint = 1 if mat.livi_sense else 0
                    if mat['radentry'].split(' ')[1] in ('light', 'mirror', 'antimatter'):
                        export_op.report({'INFO'}, o.name+" has an antimatter, emission or mirror material. Basic export routine used with no modifiers.")
                        o['merr'] = 1                            
            bpy.ops.object.select_all(action='DESELECT')
            
            tempmatfilename = scene['viparams']['filebase']+".tempmat"
            with open(tempmatfilename, "w") as tempmatfile:
                tempmatfile.write(mradfile)
                
        # Geometry export routine
        
        if frame in range(max(node['frames']['Geometry'], node['frames']['Material']) + 1):
            gframe = scene.frame_current if node['frames']['Geometry'] > 0 else 0
            mframe = scene.frame_current if node['frames']['Material'] > 0 else 0
            gradfile = "# Geometry \n\n"
            for o in retobjs('livig'):
                if not o.get('merr'):
                    if not kwargs.get('mo') or (kwargs.get('mo') and o in kwargs['mo']):
                        selobj(scene, o)
                        selmesh('selenm')
                        
                        if [edge for edge in o.data.edges if edge.select]:
                            export_op.report({'INFO'}, o.name+" has a non-manifold mesh. Basic export routine used with no modifiers.")
                            o['merr'] = 1
                            
                        if not o.get('merr'):
                            if node.animmenu in ('Geometry', 'Material'):# or export_op.nodeid.split('@')[0] == 'LiVi Simulation':
                                bpy.ops.export_scene.obj(filepath=retobj(o.name, gframe, node, scene), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=True, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                                objcmd = "obj2mesh -w -a {} {} {}".format(tempmatfilename, retobj(o.name, gframe, node, scene), retmesh(o.name, max(gframe, mframe), node, scene)) 
                            elif export_op.nodeid.split('@')[0] == 'LiVi Simulation':
                                bpy.ops.export_scene.obj(filepath=retobj(o.name, scene.frame_start, node, scene), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=True, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                                objcmd = "obj2mesh -w -a {} {} {}".format(tempmatfilename, retobj(o.name, scene.frame_start, node), retmesh(o.name, scene.frame_start, node, scene))
                            else:
                                if frame == scene.fs:                        
                                    bpy.ops.export_scene.obj(filepath=retobj(o.name, scene.frame_current, node, scene), check_existing=True, filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=False, use_normals=o.data.polygons[0].use_smooth, use_uvs=True, use_materials=True, use_triangles=True, use_nurbs=True, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=True, global_scale=1.0, axis_forward='Y', axis_up='Z', path_mode='AUTO')
                                    objcmd = "obj2mesh -w -a {} {} {}".format(tempmatfilename, retobj(o.name, scene.frame_current, node, scene), retmesh(o.name, scene.frame_current, node, scene))
                                else:
                                    objcmd = ''
                            objrun = Popen(objcmd, shell = True, stdout = PIPE, stderr=STDOUT)                        
                            for line in objrun.stdout:
                                if 'non-triangle' in line.decode():
                                    export_op.report({'INFO'}, o.name+" has an incompatible mesh. Doing a simplified export")
                                    o['merr'] = 1
                                    break
    
                            o.select = False
        
#                    if not o.get('merr'):
                        gradfile += "void mesh id \n1 "+retmesh(o.name, max(gframe, mframe), node, scene)+"\n0\n0\n\n"
                else:
                    export_op.report({'INFO'}, o.name+" could not be converted into a Radiance mesh and simpler export routine has been used. No un-applied object modifiers will be exported.")
                    if o.get('merr'):
                        del o['merr']
                    geomatrix = o.matrix_world
                    try:
                        for face in [face for face in o.data.polygons if o.data.materials and face.material_index < len(o.data.materials) and o.data.materials[face.material_index]['radentry'].split(' ')[1] != 'antimatter']:
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
                    except Exception as e:
                        print(e)
                        export_op.report({'ERROR'},"Make sure your object "+o.name+" has an associated material for all faces")

        # Lights export routine
        if frame in range(node['frames']['Lights'] + 1):
            lradfile = "# Lights \n\n"    
            for geo in [g for g in retobjs('livil')]:
                iesname = os.path.splitext(os.path.basename(geo.ies_name))[0]
                subprocess.call("ies2rad -t default -m {0} -c {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} -l / -p {2} -d{3} -o {4}-{5} {6}".format(geo.ies_strength, geo.ies_colour, scene['viparams']['newdir'], geo.ies_unit, iesname, frame, geo.ies_name), shell=True)
                if geo.type == 'LAMP':
                    if geo.parent:
                        geo = geo.parent
                    lradfile += "!xform -rx {0} -ry {1} -rz {2} -t {3[0]} {3[1]} {3[2]} {4}.rad\n\n".format((180/pi)*geo.rotation_euler[0] - 180, (180/pi)*geo.rotation_euler[1], (180/pi)*geo.rotation_euler[2], geo.location, os.path.join(scene['viparams']['newdir'], iesname+"-{}".format(frame)))
                elif geo.type == 'MESH' and geo.lila:
                    rotation = geo.rotation_euler
                    for face in geo.data.polygons:
                        (fx, fy, fz) = face_centre(geo, 0, face)
                        lradfile += "!xform -rx {:.3f} -ry {:.3f} -rz {:.3f} -t {:.3f} {:.3f} {:.3f} {}{}".format((180/pi)*rotation[0], (180/pi)*rotation[1], (180/pi)*rotation[2], fx, fy, fz, os.path.join(scene['viparams']['newdir'], iesname+"-{}.rad".format(frame)), ('\n', '\n\n')[face == geo.data.polygons[-1]])
        sradfile = "# Sky \n\n"
        radfiles.append(mradfile+gradfile+lradfile+sradfile)
    
    node['radfiles'] = radfiles

# rtrace export routine
    
    reslen, rtpoints = 0, ''
    geos = retobjs('livig') if export_op.nodeid.split('@')[0] == 'LiVi Geometry' else retobjs('livic')    
    for o, geo in enumerate(geos):
        if geo.data.materials:
            if li_calcob(geo, 'livi'):
                cverts, csfi, scene.objects.active, geo['cfaces'] = [], [], geo, []                 
                selmesh('desel')
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

                (geo['cverts'], geo['cfaces'], geo['lisenseareas']) = (cverts, csfi, [vertarea(geo, mesh.vertices[vert]) for vert in cverts]) if node.cpoint == '1' else ([], csfi, [facearea(geo, f) for f in csf])      
                
                bpy.data.meshes.remove(mesh)
            else:
                for mat in geo.material_slots:
                    mat.material.use_transparent_shadows = True
        else:
            node.export = 0
            export_op.report({'ERROR'},"Make sure your object "+geo.name+" has an associated material")
        node['reslen'] = reslen
    
    with open(scene['viparams']['filebase']+".rtrace", "w") as rtrace:
        rtrace.write(rtpoints)
    
    scene.fe = max(scene.cfe, scene.gfe)
    simnode = node.outputs['Geometry out'].links[0].to_node if node.outputs['Geometry out'].links else 0
    connode = simnode.connodes() if simnode else 0

    for frame in range(scene.fs, scene.fe + 1):
        createradfile(scene, frame, export_op, connode, node)

    node.export = 1

def radcexport(export_op, node, locnode, geonode):
    skyfileslist, scene, scene.li_disp_panel, scene.vi_display = [], bpy.context.scene, 0, 0
    clearscene(scene, export_op)
#    simnode = node.outputs['Context out'].links[0].to_node
#    geonode = simnode.inputs['Geometry in'].links[0].from_node
#    locnode = simnode.inputs['Location in'].links[0].from_node

    if 'LiVi CBDM' not in node.bl_label:
        if node['skynum'] < 4:
#            locnode = 0 if node['skynum'] == 3 else simnode.inputs['Location in'].links[0].from_node            
            for frame in range(scene.fs, scene.cfe + 1):
                sunexport(scene, node, geonode, locnode, frame - scene.fs)
                if node['skynum'] < 2 and node.analysismenu != '2':
                    if frame == scene.frame_start:
                        if 'Sun' in [ob for ob in scene.objects if ob.get('VIType')]:
                            sun = [ob for ob in scene.objects if ob.get('VIType') == 'Sun'][0]
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
            if node['source'] == '0':
#                locnode = simnode.inputs['Location in'].links[0].from_node
#                if locnode.endmonth < locnode.startmonth:
#                    export_op.report({'ERROR'}, "End month is earlier than start month")
#                    return
                os.chdir(scene['viparams']['newdir'])
#                pcombfiles = ""
                pcombfiles = ''.join(["ps{}.hdr ".format(i) for i in range(146)])
#                for i in range(0, 146):
#                    pcombfiles = pcombfiles + "ps{}.hdr ".format(i)
                epwbase = os.path.splitext(os.path.basename(locnode.weather))
                if epwbase[1] in (".epw", ".EPW"):
                    with open(locnode.weather, "r") as epwfile:
                        epwlines = epwfile.readlines()
                        epwyear = epwlines[8].split(",")[0]
                        with open(os.path.join(scene['viparams']['newdir'], "{}.wea".format(epwbase[0])), "w") as wea:
                            wea.write("place {0[1]}\nlatitude {0[6]}\nlongitude {0[7]}\ntime_zone {0[8]}\nsite_elevation {0[9]}weather_data_file_units 1\n".format(epwlines[0].split(",")))
                            for epwline in epwlines[8:]:
                                if int(epwline.split(",")[1]) in range(node.startmonth, node.endmonth + 1):
                                    wea.write("{0[1]} {0[2]} {0[3]} {0[14]} {0[15]} \n".format(epwline.split(",")))
                        subprocess.call("gendaymtx -m 1 {0} {1}.wea > {1}.mtx".format(('', '-O1')[node.analysismenu in ('1', '3')], os.path.join(scene['viparams']['newdir'], epwbase[0])), shell=True)                       
                else:
                    export_op.report({'ERROR'}, "Not a valid EPW file")
                    return
    
                mtxfile = open(scene['viparams']['newdir']+os.path.sep+epwbase[0]+".mtx", "r")
            
            elif node['source'] == '1' and int(node.analysismenu) > 1:
                mtxfile = open(node.mtxname, "r")
    
            if node['source'] == '0':
                if node.inputs['Location in'].is_linked:
                    mtxlines = mtxfile.readlines()
                    vecvals, vals = mtx2vals(mtxlines, datetime.datetime(int(epwyear), 1, 1).weekday(), node)
                    mtxfile.close()
                    node['vecvals'] = vecvals
                    node['whitesky'] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"
                    oconvcmd = "oconv -w - > {0}-whitesky.oct".format(scene['viparams']['filebase'])
                    Popen(oconvcmd, shell = True, stdin = PIPE).communicate(input = node['whitesky'].encode('utf-8'))
                    if int(node.analysismenu) < 2 or node.hdr:
                        subprocess.call("vwrays -ff -x 600 -y 600 -vta -vp 0 0 0 -vd 0 1 0 -vu 0 0 1 -vh 360 -vv 360 -vo 0 -va 0 -vs 0 -vl 0 | rcontrib -bn 146 -fo -ab 0 -ad 1 -n {} -ffc -x 600 -y 600 -ld- -V+ -f tregenza.cal -b tbin -o p%d.hdr -m sky_glow {}-whitesky.oct".format(scene['viparams']['nproc'], scene['viparams']['filename']), shell = True)
#                        for j in range(0, 146):
                        [subprocess.call("pcomb -s {0} p{1}.hdr > ps{1}.hdr".format(vals[j], j), shell = True) for j in range(146)]
#                            [os.remove()]
#                            subprocess.call("{0}  p{1}.hdr".format(scene['viparams']['rm'], j), shell = True)        
                        subprocess.call("pcomb -h  "+pcombfiles+"> "+os.path.join(scene['viparams']['newdir'], epwbase[0]+".hdr"), shell = True)
                        [os.remove(os.path.join(scene['viparams']['newdir'], 'p{}.hdr'.format(i))) for i in range (146)]
                        [os.remove(os.path.join(scene['viparams']['newdir'], 'ps{}.hdr'.format(i))) for i in range (146)]
#                        subprocess.call(scene['viparams']['rm']+" ps*.hdr" , shell = True)
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
    scene.frame_set(scene.fs)

    simnode = node.outputs['Context out'].links[0].to_node if node.outputs['Context out'].links else 0
    geonode = simnode.geonodes() if simnode else 0
    
    for frame in range(scene.fs, scene.fe + 1):
        createradfile(scene, frame, export_op, node, geonode)
#    node.export = 1

def sunexport(scene, node, geonode, locnode, frame): 
    if locnode:
        simtime = node.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
        solalt, solazi, beta, phi = solarPosition(simtime.timetuple()[7], simtime.hour + (simtime.minute)*0.016666, scene['latitude'], scene['longitude'])
        subprocess.call("gensky -ang {} {} {} > {}".format(solalt, solazi, node['skytypeparams'], retsky(frame, node, scene)), shell = True)
    else:
        subprocess.call("gensky -ang {} {} {} > {}".format(45, 0, node['skytypeparams'], retsky(0, node, scene)), shell = True)

def hdrexport(scene, frame, node, geonode):
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
            sun.data.shadow_method, sun.data.shadow_ray_samples, sun.data.sky.use_sky = 'RAY_SHADOW', 8, 1
            shaddict = {'0': (0.01, 5), '1': (3, 3)}
            (sun.data.shadow_soft_size, sun.data.energy) = shaddict[str(node['skynum'])] 
        sun.location, sun.rotation_euler = [x*20 for x in (-sin(phi), -cos(phi), tan(beta))], [(math.pi/2) - beta, 0, -phi]
        if scene.render.engine == 'CYCLES' and bpy.data.worlds['World'].get('node_tree'):
            if 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)#sin(phi), -cos(phi), -2* beta/math.pi
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].keyframe_insert(data_path = 'sun_direction', frame = frame)
        sun.keyframe_insert(data_path = 'location', frame = frame)
        sun.keyframe_insert(data_path = 'rotation_euler', frame = frame)
        sun.data.cycles.use_multiple_importance_sampling = True
    bpy.ops.object.select_all()

def skyexport(node, rad_sky):
    rad_sky.write("\nskyfunc glow skyglow\n0\n0\n")
    rad_sky.write("4 .8 .8 1 0\n\n") if node['skynum'] < 3 else rad_sky.write("4 1 1 1 0\n\n")
    rad_sky.write("skyglow source sky\n0\n0\n4 0 0 1  180\n\n")

def hdrsky(skyfile):
    return("# Sky material\nvoid colorpict hdr_env\n7 red green blue {} angmap.cal sb_u sb_v\n0\n0\n\nhdr_env glow env_glow\n0\n0\n4 1 1 1 0\n\nenv_glow bubble sky\n0\n0\n4 0 0 0 5000\n\n".format(skyfile))

def createradfile(scene, frame, export_op, connode, geonode, **kwargs):    
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

def createoconv(scene, frame, export_op, connode, geonode, **kwargs):
    oconvcmd = "oconv {0}-{1}.rad > {0}-{1}.oct".format(scene['viparams']['filebase'], frame)
    oconvrun = Popen(oconvcmd, shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate()
    export_op.report({'INFO'},"Export is finished")

def cyfc1(self):
    scene = bpy.context.scene
    if 'LiVi' in scene.resnode or 'Shadow' in scene.resnode:
        for material in [m for m in bpy.data.materials if m.use_nodes and (m.livi_sense or m.vi_shadow)]:
            try:
                print([node.bl_label == 'Attribute' for node in material.node_tree.nodes])
                if any([node.bl_label == 'Attribute' for node in material.node_tree.nodes]):
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
        for ob in [o for o in scene.objects if o.get('VIType') == 'Sun']:
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
    else:
        return