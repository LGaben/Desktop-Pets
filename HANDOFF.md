# Передача и проверка Desktop-Pets

Последняя проверка sizing/frame fix (root): compileall ui/tests, Flake8 F/E9 изменённых runtime/test файлов и git diff --check PASS. `reports/verification/20261103T141724626615Z-menu-e2e/summary.json` — BLOCKED, environment exit101; source SHA256 `dcbf16fc561b0bce129a10d578a258118b2eb5c27959e00d0d77e536a4cc81fb`, source_unchanged=true. Qt PASS и новый EXE не заявляются. Пользователь может повторить прежнюю build-команду из BUILD_INSTALL_COMMAND.txt; gate сохранён. Более ранние отчёты ниже — история.

Дополнение к sizing fix: root QSS border удалён, frame явно NoFrame. Фон и видимая рамка по-прежнему рисуются paintEvent, но больше не уменьшают viewport на дополнительные 2px поверх layout margins; это предотвращает взаимное появление scrollbar и потерю ширины текста. Text/pixel assertions сохранены, Qt прогон остаётся неподтверждённым в среде агента.

3 ноября 2026, пользовательская попытка сборки `reports/verification/20261103T140534Z-security-build/pytest.log`: 194 collected, 188 passed, 6 failed (2 устаревших exact-width assertions и 4 реальных panel text-clipping проверки). Новый EXE этим не создан. Причина расчёта: detached body/buttons измерялись до наследования шрифта popup через scroll.setWidget. Исправление `_content_hint`: после parenting и polish пересчитать minimum width/height каждого action/style button через итоговые font metrics и QStyle.sizeFromContents; 44px gear/profile layout сохранены. Text-clipping E2E assertions не ослаблены; exact272 width expectation заменено на content hint + margins, no horizontal overflow и bounds. Regression увеличивает QSS font относительно фактического текущего и проверяет minimum width и реальный content rect. py_compile/F-E9/diffcheck PASS; targeted Qt pytest обычным project Python всё ещё Unable to create process, новые Qt результаты не заявляются. Сборка не запускалась.

Финальный root review одноуровневого меню: compileall ui/tests/scripts, Flake8 F/E9 тех же scopes и git diff --check PASS. Последний запуск `scripts/menu_e2e.py` из Inkscape: `reports/verification/20261103T135752700248Z-menu-e2e/summary.json`, BLOCKED, environment exit101. Source SHA256 `7ad71542dbbb3683bb0994458f071914be805da53b03832077049c7ed1eaad08`, source_unchanged=true. Qt/native/live E2E PASS не заявляется; код заморожен, пользователь приглашён запустить MENU_E2E.cmd для настоящих Qt логов и PNG в общей папке.

3 ноября 2026, исправление фактических жалоб на native popup: InteractionPanel теперь одноуровневый, без QMenu/More/Application и без срезов action list. Pet/Ball/Sleep/Follow/Settings, inline style selector и Hide/Quit либо Remove доступны напрямую. Panel имеет явный opaque paintEvent; ring — 3 main targets вокруг settings profile и один opaque footer с прямыми командами. Высота боковых целей не растягивается до высоты профиля, ширина учитывает текст/иконку; тесная область использует компактную раскладку без изменения сохранённого ring preference. Нормальное кольцо центрирует профиль у точки курсора с screen clamp. Старый _show_more_menu удалён; model/coordinator/PNG/EXE не менялись.

Добавлены tests/test_menu_e2e_qt.py (реальные Qt события и callbacks, pixel alpha/color, font metrics, geometry), scripts/menu_e2e.py и MENU_E2E.cmd: отдельные 100/150/200% процессы, timestamp logs/JUnit/native PNG, затем полный pytest. Документация docs/MENU_E2E.md. В среде агента project Python всё ещё Unable to create process; реальный runner report reports/verification/20261103T135417927731Z-menu-e2e/summary.json = BLOCKED (environment exit101), новых native PNG/Qt PASS нет. Compileall/F-E9/diffcheck PASS. Live приложение недоступно по native pipe и не остановлено; старые HTML previews исторические, не новый UI и не E2E evidence.

Root design review checks: Node `verify-native-design.cjs` PASS, compileall ui/tests/scripts/utils/i18n PASS, Flake8 F/E9 тех же scopes PASS, git diff --check PASS. Qt не исполнялся. Existing direct-settings regression обновлён для обоих layouts: lookup по accessibleName «Настройки», callback и минимум 44px сохранены; других устаревших lookup settingsShortcut/старых sizing assumptions в menu tests не осталось.

Дополнительно root прогнал pure + release-security: 59 tests PASS. Предыдущая пользовательская сборка до текущего redesign имела 174 pytest passed за 12.49s, candidate SHA256 dffaa760…, фактический Qt6Core 6.12.0.0. Это baseline предыдущей сборки, не результат исполнения новых Qt дизайн-регрессий; новые Qt tests пока не запускались.

Native capture для пользователя: двойной клик `RENDER_MENU.cmd` запускает project venv и `render_native_menus.py --theme both --force`, обновляет только четыре `{panel,ring}-{light,dark}-ru.png` в `output/menu-concepts/native-current`; без --force renderer отказывается перезаписывать существующие файлы, EXE/приложение/реестр/БД не затрагивает.

