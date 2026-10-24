"""Tiny synthetic Anvil world for exercising the real Python/C render pipeline."""
import gzip
import json
from pathlib import Path
import struct
import time
import zipfile
import zlib


def string(value):
    value = value.encode('utf-8')
    return struct.pack('>H', len(value)) + value


def payload(kind, value):
    if kind == 1:
        return struct.pack('>b', value)
    if kind == 3:
        return struct.pack('>i', value)
    if kind == 4:
        return struct.pack('>q', value)
    if kind == 7:
        return struct.pack('>i', len(value)) + value
    if kind == 8:
        return string(value)
    if kind == 9:
        subtype, values = value
        return bytes([subtype]) + struct.pack('>i', len(values)) + b''.join(payload(subtype,v) for v in values)
    if kind == 10:
        return b''.join(bytes([t]) + string(k) + payload(t,v) for k,(t,v) in value.items()) + b'\0'
    if kind == 12:
        return struct.pack('>i',len(value)) + b''.join(struct.pack('>Q',v) for v in value)
    raise ValueError(kind)


def compound(value):
    return b'\x0a\0\0' + payload(10, value)


def make_world(root, jar_path, region=(0,0)):
    root = Path(root)
    (root / 'region').mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(jar_path) as jar:
        version = json.loads(jar.read('version.json'))
    modern = version['world_version'] >= 5023
    names = [('stone',{}), ('pale_oak_planks',{}), ('wildflowers',{'facing':'north','flower_amount':'4'}),
             ('leaf_litter',{'facing':'south','segment_amount':'3'}), ('bush',{}),
             ('firefly_bush',{}), ('cactus_flower',{})]
    if modern:
        names += [('poplar_planks',{}), ('red_poplar_leaves',{}), ('orange_poplar_leaves',{}),
                  ('yellow_poplar_leaves',{}), ('poplar_log',{'axis':'x'}),
                  ('white_wool_stairs',{'facing':'east','half':'bottom','shape':'inner_left'}),
                  ('blue_concrete_slab',{'type':'top'}), ('shelf_mushroom',{'age':'1','facing':'south'}),
                  ('straw_bed',{'facing':'north','part':'head'}),
                  ('copper_golem_statue',{'facing':'south','copper_golem_pose':'sitting'}),
                  ('poplar_hanging_sign',{'attached':'false','rotation':'3'})]
    palette = [{'Name':(8,'minecraft:air')}]
    for name, properties in names:
        entry = {'Name':(8,'minecraft:'+name)}
        if properties:
            entry['Properties'] = (10, {k:(8,v) for k,v in properties.items()})
        palette.append(entry)
    if modern:
        # 26.3 uses lowercase fields and compact default states. Mixed NBT
        # lists wrap scalar entries in a compound under the empty key.
        palette = [({'id': entry['Name'], 'properties': entry['Properties']}
                    if 'Properties' in entry else {'': entry['Name']})
                   for entry in palette]
    bits = max(4, (len(palette)-1).bit_length())
    per_long = 64 // bits
    values = [0] * 4096
    values[:256] = [1]*256
    for i in range(1,len(palette)):
        x,z = 2+(i%6)*2, 2+(i//6)*3
        values[256+z*16+x] = i
    packed = [sum(v << (bits*i) for i,v in enumerate(values[j:j+per_long]))
              for j in range(0,4096,per_long)]
    sections = [(10,dict(Y=(1,4), SkyLight=(7,b'\xff'*2048), BlockLight=(7,b'\0'*2048),
                        biomes=(10,{'palette':(9,(8,['minecraft:dappled_forest' if modern else 'minecraft:plains']))}),
                        block_states=(10,{'palette':(9,(10,palette)), 'data':(12,packed)})))]
    locations, times = bytearray(4096), bytearray(4096)
    chunks = []
    offset = 2
    for x in range(3):
        for z in range(3):
            raw = compound(dict(DataVersion=(3,version['world_version']), xPos=(3,x+32*region[0]), zPos=(3,z+32*region[1]),
                                Status=(8,'minecraft:full'), sections=(9,(10,[v for _,v in sections]))))
            compressed = zlib.compress(raw)
            record = struct.pack('>I',len(compressed)+1) + b'\x02' + compressed
            sectors = (len(record)+4095)//4096
            index = 4*(x+z*32)
            locations[index:index+4] = (offset*256+sectors).to_bytes(4,'big')
            times[index:index+4] = int(time.time()-86400).to_bytes(4,'big')
            chunks.append(record.ljust(sectors*4096,b'\0'))
            offset += sectors
    (root/'region'/('r.%d.%d.mca' % region)).write_bytes(locations+times+b''.join(chunks))
    data = dict(version=(3,19133), DataVersion=(3,version['world_version']),
                LevelName=(8,'Modern renderer fixture'), SpawnX=(3,0), SpawnY=(3,64), SpawnZ=(3,0))
    if modern:
        data['spawn'] = (10,{'dimension':(8,'minecraft:overworld'),'pos':(9,(3,[0,64,0]))})
    (root/'level.dat').write_bytes(gzip.compress(compound({'Data':(10,data)})))
    return version
