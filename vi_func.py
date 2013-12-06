import bpy, os, sys, multiprocessing, mathutils, bmesh, datetime, colorsys, bgl, blf
from math import sin, cos, asin, acos, pi
from bpy.props import IntProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty
import matplotlib.pyplot as plt
from . import windrose

#from . import windrose
dtdf = datetime.date.fromordinal

def newrow(layout, s1, root, s2):
    row = layout.row()
    row.label(s1)
    row.prop(root, s2)

def retobj(name, fr, node):
    if node.animmenu == "Geometry":
        return(node.objfilebase+"-{}-{}.obj".format(name.replace(" ", "_"), fr))
    else:
        return(node.objfilebase+"-{}-0.obj".format(name.replace(" ", "_")))

def retmesh(name, fr, node):
    if node.animmenu in ("Geometry", "Material"):
        return(node.objfilebase+"-{}-{}.mesh".format(name.replace(" ", "_"), fr))
    else:
        return(node.objfilebase+"-{}-0.mesh".format(name.replace(" ", "_")))

def retmat(fr, node):
    if node.animmenu == "Material":
        return(node.filebase+"-"+str(fr)+".rad")
    else:
        return(node.filebase+"-0.rad")

def retsky(fr, node, geonode):
    if node.animmenu == "Time":
        return(geonode.filebase+"-"+str(fr)+".sky")
    else:
        return(geonode.filebase+"-0.sky")

def nodeinit(node):
    if str(sys.platform) != 'win32':
        node.rm = "rm "
        node.cat = "cat "
        node.fold = "/"
        node.cp = "cp "
    else:
        node.rm = "del "
        node.cat = "type "
        node.fold = r'"\"'
        node.cp = "copy "
    node.nproc = str(multiprocessing.cpu_count())
    node.filepath = bpy.data.filepath
    node.filename = os.path.splitext(os.path.basename(node.filepath))[0]
    node.filedir = os.path.dirname(node.filepath)
    if not os.path.isdir(os.path.join(node.filedir, node.filename)):
        os.makedirs(os.path.join(node.filedir, node.filename))
    if not os.path.isdir(os.path.join(node.filedir, node.filename, 'obj')):
       os.makedirs(os.path.join(node.filedir, node.filename, 'obj'))
    node.newdir = os.path.join(node.filedir, node.filename)
    node.filebase = os.path.join(node.newdir, node.filename)
    node.objfilebase = os.path.join(node.newdir, 'obj', node.filename)
    node.idf_file = os.path.join(node.newdir, "in.idf")

def nodeexported(self):
    self.exported = 0

def negneg(x):
    if float(x) < 0:
        x = 0
    return float(x)

def clearscenece(scene):
    for sunob in [ob for ob in scene.objects if ob.type == 'LAMP' and ob.data.type == 'SUN']:
        scene.objects.unlink(sunob)

    for ob in [ob for ob in scene.objects if ob.type == 'MESH']:
        scene.objects.active = ob
        for vcol in ob.data.vertex_colors:
            bpy.ops.mesh.vertex_color_remove()

def clearscenege(scene):
    for ob in [ob for ob in scene.objects if ob.type == 'MESH']:
        scene.objects.active = ob
        for vcol in ob.data.vertex_colors:
            bpy.ops.mesh.vertex_color_remove()

def clearscened(scene):
    for ob in [ob for ob in scene.objects if ob.type == 'MESH']:
        if ob.lires == 1:
            scene.objects.unlink(ob)

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