3 ноября 2026, новый дизайн native pet menu (после успешной пользовательской Qt6 сборки `reports/verification/20261103T115345Z-security-build/summary.json`, status built, candidate SHA256 начинается dffaa): `ui/interaction_panel.py` теперь использует компактный list-popover (~272px) с original nearest-neighbour thumbnail, именем/характером и прямыми настройками; кольцо — четыре отдельные поверхности вокруг профиля, прозрачные промежутки без закрашенного креста. Общие `ui/menu_visuals.py` дают локальные QPainter иконки, системную light/dark палитру и согласованные tray/secondary меню. Menu i18n очищен от emoji по явным семантическим ключам; callbacks, PlainText до user text, hover/coordinator, Tab/Esc и fitting/scroll fallback сохранены. Имя визуально elided по реальной ширине, полное имя остаётся доступным, user tooltip не создаётся. Settings window не менялось.

Для дизайн-review отдельно: `output/menu-concepts/native-menu-design.html` (inline), `native-menu-design-preview.html` (offline, обе раскладки). Это HTML-концепция геометрии, не нативный screenshot. Источник истины — `python scripts/render_native_menus.py --output output/menu-concepts/native-light --theme light --lang ru` (и аналогично dark/en с отдельным output): renderer создаёт настоящие Qt PNG без pet model/DB/registry IO/tray, существующие PNG не перезаписывает. Новая сборка пока не запускалась; обычная проба project Qt6 venv в среде агента всё ещё Unable to create process. Добавлены Qt design regressions для обеих тем/стилей/длинного markup-name/иконок и обновлён tiny-screen test под новые margins. Старый reactive demo, оригинальные sprites и EXE не менялись.

Design-review уточнение: весь ring-профиль 96×100 — прямая кнопка настроек с оригинальным idle-аватаром 32px, именем и явной подписью «Настройки»; initial focus на первом primary action. Avatar берётся из первого idle кадра loader без движения таймлайна. Compileall, Flake8 F/E9 и git diff --check PASS; `node output/menu-concepts/verify-native-design.cjs` PASS (offline resources, exact original PNG, JS syntax, actions/More/Escape). Qt6 дизайн-тесты здесь не исполнялись. Экспорт концепции воспроизводится: `python scripts/export_menu_preview.py --source output/menu-concepts/native-menu-design.html --output output/menu-concepts/native-menu-design-preview.html --stack-variants --force`.

3 ноября 2026, исправление пользовательского build pytest: `InteractionPanel.open_at` теперь полирует QSS/layout до измерения и использует одинаковый minimum-width floor 218px (+12px outer margins) для проверки кольца и фактического resize. Ранее fit проверял только hint, а resize расширял его до 230px, поэтому кольцо ошибочно оставалось активным в workarea 200×180. Regression сохранён для исходных коротких подписей, дополнен RU/EN действиями с Settings и высотой 120px. Project Qt6 venv обычным запуском по-прежнему выдаёт Unable to create process в среде агента; Qt pytest и новая сборка здесь не запускались. Пользователь может повторить команду из BUILD_INSTALL_COMMAND.txt; gate не отключён, старые EXE не менялись.

3 ноября 2026, security remediation по отдельному запросу пользователя: выполнен перенос всего runtime/tests/scripts на PyQt6/Qt6 6.12.0 без compatibility wrapper; spec исключает старые Qt5 и неиспользуемые QML/WebEngine. JSON settings получили size cap 4 194 304 characters, RecursionError/shape validation, безопасный fallback и сохранение corrupt raw через autosave; explicit Apply/add/remove разрешают восстановление, hidden pet-count cap не добавлен. Имена QLabel получают PlainText до пользовательского текста. Зафиксированы 18 Windows CPython 3.13 AMD64 wheels с SHA256/provenance; PyInstaller 6.22.3; scripts/verify_lock.py проверяет pins/tags/наблюдавшуюся metadata. Requires-Dist Sip/Ruff не удалось наблюдать, это отмечено явно; установка с hashes без --no-deps должна fail closed. scripts/build_release.py — прямой CLI с project venv, isolated binary hash install, pip check, pytest, отдельными timestamp dist/work, source/asset manifest до проверок и сравнением после build/sign, фактической PE/Qt6 DLL проверкой через scripts/verify_bundle.py. Optional signing использует личный store thumbprint/SignTool, без паролей/поддельного сертификата. Пользователь сообщил, что сертификата нет, поэтому signing pending и unsigned явно обозначен.

Итог root: `reports/verification/20261103-security-remediation-review/summary.json` — 55 pure + 4 release-security unittest (59 всего), 5 fox checks, compile/runtime-context/F/E9/wheel-lock/EXE integrity PASS. Qt/pytest/Ruff/smoke BLOCKED; benchmark не запускался. Offline preview теперь без CDN/iframe, с локальными SVG, inline PNG и deny-network CSP; Node selfcheck/source hash/2 scripts PASS. Новые Qt security regressions добавлены, не исполнялись. Полная история аудита и отдельный актуальный remediation раздел находятся в docs/SECURITY_REVIEW_2026-11-03.md; recipe — docs/SECURE_BUILD.md. Qt6 6.12.0 не объявляется полностью CVE-free: новый CBOR advisory CVE-2026-105924 затрагивает неиспользуемый приложением QCborValue→JSON; patched 6.12.1 wheel на дату фикса не был доступен, следующий version/hash update остаётся задачей после публикации.

