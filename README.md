# Minecraft Overviewer: новые блоки, продолжение рендера и веб-прогресс

Исходники на базе GregoryAM-SP/The-Minecraft-Overviewer. Проверены рендер миров
Java Edition 1.21.5, модели из клиентских JAR 26.3 и 26.4-snapshot-5, восстановление
после остановки и лимит RAM в Ubuntu WSL2. Будущие версии с совместимым форматом
моделей поддерживаются автоматически; специальные модели могут требовать доработки.

## Скачать, собрать и запустить в Ubuntu / WSL2

Репозиторий приватный: используйте свой вход GitHub для клонирования либо
**Code → Download ZIP** и откройте распакованный каталог в Ubuntu.
В WSL храните исходники, копию мира и результат в `/home/имя`, чтобы избежать
медленной работы через OneDrive и `/mnt/c`.

```bash
sudo apt-get update
sudo apt-get install -y git build-essential python3-dev python3-venv unzip
git clone https://github.com/1tah/minecraft-overviewer-modern.git
cd minecraft-overviewer-modern
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0' 'numpy==2.3.5' 'Pillow==12.3.0' requests networkx
git clone --depth 1 --branch 12.3.0 https://github.com/python-pillow/Pillow.git ../overviewer-pillow-headers
export PIL_INCLUDE_DIR="$(cd ../overviewer-pillow-headers/src/libImaging && pwd)"
python setup.py build
cp example_config.py render_config.py
nano render_config.py
```

В конфиге укажите путь к **копии мира**, каталогу результата и официальному
**клиентскому** JAR вашей версии Minecraft. В примере все измерения находятся
в одном обычном сохранении. Для Paper/Bukkit с отдельными `world_nether` и
`world_the_end` в конце примера показаны дополнительные записи `worlds`:
поменяйте также поле `world` у соответствующего рендера.
`Depth(max=47)` в Nether убирает крышу, как на вашей прежней карте.
Для Overworld высота не обрезана; старый срез Y=254 можно вернуть через `Depth`.

Запустите рендер из каталога исходников:

```bash
source .venv/bin/activate
python overviewer.py -c render_config.py -p 4 --memory-limit 4G
```

`-p 4` — четыре рабочих процесса. `--memory-limit 4G` — общий предел памяти
группы рендера, включая рабочих, с отключённым swap этой группы. Нужны cgroup v2
и работающий systemd не ниже 254; проверено на Ubuntu 26.04 WSL2.
При нехватке памяти завершится группа рендера; увеличьте лимит либо уменьшите
`-p` и запустите **ту же команду**. Журнал продолжит сохранённый план.
Первоначальный анализ до создания плана при прерывании выполняется повторно.
Не используйте `--forcerender` для обычного продолжения.

## Смотреть карту во время генерации

Второй терминал Ubuntu (укажите **тот же outputdir**, что в конфиге):

```bash
cd ~/minecraft-overviewer-modern
mkdir -p "$HOME/minecraft-map"
.venv/bin/python -m http.server 8080 --bind 127.0.0.1 --directory "$HOME/minecraft-map"
```

Замените outputdir в конфиге на полный путь `/home/ваш_пользователь/minecraft-map`.
Откройте **http://localhost:8080/** в Windows или Ubuntu.
Overviewer создаёт сайт, а HTTP-сервер раздаёт его: оба процесса должны работать
одновременно, чтобы видеть генерацию. Для публичного домена раздавайте outputdir
через свой Nginx/Apache; встроенный сервер по этой команде доступен локально.

При первом рендере сначала виден экран подготовки текстур и анализа мира.
Затем открывается карта и строка состояния выбранного мира/слоя:

```text
CublayCraft-Nether · Рендер · Готово 7599 из 229780 тайлов (3.3%) · Осталось 222181 тайлов · Осталось ~222 мин
```

Состояние опрашивается каждые 2 секунды, тайлы обновляются примерно раз в
15 секунд и по завершении. До создания обзорных тайлов часть карты может быть
пустой; готовые подробные участки появляются по мере рендера. ETA приблизительное,
до первых завершённых тайлов показывается «—». Счётчик включает подробные и
обзорные тайлы текущего плана, поэтому не равен числу чанков.
После обычного прерывания показывается «Прервано», после ошибки — «Ошибка»;
при аварийном убийстве процесса через 90 секунд без heartbeat появляется
«Нет обновлений — возможно, рендер прерван». После завершения сайт остаётся
доступным, пока работает HTTP-сервер. Параметр `webprogress = False` отключает статус.

Если Nginx/CDN кэширует всё, отключите кэш для `/render-progress.json`,
`/index.html` и корня сайта; для JS/CSS и тайлов учитывайте query string.
Для долгого рендера запускайте его в `tmux` или службе: закрытие SSH/Ubuntu-терминала
может остановить запущенные в нём процессы.

