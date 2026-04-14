#!/usr/bin/env bash
#===============================================================================
# Меню управления шлюзом OWEN-ModbusTCP Gateway для Linux
#===============================================================================
# Bash-меню для управления шлюзом RS-485 to Modbus TCP.
# Работает в Linux без зависимости от Python для базовых операций.
#
# Автор: MiniMax Agent
# Дата: 2026
#===============================================================================

set -euo pipefail

#===============================================================================
# Конфигурация
#===============================================================================
# Директория установки приложения
APP_DIR="${APP_DIR:-/opt/owen-gateway}"
# Директория конфигурации
CONFIG_DIR="${CONFIG_DIR:-/etc/owen-gateway}"
# Файл конфигурации шлюза
CONFIG_FILE="${CONFIG_DIR}/owen_config.json"
# Файл конфигурации зонда
PROBE_CONFIG="${CONFIG_DIR}/owen_probe.json"
# Имя системной службы
SERVICE_NAME="${SERVICE_NAME:-owen-gateway}"
# Путь к виртуальному окружению Python
VENV_BIN="${APP_DIR}/.venv/bin"

#-------------------------------------------------------------------------------
# Цвета для вывода в терминал
#-------------------------------------------------------------------------------
RED='\033[0;31m'          # Красный - ошибка
GREEN='\033[0;32m'        # Зеленый - успех
YELLOW='\033[1;33m'      # Желтый - предупреждение
BLUE='\033[0;34m'         # Синий - информация
CYAN='\033[0;36m'         # Голубой - заголовок
NC='\033[0m'              # Без цвета (сброс)

#-------------------------------------------------------------------------------
# Вспомогательные функции
#-------------------------------------------------------------------------------

# Вывод заголовка меню
print_header() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "   OWEN-ModbusTCP Gateway - Управление"
    echo "=============================================="
    echo -e "${NC}"
}

# Вывод статуса с цветовой индикацией
# Аргументы: статус (OK|WARNING|ERROR|INFO), сообщение
print_status() {
    local status="$1"
    local message="$2"
    case "$status" in
        "OK")
            echo -e "${GREEN}[OK]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[ПРЕДУПРЕЖДЕНИЕ]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ОШИБКА]${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}[ИНФО]${NC} $message"
            ;;
    esac
}

# Проверка прав суперпользователя
check_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        SUDO="sudo"
    else
        SUDO=""
    fi
    return 0
}

# Проверка наличия виртуального окружения Python
check_venv() {
    if [[ ! -d "${VENV_BIN}" ]]; then
        print_status "ERROR" "Виртуальное окружение Python не найдено: ${VENV_BIN}"
        return 1
    fi
    return 0
}

# Проверка наличия файла конфигурации
check_config() {
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        print_status "WARNING" "Файл конфигурации не найден: ${CONFIG_FILE}"
        return 1
    fi
    return 0
}

#-------------------------------------------------------------------------------
# Управление службой
#-------------------------------------------------------------------------------

# Показать статус службы
service_status() {
    echo -e "\n${BLUE}--- Статус службы ---${NC}"
    if systemctl is-active --quiet "${SERVICE_NAME}.service" 2>/dev/null; then
        print_status "OK" "Служба ${SERVICE_NAME} запущена"
        echo ""
        ${SUDO} systemctl status "${SERVICE_NAME}.service" --no-pager || true
    else
        print_status "WARNING" "Служба ${SERVICE_NAME} остановлена"
    fi
}

# Запустить службу
service_start() {
    echo -e "\n${BLUE}--- Запуск службы ---${NC}"
    check_venv || return 1
    ${SUDO} systemctl start "${SERVICE_NAME}.service"
    sleep 1
    service_status
}

# Остановить службу
service_stop() {
    echo -e "\n${BLUE}--- Остановка службы ---${NC}"
    ${SUDO} systemctl stop "${SERVICE_NAME}.service"
    print_status "OK" "Служба остановлена"
}

