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

import bpy, os, math, subprocess, datetime, bmesh
from math import sin, cos, tan, pi
from subprocess import PIPE, Popen, STDOUT
from .vi_func import retsky, retobj, retmesh, clearscene, solarPosition, mtx2vals, retobjs, selobj, selmesh, vertarea, radpoints, clearanim

def radgexport(export_op, node, **kwargs):
    scene = bpy.context.scene  
    export = 'geoexport' if export_op.nodeid.split('@')[0] == 'LiVi Geometry' else 'genexport'
    if bpy.context.active_object and not bpy.context.active_object.layers[scene.active_layer]:
        export_op.report({'INFO'}, "Active geometry is not on the active layer. You may need to lock layers.")
    radfiles = []
    geogennode = node.inputs['Generative in'].links[0].from_node if node.inputs['Generative in'].links else 0
    geooblist, caloblist, lightlist = retobjs('livig'), retobjs('livic'), retobjs('livil')    
    if not kwargs:
        mableobs = set(geooblist + caloblist)
        scene['livig'], scene['livic'], scene['livil'] = [o.name for o in geooblist], [o.name for o in caloblist], [o.name for o in lightlist]
        if geogennode:            
            for o in mableobs: 
                seldict = {'ALL': True, 'Selected': (False, True)[o.select], 'Not Selected': (True, False)[o.select]}
                o.manip = seldict[geogennode.oselmenu]
            for o in mableobs:
                if geogennode.geomenu == 'Mesh':
                    selobj(scene, o)
                    if o.vertex_groups.get('genfaces'):
                        selmesh('rd')
                    else:                        
                        o.vertex_groups.new('genfaces')
                        o.vertex_groups.active = o.vertex_groups['genfaces']
                        mseldict = {'Not Selected': 'INVERT', 'All': 'SELECT', 'Selected': 'PASS'}
                        selmesh(mseldict[geogennode.mselmenu])
                    o['vgi'] = o.vertex_groups['genfaces'].index
            scene['livim'] = [o.name for o in mableobs if o.manip]
            clearanim(scene, [bpy.data.objects[on] for on in scene['livim']])
    
    if export == 'geoexport':
        clearscene(scene, export_op)
        scene.fs = scene.frame_start if node.animmenu != 'Static' else 0
    else:
        (scene.fs, scene.gfe, node['frames']['Material'], node['frames']['Geometry'], node['frames']['Lights']) = [kwargs['genframe']] * 5 if kwargs.get('genframe') else (0, 0, 0, 0, 0)
        scene.cfe = 0
        
    for frame in range(scene.fs, scene.gfe + 1): 
        rti, rtpoints = 1, ''
        if export == 'geoexport':
            scene.frame_set(frame)
        
        if frame in range(node['frames']['Material'] + 1):
            mradfile, matnames = "# Materials \n\n", []
            for o in [bpy.data.objects[on] for on in scene['livig']]: 
                mradfile +=  ''.join([m.radmat(scene) for m in o.data.materials if m.name not in matnames])
                matnames = set([mat.name for mat in o.data.materials])
                for mat in [m for m in o.data.materials if m.name not in matnames]:
                    matnames.append(mat.name)
                    if mat['radentry'].split(' ')[1] in ('light', 'mirror', 'antimatter'):
                        export_op.report({'INFO'}, o.name+" has an antimatter, emission or mirror material. Basic export routine used with no modifiers.")
                        o['merr'] = 1 
            bpy.ops.object.select_all(action='DESELECT')
            
            tempmatfilename = scene['viparams']['filebase']+".tempmat"
            with open(tempmatfilename, "w") as tempmatfile:
                tempmatfile.write(mradfile)
                
        # Geometry export routine
        
        if frame in range(scene.fs, max(node['frames']['Geometry'], node['frames']['Material']) + 1):
            gframe = scene.frame_current if node['frames']['Geometry'] > 0 else 0
            mframe = scene.frame_current if node['frames']['Material'] > 0 else 0
            gradfile = "# Geometry \n\n"
            lradfile = "# Lights \n\n" 
            
            for o in set(geooblist + caloblist):                
                bm = bmesh.new()
                bm.from_mesh(o.data)
                bm.transform(o.matrix_world)
                if o.name in scene['livig']:
                    if not kwargs.get('mo') or (kwargs.get('mo') and o in kwargs['mo']):
                        if not o.get('merr'):                    
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
                                    objcmd = "obj2mesh -w -a {} {} {}".format(tempmatfilename, retobj(o.name, scene.frame_start, node, scene), retmesh(o.name, scene.frame_start, node, scene))
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
                                gradfile += "void mesh id \n1 "+retmesh(o.name, max(gframe, mframe), node, scene)+"\n0\n0\n\n"
        
                        if o.get('merr'):
                            export_op.report({'INFO'}, o.name+" has an antimatter material or could not be converted into a Radiance mesh and simpler export routine has been used. No un-applied object modifiers will be exported.")
                            genframe = gframe + 1 if not kwargs else kwargs['genframe']  
                            if o.data.shape_keys and o.data.shape_keys.key_blocks[0] and o.data.shape_keys.key_blocks[genframe]:
                                skv0, skv1 = o.data.shape_keys.key_blocks[0].value, o.data.shape_keys.key_blocks[genframe].value
                                sk0, sk1 = bm.verts.layers.shape.keys()[0], bm.verts.layers.shape.keys()[genframe]
                                skl0, skl1 = bm.verts.layers.shape[sk0], bm.verts.layers.shape[sk1]
                                gradfile += radpoints(o, [face for face in bm.faces if o.data.materials and face.material_index < len(o.data.materials) and o.data.materials[face.material_index]['radentry'].split(' ')[1] != 'antimatter'], (skv0, skv1, skl0, skl1))            
                            else:
                                gradfile += radpoints(o, [face for face in bm.faces if o.data.materials and face.material_index < len(o.data.materials) and o.data.materials[face.material_index]['radentry'].split(' ')[1] != 'antimatter'], 0)

                        if o.get('merr'):
                            del o['merr']
                            
                # rtrace export routine
        
                if o.name in scene['livic']:
                    cverts, csfi, scene.objects.active, o['cfaces'] = [], [], o, []               
                    selmesh('desel')
                    scene.objects.active = o
            
                    if node.cpoint == '0':               
                        if bm.verts.layers.int.get('cindex'):
                            bm.verts.layers.int.remove(bm.verts.layers.int['cindex'])
                        if bm.faces.layers.int.get('cindex'):
                            bm.faces.layers.int.remove(bm.faces.layers.int['cindex'])
                        bm.faces.layers.int.new('cindex')
                        cindex = bm.faces.layers.int['cindex'] 
                        csf = [face for face in bm.faces if o.data.materials[face.material_index].mattype == '1']
                        csfc = [face.calc_center_median() for face in bm.faces if o.data.materials[face.material_index].mattype == '1']
                        csfi = [face.index for face in bm.faces if o.data.materials[face.material_index].mattype == '1']
                        
                        for fi, f in enumerate(csf):
                            rtpoints += '{0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} \n'.format([csfc[fi][i] + node.offset * f.normal.normalized()[i] for i in range(3)], f.normal.normalized()[:])
                            f[cindex] = rti
                            rti+= 1
                            
                    elif node.cpoint == '1': 
                        if bm.faces.layers.int.get('cindex'):
                            bm.faces.layers.int.remove(bm.faces.layers.int['cindex'])
                        if bm.verts.layers.int.get('cindex'):
                            bm.verts.layers.int.remove(bm.verts.layers.int['cindex'])
                        bm.verts.layers.int.new('cindex')
                        cindex = bm.verts.layers.int['cindex']
                        cverts = set([item for sublist in [face.verts[:] for face in bm.faces if o.data.materials[face.material_index].mattype == '1'] for item in sublist])
                        for vert in cverts:
                            rtpoints += '{0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} \n'.format([vert.co[i] + node.offset * vert.normal.normalized()[i] for i in range(3)], (vert.normal.normalized()[:]))
                            vert[cindex] = rti
                            rti += 1
                    (o['cverts'], o['cfaces'], o['lisenseareas']) = ([cv.index for cv in cverts], csfi, [vertarea(bm, vert) for vert in cverts]) if scene['liparams']['cp'] == '1' else ([], csfi, [f.calc_area() for f in csf])      
                bm.transform(o.matrix_world.inverted())
                bm.to_mesh(o.data)
                bm.free()
                            
    # Lights export routine

            for o in lightlist:
                if frame in range(node['frames']['Lights'] + 1):
                    iesname = os.path.splitext(os.path.basename(o.ies_name))[0]
                    if os.path.isfile(o.ies_name):
                        subprocess.call("ies2rad -t default -m {0} -c {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} -p {2} -d{3} -o {4}-{5} {6}".format(o.ies_strength, o.ies_colour, scene['viparams']['newdir'], o.ies_unit, iesname, frame, o.ies_name), shell=True)
                        if o.type == 'LAMP':
                            if o.parent:
                                o = o.parent
                            lradfile += "!xform -rx {0[0]} -ry {0[1]} -rz {0[2]} -t {1[0]} {1[1]} {1[2]} {2}.rad\n\n".format([(180/pi)*o.rotation_euler[i] for i in range(3)], o.location, os.path.join(scene['viparams']['newdir'], iesname+"-{}".format(frame)))
                        elif o.type == 'MESH':
                            for face in o.data.polygons:
                                lradfile += "!xform -rx {0[0]:.3f} -ry {0[1]:.3f} -rz {0[2]:.3f} -t {1[0]:.3f} {1[1]:.3f} {1[2]:.3f} {2}{3}".format([(180/pi)*o.rotation_euler[i] for i in range(3)], o.matrix_world * face.center, os.path.join(scene['viparams']['newdir'], iesname+"-{}.rad".format(frame)), ('\n', '\n\n')[face == o.data.polygons[-1]])
                    elif iesname:
                        export_op.report({'ERROR'}, 'The IES file associated with {} cannot be found'.format(o.name))
            
            sradfile = "# Sky \n\n"
        radfiles.append(mradfile+gradfile+lradfile+sradfile)
    node['reslen'] = rti - 1
    node['radfiles'] = radfiles
    
    with open(scene['viparams']['filebase']+".rtrace", "w") as rtrace:
        rtrace.write(rtpoints)
    
    scene.fe = max(scene.cfe, scene.gfe)
    simnode = node.outputs['Geometry out'].links[0].to_node if node.outputs['Geometry out'].links else 0
    connode = simnode.connodes() if simnode else 0

    for frame in range(scene.fs, scene.fe + 1):
        createradfile(scene, frame, export_op, connode, node)
        if kwargs:
            createoconv(scene, frame, export_op)
            
