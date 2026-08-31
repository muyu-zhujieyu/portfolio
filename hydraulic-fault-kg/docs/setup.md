# 液压故障演化过程的机理约束事件知识图谱与大模型问答系统
# 运行与联调说明

## 开发环境

- IDE：IntelliJ IDEA 2026.1
- 操作系统：Windows 11 Pro for Workstations
- 终端：IntelliJ IDEA 自带 Terminal

---

## 一、后端运行

### 1.1 首次启动

在 IntelliJ IDEA Terminal 中依次执行：

```powershell
# 1. 进入后端目录
cd D:\kg0623\backend

# 2. 创建虚拟环境（仅首次）
python -m venv venv

# 3. 激活虚拟环境
.\venv\Scripts\Activate.ps1
# 如 PowerShell 执行策略受限，先执行：
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. 安装依赖
pip install -r requirements.txt

# 5. 初始化数据库（仅首次）
python init_db.py

# 6. 启动后端
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 1.2 后续启动

```powershell
cd D:\kg0623\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 1.3 启动成功标志

```
============================================================
  液压故障演化事件知识图谱与大模型问答系统
  Hydraulic Fault KG & Intelligent QA Backend
============================================================
[OK] 数据库初始化完成: D:\kg0623\backend\kg.db
     已创建 16 张数据表

  数据库路径: backend/kg.db
  数据表数量: 17
    - sources: 5 行
    - paragraphs: 263 行
    - ...

  API 文档: http://127.0.0.1:8000/docs
  健康检查: http://127.0.0.1:8000/api/health
============================================================
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 二、后端接口检查

### 2.1 健康检查

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/health
```

**预期结果：**
```json
{
    "状态": "正常",
    "系统名称": "液压故障演化过程的机理约束事件知识图谱与大模型问答系统",
    "说明": "后端服务已启动"
}
```

### 2.2 查看公开资料来源

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/sources
```

**预期结果：**
- 返回 `总数: 5`
- 来源列表包含 5 条记录：SRC-MANUAL-001, SRC-PAPER-001, SRC-TEXT-001, SRC-COMP-001, SRC-CASE-001
- 每条记录包含：来源编号、来源类型、标题、作者、年份、出版方、文件路径、公开说明、资料描述

### 2.3 文档解析 + 段落清洗 + 领域过滤

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/sources/filter
```

**预期结果：**
- 状态：成功
- 清洗后段落数：265
- 液压相关段落数：255
- 过滤保留率：约 96.2%

### 2.4 事件抽取与证据锚定

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/extraction/run
```

**预期结果：**
- 状态：成功
- 事件总数：833
- 证据总数：833
- 事件类型统计：故障事件(243) + 状态事件(175) + 检测事件(65) + 维修事件(186) + 传播事件(132) + 证据事件(32)

```powershell
# 查看抽取统计
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/extraction/statistics
```

**预期结果：**
- 锚定率：1.0（100%）
- 事件类型统计含 6 种中文类型
- 部件频次 Top5：液压泵(116)、过滤器(94)、阀芯(84)、冷却器(58)、蓄能器(47)

### 2.5 知识图谱构建

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/graph/build
```

**预期结果：**
- 状态：成功
- 节点总数：92
- 边总数：177
- 事件链总数：6

### 2.6 获取 ECharts 图谱数据

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/kg
```

**预期结果：**
- nodes 数组中节点 name 为中文（如"密封件内泄漏""压力下降"），不是 EVT 编号
- links 数组中 relation_zh 为中文（如"演化为""导致"）
- categories 为 6 种中文图例（故障模式、异常状态、检测方式、维修动作、部件、机理模板）

### 2.7 大模型图谱问答

```powershell
# 提问
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/qa `
  -ContentType "application/json" `
  -Body '{"question":"油液污染可能如何演化为压力波动？"}'
```

**预期结果：**
- 包含：用户问题、中文答案、匹配故障演化链、命中机理模板、支撑证据、推荐维修措施、置信度、答案依据说明、可继续追问的问题、session_id
- 答案依据说明含："本答案基于事件知识图谱、机理模板和证据span生成"
- 中文答案含"大模型只负责组织自然语言表达"

```powershell
# 查看示例问题
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/qa/examples
```

**预期结果：** 返回 8 类问答类型的示例问题

```powershell
# 连续追问（使用返回的 session_id）
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/qa `
  -ContentType "application/json" `
  -Body '{"question":"维修后需要做什么检测？","session_id":"SES-xxxxx"}'
