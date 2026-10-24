# Copy to render_config.py and edit paths. These variables are supplied by Overviewer.
def manual_marker(poi):
    """Return a safe popup for a manually configured place."""
    from html import escape
    if poi.get('id') == 'manual':
        name = escape(str(poi.get('name', 'Место')))
        description = escape(str(poi.get('description', '')))
        return (name, '<b>' + name + '</b><br>' + description)


worlds['CublayCraft'] = '/srv/minecraft/world-snapshot'
outputdir = '/srv/www/minecraft-map'
texturepath = '/srv/minecraft/assets/1.21.5.jar'
webprogress = True

renders['overworld'] = {
    'world': 'CublayCraft', 'dimension': 'overworld', 'title': 'Обычный мир',
    'rendermode': [Base(), EdgeLines(), SmoothLighting(strength=1)],
    'defaultzoom': 4,
    'poititle': 'Места',
    'markers': [{'name': 'Мои места', 'filterFunction': manual_marker,
                 'icon': 'markers/marker_home.png', 'checked': True}],
    # Add your places here; see CONFIG_RU.md for complete examples.
    'manualpois': [],
}
renders['nether'] = {
    'world': 'CublayCraft', 'dimension': 'nether', 'title': 'Нижний мир — срез Y=47',
    'rendermode': [Base(), EdgeLines(), Nether(), SmoothLighting(strength=0.5), Depth(max=47)],
    'defaultzoom': 4,
}
renders['end'] = {
    'world': 'CublayCraft', 'dimension': 'end', 'title': 'Край',
    'rendermode': [Base(), EdgeLines(), SmoothLighting(strength=0.5)],
    'defaultzoom': 4,
}
# For separate Bukkit/Paper worlds, add aliases to worlds and change 'world' above:
# worlds['CublayCraft-Nether'] = '/srv/minecraft/world_nether'
# worlds['CublayCraft-End'] = '/srv/minecraft/world_the_end'
# To reproduce the old Overworld height cut, append Depth(max=254) to its rendermode.
# Boundaries in blocks: renders['overworld']['crop'] = (-5000, -5000, 5000, 5000)
# After changing manualpois, run:
# python overviewer.py --genpoi -c render_config.py --skip-scan --skip-players -p 1
