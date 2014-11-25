import bpy, os, sys, multiprocessing, mathutils, bmesh, datetime, colorsys, bgl, blf, numpy
from math import sin, cos, asin, acos, pi, isnan
from bpy.props import IntProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty
try:
    import matplotlib
    matplotlib.use('Qt4Agg', force = True)
    import matplotlib.pyplot as plt
    from .windrose import WindroseAxes
    mp = 1
except:
    mp = 0

dtdf = datetime.date.fromordinal
#s = 60

def cmap(cm):
    cmdict = {'hot': 'livi', 'grey': 'shad'}
    for i in range(20):       
        if not bpy.data.materials.get('{}#{}'.format(cmdict[cm], i)):
            bpy.data.materials.new('{}#{}'.format(cmdict[cm], i))
        bpy.data.materials['{}#{}'.format(cmdict[cm], i)].diffuse_color = colorsys.hsv_to_rgb(0.75 - 0.75*(i/19), 1, 1) if cm == 'hot' else colorsys.hsv_to_rgb(1, 0, (i/19))

def radmat(self, scene):
    radname = self.name.replace(" ", "_")    
    radentry = '# ' + ('plastic', 'glass', 'dielectric', 'translucent', 'mirror', 'light', 'metal', 'antimatter')[int(self.radmatmenu)] + ' material\n' + \
            'void {} {}\n'.format(('plastic', 'glass', 'dielectric', 'trans', 'mirror', 'light', 'metal', 'antimatter')[int(self.radmatmenu)], radname) + \
           {'0': '0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} {2:.3f}\n'.format(self.radcolour, self.radspec, self.radrough), 
            '1': '0\n0\n3 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n'.format(self.radcolour), 
            '2': '0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} 0\n'.format(self.radcolour, self.radior),
            '3': '0\n0\n7 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} {2:.3f} {3:.3f} {4:.3f}\n'.format(self.radcolour, self.radspec, self.radrough, self.radtrans, self.radtranspec), 
            '4': '0\n0\n3 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n'.format(self.radcolour),
            '5': '0\n0\n3 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n'.format(self.radcolour), 
            '6': '0\n0\n5 {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} {1:.3f} {2:.3f}\n'.format(self.radcolour, self.radspec, self.radrough), 
            '7': '1 void\n0\n0\n'}[self.radmatmenu] + '\n'

    self['radentry'] = radentry
    return(radentry)

def radpoints(o, faces, sks):
    fentries = ['']*len(faces)   
    if sks:
        (skv0, skv1, skl0, skl1) = sks
    for f, face in enumerate(faces):
        fentry = "# Polygon \n{} polygon poly_{}_{}\n0\n0\n{}\n".format(o.data.materials[face.material_index].name.replace(" ", "_"), o.name.replace(" ", "_"), face.index, 3*len(face.verts))
        if sks:
            ventries = ''.join([" {0[0]} {0[1]} {0[2]}\n".format((o.matrix_world*mathutils.Vector((v[skl0][0]+(v[skl1][0]-v[skl0][0])*skv1, v[skl0][1]+(v[skl1][1]-v[skl0][1])*skv1, v[skl0][2]+(v[skl1][2]-v[skl0][2])*skv1)))) for v in face.verts])
        else:
            ventries = ''.join([" {0[0]:.3f} {0[1]:.3f} {0[2]:.3f}\n".format(v.co) for v in face.verts])
        fentries[f] = ''.join((fentry, ventries))        
    return ''.join(fentries)
                       
def viparams(op, scene):
    if not bpy.data.filepath:
        op.report({'ERROR'},"The Blender file has not been saved. Save the Blender file before exporting")
        return 'Save file'
    if " "  in bpy.data.filepath:
        op.report({'ERROR'},"The directory path or Blender filename has a space in it. Please save again without any spaces in the file name or the directory path")
        return 'Rename file'
    fd, fn = os.path.dirname(bpy.data.filepath), os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if not os.path.isdir(os.path.join(fd, fn)):
        os.makedirs(os.path.join(fd, fn))
    if not os.path.isdir(os.path.join(fd, fn, 'obj')):
        os.makedirs(os.path.join(fd, fn, 'obj'))
    nd = os.path.join(fd, fn)
    fb, ofb, idf  = os.path.join(nd, fn), os.path.join(nd, 'obj', fn), os.path.join(nd, 'in.idf')
    scene['viparams'] = {'rm': ('rm ', 'del ')[str(sys.platform) == 'win32'], 'cat': ('cat ', 'type ')[str(sys.platform) == 'win32'],
    'cp': ('cp ', 'copy ')[str(sys.platform) == 'win32'], 'nproc': str(multiprocessing.cpu_count()), 'filepath': bpy.data.filepath,
    'filename': fn, 'filedir': fd, 'newdir': nd, 'objfilebase': ofb, 'idf_file': idf, 'filebase': fb}
    if not scene.get('liparams'):
        scene['liparams'] = {}

def nodestate(self, opstate):
    if self['exportstate'] !=  opstate:
        self.exported = False
        if self.bl_label[0] != '*':
            self.bl_label = '*'+self.bl_label
    else:
        self.exported = True
        if self.bl_label[0] == '*':
            self.bl_label = self.bl_label[1:-1]

def face_centre(ob, obresnum, f):
    if obresnum:
        vsum = mathutils.Vector((0, 0, 0))
        for v in f.vertices:
            vsum = ob.active_shape_key.data[v].co + vsum
        return(vsum/len(f.vertices))
    else:
        return(f.center)

def v_pos(ob, v):
    return(ob.active_shape_key.data[v].co if ob.lires else ob.data.vertices[v].co)
    
def newrow(layout, s1, root, s2):
    row = layout.row()
    row.label(s1)
    row.prop(root, s2)

