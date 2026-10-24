# Сборка и запуск доработанного Overviewer

Для Ubuntu 20.04 с Python 3.8 используйте готовый архив из GitHub Releases:
он содержит собственный Python и нативный модуль. Инструкция:
[deploy/ubuntu20/START_HERE_RU.md](deploy/ubuntu20/START_HERE_RU.md).
Ниже — сборка обычных исходников с современным Python.

Быстрый запуск, пример конфигурации и просмотр карты во время генерации:
[README.md](README.md). Веб-прогресс включён по умолчанию (`webprogress = True`),
HTTP-сервер запускается отдельно. Для уже работающего Nginx достаточно раздавать
тот же outputdir; отключите кэш для `render-progress.json`, index.html и корня сайта.

База: GregoryAM-SP/The-Minecraft-Overviewer, commit
`4a8c8fa00d3593668a2e31d77538f7597fb4d3e9`, полученный 24 октября 2026.
Это исходники для Minecraft **Java Edition**, не Bedrock.

Параметры мира, размер карты, примеры ручных маркеров и иконок:
[CONFIG_RU.md](CONFIG_RU.md). Для новой установки используйте полный архив или
текущий репозиторий. При установке архива только изменений список `remove` в
`delivery-manifest.json` перечисляет устаревшие файлы форка для удаления;
`git apply` выполняет эти удаления вместе с патчем.

## Что входит в поставку

* `Overviewer-modern-source.zip` — исходники целиком. Распаковать и собрать.
* `Overviewer-changed-files.zip` — только заменяемые/новые файлы с сохранением путей.
* `Overviewer-changes.patch` — текстовый патч относительно указанного commit.
* `ANALYSIS_RU.md` — сравнение репозиториев, устройство доработок и границы проверки.

Достаточно взять **именно указанную ревизию форка** и распаковать поверх неё
`Overviewer-changed-files.zip`. C-файлы не менялись: заменяются Python-файлы,
JS/CSS веб-карты, добавляются пять модулей и вспомогательные проверки. Полный список — в
`delivery-manifest.json`. Для другой ревизии форка необходимо проверить diff,
поскольку простая замена файлов может затереть изменения автора.

Заменяемые рабочие файлы:

```text
overviewer.py
overviewer_core/dispatcher.py
overviewer_core/files.py
overviewer_core/textures.py
overviewer_core/tileset.py
overviewer_core/world.py
overviewer_core/assetmanager.py
overviewer_core/settingsDefinition.py
overviewer_core/aux_files/genPOI.py
overviewer_core/util.py
overviewer_core/data/js_src/util.js
overviewer_core/data/web_assets/overviewer.css
```

Обязательные новые модули:

```text
overviewer_core/memorylimit.py
overviewer_core/renderjournal.py
overviewer_core/resource_models.py
overviewer_core/tilelayout.py
overviewer_core/webprogress.py
overviewer_core/palette26.py
```

Файлы `test/*` и `contrib/verify_modern_render.py` нужны для проверок, а не
для обычного запуска. Версия нашей сборки — `26.3+resume.5`; это номер сборки,
а не гарантия поддержки произвольных будущих форматов Minecraft.
В manifest `sha256` относится к байтам файлов архива, `sha256_lf_utf8` — к
UTF-8-тексту после нормализации CRLF/LF; второе удобно при установке через
`git apply`, поскольку Git может менять окончания строк.

В архивах нет Minecraft JAR, текстур Mojang, виртуального окружения и Windows DLL.
Нужен ваш официальный клиентский JAR нужной версии. Серверный JAR не подходит:
в нём нет полного набора клиентских текстур/моделей.

## Linux: Ubuntu 24.04 и более новые совместимые системы

Для ограничения RAM требуются **cgroup v2, systemd 254+ и рабочая пользовательская
сессия systemd**. Сборка/рендер без `--memory-limit` не требуют systemd.

Если используется архив целых исходников:

```bash
unzip Overviewer-modern-source.zip
cd minecraft-overviewer-modern
```

Если используется только архив изменений:

```bash
git clone https://github.com/GregoryAM-SP/The-Minecraft-Overviewer.git minecraft-overviewer-modern
cd minecraft-overviewer-modern
git checkout --detach 4a8c8fa00d3593668a2e31d77538f7597fb4d3e9
unzip -o ../Overviewer-changed-files.zip
```

