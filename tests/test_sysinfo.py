"""Tests for system info collector and renderer."""

from unittest.mock import MagicMock, patch

import pytest

from kraken.sysinfo.collector import SystemStats, collect_stats
from kraken.sysinfo.renderer import render_stats_image, _temp_color


class TestCollectStats:
    @patch("kraken.sysinfo.collector.psutil")
    def test_cpu_temp(self, mock_psutil: MagicMock) -> None:
        mock_entry = MagicMock()
        mock_entry.current = 45.0
        mock_psutil.sensors_temperatures.return_value = {
            "coretemp": [mock_entry],
        }
        mock_psutil.cpu_percent.return_value = 25.0
        stats = collect_stats(include_cpu=True, include_gpu=False)
        assert stats.cpu_temp_c == 45.0
        assert stats.cpu_usage_percent == 25.0
        assert stats.gpu_temp_c is None

    @patch("kraken.sysinfo.collector.psutil")
    def test_no_sensors(self, mock_psutil: MagicMock) -> None:
        mock_psutil.sensors_temperatures.return_value = {}
        mock_psutil.cpu_percent.return_value = 0.0
        stats = collect_stats(include_cpu=True)
        assert stats.cpu_temp_c is None

    def test_disabled(self) -> None:
        stats = collect_stats(include_cpu=False, include_gpu=False)
        assert stats.cpu_temp_c is None
        assert stats.gpu_temp_c is None
        assert stats.cpu_usage_percent is None


class TestTempColor:
    def test_cold(self) -> None:
        r, g, b = _temp_color(20)
        assert b > r  # Should be blue-ish

    def test_hot(self) -> None:
        r, g, b = _temp_color(80)
        assert r == 255
        assert g == 0
        assert b == 0

    def test_warm(self) -> None:
        r, g, b = _temp_color(50)
        assert r > 0


class TestRenderStatsImage:
    def test_renders_image(self) -> None:
        stats = SystemStats(cpu_temp_c=45.0, gpu_temp_c=None, cpu_usage_percent=30.0)
        img = render_stats_image(stats, size=(240, 240))
        assert img.size == (240, 240)
        assert img.mode == "RGB"

    def test_renders_with_gpu(self) -> None:
        stats = SystemStats(cpu_temp_c=50.0, gpu_temp_c=65.0, cpu_usage_percent=50.0)
        img = render_stats_image(stats, size=(240, 240))
        assert img.size == (240, 240)

    def test_renders_no_data(self) -> None:
        stats = SystemStats()
        img = render_stats_image(stats, size=(240, 240))
        assert img.size == (240, 240)

    def test_different_sizes(self) -> None:
        stats = SystemStats(cpu_temp_c=40.0)
        for size in [(240, 240), (640, 640)]:
            img = render_stats_image(stats, size=size)
            assert img.size == size
