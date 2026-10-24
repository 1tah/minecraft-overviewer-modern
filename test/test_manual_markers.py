from overviewer_core.aux_files.genPOI import handleManual


def test_manual_places_are_not_duplicated_for_region_sets_or_crops():
    def select(poi):
        return poi['name']
    filters = [('places', 'Places', select, region, '/world', 'overworld')
               for region in ('terrain', 'entities', 'crop2')]
    filters.append(('portals', 'Portals', select, 'terrain', '/world', 'overworld'))
    markers = {'places': {'raw': []}, 'portals': {'raw': []}}
    handleManual([dict(id='manual', x=120, y=72, z=-340, name='Spawn')], filters, markers)
    assert len(markers['places']['raw']) == 1
    assert len(markers['portals']['raw']) == 1
    assert markers['places']['raw'][0]['text'] == 'Spawn'
