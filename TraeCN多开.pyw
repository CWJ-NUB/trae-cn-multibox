# -*- coding: utf-8 -*-
# CWJ-NUB · https://github.com/CWJ-NUB/trae-cn-multibox
"""Trae CN 多开启动台。双击运行，只用标准库。"""
import base64
import json
import os
import queue
import re
import subprocess
import sys
import threading
import traceback
import webbrowser
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

AUTHOR = "CWJ-NUB"
REPO_URL = "https://github.com/" + AUTHOR + "/trae-cn-multibox"
__author__ = AUTHOR
APP_TITLE = "Trae CN 多账号启动台"
BASE = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
ROOT_DIR = os.path.join(BASE, "TraeCNProfiles")
CONFIG_PATH = os.path.join(ROOT_DIR, "launcher.json")
LOG_PATH = os.path.join(ROOT_DIR, "launcher.log")

BG = "#FAF8F6"
FG = "#2B2622"
ACCENT = "#B26B4F"
GREEN = "#5B7B6C"
MUTED = "#F0EBE7"
GREY = "#8A817A"
WARN_BG = "#FBEEE8"
WARN_FG = "#9A4B32"
FONT = ("Microsoft YaHei", 10)
FONT_BOLD = ("Microsoft YaHei", 10, "bold")
CREATE_NO_WINDOW = 0x08000000

PS_PROCESSES = (
    "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
    "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'Trae' } | "
    "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
)
PS_EXE_PATH = (
    "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
    "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'Trae' } | "
    "Select-Object -First 1 -ExpandProperty ExecutablePath"
)
COMMON_EXE_PATHS = [
    r"%ProgramFiles%\Trae CN\Trae CN.exe",
    r"%LOCALAPPDATA%\Programs\Trae CN\Trae CN.exe",
    r"D:\AppGallery\Trae CN\Trae CN.exe",
    r"D:\Program Files\Trae CN\Trae CN.exe",
    r"C:\Program Files\Trae CN\Trae CN.exe",
    r"E:\Trae CN\Trae CN.exe",
    r"D:\Trae CN\Trae CN.exe",
    r"C:\Trae CN\Trae CN.exe",
]
MAIN_ID = 1
MAIN_DIR_LABEL = "默认目录（桌面图标那个，不加参数）"
DEFAULT_DIR_CANDIDATES = [
    r"%APPDATA%\Trae CN",
    r"%APPDATA%\TRAE CN",
    r"%APPDATA%\Trae",
    r"%APPDATA%\TRAE SOLO CN",
    r"%LOCALAPPDATA%\Programs\Trae CN",
    r"%USERPROFILE%\.trae",
    r"%USERPROFILE%\.trae-cn",
]