Подробности: [сборка и ограничения](BUILD_AND_RUN_RU.md),
[проверенный запуск WSL](WSL_RUN_RU.md), [анализ исходников](ANALYSIS_RU.md),
[пример конфигурации](example_config.py). Лицензия — [GPL](COPYING.txt).
За основу взяты [оригинальный Overviewer](https://github.com/overviewer/Minecraft-Overviewer)
и [форк GregoryAM-SP](https://github.com/GregoryAM-SP/The-Minecraft-Overviewer).

---

Ниже сохранена исходная документация форка. Для этой доработанной версии
используйте команды выше и русскую инструкцию.

![Overviewer](https://gregoryam.com/assets/img/assets/overviewer-thumbnail.webp)
[![Unit tests](https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/actions/workflows/ci.yml)
<br><strong>Works with Minecraft Java Edition v1.2.1 - v26.2</strong>
<hr>

### [Python 3.10+](https://www.python.org/downloads/) Required

<hr>

### (Example Map)<br> [Overviewer Debug World Render](https://overviewer.gregoryam.com/ov_render/)

<hr>

### What is The Minecraft Overviewer?
The Minecraft Overviewer is a command-line tool for rendering high-resolution maps of Minecraft Worlds.\
It generates a set of static HTML Image files and uses LeafletJS to display an interactive map.

While The Minecraft Overviewer was in active development for nearly a decade by the original developers, they have stopped development; leading to the community to take over the project and work to continue development.

## The Minecraft Overviewer includes:
- Day / Night Lighting
- Cave Rendering
- Mineral Overlays
- Many Plugins for more features!

## The Minecraft Overviewer Codebase:
Mostly written in Python with critial sections written in C as an extension module.

## Documentation
You can visit [docs.overviewer.org](https://docs.overviewer.org) to view the entire documentation of The Minecraft Overviewer.

This Repo will soon have a Wiki that will better reflect the documentation.

## Disclaimer!
For large maps, there is a lot of data to parse through the process. If your world is very large, expect the initial render to take at least an hour to render, or possibly even days.

Since Minecraft Maps can be infinite, the maximum time this could take is also infinite.\
**Keep this in mind for large worlds.**

## Running Overviewer

While Overviewer can be run directly from the command line, it's generally easiest to set up a configuration file and running script once that you can then use whenever you want to update your map, so that's what we'll go over here. It's worth noting that this guide is designed for use on Windows computers.

**Step 1:** Download the latest zipped release from [Github](https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/releases).

**Step 2:** Download the sample [configuration and batch files](https://josh47.com/i/SampleOverviewerFiles.zip).

**Step 3:** Unzip the downloaded files. You can put them wherever you like on your system.

**Step 4:** Edit *RunOverviewer.bat* using your favorite text editor (Notepad works great). 

 - Change D:\Path\To\overviewer-version to the path where you extracted the release zip.
 - Change D:\Path\To\Config\ConfigOverviewer.txt to the path where you put the configuration file, and change the name if necessary.
 - Change D:\Path\To\OutputLog\log.txt to wherever you'd like the log file to be saved. You can rename log.txt to something else if you'd like, or remove the path and the ">>" entirely if you prefer the output to go to your terminal instead.
 - Save the file.

**Step 5:** Edit *ConfigOverviewer.txt*

 - Replace C:/Users/YourPathHere with the path to your world file.
 - Replace D:/YourPathHere with the path to where you want the map's files to be.
 - Add, remove, or edit any renders you'd like to change. The sample comes with four smooth-lighting renders from the overworld, one for each isometric perspective. For more info on the config file, visit [the docs](http://docs.overviewer.org/en/latest/config/). Overviewer supports the Nether, the End, and a cave view, though these are not included in the sample config.
 - Save the file.

**Step 6:** You're ready to run! Double-click the RunOverviewer.bat file to begin. It will open a terminal window, and then you can press the key directed to continue and start the render. As mentioned above, if this is the first time you're running the render, it could take hours or possibly even days. Don't worry, updating the map after the initial run is much faster.

**Step 7:** Once it completes, you can go to the folder you instructed it to place the output in and open "Index.html" to view the map. To share with others, you can give them the whole folder, or host it online!

**In the future:** To update your map, just double-click the RunOverviewer.bat file again. Overviewer will automatically check your world to find out where things have changed, and only update those parts of the map.

## Getting Help
A great place to start is the old [docs](http://docs.overviewer.org/en/latest/). They aren't being updated anymore, but since this repo's Wiki is still a work in progress, they're a great tool and nearly all the information in them is still accurate.

Another option is to reach out on the [Overviewer Discord](https://discord.gg/32Bz2yW)! There you can find a friendly, helpful community. Please read the rules in the \#Rules channel before messaging.

## Viewing the results
Within the output directory you've specified, you will find:
- Index.html (The render of your world)
- JavaScript (JS), Cascading Style Sheets (CSS) and PNG files.
- Directory: world-lighting (containing the generated chunk images)
- Directory: markers ( These markers can be used with GenPOI )

You can upload these files on a web server and let others view your map.

## Bedrock and other formats
The Minecraft Overviewer **only** supports the world format from the Java Edition of Minecraft.\
Minecraft Bedrock worlds are not supported.

Using a tool such as [Amulet](https://www.amuletmc.com/) to convert your Bedrock Worlds into Java Edition Worlds has been reported to work.\
But, the results may vary.
