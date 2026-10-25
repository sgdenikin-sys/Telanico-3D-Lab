# Settlements Hall Lite — separate mobile optimization experiment

## Baseline and scope
Current approved V2: **34,643 triangles**, 11 core glTF PBR materials, 2 independently
hinged doors with 100-degree opens, 4 morph-animated pieces of fabric, 4 clips.
Authoring source: `blender/scripts/build_settlements_hall.py`. The published V2
remains unchanged at `artifacts/settlements_hall/v2-animated/`.

The new generator option **`--quality lite`** alters only mesh construction
for a newly generated model and **does not overwrite** existing V2 assets by
default. It simplifies arch tessellation, drum/window repetition, dome rings and
ornament, roof seams, secondary facades, columns, small bevels, flag tessellation,
and optional paving microdetail. Never strip glass, doors, armatures/shape keys,
or the recognizable dome. Eleven materials and the exact four animation clips
remain mandatory. Retain the building's ivory/deep-teal/aged-brass style.

## How to build in a Blender-enabled Codex workspace
From repository root, preserving any existing changes:

```sh
blender -b --python-exit-code 1 --python blender/scripts/build_settlements_hall.py -- --quality lite --render
python tools/compare_settlements_hall_lod.py
python tools/validate_settlements_hall.py blender/generated/settlements_hall_lite/settlements_hall.glb
```

The first command writes a **separate** editable file, GLB, stats and rendered
previews to `blender/generated/settlements_hall_lite/`. It never writes
`godot/assets/generated/settlements_hall.glb` when using the default Lite
output directory. For all custom output directories specify `--quality lite`.

## Acceptance criteria and further work
1. **Target 15–20k triangles**, soft fallback ceiling **22k**. This is a target,
   **not a claimed measured result**; inspect numbers from the actual export.
2. Match landmark dimensions/recognizable silhouette within 12cm of V2. Keep
   front entrance, stairs, ribbed dome, wings, and transparent blue glass.
3. Preserve PBR distinctions between ivory stone, bronze/brass, blue roof metal,
   tinted glass, blue doors and fabric. Ensure transparent glass renders correctly
   in Godot Compatibility.
4. Independently opening/closing 100-degree doors and four looping flag fabric
   animations must survive *GLB reimport* in Godot 4.6.3.
5. Compare the V2 and Lite Hero/Front/Rear/Detail camera renders at equal scale.
   The mobile variant should read less busy, not collapse into toy-like blocks.
6. Verify Web/iPhone landscape visual read, loading, FPS and memory *before*
   calling the version mobile-ready. Browser emulation is not actual Safari.
7. If triangle budget or visual fidelity fails, make one targeted adjustment
   to the Lite preset and rerun only this model's checks (not whole-game tests).

## Delivery and publishing
Publish corrected `.blend`, `.glb`, four renders, animation demo and reports
under a new `artifacts/settlements_hall/v3-lite/` directory **only after**
successful build/validation. Do not rewrite V2 assets. The existing independent
Web viewer can load a ZIP or GLB; optionally stage the validated Lite GLB in
the dedicated public `Telanico-3D-Web/site/hall/` asset path, but **never modify
the root game release or main scene**. Do not rely on downloading private files
from public Actions, which previously failed 403. Do not add new infrastructure.

## V3 Lite — результат выполненной сборки

Готовая версия публикуется отдельно в
[`artifacts/settlements_hall/v3-lite/`](../../artifacts/settlements_hall/v3-lite/README.md).
V2, её опубликованные файлы, `godot/`, `site/` и настройки публикации игры не изменены.

| Показатель | V2 | V3 Lite |
| --- | ---: | ---: |
| Треугольники в экспортированном GLB | 34 643 | **19 816** |
| Вершины после экспорта | 53 673 | 28 754 |
| Размер GLB, байт | 2 093 408 | 1 112 284 |
| PBR-материалы | 11 | 11, полностью идентичны V2 |
| Меши / поверхности | 18 / 22 | 18 / 22 |
| Створки / анимируемые полотна / клипы | 2 / 4 / 4 | 2 / 4 / 4 |

Полигонов меньше на **42,8%**, GLB меньше на **46,9%**. Изменение общих
габаритов — максимум 3,2 см по глубине из-за мелкой окантовки площадки;
высота и ширина сохранены. Пустых треугольников нет.