# Перезапустить службу
service_restart() {
    echo -e "\n${BLUE}--- Перезапуск службы ---${NC}"
    check_venv || return 1
    ${SUDO} systemctl restart "${SERVICE_NAME}.service"
    sleep 1
    service_status
}

# Показать логи службы
service_logs() {
    echo -e "\n${BLUE}--- Логи службы (последние 50 строк) ---${NC}"
    echo "Нажмите Ctrl+C для выхода"
    echo ""
    ${SUDO} journalctl -u "${SERVICE_NAME}.service" -n 50 -f --no-pager
}

# Показать только ошибки в логах
service_logs_error() {
    echo -e "\n${BLUE}--- Только ошибки в логах ---${NC}"
    ${SUDO} journalctl -u "${SERVICE_NAME}.service" -p err -n 50 --no-pager || true
}

#-------------------------------------------------------------------------------
# Инструменты конфигурации
#-------------------------------------------------------------------------------

# Показать сводку конфигурации
config_summary() {
    echo -e "\n${BLUE}--- Сводка конфигурации ---${NC}"
    check_config || return 1
    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config list-config --config "${CONFIG_FILE}"
}

# Показать список устройств на линии
config_list_line() {
    local line="${1:-1}"
    echo -e "\n${BLUE}--- Устройства на линии ${line} ---${NC}"
    check_config || return 1
    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config list-line --config "${CONFIG_FILE}" --line "${line}"
}

# Показать информацию о TRM138
config_show_trm138() {
    echo -e "\n${BLUE}--- Информация о TRM138 ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    echo "Поиск по:"
    echo "  1. Номер устройства"
    echo "  2. Базовый адрес"
    read -p "Выберите вариант: " option

    case "$option" in
        1)
            read -p "Номер устройства: " device
            PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config show-trm138 \
                --config "${CONFIG_FILE}" --line "${line}" --device "${device}"
            ;;
        2)
            read -p "Базовый адрес: " address
            PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config show-trm138 \
                --config "${CONFIG_FILE}" --line "${line}" --base-address "${address}"
            ;;
        *)
            print_status "ERROR" "Неверный вариант"
            ;;
    esac
}

# Добавить устройство TRM138
config_add_trm138() {
    echo -e "\n${BLUE}--- Добавить устройство TRM138 ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    read -p "Базовый адрес OWEN (например, 48): " address
    if [[ ! "$address" =~ ^[0-9]+$ ]]; then
        print_status "ERROR" "Неверный адрес"
        return 1
    fi

    read -p "Каналы [1-8]: " channels
    channels="${channels:-1-8}"

    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config add-trm138 \
        --config "${CONFIG_FILE}" --line "${line}" --base-address "${address}" --channels "${channels}"

    print_status "OK" "Устройство TRM138 добавлено. Для применения изменений перезапустите службу."
}

# Удалить устройство TRM138
config_remove_trm138() {
    echo -e "\n${BLUE}--- Удалить устройство TRM138 ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    read -p "Базовый адрес: " address
    if [[ ! "$address" =~ ^[0-9]+$ ]]; then
        print_status "ERROR" "Неверный адрес"
        return 1
    fi

    read -p "Подтвердите удаление? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config remove-trm138 \
            --config "${CONFIG_FILE}" --line "${line}" --base-address "${address}"
        print_status "OK" "Устройство удалено. Для применения изменений перезапустите службу."
    else
        print_status "INFO" "Отменено"
    fi
}

#===============================================================================
# ФУНКЦИИ УПРАВЛЕНИЯ ЛИНИЯМИ
#===============================================================================

# Показать список линий
line_list() {
    echo -e "\n${BLUE}--- Список линий ---${NC}"
    check_config || return 1
    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config list-lines --config "${CONFIG_FILE}"
}

