# Skill 模板说明

把“证据链决策”复用为其他领域 Skill 的最小步骤：

1. **复制结构**：参考 `skills/evidence-decision/`（SKILL.md + config/schema.yaml + examples.md）。
2. **换领域名词**：修改 description 与正文中的场景词（质量决策 → 政策匹配/信贷尽调/诊疗路径）。
3. **换证据源**：
   - 文本知识库（政策库/研报库/指南库）→ `search-knowledge-base`；
   - 表格台账 → `analyze-text-file`/台账摘要；
   - 图谱（政策条件-企业属性）→ `graph_search`。
4. **保留不可妥协的工作流**：检索→推理→反证→校验→带引用输出。
5. **改写 examples**：用领域真实/合成样例替代制造样例。

验收口径：任一输出可被第三方按证据反查；无证据不断言；更新领域语料后仍可回放 Golden。
