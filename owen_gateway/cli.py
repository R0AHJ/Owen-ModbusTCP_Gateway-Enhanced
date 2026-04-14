from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from owen_gateway.config import load_config
from owen_gateway.config_tools import (
    add_trm138_device,
    enable_channel,
    disable_channel,
    disable_line,
    enable_line,
    export_config_document,
    get_channel_status,
    get_line_devices,
    list_lines,
    load_config_document,
    parse_channels,
    remove_line,
    remove_trm138_device,
    render_config_summary,
    render_device_details,
    render_line_devices,
    render_validation_report,
    save_config_document,
    set_line,
    show_line,
    update_trm138_channels,
    validate_config,
    write_generated_modbus_map,
)
from owen_gateway.service import OwenGatewayService


def build_run_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m owen_gateway",
        description="OVEN RS-485 to Modbus-TCP gateway",
    )
    parser.add_argument("--config", default="owen_config.json", help="path to config json")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="logging level",
    )
    return parser


def build_config_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m owen_gateway config",
        description="OVEN gateway config tools",
    )
    subparsers = parser.add_subparsers(dest="config_command", required=True)

    line_parser = subparsers.add_parser("set-line", help="create or update serial line")
    line_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    line_parser.add_argument("--line", type=int, required=True, help="line number 1..2")
    line_parser.add_argument("--port", required=True, help="serial port, for example COM6")
    line_parser.add_argument("--baudrate", type=int, required=True, help="serial baudrate")
    line_parser.add_argument("--bytesize", type=int, default=8, choices=[7, 8], help="serial bytesize")
    line_parser.add_argument("--parity", default="N", choices=["N", "E", "O"], help="serial parity")
    line_parser.add_argument("--stopbits", type=int, default=1, choices=[1, 2], help="serial stop bits")
    line_parser.add_argument("--timeout-ms", type=int, default=1000, help="serial timeout in ms")
    line_parser.add_argument("--address-bits", type=int, default=8, choices=[8, 11], help="OVEN address width")
    line_parser.add_argument("--poll-interval-ms", type=int, default=1000, help="poll interval in ms")
    line_parser.add_argument("--slave-base", type=int, help="starting SlaveID for this line")

    trm_parser = subparsers.add_parser("add-trm138", help="add TRM138 points to selected line")
    trm_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    trm_parser.add_argument("--line", type=int, required=True, help="line number 1..2")
    trm_parser.add_argument("--base-address", type=int, required=True, help="TRM138 base OVEN address")
    trm_parser.add_argument(
        "--channels",
        default="1-8",
        help='channels to poll, for example "1-8" or "1,2,5"',
    )
    trm_parser.add_argument("--tag", help="legacy alias, ignored for generated point names")

    list_parser = subparsers.add_parser("list-config", help="print configured lines and devices")
    list_parser.add_argument("--config", default="owen_config.json", help="path to config json")

    show_line_parser = subparsers.add_parser("list-line", help="print devices on selected line")
    show_line_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    show_line_parser.add_argument("--line", type=int, required=True, help="line number 1..2")

    show_trm_parser = subparsers.add_parser("show-trm138", help="print selected TRM138 details")
    show_trm_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    show_trm_parser.add_argument("--line", type=int, required=True, help="line number 1..2")
    show_trm_parser.add_argument("--device", type=int, help="device number on line")
    show_trm_parser.add_argument("--base-address", type=int, help="TRM138 base OVEN address")
    show_trm_parser.add_argument("--tag", help="service tag")

    remove_line_parser = subparsers.add_parser("remove-line", help="remove line and all its devices")
    remove_line_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    remove_line_parser.add_argument("--line", type=int, required=True, help="line number 1..2")

    remove_trm_parser = subparsers.add_parser("remove-trm138", help="remove TRM138 from selected line")
    remove_trm_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    remove_trm_parser.add_argument("--line", type=int, required=True, help="line number 1..2")
    remove_trm_parser.add_argument("--device", type=int, help="device number on line")
    remove_trm_parser.add_argument("--base-address", type=int, help="TRM138 base OVEN address")
    remove_trm_parser.add_argument("--tag", help="service tag")

    update_trm_parser = subparsers.add_parser(
        "set-trm138-channels",
        help="change polled channels for existing TRM138",
    )
    update_trm_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    update_trm_parser.add_argument("--line", type=int, required=True, help="line number 1..2")
    update_trm_parser.add_argument("--channels", required=True, help='channels, for example "1-6,8"')
    update_trm_parser.add_argument("--device", type=int, help="device number on line")
    update_trm_parser.add_argument("--base-address", type=int, help="TRM138 base OVEN address")
    update_trm_parser.add_argument("--tag", help="service tag")

    menu_parser = subparsers.add_parser("menu", help="interactive config menu")
    menu_parser.add_argument("--config", default="owen_config.json", help="path to config json")

    export_parser = subparsers.add_parser("export-config", help="save current config to another file")
    export_parser.add_argument("--config", default="owen_config.json", help="source config json")
    export_parser.add_argument("--output", required=True, help="target config json")

    # -------------------------------------------------------------------------
    # Новые команды для управления каналами
    # -------------------------------------------------------------------------
    channel_status_parser = subparsers.add_parser(
        "channel-status",
        help="показать статус каналов устройства",
    )
    channel_status_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    channel_status_parser.add_argument("--line", type=int, required=True, help="номер линии 1..2")
    channel_status_parser.add_argument("--device", type=int, help="номер устройства")
    channel_status_parser.add_argument("--base-address", type=int, help="базовый адрес OWEN")

    channel_enable_parser = subparsers.add_parser(
        "channel-enable",
        help="включить канал для опроса",
    )
    channel_enable_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    channel_enable_parser.add_argument("--line", type=int, required=True, help="номер линии 1..2")
    channel_enable_parser.add_argument("--channel", type=int, required=True, help="номер канала 1..8")
    channel_enable_parser.add_argument("--device", type=int, help="номер устройства")
    channel_enable_parser.add_argument("--base-address", type=int, help="базовый адрес OWEN")

    channel_disable_parser = subparsers.add_parser(
        "channel-disable",
        help="отключить канал от опроса",
    )
    channel_disable_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    channel_disable_parser.add_argument("--line", type=int, required=True, help="номер линии 1..2")
    channel_disable_parser.add_argument("--channel", type=int, required=True, help="номер канала 1..8")
    channel_disable_parser.add_argument("--device", type=int, help="номер устройства")
    channel_disable_parser.add_argument("--base-address", type=int, help="базовый адрес OWEN")

    # -------------------------------------------------------------------------
    # Команда проверки конфигурации
    # -------------------------------------------------------------------------
    validate_parser = subparsers.add_parser(
        "validate",
        help="проверить конфигурацию на ошибки",
    )
    validate_parser.add_argument("--config", default="owen_config.json", help="path to config json")

    # -------------------------------------------------------------------------
    # Команды управления линиями
    # -------------------------------------------------------------------------
    list_lines_parser = subparsers.add_parser(
        "list-lines",
        help="показать все линии",
    )
    list_lines_parser.add_argument("--config", default="owen_config.json", help="path to config json")

    show_line_parser = subparsers.add_parser(
        "show-line",
        help="показать параметры линии",
    )
    show_line_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    show_line_parser.add_argument("--line", type=int, required=True, help="номер линии 1..2")

    line_enable_parser = subparsers.add_parser(
        "line-enable",
        help="включить линию",
    )
    line_enable_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    line_enable_parser.add_argument("--line", type=int, required=True, help="номер линии 1..2")

    line_disable_parser = subparsers.add_parser(
        "line-disable",
        help="выключить линию",
    )
    line_disable_parser.add_argument("--config", default="owen_config.json", help="path to config json")
    line_disable_parser.add_argument("--line", type=int, required=True, help="номер линии 1..2")

    return parser


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["config"]:
        return _run_config_tool(argv[1:])

    parser = build_run_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_config(args.config)
    service = OwenGatewayService(config)
    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        return 0
    return 0