HELP_TEXT = """Trae CN 多开 · 使用说明

双击 TraeCN多开.pyw 就能开。Windows 自带 Python 3 就行，tkinter 也是自带的，
不用装东西，不用管理员权限，也不碰你的登录凭据。

上手
  顶部填一次 Trae CN.exe 的路径，点「自动探测」一般能自己找到。
  第 1 行是你原来那个账号，点「启动」跟双击桌面图标一模一样，不用重新登录。
  想加号就点「新建实例」或「批量新建」，选中新行点「启动」，
  在弹出的窗口里登另一个账号。「全部启动」一次全拉起来，已经开着的不重复开。

原来的账号会不会没
  不会。它在 Trae 自己的默认目录里，这工具从来没动过，也不会去动。
  新增的只是 %LOCALAPPDATA%\\TraeCNProfiles\\account-N\\ 这些独立目录。
  主实例的「重置登录」「删除实例」是禁用的，免得手滑把原来的设置、
  插件和工作区搞没了。要给主实例换号，在 Trae 窗口里退出登录就行。

按钮
  新建 / 批量新建   一次加 1 个或 1-30 个位置，目录第一次启动才建
  启动 / 全部启动   主实例 = Trae CN.exe --new-window；隔离实例多一个 --user-data-dir
  停止              按命令行对上 PID 再 taskkill，不会误杀别的实例；停主实例会问一句
  刷新状态          后台查进程和目录大小，界面不卡
  编辑备注          双击表格行也能改，只是给自己看的标签
  打开目录          隔离实例开 account-N，主实例开 Trae 默认目录
  重置登录          目录改名成 .bak-时间戳，不删数据，下次是全新登录态
  删除实例          只从列表移除，目录留着
  扫描已有目录      把之前手工建的 account-N 收进列表，启动时也会自动扫
  桌面快捷方式      在桌面建个入口，不改动本文件

东西放在哪
  %APPDATA%\\Trae CN\\              账号 A 的默认目录，Trae 自己管，本工具不碰
  %LOCALAPPDATA%\\TraeCNProfiles\\
    launcher.json                  实例清单和 exe 路径，纯文本，没有 token
    launcher.log                   出错时的堆栈
    main-cwd\\                      主实例的工作目录
    account-2\\、account-3\\...      各账号自己的登录态
    account-2.bak-...              重置时留下的备份
  配置目录固定，重装或升级这个工具不会丢列表。备份就拷走整个文件夹。

有个坑得记住
  签到按设备算，跟账号无关。TRAE CN 3.4.4 有人真机测过：
  --user-data-dir 能分开登录态，设备号却还是同一个，第二个号当天点签到
  会看到「本设备每日已签到」。用量、模型、请求是按账号独立的，不受影响。
  依据：https://github.com/magpie-community/plugins/issues/436
  所以挂几个号各跑各的任务没问题，指望多开领多份签到积分是白折腾。

状态怎么认
  WMI 查 Trae 进程命令行：隔离实例带 --user-data-dir=<ROOT>\\account-N，
  主实例不带这个参数。Chromium 子进程带 --type=，语言服务进程带 --node-ipc，
  这两种都要排除，不然窗口关了之后残留的进程会让「启动」点了没反应。

出问题了
  双击没反应      看看 .pyw 是不是还关联着 pythonw.exe；或者在这目录按住 Shift
                   右键开 PowerShell 跑 python TraeCN多开.pyw，报错会直接显示
  找不到 exe      点「浏览...」手动选 Trae CN.exe
  状态不对        点「刷新状态」，刚启动的进程要一两秒才登记
  停止没反应      那个窗口不是本工具开的，命令行里没有对应参数，工具管不到
  占用算得慢      几个 GB 的目录遍历会慢，是后台线程，等一下就好
  界面报错        看 %LOCALAPPDATA%\\TraeCNProfiles\\launcher.log

这个工具不做什么
  不读 storage.json，不解密凭据，不改机器码，不写注册表。除了你点「项目仓库」
  时开一下浏览器，其余一律不联网，也不往任何地方发数据。
  登录全走官方客户端自己的界面。账号备注只是文本，不存 token / 密码 / Cookie。
  多账号本身踩服务条款灰线，账号异常自己担着。

  程序、说明、快捷方式创建器都在这一个 .pyw 里。把这一个文件单独拷到
  任何 Windows 机器上都能直接用，README / LICENSE 那些运行时不需要。

  作者 CWJ-NUB
  仓库 https://github.com/CWJ-NUB/trae-cn-multibox
  界面标题右边、这个窗口底下都能点，点一下用系统浏览器打开。
"""


def log(msg):
    try:
        os.makedirs(ROOT_DIR, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def fatal(msg):
    log("FATAL:\n" + msg)
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg[:1600], APP_TITLE + " - 启动失败", 0x10)
    except Exception:
        pass


def powershell_text(command, timeout=12):
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, creationflags=CREATE_NO_WINDOW,
    )
    return (r.stdout or "").strip()


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def detect_exe():
    try:
        out = powershell_text(PS_EXE_PATH, timeout=8)
        candidate = out.splitlines()[0].strip() if out else ""
        if candidate and os.path.isfile(candidate):
            return candidate
    except Exception as e:
        log("detect_exe (process): %r" % e)
    for raw in COMMON_EXE_PATHS:
        path = os.path.expandvars(raw)
        if os.path.isfile(path):
            return path
    return ""


def list_processes():
    out = powershell_text(PS_PROCESSES)
    if not out:
        return []
    starts = [p for p in (out.find("["), out.find("{")) if p >= 0]
    if starts and min(starts) > 0:
        out = out[min(starts):]
    try:
        data = json.loads(out)
    except Exception as e:
        log("list_processes parse: %r | raw=%s" % (e, out[:300]))
        return []
    if isinstance(data, dict):
        data = [data]
    result = []
    for item in data:
        try:
            result.append((int(item["ProcessId"]), item.get("CommandLine") or ""))
        except Exception:
            pass
    return result


