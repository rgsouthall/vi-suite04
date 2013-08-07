import bpy, os, math
from math import sin, cos, asin, acos, pi

def obj(name, fr, node):
    if node.animmenu == "Geometry":
        return(node.filebase+"-{}-{}.obj".format(name.replace(" ", "_"), fr))
    else:
        return(node.filebase+"-{}-0.obj".format(name.replace(" ", "_")))

def mesh(name, fr, node):
    if node.animmenu in ("Geometry", "Material"):
        return(node.filebase+"-{}-{}.mesh".format(name.replace(" ", "_"), fr))
    else:
        return(node.filebase+"-{}-0.mesh".format(name.replace(" ", "_")))

def mat(fr, node):
    if node.animmenu == "Material":
        return(node.filebase+"-"+str(fr)+".mat")
    else:
        return(node.filebase+"-0.mat")

def sky(fr, node):
    if node.animmenu == "Time":
        return(node.filebase+"-"+str(fr)+".sky")
    else:
        return(node.filebase+"-0.sky")
        
def nodeinit(node):
    node.filepath = bpy.data.filepath
    node.filename = os.path.splitext(os.path.basename(node.filepath))[0]
    node.filedir = os.path.dirname(node.filepath)
    if not os.path.isdir(node.filedir+node.fold+node.filename):
        os.makedirs(node.filedir+node.fold+node.filename)        
    node.newdir = node.filedir+node.fold+node.filename
    node.filebase = node.newdir+node.fold+node.filename

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