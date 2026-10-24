import os
from pathlib import Path
ROOT = Path(os.environ.get('OVERVIEWER_HOME', '.')).resolve()

# -*- coding: utf-8 -*-
# CublayCraft: ваш серверный конфиг для Minecraft Overviewer Modern.
# Сохранены названия слоёв, фильтры, POI, границы, освещение и ракурсы.
# ПЕРЕД ЗАПУСКОМ: проверьте пути worlds, outputdir и texturepath ниже.
# texturepath — клиентский JAR, а не серверный JAR и не архив мира.
# Для 26.3 замените путь на свой клиентский 26.3.jar.
texturepath = str(ROOT / 'assets/client.jar')

# Новый общий веб-статус работает без старого JSObserver.
webprogress = True
# Безопасное значение по умолчанию; -p в командной строке его переопределяет.
processes = 4

# Миры можно положить в worlds/ либо заменить пути ниже своими абсолютными путями.
worlds['CublayCraft-Over'] = str(ROOT / 'worlds/2015')
worlds['CublayCraft-Nether'] = str(ROOT / 'worlds/2015_nether')
worlds['CublayCraft-End'] = str(ROOT / 'worlds/2015_the_end')
worlds['CublayCraft-Builder'] = str(ROOT / 'worlds/plotworld')
#worlds['mine'] = "/home/cube/mine"

# Modern saves keep all dimensions below one world root with level.dat.
for _alias, _dimension in [
    ('CublayCraft-Nether', 'the_nether'), ('CublayCraft-End', 'the_end')
]:
    _main = Path(worlds['CublayCraft-Over'])
    if not (Path(worlds[_alias]) / 'level.dat').is_file() and (_main / 'dimensions/minecraft' / _dimension).is_dir():
        worlds[_alias] = str(_main)

outputdir = str(ROOT / 'output')

#def signFilter(poi):
#    if poi['id'] == 'Sign':
#    return "\n".join([poi['Text1'], poi['Text2'], poi['Text3'], poi['Text4']])

#def chestFilter(poi):
#    if poi['id'] == "Chest":
#    return "Chest with %d items" % len(poi['Items'])

#def playerIcons(poi):
#    if poi['id'] == 'Player':
#        poi['icon'] = "http://overviewer.org/avatar/%s" % poi['EntityId']
#        return "Last known location for %s" % poi['EntityId']

def townFilter(poi):
    if poi['id']=='Города':
       poi['icon']='icons/Города.png'
       try:
           return (poi['name'], poi['description'])
       except KeyError:
           return poi['name'] + '\n'
def baseFilter(poi):
    if poi['id']=='Базы игроков':
       poi['icon']='icons/Базы игроков.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def pixelFilter(poi):
    if poi['id']=='Пиксель арты':
       poi['icon']='icons/Арт.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def tcFilter(poi):
    if poi['id']=='Торговые центры':
       poi['icon']='icons/ТЦ и ТК.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def redFilter(poi):
    if poi['id']=='Красная ветка':
       poi['icon']='icons/База игрока красная.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def yellowFilter(poi):
    if poi['id']=='Желтая ветка':
       poi['icon']='icons/База игрока желтая.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def blueFilter(poi):
    if poi['id']=='Синяя ветка':
       poi['icon']='icons/База игрока синяя.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def greenFilter(poi):
    if poi['id']=='Зеленая ветка':
       poi['icon']='icons/База игрока зеленая.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def endportFilter(poi):
    if poi['id']=='End порталы':
       poi['icon']='icons/Энд портал.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'
def fermsFilter(poi):
    if poi['id']=='Фермы':
       poi['icon']='icons/Фермы.png'
       try:
           return poi['name'] + '<br />' +  poi['description']
       except KeyError:
           return poi['name'] + '\n'

rendermode = "smooth_lighting"
end_smooth_lighting = [Base(), EdgeLines(), SmoothLighting(strength=0.5)]