```

### 2.8 维修方案推荐

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/recommend `
  -ContentType "application/json" `
  -Body '{"部件":"液压泵","故障模式":"内泄漏","异常状态列表":["压力下降","流量损失"]}'
```

**预期结果：**
- 优先级分数 > 0.5
- 包含：可能故障、命中机理模板、推荐维修动作(10+条)、注意事项、风险等级、推荐理由、支撑证据、预计停机时间、是否需要人工复核
- 优先级分数公式标注

### 2.9 系统优势分析

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/advantages
```

**预期结果：**
- 6 大优势模块
- 每个模块含：普通大模型不足 + 本系统方法优势
- 对比表格：8 维度 × 2 列

### 2.10 资料导入（可选功能）

```powershell
# 上传 TXT 文件
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/import/upload `
  -Form @{file=Get-Item "D:\kg0623\data\raw_sources\manuals\manual_sample.txt"}

# 上传 CSV 文件
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/import/upload `
  -Form @{file=Get-Item "D:\kg0623\data\raw_sources\path\to\data.csv"}

# 分析文件（用返回的 file_id 替换）
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/import/analyze/UPL-xxxxxxxx

# 查看分析结果
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/import/result/UPL-xxxxxxxx

# 加入知识图谱
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/import/add-to-kg/UPL-xxxxxxxx
```

**预期结果：**
- 上传返回：文件编号、文件类型、保存路径、解析状态"待分析"
- 分析返回：抽取事件、证据span、异常指标（表格）/ 图片解析文本（图片）/ 故障链（文档）
- 加入图谱返回：加入事件数、加入证据数
- 接口说明中明确"可选增量功能"

---

## 三、前端运行

### 3.1 安装与启动

在 IntelliJ IDEA Terminal 中执行：

```powershell
# 1. 进入前端目录
cd D:\kg0623\frontend

# 2. 安装依赖（仅首次）
npm install

# 3. 启动开发服务器
npm run dev
```

**启动成功标志：**
```
  VITE v5.4.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://xxx.xxx.xxx.xxx:5173/