def extract_udd(cmdline):
    # 路径带空格时引号写法不统一，三种都得认
    patterns = [
        r'--user-data-dir="([^"]+)"',
        r'"--user-data-dir=([^"]+)"',
        r"--user-data-dir=(\S+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, cmdline, re.I)
        if m:
            return os.path.normcase(os.path.normpath(m.group(1).strip('"')))
    return ""


def is_electron_main(cmdline):
    # 语言服务进程没有 --type=，但有 --node-ipc；认错了关窗后启动会失灵
    low = cmdline.lower()
    return "--type=" not in low and "--node-ipc" not in low


def default_profile_dir():
    for raw in DEFAULT_DIR_CANDIDATES:
        path = os.path.expandvars(raw)
        if os.path.isdir(path):
            return path
    return ""


def main_instance():
    return {
        "id": MAIN_ID,
        "name": "主实例（原账号 A）",
        "account": "",
        "dir": "",
        "main": True,
    }


def pids_for(inst, procs):
    # 主实例只认不带隔离目录的真主进程
    if inst.get("main"):
        root = os.path.normcase(os.path.normpath(ROOT_DIR)) + os.sep
        found = []
        for pid, cmdline in procs:
            if not cmdline.strip() or not is_electron_main(cmdline):
                continue
            udd = extract_udd(cmdline)
            if not udd or not udd.startswith(root):
                found.append(pid)
        return found
    target = os.path.normcase(os.path.normpath(inst["dir"]))
    return [pid for pid, cmdline in procs if extract_udd(cmdline) == target]


def dir_size(path):
    total = 0
    if not os.path.isdir(path):
        return total
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def human(n):
    if n <= 0:
        return "-"
    if n < 1024 ** 2:
        return "%.0f KB" % (n / 1024.0)
    if n < 1024 ** 3:
        return "%.1f MB" % (n / 1024.0 ** 2)
    return "%.2f GB" % (n / 1024.0 ** 3)


def load_config():
    exe, items = "", []
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data.get("instances"), list):
            exe = data.get("exe", "")
            for inst in data["instances"]:
                inst["id"] = int(inst["id"])
                inst.setdefault("name", "账号 %s" % inst["id"])
                inst.setdefault("account", "")
                inst.setdefault("dir", os.path.join(ROOT_DIR, "account-%s" % inst["id"]))
                items.append(inst)
    except FileNotFoundError:
        pass
    except Exception:
        log("load_config:\n" + traceback.format_exc())

    # 主实例固定在第一行，顺手把旧配置里的备注接过来
    main = main_instance()
    for inst in items:
        if inst["id"] == MAIN_ID:
            main["name"] = inst.get("name") or main["name"]
            main["account"] = inst.get("account", "")
            break
    items = [main] + [i for i in items if i["id"] != MAIN_ID]
    items.sort(key=lambda i: (0 if i["id"] == MAIN_ID else 1, i["id"]))
    return {"exe": exe, "instances": items}


