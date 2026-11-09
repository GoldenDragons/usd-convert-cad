from pathlib import Path
import tempfile
import unittest

from desktop.core import build_options, plan_jobs, worker_command


class CoreTests(unittest.TestCase):
    def test_options_preserve_text_as_single_argument(self):
        self.assertEqual(build_options({"--creator": '中文 名称 & "x"', "--convert-metadata": True}),
                         ["--convert-metadata", "--creator", '中文 名称 & "x"'])

    def test_invalid_numeric_values(self):
        for flag, values in {"--physics-accuracy-level": ["nan", "inf", "-1", "1.1"],
                             "--progress-frequency": ["0", "-1", "abc"], "--tess-lod": ["5"]}.items():
            for value in values:
                with self.subTest(flag=flag, value=value), self.assertRaises(ValueError):
                    build_options({flag: value})

    def test_colliding_names_and_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out = root / "out"
            out.mkdir()
            (out / "零件.usdc").write_bytes(b"KEEP")
            sources = []
            for folder in ["first", "second"]:
                d = root / folder
                d.mkdir()
                source = d / "零件.prt"
                source.touch()
                sources.append(str(source))
            jobs = plan_jobs(sources + sources, str(out), "usdc")
            self.assertEqual(len(jobs), 2)
            self.assertEqual([Path(j["output"]).name for j in jobs], ["零件_2.usdc", "零件_3.usdc"])
            self.assertEqual((out / "零件.usdc").read_bytes(), b"KEEP")

    def test_missing_and_unsupported_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                plan_jobs([str(root / "missing.prt")], "", "usdc")
            txt = root / "file.txt"
            txt.touch()
            with self.assertRaises(ValueError):
                plan_jobs([str(txt)], "", "usdc")

    def test_worker_command_does_not_use_shell(self):
        command = worker_command("中文 & a.prt", "a.usdc", ["--creator", "a b"])
        self.assertEqual(command[-6:], ["-i", "中文 & a.prt", "-o", "a.usdc", "--creator", "a b"])


if __name__ == "__main__":
    unittest.main()
