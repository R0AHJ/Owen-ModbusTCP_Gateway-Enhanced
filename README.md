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

Коды последних ошибок:

- `0` none
- `1` timeout
- `2` bad flag
- `3` hash mismatch
- `4` decode error
- `5` io error

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

Готовые примеры:

- [owen_config.single_trm138.com6.json](/D:/Python_Project/owen_config.single_trm138.com6.json)
- [owen_config.example.json](/D:/Python_Project/owen_config.example.json)
- [owen_config.com6.two_trm138.addr48_96.json](/D:/Python_Project/owen_config.com6.two_trm138.addr48_96.json)
- [owen_config.linux.json](/D:/Python_Project/owen_config.linux.json)
- [owen_config.windows.json](/D:/Python_Project/owen_config.windows.json)

Навигация по проекту:

- [PROJECT_FILES.md](/D:/Python_Project/PROJECT_FILES.md)
- [CHANGELOG_RU.md](/D:/Python_Project/CHANGELOG_RU.md)
- [deploy/linux/README_RU.md](/D:/Python_Project/deploy/linux/README_RU.md)

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

## Linux и автозапуск

Для установки на Linux с `systemd` используй:

- [deploy/linux/install.sh](/D:/Python_Project/deploy/linux/install.sh)
- [deploy/linux/owen-gateway.service.template](/D:/Python_Project/deploy/linux/owen-gateway.service.template)
- [deploy/linux/README_RU.md](/D:/Python_Project/deploy/linux/README_RU.md)
