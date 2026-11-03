# Проверяемая сборка Qt6 для Windows

Цель релиза — **обычный Windows CPython 3.13 AMD64 (MSC)**. Исходный код использует API Python 3.10+, но lock-файлы намеренно рассчитаны на Windows x64 / CPython 3.13. Не следует запускать приложение или сборку от администратора.

## Зафиксированные зависимости

- Runtime: PyQt6 6.12.0, Qt 6.12.0, PyQt6-sip 13.13.0.
- Builder: PyInstaller 6.22.3 с зафиксированными altgraph, hooks-contrib, packaging, pefile, pywin32-ctypes, setuptools, wheel и pip.
- Проверки: pytest 9.1.1, Ruff 0.17.2 и их зафиксированные зависимости.

Файлы в `requirements/`:

| Файл | Состав |
| --- | --- |
| `runtime-cp313-win_amd64.lock` | 3 runtime wheels |
| `build-cp313-win_amd64.lock` | Runtime + builder, 12 wheels всего |
| `test-cp313-win_amd64.lock` | Runtime + builder + проверки, 18 wheels всего |
| `windows-cp313-amd64.provenance.json` | Имя, версия, wheel filename, SHA256, первичный источник metadata и наблюдавшиеся Requires-Dist |

SHA256 проверены по официальным PyPI JSON/release-files. Это **metadata-derived набор, а не выполненный pip resolver**. Для Sip и Ruff файл и hash подтверждены, но dependency metadata не удалось прочитать через доступный renderer; это явно отмечено в provenance. Установка идёт с `--require-hashes` **без `--no-deps`**: новая неучтённая зависимость остановит установку, а не установится незаметно. После установки выполняется `pip check`. Sdist и сборка внешних пакетов из исходников запрещены `--only-binary=:all:`.

```powershell
python scripts/verify_lock.py
```

Эта offline-проверка требует packaging, включённый в build/test lock. Она проверяет wheel tags, pins/hashes и наблюдавшиеся зависимости для целевой платформы. Она не заявляет успешную установку пакетов.

## Сборка отдельного кандидата

Из корня проекта, рабочим Windows CPython 3.13 x64:

```powershell
python scripts/build_release.py --install
```

Скрипт проверяет платформу до создания окружения и установки. Затем создаёт `.build-envs/qt6-cp313`, устанавливает test lock через `pip --isolated` с явным `https://pypi.org/simple`, hashes и binary-only. Глобальная среда не меняется. Если окружение уже подготовлено, `--install` можно опустить; точные версии всё равно проверяются.

Для другого **проектного** venv можно передать `--env .build-envs/another-name`. Окружение вне проекта или каталог без признаков venv отвергаются. Существующий `dist/DesktopPet.exe` не используется как выходной файл и не запускается.

Проверки перед сборкой: pip check, lock, реальные installed versions, отсутствие PyQt5, compile и pytest с Qt offscreen. Затем `python -m PyInstaller` вызывается с абсолютным spec и новыми каталогами:

```text
dist-test-security-<UTC timestamp>/DesktopPet.exe
build-test-security-<UTC timestamp>/
reports/verification/<UTC timestamp>-security-build/
```

Занятый выходной каталог не перезаписывается. До проверок и сборки сохраняется `source-manifest.json`: SHA256 исходников, тестов, build scripts, spec, pyproject, locks/provenance и PNG/ICO assets. `.env`, `.git`, личные данные и output-прототип в него не входят. Manifest повторно сравнивается после сборки и после подписания; изменение входов запрещает статус `built`.

`scripts/verify_bundle.py` читает новый EXE как данные, без запуска и без извлечения файлов на диск. Проверяются:

- Python tag 313 / `python313.dll`, отсутствие Qt5/PyQt5 entries;
- фактические PE FileVersion Qt6Core/Gui/Widgets и при наличии Svg — 6.12.0.0;
- AMD64, ASLR, DEP, manifest `asInvoker` / `uiAccess=false`;
- SHA256 всего кандидата и каждой исследованной Qt DLL.

