"""Validated conversion options and collision-safe batch planning (no UI imports)."""
from pathlib import Path
import math
import sys


def option(flag, label, description, kind="bool", choices=None):
    return dict(flag=flag, label=label, description=description, kind=kind, choices=choices)


OPTIONS = [
    option("--tess-lod", "曲面细节等级", "0–4，越高通常越精细，耗时和文件体积也可能增加。留空使用转换器默认值。", "choice", ["0", "1", "2", "3", "4"]),
    option("--accurate-tessellation", "精确三角化", "启用更精确的曲面三角化。"),
    option("--fast-surface-curvatures", "快速曲率计算", "关闭精确曲面曲率计算。"),
    option("--convert-curves", "转换曲线和线框", "将支持的二维模型空间线条、三维曲线转换为 USD BasisCurves。"),
    option("--convert-metadata", "保留 CAD 元数据", "将源文件元数据写入 USD 自定义属性。"),
    option("--up-axis", "向上轴", "file=源文件方向；y=Y 轴向上；z=Z 轴向上。", "choice", ["file", "y", "z"]),
    option("--instancing-style", "重复零件实例方式", "none=无实例；reference=引用；instanceable-reference=可实例化引用。", "choice", ["none", "reference", "instanceable-reference"]),
    option("--composition-style", "装配文件组织", "none=单体；reference=外部引用；payload=载荷。USDZ 只能使用 none。", "choice", ["none", "reference", "payload"]),
    option("--filter-style", "隐藏元素处理", "none=不过滤；omit=省略；hide=保留但隐藏；deactivate=停用。需读取隐藏元素时同时启用下项。", "choice", ["none", "omit", "hide", "deactivate"]),
    option("--load-hidden", "读取隐藏元素", "读取 CAD 内被隐藏的零件，再按隐藏元素处理规则输出。"),
    option("--material-type", "材质类型", "none=无材质；preview-surface=通用；preview-surface-omnipbr=OmniPBR；preview-surface-materialx=MaterialX。USDZ 会将 OmniPBR 切换为通用材质。", "choice", ["none", "preview-surface", "preview-surface-omnipbr", "preview-surface-materialx"]),
    option("--no-materials", "不输出材质", "只转换几何等数据，优先于材质类型选项。"),
    option("--no-normals", "不输出法线", "不写入顶点/面法线；查看器可能需要重新计算。"),
    option("--no-dedup", "关闭去重", "不合并重复网格和材质，可能增大输出文件。"),
    option("--global-xforms", "使用全局变换", "输出全局变换，而不是父子层级的局部变换。"),
    option("--read-constraints", "导出固定装配约束", "支持部分 CATIA、NX、SolidWorks 固定约束；并非所有装配约束。不会自动创建刚体和碰撞。"),
    option("--convert-physics-data", "输出物理属性", "读取并输出受支持的 CAD 物理属性。"),
    option("--physics-accuracy-level", "物理属性精度", "0–1 之间的数值，用于物理属性计算。", "float"),
    option("--physics-use-geometry-on-ribrep", "RiBRep 使用几何计算", "计算 RiBRep 物理属性时使用几何而不是拓扑。"),
    option("--revit-lod", "Revit 细节等级", "仅 Revit：0=文件默认；1=粗；2=中；3=精细。", "choice", ["0", "1", "2", "3"]),
    option("--view-layer-name", "视图层或简化表示名称", "按 CAD 中的准确名称选择视图层或简化表示。", "text"),
    option("--creator", "创建者元数据", "写入输出 USD 层的创建者字段。", "text"),
    option("--progress", "输出转换进度", "在日志中显示转换器报告的进度。"),
    option("--progress-frequency", "进度报告频率", "大于 0 的数值，单位 Hz；配合输出转换进度使用。", "float"),
]

SUPPORTED = frozenset(".jt .dgn .catpart .catproduct .cgr .3dxml .ifc .ifczip .prt .asm .xmt .x_t .x_b .xmt_txt .sldprt .sldasm .stl .ipt .iam .dwg .dxf .rvt .rfa .par .pwd .psm .stp .step .igs .iges .3dm .dae .fbx .obj .3ds .3mf .gltf .glb .sat .sab".split())


def build_options(values):
    unknown = set(values) - {o["flag"] for o in OPTIONS}
    if unknown:
        raise ValueError("不支持的参数：" + ", ".join(sorted(unknown)))
    args = []
    for o in OPTIONS:
        value = values.get(o["flag"])
        if o["kind"] == "bool":
            if value:
                args.append(o["flag"])
            continue
        if value is None or str(value).strip() == "":
            continue
        value = str(value).strip()
        if o["kind"] == "choice" and value not in o["choices"]:
            raise ValueError(o["label"] + "：请选择列表中的值")
        if o["kind"] in ("int", "float"):
            try:
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError()
                if o["flag"] == "--physics-accuracy-level" and not 0 <= number <= 1:
                    raise ValueError()
                if o["flag"] == "--progress-frequency" and number <= 0:
                    raise ValueError()
            except ValueError:
                raise ValueError(o["label"] + "：数值不在有效范围内") from None
        args.extend([o["flag"], value])
    return args


def plan_jobs(inputs, output_dir, extension):
    extension = extension.lower().lstrip(".")
    if extension not in {"usd", "usda", "usdc", "usdz"}:
        raise ValueError("不支持的输出格式")
    jobs, seen, reserved = [], set(), set()
    for item in inputs:
        source = Path(item).resolve()
        key = str(source).casefold()
        if key in seen:
            continue
        if not source.is_file():
            raise ValueError("输入文件不存在：" + str(source))
        if source.suffix.lower() not in SUPPORTED:
            raise ValueError("不支持的输入格式：" + source.suffix)
        seen.add(key)
        directory = Path(output_dir).resolve() if output_dir.strip() else source.parent
        if directory.exists() and not directory.is_dir():
            raise ValueError("输出位置不是文件夹：" + str(directory))
        dest = directory / (source.stem + "." + extension)
        suffix = 2
        while dest.exists() or str(dest).casefold() in reserved:
            dest = directory / f"{source.stem}_{suffix}.{extension}"
            suffix += 1
        reserved.add(str(dest).casefold())
        jobs.append(dict(input=str(source), output=str(dest)))
    return jobs


def worker_command(input, output, args):
    if getattr(sys, "frozen", False):
        interpreter = Path(sys.executable).parent / "runtime" / "python.exe"
    else:
        interpreter = Path(sys.executable)
    return [str(interpreter), "-u", "-m", "usd_convert_cad", "-i", input, "-o", output, *args]
