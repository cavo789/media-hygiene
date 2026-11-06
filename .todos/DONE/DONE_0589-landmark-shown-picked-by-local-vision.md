# 0589 — 🤖 The building a photo shows, picked by a local vision model

- **Priority**: Low
- **Batch**: places
- **Depends**: 0545
- **Files**: `src/media_hygiene/geo/landmarks.py`, `src/media_hygiene/index/`

## Why

Split from 0545 (maintainer, 2026-11-05). The GPS gives the nearest named monument within
`NEAR_M`: a cathedral photographed from 400 m gets nothing, and a photo taken next to a castle,
facing away, gets the castle.

## What

An opt-in 🤖 local model (Ollama, like `mh tags`) chooses among the GeoNames/OSM landmarks within
about 1 km the one the picture shows: a short list to pick from, never a free guess, offline. It
writes into the storage of 0545, source recorded; a name typed by hand (0489) always wins.

## Done when

On synthetic candidates, the chosen landmark is stored with its source and found by search; with
no model available, nothing changes. Precision is measured on real photos by the maintainer.
