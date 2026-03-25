# Project Files

Краткое описание основных файлов и каталогов проекта.

## Корень проекта

- [README.md](/D:/Python_Project/README.md) - краткое описание проекта, текущая модель работы, запуск и базовая карта регистров.
- [OWEN_GATEWAY_GUIDE_RU.md](/D:/Python_Project/OWEN_GATEWAY_GUIDE_RU.md) - рабочая инструкция по эксплуатации шлюза.
- [MODBUS_MAP_SINGLE_TRM138.md](/D:/Python_Project/MODBUS_MAP_SINGLE_TRM138.md) - карта регистров для одного `TRM138`.
- [MODBUS_MAP_CURRENT_2LINE.md](/D:/Python_Project/MODBUS_MAP_CURRENT_2LINE.md) - карта для текущего двухлинейного сценария.
- [MODBUS_MAP_2BUS_16DEV.md](/D:/Python_Project/MODBUS_MAP_2BUS_16DEV.md) - расширенная карта для многоприборной схемы.
- [MODBUS_MULTI_DEVICE_SAME_MAP.md](/D:/Python_Project/MODBUS_MULTI_DEVICE_SAME_MAP.md) - описание сценария с одинаковой картой на разных `SlaveID`.
- [MULTI_LINE_GATEWAY.md](/D:/Python_Project/MULTI_LINE_GATEWAY.md) - заметки по многолинейному шлюзу.
- [CONFIG_UTILS.md](/D:/Python_Project/CONFIG_UTILS.md) - описание утилит и генерации конфигов.
- [RELEASE_NOTES_v0.1.0-pre1.md](/D:/Python_Project/RELEASE_NOTES_v0.1.0-pre1.md) - заметки к текущему prerelease.
- [SESSION_NOTES.md](/D:/Python_Project/SESSION_NOTES.md) - журнал прошлой отладки и промежуточных наблюдений.
- [requirements.txt](/D:/Python_Project/requirements.txt) - зависимости Python.

## Шаблоны конфигурации

- [owen_config.example.json](/D:/Python_Project/owen_config.example.json) - базовый пример для одного прибора.
- [owen_config.single_trm138.com6.json](/D:/Python_Project/owen_config.single_trm138.com6.json) - готовый пример для одного `TRM138` на `COM6`.
- [owen_config.com6.two_trm138.addr48_96.json](/D:/Python_Project/owen_config.com6.two_trm138.addr48_96.json) - пример для двух приборов с базовыми адресами `48` и `96`.
- [owen_config.multi_device.same_map.example.json](/D:/Python_Project/owen_config.multi_device.same_map.example.json) - пример, где одинаковая карта используется на разных `SlaveID`.
- [owen_config.multiline.example.json](/D:/Python_Project/owen_config.multiline.example.json) - пример многолинейной конфигурации.
- [owen_config.windows.json](/D:/Python_Project/owen_config.windows.json) - шаблон для Windows.
- [owen_config.linux.json](/D:/Python_Project/owen_config.linux.json) - шаблон для Linux.
- [owen_probe.com6.json](/D:/Python_Project/owen_probe.com6.json) - конфиг для утилиты `probe`.
- [owen_config.com6.2400.addr96.json](/D:/Python_Project/owen_config.com6.2400.addr96.json) - точечный пример под конкретную линию.
- [owen_config.com6.9600.addr96.json](/D:/Python_Project/owen_config.com6.9600.addr96.json) - точечный пример под конкретную линию.
- [owen_config.com6.test.json](/D:/Python_Project/owen_config.com6.test.json) - старый тестовый пример.

## Основной код шлюза

- [owen_gateway/__main__.py](/D:/Python_Project/owen_gateway/__main__.py) - точка входа `python -m owen_gateway`.
- [owen_gateway/cli.py](/D:/Python_Project/owen_gateway/cli.py) - CLI, загрузка конфига и запуск сервиса.
- [owen_gateway/service.py](/D:/Python_Project/owen_gateway/service.py) - основной цикл опроса, публикация в `Modbus TCP`, статус каналов и `HR48`.
- [owen_gateway/config.py](/D:/Python_Project/owen_gateway/config.py) - модели и валидация конфигурации.
- [owen_gateway/protocol.py](/D:/Python_Project/owen_gateway/protocol.py) - OVEN-протокол, `CRC`, `hash`, декодирование payload, включая `stored_dot`.
- [owen_gateway/serial_client.py](/D:/Python_Project/owen_gateway/serial_client.py) - обмен по последовательному порту.
- [owen_gateway/modbus_server.py](/D:/Python_Project/owen_gateway/modbus_server.py) - сервер `Modbus TCP` и публикация регистров.
- [owen_gateway/encoding.py](/D:/Python_Project/owen_gateway/encoding.py) - преобразование значений в Modbus-регистры.
- [owen_gateway/probe.py](/D:/Python_Project/owen_gateway/probe.py) - отдельная утилита для ручной проверки чтения параметров прибора.
- [owen_gateway/config_tools.py](/D:/Python_Project/owen_gateway/config_tools.py) - генерация конфигов и Markdown-карт.
- [owen_gateway/trm138_parameters.py](/D:/Python_Project/owen_gateway/trm138_parameters.py) - каталог параметров `TRM138`.

## Документы на прибор и протокол

- [owen_gateway/DOC/re_trm138.pdf](/D:/Python_Project/owen_gateway/DOC/re_trm138.pdf) - руководство по эксплуатации `TRM138`.
- [owen_gateway/DOC/oficialnoe_opisanie_protokola_obmena_po_rs485_priborov_firmi_oven_15.01.07.pdf](/D:/Python_Project/owen_gateway/DOC/oficialnoe_opisanie_protokola_obmena_po_rs485_priborov_firmi_oven_15.01.07.pdf) - официальное описание протокола OVEN по `RS-485`.

## Тесты

- [tests/test_cli.py](/D:/Python_Project/tests/test_cli.py) - тесты CLI.
- [tests/test_config.py](/D:/Python_Project/tests/test_config.py) - тесты загрузки и валидации конфигов.
- [tests/test_config_tools.py](/D:/Python_Project/tests/test_config_tools.py) - тесты генерации конфигов и карт.
- [tests/test_encoding.py](/D:/Python_Project/tests/test_encoding.py) - тесты упаковки Modbus-значений.
- [tests/test_owen_protocol.py](/D:/Python_Project/tests/test_owen_protocol.py) - тесты OVEN-протокола и декодирования `stored_dot`.
- [tests/test_service.py](/D:/Python_Project/tests/test_service.py) - тесты логики сервиса и расчета ЛУ.

## Служебные каталоги

- `owen_gateway/` - основной пакет проекта.
- `tests/` - автотесты.
- `archive/` - архивные материалы проекта.
- `.venv/` - локальное виртуальное окружение.
- `.idea/` - локальные файлы IDE.
- `__pycache__/` - кэш Python.