def retobj(name, fr, node, scene):
    if node.animmenu == "Geometry":
        return(scene['viparams']['objfilebase']+"-{}-{}.obj".format(name.replace(" ", "_"), fr))
    else:
        return(scene['viparams']['objfilebase']+"-{}-{}.obj".format(name.replace(" ", "_"), bpy.context.scene.frame_start))

def retelaarea(node):
    inlinks = [sock.links[0] for sock in node.inputs if sock.bl_idname in ('EnViSSFlowSocket', 'EnViSFlowSocket') and sock.links]
    outlinks = [sock.links[:] for sock in node.outputs if sock.bl_idname in ('EnViSSFlowSocket', 'EnViSFlowSocket') and sock.links]
    inosocks = [link.from_socket for link in inlinks if inlinks]
    outosocks = [link.to_socket for x in outlinks for link in x]
    if outosocks or inosocks:
        elaarea = max([facearea(bpy.data.objects[sock.node.zone], bpy.data.objects[sock.node.zone].data.polygons[int(sock.sn)]) for sock in outosocks + inosocks])
        node["_RNA_UI"] = {"ela": {"max":elaarea}}
#    except Exception as e:
#        print(e)
        
def objmode():
    if bpy.context.active_object and bpy.context.active_object.type == 'MESH' and not bpy.context.active_object.hide:
        bpy.ops.object.mode_set(mode = 'OBJECT')

def retmesh(name, fr, node, scene):
    if node.animmenu in ("Geometry", "Material"):
        return(scene['viparams']['objfilebase']+"-{}-{}.mesh".format(name.replace(" ", "_"), fr))
    else:
        return(scene['viparams']['objfilebase']+"-{}-{}.mesh".format(name.replace(" ", "_"), bpy.context.scene.frame_start))

def nodeinputs(node):
    try:
        ins = [i for i in node.inputs if not i.hide]
        if ins and not all([i.links for i in ins]):
            return 0
        elif ins and any([i.links[0].from_node.use_custom_color for i in ins if i.links]):
            return 0
        else:
            inodes = [i.links[0].from_node for i in ins if i.links[0].from_node.inputs]
            for inode in inodes:
                iins = [i for i in inode.inputs if not i.hide]
                if iins and not all([i.is_linked for i in iins]):
                    return 0
                elif iins and not all([i.links[0].from_node.use_custom_color for i in iins if i.is_linked]):
                    return 0
        return 1
    except:
        pass

def retmat(fr, node, scene):
    if node.animmenu == "Material":
        return("{}-{}.rad".format(scene['viparams']['filebase'], fr))
    else:
        return("{}-{}.rad".format(scene['viparams']['filebase'], scene.frame_start))

def retsky(fr, node, scene):
    if node.animmenu == "Time":
        return("{}-{}.sky".format(scene['viparams']['filebase'], fr))
    else:
        return("{}-{}.sky".format(scene['viparams']['filebase'], scene.frame_start))

def nodeexported(self):
    self.exported = 0

def negneg(x):
    x = 0 if float(x) < 0 else x        
    return float(x)

def clearscene(scene, op):
    for ob in [ob for ob in scene.objects if ob.type == 'MESH']:
        if ob.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
        if ob.get('lires'):
            scene.objects.unlink(ob)       
        if scene.get('livig') and ob.name in scene['livig']:
            v, f, svv, svf = [0] * 4             
            if 'export' in op.name or 'simulation' in op.name:
                bm = bmesh.new()
                bm.from_mesh(ob.data)
                if "export" in op.name:
                    if bm.faces.layers.int.get('rtindex'):
                        bm.faces.layers.int.remove(bm.faces.layers.int['rtindex'])
                    if bm.verts.layers.int.get('rtindex'):
                        bm.verts.layers.int.remove(bm.verts.layers.int['rtindex'])
                if "simulation" in op.name:
                    while bm.verts.layers.float.get('res{}'.format(v)):
                        livires = bm.verts.layers.float['res{}'.format(v)]
                        bm.verts.layers.float.remove(livires)
                        v += 1
                    while bm.faces.layers.float.get('res{}'.format(f)):
                        livires = bm.faces.layers.float['res{}'.format(f)]
                        bm.faces.layers.float.remove(livires)
                        f += 1
                bm.to_mesh(ob.data)
                bm.free()

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

def retmenu(dnode, axis, mtype):
    if mtype == 'Climate':
        return [dnode.inputs[axis].climmenu, dnode.inputs[axis].climmenu]
    if mtype == 'Zone':
        return [dnode.inputs[axis].zonemenu, dnode.inputs[axis].zonermenu]
    elif mtype == 'Linkage':
        return [dnode.inputs[axis].linkmenu, dnode.inputs[axis].linkrmenu]
    elif mtype == 'External node':
        return [dnode.inputs[axis].enmenu, dnode.inputs[axis].enrmenu]
        
