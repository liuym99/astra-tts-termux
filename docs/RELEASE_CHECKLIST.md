# 发布前检查清单

- [ ] 删除模型权重、参考音频和个人音色文件
- [ ] 删除日志、缓存、任务结果和设备绝对路径
- [ ] 检查第三方模型、词典、转换器和前端资源许可证
- [ ] 用全新目录验证安装说明
- [ ] `python3 -m py_compile services/*.py`
- [ ] `bash -n scripts/*.sh tests/*.sh`
- [ ] 检查 README 中的端口、环境变量和 API 示例
- [ ] 不提交 `.env`、密码、Token 或 SSH 私钥
- [ ] 建议使用 GitHub Secret Scanning 和 Dependabot
