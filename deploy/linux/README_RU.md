# Развертывание на Linux

## Что входит

- `install.sh` - установка проекта в `/opt/owen-gateway`, создание `venv`,
  копирование конфига и регистрация `systemd`-сервиса
- `owen-gateway.service.template` - шаблон unit-файла

## Требования

- Linux с `systemd`
- `python3`
- `python3-venv`
- `rsync`
- права `sudo`

Для доступа к USB-RS485 адаптеру пользователь сервиса должен иметь доступ к
устройству `/dev/ttyUSB*` или `/dev/ttyACM*`. Обычно это решается добавлением
пользователя в группу `dialout`.

## Быстрая установка

Из корня репозитория:

```bash
chmod +x deploy/linux/install.sh
sudo SERVICE_USER=owen SERVICE_GROUP=dialout ./deploy/linux/install.sh
```

По умолчанию будут использованы:

- код проекта: `/opt/owen-gateway`
- рабочий конфиг: `/etc/owen-gateway/owen_config.json`
- probe-конфиг: `/etc/owen-gateway/owen_probe.json`
- имя сервиса: `owen-gateway`

## Переменные установки

Можно переопределить:

- `APP_DIR`
- `CONFIG_DIR`
- `SERVICE_NAME`
- `SERVICE_USER`
- `SERVICE_GROUP`
- `PYTHON_BIN`
- `CONFIG_SOURCE`
- `PROBE_CONFIG_SOURCE`

Пример:

```bash
sudo APP_DIR=/srv/owen-gateway \
     CONFIG_DIR=/etc/owen-gateway \
     SERVICE_NAME=owen-gateway \
     SERVICE_USER=owen \
     SERVICE_GROUP=dialout \
     CONFIG_SOURCE=$PWD/owen_config.linux.json \
     ./deploy/linux/install.sh
```

## Автозапуск

После установки сервис будет зарегистрирован и включен в автозапуск:

```bash
sudo systemctl enable owen-gateway
sudo systemctl start owen-gateway
```

Проверка:

```bash
systemctl status owen-gateway
journalctl -u owen-gateway -f
```

## Проверка probe

Если нужен отдельный пробный опрос:

```bash
PYTHONPATH=/opt/owen-gateway /opt/owen-gateway/.venv/bin/python -m owen_gateway.probe \
  --config /etc/owen-gateway/owen_probe.json \
  --log-level INFO
```

## Проверка конфиг-утилит

Примеры:

```bash
PYTHONPATH=/opt/owen-gateway /opt/owen-gateway/.venv/bin/python -m owen_gateway config list-config --config /etc/owen-gateway/owen_config.json
PYTHONPATH=/opt/owen-gateway /opt/owen-gateway/.venv/bin/python -m owen_gateway config list-line --config /etc/owen-gateway/owen_config.json --line 1
PYTHONPATH=/opt/owen-gateway /opt/owen-gateway/.venv/bin/python -m owen_gateway config show-trm138 --config /etc/owen-gateway/owen_config.json --line 1 --base-address 96
```

## Что проверить на сервере после установки

1. Видит ли система адаптер: `ls -l /dev/ttyUSB*`
2. Имеет ли пользователь сервиса доступ к порту
3. Поднимается ли `Modbus TCP` на нужном адресе и порту
4. Читается ли `rEAd`
5. Работает ли запись `C.SP` и подтверждается ли она обратным чтением