Первый запуск исходного пресета дал 16 868 треугольников, но чрезмерно упрощал
купол и исключал один из экспортируемых материалов мощения. Одной направленной
корректировкой Lite восстановлены все фасадные окна и 24 колонны, 12 рёбер купола,
основные швы кровель и второй оттенок мощения. Купол использует 48 радиальных
сегментов и 10 вертикальных интервалов; сокращены мелкие профили, арочная
тесселяция, повторения верхнего барабана и мелкий орнамент.

### Сравнение изображений

В каталоге V3 находятся `comparison_hero.png`, `comparison_front.png`,
`comparison_rear.png`, `comparison_detail.png`: V2 слева, Lite справа,
одинаковый масштаб и одинаковые размеры исходных PNG. Отдельная проверка
загрузила камеры и три источника света из оригинального V2 `.blend` и подтвердила
совпадение всех семи объектов с Lite. Цвета и PBR-параметры всех одиннадцати
материалов дополнительно сравнены непосредственно в GLB.

Сохранены узнаваемый силуэт, пропорции, классические фасады, лестница, рисунок
главных рёбер и цветовая иерархия. На игровых ракурсах модель не стала блочной;
при близком рассмотрении видны более простые арки, меньше окон верхнего барабана
и мелкого декора. Это намеренные различия Lite, а не утверждение о побитово
одинаковом изображении. Парные рендеры доступны для самостоятельной оценки.

### Проверки Godot 4.6.3

В отдельном локальном проекте повторно импортирован именно Lite GLB:

- Обе створки открываются наружу на 99,99999°, неподвижность петель проверена;
  закрытие возвращает исходную позу.
- Все четыре полотна сохранили по три морф-цели, меняющиеся веса и бесшовный цикл.
- Все четыре клипа, раздельные движущиеся объекты, независимое проигрывание
  ветра и дверей, стекло с альфой 0,63 и пять простых коллайдеров проверены.
- Повторный экспорт сохранённого Lite `.blend` также сохранил геометрию,
  материалы и все клипы. Экспортёр распознаёт Lite-сцену и по умолчанию выбирает
  отдельный Lite-путь вместо пути V2.

Дополнительно выполнена **пиксельная проверка в Godot 4.6.3 Compatibility /
WebGL 2.0**, в Chromium со SwiftShader, в окне 844×390. Использована копия уже
имеющегося `site/index.js` / `site/index.wasm` с отдельным локальным asset-only
PCK. Исходные файлы игры не правились, ничего не публиковалось на игровом сайте.

Тот же импортированный материал стекла отображался над четырьмя цветными
квадратами и сравнивался с состояниями без стекла и с непрозрачным контролем.
Отношение цветового смещения составило **0,627–0,631**, соответствуя альфе 0,63;
фон действительно виден сквозь стекло. Сохранены три контрольных PNG. В том же
Web-runtime проверены позы дверей и всех четырёх полотен, сняты кадры V2 и Lite.

Программный рендер показал около 3 FPS для обоих вариантов. JS heap в этом
одном прогоне составлял приблизительно 52–54 МБ; счётчик native memory в Web
возвращает неподдерживаемый ноль. Замеры разделяют прогретый кэш и не являются
изолированным сравнением памяти или холодной загрузки. Они **не подтверждают
мобильную готовность**. Реальный iPhone/Safari и аппаратный GPU не проверялись.

### Файлы и воспроизведение

В V3 отдельно размещены `.blend`, `.glb`, четыре рендера, четыре пары сравнения,
GIF/MP4 с анимациями, нативные и визуальные JSON-отчёты и SHA-256. ZIP содержит
Lite-модель и самостоятельный Godot viewer; оригинальный V2 GLB в ZIP не включён,
чтобы загрузчики архивов однозначно выбирали Lite.

```sh
blender -b --python-exit-code 1 --python blender/scripts/build_settlements_hall.py -- --quality lite --render
python tools/compare_settlements_hall_lod.py
python tools/validate_settlements_hall.py blender/generated/settlements_hall_lite/settlements_hall.glb
python tools/compare_hall_lite_renders.py
blender -b --python-exit-code 1 --python blender/scripts/render_settlements_hall_demo.py -- --glb blender/generated/settlements_hall_lite/settlements_hall.glb --frames work/hall-v3-animation-frames
python tools/package_settlements_hall_lite.py
```

Последний шаг выполняется после нативных и визуальных проверок. Визуальный
fixture — `tools/hall_lite_visual_qa.gd`, runner — `tools/check_hall_lite_visual.py`.
Они рассчитаны на отдельный scratch-проект `work/hall-v3-godot/` и подготовленный
QA PCK `work/hall-v3-web/`, а не на запуск основной игры. Копирование существующего
движка и `--export-pack Web` не требует установки шаблонов или новой инфраструктуры.