def processf(pro_op, node):
    rtypes, ctypes, ztypes, zrtypes, ltypes, lrtypes = [], [], [], [], [], []
    resfile = open(node.resfilename, 'r')

    envdict = {'Site Outdoor Air Drybulb Temperature [C] !Hourly': "Temperature ("+ u'\u00b0'+"C)",
               'Site Outdoor Air Relative Humidity [%] !Hourly': 'Humidity (%)',
                'Site Wind Direction [deg] !Hourly': 'Wind Direction (deg)',
                'Site Wind Speed [m/s] !Hourly': 'Wind Speed (m/s)',
                'Site Diffuse Solar Radiation Rate per Area [W/m2] !Hourly': "Diffuse Solar (W/m"+u'\u00b2'+")",
                'Site Direct Solar Radiation Rate per Area [W/m2] !Hourly': "Direct Solar (W/m"+u'\u00b2'+")"}
    zresdict = {'Zone Air Temperature [C] !Hourly': "Zone Temperature ("+ u'\u00b0'+"C)",
                'Zone Air System Sensible Heating Rate [W] !Hourly': 'Zone heating (W)',
                'Zone Air System Sensible Cooling Rate [W] !Hourly': 'Zone cooling (W)',
                'Zone Windows Total Transmitted Solar Radiation Rate [W] !Hourly': 'Solar gain (W)',
                'AFN Zone Infiltration Volume [m3] !Hourly': 'Infiltration (m'+u'\u00b3'+')',
                'AFN Zone Infiltration Air Change Rate [ach] !Hourly': 'ACH'}
    lresdict = {'AFN Linkage Node 1 to Node 2 Volume Flow Rate [m3/s] !Hourly': 'Linkage Flow 1 to 2',
                'AFN Surface Venting Window or Door Opening Factor [] !Hourly': 'Opening Factor'}
    resdict = {}

    objlist = [obj.name.upper() for obj in bpy.data.objects if obj.envi_type == '1' and obj.layers[1] == True]

    for line in resfile.readlines():
        linesplit = line.strip('\n').split(',')

        if linesplit[0] in resdict:
            resdict[linesplit[0]].append(linesplit[1])
            if linesplit[0] == dos:
                resdict['Month'].append(linesplit[2])
                resdict['Day'].append(linesplit[3])
                resdict['Hour'].append(linesplit[5])

        elif len(linesplit) > 3 and linesplit[2] == 'Day of Simulation[]':
            resdict[linesplit[0]] = ['Day of Simulation']
            resdict['Month'] = []
            resdict['Day'] = []
            resdict['Hour'] = []
            dos = linesplit[0]
            node['rtypes'] = ['Time']

        elif len(linesplit) > 3 and linesplit[2] == 'Environment':
            if 'Climate' not in node['rtypes']:
                node['rtypes']+= ['Climate']
            resdict[linesplit[0]] = ['Climate', envdict[linesplit[3]]]
            ctypes.append(envdict[linesplit[3]])

        elif len(linesplit) > 3 and linesplit[2] in objlist:
            if 'Zone' not in node['rtypes']:
               node['rtypes'] += ['Zone']
            resdict[linesplit[0]] = [linesplit[2], zresdict[linesplit[3]]]
            if linesplit[2] not in ztypes:
                ztypes.append(linesplit[2])
            if zresdict[linesplit[3]] not in zrtypes:
                zrtypes.append(zresdict[linesplit[3]])

        elif len(linesplit) > 3 and linesplit[3] in lresdict:
            if 'Linkage' not in node['rtypes']:
               node['rtypes'] += ['Linkage']
            resdict[linesplit[0]] = [linesplit[2], lresdict[linesplit[3]]]
            if linesplit[2] not in ltypes:
                ltypes.append(linesplit[2])
            if lresdict[linesplit[3]] not in lrtypes:
                lrtypes.append(lresdict[linesplit[3]])

    resfile.close()
#    node['rtypes'] = rtypes
    node['dos'] = dos
    node['resdict'] = resdict
    node['ctypes'] = ctypes
    node['ztypes'] = ztypes
    node['zrtypes'] = zrtypes
    node['ltypes'] = ltypes
    node['lrtypes'] = lrtypes
    node.dsdoy = int(resdict[dos][1])
    node.dedoy = int(resdict[dos][-1])


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
def fvprop(fvname, fvattr, fvdef, fvsub):
    return(FloatVectorProperty(name=fvname, attr = fvattr, default = fvdef, subtype =fvsub))
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

def boundpoly(obj, mat, poly):
    if mat.envi_boundary:
        polyloc = obj.matrix_world*mathutils.Vector(poly.center)
        for node in bpy.data.node_groups['EnVi Network'].nodes:
            if hasattr(node, 'zone'):
                if node.inputs[mat.name+'_b'].is_linked == True:
                    bobj = bpy.data.objects[node.inputs[mat.name+'_b'].links[0].from_node.zone]
                    for bpoly in bobj.data.polygons:
                        bpolyloc = bobj.matrix_world*mathutils.Vector(bpoly.center)
                        if bobj.data.materials[bpoly.material_index] == mat and max(bpolyloc - polyloc) < 0.001 and abs(bpoly.area - poly.area) < 0.01:
                            return(("Surface", node.inputs[mat.name+'_b'].links[0].from_node.zone+'_'+str(bpoly.index), "NoSun", "NoWind"))

                elif node.outputs[mat.name+'_b'].is_linked == True:
                    bobj = bpy.data.objects[node.outputs[mat.name+'_b'].links[0].to_node.zone]
                    for bpoly in bobj.data.polygons:
                        bpolyloc = bobj.matrix_world*mathutils.Vector(bpoly.center)
                        if bobj.data.materials[bpoly.material_index] == mat and max(bpolyloc - polyloc) < 0.001 and abs(bpoly.area - poly.area) < 0.01:
                            return(("Surface", node.outputs[mat.name+'_b'].links[0].to_node.zone+'_'+str(bpoly.index), "NoSun", "NoWind"))
            else:
                return(("Outdoors", "", "SunExposed", "WindExposed"))
        else:
            return(("Outdoors", "", "SunExposed", "WindExposed"))
    else:
        return(("Outdoors", "", "SunExposed", "WindExposed"))


