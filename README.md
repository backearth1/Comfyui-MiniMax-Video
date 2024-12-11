
## API 参数说明

### Image to Video 节点参数

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| client | MiniMax API 客户端 | MINIMAX_CLIENT | - |
| image | 输入图片 | IMAGE | - |
| prompt | 视频生成提示词 | STRING | "" |
| model | 视频生成模型 | ["video-01", "video-01-live2d"] | "video-01" |
| output_name | 输出文件名 | STRING | "output.mp4" |

## 注意事项

1. 确保你有有效的 MiniMax API 密钥
2. 视频生成可能需要一定时间，请耐心等待
3. 生成的视频文件会保存在 ComfyUI 的输出目录中
4. 建议使用清晰的正面图片作为输入以获得最佳效果

## 常见问题

**Q: 为什么视频生成失败？**
A: 请检查：
- API 密钥是否正确
- 网络连接是否正常
- 输入图片是否符合要求
- 提示词是否适当

**Q: 如何获取最佳效果？**
A: 建议：
- 使用清晰的正面图片
- 编写清晰具体的提示词
- 根据需求选择合适的模型

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的图片转视频功能
- 支持视频预览和保存

## 许可证

MIT License

## 贡献指南

欢迎提交 Issues 和 Pull Requests！

## 致谢

- 感谢 ComfyUI 团队提供优秀的基础框架
- 感谢 MiniMax 提供强大的 API 服务