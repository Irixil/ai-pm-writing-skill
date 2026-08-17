# AI 产品经理个人写作 Skill

`ai-pm-personal-writing` 是一套面向 AI 产品经理专业文章与产品思考随笔的个人写作 Skill。它把真实经历、产品材料、事实证据和作者判断组织成一篇有立场、有边界、能够落到产品行动的文章。

当前版本为 `2.3.0`。

## 适合写什么

- AI 产品方法、产品设计与迭代经验
- Agent、RAG、模型评测与大模型应用分析
- AI 行业与产品趋势判断
- 产品案例拆解、项目复盘与转行科普
- 从个人经历、阅读材料或现实分歧进入产品判断的思考随笔
- 已有文章的结构调整、事实核验和深度改稿

它不用于 PRD、管理层汇报、小说、营销软文、普通聊天和纯代码教程。

## 写作特点

- 开头直接进入判断、具体经历或真实矛盾
- 先检查题目、概念边界和隐藏前提，再选择立场
- 区分事实、个人感受、作者推断和当前未知
- 同时考虑用户价值、产品机制、商业条件与风险边界
- 主动处理最强反方，不用虚弱的假想观点陪衬
- 保留真实经历的时间、频率、场景和程度，不扩大成普遍结论
- 把抽象判断落到授权、纠正、撤回、人工接管和验证标准
- 表达专业、自然、克制，不批量制造金句、反问和营销口号

个人观察型产品随笔还会保留一条特殊路径。文章可以先把作者放进问题，再从亲近关系、阅读材料和现实案例逐步走向产品判断，最后回到一个具体的行动或仍未解决的问题。

## 默认协作流程

Skill 默认分四个阶段工作。

1. 讨论文章真正要回答的问题、中心观点、证据、反方和成立条件。
2. 确认标题、读者、章节任务、主要材料和预计篇幅。
3. 按确认的大纲逐章生成和修改。
4. 整合全文，统一术语、来源、结构与个人文风。

如果希望一次性交付，可以明确要求“跳过确认”或“直接写完”。Skill 仍会在内部完成观点和结构检查。

## 安装

将仓库克隆到 Codex 的 Skills 目录。这个仓库当前是私有仓库，克隆时需要使用有权限的 GitHub 账号。

```bash
git clone https://github.com/Irixil/ai-pm-writing-skill.git ~/.codex/skills/ai-pm-personal-writing
```

也可以下载仓库后，把整个目录复制到 `~/.codex/skills/ai-pm-personal-writing`。

## 使用示例

```text
使用 $ai-pm-personal-writing，和我讨论一篇关于 Agent 产品授权边界的文章观点。
```

```text
使用 $ai-pm-personal-writing，把这段真实产品体验整理成一篇个人观察型产品随笔。
```

```text
使用 $ai-pm-personal-writing，直接改完这篇 AI 产品文章，并核对事实、反方和结论边界。
```

## 文章检查器

检查专业文章：

```bash
python3 scripts/check_ai_pm_article.py 稿件.md
```

检查个人观察型产品随笔：

```bash
python3 scripts/check_ai_pm_article.py --mode essay 稿件.md
```

检查器会发现占位符、空泛开场、模型化路标、营销表达、翻案句密度、绝对化断言、短句排队和来源风险。它只负责提示文字形状，最终判断仍需回到材料、观点和具体体裁。

## 目录结构

```text
ai-pm-personal-writing/
├── SKILL.md
├── agents/openai.yaml
├── assets/icon.svg
├── references/
│   ├── article-structure.md
│   ├── evidence.md
│   ├── revision.md
│   └── voice-profile.md
└── scripts/check_ai_pm_article.py
```

- `SKILL.md` 定义任务边界和完整工作流。
- `voice-profile.md` 保存已经确认的长期写作习惯。
- `article-structure.md` 提供不同文章类型的论证结构。
- `evidence.md` 规定事实、引语、产品能力和个人经历的边界。
- `revision.md` 用于全文形成后的系统改稿。
- `check_ai_pm_article.py` 提供可重复执行的成稿检查。

## 许可

MIT License
