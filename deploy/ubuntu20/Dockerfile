FROM ubuntu:20.04 AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY . /src
RUN python3 deploy/ubuntu20/download_runtime.py /opt/portable-python
RUN /opt/portable-python/bin/python3 -m pip install --only-binary=:all: \
    -r deploy/ubuntu20/requirements.lock.txt
RUN CC=gcc CXX=g++ PIL_INCLUDE_DIR=/src/deploy/ubuntu20/pillow_include \
    /opt/portable-python/bin/python3 setup.py build
RUN /opt/portable-python/bin/python3 -c "from pathlib import Path; assert all(any(Path('build').glob('lib*/'+name+'.py')) for name in ('overviewer_cache_policy','overviewer_worker_start'))"
RUN /opt/portable-python/bin/python3 -m pip install --target=/tmp/testdeps pytest pytest-mock && \
    PYTHONPATH=/tmp/testdeps /opt/portable-python/bin/python3 -m pytest -q
ARG SOURCE_REVISION=unknown
RUN /opt/portable-python/bin/python3 deploy/ubuntu20/build_artifact.py \
    --source /src --runtime /opt/portable-python --output /out --revision "$SOURCE_REVISION"
RUN /out/CublayCraft-Overviewer/overviewer.py --version
RUN /opt/portable-python/bin/python3 deploy/ubuntu20/make_cache_hotfix.py /out/fix_memory_cache.py
RUN /opt/portable-python/bin/python3 deploy/ubuntu20/make_start_hotfix.py /out/fix_start_workers.py
FROM scratch AS artifact
COPY --from=build /out/CublayCraft-Overviewer-Ubuntu20.04-x86_64.tar.gz /
COPY --from=build /out/CublayCraft-Overviewer-Ubuntu20.04-x86_64.tar.gz.sha256 /
COPY --from=build /out/fix_memory_cache.py /
COPY --from=build /out/fix_start_workers.py /
