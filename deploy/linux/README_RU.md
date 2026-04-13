# Развертывание OWEN-ModbusTCP Gateway на Linux

## Содержание

1. [Обзор](#обзор)
2. [Требования](#требования)
3. [Установка](#установка)
4. [Управление шлюзом](#управление-шлюзом)
5. [Управление каналами](#управление-каналами)
6. [Проверка конфигурации](#проверка-конфигурации)
7. [Обновление](#обновление)
8. [Удаление](#удаление)
9. [Решение проблем](#решение-проблем)

---

## Обзор

Шлюз OWEN-ModbusTCP Gateway обеспечивает преобразование протокола OWEN RS-485
в протокол Modbus TCP. Предназначен для подключения промышленных приборов OWEN
(преимущественно TRM138) к системам SCADA через интерфейс Modbus TCP.

### Компоненты дистрибутива

| Файл | Описание |
|------|----------|
| `install.sh` | Скрипт установки |
| `owen-gateway.sh` | Интерактивное bash-меню управления |
| `owen-gateway.service.template` | Шаблон systemd-сервиса |

---

## Требования

### Системные требования

- Операционная система: Linux с systemd
- Python 3.9+
- Права суперпользователя (sudo)
- Доступ к сети для Modbus TCP клиентов

### Необходимые пакеты

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3 python3-venv python3-pip rsync

# CentOS/RHEL
sudo yum install python3 python3-venv rsync

# Alpine
sudo apk add python3 py3-pip rsync
```

### Права доступа

Для доступа к USB-RS485 адаптеру пользователь сервиса должен иметь доступ
к устройству `/dev/ttyUSB*` или `/dev/ttyACM*`:

```bash
# Добавить пользователя в группу dialout
sudo usermod -a -G dialout <имя_пользователя>

# Перелогиниться для применения изменений
```

---

## Установка

### Быстрая установка

Из корня репозитория:

```bash
chmod +x deploy/linux/install.sh deploy/linux/owen-gateway.sh
sudo ./deploy/linux/install.sh
```

### Установка с параметрами

```bash
sudo APP_DIR=/srv/owen-gateway \
     CONFIG_DIR=/etc/owen-gateway \
     SERVICE_NAME=owen-gateway \
     SERVICE_USER=owen \
     SERVICE_GROUP=dialout \
     CONFIG_SOURCE=$PWD/owen_config.json \
     PROBE_CONFIG_SOURCE=$PWD/owen_probe.json \
     ./deploy/linux/install.sh
```

### Переменные установки

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `APP_DIR` | Директория приложения | `/opt/owen-gateway` |
| `CONFIG_DIR` | Директория конфигурации | `/etc/owen-gateway` |
| `SERVICE_NAME` | Имя systemd-сервиса | `owen-gateway` |
| `SERVICE_USER` | Пользователь сервиса | `root` |
| `SERVICE_GROUP` | Группа пользователя | `root` |
| `PYTHON_BIN` | Путь к Python | `python3` |
| `CONFIG_SOURCE` | Исходный файл конфига | - |
| `PROBE_CONFIG_SOURCE` | Исходный файл probe | - |

### Проверка после установки

```bash
# Проверить статус службы
sudo systemctl status owen-gateway

# Проверить доступность serial-порта
ls -la /dev/ttyUSB*

# Проверить прослушивание Modbus TCP
sudo ss -tlnp | grep 15020
```

---

## Управление шлюзом

### Интерактивное меню (рекомендуется)

```bash
sudo /opt/owen-gateway/owen-gateway.sh
```

Меню позволяет:
- Управлять службой (запуск/остановка/перезапуск/статус)
- Работать с конфигурацией (добавление/удаление устройств)
- **Управлять каналами** (включение/отключение)
- **Проверять конфигурацию** (валидация)
- Просматривать логи
- Создавать резервные копии
- Запускать диагностику

### Командный режим

```bash
# Статус службы
sudo /opt/owen-gateway/owen-gateway.sh status

# Запуск/остановка/перезапуск
sudo /opt/owen-gateway/owen-gateway.sh start
sudo /opt/owen-gateway/owen-gateway.sh stop
sudo /opt/owen-gateway/owen-gateway.sh restart

# Просмотр логов
sudo /opt/owen-gateway/owen-gateway.sh logs

# Системная информация
/opt/owen-gateway/owen-gateway.sh info

# Резервная копия конфигурации
/opt/owen-gateway/owen-gateway.sh config backup

# Проверка конфигурации
/opt/owen-gateway/owen-gateway.sh config validate

# Управление каналами
/opt/owen-gateway/owen-gateway.sh channel status
/opt/owen-gateway/owen-gateway.sh channel enable
/opt/owen-gateway/owen-gateway.sh channel disable

# Справка
/opt/owen-gateway/owen-gateway.sh help
```

### systemctl (альтернативно)

```bash
# Управление службой
sudo systemctl enable owen-gateway
sudo systemctl start owen-gateway
sudo systemctl stop owen-gateway
sudo systemctl restart owen-gateway

# Проверка статуса
systemctl status owen-gateway

# Просмотр логов
journalctl -u owen-gateway -f
journalctl -u owen-gateway -p err
```

---

## Управление каналами

Шлюз поддерживает включение/отключение отдельных каналов прибора без
удаления конфигурации. Отключенный канал не опрашивается.

### Через меню

1. Запустите меню: `sudo /opt/owen-gateway/owen-gateway.sh`
2. Выберите пункт **3. Управление каналами**
3. Выберите действие:
   - **1** - Показать статус всех каналов
   - **2** - Включить канал
   - **3** - Отключить канал

### Через командную строку

```bash
# Показать статус каналов
PYTHONPATH=/opt/owen-gateway \
/opt/owen-gateway/.venv/bin/python -m owen_gateway config channel-status \
    --config /etc/owen-gateway/owen_config.json \
    --line 1 --base-address 48

# Отключить канал CH3
PYTHONPATH=/opt/owen-gateway \
/opt/owen-gateway/.venv/bin/python -m owen_gateway config channel-disable \
    --config /etc/owen-gateway/owen_config.json \
    --line 1 --base-address 48 --channel 3

# Включить канал CH3
PYTHONPATH=/opt/owen-gateway \
/opt/owen-gateway/.venv/bin/python -m owen_gateway config channel-enable \
    --config /etc/owen-gateway/owen_config.json \
    --line 1 --base-address 48 --channel 3
```

### Примечания

- После изменения конфигурации необходимо перезапустить службу
- Отключенные каналы сохраняются в конфигурации и могут быть снова включены
- Отключение канала полезно при неисправности датчика или для экономии ресурсов

---

## Проверка конфигурации

Шлюз поддерживает проверку конфигурации на наличие ошибок и конфликтов адресов.

### Что проверяется

- **Пересечения OWEN адресов** на одной линии
- **Пересечения Modbus адресов** для одного Slave ID
- **Выход адресов за допустимый диапазон**
- **Отсутствие обязательных секций**

### Через меню

1. Запустите меню: `sudo /opt/owen-gateway/owen-gateway.sh`
2. Выберите пункт **4. Проверка конфигурации**
3. Выберите:
   - **1** - Проверить конфигурацию
   - **2** - Сгенерировать карту Modbus

### Через командную строку

```bash
# Проверить конфигурацию
PYTHONPATH=/opt/owen-gateway \
/opt/owen-gateway/.venv/bin/python -m owen_gateway config validate \
    --config /etc/owen-gateway/owen_config.json

# Сгенерировать карту Modbus
PYTHONPATH=/opt/owen-gateway \
/opt/owen-gateway/.venv/bin/python -m owen_gateway config export-config \
    --config /etc/owen-gateway/owen_config.json \
    --output /tmp/exported_config.json
```

---

## Обновление

### Полное обновление

```bash
# Остановить службу
sudo systemctl stop owen-gateway

# Создать резервную копию
sudo /opt/owen-gateway/owen-gateway.sh config backup

# Обновить код
cd <путь_к_репозиторию>
git pull
rsync -av --exclude='.venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='owen_config.json' \
    ./ /opt/owen-gateway/

# Обновить зависимости
sudo /opt/owen-gateway/.venv/bin/pip install -r /opt/owen-gateway/requirements.txt

# Запустить службу
sudo systemctl start owen-gateway

# Проверить статус
sudo systemctl status owen-gateway
```

### Обновление только конфигурации

```bash
# Сохранить текущую конфигурацию
cp /etc/owen-gateway/owen_config.json /tmp/owen_config_backup.json

# Проверить новую конфигурацию
PYTHONPATH=/opt/owen-gateway \
/opt/owen-gateway/.venv/bin/python -m owen_gateway config validate \
    --config /путь/к/новой/конфигурации.json

# Заменить конфигурацию
sudo cp /путь/к/новой/конфигурации.json /etc/owen-gateway/owen_config.json

# Перезапустить службу
sudo systemctl restart owen-gateway
```

---

## Удаление

### Удаление с сохранением данных

```bash
# Остановить службу
sudo systemctl stop owen-gateway

# Отключить автозапуск
sudo systemctl disable owen-gateway

# Удалить файлы сервиса
sudo rm /etc/systemd/system/owen-gateway.service
sudo systemctl daemon-reload

# Удалить приложение (конфигурация сохраняется)
sudo rm -rf /opt/owen-gateway
```

### Полное удаление

```bash
# Удалить всё
sudo systemctl stop owen-gateway
sudo systemctl disable owen-gateway
sudo rm /etc/systemd/system/owen-gateway.service
sudo systemctl daemon-reload
sudo rm -rf /opt/owen-gateway
sudo rm -rf /etc/owen-gateway

# Удалить пользователя (если создавался)
sudo userdel owen 2>/dev/null || true
```

---

## Решение проблем

### Служба не запускается

```bash
# Проверить логи
sudo journalctl -u owen-gateway -p err --no-pager

# Проверить конфигурацию
sudo /opt/owen-gateway/owen-gateway.sh config validate

# Проверить Modbus TCP порт
sudo ss -tlnp | grep 15020
```

### Python-меню не работает

Если при запуске Python CLI-меню возникают проблемы с кодировкой,
используйте **bash-меню** - оно работает без Python для базовых операций.

### Проблемы с serial-портом

```bash
# Проверить доступность порта
ls -la /dev/ttyUSB*

# Проверить права доступа
ls -la /dev/ttyUSB0
groups <имя_пользователя>

# Добавить права (если нужно)
sudo usermod -a -G dialout <имя_пользователя>
```

### Превышение лимита файлов

```bash
# Проверить лимиты
ulimit -n

# Увеличить лимиты для пользователя
sudo bash -c 'cat >> /etc/security/limits.d/owen.conf << EOF
owen    soft    nofile  65535
owen    hard    nofile  65535
EOF'
```

### Проверка связи с прибором

```bash
# Запустить probe
PYTHONPATH=/opt/owen-gateway \
/opt/owen-gateway/.venv/bin/python -m owen_gateway.probe \
    --config /etc/owen-gateway/owen_probe.json \
    --log-level DEBUG
```

---

## Карта регистров Modbus

Карта регистров генерируется автоматически при изменении конфигурации
и сохраняется в файл `*.modbus_map.md`.

Пример содержимого:

```markdown
# Generated Modbus Map

## Endpoint
- Modbus TCP: `0.0.0.0:15020`
- Service SlaveID: `100`

## Service Registers
| Register | Meaning |
|----------|---------|
| HR1 | Aggregated gateway status |
| HR2 | Last error code |
| HR3 | Success counter |
| ...
```

---

## Контакты и поддержка

При возникновении проблем создавайте issue на GitHub:
https://github.com/R0AHJ/Owen-ModbusTCP_Gateway