def _run_config_tool(argv: list[str]) -> int:
    parser = build_config_parser()
    args = parser.parse_args(argv)
    payload = load_config_document(args.config)

    if args.config_command == "set-line":
        bus_payload = set_line(
            payload,
            line=args.line,
            port=args.port,
            baudrate=args.baudrate,
            bytesize=args.bytesize,
            parity=args.parity,
            stopbits=args.stopbits,
            timeout_ms=args.timeout_ms,
            poll_interval_ms=args.poll_interval_ms,
            address_bits=args.address_bits,
            modbus_slave_base=args.slave_base,
        )
        save_config_document(args.config, payload)
        map_path = write_generated_modbus_map(args.config, payload)
        print(
            "updated line "
            f"{bus_payload['name']}: port={bus_payload['serial']['port']} "
            f"baudrate={bus_payload['serial']['baudrate']} "
            f"parity={bus_payload['serial']['parity']}"
        )
        print(f"generated map: {map_path}")
        return 0

    if args.config_command == "add-trm138":
        result = add_trm138_device(
            payload,
            line=args.line,
            base_address=args.base_address,
            channels=parse_channels(args.channels),
            tag=args.tag,
        )
        save_config_document(args.config, payload)
        map_path = write_generated_modbus_map(args.config, payload)
        print(
            "added TRM138 "
            f"on {result['bus']} "
            f"device={result['device']} base_address={result['base_address']} "
            f"channels={result['channels']}"
        )
        print(f"generated map: {map_path}")
        return 0

    if args.config_command == "list-config":
        print(render_config_summary(payload))
        return 0

    if args.config_command == "list-line":
        print(render_line_devices(payload, args.line))
        return 0

    if args.config_command == "show-trm138":
        if args.device is None and args.base_address is None and not args.tag:
            parser.error("show-trm138 requires --device or --base-address or --tag")
        print(
            render_device_details(
                payload,
                line=args.line,
                device=args.device,
                base_address=args.base_address,
                tag=args.tag,
            )
        )
        return 0

    if args.config_command == "remove-line":
        result = remove_line(payload, line=args.line)
        save_config_document(args.config, payload)
        map_path = write_generated_modbus_map(args.config, payload)
        print(
            f"removed line{result['line']}: "
            f"devices_points_removed={result['removed_points']}"
        )
        print(f"generated map: {map_path}")
        return 0

    if args.config_command == "remove-trm138":
        if args.device is None and args.base_address is None and not args.tag:
            parser.error("remove-trm138 requires --device or --base-address or --tag")
        result = remove_trm138_device(
            payload,
            line=args.line,
            device=args.device,
            base_address=args.base_address,
            tag=args.tag,
        )
        save_config_document(args.config, payload)
        map_path = write_generated_modbus_map(args.config, payload)
        print(
            "removed TRM138 "
            f"on {result['bus']} "
            f"device={result['device']} base_address={result['base_address']} "
            f"points={result['removed_points']}"
        )
        print(f"generated map: {map_path}")
        return 0

    if args.config_command == "menu":
        return _run_config_menu(args.config)

    if args.config_command == "set-trm138-channels":
        if args.device is None and args.base_address is None and not args.tag:
            parser.error("set-trm138-channels requires --device or --base-address or --tag")
        result = update_trm138_channels(
            payload,
            line=args.line,
            channels=parse_channels(args.channels),
            device=args.device,
            base_address=args.base_address,
            tag=args.tag,
        )
        save_config_document(args.config, payload)
        map_path = write_generated_modbus_map(args.config, payload)
        print(
            "updated TRM138 channels "
            f"on {result['bus']} "
            f"device={result['device']} base_address={result['base_address']} "
            f"channels={result['channels']}"
        )
        print(f"generated map: {map_path}")
        return 0

    if args.config_command == "export-config":
        _source, target = export_config_document(args.config, args.output, payload)
        print(f"exported config: {target}")
        print(f"generated map: {target.with_name(f'{target.stem}.modbus_map.md')}")
        return 0

    # -------------------------------------------------------------------------
    # Обработчики команд управления каналами
    # -------------------------------------------------------------------------

    if args.config_command == "channel-status":
        # Показать статус каналов устройства
        if args.device is None and args.base_address is None:
            parser.error("channel-status требует --device или --base-address")
        channels = get_channel_status(
            payload,
            line=args.line,
            device=args.device,
            base_address=args.base_address,
        )
        print(f"\nСтатус каналов на линии {args.line}:")
        print("-" * 40)
        for ch in channels:
            if ch["configured"]:
                status = "включен" if ch["enabled"] else "отключен"
                print(f"  CH{ch['channel']}: адрес={ch['address']} [{status}]")
            else:
                print(f"  CH{ch['channel']}: не настроен")
        return 0

    if args.config_command == "channel-enable":
        # Включить канал
        if args.device is None and args.base_address is None:
            parser.error("channel-enable требует --device или --base-address")
        result = enable_channel(
            payload,
            line=args.line,
            channel=args.channel,
            device=args.device,
            base_address=args.base_address,
        )
        save_config_document(args.config, payload)
        print(f"Канал CH{args.channel} включен на устройстве {result['device']}")
        print(f"Линия: {result['bus']}, адрес: {result['channel_base_address']}")
        return 0

    if args.config_command == "channel-disable":
        # Отключить канал
        if args.device is None and args.base_address is None:
            parser.error("channel-disable требует --device или --base-address")
        result = disable_channel(
            payload,
            line=args.line,
            channel=args.channel,
            device=args.device,
            base_address=args.base_address,
        )
        save_config_document(args.config, payload)
        print(f"Канал CH{args.channel} отключен на устройстве {result['device']}")
        print(f"Линия: {result['bus']}, адрес: {result['channel_base_address']}")
        return 0

    # -------------------------------------------------------------------------
    # Обработчик проверки конфигурации
    # -------------------------------------------------------------------------

    if args.config_command == "validate":
        # Проверить конфигурацию на ошибки
        issues = validate_config(payload)
        print(render_validation_report(issues))
        return 0 if not issues else 1

    # -------------------------------------------------------------------------
    # Обработчики команд управления линиями
    # -------------------------------------------------------------------------

    if args.config_command == "list-lines":
        # Показать список всех линий
        lines = list_lines(payload)
        if not lines:
            print("Линии не настроены")
        else:
            print("\nНастроенные линии:")
            print("-" * 50)
            for line in lines:
                status = "включена" if line["enabled"] else "выключена"
                print(f"  {line['name']}: {status}")
                print(f"    Порт: {line['port']}, Скорость: {line['baudrate']} бод")
        return 0

    if args.config_command == "show-line":
        # Показать параметры линии
        print(show_line(payload, line=args.line))
        return 0

    if args.config_command == "line-enable":
        # Включить линию
        result = enable_line(payload, line=args.line)
        save_config_document(args.config, payload)
        print(f"Линия {result['bus']} включена")
        print(f"Порт: {result['port']}")
        return 0

    if args.config_command == "line-disable":
        # Выключить линию
        result = disable_line(payload, line=args.line)
        save_config_document(args.config, payload)
        print(f"Линия {result['bus']} выключена")
        print(f"Порт: {result['port']}")
        return 0

    parser.error(f"unsupported config command: {args.config_command}")
    return 2


