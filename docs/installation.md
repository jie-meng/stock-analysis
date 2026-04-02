# 安装指南

本指南帮助你从零开始配置好运行环境。你需要安装两样东西：**Python**（运行分析脚本）和 **opencode**（AI 编程助手）。

---

## 1. 安装 Python

需要 Python 3.11 或更高版本（推荐 3.12）。

<details>
<summary><strong>macOS</strong></summary>

### 方式一：Homebrew 安装（推荐）

如果你还没安装 Homebrew，先安装它：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

然后安装 Python：

```bash
brew install python@3.12
```

验证安装：

```bash
python3 --version
# 应显示 Python 3.12.x
```

### 方式二：官网下载

1. 打开 [python.org/downloads](https://www.python.org/downloads/)
2. 下载 macOS 安装包（.pkg 文件）
3. 双击运行安装程序，按提示完成安装

验证安装：

```bash
python3 --version
```

</details>

<details>
<summary><strong>Windows</strong></summary>

### 方式一：官网下载（推荐）

1. 打开 [python.org/downloads](https://www.python.org/downloads/)
2. 点击下载最新 Python 3.12.x 版本
3. **重要**：运行安装程序时，勾选底部的 **Add Python to PATH**
4. 点击 "Install Now" 完成安装

验证安装（打开"命令提示符"或 PowerShell）：

```bash
python --version
# 应显示 Python 3.12.x
```

### 方式二：Microsoft Store

1. 打开 Microsoft Store
2. 搜索 "Python 3.12"
3. 点击安装

> Windows 上 Python 命令是 `python`（不是 `python3`），后续文档中看到 `python3` 请替换为 `python`。

</details>

<details>
<summary><strong>Linux (Ubuntu/Debian)</strong></summary>

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

验证安装：

```bash
python3 --version
```

**其他发行版：**

- Fedora / RHEL: `sudo dnf install python3 python3-pip`
- Arch: `sudo pacman -S python python-pip`

</details>

---

## 2. 安装 Python 依赖包

打开终端/命令提示符，进入项目目录后安装所需的包：

```bash
cd stock-analysis
pip install -Ur requirements.txt
```

> 如果 `pip` 命令提示找不到，试试 `pip3`。Windows 上用 `pip`，macOS/Linux 上用 `pip3`。

---

## 3. 安装 opencode

[opencode](https://opencode.ai) 是一个开源 AI 编程助手，也是本项目的交互入口。

下表列出了各平台的安装方式及是否需要额外依赖：

| 平台 | 安装方式 | 是否需要 Node.js | 说明 |
|------|----------|:---:|------|
| macOS | `brew install anomalyco/tap/opencode` | 否 | Homebrew 直接安装二进制 |
| macOS | `curl -fsSL https://opencode.ai/install \| bash` | 否 | 脚本自动下载二进制 |
| macOS | 桌面应用 | 否 | 从官网下载 .dmg |
| Windows | `choco install opencode` | 否 | Chocolatey 安装二进制 |
| Windows | `scoop install opencode` | 否 | Scoop 安装二进制 |
| Windows | `npm install -g opencode-ai` | **是** | 需要先安装 Node.js |
| Windows | 桌面应用 | 否 | 从官网下载 .exe |
| Linux | `curl -fsSL https://opencode.ai/install \| bash` | 否 | 脚本自动下载二进制 |
| Linux | `brew install anomalyco/tap/opencode` | 否 | Homebrew on Linux |
| Linux | `npm install -g opencode-ai` | **是** | 需要先安装 Node.js |
| Linux | `paru -S opencode-bin` | 否 | Arch Linux AUR |

> **简单原则**：优先用 brew / choco / scoop / curl 脚本安装，这些方式**不需要 Node.js**。只有选择 npm 方式才需要先装 Node.js。

<details>
<summary><strong>macOS 安装步骤</strong></summary>

### 方式一：Homebrew（推荐，无需 Node.js）

```bash
brew install anomalyco/tap/opencode
```

> 推荐用 `anomalyco/tap/opencode` 而非 `brew install opencode`，前者由 opencode 团队维护，更新更及时。

### 方式二：curl 安装脚本（无需 Node.js）

```bash
curl -fsSL https://opencode.ai/install | bash
```

### 方式三：桌面应用（无需 Node.js）

前往 [opencode.ai/download](https://opencode.ai/download) 下载 macOS 版桌面应用（beta）。

</details>

<details>
<summary><strong>Windows 安装步骤</strong></summary>

### 方式一：Chocolatey（推荐，无需 Node.js）

如果你还没安装 Chocolatey，以**管理员身份**打开 PowerShell，执行：

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

然后安装 opencode：

```powershell
choco install opencode
```

### 方式二：Scoop（无需 Node.js）

如果你还没安装 Scoop：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

然后安装 opencode：

```powershell
scoop install opencode
```

### 方式三：npm（需要 Node.js）

如果你已经安装了 Node.js，可以直接用 npm：

```powershell
npm install -g opencode-ai
```

如果没有 Node.js，参考下方 [安装 Node.js](#windows-安装-nodejs) 的说明。

### 方式四：桌面应用（无需 Node.js）

前往 [opencode.ai/download](https://opencode.ai/download) 下载 Windows 版桌面应用（beta）。

### 方式五：手动下载二进制（无需 Node.js）

前往 [GitHub Releases](https://github.com/anomalyco/opencode/releases) 下载 Windows 版 `.exe` 文件，放到 PATH 中的目录即可。

</details>

<details>
<summary><strong>Linux 安装步骤</strong></summary>

### 方式一：curl 安装脚本（推荐，无需 Node.js）

```bash
curl -fsSL https://opencode.ai/install | bash
```

### 方式二：Homebrew on Linux（无需 Node.js）

```bash
brew install anomalyco/tap/opencode
```

### 方式三：Arch Linux（无需 Node.js）

```bash
sudo pacman -S opencode        # 稳定版
paru -S opencode-bin           # AUR 最新版
```

### 方式四：npm（需要 Node.js）

```bash
npm install -g opencode-ai
```

</details>

---

### Windows 安装 Node.js

> 仅在选择 npm 方式安装 opencode 时才需要。推荐优先使用 Chocolatey 或 Scoop，可以跳过此节。

<details>
<summary><strong>Node.js 安装步骤</strong></summary>

### 方式一：官网下载（推荐）

1. 打开 [nodejs.org](https://nodejs.org/)
2. 下载 LTS（长期支持）版本
3. 运行安装程序，按默认选项安装即可

验证安装：

```powershell
node --version
npm --version
```

### 方式二：通过 Chocolatey

```powershell
choco install nodejs-lts
```

### 方式三：通过 Scoop

```powershell
scoop install nodejs-lts
```

安装完 Node.js 后，就可以用 npm 安装 opencode 了：

```powershell
npm install -g opencode-ai
```

</details>

---

### 配置 opencode

安装完成后，进入项目目录启动 opencode：

```bash
cd stock-analysis
opencode
```

首次运行需要配置 AI 模型。最简单的方式是使用 opencode 内置的 Zen 服务：

1. 在 opencode 界面中输入 `/connect`
2. 选择 `opencode`
3. 前往 [opencode.ai/auth](https://opencode.ai/auth) 登录并获取 API Key
4. 将 API Key 粘贴到提示框中

也支持其他模型供应商（OpenAI、Anthropic、DeepSeek、Gemini 等），以及用 GitHub Copilot 或 ChatGPT Plus/Pro 账号直接登录。

更多配置细节参考 [opencode 官方文档](https://opencode.ai/docs)。

---

## 4. 下载本项目

```bash
git clone https://github.com/your-username/stock-analysis.git
cd stock-analysis
pip install -Ur requirements.txt
```

如果你不熟悉 git，也可以在 GitHub 页面点击 **Code → Download ZIP**，下载后解压，然后在解压目录执行 `pip install -Ur requirements.txt`。

---

## 5. 开始使用

一切就绪后，在项目目录启动 opencode：

```bash
cd stock-analysis
opencode
```

然后你就可以直接用中文向 AI 助手提问了，比如：

```
帮我看看贵州茅台最近的走势
```

详细的使用方法请参考 [使用指南](./usage-guide.md)。

---

## 常见问题

<details>
<summary><strong>pip install 报错 "Permission denied"</strong></summary>

在命令前加 `--user` 参数：

```bash
pip install --user -r requirements.txt
```

</details>

<details>
<summary><strong>macOS 提示 "command not found: python3"</strong></summary>

安装 Xcode 命令行工具：

```bash
xcode-select --install
```

</details>

<details>
<summary><strong>Windows 上 python 命令无法识别</strong></summary>

1. 重新运行 Python 安装程序
2. 选择 "Modify"
3. 确保勾选了 "Add Python to environment variables"

</details>

<details>
<summary><strong>akshare 安装很慢或失败</strong></summary>

使用国内镜像源：

```bash
pip install -Ur requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

</details>

<details>
<summary><strong>opencode 安装后提示 "command not found"</strong></summary>

- 如果用 npm 安装的，检查 Node.js 的全局 bin 目录是否在 PATH 中：`npm bin -g`
- 如果用 curl 脚本安装的，重新打开终端窗口
- Windows 上安装后可能需要重启 PowerShell

</details>