renders["over"] = {
    'world': 'CublayCraft-Over',
    'title': '\u0414\u0435\u043d\u044c', #День
    #'rendermode': smooth_lighting,
    'rendermode': [Base(), EdgeLines(), SmoothLighting(strength=1), Depth(max=254)],
    'dimension': 'overworld',
    'manualpois':[
        {
            'id':'Города',
            'x':4687,
            'y':64,
            'z':1161,
            'name':'Татарстан'
        },
        {
            'id':'Города',
            'x':3390,
            'y':64,
            'z':1204,
            'name':'Изумрудный город'
        },
                {
            'id':'Города',
            'x':4223,
            'y':64,
            'z':-6521,
            'name':'Город Steam-Punk'
        },
        {
            'id':'Города',
            'x':-7163,
            'y':64,
            'z':-2867,
            'name':'Атлантида'
        },
        {
            'id':'Города',
            'x':3235,
            'y':64,
            'z':3807,
            'name':'Империя'
        },
                        {
            'id':'Торговые центры',
            'x':1075,
            'y':64,
            'z':-4928,
            'name':'Торговый зал "Красная поляна"'
        },
                                        {
            'id':'Торговые центры',
            'x':4137,
            'y':64,
            'z':-1956,
            'name':'Торговый комплекс "Зелёный городок"'
        },
                                        {
            'id':'Торговые центры',
            'x':40,
            'y':64,
            'z':3771,
            'name':'Торговый центр "Тёмный замок"'
        },
                                        {
            'id':'Торговые центры',
            'x':-5655,
            'y':64,
            'z':1550,
            'name':'ТЦ на желтой'
        },
#Базы игроков
#Желтая ветка
        {
            'id':'Базы игроков',
            'x':-1407,
            'y':64,
            'z':-980,
            'name':'Перчик'
        },
        {
            'id':'Базы игроков',
            'x':-2007,
            'y':64,
            'z':-1918,
            'name':'_Kaktus_CZ_ & Egorizik'
        },
        {
            'id':'Базы игроков',
            'x':-2542,
            'y':64,
            'z':-822,
            'name':'Torsons'
        },
        {
            'id':'Базы игроков',
            'x':-2742,
            'y':64,
            'z':399,
            'name':'distructor'
        },
        {
            'id':'Базы игроков',
            'x':-4078,
            'y':64,
            'z':1620,
            'name':'IL86'
        },
        {
            'id':'Базы игроков',
            'x':-4894,
            'y':64,
            'z':-1753,
            'name':'ПОЗЕР'
        },
        {
            'id':'Базы игроков',
            'x':-6006,
            'y':64,
            'z':1295,
            'name':'EUGENlJUS'
        },
        {
            'id':'Базы игроков',
            'x':-7909,
            'y':64,
            'z':-2832,
            'name':'База THE REBELS'
        },
#Красная ветка
        {
            'id':'Базы игроков',
            'x':2487,
            'y':64,
            'z':-2542,
            'name':'Sawl'
        },
        {
            'id':'Базы игроков',
            'x':-1061,
            'y':72,
            'z':-3913,
            'name':'Nefz & beJIbIu_WhiTe',
            'description':'городок'
        },
        {
            'id':'Базы игроков',
            'x':655,
            'y':64,
            'z':-3970,
            'name':'Croud'
        },
        {
            'id':'Базы игроков',
            'x':1817,
            'y':64,
            'z':-4525,
            'name':'Hutas'
        },
        {
            'id':'Базы игроков',
            'x':4894,
            'y':64,
            'z':-5683,
            'name':'BlackPirat'
        },
        {
            'id':'Базы игроков',
            'x':4148,
            'y':64,
            'z':-5784,
            'name':'S1mmy8769, Nergy_Box, YT_FiNNSTER, Realgentelman'
        },
        {
            'id':'Базы игроков',
            'x':-13,
            'y':64,
            'z':-6000,
            'name':'InterpoL'
        },
        {
            'id':'Базы игроков',
            'x':878,
            'y':64,
            'z':-6112,
            'name':'eldalomeo'
        },
        {
            'id':'Базы игроков',
            'x':2021,
            'y':64,
            'z':-6235,
            'name':'turbo'
        },
        {
            'id':'Базы игроков',
            'x':5323,
            'y':64,
            'z':-8500,
            'name':'Dragon_Fly_TV'
        },
        {
            'id':'Базы игроков',
            'x':-6160,
            'y':64,
            'z':-9402,
            'name':'AndPro'
        },
#Зелёная ветка
        {
            'id':'Базы игроков',
            'x':740,
            'y':64,
            'z':124,
            'name':'joukeecz & Zerrochi'
        },
        {
            'id':'Базы игроков',
            'x':976,
            'y':72,
            'z':204,
            'name':'MINI__FROSTIK_',
            'description':'Медовый остров'
        },
        {
            'id':'Базы игроков',
            'x':1956,
            'y':64,
            'z':-276,
            'name':'B1ackie & Steinyasha'
        },
        {
            'id':'Базы игроков',
            'x':2356,
            'y':64,
            'z':1761,
            'name':'Pro100Antoxa'
        },
        {
            'id':'Базы игроков',
            'x':2903,
            'y':64,
            'z':561,
            'name':'fN9ne'
        },
        {
            'id':'Базы игроков',
            'x':3447,
            'y':64,
            'z':100,
            'name':'The_Lurkez'
        },
        {
            'id':'Базы игроков',
            'x':4089,
            'y':64,
            'z':392,
            'name':'VladykaSirius'
        },
        {
            'id':'Базы игроков',
            'x':4387,
            'y':64,
            'z':-834,
            'name':'Rivaviva'
        },
        {
            'id':'Базы игроков',
            'x':5354,
            'y':64,
            'z':3626,
            'name':'Li_ora'
        },
        {
            'id':'Базы игроков',
            'x':6095,
            'y':64,
            'z':-6595,
            'name':'Kharkovite'
        },
        {
            'id':'Базы игроков',
            'x':6929,
            'y':64,
            'z':-6667,
            'name':'RostBarracuda'
        },
        {
            'id':'Базы игроков',
            'x':6775,
            'y':64,
            'z':-1793,
            'name':'Mr_Green25 & _LoveSosa_'
        },
        {
            'id':'Базы игроков',
            'x':6787,
            'y':64,
            'z':3597,
            'name':'SoftPanda3'
        },
        {
            'id':'Базы игроков',
            'x':8368,
            'y':64,
            'z':-5835,
            'name':'Daesael'
        },
        {
            'id':'Базы игроков',
            'x':9793,
            'y':64,
            'z':-4425,
            'name':'Mirkovka & Komander_'
        },
        {
            'id':'Базы игроков',
            'x':9763,
            'y':64,
            'z':9183,
            'name':'Штейн и матюша'
        },
#Синяя ветка
                {
            'id':'Базы игроков',
            'x':-44,
            'y':64,
            'z':738,
            'name':'Император Adrian'
        },
        {
            'id':'Базы игроков',
            'x':287,
            'y':72,
            'z':957,
            'name':'Префектура PrOsTiK'
        },
                {
            'id':'Базы игроков',
            'x':415,
            'y':64,
            'z':1980,
            'name':'Niksa & som1c'
        },
                {
            'id':'Базы игроков',
            'x':-2449,
            'y':64,
            'z':4105,
            'name':'welcome32 & lemon'
        },
        {
            'id':'Базы игроков',
            'x':5546,
            'y':64,
            'z':7924,
            'name':'PaN_PiteN & Landcat'
        },
        {
            'id':'Базы игроков',
            'x':-2563,
            'y':64,
            'z':8207,
            'name':'Lady_MineRain'
        },
        {
            'id':'Базы игроков',
            'x':-6821,
            'y':64,
            'z':9077,
            'name':'_Rogalik_Games_ & RENDAL_01'
        },
        {
            'id':'Базы игроков',
            'x':8564,
            'y':64,
            'z':9686,
            'name':'el_mecanico + loco_viejo'
        },
#Фермы
        {
            'id':'Фермы',
            'x':923,
            'y':50,
            'z':172,
            'name':'Ферма рейдов'
        },
        {
            'id':'Фермы',
            'x':1229,
            'y':50,
            'z':-744,
            'name':'Ферма гвардов'
        },
#Фермы
        {
            'id':'Фермы',
            'x':3520,
            'y':64,
            'z':1544,
            'name':'Мини комплекс ферм'
        },
        {
            'id':'Фермы',
            'x':5177,
            'y':64,
            'z':-1990,
            'name':'Комплекс ферм'
        },
        {
            'id':'Фермы',
            'x':-5655,
            'y':64,
            'z':1550,
            'name':'Комплекс ферм'
        },
        {
            'id':'Фермы',
            'x':7440,
            'y':64,
            'z':1344,
            'name':'Ферма рейдов'
        },
        {
            'id':'Фермы',
            'x':9811,
            'y':64,
            'z':-5924,
            'name':'Ферма гвардов'
        },
        {
            'id':'Фермы',
            'x':-853,
            'y':64,
            'z':2055,
            'name':'Ферма шерсти'
        },
        {
            'id':'Фермы',
            'x':1170,
            'y':64,
            'z':4188,
            'name':'Ферма пороха'
        },
        {
            'id':'Фермы',
            'x':686,
            'y':64,
            'z':4262,
            'name':'Ферма снега'
        },
        {
            'id':'Фермы',
            'x':-873,
            'y':64,
            'z':4869,
            'name':'Ферма лиан'
        },
        {
            'id':'Фермы',
            'x':-1749,
            'y':64,
            'z':5175,
            'name':'Ферма меди'
        },
        {
            'id':'Фермы',
            'x':470,
            'y':64,
            'z':7043,
            'name':'Ферма спрутов'
        },
        {
            'id':'Фермы',
            'x':-1029,
            'y':64,
            'z':7870,
            'name':'Ферма рейдов'
        },
        {
            'id':'Фермы',
            'x':-2452,
            'y':64,
            'z':2596,
            'name':'Ферма мобов'
        },
        {
            'id':'Фермы',
            'x':-3062,
            'y':64,
            'z':2565,
            'name':'Ферма рейдов'
        },
        {
            'id':'Фермы',
            'x':-4553,
            'y':64,
            'z':2354,
            'name':'Ферма ведьм'
        },
        {
            'id':'Фермы',
            'x':-7267,
            'y':64,
            'z':-5370,
            'name':'Ферма трезубцев'
        },
        {
            'id':'Фермы',
            'x':4,
            'y':64,
            'z':-2185,
            'name':'Ферма льда'
        },
        {
            'id':'Фермы',
            'x':4279,
            'y':64,
            'z':-4378,
            'name':'Ферма коров'
        },
        {
            'id':'Фермы',
            'x':2449,
            'y':64,
            'z':-4459,
            'name':'Ферма рейдов'
        },
        {
            'id':'Фермы',
            'x':-1538,
            'y':64,
            'z':-5985,
            'name':'Ферма цветов'
        },
        {
            'id':'Фермы',
            'x':7849,
            'y':64,
            'z':-10057,
            'name':'Ферма трезубцев'
        },
    ],
    #'markers': [dict(name='players',filterFunction=playerIcons,checked=True),
    'markers': [
        dict(name='Города',filterFunction=townFilter,icon="icons/Города.png", showIconInLegend=True),
        dict(name='Базы игроков',filterFunction=baseFilter,icon="icons/Базы игроков.png", showIconInLegend=True),
                dict(name='Торговые центры',filterFunction=tcFilter,icon="icons/ТЦ и ТК.png", showIconInLegend=True),
        dict(name='Фермы',filterFunction=fermsFilter,icon="icons/Фермы.png", showIconInLegend=True)
    ],
    'defaultzoom': 7,
    "crop": (-10250, -10250, 10250, 10250),
    #'forcerender': True
}
renders["over_night"] = {
    'world': 'CublayCraft-Over',
    'title': '\u041d\u043e\u0447\u044c', #Ночь
    'rendermode': night,
    'dimension': 'overworld',
    'defaultzoom': 7,
        'center': (0, 0, 0),
    "crop": (-10250, -10250, 10250, 10250),
    #'forcerender': True
}
renders["nether"] = {
    'world': 'CublayCraft-Nether',
    'title': '\u041d\u0438\u0436\u043d\u0438\u0439 \u043c\u0438\u0440', #Нижний мир
    'rendermode': [Base(), EdgeLines(), Nether(), SmoothLighting(strength=0.5), Depth(max=47)],
        'dimension': "nether",
    'defaultzoom': 3,
    "crop": (-5100, -5100, 5100, 5100),
    #'forcerender': True
        'manualpois':[
{
'id':'Красная ветка',
'x':188,
'y':50,
'z':-227,
'name':'Mefisto1345'
},
{
'id':'Красная ветка',
'x':-54,
'y':50,
'z':-209,
'name':'Xaker__Cool'
},
{
'id':'Красная ветка',
'x':-125,
'y':50,
'z':-239,
'name':'SkyDance_'
},
{
'id':'Красная ветка',
'x':312,
'y':50,
'z':-317,
'name':'Sawl'
},
{
'id':'Красная ветка',
'x':-204,
'y':50,
'z':-479,
'name':'Jucl ( Chican )'
},
{
'id':'Красная ветка',
'x':-129,
'y':50,
'z':-491,
'name':'Nefz & beJIbIu_WhiTe'
},
{
'id':'Красная ветка',
'x':83,
'y':50,
'z':-491,
'name':'_Croud_'
},
{
'id':'Красная ветка',
'x':90,
'y':50,
'z':-539,
'name':'Fireshark112'
},
{
'id':'Красная ветка',
'x':228,
'y':50,
'z':-563,
'name':'Hutas'
},
{
'id':'Красная ветка',
'x':-435,
'y':50,
'z':-563,
'name':'Roma102009'
},
{
'id':'Красная ветка',
'x':611,
'y':50,
'z':-707,
'name':'BlackPirat'
},
{
'id':'Красная ветка',
'x':520,
'y':50,
'z':-719,
'name':'Nergy_Box && S1mmy8769 && YT_FiNNSTER && Realgentelman'
},
{
'id':'Красная ветка',
'x':10,
'y':50,
'z':-749,
'name':'DoCeNtTV'
},
{
'id':'Красная ветка',
'x':110,
'y':50,
'z':-761,
'name':'eldalomeo'
},
{
'id':'Красная ветка',
'x':251,
'y':50,
'z':-779,
'name':'dalandis'
},
{
'id':'Красная ветка',
'x':526,
'y':50,
'z':-815,
'name':'van1llin'
},
{
'id':'Красная ветка',
'x':286,
'y':50,
'z':-923,
'name':'Leila_OG'
},
{
'id':'Красная ветка',
'x':-408,
'y':50,
'z':-1007,
'name':'MinerFixed'
},
{
'id':'Красная ветка',
'x':254,
'y':50,
'z':-1073,
'name':'Weyland'
},
{
'id':'Красная ветка',
'x':669,
'y':50,
'z':-1073,
'name':'Dragon_Fly_TV'
},
{
'id':'Красная ветка',
'x':-505,
'y':50,
'z':-1133,
'name':'Matychka'
},
{
'id':'Красная ветка',
'x':272,
'y':50,
'z':-1175,
'name':'_Adrian_07_'
},
{
'id':'Красная ветка',
'x':-774,
'y':50,
'z':-1175,
'name':'_Alonzo_'
},
{
'id':'Красная ветка',
'x':-41,
'y':50,
'z':-1229,
'name':'Ilyastik'
},
{
'id':'Красная ветка',
'x':1197,
'y':50,
'z':-1259,
'name':'гильдия св. Смерти'
},
{
'id':'Желтая ветка',
'x':-149,
'y':50,
'z':-79,
'name':'MizharkPlay'
},
{
'id':'Желтая ветка',
'x':-161,
'y':50,
'z':7,
'name':'Drofin'
},
{
'id':'Желтая ветка',
'x':-251,
'y':50,
'z':-236,
'name':'_Kaktus_CZ_'
},
{
'id':'Желтая ветка',
'x':-335,
'y':50,
'z':-106,
'name':'Torsons'
},
{
'id':'Желтая ветка',
'x':-335,
'y':50,
'z':36,
'name':'JayJay'
},
{
'id':'Желтая ветка',
'x':-383,
'y':50,
'z':170,
'name':'Orbus_'
},
{
'id':'Желтая ветка',
'x':-395,
'y':50,
'z':52,
'name':'ponchers'
},
{
'id':'Желтая ветка',
'x':-515,
'y':50,
'z':197,
'name':'IL86'
},
{
'id':'Желтая ветка',
'x':-527,
'y':50,
'z':520,
'name':'Новогодний остров'
},
{
'id':'Желтая ветка',
'x':-599,
'y':50,
'z':-224,
'name':'_LoveSosa_'
},
{
'id':'Желтая ветка',
'x':-635,
'y':50,
'z':415,
'name':'loblNemezis & Dir19 & Akuragava'
},
{
'id':'Желтая ветка',
'x':-653,
'y':50,
'z':-232,
'name':'VessAY'
},
{
'id':'Желтая ветка',
'x':-695,
'y':50,
'z':-133,
'name':'oplkill'
},
{
'id':'Желтая ветка',
'x':-755,
'y':50,
'z':172,
'name':'EUGENlJUS'
},
{
'id':'Желтая ветка',
'x':-743,
'y':50,
'z':-455,
'name':'GoodDra'
},
{
'id':'Желтая ветка',
'x':-833,
'y':50,
'z':173,
'name':'CKOBOPODKA2 & _LoganTV_ & TOPOTOP'
},
{
'id':'Желтая ветка',
'x':-851,
'y':50,
'z':9,
'name':'DamirF777'
},
{
'id':'Желтая ветка',
'x':-863,
'y':50,
'z':407,
'name':'prestig9110 & beJIbIu_WhiTe & InterpoL'
},
{
'id':'Желтая ветка',
'x':-875,
'y':50,
'z':-63,
'name':'_Almazik_'
},
{
'id':'Желтая ветка',
'x':-971,
'y':50,
'z':406,
'name':'IwINy (llklxq)'
},
{
'id':'Желтая ветка',
'x':-917,
'y':50,
'z':-664,
'name':'a_fantasy'
},
{
'id':'Желтая ветка',
'x':-1007,
'y':50,
'z':-349,
'name':'THE REBELS'
},
{
'id':'Желтая ветка',
'x':-1019,
'y':50,
'z':-10,
'name':'Catogg'
},
{
'id':'Желтая ветка',
'x':-1037,
'y':50,
'z':170,
'name':'Alissi'
},
{
'id':'Желтая ветка',
'x':-1139,
'y':50,
'z':866,
'name':'AmuTige'
},
{
'id':'Синяя ветка',
'x':33,
'y':50,
'z':77,
'name':'RadioHad && caxarok'
},
{
'id':'Синяя ветка',
'x':29,
'y':50,
'z':113,
'name':'PrOsTiK'
},
{
'id':'Синяя ветка',
'x':-38,
'y':50,
'z':113,
'name':'_Adrian_07_'
},
{
'id':'Синяя ветка',
'x':-10,
'y':50,
'z':161,
'name':'MinorSpace'
},
{
'id':'Синяя ветка',
'x':42,
'y':50,
'z':257,
'name':'Hukca & som1c (ApelsinA)'
},
{
'id':'Синяя ветка',
'x':-51,
'y':50,
'z':245,
'name':'Simply_Red'
},
{
'id':'Синяя ветка',
'x':60,
'y':50,
'z':359,
'name':'Kolmo'
},
{
'id':'Синяя ветка',
'x':401,
'y':50,
'z':461,
'name':'vitux & Yurik10'
},
{
'id':'Синяя ветка',
'x':-57,
'y':50,
'z':497,
'name':'Makasake'
},
{
'id':'Синяя ветка',
'x':-405,
'y':50,
'z':509,
'name':'lemon & welcome32'
},
{
'id':'Синяя ветка',
'x':-256,
'y':50,
'z':523,
'name':'Kerubifi'
},
{
'id':'Синяя ветка',
'x':272,
'y':50,
'z':539,
'name':'WiCry & kipo4'
},
{
'id':'Синяя ветка',
'x':-348,
'y':50,
'z':551,
'name':'MyNameIsNik45'
},
{
'id':'Синяя ветка',
'x':293,
'y':50,
'z':665,
'name':'ne_chebyrek'
},
{
'id':'Синяя ветка',
'x':-189,
'y':50,
'z':803,
'name':'20Roma20'
},
{
'id':'Синяя ветка',
'x':-320,
'y':50,
'z':1025,
'name':'GipperDipper'
},
{
'id':'Синяя ветка',
'x':-851,
'y':50,
'z':1133,
'name':'_Rogalik_Games_'
},
{
'id':'Синяя ветка',
'x':217,
'y':50,
'z':1175,
'name':'SkyDragon'
},
{
'id':'Синяя ветка',
'x':1071,
'y':50,
'z':1211,
'name':'el_mecanico'
},
{
'id':'Зеленая ветка',
'x':65,
'y':50,
'z':-18,
'name':'PupKin'
},
{
'id':'Зеленая ветка',
'x':83,
'y':50,
'z':21,
'name':'joukeecz'
},
{
'id':'Зеленая ветка',
'x':119,
'y':50,
'z':24,
'name':'MINI__FROSTIK_'
},
{
'id':'Зеленая ветка',
'x':227,
'y':50,
'z':-25,
'name':'_B1ackie_ & Steinyasha'
},
{
'id':'Зеленая ветка',
'x':293,
'y':50,
'z':209,
'name':'Pro100Antoxa37'
},
{
'id':'Зеленая ветка',
'x':317,
'y':50,
'z':-147,
'name':'kplay'
},
{
'id':'Зеленая ветка',
'x':359,
'y':50,
'z':70,
'name':'fN9ne'
},
{
'id':'Зеленая ветка',
'x':395,
'y':50,
'z':242,
'name':'Immortal_Life'
},
{
'id':'Зеленая ветка',
'x':383,
'y':50,
'z':-313,
'name':'andrew_10'
},
{
'id':'Зеленая ветка',
'x':408,
'y':50,
'z':78,
'name':'Som1c'
},
{
'id':'Зеленая ветка',
'x':419,
'y':50,
'z':158,
'name':'Cublay & kurlykepty & ilyas0'
},
{
'id':'Зеленая ветка',
'x':409,
'y':50,
'z':166,
'name':'Evgenii'
},
{
'id':'Зеленая ветка',
'x':437,
'y':50,
'z':9,
'name':'The_Lurkez'
},
{
'id':'Зеленая ветка',
'x':458,
'y':50,
'z':46,
'name':'Aleksmite'
},
{
'id':'Зеленая ветка',
'x':458,
'y':50,
'z':58,
'name':'Berlan'
},
{
'id':'Зеленая ветка',
'x':455,
'y':50,
'z':294,
'name':'Lawer328'
},
{
'id':'Зеленая ветка',
'x':467,
'y':50,
'z':89,
'name':'PraiseTheVodka'
},
{
'id':'Зеленая ветка',
'x':509,
'y':50,
'z':53,
'name':'VladykaSirius'
},
{
'id':'Зеленая ветка',
'x':545,
'y':50,
'z':-110,
'name':'Rivaviva'
},
{
'id':'Зеленая ветка',
'x':533,
'y':50,
'z':424,
'name':'Nebulet'
},
{
'id':'Зеленая ветка',
'x':629,
'y':50,
'z':196,
'name':'Takenava'
},
{
'id':'Зеленая ветка',
'x':587,
'y':50,
'z':149,
'name':'lodachka'
},
{
'id':'Зеленая ветка',
'x':641,
'y':50,
'z':-60,
'name':'Adekvatniy_'
},
{
'id':'Зеленая ветка',
'x':653,
'y':50,
'z':455,
'name':'Li_Ora'
},
{
'id':'Зеленая ветка',
'x':761,
'y':50,
'z':-828,
'name':'Kharkovite'
},
{
'id':'Зеленая ветка',
'x':833,
'y':50,
'z':-834,
'name':'RostBarracuda'
},
{
'id':'Зеленая ветка',
'x':845,
'y':50,
'z':-226,
'name':'Mr_Green25'
},
{
'id':'Зеленая ветка',
'x':845,
'y':50,
'z':461,
'name':'SoftPanda3 && MiSanTo && TheBadCompany'
},
{
'id':'Зеленая ветка',
'x':863,
'y':50,
'z':-673,
'name':'J_ROSH'
},
{
'id':'Зеленая ветка',
'x':983,
'y':50,
'z':300,
'name':'No_Oluk'
},
{
'id':'Зеленая ветка',
'x':983,
'y':50,
'z':-64,
'name':'Bard_Allen'
},
{
'id':'Зеленая ветка',
'x':995,
'y':50,
'z':-612,
'name':'Грибной остров'
},
{
'id':'Зеленая ветка',
'x':995,
'y':50,
'z':71,
'name':'marvinmango'
},
{
'id':'Зеленая ветка',
'x':1037,
'y':50,
'z':-153,
'name':'AlexKiborg'
},
{
'id':'Зеленая ветка',
'x':1049,
'y':50,
'z':-719,
'name':'Daesael'
},
{
'id':'Зеленая ветка',
'x':1073,
'y':50,
'z':412,
'name':'Polymorph'
},
{
'id':'Зеленая ветка',
'x':1139,
'y':50,
'z':-847,
'name':'rainbowoof & xKobo'
},
{
'id':'Зеленая ветка',
'x':1191,
'y':50,
'z':989,
'name':'Stavrik'
},
{
'id':'Зеленая ветка',
'x':1217,
'y':50,
'z':1133,
'name':'Stein & Matychka'
},
{
'id':'Зеленая ветка',
'x':1215,
'y':50,
'z':-564,
'name':'Mirkovka'
},
{
'id':'End порталы',
'x':-191,
'y':50,
'z':-209,
'name':'End portal number 10 "Красная 209"'
},
{
'id':'End порталы',
'x':441,
'y':50,
'z':-491,
'name':'End portal number 11 "Красная 491"'
},
{
'id':'End порталы',
'x':-202,
'y':50,
'z':-617,
'name':'End portal number 4 "Красная 617"'
},
{
'id':'End порталы',
'x':404,
'y':50,
'z':-923,
'name':'End portal number 15 "Красная 923"'
},
{
'id':'End порталы',
'x':-226,
'y':50,
'z':-1004,
'name':'End portal number 8 "Красная 1001"'
},
{
'id':'End порталы',
'x':818,
'y':50,
'z':-1175,
'name':'End portal number 22 "Красная 1175"'
},
{
'id':'End порталы',
'x':-881,
'y':50,
'z':-1175,
'name':'End portal number 16 "Красная 1175"'
},
{
'id':'End порталы',
'x':314,
'y':50,
'z':-55,
'name':'End portal number 20 "Зелёная 317"'
},
{
'id':'End порталы',
'x':575,
'y':50,
'z':117,
'name':'End portal number 2 "Зелёная 575"'
},
{
'id':'End порталы',
'x':743,
'y':50,
'z':667,
'name':'End portal number 26 "Зелёная 743"'
},
{
'id':'End порталы',
'x':863,
'y':50,
'z':-492,
'name':'End portal number 21 "Зелёная 863"'
},
{
'id':'End порталы',
'x':1031,
'y':50,
'z':107,
'name':'End portal number 7 "Зелёная 1031"'
},
{
'id':'End порталы',
'x':1013,
'y':50,
'z':883,
'name':'End portal number 9 "Зелёная 1013"'
},
{
'id':'End порталы',
'x':1229,
'y':50,
'z':-744,
'name':'End portal number 5 "Зелёная 1229"'
},
{
'id':'End порталы',
'x':-69,
'y':50,
'z':215,
'name':'End portal number 1 "Синяя 215"'
},
{
'id':'End порталы',
'x':-438,
'y':50,
'z':509,
'name':'End portal number 19 "Синяя 509"'
},
{
'id':'End порталы',
'x':195,
'y':50,
'z':542,
'name':'End portal number 17 "Синяя 539"'
},
{
'id':'End порталы',
'x':-434,
'y':50,
'z':959,
'name':'End portal number 18 "Синяя 959"'
},
{
'id':'End порталы',
'x':231,
'y':50,
'z':1013,
'name':'End portal number 24 "Синяя 1013"'
},
{
'id':'End порталы',
'x':565,
'y':50,
'z':1214,
'name':'End portal number 25 "Синяя 1211"'
},
{
'id':'End порталы',
'x':-543,
'y':50,
'z':1265,
'name':'End portal number 27 "Синяя 1265"'
},
{
'id':'End порталы',
'x':-713,
'y':50,
'z':-125,
'name':'End portal number 3 "Жёлтая 713"'
},
{
'id':'End порталы',
'x':-851,
'y':50,
'z':512,
'name':'End portal number 13 "Жёлтая 851"'
},
{
'id':'End порталы',
'x':-701,
'y':50,
'z':-650,
'name':'End portal number 12 "Жёлтая 701"'
},
{
'id':'End порталы',
'x':-1003,
'y':50,
'z':-88,
'name':'End portal number 14 "Жёлтая 1007"'
},
{
'id':'End порталы',
'x':-1037,
'y':50,
'z':963,
'name':'End portal number 6 "Жёлтая 1037"'
},
{
'id':'End порталы',
'x':-1229,
'y':50,
'z':-686,
'name':'End portal number 23 "Жёлтая 1229"'
},
{
'id':'Фермы',
'x':-311,
'y':50,
'z':309,
'name':'Ферма мобов'
},
{
'id':'Фермы',
'x':-383,
'y':50,
'z':317,
'name':'Ферма рейдов'
},
{
'id':'Фермы',
'x':-569,
'y':50,
'z':294,
'name':'Ферма ведьм'
},
{
'id':'Фермы',
'x':-713,
'y':50,
'z':193,
'name':'Торговый зал'
},
{
'id':'Фермы',
'x':-917,
'y':50,
'z':-664,
'name':'Ферма трезубцев'
},
{
'id':'Фермы',
'x':-10,
'y':50,
'z':-269,
'name':'Ферма льда'
},
{
'id':'Фермы',
'x':336,
'y':50,
'z':-554,
'name':'Ферма рейдов'
},
{
'id':'Фермы',
'x':540,
'y':50,
'z':-551,
'name':'Ферма коров'
},
{
'id':'Фермы',
'x':125,
'y':50,
'z':-617,
'name':'Торговый цетр'
},
{
'id':'Фермы',
'x':-193,
'y':50,
'z':-731,
'name':'Ферма цветов'
},
{
'id':'Фермы',
'x':80,
'y':50,
'z':-977,
'name':'"Ферма ифритов & Ферма визер-голов"'
},
{
'id':'Фермы',
'x':968,
'y':50,
'z':-1241,
'name':'Ферма трезубцев'
},
{
'id':'Фермы',
'x':102,
'y':50,
'z':245,
'name':'Ферма ачивок'
},
{
'id':'Фермы',
'x':-100,
'y':50,
'z':257,
'name':'Ферма шерсти'
},
{
'id':'Фермы',
'x':70,
'y':50,
'z':551,
'name':'Ферма снега'
},
{
'id':'Фермы',
'x':3,
'y':50,
'z':491,
'name':'Торговый центр'
},
{
'id':'Фермы',
'x':-124,
'y':50,
'z':623,
'name':'Ферма лиан'
},
{
'id':'Фермы',
'x':63,
'y':50,
'z':881,
'name':'Ферма спрутов'
},
{
'id':'Фермы',
'x':-146,
'y':50,
'z':1001,
'name':'Ферма рейдов(фарм)'
},
{
'id':'Фермы',
'x':-213,
'y':50,
'z':1001,
'name':'Ферма рейдов(аванпост)'
},
{
'id':'Фермы',
'x':203,
'y':50,
'z':105,
'name':'"Ферма визер-голов & Ферма ифритов"'
},
{
'id':'Фермы',
'x':419,
'y':50,
'z':195,
'name':'Мини комплекс ферм'
},
{
'id':'Фермы',
'x':515,
'y':50,
'z':-237,
'name':'Торговый городок'
},
{
'id':'Фермы',
'x':653,
'y':50,
'z':-254,
'name':'Большой комплекс ферм'
},
{
'id':'Фермы',
'x':923,
'y':50,
'z':172,
'name':'Ферма рейдов'
},
{
'id':'Фермы',
'x':1229,
'y':50,
'z':-744,
'name':'Ферма гвардов'
},
    ],
    'markers': [
        dict(name='Красная ветка',filterFunction=redFilter,icon="icons/База игрока красная.png", showIconInLegend=True),
        dict(name='Желтая ветка',filterFunction=yellowFilter,icon="icons/База игрока желтая.png", showIconInLegend=True),
        dict(name='Синяя ветка',filterFunction=blueFilter,icon="icons/База игрока синяя.png", showIconInLegend=True),
        dict(name='Зеленая ветка',filterFunction=greenFilter,icon="icons/База игрока зеленая.png", showIconInLegend=True),
        dict(name='End порталы',filterFunction=endportFilter,icon="icons/Энд портал.png", showIconInLegend=True),
        dict(name='Фермы',filterFunction=fermsFilter,icon="icons/Фермы.png", showIconInLegend=True)
    ],
}
renders["nether_roof"] = {
    'world': 'CublayCraft-Nether',
    'title': '\u041a\u0440\u044b\u0448\u0430 \u043d\u0438\u0436\u043d\u0435\u0433\u043e \u043c\u0438\u0440\u0430', #Крыша нижнего мира
    'rendermode': [Base(), EdgeLines(), SmoothLighting(strength=0.5)],
        'dimension': "nether",
    'defaultzoom': 3,
    "crop": (-5100, -5100, 5100, 5100),
    #'forcerender': True
            'manualpois':[
        {
            'id':'Фермы',
            'x':7,
            'y':129,
            'z':0,
            'name':'Ферма золота и опыта',
        },
        {
            'id':'Фермы',
            'x':0,
            'y':129,
            'z':220,
            'name':'Ферма базальта',
        },
                {
            'id':'Фермы',
            'x':0,
            'y':129,
            'z':460,
            'name':'Ферма золота',
        },
            {
            'id':'Фермы',
            'x':-254,
            'y':129,
            'z':0,
            'name':'Обменник на пиглинах',
        },
                {
            'id':'Фермы',
            'x':-944,
            'y':129,
            'z':0,
            'name':'Ферма незерского нароста',
        },
    ],
    'markers': [
        dict(name='Фермы',filterFunction=fermsFilter,icon="icons/Фермы.png", showIconInLegend=True)
    ],
}
renders["the_end"] = {
    "world": "CublayCraft-End",
    "title": "\u041a\u0440\u0430\u0439 \u0028\u044d\u043d\u0434\u0435\u0440 \u043c\u0438\u0440\u0029", #Край (эндер мир)
    "rendermode": end_smooth_lighting,
    "dimension": "end",
    "crop": (-5500, -5500, 5500, 5500),
    'defaultzoom': 6,
    #'forcerender': True
    'manualpois':[
        {
            'id':'Пиксель арты',
            'x':2190,
            'y':100,
            'z':-4871,
            'name':'BlackPirat',
            'description':'Скажем нет кубизму:)))'
        },
        {
            'id':'Пиксель арты',
            'x':0,
            'y':100,
            'z':-642,
            'name':'CublayCraft',
            'description':'Газета CublayCraft'
        },
        {
            'id':'Пиксель арты',
            'x':-325,
            'y':100,
            'z':-437,
            'name':'CublayCraft',
            'description':'Схема хайперлупов'
        },
{
            'id':'Пиксель арты',
            'x':-572,
            'y':100,
            'z':-436,
            'name':'SoftPanda3 & prestig9110',
            'description':'Новогоднее чудо'
        },
        {
            'id':'Пиксель арты',
            'x':-330,
            'y':100,
            'z':-197,
            'name':'SoftPanda3',
            'description':'Хэллоуин'
        },
        {
            'id':'Пиксель арты',
            'x':-543,
            'y':100,
            'z':-6,
            'name':'beJIbIu_WhiTe & _Nefz_ & BlackPirat',
            'description':'Ауткаст'
        },
        {
            'id':'Пиксель арты',
            'x':-558,
            'y':100,
            'z':378,
            'name':'Valhalla',
            'description':'Meghan Markle (Шальная императрица)'
        },
        {
            'id':'Пиксель арты',
            'x':-576,
            'y':100,
            'z':792,
            'name':'Niksa',
            'description':'Сон волка'
        },
        {
            'id':'Пиксель арты',
            'x':-323,
            'y':100,
            'z':66,
            'name':'SoftPanda3',
            'description':'Милая пандочка'
        },
        {
            'id':'Пиксель арты',
            'x':-341,
            'y':100,
            'z':472,
            'name':'SoftPanda3',
            'description':'Трисс Меригольд'
        },
        {
            'id':'Пиксель арты',
            'x':-323,
            'y':100,
            'z':751,
            'name':'Kerubifi',
            'description':'Тян'
        },
        {
            'id':'Пиксель арты',
            'x':719,
            'y':100,
            'z':-332,
            'name':'Nefz',
            'description':'beJIbIu_WhiTe'
        },
        {
            'id':'Пиксель арты',
            'x':654,
            'y':100,
            'z':-14,
            'name':'Матюшка',
            'description':'Динозаврик'
        },
        {
            'id':'Пиксель арты',
            'x':565,
            'y':100,
            'z':499,
            'name':'Dalandis',
            'description':'AC/DC. При поддержке СофтПанды, Престижа, Матюши и Штейняши'
        },
        {
            'id':'Пиксель арты',
            'x':190,
            'y':100,
            'z':834,
            'name':'Матюшка',
            'description':'За Альянс! Орда сосед'
        },
        {
            'id':'Пиксель арты',
            'x':-70,
            'y':100,
            'z':826,
            'name':'CublayCraft',
            'description':'Приветствие'
        },
        {
            'id':'Пиксель арты',
            'x':207,
            'y':100,
            'z':565,
            'name':'beJIbIu_WhiTe & prestig9110',
            'description':'Инь и ян'
        },
        {
            'id':'Пиксель арты',
            'x':179,
            'y':100,
            'z':386,
            'name':'lodachka',
            'description':'Coffin dance meme'
        },
        {
            'id':'Пиксель арты',
            'x':258,
            'y':100,
            'z':256,
            'name':'Nefz',
            'description':'Первый поцелуй'
        },
        {
            'id':'Пиксель арты',
            'x':128,
            'y':100,
            'z':269,
            'name':'Nefz',
            'description':'Страсть'
        },
        {
            'id':'Пиксель арты',
            'x':-4,
            'y':100,
            'z':262,
            'name':'Immortal_life',
            'description':'Чеширский кот'
        },
        {
            'id':'Пиксель арты',
            'x':-6,
            'y':100,
            'z':388,
            'name':'MinorSpace',
            'description':'Космонавт'
        },
        {
            'id':'Пиксель арты',
            'x':-2,
            'y':100,
            'z':514,
            'name':'VladykaSirius',
            'description':'Человек'
        },
        {
            'id':'Пиксель арты',
            'x':-2,
            'y':100,
            'z':643,
            'name':'VladykaSirius',
            'description':'Cublay'
        },
        {
            'id':'Пиксель арты',
            'x':-131,
            'y':100,
            'z':643,
            'name':'joukeecz',
            'description':'Старец'
        },
        {
            'id':'Пиксель арты',
            'x':-131,
            'y':100,
            'z':643,
            'name':'Nefz',
            'description':'Погрызунчик'
        },
        {
            'id':'Пиксель арты',
            'x':-131,
            'y':100,
            'z':386,
            'name':'legushQka',
            'description':'Карты'
        },
        {
            'id':'Пиксель арты',
            'x':-131,
            'y':100,
            'z':268,
            'name':'MinorSpaсe',
            'description':'Планета'
        },
        {
            'id':'Пиксель арты',
            'x':1291,
            'y':100,
            'z':1659,
            'name':'kipo4 & Niksa',
            'description':'Шерстяной бутерброд'
        },
        {
            'id':'Пиксель арты',
            'x':-2414,
            'y':100,
            'z':-3718,
            'name':'Kerubifi & VessAY',
            'description':'Director Jesse Faden'
        },
        {
            'id':'Пиксель арты',
            'x':-2401,
            'y':100,
            'z':-5014,
            'name':'SoftPanda3',
            'description':'Life Is Strange: Хлоя Элизабет Прайс'
        },
        {
            'id':'Пиксель арты',
            'x':-2534,
            'y':100,
            'z':-4618,
            'name':'SoftPanda3',
            'description':'ВанКорг'
        },
        {
            'id':'Пиксель арты',
            'x':-1999,
            'y':100,
            'z':-4648,
            'name':'SoftPanda3',
            'description':'Картина девушки часть №3'
        },
        {
            'id':'Пиксель арты',
            'x':-2236,
            'y':100,
            'z':-4384,
            'name':'SoftPanda3',
            'description':'Картина девушки часть №2'
        },
        {
            'id':'Пиксель арты',
            'x':-2264,
            'y':100,
            'z':-4623,
            'name':'SoftPanda3',
            'description':'Картина девушки часть №1'
        },
        {
            'id':'Пиксель арты',
            'x':-2007,
            'y':100,
            'z':-4398,
            'name':'SoftPanda3',
            'description':'Картина девушки часть №4'
        },
        {
            'id':'Пиксель арты',
            'x':-2269,
            'y':100,
            'z':4339,
            'name':'Hutas & MinorSpace',
            'description':'Мы следим за тобой, ничтожество часть №1'
        },
        {
            'id':'Пиксель арты',
            'x':-2640,
            'y':100,
            'z':4056,
            'name':'Hutas & MinorSpace',
            'description':'Мы следим за тобой, ничтожество часть №2'
        },
        {
            'id':'Пиксель арты',
            'x':-2749,
            'y':100,
            'z':3963,
            'name':'Hutas & MinorSpace',
            'description':'Мы следим за тобой, ничтожество часть №3'
        },
        {
            'id':'Пиксель арты',
            'x':-3007,
            'y':100,
            'z':3579,
            'name':'Hutas & MinorSpace',
            'description':'Мы следим за тобой, ничтожество часть №4'
        },
    ],
    'markers': [
        dict(name='Пиксель арты',filterFunction=pixelFilter,icon="icons/Арт.png", showIconInLegend=True)
    ],
}
renders["plotworldUL"] = {
    'world': 'CublayCraft-Builder',
    'title': '\u0421\u0435\u0432\u0435\u0440', #Север
        'northdirection' : 'upper-left',
    'rendermode': smooth_lighting,
     'dimension': 'overworld',
    'defaultzoom': 3,
    "crop": (-1800, -1800, 1800, 1800),
    #'forcerender': True
}
renders["plotworldUR"] = {
    'world': 'CublayCraft-Builder',
    'title': '\u0412\u043e\u0441\u0442\u043e\u043a', #Восток
        'northdirection' : 'upper-right',
    'rendermode': smooth_lighting,
    'dimension': 'overworld',
    'defaultzoom': 3,
    "crop": (-1800, -1800, 1800, 1800),
    #'forcerender': True
}
renders["plotworldLL"] = {
    'world': 'CublayCraft-Builder',
    'title': '\u0417\u0430\u043f\u0430\u0434', #Запад
        'northdirection' : 'lower-left',
    'rendermode': smooth_lighting,
    'dimension': 'overworld',
    'defaultzoom': 3,
    "crop": (-1800, -1800, 1800, 1800),
    #'forcerender': True
}
renders["plotworldLR"] = {
    'world': 'CublayCraft-Builder',
    'title': '\u042E\u0433', #Юг
        'northdirection' : 'lower-right',
    'rendermode': smooth_lighting,
    'dimension': 'overworld',
    'defaultzoom': 3,
    "crop": (-1800, -1800, 1800, 1800),
    #'forcerender': True
}

# Маркеры после завершения рендера:
# python overviewer.py --genpoi -c configNew.py --skip-scan --skip-players -p 1
# Иконки из вашего старого сайта должны лежать в outputdir/icons/.
# Ручные маркеры и выбранные изначально группы оставлены без изменений.