Фактическая попытка build_release.py --install зафиксирована в `reports/verification/20261103T101521Z-security-build/summary.json`: preflight BLOCKED до установки/venv, потому что доступный Inkscape Python — 3.12.9 GCC, а release target требует рабочий Windows CPython 3.13 AMD64 MSC. Прямой PyPI HTTPS из Python блокируется WinError 10013; доступ/политики не обходились. Новый EXE не создан и не запущен. Старый текущий EXE по-прежнему `891EF0E1BD08A83B16D46861C3FFE860C49CE5129FFAD1AF569197F1C01C9583`, NotSigned, Qt5 5.15.2; он **не содержит эти исправления**. Оба старых EXE и оригинальные PNG сохранены. Записи read-only аудита ниже исторические; нынешняя remediation меняла исходный код, инструменты и документы.

3 ноября 2026 — read-only аудит безопасности: `docs/SECURITY_REVIEW_2026-11-03.md`. Подтверждён Low локальный startup DoS через deeply nested JSON в MemoryBackend, потенциальный Low AutoText в именах QLabel; отмечены условные component/supply-chain риски старого Qt и builder. Фактический текущий EXE имеет SHA256 `891EF0E1BD08A83B16D46861C3FFE860C49CE5129FFAD1AF569197F1C01C9583`, 40 601 156 bytes, NotSigned, AMD64, ASLR/DEP, manifest asInvoker/uiAccess=false. Ограниченным read-only чтением только двух Qt DLL в памяти подтверждены QtCore/QtSvg 5.15.2.0 и совпадение с venv; embedded Python не извлекался/не исполнялся, bootloader version не установлена. PyInstaller 6.20.0 — подтверждённая версия builder venv, а не доказанная версия EXE; advisory <6.22.1 относится к привилегированному запуску. SQL payload в временной БД остался данными. Remote RCE/SQLi/keylogger/autostart/elevation не подтверждены; это не сертификат безопасности. Native runtime отделён от CDN-запросов браузерного прототипа. Полный отчёт содержит сценарии, severity, строки, первичные advisories и ограничения. Код, EXE, реестр, зависимости и настройки не менялись; исправления по запросу аудита не применялись.

Итог проверки группового интереса от 3 ноября 2026: `reports/verification/20261103-cursor-interest-review/summary.json` — 52 pure unittest, 5 fox checks, compile, runtime-context, Flake8 F/E9 и EXE integrity PASS. Qt/pytest/Ruff/smoke BLOCKED из-за отсутствующих зависимостей; benchmark не запускался. Независимая read-only проверка coordinator на 12 000 polls с seed 392 дала 285 эпизодов, распределённых между тремя питомцами 88/94/103: owner всегда eligible и не blocked, длительность 2–4 с не продлевается, прямой передачи интереса без общей паузы нет. Новый Qt-clock regression проверен чтением и компиляцией, но не исполнялся. Визуальный GUI PASS не заявлен.

3 ноября 2026, 12:10 — исправление доступа к меню и групповой реакции. Один CursorInterestCoordinator в primary выбирает случайного видимого свободного питомца рядом с реально движущимся курсором после 0,4 с; интерес длится 2–4 с, затем общая пауза 4–6 с. Ни один другой питомец не получает автоматическую цель в это время. Poll поступает от любого живого окна с общей защитой от дублирования, поэтому скрытие primary не останавливает видимых спутников; когда все скрыты, их mouse timers остановлены. Hover проверяется и на каждом animation tick: отменяет свободную прогулку в idle, прекращает автоматический эпизод и удерживает окно ещё 1,8 с после ухода курсора. Left press немедленно блокирует перемещение, drag остаётся пороговым, короткий release гладит. Владение мячом, carry timer и явное постоянное Follow не отменяются наведением. Сон, petting/сердечки в том числе nonfox, меню, нажатие, перенос и пауза исключают автоматический интерес; hide/remove/retype освобождают владельца и запускают общую паузу.

В трее добавлено «Питомцы → имя → действия» на тех же callbacks, в том числе для скрытого питомца. Native panel/ring перестроены: «Погладить / Мяч / Сон» главные, четыре цели у кольца, «Ещё…» для вторичных команд, прямой gear Settings с 44px целью в шапке/центре. Полная согласованная палитра normal/hover/pressed/focus и Segoe UI распространяется на popup, вторичные меню и tray; длинные подписи больше не режутся textwrap. Явная команда переименована в «Следовать постоянно» / «Остановить слежение». Новые 13 pure coordinator tests подключены в scripts/verify.py. Проверки worker: 52 pure unittest + 5 personality PASS, compile и Flake8 F/E9 PASS, git diff --check PASS. Добавлен tests/test_cursor_group_qt.py с групповой/lifecycle/hover/press/tray/settings проверкой и обновлены старые проверки иерархии. Qt GUI не запускался: в доступном Python нет PyQt5; ComputerUse native pipe также недоступен, визуальное принятие не заявлено. HTML-прототип, исходные PNG и EXE не менялись; сборку на этом этапе не запускали.