Установка и сборка (проверены Python 3.12 на Windows и 3.14 в Ubuntu WSL):

```bash
sudo apt-get update
sudo apt-get install -y git build-essential python3-dev python3-venv unzip
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0' 'numpy==2.3.5' 'Pillow==12.3.0' requests networkx pytest pytest-mock

PILLOW_VERSION="$(python -c 'import PIL; print(PIL.__version__)')"
git clone --depth 1 --branch "$PILLOW_VERSION" https://github.com/python-pillow/Pillow.git ../overviewer-pillow-headers
export PIL_INCLUDE_DIR="$(cd ../overviewer-pillow-headers/src/libImaging && pwd)"
python setup.py build
python -m pytest -q
```

Нужны заголовки **той же версии Pillow**, которая установлена в `.venv`.
Используйте `setup.py build`: он также создаёт `primitives.h`. Один только
`build_ext` из чистого checkout недостаточен.

## Конфигурация

Создайте `render_config.py`, заменив пути:

```python
worlds['main'] = '/srv/minecraft/world-snapshot'
outputdir = '/srv/www/minecraft-map'

renders['overworld'] = {
    'world': 'main',
    'dimension': 'overworld',
    'title': 'Мой мир',
    'rendermode': 'smooth_lighting',
    'texturepath': '/srv/minecraft/assets/26.3.jar',
}
```

Для мира 1.21.5 можно использовать официальный `1.21.5.jar`; его генерация
проверена отдельно. Для 26.3 используйте `26.3.jar`. Для более новых версий —
соответствующий клиентский JAR. Лучше указывать `texturepath` явно, чтобы
автоматический поиск не выбрал ресурсы другой установленной версии.

Первое обновление **уже существующей карты**, на которой новые блоки раньше
были пропущены, требует однократного полного рендера: сохранённые картинки сами
от установки новых исходников не изменятся.

```bash
python overviewer.py -c render_config.py -p 4 --memory-limit 8G --forcerender
```

После успешного завершения используйте обычное обновление:

```bash
python overviewer.py -c render_config.py -p 4 --memory-limit 8G
```

`-p 4` задаёт число работников. `--memory-limit 8G` ограничивает **сумму памяти
процессов рендера** (координатор, менеджер, работники, дочерние процессы), а не
8 GiB каждому. Swap для этой группы запрещён. Размер — положительное число
байтов либо целые `K`, `M`, `G`, `T`, например `6144M`.

После переноса процесса в cgroup программа читает реальный `memory.max` и
`memory.swap.max`; если лимит не установлен, она отказывается начинать рендер.
При успехе в логе есть `Verified total cgroup memory cap`.

При достижении лимита ядро может завершить группу рендера. Прогресс остаётся
на диске. Повторите запуск с меньшим `-p` либо увеличенным разумным лимитом.
Оставьте память ОС и Minecraft-серверу; этот лимит не резервирует RAM и не
ограничивает чужие процессы. Служебный Python-процесс запуска остаётся вне
scope; основные данные мира/текстуры и работники загружаются внутри группы.
Лимит не обещает отсутствия глобального OOM по другим
причинам. Без `--memory-limit` жёсткого ограничения нет.

Проверка возможностей сервера:

```bash
systemd --version
cat /sys/fs/cgroup/cgroup.controllers
systemctl --user status
```

В списке контроллеров должен быть `memory`. При отсутствии user bus или прав
на контроллер исправьте настройку сессии/сервера: программа не переключается
на незаметный запуск без ограничения.

## Продолжение после прерывания

Просто повторите команду с той же конфигурацией и тем же каталогом результата:

```bash
python overviewer.py -c render_config.py -p 2 --memory-limit 8G
```

Число работников и лимит памяти можно менять между запусками.
Признак продолжения в логе:

```text
Resuming overworld: ... pending tiles; skipping chunk/tile scan.
```

В каталоге каждого рендера сохраняется `.overviewer-resume-0.sqlite3`;
при нескольких crop-зонах используются отдельные номера. Не удаляйте эти
файлы и SQLite rollback-журналы рядом с ними. После успешной публикации
метаданных журнал удаляется автоматически. Одновременный запуск двух
координаторов в один outputdir запрещён файловой блокировкой.

