import bpy, mathutils, math
from . import vi_func
from .livi_export import radgexport

try:
    import numpy
    np = 1
except:
    np = 0

def vigen(calc_op, li_calc, resapply, geonode, connode, simnode, geogennode, tarnode):
    scene = bpy.context.scene
    scene.frame_set(scene.frame_start)
    simnode['Animation'] = 'Animated'
    
    for geo in vi_func.retobjs('livig'):
        if any([m.livi_sense for m in geo.data.materials]):
            vi_func.selobj(scene, geo)
            bpy.ops.anim.keyframe_clear_v3d()
            geo['licalc'] = 1
                    
    for geo in vi_func.retobjs('livic'):  
        vi_func.selobj(scene, geo)
        geo.data.animation_data_clear()
        while geo.data.vertex_colors:
            bpy.ops.mesh.vertex_color_remove()        
        while geo.data.shape_keys:
            bpy.context.object.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove(all=True)
        bpy.ops.object.mode_set(mode = 'EDIT')
        if geo.vertex_groups.get('genfaces'):            
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.mesh.select_all(action='DESELECT')
        else:
            geo.vertex_groups.new('genfaces')
            geo.vertex_groups.active = geo.vertex_groups['genfaces']
            if geogennode.selmenu == 'Not Selected':
                bpy.ops.mesh.select_all(action='INVERT')    
            elif geogennode.selmenu == 'All':
                bpy.ops.mesh.select_all(action='SELECT') 
            bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode = 'OBJECT')
        geo['vgi'] = geo.vertex_groups['genfaces'].index
                    
    radgexport(calc_op, geonode, genframe = scene.frame_current)
    res = [li_calc(calc_op, simnode, connode, geonode, vi_func.livisimacc(simnode, connode), genframe = scene.frame_current)]

    for geo in vi_func.retobjs('livic'):        
        geo['licalc'] = vi_func.gentarget(tarnode, geo['oreslist']['{}'.format(scene.frame_current)]) 
        livicgeos = vi_func.retobjs('livic')
        if geo.get('licalc') == 1:
            vi_func.selobj(scene, geo)
            bpy.ops.object.shape_key_add(from_mix = False)
            geo.keyframe_insert(data_path='["licalc"]')
            geo.keyframe_insert(data_path='["licalc"]', frame = scene.frame_current + 1)
            
    while scene.frame_current < scene.frame_start + geogennode.steps + 1 and vi_func.retobjs('livic'):
        if scene.frame_current == scene.frame_start + 1:            
            for geo in vi_func.retobjs('livic'):
                if geogennode.mmanmenu == '3':               
                    for face in geo.data.polygons:
                        face.select = True if all([geo.data.vertices[v].groups for v in face.vertices]) else False
     
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.extrude_faces_move(MESH_OT_extrude_faces_indiv={"mirror":False}, TRANSFORM_OT_shrink_fatten={"value":0})
                    if geo.vertex_groups.get('genexfaces'):
                        bpy.context.object.vertex_groups.active_index  = 1
                        bpy.ops.object.vertex_group_remove()
                    geo.vertex_groups.new('genexfaces')
                    bpy.context.object.vertex_groups.active_index  = 1
                    bpy.ops.object.vertex_group_assign()
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                    geo['vgi'] = geo.vertex_groups['genexfaces'].index
                    
        
        if scene.frame_current > scene.frame_start:              
            for geo in vi_func.retobjs('livic'):
                geo.keyframe_insert(data_path='["licalc"]')
                vi_func.selobj(scene, geo)        
                bpy.ops.object.shape_key_add(from_mix = False)
                geo.active_shape_key.name = 'gen-' + str(scene.frame_current)
                modgeo(geo, geogennode, scene, scene.frame_current, scene.frame_start)   
        
                for shape in geo.data.shape_keys.key_blocks:
                    if "Basis" not in shape.name:
                        shape.value = 1 if shape.name == 'gen-{}'.format(scene.frame_current) else 0
                        shape.keyframe_insert("value")
    
            radgexport(calc_op, geonode, genframe = scene.frame_current)
            res.append(li_calc(calc_op, simnode, connode, geonode, vi_func.livisimacc(simnode, connode), genframe = scene.frame_current))
            
            for geo in vi_func.retobjs('livic'):
                geo['licalc'] = vi_func.gentarget(tarnode, geo['oreslist']['{}'.format(scene.frame_current)]) 
                geo.keyframe_insert(data_path='["licalc"]', frame = scene.frame_current + 1)
                                
        scene.frame_set(scene.frame_current + 1)
        scene.frame_end = scene.frame_current
    
    scene.frame_end = scene.frame_end - 1       
    resapply(calc_op, res, 0, simnode, connode, geonode)
        
    for frame in vi_func.framerange(scene, 'Animation'):
        scene.frame_set(frame)
        for geo in livicgeos:
            for shape in geo.data.shape_keys.key_blocks:
                if "Basis" not in shape.name:
                    shape.value = 1 if shape.name == 'gen-{}'.format(frame) else 0
                    if shape == geo.data.shape_keys.key_blocks[-1] and frame > int(shape.name.split('-')[1]):
                        shape.value = 1
                    shape.keyframe_insert("value")
                    
    vi_func.vcframe('', scene, livicgeos, simnode['Animation'])            
    scene.frame_current = scene.frame_start       
        
