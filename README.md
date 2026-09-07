# 🗂️ Qwen MCP Filesystem Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Protocol MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A secure, high-performance [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants (Qwen, Claude Desktop, Antigravity, Cursor, Cline, Roo Code, etc.) controlled read, write, and search access to designated project workspaces.

---

## 📑 Table of Contents

- [Features](#features)
- [Workspace Architecture](#workspace-architecture)
- [Download from GitHub](#download-from-github)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
  - [Method 1: Zero-Install with `uvx` (Recommended)](#method-1-zero-install-with-uvx-recommended)
  - [Method 2: Standard Python Virtual Environment](#method-2-standard-python-virtual-environment)
- [MCP Client Configuration](#mcp-client-configuration)
- [Available MCP Tools](#available-mcp-tools)
- [Environment Variables](#environment-variables)
- [Security and Sandboxing](#security-and-sandboxing)
- [Troubleshooting and FAQ](#troubleshooting-and-faq)

---

## ✨ Features

- 🛡️ **Sandbox Security**: Built-in protection against directory traversal attacks (`../`). AI clients can only interact within project boundaries.
- 📁 **Dual Project Modes**:
  - **Internal Projects**: Self-contained directories inside `workspace/projects/`.
  - **External Projects**: Mount any folder on your machine via `.txt` link shortcuts without duplicating or moving files.
- ⚡ **Zero-Config Execution**: Launch seamlessly with `uvx` without manually creating virtual environments.
- 🔍 **In-File Text Search**: Fast string and pattern search across files with line numbers and preview snippets.
- 🛠️ **Full Filesystem Toolkit**: Create, list, read, write, append, rename/move, and delete files or folders.
- 🗜️ **Binary & UTF-8 Support**: Reads and writes text as standard UTF-8; automatically encodes binary data in Base64.

---

## 🏗️ Workspace Architecture

```text
Qwen-mcp/
├── server.py               # FastMCP server implementation
├── pyproject.toml          # Packaging metadata & entry point
├── requirements.txt        # Python dependencies
├── install.cmd / .sh       # Automated installation helper scripts
├── run.cmd / .sh           # Server launcher helper scripts
└── workspace/              # Root workspace directory (customizable)
    ├── projects/           # Internal projects live here
    │   └── my-project/     # AI accesses as "my-project"
    └── external/           # Shortcut pointer files for external folders
        └── desktop-app.txt # Points to an external path on your machine
```

### 1. Internal Projects

Any folder created inside `workspace/projects/<project-name>` is directly accessible by its folder name:

- Folder path: `workspace/projects/ecommerce-api`
- AI Project Name: `ecommerce-api`

### 2. External Projects

To expose an existing project located anywhere on your computer without moving it, create a `<project-name>.txt` file inside `workspace/external/` (or directly inside `workspace/`).

Inside `workspace/external/desktop-app.txt`:

```text
C:\Users\YourName\Desktop\my-existing-app
```

_(On Linux/macOS, use standard paths like `/home/yourname/Desktop/my-existing-app`)_

The AI can now interact with this external folder using the project name `desktop-app`.

---

## 📥 Download from GitHub

You can obtain the project files using either of the following methods:

### Option A: Clone via Git (Recommended)

Open your terminal or PowerShell and run:

```bash
git clone https://github.com/<your-username>/Qwen-mcp.git
cd Qwen-mcp
```

### Option B: Download as a ZIP Archive

1. Visit the repository page on **GitHub**.
2. Click the green **`<> Code`** button located at the top right of the file list.
3. Click **`Download ZIP`**.
4. Extract the `.zip` archive to a folder on your computer (e.g. `D:/MCPs/Qwen-mcp` or `~/MCPs/Qwen-mcp`).
5. Open your terminal or Command Prompt inside the extracted folder.

---

## 📋 Prerequisites

- **Python 3.10 or higher**: [Download Python](https://www.python.org/downloads/) _(make sure to check "Add Python to PATH" on Windows)_.
- _(Recommended)_ **Astral `uv`**: [Install uv](https://docs.astral.sh/uv/getting-started/installation/) for ultra-fast, zero-setup execution.

---

## 🚀 Installation and Setup

### Method 1: Zero-Install with `uvx` (Recommended)

When using `uvx`, you do **not** need to create a virtual environment or install dependencies manually. Your MCP client will execute the server on demand.

Make sure `uv` is installed:

```bash
# Verify installation
uv --version
```

### Method 2: Standard Python Virtual Environment

If you prefer using standard Python:

#### On Windows:

Run the automated batch script:

```cmd
install.cmd
```

_Or manually run:_

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### On Linux / macOS:

Run the automated shell script:

```bash
chmod +x install.sh run.sh
./install.sh
```

_Or manually run:_

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ MCP Client Configuration

Add `qwen-mcp` to your MCP client configuration file (e.g., `claude_desktop_config.json`, `mcp_config.json`, or Cursor / Cline / Antigravity MCP settings).

### Configuration Using `uvx` (Recommended)

```json
{
  "mcpServers": {
    "qwen-mcp": {
      "command": "uvx",
      "args": ["--from", "/ABSOLUTE/PATH/TO/Qwen-mcp", "qwen-mcp"],
      "env": {
        "QWEN_MCP_ALLOW_EXTERNAL": "true"
      }
    }
  }
}
```

> [!NOTE]
> Replace `/ABSOLUTE/PATH/TO/Qwen-mcp` with your actual repository path.
>
> - **Windows Example:** `D:/Root/DummyCode/Experiment/MCPs/Qwen-mcp`
> - **Linux/macOS Example:** `/home/user/projects/Qwen-mcp`

### Configuration Using Python Directly

```json
{
  "mcpServers": {
    "qwen-mcp": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/Qwen-mcp/server.py"],
      "env": {
        "QWEN_MCP_ALLOW_EXTERNAL": "true"
      }
    }
  }
}
```

_(On Windows, you can specify the full interpreter path if `python` is not on your global PATH, e.g., `D:/Root/DummyCode/Experiment/MCPs/Qwen-mcp/.venv/Scripts/python.exe`)_.

---

## 🧰 Available MCP Tools

Once connected, your AI assistant has access to the following 12 tools:

| Tool                             | Description                                                                            | Key Arguments                                                                 |
| :------------------------------- | :------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------- |
| `qwen_status`                    | Returns server health, active workspace directory, and security flags.                 | _None_                                                                        |
| `qwen_list_projects`             | Lists all detected internal projects and linked external shortcuts.                    | _None_                                                                        |
| `qwen_create_project`            | Creates a new internal project folder inside `workspace/projects/`.                    | `name` (string)                                                               |
| `qwen_register_external_project` | Links an external directory by saving its path into a `.txt` link file.                | `name`, `path`, `create` (optional bool)                                      |
| `qwen_resolve_project`           | Resolves any registered project name to its actual absolute filesystem path.           | `project` (string)                                                            |
| `qwen_list_files`                | Lists files and folders with optional glob filtering and recursion.                    | `project`, `path` (default `""`), `pattern` (default `*`), `recursive` (bool) |
| `qwen_read_file`                 | Reads file content. Returns clean UTF-8 text or Base64 binary string.                  | `project`, `path`                                                             |
| `qwen_write_file`                | Creates or overwrites a file (auto-creates intermediate directories).                  | `project`, `path`, `content`, `encoding`, `create_dirs`                       |
| `qwen_append_file`               | Appends content to an existing file (creates file if it does not exist).               | `project`, `path`, `content`, `encoding`, `create_dirs`                       |
| `qwen_delete_file`               | Deletes a file or directory (`recursive=true` required for non-empty folders).         | `project`, `path`, `recursive` (bool)                                         |
| `qwen_rename_file`               | Renames or moves a file or directory within a project.                                 | `project`, `old_path`, `new_path`                                             |
| `qwen_search_files`              | Performs string or regex search across files, reporting line numbers and text matches. | `project`, `query`, `path`, `pattern`, `case_sensitive`, `max_results`        |

---

## 🔧 Environment Variables

You can customize the server behavior by defining environment variables in your client configuration:

| Variable                              | Default              | Description                                                                |
| :------------------------------------ | :------------------- | :------------------------------------------------------------------------- |
| `QWEN_MCP_ROOT`                       | `Qwen-mcp/workspace` | The directory where `projects/` and `external/` reside.                    |
| `QWEN_MCP_ALLOW_EXTERNAL`             | `true`               | When set to `false`, disables access to external `.txt` project shortcuts. |
| `QWEN_MCP_ALLOW_CREATE_EXTERNAL_DIRS` | `true`               | Allows auto-creating external directory targets if they do not yet exist.  |
| `QWEN_MCP_MAX_READ_BYTES`             | `2097152` _(2 MB)_   | Max bytes read before truncating or streaming file content.                |

---

## 🔒 Security and Sandboxing

- **Strict Path Containment**: Any attempt by an AI client to access files outside the designated project root (e.g. `../../Windows/System32` or `../../etc/passwd`) raises a `PermissionError`.
- **System Root Protection**: Registering root filesystem drives (e.g. `C:\` or `/`) as projects is explicitly disallowed.
- **Controlled Exposure**: Set `QWEN_MCP_ALLOW_EXTERNAL=false` if you want the server to strictly restrict file operations to the local `workspace/projects/` directory only.

---

## ❓ Troubleshooting and FAQ

<details>
<summary><b>1. Error: "Project '&lt;name&gt;' not found"</b></summary>

Ensure either:

- A folder named `<name>` exists inside `workspace/projects/`, or
- A link file named `<name>.txt` exists inside `workspace/external/` pointing to a valid absolute directory path.

</details>

<details>
<summary><b>2. Error: "Path escapes project root"</b></summary>

The requested relative path traverses above the project folder. Ensure paths provided to file tools do not use `../` to back out of the project sandbox.

</details>

<details>
<summary><b>3. MCP client does not find the <code>uvx</code> command</b></summary>

Make sure `uv` is installed and available in your system's `PATH`. Restart your terminal or MCP host app (e.g. Claude Desktop) after installing `uv`.

</details>

---

## 📄 License

Distributed under the [MIT License](LICENSE). Feel free to use, modify, and integrate into your own AI workflows.
