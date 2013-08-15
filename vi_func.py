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
                
def processf(node, file):
    dos = [[], [], [], [], []]
    at = [[], []]
    ah = [[], []]
    aws = [[], []]
    awd = [[], []]
    asd = [[], []]
    asb = [[], []]
    resfile = open(file, 'r')
    xtypes = []
    climlist = []
#    objno = len([obj for obj in bpy.data.objects if obj.layers[1] == True])

    for line in resfile:
        if len(line.split(",")) > 2 and line.split(",")[2] == "Day of Simulation[]":
            dos[0] = line.split(",")[0]
            xtypes.append("Time")
        elif len(line.split(",")) > 2 and line.split(",")[2] == "Environment":
            if line.split(",")[3].strip('\n') == "Site Outdoor Air Drybulb Temperature [C] !Hourly":
                climlist.append('Ambient Temperature (C)')
                at[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Outdoor Air Relative Humidity [%] !Hourly":
                climlist.append('Ambient Humidity (%)')
                ah[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Wind Speed [m/s] !Hourly":
                climlist.append('Ambient Wind Speed (m/s)')
                aws[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Wind Direction [deg] !Hourly":
                climlist.append('Ambient Wind Direction (deg from N)')
                awd[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Diffuse Solar Radiation Rate per Area [W/m2] !Hourly":
                climlist.append('Diffuse Solar Radiation (W/m^2)')
                asd[0] = line.split(",")[0]
            if line.split(",")[3].strip('\n') == "Site Direct Solar Radiation Rate per Area [W/m2] !Hourly":
                climlist.append('Direct Solar Radiation (W/m^2)')
                asb[0] = line.split(",")[0]
            xtypes.append("Climate")
            node['climlist'] = climlist
        elif len(line.split(",")) > 2 and line.split(",")[2] in [obj.name.upper() for obj in bpy.data.objects if obj.layers[1] == True]:
            for obj in bpy.data.objects:
                if obj.layers[1] == True and obj.name.upper() == line.split(",")[2]:
                    if (obj.name, obj.name, 'Zone name') not in zonelist:
                        zonelist.append(obj.name)
                    if line.split(",")[3].split("!")[0] == "Zone Infiltration Current Density Volume Flow Rate [m3/s] ":
                        zoneres.append([line.split(",")[0], obj.name, "Zone Infiltration [m3/s] "])
                    elif line.split(",")[3].split("!")[0] == "Zone Windows Total Transmitted Solar Radiation Rate [W] ":
                        zoneres.append([line.split(",")[0], obj.name, "Total Solar Gain [W] "])
                    else:
                        zoneres.append([line.split(",")[0], obj.name, line.split(",")[3].split("!")[0]])
                    zoneresno.append(line.split(",")[0])
                    if line.split(",")[3].split("!")[0] not in [zr[1] for zr in zonereslist]:
                        if line.split(",")[3].split("!")[0] == "Zone Infiltration Current Density Volume Flow Rate [m3/s] ":
                            zonereslist.append(("Zone Infiltration [m3/s] ", line.split(",")[3].split("!")[0], 'Results Parameter'))
                        elif line.split(",")[3].split("!")[0] == "Zone Windows Total Transmitted Solar Radiation Rate [W] ":
                            zonereslist.append(("Total Solar Gain [W] ", line.split(",")[3].split("!")[0], 'Results Parameter'))
                        else:
                            zonereslist.append((line.split(",")[3].split("!")[0], line.split(",")[3].split("!")[0], 'Results Parameter'))
            if ("Zone", "Zone", "Plot a zone result on the x-axis") not in node['xtypes']:
                xtypes.append("Zone")     
#            er.zonereslist = zonereslist
            
        elif line.split(",")[0] in zoneresno:
            zoneres[[i for i,x in enumerate(zoneresno) if x == line.split(",")[0]][0]].append(float(line.split(",")[1].strip("\n")))
            
        elif line.split(",")[0] == dos[0]:
            dos[1].append(int(line.split(",")[1]))
            dos[2].append(int(line.split(",")[2]))
            dos[3].append(int(line.split(",")[3]))
            dos[4].append(int(line.split(",")[5]))
        
        elif line.split(",")[0] == at[0]: 
            at[1].append(float(line.split(",")[1].strip('\n')))
        
        elif line.split(",")[0] == ah[0]: 
            ah[1].append(float(line.split(",")[1].strip('\n')))
        
        elif line.split(",")[0] == aws[0]: 
            aws[1].append(float(line.split(",")[1].strip('\n')))    
        
        elif line.split(",")[0] == awd[0]: 
            awd[1].append(float(line.split(",")[1].strip('\n')))   
        
        elif line.split(",")[0] == asb[0]: 
            asb[1].append(float(line.split(",")[1].strip('\n'))) 
        
        elif line.split(",")[0] == asd[0]: 
            asd[1].append(float(line.split(",")[1].strip('\n'))) 
                
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