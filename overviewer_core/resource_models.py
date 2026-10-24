"""Render previously unknown blocks from the client JAR's blockstate/model JSON.

Native Overviewer materials retain their existing renderer. This adapter handles
vanilla cuboid models, parents, texture references, multipart conditions and
block/element rotations. Weighted variants use a deterministic first choice.
The copper statue uses approximate cuboids; other special entity renderers and
future model schemas fail explicitly.
"""
import itertools
import json
import logging
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

FIRST_ID, LAST_ID = 14000, 15000
MISSING_ID = 13999


def location(name, folder, suffix='.json'):
    namespace, path = name.split(':', 1) if ':' in name else ('minecraft', name)
    if namespace not in ('minecraft',) or '..' in Path(path).parts:
        raise ValueError('Unsupported resource location: ' + name)
    return 'assets/%s/%s/%s%s' % (namespace, folder, path, suffix)


def matches(condition, properties):
    if 'OR' in condition:
        return any(matches(c, properties) for c in condition['OR'])
    if 'AND' in condition:
        return all(matches(c, properties) for c in condition['AND'])
    return all(properties.get(k) in str(v).split('|') for k, v in condition.items())


def domains(condition, result):
    for key, value in condition.items():
        if key in ('OR', 'AND'):
            for part in value:
                domains(part, result)
        else:
            result.setdefault(key, set()).update(str(value).split('|'))


def rotate(points, axis, degrees, origin=(8, 8, 8), rescale=False):
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    i = 'xyz'.index(axis)
    a, b = (i + 1) % 3, (i + 2) % 3
    matrix = np.eye(3)
    matrix[a, a] = matrix[b, b] = cosine
    matrix[a, b], matrix[b, a] = -sine, sine
    points = (points - origin) @ matrix.T
    if rescale:
        points[:, [a, b]] /= abs(cosine)
    return points + origin