```

### 3.2 页面访问与预期内容

#### http://localhost:5173/login — 登录页
- 登录表单（用户名/密码输入框 + 登录按钮）
- 系统名称标题

#### http://localhost:5173/dashboard — 系统首页 ⭐
- 深蓝渐变标题 Hero：系统全称
- 8 个统计卡片（公开资料/段落/事件/证据/模板/节点/边/问答）
- 6 步主流程可视化：📚公开资料→🔍抽取过滤→⚡事件建模→✅机理校验→📊图谱入库→🤖大模型问答
- ⚠ 黄色说明："资料导入分析是可选增量功能，不是主流程前提"
- 8 个快捷入口卡片（数据源/抽取/图谱/QA[必须]/维修/优势/导入[可选]/管理）

#### http://localhost:5173/sources — 公开资料来源管理 ⭐
- ⚠ 蓝色说明："本系统知识图谱的主数据来源于公开维修手册..."
- 6 个统计卡片：资料总数 + 5 种来源类型各计数
- 10 列表格：来源编号/来源类型/标题/作者/年份/出版方/文件路径/文档类型/公开说明/资料描述
- "解析所有文档"按钮
- 底部说明标注 5 种公开资料来源类型

#### http://localhost:5173/extraction — 抽取过滤过程 ⭐
- ⚠ 说明："本页面展示从公开资料中抽取液压故障知识的全过程"
- 6 步流程可视化（彩色步骤圆点 + 箭头）
- 8 个统计卡片 + 2 个操作按钮
- 3 个数据表格：过滤后段落 / 抽取事件 / 证据 span
- 底部主流程说明

#### http://localhost:5173/build-process — 构建过程
- 11 个阶段卡片（3 列网格），每个含：核心问题/输入/操作/产出/验收标准/结果摘要
- "开始构建"按钮 → 实时日志控制台
- 底部 12 项构建统计

#### http://localhost:5173/kg — 知识图谱展示 ⭐⭐⭐
- ECharts Force 图谱（620px 高度）
- 节点标签全部中文（如"内泄漏""压力下降""油液污染"）
- 图例全部中文（故障模式/异常状态/检测方式/维修动作/部件/机理模板）
- 边标签全部中文（演化为/导致/由检测确认/由维修处理）
- T1-T6 模板筛选按钮
- 右侧详情面板：14 个中文字段 + 证据原文 + 来源追溯
- 底部 6 条中文故障演化链

#### http://localhost:5173/qa — 大模型图谱问答 ⭐⭐⭐（核心必须功能）
- 顶部红色警告："大模型只负责组织语言表达，不直接编造事实"
- 左侧聊天界面（用户/AI 气泡对话）
- 每次回答可折叠展开：匹配故障演化链/命中机理模板/支撑证据原文/推荐维修措施
- 右侧 ECharts 相关子图谱
- 9 个预设问题（覆盖 8 类问答类型）
- 置信度百分比 + 答案依据说明
- 支持 session_id 连续追问 + 新建会话

#### http://localhost:5173/recommend — 维修方案推荐
- 优先级分数公式展示
- 部件/故障模式/异常状态下拉选择器
- 4 个评分卡片 + 推荐理由 Alert
- 竖向步骤展示维修动作
- 可能故障 / 命中机理模板 / 注意事项 / 证据 / 停机时间

#### http://localhost:5173/admin — 后台管理
- 9 个统计卡片（点击跳转对应 Tab）
- 搜索框 + 事件类型筛选 + 版本状态筛选
- 10 个 Tab：数据来源/过滤段落/事件/证据/机理模板/事件关系/版本日志/问答记录/导入文件
- 每个 Tab 的数据表格，字段全部中文

#### http://localhost:5173/metrics — 构建质量评价
- 6 个统计卡片
- 2 个 ECharts 柱状图（基础抽取指标 + 机理证据质量）
- 17 项指标定义表格（分组/名称/定义/期望方向）
- 评价总结说明

#### http://localhost:5173/advantages — 方法优势与难点突破
- 6 大难点对比卡片
- 每卡片：左侧红色"普通大模型不足" + 右侧绿色"本系统方法优势"
- 每个难点附技术实现标签
- 底部核心结论

#### http://localhost:5173/import — 资料导入分析（可选功能）
- ⚠ 顶部黄色 Alert："可选增量功能，不是系统主流程前提"
- 4 步进度条：上传→分析→查看→入图
- 拖拽上传区 + 文件列表表格
- 分析结果 6 个 Tab（事件/证据/故障链/异常指标/维修建议/解析文本）
- ECharts 子图谱展示本次分析生成的故障链
- 底部说明"导入分析不是让大模型生成答案"

#### http://localhost:5173/report — 汇报展示
- 科研 PPT 风格页面
- 深蓝渐变标题栏
- 9 个模块卡片：数据来源/主流程/可选导入/图谱构建/大模型问答/故障链/优劣对比/界面展示/底部横幅

---

## 四、重点检查项

| 序号 | 检查项 | 检查方法 | 通过标准 |
|------|--------|----------|----------|
| 1 | 主流程是否从公开资料抽取建图 | 访问 /sources + /extraction | 页面展示公开资料来源 + 抽取过滤过程 |
| 2 | /sources 展示 5 类公开资料 | 访问 /sources | 表格含维修手册/论文/教材/说明书/案例 |
| 3 | /extraction 展示完整流水线 | 访问 /extraction，点击过滤和抽取 | 6步流程 + 3个数据表格 |
| 4 | /kg 全部中文 | 访问 /kg | 节点/边/图例/详情/链全部中文，无 EVT/Component/FaultEvent |
| 5 | /qa 是大模型图谱问答 | 访问 /qa，输入问题 | 返回含证据/模板/链的回答 |
| 6 | /qa 回答展示证据/模板/链 | 展开回答的折叠面板 | 可看到匹配故障演化链/命中机理模板/支撑证据原文 |
| 7 | /import 定位为可选 | 访问 /import | 顶部黄色 Alert + 进度条 + "可选增量功能"标注 |
| 8 | /advantages 对比普通大模型 | 访问 /advantages | 左(红色不足) + 右(绿色优势)，6个维度 |
| 9 | /report 课题汇报风格 | 访问 /report | 科研PPT风格，白底+深蓝标题+卡片+阴影 |

---

## 五、常见问题排查

### 5.1 后端启动失败

```powershell
# 检查 1: 端口是否被占用
netstat -ano | findstr :8000
# 如果占用，关闭占用进程或换端口

