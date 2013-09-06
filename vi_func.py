import bpy, os, sys, multiprocessing, mathutils, bmesh, datetime
from math import sin, cos, asin, acos, pi
from bpy.props import IntProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty
dtdf = datetime.date.fromordinal

def obj(name, fr, node):
    if node.animmenu == "Geometry":
        return(node.objfilebase+"-{}-{}.obj".format(name.replace(" ", "_"), fr))
    else:
        return(node.objfilebase+"-{}-0.obj".format(name.replace(" ", "_")))

def mesh(name, fr, node):
    if node.animmenu in ("Geometry", "Material"):
        return(node.objfilebase+"-{}-{}.mesh".format(name.replace(" ", "_"), fr))
    else:
        return(node.objfilebase+"-{}-0.mesh".format(name.replace(" ", "_")))

def mat(fr, node):
    if node.animmenu == "Material":
        return(node.filebase+"-"+str(fr)+".rad")
    else:
        return(node.filebase+"-0.rad")

def sky(fr, node, geonode):
    if node.animmenu == "Time":
        return(geonode.filebase+"-"+str(fr)+".sky")
    else:
        return(geonode.filebase+"-0.sky")

def nodeinit(node):
    if str(sys.platform) != 'win32':
        node.nproc = str(multiprocessing.cpu_count())
        node.rm = "rm "
        node.cat = "cat "
        node.fold = "/"
        node.cp = "cp "
    else:
        node.nproc = "1"
        node.rm = "del "
        node.cat = "type "
        node.fold = "\\"
        node.cp = "copy "
    node.filepath = bpy.data.filepath
    node.filename = os.path.splitext(os.path.basename(node.filepath))[0]
    node.filedir = os.path.dirname(node.filepath)
    if not os.path.isdir(node.filedir+node.fold+node.filename):
        os.makedirs(node.filedir+node.fold+node.filename)
    if not os.path.isdir(node.filedir+node.fold+node.filename+node.fold+'obj'):
       os.makedirs(node.filedir+node.fold+node.filename+node.fold+'obj')
    node.newdir = node.filedir+node.fold+node.filename
    node.filebase = node.newdir+node.fold+node.filename
    node.objfilebase = node.newdir+node.fold+'obj'+node.fold+node.filename
    node.idf_file = node.newdir+node.fold+"in.idf"

def nodeexported(self):
    self.exported = 0

#Compute solar position (altitude and azimuth in degrees) based on day of year (doy; integer), local solar time (lst; decimal hours), latitude (lat; decimal degrees), and longitude (lon; decimal degrees).
def solarPosition(doy, lst, lat, lon):
    #Set the local standard time meridian (lsm) (integer degrees of arc)
    lsm = int(lon/15)*15
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
    azimuth = radToDeg*phi if ast<=12 else 360 - radToDeg*phi
    return([altitude, azimuth])

def negneg(x):
    if float(x) < 0:
        x = 0
    return float(x)

def clearscenee(scene):
    for sunob in [ob for ob in scene.objects if ob.type == 'LAMP' and ob.data.type == 'SUN']:
        scene.objects.unlink(sunob)

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
    
def socklink(sock):
    try:
        if sock.is_linked and sock.draw_color(bpy.context, sock.node) != (sock.links[0].from_socket, sock.links[0].to_socket)[sock.in_out == 'Out'].draw_color(bpy.context, sock.node):
            bpy.data.node_groups['EnVi Network'].links.remove(sock.links[0])
    except:
        pass
