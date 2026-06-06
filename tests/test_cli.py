"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from kraken.cli.app import cli
from kraken.core.models import DeviceInfo, SensorData


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCLIVersion:
    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "kraken" in result.output
        assert "0.1.0" in result.output


class TestStatusCommand:
    @patch("kraken.cli.commands.status.find_kraken_hwmon")
    @patch("kraken.cli.commands.status.read_sensors")
    def test_status_text(self, mock_read: MagicMock, mock_find: MagicMock,
                         runner: CliRunner, tmp_path: Path) -> None:
        mock_find.return_value = tmp_path
        mock_read.return_value = SensorData(
            liquid_temp_c=29.2, pump_rpm=2703, fan_rpm=1050, timestamp=0.0
        )
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "29.2" in result.output
        assert "2703" in result.output
        assert "1050" in result.output

    @patch("kraken.cli.commands.status.find_kraken_hwmon")
    @patch("kraken.cli.commands.status.read_sensors")
    def test_status_json(self, mock_read: MagicMock, mock_find: MagicMock,
                         runner: CliRunner, tmp_path: Path) -> None:
        mock_find.return_value = tmp_path
        mock_read.return_value = SensorData(
            liquid_temp_c=30.0, pump_rpm=2500, fan_rpm=1000, timestamp=0.0
        )
        result = runner.invoke(cli, ["status", "--json"])
        assert result.exit_code == 0
        assert '"liquid_temp_c": 30.0' in result.output
        assert '"pump_rpm": 2500' in result.output