def _run_config_menu(config_path: str) -> int:
    while True:
        payload = load_config_document(config_path)
        print()
        print("OVEN Gateway Config Menu")
        print("------------------------")
        print("1. Show config summary")
        print("2. Line submenu")
        print("3. Set or update line")
        print("4. Add TRM138")
        print("5. Remove line")
        print("6. Export config")
        print("7. Regenerate Modbus map")
        print("0. Exit")
        choice = input("Select action: ").strip()

        try:
            if choice == "1":
                print()
                print(render_config_summary(payload))
                _pause_menu()
                continue
            if choice == "2":
                line = int(input("Line number (1..2): ").strip())
                _run_line_submenu(config_path, line)
                continue
            if choice == "3":
                line = int(input("Line number (1..2): ").strip())
                port = input("Serial port: ").strip()
                baudrate = int(input("Baudrate [9600]: ").strip() or "9600")
                bytesize = int(input("Bytesize [8]: ").strip() or "8")
                parity = (input("Parity [N]: ").strip() or "N").upper()
                stopbits = int(input("Stopbits [1]: ").strip() or "1")
                timeout_ms = int(input("Timeout ms [1000]: ").strip() or "1000")
                address_bits = int(input("Address bits [8]: ").strip() or "8")
                poll_interval_ms = int(input("Poll interval ms [1000]: ").strip() or "1000")
                slave_base_raw = input("Slave base [default]: ").strip()
                set_line(
                    payload,
                    line=line,
                    port=port,
                    baudrate=baudrate,
                    bytesize=bytesize,
                    parity=parity,
                    stopbits=stopbits,
                    timeout_ms=timeout_ms,
                    address_bits=address_bits,
                    poll_interval_ms=poll_interval_ms,
                    modbus_slave_base=int(slave_base_raw) if slave_base_raw else None,
                )
            elif choice == "4":
                line = int(input("Line number (1..2): ").strip())
                base_address = int(input("Base OVEN address: ").strip())
                channels = parse_channels(input("Channels [1-8]: ").strip() or "1-8")
                add_trm138_device(
                    payload,
                    line=line,
                    base_address=base_address,
                    channels=channels,
                )
            elif choice == "5":
                line = int(input("Line number (1..2): ").strip())
                confirm = input(f"Remove line{line} and all devices? [y/N]: ").strip().lower()
                if confirm == "y":
                    remove_line(payload, line=line)
                else:
                    print("cancelled")
                    continue
            elif choice == "6":
                output_path = input("Export target path: ").strip()
                if not output_path:
                    print("cancelled")
                    continue
                _source, target = export_config_document(config_path, output_path, payload)
                print(f"exported config: {target}")
                print(f"generated map: {target.with_name(f'{target.stem}.modbus_map.md')}")
                continue
            elif choice == "7":
                pass
            elif choice == "0":
                return 0
            else:
                print("Unknown command")
                continue

            save_config_document(config_path, payload)
            map_path = write_generated_modbus_map(config_path, payload)
            print(f"saved: {config_path}")
            print(f"generated map: {map_path}")
        except Exception as exc:
            print(f"error: {exc}")