3 ноября 2026, 10:56 — по запросу пользователя выполнена новая прямая попытка сборки актуального абсолютного `DesktopPet.spec` через `C:\Program Files\Inkscape\bin\python.exe -m PyInstaller`, с `--noconfirm`, отдельными `dist-test` и `build-test`. Итог BLOCKED, exit 1: `No module named PyInstaller`; в этом же MinGW Python 3.12.9 нет PyQt5. WindowsApps alias не запускается (`The file cannot be accessed by the system`), найденный `C:\Users\User\Desktop\prikol\venv\Scripts\python.exe` тоже не запускается, exit 101. Рабочий совместимый CPython/venv с зависимостями в проверенных обычных местах не найден. Новый EXE не создан. Отчёт, точная команда и лог: `reports/verification/20261103-105509-exe-build/summary.json`, `build-command.txt`, `build.log`; диагностика интерпретаторов — `interpreters.json` и `parent-venv-probe.log`. Оба прежних EXE побайтно сохранены по SHA256: текущий `Desktop-Pets/dist/DesktopPet.exe` — `DA4E854251F97AE8ED25C541F7CE2B61A28B923A978CA6874C5B8BAAE6C39170`, родительский `pet/dist/DesktopPet.exe` — `DBF5BC03F8E1AC215518CE8558DA10AD945197B0F09DFFA318295A5291647F30`. Исходный код и spec не менялись; EXE не запускались, зависимости не устанавливались, execution policy не менялась.

3 ноября 2026 — меню и реакция на курсор в исходном коде. «Стиль меню → Панель / Кольцо» доступен в трее и через «Ещё…» у питомца; выбор сохраняется глобально, применяется ко всем питомцам и закрывает прежние popup. Оба layout используют один набор callback; кольцо содержит все шесть действий, Tab/Esc и при недостатке места переходит в прокручиваемую панель. Новая pure-политика CursorReaction реагирует только на реальное движение курсора поблизости: любопытная лиса сближается, спокойная отбегает, активная может выбрать оба варианта. Удерживаются направление на один подход, радиусы входа/выхода 160/215 px, интервал перепланирования 0,4 с, мёртвая зона и буфер до курсора. Цели достижимы в рабочих границах текущего экрана, включая отрицательные координаты. Сон, поглаживание, перенос, открытые меню, погоня за мячом и его перенос имеют приоритет; sample ресинхронизируется во время блокировок. Явное «Следовать за мышкой» остаётся отдельной командой. Прежняя редкая дальняя погоня и реакция на неподвижный курсор удалены; нет клавиатурных hooks, прыжков или неподвижного поворота за курсором.

Проверка родительского агента: `reports/verification/20261103-menu-cursor-final/summary.json` — 39 чистых unittest, 5 проверок характера, compile, runtime-context, Flake8 F/E9 и неизменность EXE PASS. Qt/pytest/Ruff/smoke BLOCKED: доступный Inkscape Python не содержит нужных модулей; benchmark намеренно не запускался. Полная GUI-верификация не заявлена. Добавлены Qt-сценарии обоих стилей на RU/EN, маленькой рабочей области, общих селекторов и приоритетов движения; они не запускались. Дополнительные read-only проверки политики родительским агентом подтвердили достижимые границы, направление и буфер при десятках тысяч случайных и последовательных входов.

Для просмотра без сборки обновлён `output/menu-concepts/menu-preview.html`: один живой макет с явным выбором стиля на месте, оригинальными idle/walk/run/lie PNG и реальным ограниченным движением за/от курсора. Закрытие меню или щелчок по свободной области разрешает движение. После первого явного действия исходный хвост непрерывно идёт по idle 1→2→3→4→5 с фазой 264 мс; меню не сбрасывает фазу, пауза и скрытие отключают loop. При загрузке анимация не запускается. Мёртвая зона отменяет только перемещение, сохраняя направление текущего подхода. Это локальная демонстрация, не подключение к глобальному вводу Windows; клавиши и кнопки мыши не вызывают bob/прыжок. `node output/menu-concepts/verify-menu.cjs` PASS: байты PNG совпадают с оригиналами, cadence/фаза idle, layout selector, движение/направление, ограничение dt, pause/sleep/follow/menu/resize/hidden и синтаксис шести scripts standalone-wrapper. Визуальная проверка браузером недоступна; иконки standalone-wrapper загружаются с CDN. Исходные PNG и EXE не менялись, сборка не выполнялась.

2 ноября 2026: те же сердечки по короткому ЛКМ или кнопке «Погладить» доступны всем 21 видам SimplePet. У остальных 20 видов нет реакции головы и изменений текущего поведения, движения, погони или фазы анимации; сердечки идут 0,95 с по реальному времени. Лиса сохраняет прежнюю реакцию головы и непрерывный хвост. Явный сон отклоняет действие; повторный клик во время эффекта не перезапускает его. Для остальных видов эффект центрируется по фактической ширине окна. Добавлены 20 параметрических проверок модели и 4 Qt-сценария клика/панели в обе стороны с таймером и очисткой. Проходят 24 чистых unittest, 5 проверок характера, compile изменённых Python-файлов, Flake8 F/E9 для pet/ui/utils/tests/scripts/main.py, проверка исходных 30 PNG и 15 поз/APNG, Node-проверка непрерывности хвоста, git diff --check. Qt-тесты не запускались: доступный Inkscape Python не содержит PyQt5. Исходные PNG и EXE не менялись, сборка не выполнялась.

