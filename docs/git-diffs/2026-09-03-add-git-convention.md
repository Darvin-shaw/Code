# Git Diff 总结：新增提交流程约定

- 日期：2026-09-03
- 分支：main
- 涉及文件：
  - `AGENTS.md`（新增）
  - `docs/git-diffs/2026-09-03-add-git-convention.md`（新增）

## 变更摘要

- 新增 `AGENTS.md`，在仓库层面建立约定：每次推送代码到 GitHub 前，必须检查 `git diff`、将变更总结保存到 `docs/git-diffs/`，再随代码一起提交推送。
- 新建 `docs/git-diffs/` 目录，用于长期保存每次推送的 diff 总结。

## 注意事项

- 该约定对仓库内的所有后续提交（包括文档调整、空提交）生效。
- 本文件即为本次变更的 diff 总结示例。
