"""Chinese desktop front end; conversions run in isolated child processes."""

from __future__ import annotations

import os
from pathlib import Path
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from desktop.core import OPTIONS, build_options, plan_jobs, worker_command


class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CAD → USD · 批量转换工具")
        self.geometry("1180x840")
        self.minsize(1000, 720)
        self.configure(background="#f3f5f8")
        self.events = queue.Queue(maxsize=2000)
        self.cancelled = threading.Event()
        self.process_lock = threading.Lock()
        self.process = None
        self.thread = None
        self.running = False
        self.closing = False
        self.inputs = []
        self.option_vars = {}
        self.edit_widgets = []
        self.output_dir = tk.StringVar()
        self.extension = tk.StringVar(value="usdc")
        self.summary = tk.StringVar(value="添加文件后，选择输出格式和转换参数。")
        self._make_style()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(80, self._poll)

    def _make_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Microsoft YaHei UI", 10))
        style.configure("TFrame", background="#f3f5f8")
        style.configure("TLabel", background="#f3f5f8", foreground="#24334a")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 20, "bold"))
        style.configure("Sub.TLabel", foreground="#637187")
        style.configure("TButton", padding=(12, 7))
        style.configure("Accent.TButton", foreground="white", background="#2667ce")
        style.map("Accent.TButton", background=[("active", "#1854b0")])
        style.configure("Treeview", rowheight=29, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("TLabelframe", background="#f3f5f8")
        style.configure("TLabelframe.Label", background="#f3f5f8", font=("Microsoft YaHei UI", 11, "bold"))

    def _build(self):
        main = ttk.Frame(self, padding=18)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)
        ttk.Label(main, text="CAD → USD", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(main, text="选择多个模型，统一设置参数，按顺序完成转换。", style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 12))
        panes = ttk.Panedwindow(main, orient="horizontal")
        panes.grid(row=2, column=0, sticky="nsew")
        left = ttk.Frame(panes)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=3)
        left.rowconfigure(3, weight=2)
        right = ttk.Labelframe(panes, text="转换参数", padding=10)
        panes.add(left, weight=3)
        panes.add(right, weight=2)
        toolbar = ttk.Frame(left)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for text, command in (("＋ 添加文件", self._add_files), ("移除选中", self._remove_files), ("清空", self._clear_files)):
            button = ttk.Button(toolbar, text=text, command=command)
            button.pack(side="left", padx=(0, 6))
            self.edit_widgets.append(button)
        files_frame = ttk.Frame(left)
        files_frame.grid(row=1, column=0, sticky="nsew")
        self.files = ttk.Treeview(files_frame, columns=("source", "status", "output"), show="headings", selectmode="extended", height=10)
        for column, title, width in (("source", "输入文件", 290), ("status", "状态", 78), ("output", "输出文件", 220)):
            self.files.heading(column, text=title)
            self.files.column(column, width=width, minwidth=60, stretch=column != "status")
        sy = ttk.Scrollbar(files_frame, orient="vertical", command=self.files.yview)
        sx = ttk.Scrollbar(files_frame, orient="horizontal", command=self.files.xview)
        self.files.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.files.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        files_frame.rowconfigure(0, weight=1)
        files_frame.columnconfigure(0, weight=1)
        self.files.tag_configure("success", foreground="#14733b")
        self.files.tag_configure("error", foreground="#b92b31")
        output = ttk.Labelframe(left, text="输出设置", padding=10)
        output.grid(row=2, column=0, sticky="ew", pady=10)
        ttk.Label(output, text="保存目录（留空表示源文件所在目录）").grid(row=0, column=0, columnspan=3, sticky="w")
        entry = ttk.Entry(output, textvariable=self.output_dir)
        entry.grid(row=1, column=0, sticky="ew", pady=7)
        self.edit_widgets.append(entry)
        browse = ttk.Button(output, text="浏览…", command=self._choose_output)
        browse.grid(row=1, column=1, padx=(6, 0))
        self.edit_widgets.append(browse)
        ttk.Button(output, text="打开目录", command=self._open_output).grid(row=1, column=2, padx=(6, 0))
        ttk.Label(output, text="文件格式").grid(row=2, column=0, sticky="w")
        combo = ttk.Combobox(output, textvariable=self.extension, values=("usdc", "usda", "usd", "usdz"), state="readonly", width=12)
        combo.grid(row=2, column=1, columnspan=2, sticky="e")
        self.edit_widgets.append(combo)
        ttk.Label(output, text="重名自动加序号，保留已有文件；大型模型建议使用 USDC。", style="Sub.TLabel", wraplength=560).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        output.columnconfigure(0, weight=1)
        logframe = ttk.Labelframe(left, text="实时日志", padding=6)
        logframe.grid(row=3, column=0, sticky="nsew")
        self.log = tk.Text(logframe, height=8, wrap="word", state="disabled", font=("Consolas", 9), background="#182337", foreground="#e4edf9", relief="flat")
        logscroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=logscroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        logscroll.pack(side="right", fill="y")
        ttk.Label(right, text="勾选即添加参数，取消即移除；未勾选项使用转换器默认值。", wraplength=370, style="Sub.TLabel").pack(anchor="w", pady=(0, 8))
        parameter_frame = ttk.Frame(right)
        parameter_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(parameter_frame, highlightthickness=0, background="#f3f5f8", width=390)
        pscroll = ttk.Scrollbar(parameter_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=pscroll.set)
        pscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        rows = ttk.Frame(canvas)
        rows_id = canvas.create_window((0, 0), window=rows, anchor="nw")
        rows.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(rows_id, width=e.width))
        def wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")
        canvas.bind("<MouseWheel>", wheel)
        rows.bind("<MouseWheel>", wheel)
        for option in OPTIONS:
            flag = option["flag"]
            row = ttk.Frame(rows, padding=(0, 5, 8, 7))
            row.pack(fill="x")
            enabled = tk.BooleanVar(value=flag == "--progress")
            value = tk.StringVar()
            check = ttk.Checkbutton(row, text=option["label"], variable=enabled)
            check.pack(anchor="w")
            self.edit_widgets.append(check)
            control = None
            if option["kind"] != "bool":
                if option["kind"] == "choice":
                    choices = list(map(str, option.get("choices", [])))
                    control = ttk.Combobox(row, textvariable=value, values=choices, state="disabled")
                    if choices:
                        value.set(choices[0])
                else:
                    control = ttk.Entry(row, textvariable=value, state="disabled")
                control.pack(fill="x", padx=(24, 0), pady=(4, 0))
                def update_control(*_, en=enabled, widget=control, kind=option["kind"]):
                    widget.configure(state=("readonly" if kind == "choice" else "normal") if en.get() and not self.running else "disabled")
                enabled.trace_add("write", update_control)
            description = ttk.Label(row, text=f"{flag}\n{option['description']}", style="Sub.TLabel", wraplength=350, justify="left")
            description.pack(anchor="w", padx=(24, 0), pady=(3, 0))
            for widget in (row, check, description, control):
                if widget:
                    widget.bind("<MouseWheel>", wheel)
            self.option_vars[flag] = (enabled, value, control, option["kind"])
            ttk.Separator(rows).pack(fill="x", pady=1)
        bottom = ttk.Frame(main)
        bottom.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self.start = ttk.Button(bottom, text="开始批量转换", style="Accent.TButton", command=self._start)
        self.start.pack(side="right")
        self.stop = ttk.Button(bottom, text="取消转换", command=self._cancel, state="disabled")
        self.stop.pack(side="right", padx=8)
        ttk.Label(bottom, textvariable=self.summary, wraplength=700).pack(side="left")
        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.grid(row=4, column=0, sticky="ew", pady=(8, 0))

    def _add_files(self):
        if self.running:
            return
        selected = filedialog.askopenfilenames(title="选择 CAD / 三维模型（可多选）", filetypes=[("支持的模型", "*.jt *.dgn *.catpart *.catproduct *.cgr *.3dxml *.ifc *.ifczip *.prt *.asm *.par *.pwd *.psm *.xmt *.x_t *.x_b *.xmt_txt *.sldprt *.sldasm *.ipt *.iam *.dwg *.dxf *.rvt *.rfa *.stp *.step *.igs *.iges *.3dm *.stl *.dae *.fbx *.obj *.3ds *.3mf *.gltf *.glb *.sat *.sab"), ("所有文件", "*.*")])
        known = {os.path.normcase(str(Path(p).resolve())) for p in self.inputs}
        for path in selected:
            key = os.path.normcase(str(Path(path).resolve()))
            if key not in known:
                self.inputs.append(path)
                known.add(key)
        self._refresh_files()

    def _refresh_files(self):
        self.files.delete(*self.files.get_children())
        for index, path in enumerate(self.inputs):
            self.files.insert("", "end", iid=str(index), values=(path, "等待", "—"))
        self.summary.set(f"已添加 {len(self.inputs)} 个文件。")

    def _remove_files(self):
        if not self.running:
            selected = set(map(int, self.files.selection()))
            self.inputs = [p for i, p in enumerate(self.inputs) if i not in selected]
            self._refresh_files()

    def _clear_files(self):
        if not self.running:
            self.inputs.clear()
            self._refresh_files()

    def _choose_output(self):
        directory = filedialog.askdirectory(title="选择统一输出目录")
        if directory:
            self.output_dir.set(directory)

    def _open_output(self):
        path = self.output_dir.get().strip()
        if not path and self.inputs:
            path = str(Path(self.inputs[0]).parent)
        if path and Path(path).is_dir():
            try:
                os.startfile(path)
            except OSError as error:
                messagebox.showerror("无法打开目录", str(error))
        else:
            messagebox.showinfo("输出目录", "请先选择存在的输出目录，或添加输入文件。")

    def _set_running(self, running):
        self.running = running
        for widget in self.edit_widgets:
            if isinstance(widget, ttk.Combobox):
                widget.configure(state="disabled" if running else "readonly")
            else:
                widget.configure(state="disabled" if running else "normal")
        for enabled, _, control, kind in self.option_vars.values():
            if control:
                control.configure(state=("readonly" if kind == "choice" else "normal") if enabled.get() and not running else "disabled")
        self.start.configure(state="disabled" if running else "normal")
        self.stop.configure(state="normal" if running else "disabled")

    def _start(self):
        if self.running:
            return
        try:
            if not self.inputs:
                raise ValueError("请至少添加一个输入文件。")
            values = {flag: (True if kind == "bool" else value.get()) for flag, (enabled, value, _, kind) in self.option_vars.items() if enabled.get()}
            for flag, value in values.items():
                if isinstance(value, str) and not value.strip():
                    raise ValueError(f"已启用的参数 {flag} 需要填写值；不需要时请取消勾选。")
            args = build_options(values)
            if self.extension.get() == "usdz" and values.get("--composition-style", "none") != "none":
                raise ValueError("USDZ 需要单体输出：请取消装配组合参数或将其设置为 none。")
            jobs = plan_jobs(list(self.inputs), self.output_dir.get().strip(), self.extension.get())
        except (ValueError, OSError) as error:
            messagebox.showerror("请检查输入和参数", str(error))
            return
        self.cancelled.clear()
        self.progress.configure(maximum=len(jobs), value=0)
        self._set_running(True)
        for i, job in enumerate(jobs):
            self.files.item(str(i), values=(job["input"], "等待", job["output"]), tags=())
        self.summary.set(f"转换中：0 / {len(jobs)}。参数已锁定。")
        self._append_log("\n====== 开始批量转换 ======\n")
        self.thread = threading.Thread(target=self._run_jobs, args=(jobs, args), daemon=True)
        self.thread.start()

    def _run_jobs(self, jobs, args):
        completed = success = failed = 0
        started = set()
        try:
            for index, job in enumerate(jobs):
                if self.cancelled.is_set():
                    break
                started.add(index)
                self.events.put(("status", index, "转换中", ""))
                self.events.put(("log", f"\n[{index + 1}/{len(jobs)}] {job['input']}\n输出：{job['output']}\n"))
                try:
                    output = Path(job["output"])
                    if output.exists():
                        raise FileExistsError("输出文件已被其他程序创建，为保护文件已跳过。")
                    environment = os.environ.copy()
                    environment["PYTHONIOENCODING"] = "utf-8"
                    environment["PYTHONUNBUFFERED"] = "1"
                    with self.process_lock:
                        if self.cancelled.is_set():
                            self.events.put(("status", index, "已取消", "error"))
                            break
                        self.process = subprocess.Popen(worker_command(job["input"], job["output"], args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", env=environment, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                        process = self.process
                    for line in process.stdout:
                        self.events.put(("log", line))
                    process.stdout.close()
                    code = process.wait()
                    if self.cancelled.is_set():
                        self.events.put(("status", index, "已取消", "error"))
                        self.events.put(("log", "当前任务已取消；如存在未完成输出，请勿使用。\n"))
                        break
                    if code == 0 and output.is_file() and output.stat().st_size > 0:
                        success += 1
                        self.events.put(("status", index, "成功", "success"))
                    else:
                        failed += 1
                        self.events.put(("status", index, "失败", "error"))
                        self.events.put(("log", f"转换失败（退出码 {code}）；未完成的输出请勿使用。\n"))
                except Exception as error:
                    failed += 1
                    self.events.put(("status", index, "失败", "error"))
                    self.events.put(("log", f"错误：{error}\n"))
                finally:
                    with self.process_lock:
                        self.process = None
                completed += 1
                self.events.put(("progress", completed, len(jobs)))
        finally:
            if self.cancelled.is_set():
                for index in range(len(jobs)):
                    if index not in started:
                        self.events.put(("status", index, "未执行", ""))
            self.events.put(("finished", success, failed, self.cancelled.is_set()))

    def _cancel(self):
        self.cancelled.set()
        self.stop.configure(state="disabled")
        self.summary.set("正在停止转换，请稍候…")
        with self.process_lock:
            process = self.process
            if process is not None and process.poll() is None:
                try:
                    process.kill()
                except OSError:
                    pass

    def _append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        lines = int(self.log.index("end-1c").split(".")[0])
        if lines > 2500:
            self.log.delete("1.0", f"{lines - 2200}.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll(self):
        for _ in range(300):
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "log":
                self._append_log(event[1])
            elif event[0] == "status":
                _, index, status, tag = event
                values = list(self.files.item(str(index), "values"))
                values[1] = status
                self.files.item(str(index), values=values, tags=(tag,) if tag else ())
                self.files.see(str(index))
            elif event[0] == "progress":
                self.progress.configure(value=event[1])
                self.summary.set(f"转换中：{event[1]} / {event[2]}。")
            elif event[0] == "finished":
                self._set_running(False)
                text = f"{'已取消' if event[3] else '批量转换结束'}：成功 {event[1]}，失败 {event[2]}。"
                self.summary.set(text)
                self._append_log(text + "\n")
        if self.closing and not self.running and (self.thread is None or not self.thread.is_alive()):
            self.destroy()
            return
        self.after(80, self._poll)

    def _close(self):
        if self.running:
            self.closing = True
            self._cancel()
        else:
            self.destroy()


def main():
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