27 октября 2026: успешное поглаживание лисы кликом или кнопкой панели запускает три пиксельных сердечка над головой на 0,95 с: они поднимаются и исчезают. Эффект — отдельное прозрачное окно без захвата ввода/фокуса, работает от существующего animation tick и не меняет размеры/позицию спрайта или фазу хвоста. Сон, перенос, скрытие, смена питомца и завершение закрывают эффект; повторный клик во время реакции не создаёт новый. Отчёт `reports/verification/20261027-fox-hearts/summary.json`: 24 чистых unittest (включая 4 новых), 5 проверок характера, compile и доступный lint проходят; Qt/pytest/ruff/smoke заблокированы средой. Добавлены 3 Qt-сценария (всего 11 в модуле), они не запускались. Контакт: `output/fox-pet-react/heart-effect/keyframes.png`; APNG `petting-hearts-1x.apng` / `petting-hearts-4x.apng` в той же папке показывают кодовый preview поглаживания с эффектом, не GUI-снимок. Они используют реальные runtime poses, FoxReaction и общую маску/тайминг: 33 декодированных точных кадра, 1584 мс, один показ. Существующие EXE и исходные PNG не менялись; новая сборка не выполнялась.

Финальная прямая попытка сборки актуального абсолютного `DesktopPet.spec` через доступный Inkscape Python завершилась с кодом 1: `No module named PyInstaller`. Параметры указывали только `dist-test`/`build-test`; новый EXE не создан. Точная команда и вывод: `reports/verification/20261026-startup-build/build-attempt.log`.

Исправление запуска 26 октября: traceback `_log` относился к отдельному родительскому `../main.py`, а не актуальному `Desktop-Pets/main.py`. В родительский файл добавлено только определение logger; AST и flake8 F821 проходят, GUI не запускался. Новые характеры/панель этим исправлением в старую копию не переносятся. `scripts/build_test.ps1` привязан к актуальному spec независимо от cwd, проверяет Python/PyInstaller/PyQt5 и код завершения; тестовый EXE направляет в отдельный `dist-test`, work files — в `build-test`. Запрошенная самостоятельная пересборка заблокирована: совместимый Windows Python 3.13 недоступен по правам; доступный Inkscape Python 3.12 — MinGW, без PyQt5 и PyInstaller. Его нельзя смешивать с установленными cp313-модулями. Дополнительно запуск helper в текущей оболочке остановлен политикой PowerShell для .ps1; политика не менялась. В README есть прямая команда `python -m PyInstaller` с абсолютными путями для пользовательского рабочего Python. Старые EXE не менялись и не запускались; новый EXE не получен. Отчёт: `reports/verification/20261026-startup-build/summary.json`.

26 октября 2026 — реализация взаимодействий в исходном коде: у каждой новой/старой лисы без корректного ID один раз случайно выбирается active/calm/curious; ID сохраняется в roster. Отличаются прогулки, отдых, интерес к курсору и длительность игры с пойманным мячом, явные команды имеют приоритет. ПКМ открывает компактную панель; короткий ЛКМ гладит, перенос начинается после порога Qt. 15 новых sibling pose-assets подключены к голове поверх текущей idle-фазы без сброса хвоста; оригиналы не менялись. «Мяч» ставит видимый мяч рядом: бросок — захват самого мяча и выпуск с недавним импульсом, Esc/ПКМ отменяют захват. Мяч остаётся доступен после остановки; подбор проверяется из основного animation tick. Настройки/служебные действия сохранены. EXE не менялся и не пересобирался.

Проверка текущей реализации: 20 чистых unittest и 5 прямых assert-проверок характера/миграции/таймлайна проходят; flake8 выбранных изменённых модулей и компиляция проходят. В flake8 исключены существовавшие E231/E241 выравнивания старой таблицы переводов `i18n.py`; чистота всего репозитория по ruff не заявлена. Все 15 runtime PNG побайтно совпадают с проверенными pose-копиями и покрыты nested package-data; исходные 30 SHA256 сохранены. Отчёт: `reports/verification/20261026-fox-interactions/summary.json`. Добавлены 8 Qt integration tests в `tests/test_fox_interactions_qt.py`; в доступном Inkscape Python отсутствует PyQt5, Python 3.13 и локальные pytest/ruff недоступны по правам. Эти новые Qt тесты не запускались; исторический пользовательский baseline от 23 октября имел pytest/smoke/benchmark PASS и ruff FAIL, он не подтверждает новые изменения. На рабочем пользовательском Python: `python scripts/verify.py --skip-benchmark`; для реального окна затем нужен просмотр панели и броска на Windows. Художественное одобрение новой UI-реализации не заявлено.

## История предыдущих этапов

Ниже сохранены исторические результаты; актуальный статус реализации и проверок приведён выше.

26 октября 2026, актуальная проба v4: пользователь отверг остановку хвоста и паузу. Теперь хвост непрерывно продолжает исходный idle 1→2→3→4→5 по 264 мс, независимо от головы. Поглаживание меняет только голову 0→1→2→1→0 (0/132/264/1056/1188 мс); клик и выход не сбрасывают фазу и остаток времени хвоста. Подготовлены 15 PNG сочетаний: head=0 точно совпадает с текущим оригиналом, тело и лапы при любой голове точны относительно текущей исходной фазы. Исправления шеи и левого контура сохранены. APNG: 8 кадров, 1584 мс, loop=1, без дополнительного удержания; главный preview продолжает idle, cache revision continuous-tail-20261026. Python regression всех 15 поз/APNG и Node проверки времени проходят. Runtime, EXE и исходные ассеты не менялись; browser QA недоступен, художественное принятие ожидается. Прошлые описания спокойного/неподвижного хвоста ниже относятся к отвергнутой итерации.

