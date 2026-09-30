# Utilisation avancée

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-advanced.md)

Des réglages dont la plupart des gens n'ont jamais besoin : l'outil fonctionne sans eux.

## Limiter les processeurs utilisés

L'outil répartit son travail sur tous les processeurs que Docker lui laisse voir : plusieurs
images sont décodées, et les empreintes de plusieurs fichiers calculées, en même temps. Le
premier audit va plus vite, mais l'ordinateur peut devenir lent pendant ce temps.
`PYTHON_CPU_COUNT` fait croire à l'outil qu'il a moins de processeurs, par exemple deux :

```powershell
docker run --rm -it `
  -e PYTHON_CPU_COUNT=2 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr audit
```

L'audit prend plus de temps ; le reste de l'ordinateur reste réactif.

- **`--cpus=2` seul ne suffit pas.** Docker limite alors le temps de processeur, mais l'outil voit
  toujours tous les processeurs et lance autant de tâches, qui se partagent ces deux processeurs.
  Utilisez `PYTHON_CPU_COUNT`, seul ou avec `--cpus`.
- **Avec Docker Desktop**, Docker lui-même ne voit que les processeurs accordés à WSL 2
  (`processors=` dans `%UserProfile%\.wslconfig`, voir la
  [documentation de Microsoft](https://learn.microsoft.com/fr-fr/windows/wsl/wsl-config)) : une
  limite pour tous les conteneurs, pas seulement celui-ci.
- `PYTHON_CPU_COUNT` est un réglage de Python (3.13 et suivants), le langage dans lequel l'outil
  est écrit, pas de media-hygiene : il n'a pas d'équivalent dans `config.toml`
  ([documentation de Python](https://docs.python.org/fr/3/using/cmdline.html#envvar-PYTHON_CPU_COUNT),
  non traduite pour ce réglage).
