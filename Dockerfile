# syntax=docker/dockerfile:1.19
#
# media-hygiene — the shipped image. Build: `docker build --tag media-hygiene .`
# Run:  docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" media-hygiene audit
# The development environment is built by .devcontainer/Dockerfile, never by this file.

# Base image pinned by digest: this is what users run on their photos.
ARG PYTHON_IMAGE=python:3.14-slim-trixie@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2
ARG UV_VERSION=0.12.19
# FFmpeg source release, pinned by the SHA-256 of its tarball. When bumping the version, check
# the tarball's .asc signature against the FFmpeg release key
# (FCF9 86EA 15E6 E293 A564 4F10 B432 2F04 D676 58D8) before trusting its new SHA-256.
ARG FFMPEG_VERSION=9.0.2
ARG FFMPEG_SHA256=8c3850283eb25fa026482078a04051e0be17347b09ef81a0849bec15a96e002e
# Demuxers per video extension: mov (3g2 3gp m4v mov mp4), m4v (raw MPEG-4 video named .m4v),
# matroska (mkv webm), avi, flv, mpegts (m2ts mts ts), mpegps and mpegvideo (mpeg mpg), asf (wmv).
ARG VIDEO_DEMUXERS=mov,m4v,matroska,avi,flv,mpegts,mpegps,mpegvideo,asf

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# --- ffprobe: only what scan/video_check.py asks of it ---------------------------------------
# The tool only asks whether a video container opens, and which streams it holds: the demuxers
# of the video extensions it knows, the file protocol and zlib (compressed headers) are enough.
# No decoder, no network, no other library: a few MB instead of 141 MB for a full static build.
FROM ${PYTHON_IMAGE} AS ffprobe

ARG FFMPEG_VERSION
ARG FFMPEG_SHA256
ARG VIDEO_DEMUXERS

# Discarded stage: the compiler never reaches the image; the base is pinned by digest and the
# FFmpeg source by checksum.
# hadolint ignore=DL3008
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev make nasm xz-utils zlib1g-dev

ADD --checksum=sha256:${FFMPEG_SHA256} \
    https://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.xz /tmp/ffmpeg.tar.xz

WORKDIR /tmp/ffmpeg
RUN tar -xf /tmp/ffmpeg.tar.xz --strip-components=1 && \
    ./configure \
        --disable-everything --disable-autodetect --disable-asm --disable-doc \
        --disable-debug --disable-network --disable-programs --enable-ffprobe \
        --disable-avdevice --disable-avfilter --disable-swscale --disable-swresample \
        --enable-small --enable-zlib --enable-protocol=file \
        --enable-demuxer="${VIDEO_DEMUXERS}" && \
    make -j"$(nproc)" ffprobe && \
    strip ffprobe

# --- ffmpeg: only what scan/keyframes.py asks of it ---------------------------------------
# Decode one frame at a given moment, turn it upright, shrink it to a grayscale square and
# write its raw pixels to a pipe. The same demuxers as ffprobe, the decoders of phone, camera
# and older PC videos, the scale/format/rotation filters; assembly kept (decoding speed).
# No AV1 (its decoder needs an external library): such a video is simply not fingerprinted.
FROM ffprobe AS ffmpeg

ARG VIDEO_DEMUXERS

RUN make distclean && \
    ./configure \
        --disable-everything --disable-autodetect --disable-doc --disable-debug \
        --disable-network --disable-programs --enable-ffmpeg \
        --disable-avdevice --disable-swresample \
        --enable-small --enable-zlib --enable-protocol=file,pipe \
        --enable-demuxer="${VIDEO_DEMUXERS}" \
        --enable-decoder=h264,hevc,mpeg4,mpeg1video,mpeg2video,mjpeg,vp8,vp9,h263,flv \
        --enable-decoder=msmpeg4v1,msmpeg4v2,msmpeg4v3,wmv1,wmv2,wmv3,vc1,prores \
        --enable-parser=h264,hevc,mpeg4video,mpegvideo,mjpeg,vp8,vp9,h263,vc1 \
        --enable-filter=scale,format,transpose,hflip,vflip,null \
        --enable-encoder=rawvideo --enable-muxer=rawvideo && \
    make -j"$(nproc)" ffmpeg && \
    strip ffmpeg

# --- builder: resolve the locked dependencies, then install the project as a wheel ---------
FROM ${PYTHON_IMAGE} AS builder

COPY --from=uv /uv /usr/local/bin/uv

# The virtual environment lives at the same path in both stages: its scripts hardcode it.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /src

# Dependencies first: this layer is only rebuilt when the lockfile changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# --- runtime: the interpreter, the virtual environment, ffprobe and ffmpeg — nothing else ---
FROM ${PYTHON_IMAGE} AS runtime

ARG VERSION=0.2.0
ARG APP_UID=1000
ARG APP_GID=1000

LABEL org.opencontainers.image.title="media-hygiene" \
      org.opencontainers.image.description="Find and safely clean duplicate photos and videos across folders and disks." \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.licenses="MIT"

# Avoid .pyc cache files from build-time pip/pre-commit invocations, and unbuffered stdout for
# any Python process run interactively in this container.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/opt/venv/bin:${PATH}

# Every mount point exists and belongs to the app user: a named volume mounted there for the
# first time inherits that ownership (e.g. -v media-hygiene-cache:/cache).
RUN groupadd --gid "${APP_GID}" app && \
    useradd --uid "${APP_UID}" --gid "${APP_GID}" --no-create-home --shell /usr/sbin/nologin app && \
    mkdir -p /data /config /journal /quarantine /reports /cache && \
    chown app:app /config /journal /quarantine /reports /cache

COPY --from=ffprobe /tmp/ffmpeg/ffprobe /usr/local/bin/ffprobe
COPY --from=ffmpeg /tmp/ffmpeg/ffmpeg /usr/local/bin/ffmpeg
COPY --from=builder /opt/venv /opt/venv

USER ${APP_UID}:${APP_GID}
WORKDIR /tmp

ENTRYPOINT ["media-hygiene"]
CMD ["--help"]
