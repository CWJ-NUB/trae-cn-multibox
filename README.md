# Trae CN 多开启动台

一台 Windows 机器上同时登几个 Trae CN 账号，用一个界面管起来。

做法挺土：给每个实例单独指定 `--user-data-dir`，登录态就各存各的。这是 Electron / VS Code 系客户端自带的参数，不用改客户端、不用装切号工具，也不碰任何凭据文件。

*A single-file Windows GUI launcher for running multiple TRAE CN instances with separate accounts. No installer, no dependencies, no credential handling.*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-0078D6) ![Dependencies](https://img.shields.io/badge/Dependencies-0-brightgreen) ![License](https://img.shields.io/badge/License-MIT-orange)

## 先跑起来

需要 Windows 10/11 + Python 3，系统自带 tkinter 就够。不用 pip install，不用管理员权限，不用打包成 exe。

1. 下载 [`TraeCN多开.pyw`](TraeCN多开.pyw)，双击。Windows 会把 `.pyw` 交给 `pythonw.exe`，直接出界面，没有黑色控制台窗口。
2. 顶部填一次 `Trae CN.exe` 的路径，点「自动探测」一般能自己找到。
3. 第 1 行「主实例」是你原来那个账号，点「启动」和双击桌面图标一样；要加号就点「新建实例」或「批量新建」，选中新行点「启动」，在弹出的窗口里登另一个账号。

双击没反应的话，在这个目录按住 Shift 右键开 PowerShell，跑 `python TraeCN多开.pyw`，报错会直接显示，也会写进 `launcher.log`。界面里有「桌面快捷方式」按钮，还有「使用说明」按钮，完整文档内置在程序里，不用回来翻 README。

## 源码在哪

仓库里那个 [`TraeCN多开.pyw`](TraeCN多开.pyw) 就是全部源码，一行不缺。纯文本 Python，只用标准库，没有编译、没有打包、没有混淆、没有构建步骤，也不会偷偷联网。作者是 `CWJ-NUB`。改完保存，下次双击跑的就是新逻辑；想看报错就 `python TraeCN多开.pyw`。

`.pyw` 和 `.py` 只差一件事：Windows 双击时前者走 `pythonw.exe`，不弹控制台。文件本身是普通 Python，GitHub 也按 Python 高亮（见 [`.gitattributes`](.gitattributes)）。MIT 许可证，随便改、随便分发。

原来的账号一个都不动，照常用桌面图标打开；新增的每个账号分到一个独立的 `account-N` 目录，各自登录、各自保留设置和插件。工具只读两样东西：进程命令行、目录大小。不读 `storage.json`、不解密凭据、不改机器码、不写注册表。

## 界面里有什么

| 功能 | 说明 |
| --- | --- |
| 主实例固定第 1 行 | 启动命令就是 `Trae CN.exe --new-window`，不带任何隔离参数 |
| 批量新建 1–30 个 | 编号自动排 `account-2`、`account-3`…；目录首次启动才建，不会一上来占几十 GB |
| 全部启动 / 单独启动 | 已运行的不重复启动；每个实例独立工作目录，Crashpad 日志不会堆在启动器旁边 |
| 停止 | 按命令行里的 `--user-data-dir` 对上 PID 再 `taskkill /T /F`，不会误杀别的实例 |
| 状态与占用 | 后台线程查 WMI 进程、算目录大小，界面不卡；运行中墨绿、未运行灰色 |
| 账号备注 | 双击行编辑，纯文本标签，方便记住哪个窗口登的是哪个号 |
| 重置登录 | 目录改名成 `.bak-时间戳` 备份，不删数据，可回滚 |
| 扫描已有目录 | 把之前手工建的 `account-N` 收进列表，不重复建号 |
| 自动探测 exe | 先从运行中的 Trae 进程读路径，再回退到常见安装位置 |
| 作者 / 仓库入口 | 标题右边和「使用说明」窗口里都能点，点一下用系统浏览器打开项目仓库。只有这一步会开浏览器，不发任何数据 |

进程识别做了两层过滤：Chromium 子进程带 `--type=`，VS Code 语言服务进程带 `--node-ipc`，两者都排除。否则窗口关掉后残留的辅助进程会让「启动」点了没反应。

## 原理

```
桌面图标 / 主实例          Trae CN.exe --new-window
                            └─ 默认目录 %APPDATA%\Trae CN  →  账号 A

启动台第 2 行              Trae CN.exe --user-data-dir=<ROOT>\account-2 --new-window
                            └─ 独立目录                       →  账号 B

启动台第 3 行              Trae CN.exe --user-data-dir=<ROOT>\account-3 --new-window
                            └─ 独立目录                       →  账号 C
```

`ROOT` = `%LOCALAPPDATA%\TraeCNProfiles`。每个目录存自己的登录态、设置、扩展和缓存，互不覆盖。实例清单在同目录的 `launcher.json`，只有文本标签和 exe 路径，没有 token。

不用复制整个安装目录 —— 社区里流传的「把 Trae 复制成 Trae-2」是多余的，同一个 exe 加参数就行。

## 设备号不会跟着分开

多开只解决「同时在线」，别指望靠它刷签到。

2026-10-29 有人在 Windows 11 + TRAE CN 3.4.4（融合版）上做过完整真机验证，记在 [magpie-community/plugins#436](https://github.com/magpie-community/plugins/issues/436)：

| 验证项 | 结果 |
| --- | --- |
| `--user-data-dir=<新目录>` 是否生效 | 生效，生成独立 `storage.json`，UID 不同 |
| 默认目录的账号 A 是否被覆盖 | 没变，文件哈希和修改时间一致 |
| 设备号是否随目录分开 | 没分开，还是同一个 16 位设备号 |
| 第二账号在客户端手动签到 | 提示「本设备每日已签到」 |

维护者的结论是：签到按设备算，同一台机器当天只有第一个账号能领；用量、模型、请求按账号独立，不受影响。那个 issue 已经关了。

挂几个号各跑各的任务没问题，指望多开领多份签到积分是白折腾。

官方社区 [topic/9364](https://forum.trae.cn/t/topic/9364) 在 2026-04-15 回复过「暂不支持修改配置目录」，但参数确实被客户端接受。两件事不冲突：参数能用，不代表所有状态都跟着走，设备号就是反例。以上是第三方实测，不是官方承诺，客户端升级后行为可能变化，用之前自己验一次更稳妥。

## 数据放在哪

| 项目 | 位置 |
| --- | --- |
| 账号 A 的登录态 | `%APPDATA%\Trae CN`，Trae 自己管，本工具从不读写、改名或删除 |
| 隔离实例 | `%LOCALAPPDATA%\TraeCNProfiles\account-N\` |
| 实例清单 | `%LOCALAPPDATA%\TraeCNProfiles\launcher.json` |
| 异常日志 | `%LOCALAPPDATA%\TraeCNProfiles\launcher.log` |

账号备注只是给自己看的文本，不存密码 / Cookie / Token。每个实例的数据目录可能长到 3–8 GB（含模型缓存），开多个之前先看磁盘；融合版更新频繁，升级后独立目录偶尔要重建。

## 常见问题

**原来的账号会丢吗？**
不会。主实例走 Trae 的默认目录，工具只新增 `account-N`。主实例的「重置登录」「删除实例」是禁用的，免得手滑把原来的设置、插件和工作区搞没了。想给主实例换号，在 Trae 窗口里退出登录就行。

**和「一键切号」工具有什么区别？**
切号是「关进程 → 覆写登录态 → 重启」，同一时刻只有一个账号在线，而且会动凭据文件。这里是多个窗口同时在线，完全不碰凭据。

**为什么用 `.pyw` 不用 `.cmd` / exe？**
中文路径走 Windows 宽字符，不经过 cmd 代码页，不会乱码；没有黑框；零第三方依赖；源码能直接审阅，不用信任来路不明的二进制。

**状态不准 / 停止没反应？**
点「刷新状态」，刚启动的进程要一两秒才登记。「停止」依赖命令行里的 `--user-data-dir`，自己手工开的普通 Trae 窗口，工具管不到。

**想连扩展和缓存也彻底隔开？**
这里只做 `--user-data-dir` 隔离。更彻底的 `APPDATA` / `USERPROFILE` 环境变量级重定向要第三方方案，代价是每个实例多占几 GB，而且通常要碰凭据。

## 免责声明

- 本项目是非官方的个人工具，与 TRAE / 字节跳动及其关联方没有任何关系，也未获得其认可或授权。
- 本项目只做进程与目录隔离，不提供、也不会提供绕过服务条款、伪造设备号、刷签到、批量领取额度或任何自动化账号操作的能力。
- 多账号使用是否合规取决于你与 TRAE 之间的服务条款，请自行判断并承担账号异常、额度回收等全部风险。使用前请阅读官方条款。
- 软件按「现状」提供，不作任何明示或暗示担保；作者不对数据丢失或账号状态变化负责。

## 参考依据

- 真机验证（设备号 / 签到结论）：https://github.com/magpie-community/plugins/issues/436
- 官方社区关于配置目录的回复：https://forum.trae.cn/t/topic/9364
- TRAE CN 官网：https://www.trae.cn

## 许可证

[MIT](LICENSE) © 2026 CWJ-NUB