def radcexport(export_op, node, locnode, geonode):
    skyfileslist, scene, scene.li_disp_panel, scene.vi_display = [], bpy.context.scene, 0, 0
    clearscene(scene, export_op)

    if 'LiVi CBDM' not in node.bl_label:
        if node['skynum'] < 4:
            for frame in range(scene.fs, scene.cfe + 1):
                sunexport(scene, node, locnode, frame - scene.fs)
                if node['skynum'] < 2 and node.analysismenu != '2':
                    if frame == scene.frame_start:
                        if 'SUN' in [ob.data.type for ob in scene.objects if ob.type == 'LAMP' and ob.get('VIType')]:
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
                    hdrexport(scene, frame, node)
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
                os.chdir(scene['viparams']['newdir'])
                pcombfiles = ''.join(["ps{}.hdr ".format(i) for i in range(146)])
                epwbase = os.path.splitext(os.path.basename(locnode.weather))
                if epwbase[1] in (".epw", ".EPW"):
                    with open(locnode.weather, "r") as epwfile:
                        epwlines = epwfile.readlines()
                        epwyear = epwlines[8].split(",")[0]
                        subprocess.call("epw2wea {} {}".format(locnode.weather, os.path.join(scene['viparams']['newdir'], "{}.wea".format(epwbase[0]))), shell=True)
                        subprocess.call("gendaymtx -m 1 {0} {1}.wea > {1}.mtx".format(('', '-O1')[node.analysismenu in ('1', '3')], os.path.join(scene['viparams']['newdir'], epwbase[0])), shell=True)                       
                else:
                    export_op.report({'ERROR'}, "Not a valid EPW file")
                    return
    
                mtxfile = open(os.path.join(scene['viparams']['newdir'], epwbase[0]+".mtx"), "r")
            
            elif node['source'] == '1' and int(node.analysismenu) > 1:
                mtxfile = open(node.mtxname, "r")
    
            if node['source'] == '0':
                if node.inputs['Location in'].is_linked:
                    mtxlines = mtxfile.readlines()
                    vecvals, vals = mtx2vals(mtxlines, datetime.datetime(int(epwyear), node.startmonth, 1).weekday(), node)
                    mtxfile.close()
                    node['vecvals'] = vecvals
                    node['whitesky'] = "void glow sky_glow \n0 \n0 \n4 1 1 1 0 \nsky_glow source sky \n0 \n0 \n4 0 0 1 180 \nvoid glow ground_glow \n0 \n0 \n4 1 1 1 0 \nground_glow source ground \n0 \n0 \n4 0 0 -1 180\n\n"
                    oconvcmd = "oconv -w - > {0}-whitesky.oct".format(scene['viparams']['filebase'])
                    Popen(oconvcmd, shell = True, stdin = PIPE).communicate(input = node['whitesky'].encode('utf-8'))
                    if int(node.analysismenu) < 2 or node.hdr:
                        subprocess.call("vwrays -ff -x 600 -y 600 -vta -vp 0 0 0 -vd 0 1 0 -vu 0 0 1 -vh 360 -vv 360 -vo 0 -va 0 -vs 0 -vl 0 | rcontrib -bn 146 -fo -ab 0 -ad 1 -n {} -ffc -x 600 -y 600 -ld- -V+ -f tregenza.cal -b tbin -o p%d.hdr -m sky_glow {}-whitesky.oct".format(scene['viparams']['nproc'], scene['viparams']['filename']), shell = True)
                        [subprocess.call("pcomb -s {0} p{1}.hdr > ps{1}.hdr".format(vals[j], j), shell = True) for j in range(146)]
                        subprocess.call("pcomb -h  "+pcombfiles+"> "+os.path.join(scene['viparams']['newdir'], epwbase[0]+".hdr"), shell = True)
                        [os.remove(os.path.join(scene['viparams']['newdir'], 'p{}.hdr'.format(i))) for i in range (146)]
                        [os.remove(os.path.join(scene['viparams']['newdir'], 'ps{}.hdr'.format(i))) for i in range (146)]
                        node.hdrname = os.path.join(scene['viparams']['newdir'], epwbase[0]+".hdr")                    
                    if node.hdr:
                        Popen("oconv -w - > {}.oct".format(os.path.join(scene['viparams']['newdir'], epwbase[0])), shell = True, stdin = PIPE, stdout=PIPE, stderr=STDOUT).communicate(input = hdrsky(os.path.join(scene['viparams']['newdir'], epwbase[0]+".hdr").encode('utf-8')))
                        subprocess.call('cnt 750 1500 | rcalc -f "'+os.path.join(scene.vipath, 'Radfiles', 'lib', 'latlong.cal')+'" -e "XD=1500;YD=750;inXD=0.000666;inYD=0.001333" | rtrace -af pan.af -n {} -x 1500 -y 750 -fac "{}{}{}.oct" > '.format(scene['viparams']['nproc'], os.path.join(scene['viparams']['newdir'], epwbase[0])) + '"'+os.path.join(scene['viparams']['newdir'], epwbase[0]+'p.hdr')+'"', shell=True)
                else:
                    export_op.report({'ERROR'}, "No location node connected")
                    return
            if node.hdrname and os.path.isfile(node.hdrname) and node.hdrname not in bpy.data.images:
                bpy.data.images.load(node.hdrname)
            
            if int(node.analysismenu) < 2:
                node['skyfiles'] = [hdrsky(node.hdrname)]
    
    scene.fe = max(scene.cfe, scene.gfe)
    scene.frame_set(scene.fs)
    
    for frame in range(scene.fs, scene.fe + 1):
        createradfile(scene, frame, export_op, node, geonode)

