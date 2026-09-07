# 🗂️ Qwen MCP Filesystem Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Protocol MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#prerequisites)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A dedicated, safe Model Context Protocol (MCP) server that empowers **Qwen Studio** and other desktop AI environments with controlled read, write, search, and management access to your local Windows files and projects.

---

## 📑 Table of Contents

- [Why This Exists](#why-this-exists)
- [How It Works](#how-it-works)
- [Features](#features)
- [Workspace Architecture](#workspace-architecture)
- [Download from GitHub](#download-from-github)
- [Prerequisites](#prerequisites)
- [Zero-Effort Quick Start](#zero-effort-quick-start)
- [Connecting to Qwen Studio & Other MCP Clients](#connecting-to-qwen-studio--other-mcp-clients)
- [Feeding Your Projects to Qwen Studio](#feeding-your-projects-to-qwen-studio)
- [Available MCP Tools](#available-mcp-tools)
- [Environment Variables](#environment-variables)
- [Security & Sandboxing](#security--sandboxing)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [License](#license)

---

## 💡 Why This Exists

Desktop AI environments—such as **Qwen Studio**—and complex creative workstation software (like **DaVinci Resolve Studio**) operate within protected sandbox boundaries. By design, they cannot freely browse, modify, or control files on your Windows machine.

When you want an AI assistant to assist with your codebase, automate scripting, or build plugins:

- ❌ **The Old Way**: You are forced to manually copy and paste code back and forth between your editor and the AI chat window. The AI has zero context about the rest of your project structure, cannot verify changes, and cannot create or edit files directly.
- ❌ **The Dangerous Way**: Giving an AI broad, unrestricted terminal or OS-level access risks accidental file deletion or damage to critical Windows system directories.

### The Solution: Qwen MCP

**Qwen MCP** acts as a secure, purpose-built bridge. It lets you "feed" specific local folders and external projects directly to Qwen Studio through the standardized **Model Context Protocol (MCP)**.

With Qwen MCP, Qwen Studio can autonomously explore your project tree, read files, write code, append changes, rename files, and perform regex searches—**strictly inside the project folders you choose to connect**.

---

## ⚙️ How It Works

```text
┌─────────────────────────┐          JSON-RPC (stdio)          ┌───────────────────────────┐
│       Qwen Studio       │ ◄────────────────────────────────► │     Qwen MCP Server       │
│   (Desktop AI Client)   │                                    │        (Python/uvx)       │
└─────────────────────────┘                                    └─────────────┬─────────────┘
                                                                             │ Controlled Sandboxed Access
                                                 ┌───────────────────────────┴───────────────────────────┐
                                                 ▼                                                       ▼
                                    ┌────────────────────────┐                             ┌────────────────────────┐
                                    │   Internal Projects    │                             │   External Projects    │
                                    │  workspace/projects/*  │                             │  Shortcut .txt Pointers│
                                    └────────────────────────┘                             └───────────┬────────────┘
                                                                                                       │ Maps to
                                                                                                       ▼
                                                                                           ┌────────────────────────┐
                                                                                           │ Any Folder on Windows  │
                                                                                           │ e.g. DaVinci Fuses,    │
                                                                                           │ Scripts, Web Projects  │
                                                                                           └────────────────────────┘
```

1. **You launch or connect the MCP server** in your Qwen Studio configuration (handled automatically via `uvx` with zero installation).
2. **You feed your project** either by placing it into the internal `workspace/projects/` folder or by adding a lightweight `.txt` link inside `workspace/external/` pointing to any folder on your computer.
3. **Qwen Studio takes over**: It queries the server tools to inspect files, execute changes, and search code with complete sandbox protection.

---

## ✨ Features

- 🛡️ **Strict Path Traversal Protection**: Prevents directory traversal attacks (`../`). File operations cannot escape the designated project boundary.
- 🔗 **Dual Project Mapping**:
  - **Internal Projects**: Store projects directly in `workspace/projects/<name>`.
  - **External Shortcuts**: Mount folders anywhere on your drive (e.g. DaVinci Resolve scripts, desktop code) via 1-line `.txt` link files without moving or copying original files.
- ⚡ **Zero-Effort Execution**: Automatically launches via Astral `uvx` without requiring manual virtual environments or dependency installs.
- 🔍 **In-File Text Search**: Deep regex and string search across files with line numbers and preview matches.
- 🛠️ **Full Filesystem Capabilities**: List directory structures, read UTF-8 and binary (Base64) files, write, append, rename/move, and delete.
- 🔒 **Drive Root Protection**: Explicitly blocks mounting Windows drive roots (like `C:\`) for maximum system safety.

---

## 🏗️ Workspace Architecture

```text
Qwen-mcp/
├── server.py               # FastMCP core filesystem engine
├── pyproject.toml          # Packaging metadata & entry point
├── requirements.txt        # Python dependencies (mcp>=1.0.0)
├── install.cmd / .sh       # Helper installation scripts (optional)
├── run.cmd / .sh           # Helper launch scripts (optional)
└── workspace/              # Root workspace directory
    ├── projects/           # Internal projects live here
    │   └── my-project/     # AI accesses as "my-project"
    └── external/           # External project shortcut link files
        └── davinci-app.txt # 1-line text file pointing to external folder
```

---

## 📥 Download from GitHub

Choose the method that works best for you:

### Option A: Clone via Git (Recommended)

```bash
git clone https://github.com/<your-username>/Qwen-mcp.git
cd Qwen-mcp
```

### Option B: Download as a ZIP Archive

1. On the **GitHub** repository page, click the green **`<> Code`** button.
2. Select **`Download ZIP`**.
3. Extract the ZIP file to your preferred folder (e.g., `D:\MCPs\Qwen-mcp` or `C:\Users\YourUser\Qwen-mcp`).
4. Open the folder in your terminal or command prompt.

---

## 📋 Prerequisites

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/) _(ensure "Add Python to PATH" is checked on Windows)_.
- **Astral `uv` (Recommended)**: [Install uv](https://docs.astral.sh/uv/getting-started/installation/) for instant, zero-setup execution.

```bash
# Verify uv installation
uv --version
```

---

## 🚀 Zero-Effort Quick Start

### Method 1: Using `uvx` (Zero-Install, Recommended)

You do **not** need to create virtual environments or manually install dependencies. `uvx` will automatically install requirements in an isolated cache and run the server on demand.

### Method 2: Standard Python Virtual Environment

If you prefer a traditional Python virtual environment:

#### On Windows:

Double-click `install.cmd` or run:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### On Linux / macOS:

```bash
chmod +x install.sh run.sh
./install.sh
```

---

## ⚙️ Connecting to Qwen Studio & Other MCP Clients

Add the server configuration into your client's MCP settings file (such as Qwen Studio, Claude Desktop, Antigravity IDE, Cursor, Cline, or Roo Code).

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

---

## 📂 Feeding Your Projects to Qwen Studio

Once Qwen MCP is connected, you have two effortless ways to grant Qwen Studio access to your projects:

### 1. The Direct Folder Method (Internal)

Simply create or copy your project folder inside `workspace/projects/`:

```text
workspace/projects/my-video-tool/
```

Qwen Studio will now recognize and interact with this project by the name `my-video-tool`.

### 2. The Shortcut Pointer Method (External — Recommended for Existing Work)

If your project already lives elsewhere on Windows (for example, in your Documents, Desktop, or DaVinci Resolve directories), you don't need to move it!

1. Create a `.txt` file inside `workspace/external/` named after your project, e.g., `davinci-plugin.txt`.
2. Inside that file, write the single absolute path to your project folder:
   ```text
   C:\Users\YourName\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Fuses\MyPlugin
   ```
3. That's it! Qwen Studio can now read and write directly to `davinci-plugin` safely.

_(You can also use the `qwen_register_external_project` tool from inside Qwen Studio to link external directories automatically)._

---

## 🧰 Available MCP Tools

Qwen Studio automatically receives access to these 12 filesystem tools:

| Tool                             | Description                                                           | Key Arguments                                           |
| :------------------------------- | :-------------------------------------------------------------------- | :------------------------------------------------------ |
| `qwen_status`                    | Checks server health, active workspace directory, and security flags. | _None_                                                  |
| `qwen_list_projects`             | Lists all internal and external connected projects.                   | _None_                                                  |
| `qwen_create_project`            | Creates a new project folder inside `workspace/projects/`.            | `name` (string)                                         |
| `qwen_register_external_project` | Registers an external folder path via a `.txt` shortcut file.         | `name`, `path`, `create` (bool)                         |
| `qwen_resolve_project`           | Resolves any project name to its actual absolute filesystem path.     | `project` (string)                                      |
| `qwen_list_files`                | Recursively or shallowly lists files and subdirectories.              | `project`, `path`, `pattern`, `recursive`               |
| `qwen_read_file`                 | Reads file content as clean UTF-8 text or Base64 (for binaries).      | `project`, `path`                                       |
| `qwen_write_file`                | Writes or overwrites a file (auto-creates directories).               | `project`, `path`, `content`, `encoding`                |
| `qwen_append_file`               | Appends text or binary content to an existing or new file.            | `project`, `path`, `content`, `encoding`                |
| `qwen_delete_file`               | Deletes a file or directory (`recursive=true` for folders).           | `project`, `path`, `recursive`                          |
| `qwen_rename_file`               | Renames or moves a file/folder within a project.                      | `project`, `old_path`, `new_path`                       |
| `qwen_search_files`              | Searches text/regex inside project files with line numbers.           | `project`, `query`, `path`, `pattern`, `case_sensitive` |

---

## 🔧 Environment Variables

You can configure operational limits via environment variables in your client config:

| Variable                              | Default            | Description                                                    |
| :------------------------------------ | :----------------- | :------------------------------------------------------------- |
| `QWEN_MCP_ROOT`                       | `workspace/`       | Path where `projects/` and `external/` are located.            |
| `QWEN_MCP_ALLOW_EXTERNAL`             | `true`             | Allows or blocks mapping external project shortcuts.           |
| `QWEN_MCP_ALLOW_CREATE_EXTERNAL_DIRS` | `true`             | Automatically creates missing target directories when linking. |
| `QWEN_MCP_MAX_READ_BYTES`             | `2097152` _(2 MB)_ | File size threshold before content is truncated or converted.  |

---

## 🔒 Security & Sandboxing

- **Directory Traversal Defense**: All paths are resolved and validated using strict containment checks. Any attempt by the AI to escape using `../../` triggers an immediate `PermissionError`.
- **Protected Roots**: Windows drive roots (`C:\`, `D:\`) cannot be registered as project sandboxes.
- **Isolated Control**: Setting `QWEN_MCP_ALLOW_EXTERNAL=false` restricts the server exclusively to files inside `workspace/projects/`.

---

## ❓ Troubleshooting & FAQ

<details>
<summary><b>1. Why can't Qwen Studio find my project?</b></summary>

Verify that:

- For internal projects: A folder named `<project-name>` exists inside `workspace/projects/`.
- For external projects: A text file named `<project-name>.txt` exists inside `workspace/external/` with a valid, absolute path on the first line.
- You can ask the AI to run `qwen_list_projects` to see all active projects detected by the server.
</details>

<details>
<summary><b>2. How do I give Qwen Studio access to DaVinci Resolve or Fusion scripts?</b></summary>

Create a text file `workspace/external/davinci-scripts.txt` and paste the path to your DaVinci Resolve Fusion Scripts or Fuses directory. In Qwen Studio, refer to the project as `davinci-scripts`.

</details>

<details>
<summary><b>3. Error: "Path escapes project root"</b></summary>

The AI client attempted to access a path above the designated project directory. All file operations must stay within the root of the targeted project.

</details>

<details>
<summary><b>4. uvx is not recognized on Windows</b></summary>

Install Astral `uv` from https://docs.astral.sh/uv/ and restart your terminal or Qwen Studio so your system `PATH` updates.

</details>

---

## 📄 License

Distributed under the [MIT License](LICENSE). Built for seamless, safe AI development.