class ModelRegistry:
    def __init__(self, textures, native_names):
        self.entries = {}
        self.properties = {}
        self.models = {}
        self.states = {}
        files = set()
        if textures.find_file_local_path and Path(textures.find_file_local_path).is_dir():
            root = Path(textures.find_file_local_path)
            files.update(p.relative_to(root).as_posix() for p in root.glob('assets/minecraft/blockstates/*.json'))
        for jar in textures.jars.values():
            files.update(n for n in jar.namelist() if n.startswith('assets/minecraft/blockstates/') and n.endswith('.json'))
        next_id = FIRST_ID
        self.available_names = {'minecraft:' + Path(filename).stem for filename in files}
        for filename in sorted(files):
            name = 'minecraft:' + Path(filename).stem
            if name in native_names:
                continue
            with textures.find_file(filename) as stream:
                definition = json.load(stream)
            props = {}
            for variant in definition.get('variants', {}):
                if variant:
                    domains(dict(part.split('=', 1) for part in variant.split(',')), props)
            for part in definition.get('multipart', []):
                domains(part.get('when', {}), props)
            if name.endswith('copper_golem_statue'):
                props.update(facing={'north','east','south','west'}, copper_golem_pose={'standing','sitting','running','star'})
            keys = sorted(props)
            combinations = math.prod(len(props[k]) for k in keys)
            if combinations > 4096:
                raise ValueError('Too many model states for ' + name)
            self.properties[name] = keys
            self.states[name] = definition
            for index, values in enumerate(itertools.product(*(sorted(props[k]) for k in keys))):
                blockid, data = next_id + index // 256, index % 256
                if blockid >= LAST_ID:
                    raise ValueError('Resource model ID capacity exhausted')
                self.entries[(name, values)] = (blockid, data)
            next_id += max(1, (combinations + 255) // 256)
        logging.info('Resource models: %d additional blocks, %d states.', len(self.states), len(self.entries))

    def translate(self, palette):
        name = palette['Name']
        keys = self.properties[name]
        props = palette.get('Properties', {})
        return self.entries[(name, tuple(props[k] for k in keys))]

    def model(self, name, textures, stack=()):
        if name in self.models:
            return self.models[name]
        if name in stack or len(stack) >= 32:
            raise ValueError('Cyclic/deep model parent: ' + name)
        if name.startswith(('builtin/', 'minecraft:builtin/')):
            raise ValueError('Special model renderer required: ' + name)
        with textures.find_file(location(name, 'models')) as stream:
            child = json.load(stream)
        parent = self.model(child['parent'], textures, stack + (name,)) if 'parent' in child else {}
        model = {**parent, **child}
        model['textures'] = {**parent.get('textures', {}), **child.get('textures', {})}
        self.models[name] = model
        return model

    def applications(self, name, props):
        definition = self.states[name]
        for variant, application in definition.get('variants', {}).items():
            condition = dict(part.split('=', 1) for part in variant.split(',')) if variant else {}
            if matches(condition, props):
                yield application[0] if isinstance(application, list) else application
                break
        for part in definition.get('multipart', []):
            if matches(part.get('when', {}), props):
                application = part['apply']
                yield application[0] if isinstance(application, list) else application

    def sprites(self, textures):
        for (name, values), identity in self.entries.items():
            props = dict(zip(self.properties[name], values))
            yield identity, self.render(name, props, textures)

    def render(self, name, props, textures):
        faces = []
        for application in self.applications(name, props):
            model = self.model(application['model'], textures)
            if name.endswith('copper_golem_statue'):
                model = statue_model(model, props)
                application = {**application, 'y': {'north':0,'east':90,'south':180,'west':270}[props['facing']]}
            if 'elements' not in model:
                raise ValueError('No cuboid geometry for ' + name)
            for element in model['elements']:
                x0, y0, z0 = element['from']
                x1, y1, z1 = element['to']
                # Vertices in texture order: upper left, upper right, lower right, lower left.
                geometry = {
                    'up': [(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],
                    'down': [(x0,y0,z1),(x1,y0,z1),(x1,y0,z0),(x0,y0,z0)],
                    'north': [(x1,y1,z0),(x0,y1,z0),(x0,y0,z0),(x1,y0,z0)],
                    'south': [(x0,y1,z1),(x1,y1,z1),(x1,y0,z1),(x0,y0,z1)],
                    'west': [(x0,y1,z0),(x0,y1,z1),(x0,y0,z1),(x0,y0,z0)],
                    'east': [(x1,y1,z1),(x1,y1,z0),(x1,y0,z0),(x1,y0,z1)],
                }
                default_uv = {
                    'up': [x0,z0,x1,z1], 'down': [x0,16-z1,x1,16-z0],
                    'north': [16-x1,16-y1,16-x0,16-y0], 'south': [x0,16-y1,x1,16-y0],
                    'west': [z0,16-y1,z1,16-y0], 'east': [16-z1,16-y1,16-z0,16-y0],
                }
                for direction, face in element.get('faces', {}).items():
                    points = np.array(geometry[direction], dtype=float)
                    if 'rotation' in element:
                        rot = element['rotation']
                        if 'axis' in rot:
                            points = rotate(points, rot['axis'], rot['angle'], rot.get('origin', [8,8,8]), rot.get('rescale', False))
                        else:
                            for axis in 'xyz':
                                points = rotate(points, axis, rot.get(axis, 0), rot.get('origin', [8,8,8]))
                    points = rotate(points, 'x', -application.get('x', 0))
                    points = rotate(points, 'y', -application.get('y', 0) - 90 * textures.rotation)
                    # Front faces have normals towards west, south or up.
                    normal = np.cross(points[1]-points[0], points[3]-points[0])
                    if np.dot(normal, [1,-1,-1]) <= 1e-8:
                        continue
                    texture = face['texture']
                    seen = set()
                    while texture.startswith('#'):
                        if texture in seen:
                            raise ValueError('Cyclic texture reference in ' + name)
                        seen.add(texture)
                        texture = model['textures'][texture[1:]]
                    image = textures.load_image_texture(location(texture, 'textures', '.png')).copy()
                    uv = face.get('uv', default_uv[direction])
                    u0,v0,u1,v1 = uv
                    image = image.crop((min(u0,u1),min(v0,v1),max(u0,u1),max(v0,v1)))
                    if not image.width or not image.height:
                        continue
                    if u1 < u0:
                        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    if v1 < v0:
                        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    image = image.rotate(-face.get('rotation', 0), expand=True)
                    # UV-lock on top/bottom faces compensates for block Y rotation.
                    if application.get('uvlock') and direction in ('up', 'down'):
                        image = image.rotate(application.get('y', 0), expand=True)
                    norm = -normal / np.linalg.norm(normal)
                    shade = 1.0 if not model.get('shade', True) or not element.get('shade', True) else 0.6 + 0.4*max(0,norm[1]) + 0.2*max(0,norm[2])
                    if 'shade_direction_override' in element:
                        shade = {'up':1.0,'down':0.5,'north':0.6,'south':0.8,'east':0.6,'west':0.8}[element['shade_direction_override']]
                    if 'tintindex' in face:
                        image = textures.tint_texture(image, (120, 165, 75))
                    image = ImageEnhance.Brightness(image).enhance(shade)
                    projected = np.column_stack(((points[:,0]+points[:,2])*0.75,
                                                   18+(points[:,2]-points[:,0])*0.375-points[:,1]*0.75))
                    depth = np.mean(-points[:,0]+points[:,1]+points[:,2])
                    faces.append((depth, projected, image))
        canvas = Image.new('RGBA', (96,96))
        for _, points, image in sorted(faces, key=lambda item: item[0]):
            points = points * 4
            # Affine inverse maps each parallelogram face onto its cropped UV image.
            matrix = np.column_stack((points[1]-points[0], points[3]-points[0]))
            if abs(np.linalg.det(matrix)) < 1e-8:
                continue
            inverse = np.diag([image.width, image.height]) @ np.linalg.inv(matrix)
            offset = -inverse @ points[0]
            coefficients = (inverse[0,0],inverse[0,1],offset[0],inverse[1,0],inverse[1,1],offset[1])
            layer = image.transform(canvas.size, Image.Transform.AFFINE, coefficients, Image.Resampling.NEAREST)
            canvas.alpha_composite(layer)
        return canvas.resize((24,24), Image.Resampling.LANCZOS)


def statue_model(model, props):
    """Small cuboid approximation for the entity-rendered statue.

    Overviewer has no entity-model/animation renderer. Preserve pose, facing and
    oxidation, using the supplied particle texture, instead of an invisible block.
    """
    def cube(low, high, rotation=None):
        element = dict(from_=low, to=high, faces={d: {'texture':'#particle','uv':[0,0,16,16]}
                                               for d in ('up','down','north','south','west','east')})
        element['from'] = element.pop('from_')
        if rotation:
            element['rotation'] = rotation
        return element
    pose = props['copper_golem_pose']
    crouch = 3 if pose == 'sitting' else 0
    elements = [cube([5,4-crouch,5],[11,10-crouch,11]),
                cube([4,10-crouch,4],[12,16-crouch,12]),
                cube([7,16-crouch,7],[9,18-crouch,9])]
    for side, x in ((-1,2),(1,11)):
        arm_angle = side * 90 if pose == 'star' else 0
        elements.append(cube([x,4-crouch,6],[x+3,10-crouch,10],
                             dict(axis='z',angle=arm_angle,origin=[x+1.5,10-crouch,8])))
    for side, x in ((-1,5),(1,8)):
        angle = -75 if pose == 'sitting' else (side*40 if pose == 'running' else 0)
        elements.append(cube([x,0,6],[x+3,4,10],dict(axis='x',angle=angle,origin=[x+1.5,4,8])))
    return {**model, 'elements': elements}