def sunexport(scene, node, locnode, frame): 
    if locnode:
        simtime = node.starttime + frame*datetime.timedelta(seconds = 3600*node.interval)
        solalt, solazi, beta, phi = solarPosition(simtime.timetuple()[7], simtime.hour + (simtime.minute)*0.016666, scene['latitude'], scene['longitude'])
        subprocess.call("gensky -ang {} {} {} > {}".format(solalt, solazi, node['skytypeparams'], retsky(frame, node, scene)), shell = True)
    else:
        subprocess.call("gensky -ang {} {} {} > {}".format(45, 0, node['skytypeparams'], retsky(0, node, scene)), shell = True)

def hdrexport(scene, frame, node):
    subprocess.call("oconv {} > {}-{}sky.oct".format(retsky(frame, node, scene), scene['viparams']['filebase'], frame), shell=True)
    subprocess.call("rpict -vta -vp 0 0 0 -vd 0 1 0 -vu 0 0 1 -vh 360 -vv 360 -x 1500 -y 1500 {0}-{1}sky.oct > ".format(scene['viparams']['filebase'], frame) + os.path.join(scene['viparams']['newdir'], str(frame)+".hdr"), shell=True)
    subprocess.call('cnt 750 1500 | rcalc -f "'+os.path.join(scene.vipath, 'Radfiles', 'lib', 'latlong.cal"')+' -e "XD=1500;YD=750;inXD=0.000666;inYD=0.001333" | rtrace -af pan.af -n {0} -x 1500 -y 750 -fac "{1}-{2}sky.oct" > '.format(scene['viparams']['nproc'], scene['viparams']['filebase'], frame) + '"'+os.path.join(scene['viparams']['newdir'], str(frame)+'p.hdr')+'"', shell=True)
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