26 октября 2026: v4 исправлен остаточный контур головы x23,y19..22; маска `[22,4,24,23)` теперь переносится с мягкой alpha поверх сохранённой спины. Neck-gap fix сохранён. Пересобраны 9 PNG/APNG в том же v4, cache revision preview обновлён. Root независимо подтвердил все проверки и визуальный контакт `output/fox-pet-react/v4/spike-before-after-backgrounds.png`: оба сдвига, три фона, обе стороны. Оба сохранённых плохих PNG проваливают regression; новые PNG/APNG проходят. Исходные 30 PNG точны; runtime/EXE не менялись и не запускались. Browser QA недоступен; художественное принятие ожидается.

Обновлено: 23 октября 2026. Проект: `C:\Users\User\Desktop\prikol\pet\Desktop-Pets`.

Последнее исправление пробы v4: устранена лишняя очистка строки шеи y=28 при сдвиге головы на1px. В кадрах2/7/8 удалялись15 плотных пикселей x24..38. Builder теперь очищает только фактическое объединение областей головы; PNG/APNG пересобраны в том же v4. Regression на реальном старом PNG воспроизводит дефект и проходит на новых PNG/APNG, включая8× с приведением к46×37. Сравнение: `output/fox-pet-react/v4/gap-before-after-backgrounds.png`; исходные30PNG hash, лапы и endpoints точны. Main preview использует revisionquery для обновлённых кадров. Root независимо подтвердил проверки и просмотрел сравнение на светлом/тёмном/шахматном фоне в обе стороны. Runtime/EXE не менялись, browser QA недоступен.
Коммитов, публикаций и изменений глобальной среды нет. Родительская версия проекта не изменялась.

## Текущий результат

Выполнено 16 настоящих unit/integration тестов: 8 физики, 7 настроек, 1 SQLite — PASS.
Также PASS: compileall, синтаксис Python 3.9 для 36 файлов, Flake8 7.3.0 с правилами F/E9,
git diff --check и проверка неизменности пользовательского EXE. Эти проверки не заменяют Qt GUI тесты.

Полный pytest, Qt event-loop smoke, ruff и 9 замеров CPU/RAM пока BLOCKED из-за окружения.
Ни одного значения CPU/RAM для питомцев не получено; улучшение производительности численно
не подтверждено. Пользователь самостоятельно запускал свой EXE и сообщил, что ошибок не заметил.
Агент этот EXE не запускал: у бинарника нет безопасного режима изоляции пользовательского реестра.

Последний машинный отчет и полные логи:
`reports/verification/20261023-agent-reviewed/summary.json`.
Дополнительная проверка артефактов/синтаксиса: `archive-syntax-check.log` в той же папке.
Независимый повтор родительского агента: `reports/verification/20261023-review/summary.json` —
те же 16 тестов, compileall, runtime context, Flake8 F/E9 и EXE integrity PASS;
Qt/pytest/ruff/smoke и девять benchmark сценариев BLOCKED, измерений нет.
Отчеты, `.verification`, build и dist игнорируются Git.

## Найденное и исправленное при тестировании 23 октября

Новый тест свободного падения и затухания выявил небольшую неточность финального состояния:
при полу y=595 мяч мог остановиться на y=594.0555022405724 с остаточной скоростью.
Первый прогон: 15 PASS, 1 FAIL. Это не падение приложения, отклонение составляло менее пикселя.
В `pet/ball.py` остановка теперь устанавливает точную высоту пола и обе скорости в ноль.
Regression test проверяет положение, скорости и неизменность после следующего update.

Чтобы проверить настоящую физику без GUI, импорты Qt в Ball перенесены в ветку выбора
экранных границ. При явно переданных bounds Qt не нужен. Тест использует небольшой объект
границ, а не копию алгоритма и не поддельный модуль Qt. Покрыты равное elapsed time при разных
интервалах, постоянное ускорение, четыре столкновения с отрицательными координатами,
затухание, повторный бросок, большие/нулевые/отрицательные dt и экстремальная скорость.

Flake8 выявил два предупреждения: удерживающая окно ссылка `_window` теперь имеет точечный
`noqa: F841` с пояснением lifetime; из константного стиля кнопки в settings убраны лишние f-префиксы.
После исправлений 16 тестов и Flake8 F/E9 проходят. Родитель независимо подтвердил 16 тестов
и diff check. Полный ruff не запускался успешно.

## Архитектура предыдущих изменений

- `pet/catalog.py` — единый каталог 21 типа/emoji для factory, tray, окна и настроек.
- `utils/settings_store.py` — небольшой SettingsBackend Protocol, RegistryBackend и валидируемый
  SettingsStore; i18n отвечает за переводы и сохраняет прежний интерфейс функций настроек.
  При импорте обращений к реестру нет.