def _prompt_device_selection(payload: dict[str, object], line: int) -> int:
    print()
    print(render_line_devices(payload, line))
    raw_choice = input("Select device number from list: ").strip()
    selected_index = int(raw_choice)
    devices = get_line_devices(payload, line)
    if selected_index < 1 or selected_index > len(devices):
        raise ValueError("device selection is out of range")
    return int(devices[selected_index - 1]["device"])


def _pause_menu() -> None:
    input("Press Enter to continue...")


def _get_line_device_info(
    payload: dict[str, object],
    line: int,
    device_number: int,
) -> dict[str, object]:
    for item in get_line_devices(payload, line):
        if int(item["device"]) == device_number:
            return item
    raise ValueError("device not found")


def _channel_numbers_from_device_info(device_info: dict[str, object]) -> list[int]:
    return sorted(int(row["channel"]) for row in device_info["channel_rows"])


def _format_channel_list(channels: list[int]) -> str:
    return ",".join(f"CH{channel}" for channel in channels)


def _prompt_channel_checklist(current_channels: list[int]) -> list[int] | None:
    selected = set(current_channels)
    while True:
        print()
        print("Channel selection")
        print("-----------------")
        for channel in range(1, 9):
            marker = "x" if channel in selected else " "
            print(f"{channel}. [{marker}] CH{channel}")
        print("s. Save")
        print("q. Cancel")
        choice = input("Toggle channel or select action: ").strip().lower()
        if choice == "s":
            if not selected:
                print("At least one channel must remain enabled.")
                continue
            return sorted(selected)
        if choice == "q":
            return None
        try:
            channel = int(choice)
        except ValueError:
            print("Unknown command")
            continue
        if channel < 1 or channel > 8:
            print("Channel must be in range 1..8")
            continue
        if channel in selected:
            selected.remove(channel)
        else:
            selected.add(channel)