# Показать параметры линии
line_show() {
    echo -e "\n${BLUE}--- Параметры линии ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config show-line --config "${CONFIG_FILE}" --line "${line}"
}

# Включить/выключить линию
line_toggle() {
    echo -e "\n${BLUE}--- Включить/выключить линию ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    echo "Выберите действие:"
    echo "  1. Включить линию"
    echo "  2. Выключить линию"
    read -p "Вариант: " action

    case "$action" in
        1)
            PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config line-enable \
                --config "${CONFIG_FILE}" --line "${line}"
            print_status "OK" "Линия ${line} включена"
            ;;
        2)
            PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config line-disable \
                --config "${CONFIG_FILE}" --line "${line}"
            print_status "OK" "Линия ${line} выключена"
            ;;
        *)
            print_status "ERROR" "Неверный вариант"
            return 1
            ;;
    esac
}

#===============================================================================
# НОВЫЕ ФУНКЦИИ УПРАВЛЕНИЯ КАНАЛАМИ
#===============================================================================

# Показать статус каналов устройства
config_channel_status() {
    echo -e "\n${BLUE}--- Статус каналов устройства ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    read -p "Базовый адрес OWEN: " address
    if [[ ! "$address" =~ ^[0-9]+$ ]]; then
        print_status "ERROR" "Неверный адрес"
        return 1
    fi

    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config channel-status \
        --config "${CONFIG_FILE}" --line "${line}" --base-address "${address}"
}

# Включить канал
config_enable_channel() {
    echo -e "\n${BLUE}--- Включить канал ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    read -p "Базовый адрес OWEN: " address
    if [[ ! "$address" =~ ^[0-9]+$ ]]; then
        print_status "ERROR" "Неверный адрес"
        return 1
    fi

    read -p "Номер канала (1-8): " channel
    if [[ ! "$channel" =~ ^[1-8]$ ]]; then
        print_status "ERROR" "Неверный номер канала (допускается 1-8)"
        return 1
    fi

    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config channel-enable \
        --config "${CONFIG_FILE}" --line "${line}" --base-address "${address}" --channel "${channel}"

    print_status "OK" "Канал CH${channel} включен. Для применения изменений перезапустите службу."
}

# Отключить канал
config_disable_channel() {
    echo -e "\n${BLUE}--- Отключить канал ---${NC}"
    check_config || return 1

    read -p "Номер линии [1]: " line
    line="${line:-1}"

    read -p "Базовый адрес OWEN: " address
    if [[ ! "$address" =~ ^[0-9]+$ ]]; then
        print_status "ERROR" "Неверный адрес"
        return 1
    fi

    read -p "Номер канала (1-8): " channel
    if [[ ! "$channel" =~ ^[1-8]$ ]]; then
        print_status "ERROR" "Неверный номер канала (допускается 1-8)"
        return 1
    fi

    read -p "Подтвердите отключение канала? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config channel-disable \
            --config "${CONFIG_FILE}" --line "${line}" --base-address "${address}" --channel "${channel}"
        print_status "OK" "Канал CH${channel} отключен. Для применения изменений перезапустите службу."
    else
        print_status "INFO" "Отменено"
    fi
}

#===============================================================================
# ФУНКЦИИ ВАЛИДАЦИИ КОНФИГУРАЦИИ
#===============================================================================

# Проверить конфигурацию
config_validate() {
    echo -e "\n${BLUE}--- Проверка конфигурации ---${NC}"
    check_config || return 1

    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config validate \
        --config "${CONFIG_FILE}"
}

# Сгенерировать карту Modbus
config_modbus_map() {
    echo -e "\n${BLUE}--- Генерация карты Modbus ---${NC}"
    check_config || return 1

    read -p "Путь для сохранения [оставить пустым для авто]: " output
    output="${output:-}"

    if [[ -z "$output" ]]; then
        PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config export-config \
            --config "${CONFIG_FILE}"
        local map_file="${CONFIG_FILE%.json}.modbus_map.md"
        print_status "OK" "Карта Modbus сохранена в: ${map_file}"
    else
        PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config export-config \
            --config "${CONFIG_FILE}" --output "${output}"
        print_status "OK" "Карта Modbus сохранена в: ${output}"
    fi
}