- Ключ `HKCU\Software\DesktopPet` совместим с legacy lang/pet. Значение pets хранит JSON roster
  основного и дополнительных питомцев: тип, имя, позиция. Проверяются язык, известность типа,
  координаты и длина имени до 80 символов. Скрытого ограничения числа питомцев нет.
  Сохранение выполняется по значимым событиям и выходу; shutdown guard предотвращает потерю
  satellites при cleanup. SimplePet.save_state делегирует сохранение владельцу.
- Общие pause/resume/cleanup останавливают скрытые окна, мяч и погоню. UI таймеры имеют QObject
  владельца. Stats timer у SimplePet не запускается; настройки останавливают таймер и анимации
  также при обычном close/Alt+F4. FullPet использует управляемый action timer вместо singleShot.
  UI использует публичные carrying_ball, following_mouse, cancel_chase и set_follow_mouse.
- geometry выбирает содержащий/ближайший экран и ограничивает положение по размеру окна;
  поддерживает отрицательные координаты и удаление монитора. Первый кадр задает размер до restore.
  Цель погони учитывает центр питомца и достижимую область у края экрана.
- Движение/анимация обеих моделей используют dt, дробное накопление и остаток времени кадров.
  Ball ограничивает dt 100 ms и использует субшаги максимум 8 ms. Resume сбрасывает elapsed.
- SpriteLoader загружает кадры после QApplication, сортирует численно, разделяет normalized
  и mirrored frames. Общий LRU ограничен 128 наборами; живые загрузчики удерживают свои кадры.
  UI меняет pixmap по cacheKey, размер только при изменении, движение обрабатывается отдельно.
- PetDatabase поддерживает db_path; временные fixtures работают после импорта. SQLite connections
  действительно закрываются через closing+transaction. Тесты не меняют реестр и настоящую БД.
- Backend упаковки исправлен на setuptools.build_meta. Wheel включает main, entry point и assets.
  Runtime dependency — PyQt5, dev extra содержит pytest/ruff/build/PyInstaller. Отслеживаемый
  DesktopPet.spec использует стандартные Qt hooks, без ручного удаления DLL.

## Точные команды выполненного прогона

Из корня проекта, PowerShell:

```powershell
& 'C:/Program Files/Inkscape/bin/python.exe' scripts/verify.py --flake8-path C:/Users/User/.vscode/extensions/ms-python.flake8-2026.6.0/bundled/libs --output reports/verification/20261023-agent-reviewed
git diff --check
```

Runner действительно выполнил следующие subprocess:

```powershell
& 'C:/Program Files/Inkscape/bin/python.exe' -m unittest tests.test_ball_physics tests.test_settings_store tests.test_storage_isolation -v
& 'C:/Program Files/Inkscape/bin/python.exe' -m compileall -q pet ui utils tests scripts main.py
```

Flake8 выполнен тем же Python с PYTHONPATH на обычный установленный пакет из VSCode extension:
`-m flake8 pet ui utils tests scripts main.py --select F,E9` — PASS.
Это подмножество проверок на ошибки кода, а не замена полному ruff.

Отдельно проверены синтаксис через ast.parse(feature_version=(3,9)), read-only архив EXE
через PyInstaller CArchiveReader и его SHA256. Синтаксис 3.9 не означает runtime проверку на 3.9.
WinAPI helper измерения памяти проверен на текущем Python процессе, но это не замер питомцев.

## Артефакты сохранены

Пользовательский `dist/DesktopPet.exe`: 40 542 341 байт, SHA256 до/после:
`2342fa565d3eae8414c73f50e439a257219efdda045ba4dfa4c3d9817284119b`.
Он не удалялся, не перезаписывался, не пересобирался и не запускался в этом прогоне.
Read-only проверка подтвердила 831 PNG/ICO, python313.dll и SIP cp313 внутри архива.
Это проверка состава, а не работоспособности GUI.

Предыдущий `dist/desktop_pet-1.0.0-py3-none-any.whl` также не изменялся.
Его сборка/установка и 831 assets были проверены 20 октября. После новых исправлений исходники
main.py, pet/ball.py и ui/settings.py отличаются от того wheel и пользовательского EXE.
Новые runner/benchmark/test_ball_physics относятся к исходному проекту. Готового бинарника
с исправлением финальной остановки мяча агент не создавал.

## Ограничения среды и один локальный runner

Работает только доступный Python 3.12.9 из Inkscape. Launcher существующего venv повторно выдает
Unable to create process; штатный Python 3.13 ранее не запускался из-за AccessDenied.
Qt/SIP установлены под Python 3.13 и несовместимы с этим Python 3.12: DLL load failed.
В чистом окружении runner PyQt5, pytest и ruff отсутствуют, что видно в отдельных probe логах.
Повторная обычная установка только в workspace завершилась No matching distribution PyQt5;
ранее сеть отклоняла соединение с WinError10013. В доступном pip cache нет pytest/ruff и SIP cp312.
Защищенные executable не копировались, извлечение/запуск runtime из EXE не применялись.

Из терминала пользователя с рабочим Python 3.13 достаточно:

```powershell
python scripts/verify.py
```

Если тестовые инструменты отсутствуют, явный вариант:

```powershell
python scripts/verify.py --install-deps
```

