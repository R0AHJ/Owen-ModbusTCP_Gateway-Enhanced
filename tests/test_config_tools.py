import unittest
import tempfile
from pathlib import Path

from owen_gateway.config import load_config
from owen_gateway.config_tools import (
    add_trm138_device,
    export_config_document,
    get_line_devices,
    load_config_document,
    parse_channels,
    remove_line,
    remove_trm138_device,
    render_config_summary,
    render_device_details,
    set_line,
    update_trm138_channels,
    write_generated_modbus_map,
)


class ConfigToolsTests(unittest.TestCase):
    def test_set_line_creates_default_document(self) -> None:
        payload = load_config_document("missing-test-config.json")

        set_line(
            payload,
            line=2,
            port="COM8",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )

        self.assertEqual(payload["modbus"]["port"], 15020)
        self.assertEqual(payload["buses"][0]["name"], "line2")
        self.assertEqual(payload["buses"][0]["modbus_slave_base"], 50)

    def test_add_trm138_device_generates_requested_channels(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )

        result = add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2, 8],
            tag="TRM138 Main",
        )

        self.assertEqual(result["device"], 1)
        points = payload["points"]
        self.assertEqual(len(points), 9)
        self.assertEqual(points[0]["name"], "a96_ch1_read_R16")
        self.assertEqual(points[0]["modbus_address"], 16)
        self.assertEqual(points[1]["modbus_address"], 56)
        self.assertEqual(points[6]["address"], 103)
        self.assertEqual(points[6]["modbus_address"], 30)

    def test_add_trm138_device_uses_next_free_device_number(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2],
            tag="dev96",
        )

        result = add_trm138_device(
            payload,
            line=1,
            base_address=48,
            channels=[1],
            tag="dev48",
        )

        self.assertEqual(result["device"], 2)
        config = load_config_from_payload(payload)
        slave_ids = {point.name: point.modbus_slave_id for point in config.points}
        self.assertEqual(slave_ids["a96_ch1_read_R16"], 96)
        self.assertEqual(slave_ids["a48_ch1_read_R16"], 48)

    def test_add_trm138_device_rejects_address_overlap(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2],
            tag="dev96",
        )

        with self.assertRaisesRegex(ValueError, "address overlap"):
            add_trm138_device(
                payload,
                line=1,
                base_address=97,
                channels=[1],
                tag="overlap",
            )

    def test_parse_channels_supports_ranges_and_lists(self) -> None:
        self.assertEqual(parse_channels("1-3,5,8"), [1, 2, 3, 5, 8])

    def test_render_config_summary_includes_lines_and_devices(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2],
            tag="main trm",
        )

        summary = render_config_summary(payload)

        self.assertIn("Modbus TCP: 0.0.0.0:15020", summary)
        self.assertIn("line1: COM6 9600 8N1", summary)
        self.assertIn("device 1 -> SlaveID 96", summary)
        self.assertIn("base_address=96", summary)
        self.assertIn("channels=CH1,CH2", summary)

    def test_render_device_details_includes_slave_id_and_registers(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2],
            tag="main trm",
        )

        details = render_device_details(payload, line=1, base_address=96)

        self.assertIn("SlaveID: 96", details)
        self.assertIn("| `1` | `96` | `HR16..HR17` | `HR40` | `HR56..HR57` |", details)
        self.assertIn("| `2` | `97` | `HR18..HR19` | `HR41` | `HR58..HR59` |", details)

    def test_get_line_devices_returns_device_inventory(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=2,
            port="COM8",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(payload, line=2, base_address=48, channels=[1], tag="dev48")

        devices = get_line_devices(payload, 2)

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["slave_id"], 48)
        self.assertEqual(devices[0]["base_address"], 48)

    def test_write_generated_modbus_map_creates_markdown_file(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=2,
            port="COM8",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=2,
            base_address=48,
            channels=[1, 2],
            tag="line2 dev",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "owen_config.json"
            map_path = write_generated_modbus_map(config_path, payload)
            content = map_path.read_text(encoding="utf-8")

        self.assertTrue(map_path.name.endswith(".modbus_map.md"))
        self.assertIn("# Generated Modbus Map: owen_config.json", content)
        self.assertIn("Service `SlaveID`: `1`", content)
        self.assertIn("## line2", content)
        self.assertIn("| `1` | `48` | `48` | `CH1,CH2` |", content)
        self.assertIn("| `1` | `48` | `HR16..HR17` | `HR40` | `HR56..HR57` |", content)
        self.assertIn("| `HR48` | LU state mask, bit0..bit7 -> LU1..LU8 |", content)

    def test_export_config_document_writes_json_and_map(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2],
            tag="main trm",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "runtime_config.json"
            export_config_document("source.json", target, payload)
            map_path = target.with_name("runtime_config.modbus_map.md")

            self.assertTrue(target.exists())
            self.assertTrue(map_path.exists())
            self.assertIn('"name": "a96_ch1_read_R16"', target.read_text(encoding="utf-8"))
            self.assertIn("Service `SlaveID`: `1`", map_path.read_text(encoding="utf-8"))

    def test_remove_trm138_device_by_base_address(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(payload, line=1, base_address=96, channels=[1, 2], tag="dev96")
        add_trm138_device(payload, line=1, base_address=48, channels=[1], tag="dev48")

        result = remove_trm138_device(payload, line=1, base_address=96)

        self.assertEqual(result["device"], 1)
        self.assertEqual(result["removed_points"], 6)
        self.assertEqual(len(payload["points"]), 3)
        self.assertEqual(payload["points"][0]["name"], "a48_ch1_read_R16")

    def test_remove_line_deletes_bus_and_points(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        set_line(
            payload,
            line=2,
            port="COM8",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(payload, line=1, base_address=96, channels=[1], tag="dev96")
        add_trm138_device(payload, line=2, base_address=48, channels=[1, 2], tag="dev48")

        result = remove_line(payload, line=2)

        self.assertEqual(result["removed_points"], 6)
        self.assertEqual([bus["name"] for bus in payload["buses"]], ["line1"])
        self.assertEqual(len(payload["points"]), 3)
        self.assertEqual(payload["points"][0]["bus"], "line1")

    def test_update_trm138_channels_keeps_device_and_changes_points(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2, 3, 4, 5, 6, 7, 8],
            tag="dev96",
        )

        result = update_trm138_channels(
            payload,
            line=1,
            base_address=96,
            channels=[1, 2, 3, 4, 5, 6, 8],
        )

        self.assertEqual(result["device"], 1)
        self.assertEqual(result["channels"], "CH1,CH2,CH3,CH4,CH5,CH6,CH8")
        point_names = [point["name"] for point in payload["points"]]
        self.assertNotIn("a96_ch7_read_R28", point_names)
        self.assertIn("a96_ch8_read_R30", point_names)
        config = load_config_from_payload(payload)
        slave_ids = {point.name: point.modbus_slave_id for point in config.points}
        self.assertEqual(slave_ids["a96_ch8_read_R30"], 96)

    def test_summary_keeps_original_base_address_for_sparse_channels(self) -> None:
        payload = load_config_document("missing-test-config.json")
        set_line(
            payload,
            line=1,
            port="COM6",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout_ms=1000,
            poll_interval_ms=1000,
        )
        add_trm138_device(
            payload,
            line=1,
            base_address=96,
            channels=[7],
            tag="dev96",
        )

        summary = render_config_summary(payload)
        details = render_device_details(payload, line=1, base_address=96)

        self.assertIn("base_address=96", summary)
        self.assertIn("channels=CH7", summary)
        self.assertIn("Base address: 96", details)
        self.assertIn("| `7` | `102` | `HR28..HR29` | `HR46` | `HR68..HR69` |", details)

    def test_line_commands_support_legacy_bus1_alias(self) -> None:
        payload = load_config_document("missing-test-config.json")
        payload["buses"] = [
            {
                "name": "bus1",
                "modbus_slave_base": 10,
                "serial": {
                    "port": "/dev/ttyUSB0",
                    "baudrate": 9600,
                    "bytesize": 8,
                    "parity": "N",
                    "stopbits": 1,
                    "timeout_ms": 500,
                    "address_bits": 8,
                },
                "poll_interval_ms": 500,
            }
        ]
        add_trm138_device(payload, line=1, base_address=96, channels=[1], tag="legacy")
        payload["points"][0]["bus"] = "bus1"
        payload["points"][1]["bus"] = "bus1"
        payload["points"][2]["bus"] = "bus1"

        devices = get_line_devices(payload, 1)
        details = render_device_details(payload, line=1, base_address=96)

        self.assertEqual(len(devices), 1)
        self.assertIn("SlaveID: 96", details)


def load_config_from_payload(payload: dict[str, object]):
    import json
    import os

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(payload, handle)
        temp_path = handle.name
    try:
        return load_config(temp_path)
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
