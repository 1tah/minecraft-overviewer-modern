import os
from pathlib import Path
import pickle

import pytest

from overviewer_core.resource_models import FIRST_ID, LAST_ID, ModelRegistry, matches
from overviewer_core.textures import Textures, max_data
from overviewer_core.world import RegionSet


def test_multipart_conditions():
    assert matches({'OR':[{'east':'true'},{'west':'true'}]}, {'east':'false','west':'true'})
    assert matches({'AND':[{'axis':'x|z'},{'powered':'false'}]}, {'axis':'z','powered':'false'})
    assert not matches({'half':'top'}, {'half':'bottom'})


@pytest.mark.parametrize('jar', [p for p in os.environ.get('OVERVIEWER_TEST_JARS','').split(os.pathsep) if p])
def test_official_jar_model_states_and_geometry(jar):
    textures = Textures(texturepath=str(Path(jar).resolve()))
    textures.load_grass_color()
    registry = ModelRegistry(textures, RegionSet('overviewer_core','region')._blockmap)
    restored = pickle.loads(pickle.dumps(registry))
    assert registry.entries
    assert restored.entries == registry.entries
    for (name, values), identity in registry.entries.items():
        props = dict(zip(registry.properties[name], values))
        assert restored.translate({'Name':name,'Properties':props}) == identity
        assert FIRST_ID <= identity[0] < LAST_ID
        assert 0 <= identity[1] < min(256,max_data)
        image = registry.render(name, props, textures)
        assert image.size == (24,24)
        assert image.getbbox(), (name, props)
