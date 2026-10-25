# Рабочий порядок: main → Pages

Daylight V2 published: source `d9d6f2cb2bb24380da62bdeac5bcdaf46c604afd`, Web
`21eda739ab8c7bbcafdc3444e7b4954f1427b3f3`, Pages **40246308379 (success)**.
Owner lighting settings exported unchanged; HTTPS hashes and desktop/touch
opening passed. Overview: public `site/evidence/daylight-v2-d9d6f2c/overview.png`.


Последняя публикация terrain/lighting fix: source `ae482c02f709eefebd1e5a8b4f9d357cf51a12ac`,
Web commit `cbebf3c928b836dc2a577f0ba8b7a8c5929308a5`, Pages **40244481981 (success)**.
HTTPS runtime hashes and desktop/touch opening passed; no story regression.
Screenshots: public `site/evidence/terrain-ae482c0/`.


## Фактически работающий путь — уточнение 23 октября

Владелец впоследствии потребовал использовать уже работавшую публикацию V2.2.
Разработка остаётся в Telanico-3D-Lab/main. Для текущего превью используется
существующий Telanico-3D-Web/main и pages.yml: stage/verify в Lab, перенос только
точного проверенного site/ и manifest, push Web/main, проверка HTTPS и реального
WebGL запуска после Pages. Не переносить исходники Blender/Godot в Web и не
запускать старый import-private-web.yml. Веток, PR, новых workflow и секретов
для этого не требуется.

Текущий адрес: https://sgdenikin-sys.github.io/Telanico-3D-Web/ .
Текущая публикация Operations Textured V3 + ground textures + NW sun:
source `8573f5afb5ef2efa4211ab0e87fa6effe818f67f`, public commit
`47de15f691cdd84a6217fac795ee98d531a98324`, Pages run **40242903933 (success)**.
HTTPS-хеши runtime и существующий desktop/touch opening прошли. Полный
сюжет не запускался по ограниченному scope владельца. Новый корпус повернут
из Z-up в Y-up на уровне экземпляра; исходный GLB сохранён. Шесть ground
albedo 512×512 с mipmaps; солнце с СЗ, тени на ЮВ. Hall 0.63 и герой 2.55
сохранены, карта и маршруты не менялись. Старое ожидание 3.0 в публичном
live-чеке исправлено на утверждённое 2.55. Детали и три PNG:
`docs/assets/OPERATIONS_DOME_GAME_INTEGRATION.md` и публичный
`site/evidence/operations-ground-8573f5a/`.

Последний прямой Lab запуск 40118100126 снова завершился до runner (runner_id=0,
steps=[]). Он ничего не тестировал и не публиковал; это инфраструктурный отказ,
не ошибка игры. Не повторять его как необходимое условие работающей публикации.
Цель перехода на прямой Lab Pages ниже пока не выполнена; /Telanico-3D-Lab/
не считать опубликованным. Эта поправка имеет приоритет над прежним планом ниже.


Решение владельца от 23 октября 2026: один репозиторий Telanico-3D-Lab,
все изменения непосредственно в main, публикация из него же. Этот документ
заменяет прежние инструкции о feature/recovery/release-ветках, обязательных PR,
приватных артефактах и публикации через Telanico-3D-Web.

## Каждый рабочий цикл

1. Прочитать AGENTS.md; проверить `git status` и актуальный remote main.
   Сохранить незакоммиченную работу. Не reset, force-push или чужие перезаписи.
2. Работать в main. Использовать имеющиеся инструменты, кэш и авторизацию.
   Не создавать новую ветку или PR без отдельной просьбы владельца.
3. Изменить нужный код и проверить затронутую функциональность. Если меняется
   сама игра, собрать Web и проверить точный результат существующими тестами.
4. После успешной сборки и браузерных проверок выполнить
   `python tools/stage_web_release.py`: он помещает runtime в `site/`,
   сохраняет предыдущее содержимое в игнорируемом `build/site-history/`
   и обновляет `tools/release.json`. Другой клон/репозиторий не нужен.
5. `python tools/verify_release.py`, затем commit и push в main.
   Единственный workflow **Publish game** проверяет runtime и публикует `site/`.
6. Дождаться успешного Pages и проверки фактических HTTPS-метаданных.
   Для проверки desktop/touch использовать `tools/verify_live_web.py --commit SHA`.
   Отличать облачную Chromium touch simulation от физического iPhone Safari.

Публикация запускается при изменении `site/`, release manifest или workflow.
Правка документации не пересобирает игру. Исходный SHA в build.json — коммит,
из которого собрана игра; более поздний коммит публикации не подменяет его.

## Сборка и проверки

Godot 4.6.3 и соответствующий single-thread Web template; Compatibility renderer.
Переиспользовать установленный Blender и доступные инструменты, не скачивать
повторно по умолчанию. Linux: `bash tools/build_web.sh`; Windows:
`python tools/build_windows_release.py --blender <existing-blender.exe>`.
Существующий `python tools/test_story_browser.py build/web` проверяет desktop
и полный телефонный сценарий; для staging сохранять stdout в
`build/story-browser-release.log`. Результаты JSON остаются в
`build/screenshots/story/`. Остальные регрессии запускать по затронутому коду,
не расширять матрицу без конкретной причины.

## Первое включение

Telanico-3D-Lab приватный. Владелец выбрал Settings → Pages → Source: GitHub
Actions (подтверждено скриншотом). Если тариф разрешает Pages из приватного
репозитория, менять видимость не требуется. Публичность репозитория не является
обязательным условием нашей схемы; не предлагать её как единственный вариант.
Private Actions ранее отклонялся из-за оплаты/лимита: это отдельное ограничение,
которое выбор Pages Source сам по себе не устраняет. Повтор Publish game
39925677267, attempt 2, также завершился до назначения runner, steps=[].
Любая смена видимости открывает исходники и Git-историю и требует явного согласия.
В этой облачной сессии GitHub connection подтверждает admin=true, но callable
инструмента изменения repository settings нет; установленный gh сообщает
невалидный GH_TOKEN. Не выдавать ограничения инструментов за отсутствие прав
владельца и не искать/создавать токены в обход настроенной авторизации.

Целевой сайт: https://sgdenikin-sys.github.io/Telanico-3D-Lab/
Текущий подготовленный runtime — UI-патч V2.2, source c9ef4eb; 24 файла
проверяются по SHA-256. Предыдущая выпущенная V2.2 (source 2c94a3f) сохранена
в истории и в старом опубликованном сайте. Новый URL не считать
работающим до успешного деплоя и HTTPS-проверки.

## История и восстановление

Старые ветки и репозиторий Telanico-3D-Web не участвуют в дальнейшей работе.
Пока новый сайт не проверен, старый опубликованный сайт сохраняется без изменений.
Исторические ветки не удалять с неперенесёнными изменениями; история и теги
достаточны для отката, новые параллельные рабочие ветки не создавать.
Старые workflow-файлы перемещены в docs/history/workflows и не запускаются.
Исходную production-игру VorGun не редактировать.
