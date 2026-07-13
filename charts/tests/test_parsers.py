"""Tests para módulos de parsing y formateo de k6-charts."""

import json

from k6_charts.formatters import fmt_ms, fmt_int, fmt_dur, fmt_time_axis
from k6_charts.parsers.discovery import normalize_name, detect_kind, discover
from k6_charts.parsers.summary import parse_summary
from k6_charts.parsers.csv_timeseries import parse_csv
from k6_charts.parsers.infra import parse_infra_csv
from k6_charts.config import Theme, Palette
from k6_charts.colors import error_color, threshold_color


class TestFmtMs:
    def test_none_returns_dash(self):
        assert fmt_ms(None) == "\u2014"

    def test_nan_returns_dash(self):
        assert fmt_ms(float("nan")) == "\u2014"

    def test_inf_returns_dash(self):
        assert fmt_ms(float("inf")) == "\u2014"

    def test_small_value(self):
        assert fmt_ms(42.3) == "42.3 ms"

    def test_medium_value(self):
        assert fmt_ms(150.0) == "150 ms"

    def test_large_value(self):
        assert fmt_ms(1500.0) == "1.50 s"

    def test_exact_100(self):
        assert fmt_ms(100.0) == "100 ms"

    def test_exact_1000(self):
        assert fmt_ms(1000.0) == "1.00 s"


class TestFmtInt:
    def test_none_returns_dash(self):
        assert fmt_int(None) == "\u2014"

    def test_zero(self):
        assert fmt_int(0) == "0"

    def test_large_number(self):
        assert fmt_int(1234567) == "1 234 567"

    def test_rounds_float(self):
        assert fmt_int(42.7) == "43"


class TestFmtDur:
    def test_none_returns_dash(self):
        assert fmt_dur(None) == "\u2014"

    def test_seconds_only(self):
        assert fmt_dur(30000) == "30s"

    def test_minutes_and_seconds(self):
        assert fmt_dur(125000) == "2m 5s"

    def test_exact_minute(self):
        assert fmt_dur(60000) == "1m 0s"


class TestFmtTimeAxis:
    def test_short_span(self):
        assert fmt_time_axis(45.0, 60.0) == "45s"

    def test_long_span(self):
        assert fmt_time_axis(150.0, 200.0) == "2:30"

    def test_zero(self):
        assert fmt_time_axis(0.0, 60.0) == "0s"


class TestNormalizeName:
    def test_load_csv(self):
        assert normalize_name("api.load-raw-metrics.csv") == "api.load"

    def test_stress_json(self):
        assert normalize_name("api.stress.json") == "api.stress"

    def test_prstress_prefix(self):
        assert normalize_name("PRSTRESS-api.json") == "api.stress"

    def test_prload_prefix(self):
        assert normalize_name("PRLOAD-dashboard.json") == "dashboard.load"

    def test_plain_csv(self):
        assert normalize_name("benchmark-raw-metrics.csv") == "benchmark"

    def test_spike_csv(self):
        assert normalize_name("auth.spike-raw-metrics.csv") == "auth.spike"


class TestDetectKind:
    def test_prload(self):
        assert detect_kind("PRLOAD-api.json") == "PRLOAD"

    def test_prstress(self):
        assert detect_kind("PRSTRESS-dashboard.json") == "PRSTRESS"

    def test_no_kind(self):
        assert detect_kind("api.json") is None

    def test_case_insensitive(self):
        assert detect_kind("prload-api.json") == "PRLOAD"


class TestDiscover:
    def test_finds_json_and_csv(self, tmp_path):
        (tmp_path / "api.load-raw-metrics.csv").touch()
        (tmp_path / "api.load.json").write_text("{}")
        ds = discover(str(tmp_path))
        assert len(ds) == 1
        assert "csv" in ds[0]
        assert "summary" in ds[0]

    def test_empty_dir(self, tmp_path):
        ds = discover(str(tmp_path))
        assert ds == []


