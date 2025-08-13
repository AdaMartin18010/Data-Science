# 贡献指南

## 基本规范

- 文档使用 Markdown，遵循统一模板与编号结构
- 数学公式使用 LaTeX，代码示例需可运行且有简要注释
- 坚持交叉引用与本地相对路径

## 分支与提交

- 建议使用 feature/* 分支，提交信息简洁明确
- 大改动需附带更新的导航与交叉引用

## 翻译与国际化

- 语言目录：`Analysis/zh-CN` 与 `Analysis/en-US`
- 翻译优先：核心概念、代码与安全相关
- 元数据需包含 language、version、translation_status

## 质量检查

- 本地执行：`python Analysis/quality_checker.py Analysis/ --format json --output Analysis/quality_report_latest.json`
- CI 自动生成质量报告（见 `.github/workflows/quality-check.yml`）

## 基准与实验

- 一键运行：`scripts/run_bench.sh` 或 `scripts/run_bench.ps1`
- 生成结果：`bench_stream.json`、`bench_infer.json`
- 汇总：`python benchmarks/aggregate_results.py bench.csv bench_stream.json bench_infer.json`

## 提交前检查

- 标题层级连续、无跳跃
- 代码与公式通过渲染预览
- 新增文档已加入索引与交叉引用