#-------------------------------------------------------------------------------
# Инструменты зонда
#-------------------------------------------------------------------------------

# Запустить диагностику
probe_run() {
    echo -e "\n${BLUE}--- Запуск диагностики ---${NC}"
    check_venv || return 1
    if [[ ! -f "${PROBE_CONFIG}" ]]; then
        print_status "WARNING" "Файл конфигурации зонда не найден: ${PROBE_CONFIG}"
        return 1
    fi
    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway.probe \
        --config "${PROBE_CONFIG}" --log-level INFO
}

#-------------------------------------------------------------------------------
# Системная информация
#-------------------------------------------------------------------------------

# Показать системную информацию
system_info() {
    echo -e "\n${BLUE}--- Системная информация ---${NC}"
    echo "Директория шлюза: ${APP_DIR}"
    echo "Директория конфигурации: ${CONFIG_DIR}"
    echo "Файл конфигурации: ${CONFIG_FILE}"
    echo "Имя службы: ${SERVICE_NAME}"
    echo ""
    echo "Версия Python:"
    "${VENV_BIN}/python" --version || echo "Не найдена"
    echo ""
    echo "Установленные пакеты:"
    "${VENV_BIN}/pip" list --format=freeze 2>/dev/null | head -10 || echo "Недоступно"
    echo ""
    echo "Доступные последовательные порты:"
    ls -la /dev/ttyUSB* /dev/ttyACM* /dev/ttyS* 2>/dev/null || echo "Последовательные порты не найдены"
    echo ""
    echo "Группы пользователя:"
    id || echo "Недоступно"
}

#-------------------------------------------------------------------------------
# Резервное копирование и экспорт
#-------------------------------------------------------------------------------

# Создать резервную копию
config_backup() {
    echo -e "\n${BLUE}--- Резервное копирование ---${NC}"
    check_config || return 1

    local backup_dir="/tmp/owen-gateway-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${backup_dir}"

    cp "${CONFIG_FILE}" "${backup_dir}/"
    if [[ -f "${PROBE_CONFIG}" ]]; then
        cp "${PROBE_CONFIG}" "${backup_dir}/"
    fi

    print_status "OK" "Резервная копия создана: ${backup_dir}"
    ls -la "${backup_dir}"
}

# Экспортировать конфигурацию
config_export() {
    echo -e "\n${BLUE}--- Экспорт конфигурации ---${NC}"
    check_config || return 1

    read -p "Путь для сохранения: " output
    if [[ -z "$output" ]]; then
        print_status "ERROR" "Требуется указать путь"
        return 1
    fi

    PYTHONPATH="${APP_DIR}" "${VENV_BIN}/python" -m owen_gateway config export-config \
        --config "${CONFIG_FILE}" --output "$output"

    print_status "OK" "Экспортировано в: $output"
}

#-------------------------------------------------------------------------------
# Главное меню
#-------------------------------------------------------------------------------

# Показать главное меню
show_menu() {
    print_header
    echo "Текущий статус:"
    if systemctl is-active --quiet "${SERVICE_NAME}.service" 2>/dev/null; then
        print_status "OK" "Служба запущена"
    else
        print_status "WARNING" "Служба остановлена"
    fi
    echo ""

    echo "Главное меню:"
    echo "  1. Управление службой"
    echo "  2. Инструменты конфигурации"
    echo "  3. Управление каналами"
    echo "  4. Управление линиями"
    echo "  5. Проверка конфигурации"
    echo "  6. Диагностика (зонд)"
    echo "  7. Системная информация"
    echo "  8. Резервное копирование"
    echo "  9. Просмотр логов"
    echo ""
    echo "  0. Выход"
    echo ""
}

