# Advanced usage

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-advanced.md)

Settings that most people never need: the tool works without them.

## Limit the processors used

The tool spreads its work over every processor Docker lets it see: several images are decoded,
and the fingerprints of several files computed, at the same time. The first audit is faster, but
the computer may become sluggish meanwhile. `PYTHON_CPU_COUNT` makes the tool believe it has
fewer processors, for instance two:

```powershell
docker run --rm -it `
  -e PYTHON_CPU_COUNT=2 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene audit
```

The audit takes longer; the rest of the computer stays responsive.

- **`--cpus=2` alone is not enough.** Docker then limits the processor time, but the tool still
  sees every processor and starts as many workers, which share those two processors. Use
  `PYTHON_CPU_COUNT`, alone or together with `--cpus`.
- **With Docker Desktop**, Docker itself only sees the processors given to WSL 2 (`processors=`
  in `%UserProfile%\.wslconfig`, see
  [Microsoft's documentation](https://learn.microsoft.com/windows/wsl/wsl-config)): a limit for
  every container, not only this one.
- `PYTHON_CPU_COUNT` is a setting of Python (3.13 and later), the language the tool is written
  in, not of media-hygiene: it has no `config.toml` equivalent
  ([Python's documentation](https://docs.python.org/3/using/cmdline.html#envvar-PYTHON_CPU_COUNT)).