def objvol(obj):
    bm = bmesh.new()
    bm.from_object(obj, bpy.context.scene)

    floor, roof = [], []
    mesh = obj.data
    for f in mesh.polygons:
        if obj.data.materials[f.material_index].envi_con_type == 'Floor':
            floor.append((triarea(obj, f), (obj.matrix_world*mathutils.Vector(f.center))[2]))
        elif obj.data.materials[f.material_index].envi_con_type == 'Roof':
            roof.append((triarea(obj, f), (obj.matrix_world*mathutils.Vector(f.center))[2]))
    zfloor = list(zip(*floor))
    taf = sum(zfloor[0])
    avhf = sum([(zfloor[0][i]*zfloor[1][i])/taf for i in range(len(zfloor[0]))])
    zroof = list(zip(*roof))
    tar = sum(zroof[0])
    avhr = sum([(zroof[0][i]*zroof[1][i])/tar for i in range(len(zroof[0]))])

    return(bm.calc_volume()*obj.scale[0]*obj.scale[1]*obj.scale[2])
#    return((avhr - avhf)*(taf+tar)*obj.scale[0]*obj.scale[1]*obj.scale[2]/2)


def ceilheight(obj, vertz):
    mesh = obj.data
    for vert in mesh.vertices:
        vertz.append((obj.matrix_world * vert.co)[2])
    zmax = max(vertz)
    zmin = min(vertz)
    ceiling = [max((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) for poly in mesh.polygons if max((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) > 0.9 * zmax]
    floor = [min((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) for poly in mesh.polygons if min((obj.matrix_world * mesh.vertices[poly.vertices[0]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[1]].co)[2], (obj.matrix_world * mesh.vertices[poly.vertices[2]].co)[2]) < zmin + 0.1 * (zmax - zmin)]
    return(sum(ceiling)/len(ceiling)-sum(floor)/len(floor))


def triarea(obj, face):
    omw = obj.matrix_world
    vs = [omw*mathutils.Vector(face.center)] + [omw*obj.data.vertices[v].co for v in face.vertices] + [omw*obj.data.vertices[face.vertices[0]].co]
    return(vsarea(obj, vs))

def vsarea(obj, vs):
    if len(vs) == 5:
        cross = mathutils.Vector.cross(vs[3]-vs[1], vs[3]-vs[2])
        return(0.5*(cross[0]**2 + cross[1]**2 +cross[2]**2)**0.5)
    else:
        i = 0
        area = 0
        while i < len(vs) - 2:
            cross = mathutils.Vector.cross(vs[0]-vs[1+i], vs[0]-vs[2+i])
            area += 0.5*(cross[0]**2 + cross[1]**2 +cross[2]**2)**0.5
            i += 1
        return(area)

def rettimes(ts, fs, us):
    tot = range(min(len(ts), len(fs), len(us)))
    fstrings = [[] for t in tot]
    ustrings = [[] for t in tot]
    tstrings = ['Through: '+str(dtdf(ts[t]).month)+'/'+str(dtdf(ts[t]).day)+',' for t in tot]
    for t in tot:
        for f in fs[t].split(' '):
            fstrings[t].append('For: '+''.join([f+',' for f in f.split(' ') if f != '']))
        for uf, ufor in enumerate(us[t].split(';')):
            ustrings[t].append([])
            for ut, utime in enumerate(ufor.split(',')):
                ustrings[t][uf].append(['Until: '+''.join([u+',' for u in utime.split(' ') if u != ''])])
    ustrings[-1][-1][-1][-1] = ustrings[-1][-1][-1][-1][:-1]+';'
    return(tstrings, fstrings, ustrings)

def socklink(sock, ng):
    try:
        lsock = (sock.links[0].from_socket, sock.links[0].to_socket)[sock.in_out == 'OUT']
        if sock.is_linked and sock.draw_color(bpy.context, sock.node) != lsock.draw_color(bpy.context, lsock.node):
            bpy.data.node_groups[ng].links.remove(sock.links[0])
    except:
        pass

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
    return(simnode.csimacc if connode.bl_label == 'LiVi Compliance' else simnode.simacc)

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

def mtx2vals(mtxlines, fwd):
    np = 0
    try:
        import numpy
        vecvals = numpy.array([[x%24, (fwd+int(x/24))%7] + [0 for p in range(146)] for x in range(0,8760)])
        vals = numpy.zeros((146))
        np = 1
    except:
        vecvals = [[x%24, (fwd+int(x/24))%7] + [0 for p in range(146)] for x in range(0,8760)]
        vals = [0 for x in range(146)]

    hour = 0
    patch = 2
    for fvals in mtxlines:
        try:
            sumvals = sum([float(lv) for lv in fvals.split(" ")])
            if sumvals > 0:
                vals[patch - 2] += sumvals
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
    return(vecvals, vals)

def framerange(scene):
    return(range(scene.frame_start, scene.frame_end +1))

def retobjs(otypes):
    scene = bpy.context.scene
    if otypes == 'livig':
        return([geo for geo in scene.objects if geo.type == 'MESH' and not geo.children  and 'lightarray' not in geo.name and geo.hide == False and geo.layers[scene.active_layer] == True])
    elif otypes == 'livil':
        return([geo for geo in scene.objects if (geo.ies_name != "" or 'lightarray' in geo.name) and geo.hide == False and geo.layers[scene.active_layer] == True])
    elif otypes == 'livic':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.licalc == 1 and geo.lires == 0 and geo.hide == False and geo.layers[scene.active_layer] == True])
    elif otypes == 'livir':
        return([geo for geo in bpy.data.objects if geo.type == 'MESH' and True in [m.livi_sense for m in geo.data.materials] and geo.licalc and geo.layers[scene.active_layer] == True])
    elif otypes == 'envig':
        return([geo for geo in scene.objects if geo.type == 'MESH' and geo.hide == False and geo.layers[0] == True])

def sunpath(self, context):
    scene = context.scene
    sun = [ob for ob in scene.objects if ob.spob == 1][0]
    if 0 in (sun['solhour'] == scene.solhour, sun['solday'] == scene.solday, sun['soldistance'] == scene.soldistance):
        sunob = [ob for ob in scene.objects if ob.spob == 2][0]
        spathob = [ob for ob in scene.objects if ob.spob == 3][0]
        beta, phi = solarPosition(scene.solday, scene.solhour, scene.latitude, scene.longitude)[2:]
        sunob.location.z = sun.location.z = scene.soldistance * sin(beta)
        sunob.location.x = sun.location.x = -(scene.soldistance**2 - sun.location.z**2)**0.5  * sin(phi)
        sunob.location.y = sun.location.y = -(scene.soldistance**2 - sun.location.z**2)**0.5 * cos(phi)
        sun.rotation_euler = pi * 0.5 - beta, 0, -phi
        spathob.scale = 3 * [scene.soldistance/100]
        sunob.scale = 3 * [scene.soldistance/10]

        if scene.render.engine == 'CYCLES' and hasattr(bpy.data.worlds['World'].node_tree, 'nodes'):
            if 'Sky Texture' in [no.bl_label for no in bpy.data.worlds['World'].node_tree.nodes]:
                bpy.data.worlds['World'].node_tree.nodes['Sky Texture'].sun_direction = -sin(phi), -cos(phi), sin(beta)
#                bpy.data.worlds['World'].node_tree.nodes['Background'].inputs[1].default_value = sin(beta)
                for blnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Blackbody']:
                    blnode.inputs[0].default_value = 3000 + 50*beta*180/pi
                for emnode in [node for node in sun.data.node_tree.nodes if node.bl_label == 'Emission']:
                    emnode.inputs[1].default_value = 5 * sin(beta)
                for smblnode in [node for node in sunob.data.materials[0].node_tree.nodes if sunob.data.materials and node.bl_label == 'Blackbody']:
                    smblnode.inputs[0].default_value = 3000 + 50*beta*180/pi

        sun['solhour'], sun['solday'], sun['soldistance'] = scene.solhour, scene.solday, scene.soldistance
    else:
        return

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
    fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
    rect = [0.1, 0.1, 0.8, 0.8]
    ax = windrose.WindroseAxes(fig, rect, axisbg='w')
    fig.add_axes(ax)
    return ax