# Меню управления службой
service_menu() {
    while true; do
        echo -e "\n${BLUE}--- Управление службой ---${NC}"
        echo "  1. Запустить службу"
        echo "  2. Остановить службу"
        echo "  3. Перезапустить службу"
        echo "  4. Показать статус"
        echo ""
        echo "  0. Назад в главное меню"
        echo ""
        read -p "Выберите вариант: " option

        case "$option" in
            1) service_start ;;
            2) service_stop ;;
            3) service_restart ;;
            4) service_status ;;
            0) break ;;
            *) print_status "ERROR" "Неверный вариант" ;;
        esac
    done
}

# Меню инструментов конфигурации
config_menu() {
    while true; do
        echo -e "\n${BLUE}--- Инструменты конфигурации ---${NC}"
        echo "  1. Показать сводку конфигурации"
        echo "  2. Список устройств на линии"
        echo "  3. Информация о TRM138"
        echo "  4. Добавить устройство TRM138"
        echo "  5. Удалить устройство TRM138"
        echo "  6. Сгенерировать карту Modbus"
        echo ""
        echo "  0. Назад в главное меню"
        echo ""
        read -p "Выберите вариант: " option

        case "$option" in
            1) config_summary ;;
            2)
                read -p "Номер линии [1]: " line
                line="${line:-1}"
                config_list_line "$line"
                ;;
            3) config_show_trm138 ;;
            4) config_add_trm138 ;;
            5) config_remove_trm138 ;;
            6) config_modbus_map ;;
            0) break ;;
            *) print_status "ERROR" "Неверный вариант" ;;
        esac
    done
}

#===============================================================================
# НОВОЕ МЕНЮ УПРАВЛЕНИЯ КАНАЛАМИ
#===============================================================================

# Меню управления каналами
channel_menu() {
    while true; do
        echo -e "\n${BLUE}--- Управление каналами ---${NC}"
        echo "  1. Показать статус всех каналов"
        echo "  2. Включить канал"
        echo "  3. Отключить канал"
        echo ""
        echo "  0. Назад в главное меню"
        echo ""
        read -p "Выберите вариант: " option

        case "$option" in
            1) config_channel_status ;;
            2) config_enable_channel ;;
            3) config_disable_channel ;;
            0) break ;;
            *) print_status "ERROR" "Неверный вариант" ;;
        esac
    done
}

# Меню проверки конфигурации
validate_menu() {
    while true; do
        echo -e "\n${BLUE}--- Проверка конфигурации ---${NC}"
        echo "  1. Проверить конфигурацию"
        echo "  2. Сгенерировать карту Modbus"
        echo ""
        echo "  0. Назад в главное меню"
        echo ""
        read -p "Выберите вариант: " option

        case "$option" in
            1) config_validate ;;
            2) config_modbus_map ;;
            0) break ;;
            *) print_status "ERROR" "Неверный вариант" ;;
        esac
    done
}

# Меню управления линиями
line_menu() {
    while true; do
        echo -e "\n${BLUE}--- Управление линиями ---${NC}"
        echo "  1. Список линий"
        echo "  2. Показать параметры линии"
        echo "  3. Включить/выключить линию"
        echo ""
        echo "  0. Назад в главное меню"
        echo ""
        read -p "Выберите вариант: " option

        case "$option" in
            1) line_list ;;
            2) line_show ;;
            3) line_toggle ;;
            0) break ;;
            *) print_status "ERROR" "Неверный вариант" ;;
        esac
    done
}