# 检查 2: 虚拟环境是否正确
cd D:\kg0623\backend
.\venv\Scripts\Activate.ps1
pip list | findstr fastapi  # 应显示 fastapi

# 检查 3: 依赖是否完整
pip install -r requirements.txt

# 检查 4: 查看错误详情
python -c "from main import app; print('import OK')"
```

### 5.2 kg.db 未生成

```powershell
cd D:\kg0623\backend
# 删除旧数据库（如存在）
del kg.db

# 重新初始化
.\venv\Scripts\Activate.ps1
python init_db.py

# 验证
python -c "import os; print('kg.db exists:', os.path.exists('kg.db')); print('size:', os.path.getsize('kg.db') if os.path.exists('kg.db') else 0)"
```

### 5.3 前端页面空白

```powershell
# 检查 1: 依赖是否安装
cd D:\kg0623\frontend
npm install

# 检查 2: 是否有构建错误
npx vite build 2>&1 | Select-String "error"

# 检查 3: 开发服务器是否有错误输出
# 查看终端中的 Vite 输出，"error"或"warn"字样

# 检查 4: 浏览器控制台
# 按 F12 打开开发者工具 → Console → 查看红色错误
```

### 5.4 前端请求后端失败

```powershell
# 检查 1: 后端是否已启动
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/health

# 检查 2: 前端 API 地址是否正确
# 打开 src/api/request.ts，确认 baseURL 为 http://127.0.0.1:8000

# 检查 3: 浏览器 F12 → Network → 查看请求状态
# 如果显示 CORS 错误 → 检查 main.py 中是否配置了 CORSMiddleware
# 如果显示 500 错误 → 查看后端终端输出
# 如果显示 404 错误 → 检查路由是否正确
```

### 5.5 ECharts 图谱不显示

```powershell
# 检查 1: GET /api/kg 是否有数据
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/kg | ConvertTo-Json -Depth 1
# 应返回 nodes 和 links 数组，各不为空

# 检查 2: 是否已执行图谱构建
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/graph/build

# 检查 3: echarts 库是否正确安装
cd D:\kg0623\frontend
npm list echarts

# 检查 4: 浏览器控制台是否有 echarts 错误
```

### 5.6 图谱中仍出现英文 Component、FaultEvent、detected_by

**这是严重问题！** 图谱要求全部中文。

```powershell
# 检查数据源
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/kg | ConvertTo-Json -Depth 3

# 检查 nodes 数组中的 name 字段是否为中文
# 检查 links 数组中的 relation_zh 字段是否为中文
# 检查 categories 数组中的 name 字段是否为中文

# 如果不是中文 → 说明后端 graph_build_service.py 未正确生成中文标签
# 检查 backend/services/graph_build_service.py 的 NODE_TYPE_CONFIG
# 检查 backend/services/graph_build_service.py 的 LINK_TYPE_CONFIG
# 检查 backend/services/graph_build_service.py 的 _determine_node_label 方法
```

### 5.7 大模型问答没有返回证据

```powershell
# 检查 1: 问答接口返回内容
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/api/qa `
  -ContentType "application/json" `
  -Body '{"question":"内泄漏有什么证据？"}' | ConvertTo-Json -Depth 3

# 检查返回字段:
#   - 支撑证据 字段是否为空数组
#   - 匹配故障演化链 字段是否为空数组
#   - 中文答案 字段是否包含"当前知识图谱中未检索到"

# 如果证据为空:
#   1. 确认 data/extracted/evidence.json 存在
#   2. 确认 evidence 数据表有数据
#   3. 确认 kg_context_service.py 的 _search_evidence 方法正常工作
#   4. 尝试不同的关键词提问
```

### 5.8 /import 上传失败

```powershell
# 检查 1: uploads 目录是否存在
ls D:\kg0623\uploads

# 检查 2: 文件大小是否超过 50MB
# 检查 3: 文件格式是否支持（png/jpg/jpeg/pdf/docx/txt/md/csv/xlsx）
# 检查 4: 后端日志中的错误信息
```

### 5.9 跨域失败（CORS）

FastAPI 的 CORS 中间件已在 main.py 中配置：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],       # 允许所有方法
    allow_headers=["*"],       # 允许所有请求头
)
```