Установка только в `.verification/deps/<interpreter-tag>-<architecture>` с --upgrade;
разные Python не смешивают native wheels. Глобальная среда не изменяется. Наследованный PYTHONPATH
не используется, эффективные пути и runtime записываются в отчет. Каждый шаг — отдельный процесс
с timeout и логом; subprocess console скрывается на Windows. Qt callbacks smoke/benchmark
контролируются subprocess timeout; benchmark сохраняет исключения через sys.excepthook.

Runner запускает pytest с JUnit XML, ruff, event-loop smoke и девять отдельных benchmark процессов:
1/5/10 питомцев × idle/moving/hidden, warmup 1 секунда, замер 5 секунд. CPU — процент одного ядра
по process_time/wall; память — текущие working set/private bytes и MiB. Setup/teardown исключены,
но накладные расходы sampler каждые 200 ms входят в результат. Случайный AI отключен при сохранении
штатных таймеров. Hidden сценарий проверяет ноль активных pet timers.

По умолчанию используется offscreen: результат касается Qt процесса, не полной нагрузки DWM/GPU.
`--platform windows` явно включает видимые benchmark окна. Сейчас все девять строк имеют BLOCKED,
а не нулевые CPU/RAM. Проверки реальных мониторов, DPI, hot-unplug и GUI остаются незавершенными.

## Художественная проба лисы: 23 октября 2026

Этап 1 плана выполнен: прочитаны все 30 PNG; `output/fox-pet-react/original-audit.json` содержит alpha, палитры, опоры и SHA256. Этап 2 опробован, но quality gate не пройден: лист v1 (1706×922) меняет пропорции и сетку; одиночный keyframe v2 (1398×1125) вместо одного глаза перерисовывает всю лису. Обе попытки отклонены для интеграции; пользовательского одобрения нет.

Артефакты: `output/fox-pet-react/REVIEW.md`, `preview.html`, обе PNG, prompts и provenance. PNG скопированы неизменёнными из built-in image_gen. Python использован только для чтения и анализа изображений. PNG просмотрены напрямую; HTML проверен статически, Browser QA недоступен (нет браузера). Runtime, исходные ассеты и EXE не изменялись этой пробой. Следующий путь — pixel-level правка копий оригинала в редакторе с сохранением требуемого стиля. Предыдущие сведения и ограничения проверок выше сохранены.

Все 30 SHA256 исходных PNG совпадают с начальным аудитом. Текущий SHA256 EXE: `9976225c2add1d6e495b32d6ece51afbe9137614d62730a37a839c809b5c28a0`; отличается от исторического отчёта 20261023-review. Эта проба EXE не запускала и не записывала; историческая неизменность не заявляется. Подробности: `output/fox-pet-react/integrity.json`.

## Лиса v3: обратная связь и точечная правка копий

Пользователь отклонил стиль генераций v1/v2 и указал прыжки диагностического превью. После явного разрешения редактировать копии оригинальных PNG скриптом создан `output/fox-pet-react/v3/`: шесть кадров 46×37, APNG 1×/8×, контактный лист, воспроизводимый `build_preview.py` и `verification.json`.

Меняются только два пикселя верхней части глаза `(33,17)` и `(34,17)` внутри ROI `[33,17,35,19)`. Вне ROI RGBA совпадает с original idle/frame_1; alpha неизменна целиком; первый и последний кадры RGBA-точно исходные. Никакой генеративной перерисовки, подгонки тела или ресайза игровых PNG. v3 пока кандидат для пользовательского просмотра, не принят.

`output/fox-pet-react/preview.html` теперь по умолчанию на паузе: фиксированный оригинал, v3 на общем холсте/масштабе, выбор кадра, воспроизведение, зеркало и светлый/тёмный фон. Старый неверный step%5 и дробное равное кадрирование исключены; v1/v2 помещены в rejected архив. PNG оригиналов и runtime/EXE не менялись. Browser QA недоступен; утверждается только проверка ресурсов и математических/pixel invariants.

Root независимо проверил все шесть PNG v3 и APNG: вне ROI и alpha точны; изменено 0/2/2/2/2/0 пикселей. APNG содержит пять кадров после объединения одинаковой закрытой позы, общая длительность 1100 мс. Технический пробник моргания проверен, художественное принятие пользователем ещё не выполнено.

## Лиса v4: взаимодействие вместо технического моргания

Пользователю подошла фактура v3, но он отметил, что моргание слишком незаметно и нужны реакции на взаимодействия. Создан `output/fox-pet-react/v4/`: девять кадров 46×37, голова опускается на 1–2 пикселя, глаз прикрывается, хвост проходит исходную idle-дугу, затем возврат в оригинал. Уши следуют за головой, отдельно не складываются. v4 ожидает художественной приёмки, в runtime не подключён.

Main `output/fox-pet-react/preview.html` по умолчанию на паузе. Кнопка «Погладить» проигрывает один цикл и возвращает обычный пятикадровый idle; повтор включается отдельно. Оригинальный idle слева имеет независимый корректный цикл. Сохранены source sheet idle/lie/walk, APNG 1×/8×, contact-sheet и воспроизводимые build/verify скрипты. Вне documented ROI и в лапах RGBA exact reference; первый/последний exact original; 9 APNG кадров/1220мс, decoded exact. Все 30 исходных hash совпали; EXE не менялся и не запускался. Browser по-прежнему отсутствует, HTML проверен статически. Подробности и ограничения шеи/ушей: `output/fox-pet-react/v4/README.md`.