def processf(pro_op, node):
    rtypes, ctypes, ztypes, zrtypes, ltypes, lrtypes, entypes, enrtypes = [], [], [], [], [], [], [], []

    envdict = {'Site Outdoor Air Drybulb Temperature [C] !Hourly': "Temperature ("+ u'\u00b0'+"C)",
               'Site Outdoor Air Relative Humidity [%] !Hourly': 'Humidity (%)',
                'Site Wind Direction [deg] !Hourly': 'Wind Direction (deg)',
                'Site Wind Speed [m/s] !Hourly': 'Wind Speed (m/s)',
                'Site Diffuse Solar Radiation Rate per Area [W/m2] !Hourly': "Diffuse Solar (W/m"+u'\u00b2'+")",
                'Site Direct Solar Radiation Rate per Area [W/m2] !Hourly': "Direct Solar (W/m"+u'\u00b2'+")"}
    zresdict = {'Zone Air Temperature [C] !Hourly': "Temperature ({}C)".format(u'\u00b0'),
                'Zone Air Relative Humidity [%] !Hourly': 'Humidity (%)',
                'Zone Air System Sensible Heating Rate [W] !Hourly': 'Zone heating (W)',
                'Zone Air System Sensible Cooling Rate [W] !Hourly': 'Zone cooling (W)',
                'Zone Windows Total Transmitted Solar Radiation Rate [W] !Hourly': 'Solar gain (W)',
                'Zone Infiltration Current Density Volume Flow Rate [m3/s] !Hourly': 'Infiltration (m'+u'\u00b3'+')',
                'Zone Infiltration Air Change Rate [ach] !Hourly': 'Infiltration (ACH)',
                'Zone Mean Air Temperature [C] ! Hourly': 'Mean Temperature ({})'.format(u'\u00b0'),
                'Zone Mean Radiant Temperature [C] !Hourly' :'Mean Radiant ({})'.format(u'\u00b0'), 
                'Zone Thermal Comfort Fanger Model PPD [%] !Hourly' :'PPD',
                'Zone Thermal Comfort Fanger Model PMV [] !Hourly' :'PMV',               
                'AFN Node CO2 Concentration [ppm] !Hourly': 'CO2',
                'Zone Air CO2 Concentration [ppm] !Hourly': 'CO2',
                'Zone Mean Radiant Temperature [C] !Hourly': 'MRT', 'Zone People Occupant Count [] !Hourly': 'Occupancy'}
    enresdict = {'AFN Node CO2 Concentration [ppm] !Hourly': 'CO2'}
    lresdict = {'AFN Linkage Node 1 to Node 2 Volume Flow Rate [m3/s] !Hourly': 'Linkage Flow out',
                'AFN Linkage Node 2 to Node 1 Volume Flow Rate [m3/s] !Hourly': 'Linkage Flow in',
                'AFN Surface Venting Window or Door Opening Factor [] !Hourly': 'Opening Factor'}
    resdict = {}
    allresdict = {}
    objlist = []
    
    with open(node.resfilename, 'r') as resfile:
        intro = 1    
        for line in resfile.readlines():
            linesplit = line.strip('\n').split(',')
            if intro:
                if len(linesplit) == 1:
                    intro = 0
                elif linesplit[1] == '1' and '!Hourly' in linesplit[-1]:
                    if linesplit[3] in zresdict and linesplit[2].strip('_OCCUPANCY') not in objlist and 'ExtNode' not in linesplit[2]:
                        objlist.append(linesplit[2].strip('_OCCUPANCY'))
                    
#                    allresdict[linesplit[0]] = ['{} {}'.format(linesplit[2], linesplit[-1].strip(' !Hourly'))]
                    allresdict[linesplit[0]] = []
            elif not intro and len(linesplit) == 2:
                allresdict[linesplit[0]].append(float(linesplit[1]))
            if linesplit[0] in resdict:
                if linesplit[0] == dos:
                    allresdict['Month'].append(int(linesplit[2]))
                    allresdict['Day'].append(int(linesplit[3]))
                    allresdict['Hour'].append(int(linesplit[5]))
                    allresdict['dos'].append(int(linesplit[1]))
                    
#            if linesplit[0] in resdict:
#                resdict[linesplit[0]].append(linesplit[1])
#                if linesplit[0] == dos:
#                    resdict['Month'].append(int(linesplit[2]))
#                    resdict['Day'].append(int(linesplit[3]))
#                    resdict['Hour'].append(int(linesplit[5]))
    
            elif len(linesplit) > 3 and linesplit[2] == 'Day of Simulation[]':
                resdict[linesplit[0]], allresdict['Month'],  allresdict['Day'], allresdict['Hour'], allresdict['dos'], dos, node['rtypes'] = ['Day of Simulation'], [], [], [], [], linesplit[0], ['Time']
    
            elif len(linesplit) > 3 and linesplit[2] == 'Environment':
                if 'Climate' not in node['rtypes']:
                    node['rtypes']+= ['Climate']
                try:
                    resdict[linesplit[0]] = ['Climate', envdict[linesplit[3]]]
                    ctypes.append(envdict[linesplit[3]])
                except:
                    pass
    
            elif len(linesplit) > 3 and linesplit[2].strip('_OCCUPANCY') in objlist:
                if 'Zone' not in node['rtypes']:
                   node['rtypes'] += ['Zone']
                try:
                    resdict[linesplit[0]] = [linesplit[2].strip('_OCCUPANCY'), zresdict[linesplit[3]]]
                    if linesplit[2].strip('_OCCUPANCY') not in ztypes:
                        ztypes.append(linesplit[2].strip('_OCCUPANCY'))
                    if zresdict[linesplit[3]] not in zrtypes:
                        zrtypes.append(zresdict[linesplit[3]])
                except:
                    pass
    
            elif len(linesplit) > 3 and linesplit[3] in lresdict:
                if 'Linkage' not in node['rtypes']:
                   node['rtypes'] += ['Linkage']
                try:
                    resdict[linesplit[0]] = [linesplit[2], lresdict[linesplit[3]]]
                    if linesplit[2] not in ltypes:
                        ltypes.append(linesplit[2])
                    if lresdict[linesplit[3]] not in lrtypes:
                        lrtypes.append(lresdict[linesplit[3]])
                except:
                    pass
            
            elif len(linesplit) > 3 and linesplit[3] in enresdict:
                if 'External node' not in node['rtypes']:
                   node['rtypes'] += ['External node']
                try:
                    resdict[linesplit[0]] = [linesplit[2], enresdict[linesplit[3]]]
                    if linesplit[2] not in entypes:
                        entypes.append(linesplit[2])
                    if enresdict[linesplit[3]] not in enrtypes:
                        enrtypes.append(enresdict[linesplit[3]])
                except Exception as e:
                    print('ext', e)
    
    node.dsdoy = datetime.datetime(datetime.datetime.now().year, allresdict['Month'][0], allresdict['Day'][0]).timetuple().tm_yday
    node.dedoy = datetime.datetime(datetime.datetime.now().year, allresdict['Month'][-1], allresdict['Day'][-1]).timetuple().tm_yday
    node['dos'], node['resdict'], node['ctypes'], node['ztypes'], node['zrtypes'], node['ltypes'], node['lrtypes'], node['entypes'], node['enrtypes'] = dos, resdict, ctypes, ztypes, zrtypes, ltypes, lrtypes, entypes, enrtypes
    node['allresdict'] = allresdict
    if node.outputs['Results out'].links:
       node.outputs['Results out'].links[0].to_node.update() 
    