如果仍然跨域失败：
1. 确认 main.py 中有上述 CORSMiddleware 配置
2. 确认前端 dev server 地址是 http://localhost:5173
3. 确认前端 API 请求地址是 http://127.0.0.1:8000
4. 浏览器 F12 → Network → 查看请求的 Response Headers 是否包含 `Access-Control-Allow-Origin`

---

## 六、完整联调流程

### 步骤 1：启动后端

```powershell
cd D:\kg0623\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

确认看到：
```
  API 文档: http://127.0.0.1:8000/docs
  健康检查: http://127.0.0.1:8000/api/health
```

### 步骤 2：启动前端

```powershell
cd D:\kg0623\frontend
npm run dev
```

确认看到：
```
  ➜  Local:   http://localhost:5173/
```

### 步骤 3：验证主流程

1. 打开 http://localhost:5173/dashboard — 确认统计数字正确
2. 打开 http://localhost:5173/sources — 确认5条来源
3. 打开 http://localhost:5173/extraction — 点击"领域过滤"和"事件抽取"
4. 打开 http://localhost:5173/kg — 确认中文图谱
5. 打开 http://localhost:5173/qa — 提问并确认回答含证据
6. 打开 http://localhost:5173/recommend — 选择故障获得推荐

### 步骤 4：验证可选功能

7. 打开 http://localhost:5173/import — 上传文件并分析
8. 确认页面标注"可选增量功能"

### 步骤 5：验证管理功能

9. 打开 http://localhost:5173/admin — 切换所有Tab确认数据
10. 打开 http://localhost:5173/report — 确认汇报展示页

---

## 七、项目文件清单

### 后端 (backend/)

```
backend/
├── main.py                          # FastAPI 入口
├── database.py                      # SQLite 连接管理
├── init_db.py                       # 数据库初始化
├── schemas.py                       # Pydantic 模型
├── requirements.txt                 # Python 依赖
├── kg.db                            # SQLite 数据库（自动生成）
├── routers/
│   ├── source_router.py             # 来源资料
│   ├── extraction_router.py         # 事件抽取
│   ├── build_router.py              # 构建流程
│   ├── graph_router.py              # 知识图谱
│   ├── qa_router.py                 # 图谱问答
│   ├── llm_router.py                # 大模型管理
│   ├── recommend_router.py          # 维修推荐
│   ├── admin_router.py              # 后台管理
│   ├── metrics_router.py            # 质量评价
│   ├── advantage_router.py          # 系统优势
│   └── import_router.py             # 资料导入
└── services/
    ├── source_reader_service.py     # 文档解析
    ├── text_clean_service.py        # 文本清洗
    ├── domain_filter_service.py     # 领域过滤
    ├── event_extract_service.py     # 事件抽取
    ├── evidence_anchor_service.py   # 证据锚定
    ├── mechanism_validation_service.py  # 机理校验
    ├── fusion_service.py            # 事件融合
    ├── graph_build_service.py       # 图谱构建
    ├── kg_context_service.py        # 图谱上下文
    ├── llm_provider.py              # 大模型提供者
    ├── qa_service.py                # 问答服务
    ├── recommend_service.py         # 维修推荐
    ├── metrics_service.py           # 质量评价
    ├── advantage_service.py         # 优势分析
    └── import_service.py            # 导入服务
```

### 前端 (frontend/)

```
frontend/
├── package.json
├── vite.config.ts
├── index.html
├── tsconfig.json
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router/index.ts
│   ├── api/
│   │   ├── request.ts               # Axios 封装
│   │   └── kgApi.ts                 # API 函数
│   ├── layout/
│   │   └── MainLayout.vue           # 主导航布局
│   ├── styles/index.css
│   └── views/
│       ├── LoginView.vue
│       ├── DashboardView.vue        # 系统首页
│       ├── SourceManageView.vue     # 来源管理
│       ├── ExtractionView.vue       # 抽取过滤
│       ├── BuildProcessView.vue     # 构建过程
│       ├── KnowledgeGraphView.vue   # 图谱展示
│       ├── KGQAView.vue             # 图谱问答
│       ├── RecommendationView.vue   # 维修推荐
│       ├── AdminView.vue            # 后台管理
│       ├── MetricsView.vue          # 质量评价
│       ├── AdvantagesView.vue       # 方法优势
│       ├── ImportAnalyzeView.vue    # 资料导入
│       └── ReportView.vue           # 汇报展示
```

---

*文档版本: 1.0 | 更新日期: 2026-06-24*