# Меню логов
logs_menu() {
    while true; do
        echo -e "\n${BLUE}--- Логи ---${NC}"
        echo "  1. Просмотр последних логов (50 строк)"
        echo "  2. Только ошибки"
        echo "  3. Следить за логами в реальном времени"
        echo ""
        echo "  0. Назад в главное меню"
        echo ""
        read -p "Выберите вариант: " option

        case "$option" in
            1) service_logs ;;
            2) service_logs_error ;;
            3)
                echo -e "\n${YELLOW}Для выхода нажмите Ctrl+C${NC}"
                ${SUDO} journalctl -u "${SERVICE_NAME}.service" -f --no-pager
                ;;
            0) break ;;
            *) print_status "ERROR" "Неверный вариант" ;;
        esac
    done
}

#-------------------------------------------------------------------------------
# Главная точка входа
#-------------------------------------------------------------------------------

main() {
    check_root

    # Проверка рабочей директории
    if [[ ! -d "${APP_DIR}" ]]; then
        print_status "WARNING" "Директория шлюза не найдена: ${APP_DIR}"
        echo "Пожалуйста, обновите APP_DIR или выполните install.sh."
        exit 1
    fi

    # Режим прямых команд
    if [[ $# -gt 0 ]]; then
        case "$1" in
            # Команды управления службой
            status)
                service_status
                ;;
            start)
                service_start
                ;;
            stop)
                service_stop
                ;;
            restart)
                service_restart
                ;;
            logs)
                service_logs
                ;;
            # Команды конфигурации
            config)
                shift
                case "${1:-}" in
                    summary) config_summary ;;
                    backup) config_backup ;;
                    export) shift; config_export ;;
                    validate) config_validate ;;
                    modbus-map) config_modbus_map ;;
                    *)
                        echo "Использование: $0 config [summary|backup|export <путь>|validate|modbus-map]"
                        exit 1
                        ;;
                esac
                ;;
            # Команды управления каналами
            channel)
                shift
                case "${1:-}" in
                    status) config_channel_status ;;
                    enable) config_enable_channel ;;
                    disable) config_disable_channel ;;
                    *)
                        echo "Использование: $0 channel [status|enable|disable]"
                        exit 1
                        ;;
                esac
                ;;
            # Прочие команды
            probe)
                probe_run
                ;;
            info)
                system_info
                ;;
            help|--help|-h)
                echo "OWEN-ModbusTCP Gateway - Меню управления"
                echo ""
                echo "Использование: $0 [команда|menu]"
                echo ""
                echo "Команды управления службой:"
                echo "  status    - показать статус службы"
                echo "  start     - запустить службу"
                echo "  stop      - остановить службу"
                echo "  restart   - перезапустить службу"
                echo "  logs      - показать логи"
                echo ""
                echo "Команды конфигурации:"
                echo "  config summary    - сводка конфигурации"
                echo "  config backup     - резервная копия"
                echo "  config export     - экспорт конфигурации"
                echo "  config validate   - проверка конфигурации"
                echo "  config modbus-map - карта Modbus"
                echo ""
                echo "Команды управления каналами:"
                echo "  channel status  - статус каналов"
                echo "  channel enable  - включить канал"
                echo "  channel disable - отключить канал"
                echo ""
                echo "Прочие команды:"
                echo "  probe - запуск диагностики"
                echo "  info  - системная информация"
                echo ""
                echo "Интерактивный режим: $0"
                exit 0
                ;;
            *)
                echo "Неизвестная команда: $1"
                echo "Используйте '$0 help' для справки"
                exit 1
                ;;
        esac
        exit 0
    fi

    # Интерактивный режим меню
    while true; do
        show_menu
        read -p "Выберите вариант: " option

        case "$option" in
            1) service_menu ;;
            2) config_menu ;;
            3) channel_menu ;;
            4) line_menu ;;
            5) validate_menu ;;
            6) probe_run ;;
            7) system_info ;;
            8) config_backup ;;
            9) logs_menu ;;
            0)
                echo "До свидания!"
                exit 0
                ;;
            *)
                print_status "ERROR" "Неверный вариант"
                ;;
        esac

        echo ""
        read -p "Нажмите Enter для продолжения..." dummy
    done
}

# Запуск главной функции
main "$@"
