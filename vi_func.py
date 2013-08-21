import bpy, os, sys, multiprocessing
from math import sin, cos, asin, acos, pi
from bpy.props import IntProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty

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
    ctypes, ztypes, zrtypes = [], [], []
    resfile = open(node.resfilename, 'r')

    envdict = {'Site Outdoor Air Drybulb Temperature [C] !Hourly': "Outdoor Temperature ("+ u'\u00b0'+"C)",
               'Site Outdoor Air Relative Humidity [%] !Hourly': 'Outdoor Humidity (%)',
                'Site Wind Direction [deg] !Hourly': 'Wind Direction (deg)',
                'Site Wind Speed [m/s] !Hourly': 'Wind Speed (m/s)',
                'Site Diffuse Solar Radiation Rate per Area [W/m2] !Hourly': "Diffuse Solar (W/m"+u'\u00b2'+")",
                'Site Direct Solar Radiation Rate per Area [W/m2] !Hourly': "Direct Solar (W/m"+u'\u00b2'+")"}
    zresdict = {'Zone Air Temperature [C] !Hourly': "Zone Temperature ("+ u'\u00b0'+"C)",
                'Zone Air System Sensible Heating Rate [W] !Hourly': 'Zone heating (W)',
                'Zone Air System Sensible Cooling Rate [W] !Hourly': 'Zone cooling (W)',
                'Zone Windows Total Transmitted Solar Radiation Rate [W] !Hourly': 'Solar gain (W)'}
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
                node['rtypes'] += ['Climate']
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

    resfile.close()
    node['dos'] = dos
    node['resdict'] = resdict
    node['ctypes'] = ctypes
    node['ztypes'] = ztypes
    node['zrtypes'] = zrtypes
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
        node = [node for node in bpy.data.node_groups['EnVi Network'].nodes if node.zone == obj.name][0]
        if node.inputs[mat.name].is_linked == True:
            for bpoly in bpy.data.objects[node.inputs[mat.name].links[0].from_node.zone].data.polygons:
                if bpy.data.objects[node.inputs[mat.name].links[0].from_node.zone].data.materials[bpoly.material_index] == mat and bpoly.center[:] == poly.center[:] and bpoly.area == poly.area:
                    return(("Surface", node.inputs[mat.name].links[0].from_node.zone+str(bpoly.index), "NoSun", "NoWind"))

        elif node.outputs[mat.name].is_linked == True:
            for bpoly in bpy.data.objects[node.outputs[mat.name].links[0].to_node.zone].data.polygons:
                if bpy.data.objects[node.outputs[mat.name].links[0].to_node.zone].data.materials[bpoly.material_index] == mat and bpoly.center[:] == poly.center[:] and bpoly.area == poly.area:
                    return(("Surface", node.outputs[mat.name].links[0].to_node.zone+str(bpoly.index), "NoSun", "NoWind"))
        else:
            return(("Outdoors", "", "SunExposed", "WindExposed"))
    else:
        return(("Outdoors", "", "SunExposed", "WindExposed"))
