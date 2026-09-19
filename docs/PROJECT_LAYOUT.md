# 项目目录说明

- `services/`：运行在 Termux 的 API、上传和转换服务
- `scripts/`：Ubuntu/Operit 上执行的模型转换和投递监听脚本
- `config/`：不含设备私有资源的配置模板
- `tools/converter/`：转换器代码和模板；不包含模型权重
- `tests/`：基准测试和静态检查入口
- `web/`：可选的静态网页资源

设备专属资源建议放在仓库外：

```text
$HOME/tts-arm64/
├── astra-server.dll
├── resources/
└── services copied from this repository
```
