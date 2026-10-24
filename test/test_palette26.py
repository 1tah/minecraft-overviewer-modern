import numpy as np
import pytest

from overviewer_core.palette26 import DEFAULTS, normalize
from overviewer_core.world import RegionSet


def test_modern_id_and_properties_override_default_state():
    result = normalize({'id': 'minecraft:oak_stairs', 'properties': {'facing': 'east'}})
    assert result == {'Name': 'minecraft:oak_stairs', 'Properties': {
        'facing': 'east', 'half': 'bottom', 'shape': 'straight', 'waterlogged': 'false'}}
    assert normalize('minecraft:water')['Properties'] == {'level': '0'}
    assert normalize({'': 'minecraft:oak_log'})['Properties']['axis'] == 'y'


def test_old_palette_is_not_reinterpreted():
    old = {'Name': 'minecraft:oak_stairs', 'Properties': {'facing': 'south'}}
    assert normalize(old) is old


def test_default_strings_match_explicit_legacy_properties():
    region = RegionSet('overviewer_core', 'region')
    names = [name for name in DEFAULTS if name in region._blockmap]
    for name in names:
        explicit = {'Name': name, 'Properties': DEFAULTS[name]}
        try:
            expected = region._get_block(explicit)
        except KeyError:
            continue  # Existing unsupported native states are separate from decoding.
        assert region._get_block(name) == expected, name
    assert region._get_block('minecraft:stone') == region._get_block({'Name': 'minecraft:stone'})


def test_string_palette_decodes_a_real_section_without_missing_blocks():
    region = RegionSet('overviewer_core', 'region')
    section = {'block_states': {'palette': ['minecraft:water']}}
    blocks, data = region._get_blockdata_v118(section, set(), region._packed_longarray_to_shorts_v116)
    assert blocks.shape == data.shape == (16,16,16)
    assert np.all(blocks == region._get_block({'Name':'minecraft:water', 'Properties':{'level':'0'}})[0])
