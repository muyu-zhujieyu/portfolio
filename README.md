# muyu-zhujieyu · AI 产品作品集

作品集目前包含四个并列案例：轻量习惯养成、工业知识图谱、中文菜谱 RAG，以及 G1 人形机器人 SLAM 导航与安全运动平台。重点呈现我如何从需求分析出发，将产品逻辑转化为可运行原型或全栈系统，并通过数据边界、证据追溯和验收标准提高交付可靠性。

**[打开在线作品集总览](https://muyu-zhujieyu.github.io/portfolio/)**

## 推荐浏览路线

| 项目 | 先看什么 | 如何体验 |
| --- | --- | --- |
| 01 · 轻习惯 LiteHabit | [项目说明](litehabit/README.md) · [产品需求文档](litehabit/LiteHabit_PRD_v2.0.docx) | [打开交互 Demo](https://muyu-zhujieyu.github.io/portfolio/litehabit/)，无需安装 |
| 02 · 液压伺服阀故障知识图谱 | [项目说明](hydraulic-fault-kg/README.md) | [打开原 Vue 管理端预览](https://muyu-zhujieyu.github.io/portfolio/hydraulic-fault-kg/)；完整数据与 AI 功能按 README 启动前后端 |
| 03 · 尝尝咸淡 Recipe RAG | [项目说明](recipe-rag/README.md) · [架构说明](recipe-rag/docs/architecture.md) | [打开浏览器 Demo](https://muyu-zhujieyu.github.io/portfolio/recipe-rag/)，无需密钥；完整体验按 README 启动 CLI |
| 04 · G1 SLAM 导航与安全运动平台 | [项目说明](g1-robotics/README.md) · [产品需求文档](g1-robotics/docs/PRD.md) | [打开公开仿真](https://muyu-zhujieyu.github.io/portfolio/g1-robotics/)，无需机器人 |

## 01 · 轻习惯 LiteHabit

一款强调「轻量开始、即时反馈、看见积累」的本地优先习惯追踪 Web App。用户可以从预设或自定义习惯开始，完成每日打卡，并通过连续天数、7 天趋势、28 天热力图和阶段成就观察长期积累。

产品设计重点是降低启动成本、强化即时反馈，同时避免用过强的数据压力打断习惯形成。所有记录默认保存在浏览器本地，支持 JSON 备份和 CSV 导出，无需账号或数据上传。

## 02 · 液压伺服阀故障知识图谱与智能维护平台

面向工业维修知识分散、故障链难追溯和通用大模型容易产生无依据结论的问题，将公开维修手册、论文、教材、说明书和故障案例转化为带证据的故障事件知识图谱。

系统覆盖资料清洗、领域过滤、三元组与事件抽取、证据锚定、同义归一、机理模板校验、中文图谱展示、约束问答和维修推荐。核心原则是让模型负责组织表达，关键事实来自知识图谱、证据片段、机理模板与维修规则。

## 03 · 尝尝咸淡 Recipe RAG

面向中文家常菜搜索与推荐场景，将 Markdown 菜谱处理为父子文档结构，并结合 BGE 中文嵌入、FAISS、BM25、RRF 融合排序、元数据过滤和查询路由，支持菜品推荐、食材查询与详细步骤问答。

公开版保留完整核心链路和 6 份自编演示菜谱，同时补齐依赖、环境变量模板和架构说明。模型密钥、向量索引、虚拟环境、原始图片和来源不明确的数据均不进入仓库。

## 04 · G1 SLAM 导航与安全运动平台

基于 G1、MID360、FAST-LIO 与 Nav2 建立实机 SLAM 导航闭环，覆盖三维点云到二维地图、固定起点定位、路径预验证、受限速度桥接和到点/异常安全收口；并延伸到双臂轨迹编辑、FK/IK 与视觉目标触碰的安全预演。

公开仿真用合成地图展示启动前安全确认、连续目标导航、STOP 与 IK fail-closed 逻辑，不包含现场网络、真实点云、地图、模型权重或真机控制代码。

## 仓库结构

```text
.
├── portfolio/                 # 作品集在线总览页
├── litehabit/                 # 项目 01：轻习惯 Web App
├── hydraulic-fault-kg/        # 项目 02：工业知识图谱全栈平台
├── recipe-rag/                # 项目 03：中文菜谱混合检索 RAG
├── g1-robotics/               # 项目 04：G1 SLAM 导航与安全运动仿真
├── index.html                 # GitHub Pages 入口跳转
└── README.md                  # 仓库总览
```

## 仓库边界

- LiteHabit 仅使用浏览器本地存储，不上传个人习惯数据。
- 工业知识图谱项目只公开源码、词典、规则和必要的派生示例。
- 菜谱 RAG 只公开核心代码与自编演示数据，不提交向量索引和原始素材库。
- G1 机器人项目不公开现场账号/IP、真实地图/点云、模型权重、标定文件和可直接驱动真机的控制源码。
- 不公开模型密钥、运行数据库、用户上传文件、虚拟环境和本地构建产物。
- 不公开大体积 DOCX、PPTX、视频、CAD/三维模型或可能受授权限制的资料全文。
- 工业维护建议属于研究与辅助决策展示，正式使用必须由专业人员复核。

## GitHub Pages 发布

本仓库是纯静态多项目作品集，不需要额外构建。GitHub 仓库中选择 **Settings → Pages → Deploy from a branch → main → /(root)** 后保存，即可从以下地址访问：

- 总览：`https://muyu-zhujieyu.github.io/portfolio/`
- 四个项目：分别位于 `/litehabit/`、`/hydraulic-fault-kg/`、`/recipe-rag/`、`/g1-robotics/`

---

© 2026 muyu-zhujieyu · AI 产品作品集
