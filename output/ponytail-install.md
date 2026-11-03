# Установка core skill Ponytail

Установлен только `skills/ponytail/SKILL.md` в проект: `.agents/skills/ponytail/SKILL.md` внутри `Desktop-Pets`. Глобальные каталоги, родительский `.agents`, hooks, marketplace и AGENTS.md не изменены.

Источник: https://raw.githubusercontent.com/DietrichGebert/ponytail/main/skills/ponytail/SKILL.md

Репозиторий: https://github.com/DietrichGebert/ponytail ; ref: `main`. Содержимое получено через read-only web tool и перенесено через apply_patch без дополнительных инструкций внутри upstream-файла. 45 строк; license MIT. Commit SHA не подтверждён: GitHub commits API недоступен через web tool. Поэтому `main` не выдаётся за неизменяемую ревизию. Зафиксирован SHA256 фактически установленного файла: `bf3fd991094490a56ecd55dc5edcec275cff8bf7fb93ef0bea4b9a781e71ce3b`.

Стандартный helper был запущен ровно один раз через Inkscape Python с `--repo DietrichGebert/ponytail --path skills/ponytail --dest <Desktop-Pets>/.agents/skills --method download`, без escalation. Результат exit 1: `urllib.error.URLError`, причина `PermissionError [WinError 10013]` при соединении сокета. Повторных shell-сетевых попыток не было. После этого применён разрешённый fallback: общедоступный raw source прочитан web-инструментом, записан в разрешённый локальный путь через apply_patch. Запись успешна.

Навык доступен для явного чтения уже сейчас. Для автоматического обнаружения на следующем ходе может потребоваться открыть `Desktop-Pets` как workspace: текущая сессия начиналась в родительском `pet`. Автоматическое обнаружение из родительского workspace не проверено.