class TestLCDCommands:
    @patch("kraken.cli.commands.lcd._get_device")
    @patch("kraken.cli.commands.lcd.lcd_ops")
    def test_lcd_static(self, mock_ops: MagicMock, mock_get: MagicMock,
                        runner: CliRunner, tmp_path: Path) -> None:
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG" + b"\x00" * 100)
        mock_get.return_value = MagicMock()

        result = runner.invoke(cli, ["lcd", "static", str(img)])
        assert result.exit_code == 0
        assert "Uploaded" in result.output

    @patch("kraken.cli.commands.lcd._get_device")
    @patch("kraken.cli.commands.lcd.lcd_ops")
    def test_lcd_brightness(self, mock_ops: MagicMock, mock_get: MagicMock,
                            runner: CliRunner) -> None:
        mock_get.return_value = MagicMock()
        result = runner.invoke(cli, ["lcd", "brightness", "75"])
        assert result.exit_code == 0
        assert "75" in result.output

    @patch("kraken.cli.commands.lcd._get_device")
    @patch("kraken.cli.commands.lcd.lcd_ops")
    def test_lcd_orientation(self, mock_ops: MagicMock, mock_get: MagicMock,
                             runner: CliRunner) -> None:
        mock_get.return_value = MagicMock()
        result = runner.invoke(cli, ["lcd", "orientation", "90"])
        assert result.exit_code == 0
        assert "90" in result.output

    @patch("kraken.cli.commands.lcd._get_device")
    @patch("kraken.cli.commands.lcd.lcd_ops")
    def test_lcd_liquid(self, mock_ops: MagicMock, mock_get: MagicMock,
                        runner: CliRunner) -> None:
        mock_get.return_value = MagicMock()
        result = runner.invoke(cli, ["lcd", "liquid"])
        assert result.exit_code == 0
        assert "liquid" in result.output.lower()

    @patch("kraken.cli.commands.lcd._get_device")
    @patch("kraken.cli.commands.lcd.gif_player")
    def test_lcd_gif_with_loops(self, mock_gif: MagicMock, mock_get: MagicMock,
                                 runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "a.gif"
        f.write_bytes(b"GIF89a" + b"\x00" * 100)
        mock_get.return_value = MagicMock()

        result = runner.invoke(cli, ["lcd", "gif", str(f), "--loops", "3"])
        assert result.exit_code == 0
        assert mock_gif.play_animated_gif.called
        kwargs = mock_gif.play_animated_gif.call_args.kwargs
        assert kwargs.get("loops") == 3
        assert "3 loop" in result.output

    @patch("kraken.cli.commands.lcd._get_device")
    @patch("kraken.cli.commands.lcd.gif_player")
    def test_lcd_gif_default_infinite(self, mock_gif: MagicMock, mock_get: MagicMock,
                                       runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "a.gif"
        f.write_bytes(b"GIF89a" + b"\x00" * 100)
        mock_get.return_value = MagicMock()

        result = runner.invoke(cli, ["lcd", "gif", str(f)])
        assert result.exit_code == 0
        kwargs = mock_gif.play_animated_gif.call_args.kwargs
        assert kwargs.get("loops") == 0
        assert "Ctrl+C" in result.output

    @patch("kraken.cli.commands.lcd._get_device")
    @patch("kraken.cli.commands.lcd.gif_player")
    def test_lcd_gif_keyboard_interrupt(self, mock_gif: MagicMock, mock_get: MagicMock,
                                          runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "a.gif"
        f.write_bytes(b"GIF89a" + b"\x00" * 100)
        dev = MagicMock()
        mock_get.return_value = dev
        mock_gif.play_animated_gif.side_effect = KeyboardInterrupt()

        result = runner.invoke(cli, ["lcd", "gif", str(f)])
        assert result.exit_code == 0
        assert "Stopped" in result.output
        dev.disconnect.assert_called_once()


class TestCarouselCommands:
    def test_carousel_list_empty(self, runner: CliRunner, tmp_path: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_path):
            with patch("kraken.cli.commands.carousel.load_config") as mock_load:
                from kraken.core.models import AppConfig
                mock_load.return_value = AppConfig()
                result = runner.invoke(cli, ["carousel", "list"])
                assert result.exit_code == 0
                assert "empty" in result.output.lower()

    def test_carousel_status(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.carousel.load_config") as mock_load:
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["carousel", "status"])
            assert result.exit_code == 0
            assert "Enabled" in result.output

    def test_carousel_add(self, runner: CliRunner, tmp_path: Path) -> None:
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG" + b"\x00" * 100)

        with patch("kraken.cli.commands.carousel.load_config") as mock_load, \
             patch("kraken.cli.commands.carousel.save_config") as mock_save:
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["carousel", "add", str(img), "--seconds", "5"])
            assert result.exit_code == 0
            assert "Added" in result.output
            mock_save.assert_called_once()

    def test_carousel_add_sysinfo(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.carousel.load_config") as mock_load, \
             patch("kraken.cli.commands.carousel.save_config"):
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["carousel", "add", "--sysinfo", "-s", "15"])
            assert result.exit_code == 0
            assert "sysinfo" in result.output.lower()

    def test_carousel_add_liquid(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.carousel.load_config") as mock_load, \
             patch("kraken.cli.commands.carousel.save_config"):
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["carousel", "add", "--liquid"])
            assert result.exit_code == 0
            assert "liquid" in result.output.lower()

    def test_carousel_add_no_args_fails(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.carousel.load_config") as mock_load:
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["carousel", "add"])
            assert result.exit_code != 0

    def test_carousel_clear(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.carousel.load_config") as mock_load, \
             patch("kraken.cli.commands.carousel.save_config"):
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["carousel", "clear"])
            assert result.exit_code == 0
            assert "cleared" in result.output.lower()


class TestConfigCommands:
    def test_config_show(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.config_cmd.load_config") as mock_load:
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["config", "show"])
            assert result.exit_code == 0
            assert "brightness" in result.output

    def test_config_path(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["config", "path"])
        assert result.exit_code == 0
        assert "config.toml" in result.output


class TestSysInfoCommands:
    def test_sysinfo_config_show(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.sysinfo.load_config") as mock_load:
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["sysinfo", "config"])
            assert result.exit_code == 0
            assert "CPU temp" in result.output

    def test_sysinfo_config_modify(self, runner: CliRunner) -> None:
        with patch("kraken.cli.commands.sysinfo.load_config") as mock_load, \
             patch("kraken.cli.commands.sysinfo.save_config"):
            from kraken.core.models import AppConfig
            mock_load.return_value = AppConfig()
            result = runner.invoke(cli, ["sysinfo", "config", "--gpu", "--refresh", "3"])
            assert result.exit_code == 0
            assert "updated" in result.output.lower()