def iprop(iname, idesc, imin, imax, idef):
    return(IntProperty(name = iname, description = idesc, min = imin, max = imax, default = idef))
def eprop(eitems, ename, edesc, edef):
    return(EnumProperty(items=eitems, name = ename, description = edesc, default = edef))
def bprop(bname, bdesc, bdef):
    return(BoolProperty(name = bname, description = bdesc, default = bdef))
def sprop(sname, sdesc, smaxlen, sdef):
    return(StringProperty(name = sname, description = sdesc, maxlen = smaxlen, default = sdef))
def fprop(fname, fdesc, fmin, fmax, fdef):
    return(FloatProperty(name = fname, description = fdesc, min = fmin, max = fmax, default = fdef))
def fvprop(fvsize, fvname, fvattr, fvdef, fvsub, fvmin, fvmax):
    return(FloatVectorProperty(size = fvsize, name = fvname, attr = fvattr, default = fvdef, subtype =fvsub, min = fvmin, max = fvmax))
def niprop(iname, idesc, imin, imax, idef):
        return(IntProperty(name = iname, description = idesc, min = imin, max = imax, default = idef, update = nodeexported))
def neprop(eitems, ename, edesc, edef):
    return(EnumProperty(items=eitems, name = ename, description = edesc, default = edef, update = nodeexported))
def nbprop(bname, bdesc, bdef):
    return(BoolProperty(name = bname, description = bdesc, default = bdef, update = nodeexported))
def nsprop(sname, sdesc, smaxlen, sdef):
    return(StringProperty(name = sname, description = sdesc, maxlen = smaxlen, default = sdef, update = nodeexported))
def nfprop(fname, fdesc, fmin, fmax, fdef):
    return(FloatProperty(name = fname, description = fdesc, min = fmin, max = fmax, default = fdef, update = nodeexported))
def nfvprop(fvname, fvattr, fvdef, fvsub):
    return(FloatVectorProperty(name=fvname, attr = fvattr, default = fvdef, subtype = fvsub, update = nodeexported))

def boundpoly(obj, mat, poly, enng):
    if mat.envi_boundary:
#        polyloc = obj.matrix_world*mathutils.Vector(poly.center)
        nodes = [node for node in enng.nodes if hasattr(node, 'zone') and node.zone == obj.name]
        for node in nodes:
            insock = node.inputs['{}_{}_b'.format(mat.name, poly.index)]
            outsock = node.outputs['{}_{}_b'.format(mat.name, poly.index)]              
            if insock.links:
                bobj = bpy.data.objects[insock.links[0].from_node.zone]
                bpoly = bobj.data.polygons[int(insock.links[0].from_socket.name.split('_')[-2])]
#                bpolyloc = bobj.matrix_world*mathutils.Vector(bpoly.center)
                if bobj.data.materials[bpoly.material_index] == mat:# and max(bpolyloc - polyloc) < 0.001 and abs(bpoly.area - poly.area) < 0.01:
                    return(("Surface", node.inputs['{}_{}_b'.format(mat.name, poly.index)].links[0].from_node.zone+'_'+str(bpoly.index), "NoSun", "NoWind"))
        
            elif outsock.links:
                bobj = bpy.data.objects[outsock.links[0].to_node.zone]
                bpoly = bobj.data.polygons[int(outsock.links[0].to_socket.name.split('_')[-2])]
#                bpolyloc = bobj.matrix_world*mathutils.Vector(bpoly.center)
                if bobj.data.materials[bpoly.material_index] == mat:# and max(bpolyloc - polyloc) < 0.001 and abs(bpoly.area - poly.area) < 0.01:
                    return(("Surface", node.outputs['{}_{}_b'.format(mat.name, poly.index)].links[0].to_node.zone+'_'+str(bpoly.index), "NoSun", "NoWind"))
#            except Exception as e:
#                print(e)
            return(("Outdoors", "", "SunExposed", "WindExposed"))
#        else:
#            return(("Outdoors", "", "SunExposed", "WindExposed"))
    elif mat.envi_thermalmass:
        return(("Adiabatic", "", "NoSun", "NoWind"))
    else:
        return(("Outdoors", "", "SunExposed", "WindExposed"))


def objvol(op, obj):
    bm , floor, roof, mesh = bmesh.new(), [], [], obj.data
    bm.from_object(obj, bpy.context.scene)
    for f in mesh.polygons:
        if obj.data.materials[f.material_index].envi_con_type == 'Floor':
            floor.append((facearea(obj, f), (obj.matrix_world*mathutils.Vector(f.center))[2]))
        elif obj.data.materials[f.material_index].envi_con_type == 'Roof':
            roof.append((facearea(obj, f), (obj.matrix_world*mathutils.Vector(f.center))[2]))
    zfloor = list(zip(*floor))
    if not zfloor and op:
        op.report({'INFO'},"Zone has no floor area")