def createradfile(scene, frame, export_op, connode, geonode):    
    if not connode or not connode.get('skyfiles'):
        radtext = geonode['radfiles'][0] if scene.gfe == 0 else geonode['radfiles'][frame]
    elif not geonode:
        skyframe = frame if scene.cfe > 0 else 0
        radtext = connode['skyfiles'][skyframe]
    elif geonode and connode: 
        geoframe = frame if scene.gfe > 0 and not geonode.inputs['Generative in'].links else 0
        skyframe = frame if scene.cfe > 0 and not geonode.inputs['Generative in'].links else 0
        radtext = geonode['radfiles'][geoframe] + connode['skyfiles'][skyframe]# if len(geonode['radfiles']) == 1 else geonode['radfiles'][geoframe] + connode['skyfiles'][0]
    
    with open("{}-{}.rad".format(scene['viparams']['filebase'], frame), 'w') as radfile:
        radfile.write(radtext)
   
    if not bpy.data.texts.get('Radiance input-{}'.format(frame)):
        bpy.data.texts.new('Radiance input-{}'.format(frame))
        
    bpy.data.texts['Radiance input-{}'.format(frame)].clear()
    bpy.data.texts['Radiance input-{}'.format(frame)].write(radtext)    

def createoconv(scene, frame, export_op, **kwargs):
    oconvcmd = "oconv {0}-{1}.rad > {0}-{1}.oct".format(scene['viparams']['filebase'], frame)
    subprocess.call(oconvcmd, shell = True)
    export_op.report({'INFO'},"Export is finished")

def cyfc1(self):
    scene = bpy.context.scene
    if 'LiVi' in scene.resnode or 'Shadow' in scene.resnode:
        for material in [m for m in bpy.data.materials if m.use_nodes and m.mattype in ('1', '2')]:
            try:
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
    else:
        return