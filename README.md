# AstraTTS Android/Termux Integration

这是一个面向 Android/Termux 的 AstraTTS 部署、API 代理、音色模型转换和投递式管理工具集。

> 本仓库主要包含集成代码、脚本、配置模板和文档，并随仓库发布已获许可的  模型及其示例参考音频。其他模型权重、第三方运行时、个人数据和编译产物不随仓库发布。

## 功能

- Python API 代理：`services/api-server.py`
  - `POST /v1/speech`
  - 支持普通和流式请求
  - 有界并发队列，默认一次只运行一个模型请求
  - 默认 `speed=1.4`，可通过环境变量覆盖
- 模型上传服务：`services/upload-server.py`
- 转换任务 API：`services/converter-api.py`
- Ubuntu/Operit 模型转换脚本
- `inbox/<avatarId>/` 投递式音色转换监听器
- 基准测试脚本和部署配置模板

## 架构

```text
客户端/Web
   │
   ├── 5125  Python API 代理 ──┐
   ├── 5124  模型/参考音频上传   ├── AstraTTS 主服务 5123
   └── 5126  转换任务 API ──────┘
```


## 快速开始（Termux）

1. 安装 Python、.NET 运行时和 AstraTTS 主程序依赖。
2. 将本仓库中的 `config/config.yaml.example` 复制为实际配置，并把路径改成设备上的实际路径。
3. 将 AstraTTS 主程序及所需资源放到 `$HOME/tts-arm64`。
4. 将服务脚本复制到运行目录：

```bash
cp services/api-server.py services/upload-server.py services/converter-api.py "$HOME/tts-arm64/"
```

5. 设置环境变量并启动：

```bash
export ASTRA_TTS_HOME="$HOME/tts-arm64"
export ASTRA_API_CONCURRENCY=1
export ASTRA_DEFAULT_SPEED=1.4
python3 "$ASTRA_TTS_HOME/api-server.py" &
python3 "$ASTRA_TTS_HOME/upload-server.py" &
python3 "$ASTRA_TTS_HOME/converter-api.py" &
cd "$ASTRA_TTS_HOME"
dotnet ./astra-server.dll --urls http://0.0.0.0:5123
```

实际生产部署建议使用 tmux、Termux:Boot 或其他进程守护方式，并自行限制服务监听地址和网络访问范围。

## API 示例

普通合成：

```bash
curl -X POST http://127.0.0.1:5125/v1/speech \
  -H 'Content-Type: application/json' \
  -d '{"text":"你好，这是测试。","avatarId":"cyrene","referenceId":"default","speed":1.4}' \
  -o output.wav
```

流式合成：

```bash
curl -N -X POST http://127.0.0.1:5125/v1/speech \
  -H 'Content-Type: application/json' \
  -d '{"text":"你好，这是流式测试。","stream":true,"avatarId":"cyrene","referenceId":"default","speed":1.4}' \
  -o output.pcm
```

## 新音色转换

### 单次转换

```bash
bash scripts/convert-and-import.sh <avatarId> <file.ckpt> <file.pth>
```

### 投递式转换

目录结构：

```text
\/root/astra-convert/inbox/alice/
├── model.ckpt
└── model.pth
```

启动监听器：

```bash
bash scripts/watch-inbox.sh
```

监听器只处理每个音色目录中恰好一个 `.ckpt` 和一个 `.pth` 的目录，并使用 `.processing`、`.done`、`.error` 标记状态。

转换器依赖其模板、Python 依赖和上游模型转换许可；这些内容不代表模型权重本身的再分发许可。

## 性能说明

当前默认模型池和 API 并发均为 1，原因是 Android ARM64 设备上的模型内存占用较大。并发提高主要提升吞吐，不保证降低单次首次合成时间。重复请求缓存不属于当前默认实现，仓库中的 API 代理是直接转发版本。

## 测试

```bash
python3 -m py_compile services/*.py
bash -n scripts/*.sh tests/*.sh
bash tests/benchmark-tts.sh 2 benchmark
```

基准测试需要本地 5125 服务和可用音色，不会自动下载模型。

## 许可证

本仓库脚本和文档采用 MIT License，见 `LICENSE`。AstraTTS、ONNX Runtime、模型、词典、音色和参考音频分别受其各自许可证约束；请在发布前补充实际依赖的许可证和来源说明。