def _run_line_submenu(config_path: str, line: int) -> None:
    while True:
        payload = load_config_document(config_path)
        print()
        print(f"Line {line} submenu")
        print("----------------")
        print(render_line_devices(payload, line))
        print()
        print("1. Show device details")
        print("2. Edit device channels")
        print("3. Remove device")
        print("4. Add TRM138 to this line")
        print("0. Back")
        choice = input("Select action: ").strip()

        try:
            if choice == "1":
                selected_device = _prompt_device_selection(payload, line)
                print()
                print(render_device_details(payload, line=line, device=selected_device))
                _pause_menu()
                continue
            if choice == "2":
                selected_device = _prompt_device_selection(payload, line)
                device_info = _get_line_device_info(payload, line, selected_device)
                current_channels = _channel_numbers_from_device_info(device_info)
                print(f"Current channels: {_format_channel_list(current_channels)}")
                target_channels = _prompt_channel_checklist(current_channels)
                if target_channels is None:
                    print("cancelled")
                    continue
                update_trm138_channels(
                    payload,
                    line=line,
                    device=selected_device,
                    channels=target_channels,
                )
            elif choice == "3":
                selected_device = _prompt_device_selection(payload, line)
                confirm = input(f"Remove device {selected_device} from line{line}? [y/N]: ").strip().lower()
                if confirm != "y":
                    print("cancelled")
                    continue
                remove_trm138_device(
                    payload,
                    line=line,
                    device=selected_device,
                )
            elif choice == "4":
                base_address = int(input("Base OVEN address: ").strip())
                channels = parse_channels(input("Channels [1-8]: ").strip() or "1-8")
                add_trm138_device(
                    payload,
                    line=line,
                    base_address=base_address,
                    channels=channels,
                )
            elif choice == "0":
                return
            else:
                print("Unknown command")
                continue

            save_config_document(config_path, payload)
            map_path = write_generated_modbus_map(config_path, payload)
            print(f"saved: {config_path}")
            print(f"generated map: {map_path}")
        except Exception as exc:
            print(f"error: {exc}")