Qt DLL декомпрессируются только в память с ограничением 64 MiB. Python bytecode не исполняется. Версия builder берётся из реально использованного окружения и записывается в отчёт; она не выводится догадкой из произвольного старого EXE.

Если `.ps1` запрещён политикой, используйте этот прямой Python CLI. Менять execution policy или обходить недоступный WindowsApps Python не требуется. `scripts/build_test.ps1` — только необязательная тонкая обёртка.

## Подписание

Пользователь сообщил, что личного сертификата **нет**. Поэтому аутентичная подпись сейчас остаётся pending: сборка без параметров подписания честно помечается unsigned. Самоподписанный сертификат как замена доверенному издателю не создаётся.

Когда появится личный code-signing сертификат с private key в `CurrentUser\My` и доверенный Windows SDK SignTool, доступен готовый шаг:

```powershell
python scripts/build_release.py --sign-thumbprint YOUR_40_HEX_CERT_THUMBPRINT --signtool "C:\Path\To\WindowsSDK\signtool.exe" --timestamp-url "https://YOUR_CERTIFICATE_PROVIDER_RFC3161_ENDPOINT"
```

Thumbprint — публичный идентификатор сертификата, не ключ и не пароль. Скрипт не принимает пароль или PFX через CLI/логи. Он вызывает SignTool с SHA256 file digest и RFC3161 SHA256 timestamp, затем `signtool verify /pa /all /v`. Отсутствие инструмента/сертификата или ошибка проверки не даёт успешного подписанного релиза. `asInvoker` не запрещает вручную запускать приложение повышенным, поэтому не используйте Run as administrator.

## Проверка и откат

Просмотрите `summary.json`, `source-manifest.json`, `installed-inventory.log`, `bundle.json` и при подписании `signed-bundle.json`/`verify-signature.log`. Нужны успешные проверки и неизменные хэши старых EXE. Результат без подписи нельзя объявлять доверенным подписанным издателем. Snapshot источников обеспечивает проверяемую привязку кандидата к рабочему дереву, но не обещает побайтно идентичные EXE между разными Windows/SDK/интерпретаторами.

Кандидат находится отдельно. Автоматической установки, публикации или подмены пользовательского EXE нет. Для отката достаточно продолжить пользоваться сохранённой прежней сборкой; её известные старые библиотеки при этом остаются старыми. Перед распространяемым релизом нужен запуск GUI/smoke на рабочем Qt6 и проверка подписанного файла, если подпись доступна.

## Границы security-обновления Qt

Qt 6.12.0 Windows wheel доступен на первичном [PyPI](https://pypi.org/project/PyQt6-Qt6/6.12.0/), в отличие от Qt5 5.15.19, у которого не опубликован Windows wheel. Выбранный Qt6 устраняет затронутые аудитом старые Qt5 SVG/data-URL версии.

Однако **«исправлены все CVE» не заявляется**. Новый [Qt advisory CVE-2026-105924](https://www.qt.io/blog/security-advisory-cve-2026-105924) относится к преобразованию недоверенного CBOR через QCborValue в JSON, затрагивает 6.12.0 и указывает исправления 6.12.1/6.11.3/6.8.10. Это приложение не импортирует QCborValue и не принимает CBOR; оно читает обычный JSON settings. На дату фикса проверенный Windows wheel 6.12.1 на PyPI отсутствовал. После его появления надо обновить pins/hashes и повторить проверки, а не выдумывать hash несуществующего файла.

## Offline-прототип

```powershell
python scripts/export_menu_preview.py --force
node output/menu-concepts/verify-menu.cjs
```

Экспорт остаётся в `output/menu-concepts/menu-preview.html`. В нём нет CDN scripts, внешних шрифтов или iframe: локальные статические SVG и inline PNG заменяют зависимости wrapper. CSP запрещает сеть (`connect-src 'none'`, `img-src data:`). Сохраняются выбор меню, реальное локальное движение и исходный idle-хвост. Browser/OS telemetry и расширения браузера находятся вне этой гарантии; живой browser QA в текущей среде не выполнялся.