def save_config(cfg):
    os.makedirs(ROOT_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1000x670")
        self.root.minsize(900, 560)
        self.root.configure(bg=BG)
        self.q = queue.Queue()
        self.refreshing = False
        self.procs = []
        self.sizes = {}
        self.cfg = load_config()
        self.scan_existing()
        self.exe_var = tk.StringVar(value=self.cfg.get("exe", ""))
        self.exe_var.trace_add("write", lambda *_: self.save_exe())
        if not self.exe_var.get().strip():
            found = detect_exe()
            if found:
                self.exe_var.set(found)
        self.setup_style()
        self.build_ui()
        self.reload_tree()
        self.refresh_async()
        sys.excepthook = self.on_exception
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_style(self):
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure(".", background=BG, foreground=FG, font=FONT)
        st.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF",
                     foreground=FG, rowheight=28, borderwidth=0)
        st.configure("Treeview.Heading", background=MUTED, foreground=FG, font=FONT_BOLD)
        st.configure("TFrame", background=BG)
        st.configure("TLabel", background=BG, foreground=FG)
        st.configure("TButton", background=MUTED, foreground=FG, borderwidth=0,
                     padding=(12, 6))
        st.map("TButton", background=[("active", "#E4DCD5")])
        st.configure("Accent.TButton", background=ACCENT, foreground="#FFFFFF",
                     borderwidth=0, padding=(14, 6), font=FONT_BOLD)
        st.map("Accent.TButton", background=[("active", "#9C5B41")])
        st.configure("TEntry", fieldbackground="#FFFFFF", foreground=FG)

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=16, pady=(14, 6))
        title_row = tk.Frame(header, bg=BG)
        title_row.pack(fill="x")
        tk.Label(title_row, text=APP_TITLE, bg=BG, fg=FG,
                 font=("Microsoft YaHei", 15, "bold")).pack(side="left")
        self.repo_link = tk.Label(title_row, text="by %s · 项目仓库 ↗" % AUTHOR,
                                  bg=BG, fg=ACCENT, cursor="hand2",
                                  font=("Microsoft YaHei", 9, "underline"))
        self.repo_link.pack(side="right")
        self.repo_link.bind("<Button-1>", lambda _e: self.open_repo())
        self.repo_link.bind("<Enter>", lambda _e: self.repo_link.configure(fg="#9C5B41"))
        self.repo_link.bind("<Leave>", lambda _e: self.repo_link.configure(fg=ACCENT))
        tk.Label(header, text="第 1 行是原来的账号，下面都是新加的隔离实例。",
                 bg=BG, fg=GREY, font=FONT).pack(anchor="w", pady=(4, 0))

        warn = tk.Frame(self.root, bg=WARN_BG, padx=12, pady=8)
        warn.pack(fill="x", padx=16, pady=(4, 10))
        tk.Label(warn,
                 text="签到按设备算，一天只有第一个号能领。多开只解决同时在线。",
                 bg=WARN_BG, fg=WARN_FG, font=FONT, wraplength=940,
                 justify="left").pack(anchor="w")
        tk.Label(warn, text="备注只是给自己看的标签，不存任何登录信息。",
                 bg=WARN_BG, fg=GREY, font=FONT).pack(anchor="w", pady=(3, 0))

        pathbar = tk.Frame(self.root, bg=BG)
        pathbar.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(pathbar, text="Trae CN.exe", bg=BG, fg=FG, font=FONT_BOLD).pack(side="left")
        ttk.Entry(pathbar, textvariable=self.exe_var, width=76).pack(side="left", padx=8, fill="x", expand=True)
        ttk.Button(pathbar, text="浏览...", command=self.browse_exe).pack(side="left", padx=(0, 6))
        ttk.Button(pathbar, text="自动探测", command=self.auto_detect).pack(side="left")

        table_frame = tk.Frame(self.root, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=16)
        columns = [
            ("no", "#", 55), ("name", "名称", 140), ("account", "账号备注", 160),
            ("status", "状态", 90), ("size", "占用", 100), ("dir", "配置目录", 330),
        ]
        self.tree = ttk.Treeview(table_frame, columns=[c[0] for c in columns],
                                 show="headings", selectmode="browse")
        for key, label, width in columns:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width,
                             anchor="w" if key in ("name", "account", "dir") else "center")
        self.tree.tag_configure("main", background="#F5EDE7")
        self.tree.tag_configure("running", foreground=GREEN)
        self.tree.tag_configure("stopped", foreground=GREY)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

        row1 = tk.Frame(self.root, bg=BG)
        row1.pack(fill="x", padx=16, pady=(12, 4))
        ttk.Button(row1, text="新建实例", command=self.new_instance).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="批量新建...", command=self.batch_new).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="启动", command=self.start_selected).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="停止", command=self.stop_selected).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="全部启动", style="Accent.TButton",
                   command=self.start_all).pack(side="left")

        row2 = tk.Frame(self.root, bg=BG)
        row2.pack(fill="x", padx=16, pady=(0, 10))
        ttk.Button(row2, text="编辑备注", command=self.edit_selected).pack(side="left", padx=(0, 6))
        ttk.Button(row2, text="打开目录", command=self.open_dir).pack(side="left", padx=(0, 6))
        ttk.Button(row2, text="重置登录", command=self.reset_login).pack(side="left", padx=(0, 6))
        ttk.Button(row2, text="删除实例", command=self.delete_instance).pack(side="left", padx=(0, 6))
        ttk.Button(row2, text="扫描已有目录", command=self.scan_existing_ui).pack(side="left", padx=(0, 6))
        ttk.Button(row2, text="刷新状态", command=self.refresh_async).pack(side="left", padx=(0, 6))
        ttk.Button(row2, text="桌面快捷方式", command=self.make_shortcut).pack(side="left", padx=(0, 6))
        ttk.Button(row2, text="使用说明", command=self.show_help).pack(side="left")

        status = tk.Frame(self.root, bg=MUTED, padx=12, pady=6)
        status.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(status, textvariable=self.status_var, bg=MUTED, fg=FG,
                 font=FONT).pack(side="left")
        tk.Label(status, text="配置：" + CONFIG_PATH, bg=MUTED, fg=GREY,
                 font=FONT).pack(side="right")

    def set_status(self, text):
        self.status_var.set(text)

    def save_exe(self):
        self.cfg["exe"] = self.exe_var.get().strip()
        try:
            save_config(self.cfg)
        except Exception as e:
            log("save_exe: %r" % e)

    def browse_exe(self):
        path = filedialog.askopenfilename(
            title="选择 Trae CN.exe",
            filetypes=[("Trae CN", "Trae CN.exe"), ("可执行文件", "*.exe"), ("全部文件", "*.*")],
        )
        if path:
            self.exe_var.set(os.path.normpath(path))

    def auto_detect(self):
        found = detect_exe()
        if found:
            self.exe_var.set(found)
            messagebox.showinfo(APP_TITLE, "找到了：\n" + found)
        else:
            messagebox.showwarning(
                APP_TITLE,
                "没找到 Trae CN.exe。客户端没开着的话探测不到，点「浏览...」自己选一下。",
            )

    def show_help(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("使用说明")
        dlg.geometry("780x580")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        frame = tk.Frame(dlg, bg=BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(14, 8))
        text = tk.Text(frame, wrap="word", bg="#FFFFFF", fg=FG,
                       font=("Microsoft YaHei", 10), relief="solid", bd=1,
                       padx=14, pady=12, spacing1=2, spacing3=3)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        text.insert("1.0", HELP_TEXT)
        text.configure(state="disabled")
        bar = tk.Frame(dlg, bg=BG)
        bar.pack(fill="x", padx=16, pady=(0, 14))
        ttk.Button(bar, text="打开配置目录", command=self.open_root_dir).pack(side="left")
        ttk.Button(bar, text="%s · 项目仓库 ↗" % AUTHOR,
                   command=self.open_repo).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="关闭", command=dlg.destroy).pack(side="right")
        dlg.bind("<Escape>", lambda _e: dlg.destroy())

    def open_repo(self):
        try:
            webbrowser.open(REPO_URL)
        except Exception as e:
            log("open_repo: %r" % e)
            messagebox.showerror(APP_TITLE, "浏览器没打开：%r\n\n地址：%s" % (e, REPO_URL))

    def open_root_dir(self):
        os.makedirs(ROOT_DIR, exist_ok=True)
        os.startfile(ROOT_DIR)

    def make_shortcut(self):
        script = os.path.abspath(sys.argv[0])
        if not os.path.isfile(script):
            messagebox.showerror(APP_TITLE, "找不到自身文件：\n" + script)
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(desktop):
            onedrive = os.environ.get("OneDrive", "")
            alt = os.path.join(onedrive, "Desktop") if onedrive else ""
            if alt and os.path.isdir(alt):
                desktop = alt
        if not os.path.isdir(desktop):
            messagebox.showerror(APP_TITLE, "没找到桌面目录，快捷方式没建成。\n\n查过：\n"
                                 + os.path.join(os.path.expanduser("~"), "Desktop"))
            return
        lnk = os.path.join(desktop, "Trae CN 多开.lnk")
        pyw = sys.executable
        if not pyw.lower().endswith("pythonw.exe") and os.path.isfile(r"C:\Windows\pyw.exe"):
            pyw = r"C:\Windows\pyw.exe"
        icon = self.exe_var.get().strip().strip('"') or pyw
        script_lines = [
            "$ErrorActionPreference = 'Stop'",
            "$s = New-Object -ComObject WScript.Shell",
            "$c = $s.CreateShortcut(%s)" % ps_quote(lnk),
            "$c.TargetPath = %s" % ps_quote(pyw),
            "$c.Arguments = %s" % ps_quote('"' + script + '"'),
            "$c.WorkingDirectory = %s" % ps_quote(os.path.dirname(script)),
            "$c.IconLocation = %s" % ps_quote(icon),
            "$c.Description = 'Trae CN 多账号启动台'",
            "$c.Save()",
        ]
        encoded = base64.b64encode("\n".join(script_lines).encode("utf-16-le")).decode("ascii")
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=20, creationflags=CREATE_NO_WINDOW,
            )
            if r.returncode != 0:
                raise RuntimeError((r.stderr or r.stdout or "PowerShell 没给出原因").strip())
        except Exception as e:
            detail = "快捷方式没建成：%r\n\n%s" % (e, lnk)
            log("make_shortcut:\n" + traceback.format_exc())
            messagebox.showerror(APP_TITLE, detail)
            return
        messagebox.showinfo(APP_TITLE, "桌面快捷方式已建好：\n" + lnk)

    def reload_tree(self):
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for inst in self.cfg["instances"]:
            is_main = bool(inst.get("main"))
            running = bool(pids_for(inst, self.procs))
            tags = []
            if is_main:
                tags.append("main")
            tags.append("running" if running else "stopped")
            self.tree.insert(
                "", "end", iid=str(inst["id"]),
                values=(inst["id"], inst["name"], inst.get("account", ""),
                        "运行中" if running else "未运行",
                        "-" if is_main else human(self.sizes.get(inst["id"], 0)),
                        MAIN_DIR_LABEL if is_main else inst["dir"]),
                tags=tuple(tags),
            )
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])

    def selected_inst(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "先选中一行。")
            return None
        for inst in self.cfg["instances"]:
            if str(inst["id"]) == sel[0]:
                return inst
        return None

    def scan_existing(self):
        try:
            names = os.listdir(ROOT_DIR)
        except OSError:
            return 0
        used = {i["id"] for i in self.cfg["instances"]}
        added = 0
        for name in names:
            match = re.fullmatch(r"account-(\d+)", name, re.I)
            if not match:
                continue
            number = int(match.group(1))
            path = os.path.join(ROOT_DIR, name)
            if number in used or not os.path.isdir(path):
                continue
            self.cfg["instances"].append({
                "id": number, "name": "账号 %s" % number,
                "account": "", "dir": path,
            })
            used.add(number)
            added += 1
        self.cfg["instances"].sort(key=lambda i: i["id"])
        if added:
            try:
                save_config(self.cfg)
            except Exception as e:
                log("scan_existing save: %r" % e)
        return added

    def scan_existing_ui(self):
        added = self.scan_existing()
        self.reload_tree()
        if added:
            self.set_status("扫到 %s 个新目录。" % added)
        else:
            self.set_status("没扫到新的 account-N 目录。")

    def next_id(self):
        used = {i["id"] for i in self.cfg["instances"]}
        n = 2
        while n in used:
            n += 1
        return n

    def add_instance(self):
        n = self.next_id()
        inst = {
            "id": n,
            "name": "账号 %s" % n,
            "account": "",
            "dir": os.path.join(ROOT_DIR, "account-%s" % n),
        }
        self.cfg["instances"].append(inst)
        return inst

    def new_instance(self):
        self.add_instance()
        save_config(self.cfg)
        self.reload_tree()
        self.set_status("已新建 1 个实例，点「启动」后在新窗口登录账号。")

    def batch_new(self):
        count = simpledialog.askinteger("批量新建", "一次新建几个实例？(1-30)",
                                        parent=self.root, minvalue=1, maxvalue=30)
        if not count:
            return
        for _ in range(count):
            self.add_instance()
        save_config(self.cfg)
        self.reload_tree()
        self.set_status("已新建 %s 个实例。目录会在首次启动时才真正创建。" % count)

    def edit_selected(self):
        inst = self.selected_inst()
        if not inst:
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("编辑实例 #%s" % inst["id"])
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        name_var = tk.StringVar(value=inst["name"])
        acc_var = tk.StringVar(value=inst.get("account", ""))
        tk.Label(dlg, text="名称", bg=BG, fg=FG, font=FONT).grid(
            row=0, column=0, padx=(16, 10), pady=(18, 8), sticky="w")
        tk.Entry(dlg, textvariable=name_var, width=36, font=FONT, bg="#FFFFFF",
                 fg=FG, relief="solid", bd=1).grid(row=0, column=1, padx=(0, 16), pady=(18, 8))
        tk.Label(dlg, text="账号备注", bg=BG, fg=FG, font=FONT).grid(
            row=1, column=0, padx=(16, 10), pady=(0, 8), sticky="w")
        tk.Entry(dlg, textvariable=acc_var, width=36, font=FONT, bg="#FFFFFF",
                 fg=FG, relief="solid", bd=1).grid(row=1, column=1, padx=(0, 16), pady=(0, 8))
        tk.Label(dlg, text="只是给自己看的标签，比如「工作号」「小号 3」。",
                 bg=BG, fg=GREY, font=FONT).grid(row=2, column=0, columnspan=2,
                                                padx=16, pady=(0, 12), sticky="w")

        def save():
            inst["name"] = name_var.get().strip() or ("账号 %s" % inst["id"])
            inst["account"] = acc_var.get().strip()
            save_config(self.cfg)
            self.reload_tree()
            dlg.destroy()

        ttk.Button(dlg, text="保存", style="Accent.TButton", command=save).grid(
            row=3, column=0, padx=(16, 6), pady=(0, 16), sticky="e")
        ttk.Button(dlg, text="取消", command=dlg.destroy).grid(
            row=3, column=1, padx=(0, 16), pady=(0, 16), sticky="w")
        dlg.bind("<Return>", lambda _e: save())
        dlg.wait_window()

    def start_instance(self, inst):
        exe = self.exe_var.get().strip().strip('"')
        if not exe or not os.path.isfile(exe):
            messagebox.showerror(
                APP_TITLE,
                "找不到 Trae CN.exe：%s\n点「自动探测」或「浏览...」填一下。" % (exe or "(空)"),
            )
            return False
        if pids_for(inst, self.procs):
            return None
        try:
            # Crashpad 会往工作目录写 debug.log，让每个实例写进自己的目录
            if inst.get("main"):
                cwd = os.path.join(ROOT_DIR, "main-cwd")
                os.makedirs(cwd, exist_ok=True)
                subprocess.Popen([exe, "--new-window"], cwd=cwd)
            else:
                os.makedirs(inst["dir"], exist_ok=True)
                subprocess.Popen([exe, "--user-data-dir=" + inst["dir"], "--new-window"],
                                 cwd=inst["dir"])
        except Exception as e:
            messagebox.showerror(APP_TITLE, "启动失败：%r" % e)
            log("start_instance:\n" + traceback.format_exc())
            return False
        return True

    def start_selected(self):
        inst = self.selected_inst()
        if not inst:
            return
        result = self.start_instance(inst)
        if result is True:
            if inst.get("main"):
                self.set_status("主实例已启动，不用重新登录。")
            else:
                self.set_status("已启动 #%s，等窗口出来后登录账号。" % inst["id"])
        elif result is None:
            self.set_status("#%s 已经开着了。" % inst["id"])
        self.root.after(1500, self.refresh_async)

    def start_all(self):
        if len(self.cfg["instances"]) <= 1:
            messagebox.showinfo(
                APP_TITLE,
                "现在只有主实例。要加号先点「新建实例」或「批量新建」。",
            )
            return
        started, skipped, failed = 0, 0, 0
        for inst in self.cfg["instances"]:
            r = self.start_instance(inst)
            if r is True:
                started += 1
            elif r is None:
                skipped += 1
            else:
                failed += 1
        self.set_status("全部启动：新开 %s 个，已在运行 %s 个，失败 %s 个。" %
                        (started, skipped, failed))
        self.root.after(1800, self.refresh_async)

    def stop_instance(self, inst, quiet=False):
        if inst.get("main") and not quiet:
            if not messagebox.askyesno(
                APP_TITLE,
                "关掉主实例？\n\n平时用桌面图标开的 Trae 窗口也会一起关掉，"
                "下面那些隔离实例不受影响。",
            ):
                return False
        pids = pids_for(inst, self.procs)
        if not pids:
            if not quiet:
                messagebox.showinfo(APP_TITLE, "#%s 没在运行。" % inst["id"])
            return False
        for pid in pids:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
        if not quiet:
            messagebox.showinfo(APP_TITLE, "已停止 #%s（%s 个进程）。" % (inst["id"], len(pids)))
        return True

    def stop_selected(self):
        inst = self.selected_inst()
        if not inst:
            return
        self.stop_instance(inst)
        self.root.after(800, self.refresh_async)

    def open_dir(self):
        inst = self.selected_inst()
        if not inst:
            return
        if inst.get("main"):
            path = default_profile_dir()
            if not path:
                messagebox.showinfo(
                    APP_TITLE,
                    "没找到默认配置目录，常见的几个位置都试过了：\n"
                    + "\n".join(os.path.expandvars(p) for p in DEFAULT_DIR_CANDIDATES)
                    + "\n\n不影响使用，登录态一直由 Trae 自己管。",
                )
                return
            os.startfile(path)
            return
        if not os.path.isdir(inst["dir"]):
            os.makedirs(inst["dir"], exist_ok=True)
        os.startfile(inst["dir"])

    def reset_login(self):
        inst = self.selected_inst()
        if not inst:
            return
        if inst.get("main"):
            messagebox.showinfo(
                APP_TITLE,
                "主实例不能重置。\n\n那个目录里还有你原来的设置、插件和工作区，"
                "不想动它。要换号在 Trae 窗口里退出登录就行。",
            )
            return
        if not messagebox.askyesno(
            APP_TITLE,
            "重置「%s」？\n\n目录会改名成备份，不会删：\n%s\n\n下次启动要重新登录。"
            % (inst["name"], inst["dir"]),
        ):
            return
        self.stop_instance(inst, quiet=True)
        if not os.path.isdir(inst["dir"]):
            messagebox.showinfo(APP_TITLE, "这个实例还没有配置目录，本来就是干净的。")
            return
        backup = inst["dir"] + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        n = 1
        while os.path.exists(backup):
            backup = inst["dir"] + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-%s" % n
            n += 1
        try:
            os.rename(inst["dir"], backup)
        except Exception as e:
            messagebox.showerror(APP_TITLE, "改名失败：%r\n\n原目录没动。" % e)
            return
        messagebox.showinfo(APP_TITLE, "已重置。旧数据备份在：\n" + backup)
        self.refresh_async()

    def delete_instance(self):
        inst = self.selected_inst()
        if not inst:
            return
        if inst.get("main"):
            messagebox.showinfo(
                APP_TITLE,
                "主实例是固定第一行，删不掉。\n\n它只是个一键打开原账号的入口。",
            )
            return
        if not messagebox.askyesno(
            APP_TITLE,
            "把「%s」从列表移除？\n\n目录会留着，不删数据：\n%s" % (inst["name"], inst["dir"]),
        ):
            return
        self.cfg["instances"] = [i for i in self.cfg["instances"] if i["id"] != inst["id"]]
        save_config(self.cfg)
        self.reload_tree()
        self.set_status("已移除 #%s，目录保留。" % inst["id"])

    def refresh_async(self):
        if self.refreshing:
            return
        self.refreshing = True
        self.set_status("正在查进程和目录占用...")

        def worker():
            try:
                procs = list_processes()
                snapshot = list(self.cfg["instances"])
                sizes = {inst["id"]: dir_size(inst["dir"])
                         for inst in snapshot if not inst.get("main")}
                self.q.put(("ok", procs, sizes, ""))
            except Exception:
                self.q.put(("err", [], {}, traceback.format_exc()))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, self.poll_queue)

    def poll_queue(self):
        try:
            kind, procs, sizes, err = self.q.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll_queue)
            return
        self.refreshing = False
        if kind == "err":
            log("refresh:\n" + err)
            self.set_status("刷新失败，看日志 " + LOG_PATH)
            return
        self.procs = procs
        self.sizes = sizes
        self.reload_tree()
        running = sum(1 for inst in self.cfg["instances"] if pids_for(inst, self.procs))
        extra = len(self.cfg["instances"]) - 1
        self.set_status("%s 个隔离实例，%s 个在运行（%s）" %
                        (extra, running, datetime.now().strftime("%H:%M:%S")))

    def on_exception(self, exc_type, exc_value, exc_tb):
        log("unhandled:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        try:
            messagebox.showerror(APP_TITLE, "出错了：%s\n\n日志在 %s" % (exc_value, LOG_PATH))
        except Exception:
            pass

    def on_close(self):
        try:
            save_config(self.cfg)
        except Exception as e:
            log("on_close: %r" % e)
        self.root.destroy()


def main():
    os.makedirs(ROOT_DIR, exist_ok=True)
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        fatal(traceback.format_exc())
