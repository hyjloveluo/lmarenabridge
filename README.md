# 🚀 LMArena Bridge - AI模型竞技场API代理器 🌉

欢迎来到新一代的 LMArena Bridge！🎉 这是一个基于 FastAPI 和 WebSocket 的高性能工具集，它能让你通过任何兼容 OpenAI API 的客户端或应用程序，无缝使用 [LMArena.ai](https://lmarena.ai/) 平台上提供的海量大语言模型。

这个重构版本旨在提供更稳定、更易于维护和扩展的体验。

## ✨ 主要功能

*   **🚀 高性能后端**: 基于 **FastAPI** 和 **Uvicorn**，提供异步、高性能的 API 服务。
*   **🔌 稳定的 WebSocket 通信**: 使用 WebSocket 替代 Server-Sent Events (SSE)，实现更可靠、低延迟的双向通信。
*   **🤖 OpenAI 兼容接口**: 完全兼容 OpenAI `v1/chat/completions`、`v1/models` 以及 `v1/images/generations` 端点。
*   **📋 手动模型列表更新**: 新增 `model_updater.py` 脚本，可手动触发从 LMArena 页面提取最新的可用模型列表，并保存为 `available_models.json`，方便查阅和更新核心的 `models.json`。
*   **📎 通用文件上传**: 支持通过 Base64 上传任意类型的文件（图片、音频、PDF、代码等），并支持一次性上传多个文件。
*   **🎨 原生流式文生图**: 文生图功能已与文本生成完全统一。只需在 `/v1/chat/completions` 接口中请求图像模型，即可像接收文本一样，流式接收到 Markdown 格式的图片。
*   **🗣️ 完整对话历史支持**: 自动将会话历史注入到 LMArena，实现有上下文的连续对话。
*   **🌊 实时流式响应**: 像原生 OpenAI API 一样，实时接收来自模型的文本回应。
*   **🔄 自动程序更新**: 启动时自动检查 GitHub 仓库，发现新版本时可自动下载并更新程序。
*   **🆔 一键式会话ID更新**: 提供 `id_updater.py` 脚本，只需在浏览器操作一次，即可自动捕获并更新 `config.jsonc` 中所需的会话 ID。
*   **⚙️ 浏览器自动化**: 配套的油猴脚本 (`LMArenaApiBridge.js`) 负责与后端服务器通信，并在浏览器中执行所有必要操作。
*   **🍻 酒馆模式 (Tavern Mode)**: 专为 SillyTavern 等应用设计，智能合并 `system` 提示词，确保兼容性。
*   **🤫 Bypass 模式**: 尝试通过在请求中额外注入一个空的用户消息，绕过平台的敏感词审查。
*   **🔐 API Key 保护**: 可在配置文件中设置 API Key，为你的服务增加一层安全保障。
*   **🎯 模型-会话高级映射**: 支持为不同模型配置独立的会话ID池，并能为每个会话指定特定的工作模式（如 `battle` 或 `direct_chat`），实现更精细的请求控制。

## ⚙️ 配置文件说明

项目的主要行为通过 `config.jsonc`, `models.json` 和 `model_endpoint_map.json` 进行控制。

### `models.json` - 核心模型映射
这个文件包含了 LMArena 平台上的模型名称到其内部ID的映射，并支持通过特定格式指定模型类型。

*   **重要**: 这是程序运行所**必需**的核心文件。你需要手动维护这个列表。
*   **格式**:
    *   **标准文本模型**: `"model-name": "model-id"`
    *   **图像生成模型**: `"model-name": "model-id:image"`
*   **说明**:
    *   程序通过检查模型ID字符串中是否包含 `:image` 来识别图像模型。
    *   这种格式保持了对旧配置文件的最大兼容性，未指定类型的模型将默认为 `"text"`。
*   **示例**:
    ```json
    {
      "gemini-1.5-pro-flash-20240514": "gemini-1.5-pro-flash-20240514",
      "dall-e-3": "null:image"
    }
    ```

### `available_models.json` - 可用模型参考 (可选)
*   这是一个**参考文件**，由新增的 `model_updater.py` 脚本生成。
*   它包含了从 LMArena 页面上提取的所有模型的完整信息（ID, 名称, 组织等）。
*   你可以运行 `model_updater.py` 来生成或更新此文件，然后从中复制你需要使用的模型信息到 `models.json` 中。

### `config.jsonc` - 全局配置

这是主要的配置文件，包含了服务器的全局设置。

*   `session_id` / `message_id`: 全局默认的会话ID。当模型没有在 `model_endpoint_map.json` 中找到特定映射时，会使用这里的ID。
*   `id_updater_last_mode` / `id_updater_battle_target`: 全局默认的请求模式。同样，当特定会话没有指定模式时，会使用这里的设置。
*   `use_default_ids_if_mapping_not_found`: 一个非常重要的开关（默认为 `true`）。
    *   `true`: 如果请求的模型在 `model_endpoint_map.json` 中找不到，就使用全局默认的ID和模式。
    *   `false`: 如果找不到映射，则直接返回错误。这在你需要严格控制每个模型的会话时非常有用。
*   其他配置项如 `api_key`, `tavern_mode_enabled` 等，请参考文件内的注释。

### `model_endpoint_map.json` - 模型专属配置

这是一个强大的高级功能，允许你覆盖全局配置，为特定的模型设置一个或多个专属的会话。

**核心优势**:
1.  **会话隔离**: 为不同的模型使用独立的会话，避免上下文串扰。
2.  **提高并发**: 为热门模型配置一个ID池，程序会在每次请求时随机选择一个ID使用，模拟轮询，减少单个会话被频繁请求的风险。
3.  **模式绑定**: 将一个会话ID与它被捕获时的模式（`direct_chat` 或 `battle`）绑定，确保请求格式永远正确。

**配置示例**:
```json
{
  "claude-3-opus-20240229": [
    {
      "session_id": "session_for_direct_chat_1",
      "message_id": "message_for_direct_chat_1",
      "mode": "direct_chat"
    },
    {
      "session_id": "session_for_battle_A",
      "message_id": "message_for_battle_A",
      "mode": "battle",
      "battle_target": "A"
    }
  ],
  "gemini-1.5-pro-20241022": {
      "session_id": "single_session_id_no_mode",
      "message_id": "single_message_id_no_mode"
  }
}
```
*   **Opus**: 配置了一个ID池。请求时会随机选择其中一个，并严格按照其绑定的 `mode` 和 `battle_target` 来发送请求。
*   **Gemini**: 使用了单个ID对象（旧格式，依然兼容）。由于它没有指定 `mode`，程序会自动使用 `config.jsonc` 中定义的全局模式。

## 🛠️ 安装与使用

你需要准备好 Python 环境和一款支持油猴脚本的浏览器 (如 Chrome, Firefox, Edge)。

### 1. 准备工作

*   **安装 Python 依赖**
    打开终端，进入项目根目录，运行以下命令：
    ```bash
    pip install -r requirements.txt
    ```

*   **安装油猴脚本管理器**
    为你的浏览器安装 [Tampermonkey](https://www.tampermonkey.net/) 扩展。

*   **安装本项目油猴脚本**
    1.  打开 Tampermonkey 扩展的管理面板。
    2.  点击“添加新脚本”或“Create a new script”。
    3.  将 [`TampermonkeyScript/LMArenaApiBridge.js`](TampermonkeyScript/LMArenaApiBridge.js) 文件中的所有代码复制并粘贴到编辑器中。
    4.  保存脚本。

### 2. 运行主程序

1.  **启动本地服务器**
    在项目根目录下，运行主服务程序：
    ```bash
    python api_server.py
    ```
    当你看到服务器在 `http://127.0.0.1:5102` 启动的提示时，表示服务器已准备就绪。

2.  **保持 LMArena 页面开启**
    确保你至少有一个 LMArena 页面是打开的，并且油猴脚本已成功连接到本地服务器（页面标题会以 `✅` 开头）。这里无需保持在对话页面，只要是域名下的页面都可以LeaderBoard都可以。

### 3. 更新可用模型列表 (可选，但推荐)
此步骤会生成 `available_models.json` 文件，让你知道当前 LMArena 上有哪些可用的模型，方便你更新 `models.json`。
1.  **确保主服务器正在运行**。
2.  打开**一个新的终端**，运行模型更新器：
    ```bash
    python model_updater.py
    ```
3.  脚本会自动请求浏览器抓取模型列表，并在根目录生成 `available_models.json` 文件。
4.  打开 `available_models.json`，找到你想要的模型，将其 `"publicName"` 和 `"id"` 键值对复制到 `models.json` 文件中（格式为 `"publicName": "id"`）。

### 4. 配置会话 ID (需要时，一般只配置一次即可，除非切换模型或者原对话失效)

这是**最重要**的一步。你需要获取一个有效的会话 ID 和消息 ID，以便程序能够正确地与 LMArena API 通信。

1.  **确保主服务器正在运行**
    `api_server.py` 必须处于运行状态，因为 ID 更新器需要通过它来激活浏览器的捕获功能。

2.  **运行 ID 更新器**
    打开**一个新的终端**，在项目根目录下运行 `id_updater.py` 脚本：
    ```bash
    python id_updater.py
    ```
    *   脚本会提示你选择模式 (DirectChat / Battle)。
    *   选择后，它会通知正在运行的主服务器。

3.  **激活与捕获**
    *   此时，你应该会看到浏览器中 LMArena 页面的标题栏最前面出现了一个准星图标 (🎯)，这表示**ID捕获模式已激活**。
    *   在浏览器中打开一个 LMArena 竞技场的 **目标模型发送给消息的页面**。请注意，如果是Battle页面，请不要查看模型名称，保持匿名状态，并保证当前消息界面的最后一条是目标模型的一个回答；如果是Direct Chat，请保证当前消息界面的最后一条是目标模型的一个回答。
    *   **点击目标模型的回答卡片右上角的重试（Retry）按钮**。
    *   油猴脚本会捕获到 `sessionId` 和 `messageId`，并将其发送给 `id_updater.py`。

4.  **验证结果**
    *   回到你运行 `id_updater.py` 的终端，你会看到它打印出成功捕获到的 ID，并提示已将其写入 `config.jsonc` 文件。
    *   脚本在成功后会自动关闭。现在你的配置已完成！

### 5. 配置你的 OpenAI 客户端
将你的客户端或应用的 OpenAI API 地址指向本地服务器：
*   **API Base URL**: `http://127.0.0.1:5102/v1`
*   **API Key**: 如果 `config.jsonc` 中的 `api_key` 为空，则可随便输入；如果已设置，则必须提供正确的 Key。
*   **Model Name**: 在你的客户端中指定你想使用的模型名称（**必须与 `models.json` 中的名称完全匹配**）。服务器会根据这个名称查找对应的模型ID。

### 6. 开始聊天！ 💬
现在你可以正常使用你的客户端了，所有的请求都会通过本地服务器代理到 LMArena 上！

## 🤔 它是如何工作的？

这个项目由两部分组成：一个本地 Python **FastAPI** 服务器和一个在浏览器中运行的**油猴脚本**。它们通过 **WebSocket** 协同工作。

```mermaid
sequenceDiagram
    participant C as OpenAI 客户端 💻
    participant S as 本地 FastAPI 服务器 🐍
    participant MU as 模型更新脚本 (model_updater.py) 📋
    participant IU as ID 更新脚本 (id_updater.py) 🆔
    participant T as 油猴脚本 🐵 (在 LMArena 页面)
    participant L as LMArena.ai 🌐

    alt 初始化
        T->>+S: (页面加载) 建立 WebSocket 连接
        S-->>-T: 确认连接
    end

    alt 手动更新模型列表 (可选)
        MU->>+S: (用户运行) POST /internal/request_model_update
        S->>T: (WebSocket) 发送 'send_page_source' 指令
        T->>T: 抓取页面 HTML
        T->>S: (HTTP) POST /internal/update_available_models (含HTML)
        S->>S: 解析HTML并保存到 available_models.json
        S-->>-MU: 确认
    end

    alt 手动更新会话ID
        IU->>+S: (用户运行) POST /internal/start_id_capture
        S->>T: (WebSocket) 发送 'activate_id_capture' 指令
        T->>L: (用户点击Retry) 拦截到 fetch 请求
        T->>IU: (HTTP) 发送捕获到的ID
        IU->>IU: 更新 config.jsonc
        IU-->>-T: 确认
    end

    alt 正常聊天流程
        C->>+S: (用户聊天) /v1/chat/completions 请求
        S->>S: 转换请求为 LMArena 格式 (并从 models.json 获取模型ID)
        S->>T: (WebSocket) 发送包含 request_id 和载荷的消息
        T->>L: (fetch) 发送真实请求到 LMArena API
        L-->>T: (流式)返回模型响应
        T->>S: (WebSocket) 将响应数据块一块块发回
        S-->>-C: (流式) 返回 OpenAI 格式的响应
    end

    alt 正常聊天流程 (包含文生图)
        C->>+S: (用户聊天) /v1/chat/completions 请求
        S->>S: 检查模型名称
        alt 如果是文生图模型 (如 DALL-E)
            S->>S: (并行) 创建 n 个文生图任务
            S->>T: (WebSocket) 发送 n 个包含 request_id 的任务
            T->>L: (fetch) 发送 n 个真实请求
            L-->>T: (流式) 返回图片 URL
            T->>S: (WebSocket) 将 URL 发回
            S->>S: 将 URL 格式化为 Markdown 文本
            S-->>-C: (HTTP) 返回包含 Markdown 图片的聊天响应
        else 如果是普通文本模型
            S->>S: 转换请求为 LMArena 格式
            S->>T: (WebSocket) 发送包含 request_id 和载荷的消息
            T->>L: (fetch) 发送真实请求到 LMArena API
            L-->>T: (流式)返回模型响应
            T->>S: (WebSocket) 将响应数据块一块块发回
            S-->>-C: (流式) 返回 OpenAI 格式的响应
        end
    end
```

1.  **建立连接**: 当你在浏览器中打开 LMArena 页面时，**油猴脚本**会立即与**本地 FastAPI 服务器**建立一个持久的 **WebSocket 连接**。
    > **注意**: 当前架构假定只有一个浏览器标签页在工作。如果打开多个页面，只有最后一个连接会生效。
2.  **接收请求**: **OpenAI 客户端**向本地服务器发送标准的聊天请求，并在请求体中指定 `model` 名称。
3.  **任务分发**: 服务器接收到请求后，会根据 `model` 名称从 `models.json` 查找对应的模型ID，然后将请求转换为 LMArena 需要的格式，并附上一个唯一的请求 ID (`request_id`)，最后通过 WebSocket 将这个任务发送给已连接的油猴脚本。
4.  **执行与响应**: 油猴脚本收到任务后，会直接向 LMArena 的 API 端点发起 `fetch` 请求。当 LMArena 返回流式响应时，油猴脚本会捕获这些数据块，并将它们一块块地通过 WebSocket 发回给本地服务器。
5.  **响应中继**: 服务器根据每块数据附带的 `request_id`，将其放入正确的响应队列中，并实时地将这些数据流式传输回 OpenAI 客户端。

## 📖 API 端点

### 获取模型列表

*   **端点**: `GET /v1/models`
*   **描述**: 返回一个与 OpenAI 兼容的模型列表，该列表从 `models.json` 文件中读取。

### 聊天补全

*   **端点**: `POST /v1/chat/completions`
*   **描述**: 接收标准的 OpenAI 聊天请求，支持流式和非流式响应。

### 图像生成 (已集成)

*   **端点**: `POST /v1/chat/completions`
*   **描述**: 文生图功能现已完全集成到主聊天端点中。要生成图片，只需在请求体中指定一个图像模型（例如 `"model": "dall-e-3"`），然后像发送普通聊天消息一样发送请求即可。服务器会自动识别并处理。
*   **请求示例**:
    ```bash
    curl http://127.0.0.1:5102/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "dall-e-3",
        "messages": [
          {
            "role": "user",
            "content": "A futuristic cityscape at sunset, neon lights, flying cars"
          }
        ],
        "n": 1
      }'
    ```
*   **响应示例 (与普通聊天一致)**:
    ```json
    {
      "id": "img-as-chat-...",
      "object": "chat.completion",
      "created": 1677663338,
      "model": "dall-e-3",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "![A futuristic cityscape at sunset, neon lights, flying cars](https://...)"
          },
          "finish_reason": "stop"
        }
      ],
      "usage": { ... }
    }
    ```

## 📂 文件结构

```
.
├── .gitignore                  # Git 忽略文件
├── api_server.py               # 核心后端服务 (FastAPI) 🐍
├── id_updater.py               # 一键式会话ID更新脚本 🆔
├── model_updater.py              # 手动模型列表更新脚本 📋
├── models.json                 # 核心模型映射表 (需手动维护) 🗺️
├── available_models.json       # 可用模型参考列表 (自动生成) 📄
├── model_endpoint_map.json     # [高级] 模型到专属会话ID的映射表 🎯
├── requirements.txt            # Python 依赖包列表 📦
├── README.md                   # 就是你现在正在看的这个文件 👋
├── config.jsonc                # 全局功能配置文件 ⚙️
├── modules/
│   └── update_script.py        # 自动更新逻辑脚本 🔄
└── TampermonkeyScript/
    └── LMArenaApiBridge.js     # 前端自动化油猴脚本 🐵
```

**享受在 LMArena 的模型世界中自由探索的乐趣吧！** 💖