Изменение глубины карты также журналируется в `.overviewer-layout.json`.
После прерывания перемещения каталогов продолжаются с незавершённого шага;
старые поддеревья удаляются только после фиксации новой структуры. Этот файл
сохраняется после успешного рендера и хранит фактическую глубину дерева;
не удаляйте его отдельно от карты.

При аварийном завершении возможно повторение последней неподтверждённой
пачки (обычно до 128 заданий плюс задания в работе). Подтверждённые ранее
пачки повторно не рендерятся. Подготовка текстур и чтение списка регионов
всё равно происходят при старте; пропускается дорогой обход чанков/тайлов
при восстановлении готового плана.

Первичный анализ и построение плана должны однажды завершиться. Если процесс
оборван **до** записи готового плана, этот этап придётся повторить. Старый
Overviewer без этого патча не создавал SQLite-план: его прерванный запуск
нельзя восстановить задним числом с такой же скоростью.

Обычные сохранения мира не отменяют сохранённый план. После восстановления
сохраняется его исходная временная отметка: изменения мира после его
сканирования, в том числе новые чанки за прежними границами, подхватит
**следующее обычное обновление**. Для согласованного результата используйте
неизменяемый снимок мира. После восстановления мира из старой резервной копии
или замены мира по тому же пути используйте явную повторную проверку/рендер.

Изменение настроек рендера, исходников или ресурсов отменяет быстрый resume:
сначала выполняется новый анализ. Для намеренного сброса плана:

```bash
python overviewer.py -c render_config.py -p 2 --memory-limit 8G --discard-resume --check-tiles
```

Не добавляйте `--discard-resume` в обычный скрипт запуска: он намеренно
удаляет сохранённый прогресс. Не держите `--forcerender` в обычном расписании:
после успешно законченного запуска он действительно начинает полный рендер.

SQLite-журнал и тайлы должны лежать на файловой системе с корректными
блокировками и atomic replace. Проверки выполнялись на локальном NTFS;
для Linux предпочтительна локальная ext4/XFS. Работа на конкретном NFS/CIFS
сервере не подтверждена.

## Windows

Нужны Python 3.12 x64 и Visual Studio 2022 Build Tools с C++/Windows SDK.
Команды PowerShell в каталоге исходников:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0' 'numpy==2.3.5' 'Pillow==12.3.0' requests networkx pytest pytest-mock
$pillowVersion = python -c 'import PIL; print(PIL.__version__)'
git clone --depth 1 --branch $pillowVersion https://github.com/python-pillow/Pillow.git ..\overviewer-pillow-headers
$env:PIL_INCLUDE_DIR = (Resolve-Path ..\overviewer-pillow-headers\src\libImaging).Path
python setup.py build
python -m pytest -q
python overviewer.py -c render_config.py -p 2
```

Resume и рендер работают на Windows. `--memory-limit` в этой реализации
поддерживает **Linux**, на Windows он выдаст ошибку до загрузки мира.
Пример путей в Windows-конфигурации: `C:/Minecraft/world` и `D:/Maps/output`.

## Воспроизводимая проверка

Проверка дополнительных моделей из ваших JAR (Linux):

```bash
OVERVIEWER_TEST_JARS='/path/1.21.5.jar:/path/26.3.jar' python -m pytest -q test/test_resource_models.py
```

В PowerShell переменная использует разделитель `;`.
Проверка создаёт каждый зарегистрированный вариант модели и проверяет,
что он не пустой; это не сравнение со скриншотом игрового клиента.

Синтетический Anvil-мир и тест настоящего прерывания:

```bash
python contrib/verify_modern_render.py /path/26.3.jar /tmp/ov-check
python contrib/verify_modern_render.py /path/26.3.jar /tmp/ov-check --crash-after 3
# Предыдущая команда специально завершится с кодом 23.
python overviewer.py -c /tmp/ov-check/map.py -p 1
```

Вторая команда читает уже созданный мир. Не запускайте первую команду снова
между прерыванием и восстановлением: она создаёт новый тестовый мир.
На удалённый сервер пользователя код из этой поставки не устанавливался.
Linux-сборка, реальный рендер и изолированный OOM cgroup проверены в Ubuntu
26.04 WSL 2; результаты и повторный запуск — [WSL_RUN_RU.md](WSL_RUN_RU.md).