class TestParseSummary:
    def test_valid_summary(self, tmp_path):
        data = {
            "metrics": {
                "http_reqs": {"values": {"count": 100, "rate": 10.0}},
                "http_req_duration": {"values": {"avg": 50, "med": 45, "p(95)": 120}},
                "http_req_failed": {"values": {"rate": 0.02}},
                "checks": {"values": {"rate": 0.98}},
            },
            "root_group": {"checks": [{"name": "ok", "passes": 98, "fails": 2}]},
            "state": {"testRunDurationMs": 10000},
        }
        path = str(tmp_path / "summary.json")
        with open(path, "w") as f:
            json.dump(data, f)

        result = parse_summary(path)
        assert result is not None
        assert result["reqs"] == 100
        assert result["rps"] == 10.0
        assert result["dur_p95"] == 120
        assert result["err_rate"] == 2.0
        assert result["checks_passes"] == 98
        assert result["checks_fails"] == 2

    def test_none_path(self):
        assert parse_summary(None) is None

    def test_invalid_json(self, tmp_path):
        path = str(tmp_path / "bad.json")
        with open(path, "w") as f:
            f.write("not json")
        assert parse_summary(path) is None


class TestParseCsv:
    def _make_csv(self, tmp_path, name="test.csv"):
        header = "timestamp,metric_name,metric_value,group,extra_tags\n"
        rows = []
        for i in range(100):
            ts = 1000000 + i * 1000
            rows.append(f"{ts},http_req_duration,{50 + i % 10},::default,")
            rows.append(f"{ts},http_reqs,1,::default,")
            rows.append(f"{ts},vus,10,::default,")
        path = str(tmp_path / name)
        with open(path, "w") as f:
            f.write(header + "\n".join(rows) + "\n")
        return path

    def test_parses_valid_csv(self, tmp_path):
        path = self._make_csv(tmp_path)
        result = parse_csv(path)
        assert result is not None
        assert "t" in result
        assert "p95" in result
        assert "med" in result
        assert "rps" in result
        assert "err" in result
        assert "vus" in result
        assert result["span"] > 0

    def test_returns_none_for_empty(self, tmp_path):
        path = str(tmp_path / "empty.csv")
        with open(path, "w") as f:
            f.write("timestamp,metric_name,metric_value\n")
        assert parse_csv(path) is None

    def test_per_action_dur(self, tmp_path):
        header = "timestamp,metric_name,metric_value,group,extra_tags\n"
        rows = []
        for i in range(10):
            ts = 1000000 + i * 1000
            rows.append(
                f"{ts},http_req_duration,{50 + i},::default,entity=accounts&op=read"
            )
        path = str(tmp_path / "action.csv")
        with open(path, "w") as f:
            f.write(header + "\n".join(rows) + "\n")
        result = parse_csv(path)
        assert result is not None
        assert "accounts:read" in result["per_action_dur"]


class TestParseInfraCsv:
    def test_valid_infra(self, tmp_path):
        header = "timestamp,metric,value\n"
        rows = [
            "1000000,cpu_usage,45.2",
            "1001000,cpu_usage,47.8",
            "1002000,memory_usage,62.1",
        ]
        path = str(tmp_path / "infra.csv")
        with open(path, "w") as f:
            f.write(header + "\n".join(rows) + "\n")
        result = parse_infra_csv(path)
        assert result is not None
        assert "cpu_usage" in result
        assert "memory_usage" in result
        assert len(result["cpu_usage"]["t"]) == 2

    def test_none_path(self):
        assert parse_infra_csv(None) is None

    def test_nonexistent_file(self):
        assert parse_infra_csv("/nonexistent/file.csv") is None


class TestTheme:
    def test_default_palette(self):
        theme = Theme()
        assert theme.palette.s1 == "#2a78d6"
        assert theme.palette.good == "#0a8a0a"

    def test_palette_as_dict(self):
        p = Palette()
        d = p.as_dict()
        assert "s1" in d
        assert "crit" in d
        assert len(d) == 15


class TestColors:
    def test_error_color_good(self):
        assert error_color(0.1) == Palette().good

    def test_error_color_warn(self):
        assert error_color(1.0) == Palette().warn

    def test_error_color_crit(self):
        assert error_color(5.0) == Palette().crit

    def test_threshold_color_ok(self):
        assert threshold_color(50, 70) == Palette().good

    def test_threshold_color_crit(self):
        assert threshold_color(80, 70) == Palette().crit
