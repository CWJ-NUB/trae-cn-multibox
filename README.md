# Trae CN 多开启动台

> **一个 `.pyw` 文件，Windows 双击即用。** 借助官方客户端自带的 `--user-data-dir` 参数隔离登录态，在同一台机器上同时登录多个 Trae CN 账号，并在一个界面里统一启动、停止和管理。

*A single-file Windows GUI launcher for running multiple TRAE CN instances with separate accounts. No installer, no dependencies, no credential handling.*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-0078D6) ![Dependencies](https://img.shields.io/badge/Dependencies-0-brightgreen) ![License](https://img.shields.io/badge/License-MIT-orange)

---

## 它解决什么问题

TRAE CN 官方客户端默认只允许一个登录态。要在同一台机器上**同时**挂多个账号，最干净的做法不是装第三方切号工具，而是让每个实例拥有独立的用户数据目录 —— 这正是 Electron / VS Code 系客户端原生支持的启动参数。

本项目把这个参数包装成一个可视化启动台：

- 原来的账号一个都不动，照常用桌面图标打开；
- 新增的每个账号分配独立的 `account-N` 目录，各自登录、各自保留设置与插件；
- 在一个列表里查看运行状态、启动 / 全部启动 / 停止、打备注、查占用、重置登录。

**核心卖点是「零侵入」**：不读 `storage.json`、不解密凭据、不改机器码、不写注册表、不复制安装目录、不启动后台服务。启动的就是官方 `Trae CN.exe` 本身，登录也完全走官方登录界面。

---

## 快速开始

**环境要求**：Windows 10/11 + Python 3（系统自带 `tkinter` 即可）。不需要 pip install，不需要管理员权限，不需要打包成 exe。

1. 下载 [`TraeCN多开.pyw`](TraeCN多开.pyw)。
2. 双击它。Windows 会把 `.pyw` 关联到 `pythonw.exe`，直接出图形界面，没有黑色控制台窗口。
3. 顶部填一次 `Trae CN.exe` 的路径（点「自动探测」通常就能找到）。
4. 列表第 1 行「主实例」= 你原来那个账号，点「启动」等价于双击桌面图标；点「新建实例」或「批量新建」加账号，再点「启动」，在弹出的窗口里登录另一个账号。

> 双击没反应？在该目录按住 Shift 右键打开 PowerShell，执行 `python TraeCN多开.pyw`，报错会直接显示并写入 `launcher.log`。

界面里有个「桌面快捷方式」按钮，点一下在桌面建入口，以后连文件夹都不用进。「使用说明」按钮里内置了完整文档，不用回来翻 README。

---

## 功能

| 功能 | 说明 |
| --- | --- |
| 主实例固定第 1 行 | 原账号不会被工具改写，启动命令就是 `Trae CN.exe --new-window`，不带任何隔离参数 |
| 批量新建 1–30 个 | 编号自动排 `account-2`、`account-3`…；目录**首次启动才创建**，不会一上来占几十 GB |
| 全部启动 / 单独启动 | 已运行的不重复启动；每个实例独立工作目录，避免 Crashpad 日志堆在启动器旁边 |
| 停止 | 按命令行里的 `--user-data-dir` 精确匹配 PID 再 `taskkill /T /F`，不会误杀其他实例 |
| 状态与占用 | 后台线程查 WMI 进程 + 统计目录大小，界面不卡；运行中墨绿、未运行灰色 |
| 账号备注 | 双击行编辑，纯文本标签，方便记住哪个窗口登的是哪个号 |
| 重置登录 | 把目录改名成 `.bak-时间戳` 备份，不删数据、可回滚 |
| 扫描已有目录 | 自动收拢之前手工建的 `account-N`，不重复建号 |
| 自动探测 exe | 优先从运行中的 Trae 进程读路径，再回退到常见安装位置 |

进程识别做了两层过滤：Chromium 子进程带 `--type=`，VS Code 语言服务进程带 `--node-ipc`，两者都会被排除。否则窗口关掉后残留的辅助进程会让「启动」变成空操作。

---

## 原理

```
桌面图标 / 主实例          Trae CN.exe --new-window
                            └─ 默认目录 %APPDATA%\Trae CN  →  账号 A

启动台第 2 行              Trae CN.exe --user-data-dir=<ROOT>\account-2 --new-window
                            └─ 独立目录                       →  账号 B

启动台第 3 行              Trae CN.exe --user-data-dir=<ROOT>\account-3 --new-window
                            └─ 独立目录                       →  账号 C
```

`ROOT` = `%LOCALAPPDATA%\TraeCNProfiles`。每个目录保存自己的登录态、设置、扩展和缓存，互不覆盖。配置和实例清单存在同目录的 `launcher.json`（只有文本标签和 exe 路径，**没有任何 token**）。

不需要复制整个安装目录 —— 社区流传的「把 Trae 复制成 Trae-2」做法是多余的，同一个 exe 加参数即可。

---

## ⚠️ 必须先看：设备号不会跟着分开

这是本项目唯一绕不开的硬限制，**别拿它去刷签到**。

2026-10-29 有人在 **Windows 11 + TRAE CN 3.4.4（融合版）** 上做了完整真机验证，结论记录在 [magpie-community/plugins#436](https://github.com/magpie-community/plugins/issues/436)：

| 验证项 | 结果 |
| --- | --- |
| `--user-data-dir=<新目录>` 是否生效 | ✅ 生效，生成独立 `storage.json`，UID 不同 |
| 默认目录的账号 A 是否被覆盖 | ❌ 没变，文件哈希与修改时间一致 |
| **设备号是否随目录分开** | ❌ **相同**，还是同一个 16 位设备号 |
| 第二账号在客户端手动签到 | ❌ 提示「本设备每日已签到」 |

维护者定论：**签到按设备算**，同一台机器当天只有第一个账号能领；**用量、模型、请求按账号独立，不受影响**。该 issue 已关闭。

> ✅ 适合：挂多个账号分别跑任务、各用各的额度。
> ❌ 不适合：靠多开领多份每日签到积分。

官方社区 [topic/9364](https://forum.trae.cn/t/topic/9364) 在 2026-04-15 回复过「暂不支持修改配置目录」，但参数确实被客户端接受。两件事不冲突：参数能用 ≠ 所有状态都跟着走，设备号就是反例。

以上是第三方实测，不是官方承诺。客户端版本更新后行为可能变化，用之前建议自己验证一次。

---

## 数据与安全边界

| 项目 | 位置 / 说明 |
| --- | --- |
| 账号 A 的登录态 | `%APPDATA%\Trae CN`，**Trae 自己管理，本工具从不读写、改名或删除** |
| 隔离实例 | `%LOCALAPPDATA%\TraeCNProfiles\account-N\` |
| 实例清单 | `%LOCALAPPDATA%\TraeCNProfiles\launcher.json`，纯文本标签 + exe 路径 |
| 异常日志 | `%LOCALAPPDATA%\TraeCNProfiles\launcher.log` |

工具**只读**两样东西：进程命令行、目录大小。不碰 `storage.json`、不解密 auth blob、不改机器码、不写注册表、不联网、不采集任何数据。账号备注只是给你自己看的文本，不存密码 / Cookie / Token。

每个实例的数据目录可能长到 **3–8 GB**（含模型缓存），开多个之前先看磁盘。融合版客户端更新频繁，升级后独立目录偶尔需要重建。

---

## 常见问题

**原来的账号会丢吗？**
不会。主实例走 Trae 的默认目录，工具只新增 `account-N` 目录。主实例的「重置登录」「删除实例」被禁用，避免误伤原有设置、插件和工作区。想给主实例换号，请在 Trae 窗口里自己退出登录。

**和「一键切号」工具有什么区别？**
切号工具是「关进程 → 覆写登录态 → 重启」，同一时刻只有一个账号在线，而且会动凭据文件。本项目是多个窗口同时在线，且完全不碰凭据。

**为什么用 `.pyw` 不用 `.cmd` / exe？**
`.pyw` 双击由 `pythonw.exe` 运行，中文路径走 Windows 宽字符，不经过 cmd 代码页，不会乱码；没有黑框；零第三方依赖；源码可直接审阅，不用信任来路不明的二进制。

**状态显示不准 / 停止没反应？**
点「刷新状态」，刚启动的进程要一两秒才登记。「停止」依赖命令行里的 `--user-data-dir`，如果你是自己手工开的普通 Trae 窗口，工具管不到它。

**想彻底隔离扩展和缓存？**
本项目只做 `--user-data-dir` 隔离。更彻底的 `APPDATA` / `USERPROFILE` 环境变量级重定向需要第三方方案，代价是每个实例多占几 GB，且通常要碰凭据。

---

## 免责声明

- 本项目是**非官方**的个人工具，与 TRAE / 字节跳动及其关联方没有任何关系，也未获得其认可或授权。
- 本项目**只做进程与目录隔离**，不提供、也不会提供绕过服务条款、伪造设备号、刷签到、批量领取额度或任何自动化账号操作的能力。
- 多账号使用是否合规取决于你与 TRAE 之间的服务条款，请自行判断并承担账号异常、额度回收等全部风险。使用前请阅读官方条款。
- 软件按「现状」提供，不作任何明示或暗示担保；作者不对数据丢失或账号状态变化负责。

---

## 参考依据

- 真机验证（设备号 / 签到结论）：https://github.com/magpie-community/plugins/issues/436
- 官方社区关于配置目录的回复：https://forum.trae.cn/t/topic/9364
- TRAE CN 官网（客户端版本与融合版说明）：https://www.trae.cn

---

## 许可证

[MIT](LICENSE) © 2026 CWJ-NUB
