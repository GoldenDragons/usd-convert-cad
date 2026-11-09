# CAD → USD 批量转换器

## 便携版使用

1. 将 ZIP **完整解压**到有写入权限的本地文件夹。
2. 双击 `CADConverter.exe`，无需 Python、Omniverse Kit 或联网安装。
3. 点击“添加文件”，可以按 Ctrl/Shift 多选，并继续追加文件。
4. 选择输出目录（留空则输出到各源文件目录）、USD 格式。
5. 在右侧启用需要的参数并设置值；每项有中文说明。未启用时使用转换器默认值。
6. 开始转换，查看每个文件状态和下方实时日志。可取消当前批次。

必须复制整个 `CADConverter` 文件夹，包含 `_internal` 和 `runtime`。单独复制 EXE 无法运行。
输出重名时自动添加 `_2`、`_3` 等编号，不覆盖已有文件。
取消或转换失败可能留下不完整输出或关联文件，请根据日志检查。
参数对当前批次全部文件生效；转换期间更改设置不会改变已启动批次。
装配源文件应保留其引用的全部零部件和原有相对路径，不要只复制装配主文件。

## 系统范围

面向 Windows 10/11 x64；32 位 Windows 不支持。并不保证所有 Windows 版本和所有 CAD 格式/版本均可转换。
机器内存、输出空间、源文件完整性和格式限制仍影响转换；不需要 GPU 作为转换前提。
CAD 原始 PBR 材质不保证完整保留；具体限制参见 `LIMITATIONS.md`。
NVIDIA/HOOPS 许可和第三方声明随包保留，参见 `LICENSE.md`、`THIRD_PARTY_NOTICES.md`。

## 源码运行与重建

开发环境：Windows x64、Python 3.12。

```powershell
# 已完成本地部署时，双击 Start-GUI.cmd 即可。
.\.venv\Scripts\python.exe desktop\main.py
# 重建：安装锁定的构建工具，并生成时间戳目录和 ZIP。
.\Build-Portable.cmd
# 回归检查
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

构建使用 PyInstaller 打包图形界面；转换在包内独立 Python 进程中运行，完整保留 NVIDIA wheel 的动态库、USD 插件和相对目录。
无需额外安装任何 UI 库。PyInstaller 只用于构建，不要求目标电脑安装。
