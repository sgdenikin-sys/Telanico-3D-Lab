# Telanico 3D Lab

Один репозиторий, одна рабочая ветка **main**, одна публикация через GitHub Pages.
Исходники, Blender/Godot, тесты и готовый Web runtime находятся здесь.
Все изменения коммитятся непосредственно в main. Feature/recovery/release-ветки
и Pull Request для обычной работы не нужны.

Начинайте с [рабочего порядка](docs/PROJECT_WORKFLOW.md).

- `godot/` — игра; `blender/` — генераторы карты.
- `tools/` — существующие сборка и проверки.
- `build/` — локальные игнорируемые сборки, кэш и логи.
- `site/` — только проверенный Web runtime для публикации.
- `tools/release.json` — исходный SHA, результаты проверки и SHA-256 runtime.
- `.github/workflows/publish.yml` — единственный активный workflow.

Целевой URL: https://sgdenikin-sys.github.io/Telanico-3D-Lab/
В Pages должен быть выбран Source → GitHub Actions. Приватный репозиторий
тоже подходит, если тариф аккаунта разрешает Pages; менять видимость необязательно.
До подтверждённого запуска нового URL предыдущая V2.2 остаётся доступна по
https://sgdenikin-sys.github.io/Telanico-3D-Web/ .

В `site/` подготовлен проверенный UI-патч V2.2, исходники `c9ef4eb`: компактные
окна, канонический GIF Assistant, круглый циферблат, размер и скорость персонажа ×3.
[Проверки патча](docs/v2-2/UI_PATCH_2026-10-23.md).
Физический iPhone Safari отдельно не проверен.

Старые инструкции и workflows сохранены в `docs/history/` для истории;
они не являются текущим рабочим процессом.
