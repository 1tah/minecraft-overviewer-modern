# Copy to render_config.py and edit paths. These variables are supplied by Overviewer.
worlds['CublayCraft'] = '/srv/minecraft/world-snapshot'
outputdir = '/srv/www/minecraft-map'
texturepath = '/srv/minecraft/assets/1.21.5.jar'
webprogress = True

renders['overworld'] = {
    'world': 'CublayCraft', 'dimension': 'overworld', 'title': 'Обычный мир',
    'rendermode': [Base(), EdgeLines(), SmoothLighting(strength=1)],
    'defaultzoom': 4,
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
