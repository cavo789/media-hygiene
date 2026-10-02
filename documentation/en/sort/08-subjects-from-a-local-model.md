# 8. Name the subjects with a local model

[Documentation](../README.md) › Sorting, step 8 · 🇫🇷 [Français](../../fr/sort/08-subjects-from-a-local-model.md)

Folders, dates and your rules ([step 6](06-write-down-what-you-know.md)) sort much of a family
collection. The photos left in folders that only hold a date (`July 2016`, `2019-04`, `DCIM`)
still lack a subject: a beach, a school show, works at home. A **vision model running on your
own computer** can look at them and say. This step is **optional**: without it, everything
else works the same.

## What leaves your computer

The photos are sent to the model server you configure, and only there. Run that server on your
own computer ([Ollama](https://ollama.com)), and no photo leaves it. Nothing is ever sent
unless `config.toml` holds a `subject` rule **and** a `model`: the tool never calls a model on
its own.

## Install a vision model

1. Install [Ollama](https://ollama.com) on your computer.
2. Download a model that **sees images**, for instance `ollama pull qwen2.5vl:7b`. A larger
   model describes better, and more slowly. A model without the *vision* capability is refused
   by name.
3. Let the container reach it:
   - **Docker Desktop** (Windows, macOS): nothing to do, `host.docker.internal` is the
     computer.
   - **Docker Engine** (Linux, WSL without Docker Desktop): add
     `--add-host=host.docker.internal:host-gateway` to `docker run`, and start Ollama with
     `OLLAMA_HOST=0.0.0.0` so that it listens beyond `127.0.0.1`.

Keep `/cache` mounted ([start, step 2](../start/02-keep-the-cache.md)): the descriptions are kept
in its index, and a photo is never described twice.

## Write the rule

In `config.toml`, set the model in `[classify.ai]`, then add a `subject` rule with the
categories the model may choose from:

```toml
[classify.ai]
url = "http://host.docker.internal:11434"
model = "qwen2.5vl:7b"

[[classify.rules]]
name = "Existing folders"
match = "existing_folder"

# … your date, path and camera rules …

[[classify.rules]]
name = "Subject"
match = "subject"
categories = ["Holidays and outings", "School", "Sport and leisure", "Home and works",
              "Animals", "Nature and landscapes"]
```

- The model chooses **one** of the `categories`, or none: a photo that fits none stays to the
  other rules.
- It only speaks where **stronger signals are silent**: a file already decided by a folder, a
  date, a path, a camera or a kind is never sent. Place the rule low in the list.
- Occasions are better told by dates: the model sees a cake, not a birthday. Write the
  birthdays and Christmas as `calendar` rules ([step 6](06-write-down-what-you-know.md#dates)).
- Screenshots and documents come from the `kind` rule: the model is unreliable there.
- Avoid a "Family" or "Portraits" category: the model would put most photos in it.

## A few photos per event

Describing a photo takes seconds: about 4 seconds on one graphics card with a large model. At
that pace, 10,000 photos would take 11 hours. So each **event** (photos taken close together,
[step 4](04-classify.md#read-the-result)) is represented by a few **samples**,
`samples_per_event` (3 by default): the sharpest photos, spread over its span. The other photos
and the videos of the event follow them. A lone photo answers for itself.

The **confidence** comes from the samples, never from what the model says of itself:

| Samples | Proposal |
|---|---|
| All agree (3 of 3) | Sure: `year/category` |
| A majority (2 of 3), or one photo alone | To check: `year/To check/category` |
| Most fit no category | No subject: the other rules decide |

`per_photo = true` on the rule describes **every** photo instead, each with its own category:
much longer. Photos smaller than `min_edge` pixels (512 on their shorter side) are never sent:
on a thumbnail, the model invents details.

## Measure first: `--sample`

Before a long run, describe a few random photos and read the cost:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene classify --sample 50
```

On Docker Engine, add `--add-host=host.docker.internal:host-gateway` after `-it`.

```text
412 events or lone photos have no stronger signal than their subject: 1,236 photos
answer for them.
1,236 of them to describe with qwen2.5vl:7b, about 1 h 32 min.
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Photo                           ┃ Description                       ┃ Category             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ C:\Photos\2019-04\IMG_0412.jpg  │ Children singing on a school      │ School               │
│                                 │ stage.                            │                      │
│ …                               │ …                                 │ …                    │
└─────────────────────────────────┴───────────────────────────────────┴──────────────────────┘
Per photo: 3.6 s to describe, 0.4 s to map.
A full run would describe 1,186 more photos: about 1 h 19 min.
💡 Nothing is proposed by --sample: run classify without it.
```

The table shows whether the categories fit your photos; the time decides when to run. The
descriptions are written in English whatever the interface language: the model reads them, you
do not have to. The sample's descriptions are kept: the full run does not describe them again.

## The long run, never in the way

- Before describing, `classify` prints how many photos it will send and the estimated time.
  Above `confirm_above` photos (200 by default), it **asks first**; `--yes` does not ask.
  Refused, or without a terminal, it uses the cache only.
- **Ctrl+C** stops between two photos: what is described is kept, and the next `classify`
  starts where this one stopped.
- `--no-describe` asks the model **nothing new**: the `subject` rule reads the descriptions
  already in the cache. Change the categories or the other rules and run again in seconds; the
  events not described yet stay to the other rules.

Changing the `categories` does not describe anything again: the descriptions do not depend on
them. Only the second, text-only step runs again: choosing a category for each description,
many at a time.

## All the settings

| `[classify.ai]` | Default | Meaning |
|---|---|---|
| `url` | `http://host.docker.internal:11434` | The Ollama server. |
| `model` | empty | The vision model. Empty: no photo is ever sent. |
| `map_model` | empty | A text model choosing the categories; empty: `model`. |
| `samples_per_event` | 3 | Photos describing each event. |
| `min_edge` | 512 | Smaller photos (shorter side, in pixels) are never sent. |
| `confirm_above` | 200 | Above this many photos to describe, ask first. |
| `concurrency` | 1 | Photos described at once: one suits one graphics card. |
| `image_edge` | 768 | The longer side of the picture sent, in pixels. |
| `timeout_seconds`, `retries` | 180, 2 | Patience with a slow or busy server. |
| `batch_size` | 20 | Descriptions per category call. |
| `seconds_per_photo` | 4.5 | The estimate until this computer has described a photo. |

In an environment variable, the table is one JSON object:
`-e MEDIA_HYGIENE_CLASSIFY__AI='{"model": "qwen2.5vl:7b"}'`.

---

← [7. Sort](07-sort.md) · [Documentation](../README.md)
