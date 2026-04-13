# Industrial Gateway Templates

## OVEN RS-485 -> Modbus TCP

Шлюз для приборов OVEN, в первую очередь для `TRM138`.

Шлюз работает с полевыми устройствами только по протоколу OVEN через `RS-485`
и публикует данные клиентам через `Modbus TCP`.

## Что реализовано

- кодирование и декодирование кадров OVEN
- расчет hash параметра и CRC
- опрос одной или нескольких линий `RS-485`
- публикация данных через `Modbus TCP`
- сервисные регистры статуса и телеметрии
- публикация значения `rEAd` вместе с `time mark`
- декодирование параметров `TRM138`: `C.SP`, `HYSt`, `AL.t`
- запись `C.SP` через Modbus с последующей проверкой обратным чтением
- расчет маски состояния логических устройств в `HR48`
- изолированная обработка ошибок (сбой одного канала/прибора не прерывает опрос остальных)
- автоматическое восстановление соединения при обрыве линии
- расширенное логирование ошибок с контекстом

## Модель работы

- сервисные регистры публикуются в `SlaveID 1`
- `SlaveID` прибора равен базовому OVEN-адресу устройства
- `TRM138` читается только по OVEN-протоколу
- `time mark` публикуется отдельно и не влияет на статус канала

## Сервисные регистры

- `HR1` статус шлюза
- `HR2` последний код ошибки
- `HR3` счетчик успешных обменов
- `HR4` счетчик таймаутов
- `HR5` счетчик ошибок протокола
- `HR6` счетчик циклов опроса
- `HR10` статус линии 1
- `HR11` статус линии 2

Коды статуса шлюза:

- `1` ok
- `2` degraded
- `3` offline
- `4` protocol error
- `5` disconnected (обрыв линии)

Коды последних ошибок:

- `0` none
- `1` timeout
- `2` bad flag
- `3` hash mismatch
- `4` decode error
- `5` io error
- `6` serial init error
- `7` serial write error
- `8` serial read error
- `9` serial disconnected
- `10` device unreachable

## Карта TRM138

Для каждого прибора:

- `rEAd`: `HR16..HR31`
- статусы каналов: `HR40..HR47`
- маска логических устройств: `HR48`
- `C.SP`: `HR56..HR71`

Коды статуса канала:

- `0` disabled / no data / empty payload
- `1` ok
- `2` temporary communication error
- `3` protocol error
- `4` failed, reduced polling
- `5` reconnecting

`HR48` содержит битовую маску:

- `bit0..bit7 -> LU1..LU8`

## Параметры TRM138

Поддерживаемые параметры OVEN:

- `rEAd` -> `float32`
- `C.SP` -> `stored_dot`
- `HYSt` -> `stored_dot`
- `AL.t` -> `uint16`

Важно:

- `C.SP` и `AL.t` читаются по адресу канала так же, как `rEAd`
- `C.SP` использует OVEN-кодирование `stored_dot`
- поддерживаются `2`-байтовый и `3`-байтовый варианты `stored_dot`

Подтвержденные на реальном приборе примеры:

- `00 4b` -> `75.0`
- `13 e8` -> `100.0`
- `2b c2` -> `30.1`
- `20 24 ea` -> `94.5`

## Маска логических устройств

Шлюз рассчитывает `HR48` по следующим данным:

- измеренное значение канала `rEAd`
- уставка `C.SP`
- гистерезис `HYSt`
- характеристика выхода `AL.t`

`AL.t` опрашивается как внутренний параметр для каждого настроенного канала и
не публикуется в Modbus напрямую.

Поддерживаемые режимы `AL.t`:

- `1` direct hysteresis
- `2` reverse hysteresis
- `3` inside band
- `4` outside band

Готовые шаблоны конфигурации сейчас публикуют для записи только `C.SP`.
`HYSt` поддерживается на уровне протокола, но в штатных JSON-конфигах пока не
выводится в карту Modbus.

## Замечания по конфигурации

Раздел `health`:

- `fault_after_failures`
- `recovery_poll_interval_cycles`

Если в старом конфиге присутствует `stale_after_cycles`, он игнорируется.

Готовые примеры конфигураций:

- `owen_config.example.json` - базовый пример
- `owen_config.single_trm138.com6.json` - один TRM138 на Windows COM6
- `owen_config.com6.two_trm138.addr48_96.json` - два TRM138 на адресах 48 и 96
- `owen_config.linux.json` - конфигурация для Linux
- `owen_config.windows.json` - конфигурация для Windows

## Навигация по проекту

- [PROJECT_FILES.md](PROJECT_FILES.md) - структура проекта
- [CHANGELOG_RU.md](CHANGELOG_RU.md) - история изменений
- [OWEN_GATEWAY_GUIDE_RU.md](OWEN_GATEWAY_GUIDE_RU.md) - подробное руководство
- [deploy/linux/README_RU.md](deploy/linux/README_RU.md) - установка на Linux с systemd

## Установка

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

## Запуск

```bash
python -m owen_gateway --config owen_config.json
```

Пробный опрос:

```bash
python -m owen_gateway.probe --config owen_probe.com6.json --log-level INFO
```

Тесты:

```bash
python -m unittest discover -s tests
```

## Утилиты конфигурации

Интерактивное меню управления конфигурацией:

```bash
python -m owen_gateway config menu
```

Список доступных команд:

```bash
# Показать сводку конфигурации
python -m owen_gateway config list-config

# Добавить линию
python -m owen_gateway config set-line --line 1 --port COM6 --baudrate 9600

# Добавить TRM138
python -m owen_gateway config add-trm138 --line 1 --base-address 48 --channels 1-8

# Экспортировать конфигурацию
python -m owen_gateway config export-config --output backup_config.json
```

## Linux и автозапуск

Для установки на Linux с `systemd` используй:

- [deploy/linux/install.sh](deploy/linux/install.sh)
- [deploy/linux/owen-gateway.service.template](deploy/linux/owen-gateway.service.template)
- [deploy/linux/README_RU.md](deploy/linux/README_RU.md)

Bash-меню для управления шлюзом на Linux:

```bash
./deploy/linux/owen-gateway.sh
```

## Обработка ошибок

Шлюз устойчив к сбоям оборудования:

- **Изоляция каналов**: ошибка в одном канале не прерывает опрос остальных
- **Изоляция приборов**: сбой одного прибора не влияет на другие приборы на той же линии
- **Автоматическое восстановление**: при обрыве линии шлюз автоматически
  переподключается и продолжает работу
- **Статус обрыва**: при физическом обрыве линии регистр статуса линии (HR10/HR11)
  показывает `5` (disconnected)
- **Расширенное логирование**: все ошибки логируются с полным контекстом (bus, slave_id,
  point name, address, parameter)

Уровни логирования:

- `DEBUG` - подробная диагностика обмена данными
- `INFO` - операционные сообщения
- `WARNING` - временные сбои (таймауты)
- `ERROR` - протокольные ошибки и сбои оборудования