def modgeo(geo, geogennode, scene, fc, fs):
#    fc, fs = scene.frame_current, scene.frame_start
#    if not geo.vertex_groups.get('genfaces'):        
            
    if geogennode.geomenu == 'Object':
        pass        
    else: 
        print(geo['vgi'])

                
        
        for face in geo.data.polygons:
            try:
                if all([geo.data.vertices[v].groups[geo['vgi']] for v in face.vertices]):
                    direc = tuple(face.normal.normalized()) if geogennode.normal else (geogennode.x, geogennode.y, geogennode.z)
                    fcent = tuple(face.center)
                    for v in face.vertices:
                        if geogennode.mmanmenu in ('0', '3'):
                            geo.data.shape_keys.key_blocks['gen-{}'.format(fc)].data[v].co = geo.data.shape_keys.key_blocks['Basis'].data[v].co + mathutils.Vector([(-1, 1)[geogennode.direction == '0'] * (fc-fs) * (geogennode.extent/geogennode.steps) * d for d in direc])
                        elif geogennode.mmanmenu == '1':
                            mat_rot = mathutils.Matrix.Rotation(math.radians((fc-fs) * geogennode.extent/geogennode.steps), 4, face.normal)  if geogennode.normal else mathutils.Matrix.Rotation(math.radians((fc-fs) * geogennode.extent/geogennode.steps), 4, mathutils.Vector((geogennode.x, geogennode.y, geogennode.z)))
                            geo.data.shape_keys.key_blocks['gen-{}'.format(fc)].data[v].co = (mat_rot * (geo.data.shape_keys.key_blocks['Basis'].data[v].co - mathutils.Vector(fcent))) + mathutils.Vector(fcent)
                        elif geogennode.mmanmenu == '2':                            
                            mat_scl = mathutils.Matrix.Scale((fc-fs) * geogennode.extent/geogennode.steps, 4, mathutils.Vector([1 - fn for fn in face.normal]))  if geogennode.normal else mathutils.Matrix.Scale((fc-fs) * geogennode.extent/geogennode.steps, 4, mathutils.Vector((geogennode.x, geogennode.y, geogennode.z)))
                            geo.data.shape_keys.key_blocks['gen-{}'.format(fc)].data[v].co = (mat_scl * (geo.data.shape_keys.key_blocks['Basis'].data[v].co - mathutils.Vector(fcent))) + mathutils.Vector(fcent)
            
            except Exception as e:
                pass        
        
        
#        if geogennode.mmanmenu in ('0', '3'):            
#            if geogennode.normal:
#                for face in geo.data.polygons:
#                    try:
#                        if all([geo.data.vertices[v].groups[vgi] for v in face.vertices]):
#                            fn = tuple(face.normal.normalized())
#                            for v in face.vertices:
#                                geo.data.shape_keys.key_blocks['gen-{}'.format(fc)].data[v].co = geo.data.shape_keys.key_blocks['Basis'].data[v].co + mathutils.Vector([(-1, 1)[geogennode.direction == '0'] * (fc-fs) * (geogennode.extent/geogennode.steps) * n for n in fn])
#                    except:
#                        pass                    
#            else:
#                move = [(-1, 1)[geogennode.direction == 'Postive'] * coord*geogennode.extent/geogennode.steps for coord in (geogennode.x, geogennode.y, geogennode.z)]
#                bpy.ops.transform.translate(value=move, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
#        
#        elif geogennode.mmanmenu == '1':
#            if geogennode.normal:
#                bpy.ops.transform.rotate(value=(0, 0, (-1, 1)[geogennode.direction == '0'] * geogennode.extent/geogennode.steps), constraint_axis=(False, False, False), constraint_orientation='NORMAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
#            else:
#                move = [(-1, 1)[geogennode.direction == 'Postive'] * coord*geogennode.extent/geogennode.steps for coord in (geogennode.x, geogennode.y, geogennode.z)]
#                bpy.ops.transform.rotate(value=move, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
#        
#        elif geogennode.mmanmenu == '2':
#            if geogennode.normal:
#                bpy.ops.transform.scale(value=(0, 0, (-1, 1)[geogennode.direction == '0'] * geogennode.extent/geogennode.steps), constraint_axis=(False, False, False), constraint_orientation='NORMAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
#            else:
#                move = [(-1, 1)[geogennode.direction == 'Postive'] * coord*geogennode.extent/geogennode.steps for coord in (geogennode.x, geogennode.y, geogennode.z)]
#                bpy.ops.transform.scale(value=move, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