#    else:
#        taf = sum(zfloor[0])
#    avhf = sum([(zfloor[0][i]*zfloor[1][i])/taf for i in range(len(zfloor[0]))])
#    zroof = list(zip(*roof))
#    tar = sum(zroof[0])
#    avhr = sum([(zroof[0][i]*zroof[1][i])/tar for i in range(len(zroof[0]))])

    return(bm.calc_volume()*obj.scale[0]*obj.scale[1]*obj.scale[2])
#    return((avhr - avhf)*(taf+tar)*obj.scale[0]*obj.scale[1]*obj.scale[2]/2)


def ceilheight(obj, vertz):
    mesh = obj.data
    for vert in mesh.vertices:
        vertz.append((obj.matrix_world * vert.co)[2])
    zmax, zmin = max(vertz), min(vertz)
    ceiling = [max((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) for poly in mesh.polygons if max((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) > 0.9 * zmax]
    floor = [min((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) for poly in mesh.polygons if min((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) < zmin + 0.1 * (zmax - zmin)]
    return(sum(ceiling)/len(ceiling)-sum(floor)/len(floor))

def vertarea(mesh, vert):
    area = 0
    faces = [face for face in vert.link_faces] 
    if len(faces) > 1:
        for f, face in enumerate(faces):
            ovs = []
            fvs = [le.verts[(0, 1)[le.verts[0] == vert]] for le in vert.link_edges]
            ofaces = [oface for oface in faces if len([v for v in oface.verts if v in face.verts]) == 2]    
            for oface in ofaces:
                ovs.append([i for i in face.verts if i in oface.verts])
            if len(ovs) == 1:
                sedgevs = (vert.index, [v.index for v in fvs if v not in ovs][0])
                sedgemp = mathutils.Vector([((mesh.verts[sedgevs[0]].co)[i] + (mesh.verts[sedgevs[1]].co)[i])/2 for i in range(3)])
                eps = [mathutils.geometry.intersect_line_line(face.calc_center_median(), ofaces[0].calc_center_median(), ovs[0][0].co, ovs[0][1].co)[1]] + [sedgemp]
            elif len(ovs) == 2:
                eps = [mathutils.geometry.intersect_line_line(face.calc_center_median(), ofaces[i].calc_center_median(), ovs[i][0].co, ovs[i][1].co)[1] for i in range(2)]
            area += mathutils.geometry.area_tri(vert.co, *eps) + mathutils.geometry.area_tri(face.calc_center_median(), *eps)
    elif len(faces) == 1:
        eps = [(ev.verts[0].co +ev.verts[1].co)/2 for ev in vert.link_edges]
        eangle = (vert.link_edges[0].verts[0].co - vert.link_edges[0].verts[1].co).angle(vert.link_edges[1].verts[0].co - vert.link_edges[1].verts[1].co)
        area = mathutils.geometry.area_tri(vert.co, *eps) + mathutils.geometry.area_tri(faces[0].calc_center_median(), *eps) * 2*pi/eangle
    return area       

def facearea(obj, face):
    omw = obj.matrix_world
    vs = [omw*mathutils.Vector(face.center)] + [omw*obj.data.vertices[v].co for v in face.vertices] + [omw*obj.data.vertices[face.vertices[0]].co]
    return(vsarea(obj, vs))

def vsarea(obj, vs):
    if len(vs) == 5:
        cross = mathutils.Vector.cross(vs[3]-vs[1], vs[3]-vs[2])
        return(0.5*(cross[0]**2 + cross[1]**2 +cross[2]**2)**0.5)
    else:
        i, area = 0, 0
        while i < len(vs) - 2:
            cross = mathutils.Vector.cross(vs[0]-vs[1+i], vs[0]-vs[2+i])
            area += 0.5*(cross[0]**2 + cross[1]**2 +cross[2]**2)**0.5
            i += 1
        return(area)

def windcompass():
    rad1 = 1.4
    dep = 2.8
    lettwidth = 0.3
    lettheight = 0.15
    bpy.ops.mesh.primitive_torus_add(location=(0.0, 0.0, 0.0), view_align=False, rotation=(0.0, 0.0, 0.0), major_segments=48, minor_segments=12, major_radius=2.5, minor_radius=0.01)
    bpy.ops.mesh.primitive_cone_add(location=(0.0, rad1, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, 0.0), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=((rad1**2/2)**0.5, (rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-0.25), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(rad1, 0.0, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-0.5), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=((rad1**2/2)**0.5, -(rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-0.75), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(0.0, -rad1, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(-(rad1**2/2)**0.5, -(rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1.25), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(-rad1, 0.0, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1.5), radius1 = 0.01, depth = dep)
    bpy.ops.mesh.primitive_cone_add(location=(-(rad1**2/2)**0.5, (rad1**2/2)**0.5, 0.0), view_align=False, rotation=(pi*-0.5, 0.0, pi*-1.75), radius1 = 0.01, depth = dep)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-lettheight*1.3, dep, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'N'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=((dep**2/2)**0.5-lettheight, (1+dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*-0.25))
    txt = bpy.context.active_object
    txt.data.body = 'NE'
    txt.scale = (0.4, 0.4, 0.4)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(dep, -lettheight, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'W'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=((dep**2/2)**0.5, -lettwidth-lettheight-(dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*0.25))
    txt = bpy.context.active_object
    txt.data.body = 'SW'
    txt.scale = (0.4, 0.4, 0.4)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-lettwidth/3, -dep-lettwidth*1.3, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'S'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-(dep**2/2)**0.5-lettwidth-0.1, -lettwidth/2-(dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*-0.25))
    txt = bpy.context.active_object
    txt.data.body = 'SE'
    txt.scale = (0.4, 0.4, 0.4)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-lettwidth-dep, -lettheight, 0.0), rotation=(0.0, 0.0, 0.0))
    txt = bpy.context.active_object
    txt.data.body = 'E'
    txt.scale = (0.5, 0.5, 0.5)
    bpy.ops.object.text_add(view_align=False, enter_editmode=False, location=(-(dep**2/2)**0.5-lettwidth, -(lettheight+lettwidth)*0.5+(dep**2/2)**0.5, 0.0), rotation=(0.0, 0.0, pi*0.25))
    txt = bpy.context.active_object
    txt.data.body = 'NW'
    txt.scale = (0.4, 0.4, 0.4)
    arrverts = ((0.05, -0.25, 0.0), (-0.05, -0.25, 0.0), (0.05, 0.25, 0.0), (-0.05, 0.25, 0.0), (0.15, 0.1875, 0.0), (-0.15, 0.1875, 0.0), (0.0, 0.5, 0.0))
    arrfaces = ((1, 0, 2, 3), (2, 4, 6, 5, 3))
    arrme = bpy.data.meshes.new('windarrow')
    arrob = bpy.data.objects.new('windarrow', arrme)
    arrme.from_pydata(arrverts, [], arrfaces)
    arrme.update()
    bpy.context.scene.objects.link(arrob)

def rgb2h(rgb):
    return colorsys.rgb_to_hsv(rgb[0]/255.0,rgb[1]/255.0,rgb[2]/255.0)[0]

def livisimacc(simnode, connode):
    return(simnode.csimacc if connode.bl_label in ('LiVi Compliance', 'LiVi CBDM') else simnode.simacc)

def drawpoly(x1, y1, x2, y2):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
    bgl.glBegin(bgl.GL_POLYGON)
    bgl.glVertex2i(x1, y2)
    bgl.glVertex2i(x2, y2)
    bgl.glVertex2i(x2, y1)
    bgl.glVertex2i(x1, y1)
    bgl.glEnd()
    bgl.glDisable(bgl.GL_BLEND)

def drawloop(x1, y1, x2, y2):
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glVertex2i(x1, y2)
    bgl.glVertex2i(x2, y2)
    bgl.glVertex2i(x2, y1)
    bgl.glVertex2i(x1, y1)
    bgl.glEnd()

def drawfont(text, fi, lencrit, height, x1, y1):
    blf.position(fi, x1, height - y1 - lencrit*26, 0)
    blf.draw(fi, text)

def mtx2vals(mtxlines, fwd, node):
    for m, mtxline in enumerate(mtxlines):
        if 'NROWS' in mtxline:
            patches = int(mtxline.split('=')[1])
        elif 'NCOLS' in mtxline:
            hours = int(mtxline.split('=')[1])
        elif mtxline == '\n':
            startline = m + 1
            break

    vecvals, vals, hour, patch = numpy.array([[x%24, (fwd+int(x/24))%7] + [0 for p in range(patches)] for x in range(hours)]), numpy.zeros((patches)), 0, 2
    
    for fvals in mtxlines[startline:]:
        if fvals == '\n':
            patch += 1
            hour = 0
        else:
            sumvals = sum([float(lv) for lv in fvals.split(" ") if not isnan(eval(lv))])/3
            if sumvals > 0:
                vals[patch - 2] += sumvals
                vecvals[hour][patch] = sumvals
            hour += 1
    return(vecvals.tolist(), vals)

def bres(scene, o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    if scene['cp'] == '1':
        rtlayer = bm.verts.layers.int['cindex']
        reslayer = bm.verts.layers.float['res{}'.format(scene.frame_current)]
        res = [v[reslayer] for v in bm.verts if v[rtlayer] > 0]
    elif scene['cp'] == '0':
        rtlayer = bm.faces.layers.int['cindex']
        reslayer = bm.faces.layers.float['res{}'.format(scene.frame_current)]
        res = [f[reslayer] for f in bm.faces if f[rtlayer] > 0]
    bm.free()
    return res
    
def framerange(scene, anim):
    if anim == 'Static':
        return(range(scene.frame_current, scene.frame_current +1))
    else:
        return(range(scene.frame_start, scene.fe + 1))

def frameindex(scene, anim):
    if anim == 'Static':
        return(range(0, 1))
    else:
        return(range(0, scene.frame_end - scene.frame_start +1))

def retobjs(otypes):
    scene = bpy.context.scene
    if otypes == 'livig':
        return([geo for geo in scene.objects if geo.type == 'MESH' and len(geo.data.materials) and not (geo.parent and os.path.isfile(geo.iesname)) and not geo.lila \
        and geo.hide == False and geo.layers[scene.active_layer] == True and geo.lires == 0 and geo.get('VIType') not in ('SPathMesh', 'SunMesh', 'Wind_Plane', 'SkyMesh')])
    elif otypes == 'livigengeo':
        return([geo for geo in scene.objects if geo.type == 'MESH' and not any([m.livi_sense for m in geo.data.materials])])
    elif otypes == 'livigengeosel':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.select == True and not any([m.livi_sense for m in geo.data.materials])])
    elif otypes == 'livil':
        return([geo for geo in scene.objects if (geo.type == 'LAMP' or geo.lila) and geo.hide == False and geo.layers[scene.active_layer] == True])
    elif otypes == 'livic':
        return([geo for geo in scene.objects if geo.type == 'MESH' and li_calcob(geo, 'livi') and geo.lires == 0 and geo.hide == False and geo.layers[scene.active_layer] == True])
    elif otypes == 'livir':
        return([geo for geo in bpy.data.objects if geo.type == 'MESH' and True in [m.livi_sense for m in geo.data.materials] and geo.licalc and geo.layers[scene.active_layer] == True])
    elif otypes == 'envig':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.hide == False and geo.layers[0] == True])
    elif otypes == 'ssc':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.licalc and geo.lires == 0 and geo.hide == False and geo.layers[scene.active_layer] == True])

def viewdesc(context):
    region = context.region
#    (width, height) = [getattr(region, s) for s in ('width', 'height')]
    width, height = region.width, region.height
    mid_x, mid_y = width/2, height/2
    return(mid_x, mid_y, width, height)
    
def skfpos(o, frame, vis):
    vcos = [o.matrix_world*o.data.shape_keys.key_blocks[str(frame)].data[v].co for v in vis]
    maxx = max([vco[0] for vco in vcos])
    minx = min([vco[0] for vco in vcos])
    maxy = max([vco[1] for vco in vcos])
    miny = min([vco[1] for vco in vcos])
    maxz = max([vco[2] for vco in vcos])
    minz = min([vco[2] for vco in vcos])
    return mathutils.Vector(((maxx + minx) * 0.5, (maxy + miny) * 0.5, (maxz + minz) * 0.5))
#    return mathutils.Vector((sum([vco[0] for vco in vcos])/len(vcos), sum([vco[1] for vco in vcos])/len(vcos), sum([vco[2] for vco in vcos])/len(vcos)))

def selmesh(sel):
    bpy.ops.object.mode_set(mode = 'EDIT')
    if sel == 'selenm':
        bpy.ops.mesh.select_mode(type="EDGE")
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
    elif sel == 'desel':
        bpy.ops.mesh.select_all(action='DESELECT')
    elif sel in ('delf', 'rd'):
        if sel == 'delf':
            bpy.ops.mesh.delete(type = 'FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action='DESELECT')
#    elif sel == 'rd':
#        bpy.ops.mesh.select_all(action='SELECT')
#        bpy.ops.mesh.remove_doubles()
#        bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')

def draw_index(context, leg, mid_x, mid_y, width, height, posis, res):
    vecs = [mathutils.Vector((vec[0] / vec[3], vec[1] / vec[3], vec[2] / vec[3])) for vec in posis]
    xs = [int(mid_x + vec[0] * mid_x) for vec in vecs]
    ys = [int(mid_y + vec[1] * mid_y) for vec in vecs]
    [(blf.position(0, xs[ri], ys[ri], 0), blf.draw(0, ('{:.1f}', '{:.0f}')[r > 100].format(r))) for ri, r in enumerate(res) if (leg == 1 and (xs[ri] > 120 or ys[ri] < height - 530)) or leg == 0]
        
def edgelen(ob, edge):
    omw = ob.matrix_world
    vdiff = omw * (ob.data.vertices[edge.vertices[0]].co - ob.data.vertices[edge.vertices[1]].co)
    mathutils.Vector(vdiff).length

def sunpath1(self, context):
    sunpath()

def sunpath2(scene):
    sunpath()

def sunpath():
    # For future reference I can also project an emmisve sky texture on a sphere using the normal texture coordinate.
    scene = bpy.context.scene
    sun = [ob for ob in scene.objects if ob.get('VIType') == 'Sun'][0]
    skysphere = [ob for ob in scene.objects if ob.get('VIType') == 'SkyMesh'][0]

    if 0 in (sun['solhour'] == scene.solhour, sun['solday'] == scene.solday, sun['soldistance'] == scene.soldistance):
        sunob = [ob for ob in scene.objects if ob.get('VIType') == 'SunMesh'][0]
        spathob = [ob for ob in scene.objects if ob.get('VIType') == 'SPathMesh'][0]
        beta, phi = solarPosition(scene.solday, scene.solhour, scene['latitude'], scene['longitude'])[2:]
        sunob.location.z = sun.location.z = spathob.location.z + scene.soldistance * sin(beta)
        sunob.location.x = sun.location.x = spathob.location.x -(scene.soldistance**2 - (sun.location.z-spathob.location.z)**2)**0.5  * sin(phi)
        sunob.location.y = sun.location.y = spathob.location.y -(scene.soldistance**2 - (sun.location.z-spathob.location.z)**2)**0.5 * cos(phi)
        sun.rotation_euler = pi * 0.5 - beta, 0, -phi
        spathob.scale = 3 * [scene.soldistance/100]
        skysphere.scale = 3 * [1.05 * scene.soldistance/100]
        sunob.scale = 3*[scene.soldistance/100]

        if scene.render.engine == 'CYCLES':
            if bpy.data.worlds['World'].node_tree:
                if 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
                    bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)
            if sun.data.node_tree:
                for blnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Blackbody']:
                    blnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5 if beta > 0 else 2000
                for emnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Emission']:
                    emnode.inputs[1].default_value = 5 * sin(beta) if beta > 0 else 0
            if sunob.data.materials[0].node_tree:
                for smblnode in [node for node in sunob.data.materials[0].node_tree.nodes if sunob.data.materials and node.bl_label == 'Blackbody']:
                    smblnode.inputs[0].default_value = 2000 + 3500*sin(beta)**0.5 if beta > 0 else 2000
            if skysphere and not skysphere.hide and skysphere.data.materials[0].node_tree:
                if 'Sky Texture' in [no.bl_label for no in skysphere.data.materials[0].node_tree.nodes]:
                    skysphere.data.materials[0].node_tree.nodes['Sky Texture'].sun_direction = sin(phi), -cos(phi), sin(beta)

        sun['solhour'], sun['solday'], sun['soldistance'] = scene.solhour, scene.solday, scene.soldistance
    else:
        return

def epwlatilongi(scene, node):
    with open(node.weather, "r") as epwfile:
        fl = epwfile.readline()
        latitude, longitude = float(fl.split(",")[6]), float(fl.split(",")[7])
#    else:
#        latitude, longitude = node.latitude, node.longitude
    return latitude, longitude

#Compute solar position (altitude and azimuth in degrees) based on day of year (doy; integer), local solar time (lst; decimal hours), latitude (lat; decimal degrees), and longitude (lon; decimal degrees).
def solarPosition(doy, lst, lat, lon):
    #Set the local standard time meridian (lsm) (integer degrees of arc)
    lsm = round(lon/15, 0)*15
    #Approximation for equation of time (et) (minutes) comes from the Wikipedia article on Equation of Time
    b = 2*pi*(doy-81)/364
    et = 9.87 * sin(2*b) - 7.53 * cos(b) - 1.5 * sin(b)
    #The following formulas adapted from the 2005 ASHRAE Fundamentals, pp. 31.13-31.16
    #Conversion multipliers
    degToRad = 2*pi/360
    radToDeg = 1/degToRad
    #Apparent solar time (ast)
    ast = lst + et/60 + (lsm-lon)/15
    #Solar declination (delta) (radians)
    delta = degToRad*23.45 * sin(2*pi*(284+doy)/365)
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
    phi = 2*pi - phi if ast<=12 or ast >= 24 else phi
    azimuth = radToDeg*phi
    return([altitude, azimuth, beta, phi])

def set_legend(ax):
    l = ax.legend(borderaxespad = -4)
    plt.setp(l.get_texts(), fontsize=8)

def wr_axes():
    fig = plt.figure(figsize=(8, 8), dpi=150, facecolor='w', edgecolor='w')
    rect = [0.1, 0.1, 0.8, 0.8]
    ax = WindroseAxes(fig, rect, axisbg='w')
    fig.add_axes(ax)
    return(fig, ax)

def skframe(pp, scene, oblist, anim):
    for frame in range(scene.fs, scene.fe + 1):
        scene.frame_set(frame)
        for o in [o for o in oblist if o.data.shape_keys]:
            for shape in o.data.shape_keys.key_blocks:
                if shape.name.isdigit():
                    shape.value = shape.name == str(frame)
                    shape.keyframe_insert("value")

def gentarget(tarnode, result):
    if tarnode.stat == '0':
        res = sum(result)/len(result)
    elif tarnode.stat == '1':
        res = max(result)
    elif tarnode.stat == '2':
        res = min(result)
    elif tarnode.stat == '3':
        res = sum(result)

    if tarnode.value > res and tarnode.ab == '0':
        return(1)
    elif tarnode.value < res and tarnode.ab == '1':
        return(1)
    else:
        return(0)

def selobj(scene, geo):
    for ob in scene.objects:
        ob.select = True if ob == geo else False
    scene.objects.active = geo

def nodeid(node):
    for ng in bpy.data.node_groups:
        if node in ng.nodes[:]:
            return node.name+'@'+ng.name

def nodecolour(node, prob):
    (node.use_custom_color, node.color) = (1, (1.0, 0.3, 0.3)) if prob else (0, (1.0, 0.3, 0.3))
    return not prob

def remlink(node, links):
    for link in links:
        bpy.data.node_groups[node['nodeid'].split('@')[1]].links.remove(link)

def epentry(header, params, paramvs):
    return '{}\n'.format(header+(',', '')[header == ''])+'\n'.join([('    ', '')[header == '']+'{:{width}}! - {}'.format(str(pv[0])+(',', ';')[pv[1] == params[-1]], pv[1], width = 80 + (0, 4)[header == '']) for pv in zip(paramvs, params)]) + ('\n\n', '')[header == '']

def sockhide(node, lsocknames):
    try:
        for ins in [insock for insock in node.inputs if insock.name in lsocknames]:
            node.outputs[ins.name].hide = True if ins.links else False
        for outs in [outsock for outsock in node.outputs if outsock.name in lsocknames]:
            node.inputs[outs.name].hide = True if outs.links else False
    except Exception as e:
        print('sockhide', e)

def socklink(sock, ng):
    try:
        valid1 = sock.valid if not sock.get('valid') else sock['valid']
        for link in sock.links:
            valid2 = link.to_socket.valid if not link.to_socket.get('valid') else link.to_socket['valid'] 
            if not set(valid1)&set(valid2):
                bpy.data.node_groups[ng].links.remove(link)
    except:
        pass
    
def rettimes(ts, fs, us):
    tot = range(min(len(ts), len(fs), len(us)))
    fstrings, ustrings, tstrings = [[] for t in tot],  [[] for t in tot], ['Through: {}/{}'.format(dtdf(ts[t]).month, dtdf(ts[t]).day) for t in tot]
    for t in tot:
        fstrings[t]= ['For: '+''.join(f.strip()) for f in fs[t].split(' ') if f.strip(' ') != '']
        for uf, ufor in enumerate(us[t].split(';')):
            ustrings[t].append([])
            for ut, utime in enumerate(ufor.split(',')):
                ustrings[t][uf].append(['Until: '+','.join([u.strip() for u in utime.split(' ') if u.strip(' ')])])
    return(tstrings, fstrings, ustrings)
    
def epschedwrite(name, stype, ts, fs, us):
    params = ['Name', 'Schedule Type Limits Name']
    paramvs = [name, stype]
    for t in range(len(ts)):
        params.append('Field {}'.format(len(params)-2))
        paramvs .append(ts[t])
        for f in range(len(fs[t])):
            params.append('Field {}'.format(len(params)-2))
            paramvs.append(fs[t][f])
            for u in range(len(us[t][f])):
                params.append('Field {}'.format(len(params)-2))
                paramvs.append(us[t][f][u][0])
    return epentry('Schedule:Compact', params, paramvs)
    
def li_calcob(ob, li):
    if not ob.data.materials:
        return False
    else:
        ob.licalc = 1 if [face.index for face in ob.data.polygons if (ob.data.materials[face.material_index].mattype == '2', ob.data.materials[face.material_index].mattype == '1')[li == 'livi']] else 0
        return ob.licalc
    