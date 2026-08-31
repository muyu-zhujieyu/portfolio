# 液压故障演化事件知识图谱与智能问答后台系统

## 完整运行与联调指南

---

## 一、环境要求

| 软件 | 最低版本 | 验证命令 |
|------|----------|----------|
| Python | 3.6+ | `python --version` |
| Node.js | 16+ | `node --version` |
| npm | 8+ | `npm --version` |
| IntelliJ IDEA | 2026.1 | 菜单 → Help → About |

---

## 二、在 IntelliJ IDEA 中打开项目

### 2.1 打开项目

```
1. 启动 IntelliJ IDEA 2026.1
2. 菜单栏 → File → Open
3. 选择 D:\kg0623
4. 点击 OK
5. 等待 IDEA 索引完成（右下角进度条消失）
```

### 2.2 打开内置 Terminal

```
快捷键: Alt + F12
或: 菜单栏 → View → Tool Windows → Terminal
```

### 2.3 Terminal 中应看到

```
D:\kg0623>
```

如果不在项目根目录，执行：
```powershell
cd D:\kg0623
```

---

## 三、后端启动

### 3.1 打开第一个 Terminal（后端）

```
Alt + F12 打开 Terminal
```

### 3.2 创建 Python 虚拟环境（仅首次）

```powershell
cd D:\kg0623\backend
python -m venv venv
```

执行后应出现 `venv` 目录。

### 3.3 激活虚拟环境

```powershell
venv\Scripts\activate
```

成功后 Terminal 提示符前面会出现 `(venv)` 标记：
```
(venv) D:\kg0623\backend>
```

### 3.4 安装 Python 依赖（仅首次或更新后）

```powershell
pip install -r requirements.txt
```

应看到 6 个包安装成功：
```
Successfully installed fastapi-0.83.0 uvicorn-0.16.0 sqlalchemy-1.4.x pydantic-1.x python-jose-3.x python-multipart-0.x
```

### 3.5 初始化数据库（仅首次或数据更新后）

```powershell
python init_db.py
```

预期输出：
```
============================================================
  液压故障知识图谱数据库初始化
============================================================
  [OK] sources: 4 个源文档
  [OK] corpus: 39 条语料
  [OK] event_schema: 6 种事件类型
  [OK] mechanism_templates: 6 个机理模板
  [OK] events: 36 条事件
  [OK] evidence: 36 条证据锚定
  [OK] event_relations: 36 条关系
  [OK] version_logs: 10 条版本记录
  [OK] maintenance_rules: 10 条维修规则
  [OK] metrics: 16 项指标
============================================================
  [OK] Database initialized successfully!
  DB Path: D:\kg0623\backend\kg.db
============================================================
```

数据库文件生成位置：`D:\kg0623\backend\kg.db`

### 3.6 启动后端服务器

```powershell
python main.py
```

或者：
```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

预期输出：
```
============================================================
  Hydraulic Fault KG & Intelligent QA Backend
============================================================
  [OK] Database tables checked
  [OK] Database ready (36 events)
  API docs: http://localhost:8000/docs
  Health check: http://localhost:8000/api/health
============================================================
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 3.7 验证后端是否正常

在浏览器打开：
```
http://localhost:8000/api/health
```

应返回 JSON：
```json
{"status":"healthy","version":"1.0.0","database":"SQLite (kg.db)"}
```

---

## 四、前端启动

### 4.1 打开第二个 Terminal（前端）

在 IntelliJ IDEA 中：
```
快捷键: Ctrl + Shift + T  打开新 Terminal Tab
或点击 Terminal 窗口右上角的 + 号
```

### 4.2 安装 npm 依赖（仅首次）

```powershell
cd D:\kg0623\frontend
npm install
```

应看到约 100 个包安装成功。

### 4.3 启动前端开发服务器

```powershell
npm run dev
```

预期输出：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 4.4 验证前端是否正常

在浏览器打开：
```
http://localhost:5173
```

应自动跳转到登录页面。

---

## 五、所有页面访问地址

| 页面 | URL | 说明 |
|------|-----|------|
| 登录页 | http://localhost:5173/login | 默认自动跳转 |
| 系统首页 | http://localhost:5173/dashboard | 图谱规模/质量概况/快捷入口 |
| KG 构建过程 | http://localhost:5173/build-process | 10 阶段构建流水线 |
| 知识图谱展示 | http://localhost:5173/kg | ECharts 力导向图 |
| 知识图谱问答 | http://localhost:5173/qa | 自然语言问答 |
| 维修方案推荐 | http://localhost:5173/recommend | 智能维修决策 |
| 后台管理 | http://localhost:5173/admin | 6 模块数据管理 |
| 构建质量评价 | http://localhost:5173/metrics | 16 项指标 + 图表 |
| 汇报展示 | http://localhost:5173/report | 科研 PPT 风格 |

**登录说明**：
- 用户名：`admin`
- 密码：`admin123`
- 后端不可用时按下「登录」按钮会自动进入演示模式

---

## 六、关键 API 接口测试

所有接口可直接在浏览器或 Postman 中测试。

### 6.1 基础

```
GET  http://localhost:8000/api/health
```

### 6.2 构建流程

```
GET  http://localhost:8000/api/build/steps      # 获取 9 步定义
POST http://localhost:8000/api/build/run        # 执行构建流水线
GET  http://localhost:8000/api/build/result     # 获取构建结果摘要
GET  http://localhost:8000/api/build/logs       # 获取执行日志
```

### 6.3 知识图谱

```
GET  http://localhost:8000/api/kg                   # 完整图谱
GET  http://localhost:8000/api/kg/nodes             # 仅节点
GET  http://localhost:8000/api/kg/edges             # 仅边
GET  http://localhost:8000/api/kg/event/EVT001      # 事件详情
GET  http://localhost:8000/api/kg/evidence/EVT001   # 事件证据
GET  http://localhost:8000/api/kg/chain/T3          # 模板 T3 事件链
```

### 6.4 问答

```
POST http://localhost:8000/api/qa                   # Body: {"question": "液压缸泄漏怎么维修？"}
GET  http://localhost:8000/api/qa/examples          # 示例问题列表
```

### 6.5 维修推荐

```
POST http://localhost:8000/api/recommend            # Body: {"fault_mode": "LeakageFault", "component": "HydraulicCylinder"}
```

### 6.6 机理校验

```
GET  http://localhost:8000/api/validation/templates    # 所有模板
POST http://localhost:8000/api/validation/check-chain  # Body: {"event_ids": ["EVT001"]}
GET  http://localhost:8000/api/validation/report       # 校验报告
```

### 6.7 后台管理

```
GET  http://localhost:8000/api/admin/events
GET  http://localhost:8000/api/admin/evidence
GET  http://localhost:8000/api/admin/templates
GET  http://localhost:8000/api/admin/version-logs
GET  http://localhost:8000/api/admin/conflicts
```

### 6.8 质量评价

```
GET  http://localhost:8000/api/metrics
```

### 6.9 Swagger 文档

在浏览器打开即可交互式测试所有接口：
```
http://localhost:8000/docs
```

---

## 七、故障排查

### 7.1 后端启动失败

| 现象 | 原因 | 解决 |
|------|------|------|
| `python: command not found` | Python 未安装或未加入 PATH | 安装 Python 3.6+，确保 `python` 命令可用 |
| `No module named 'fastapi'` | 虚拟环境未激活或依赖未安装 | 先执行 `venv\Scripts\activate`，再执行 `pip install -r requirements.txt` |
| `Address already in use` (端口 8000 被占用) | 之前的进程未关闭 | `taskkill /F /IM python.exe` 或在任务管理器中结束 Python 进程 |
| `UnicodeEncodeError: 'gbk' codec` | Windows 终端编码问题 | 在 Terminal 中执行 `chcp 65001` 切换到 UTF-8 |
| `TypeError: unsupported operand type(s) for |` | Python 版本低于 3.10 不支持联合语法 | 确认使用 `venv\Scripts\python --version` 输出 3.6+ |
| `AttributeError: module 'asyncio' has no attribute 'run'` | uvicorn 版本过高 | 执行 `pip install uvicorn==0.16.0` |
| 数据库文件被锁定 | 上次未正常关闭 | `taskkill /F /IM python.exe` 后重新启动 |
| `KeyError: 'answer_type'` | 旧版 Pydantic 校验问题 | API 仍正常返回，前端有离线回退模式 |

### 7.2 前端启动失败

| 现象 | 原因 | 解决 |
|------|------|------|
| `npm: command not found` | Node.js 未安装 | 安装 Node.js 16+ |
| `npm install` 失败 | 网络问题或 npm 源不可用 | 设置镜像: `npm config set registry https://registry.npmmirror.com` |
| `vite: command not found` | node_modules 未安装 | 执行 `npm install` |
| 端口 5173 被占用 | 其他 Vite 实例运行中 | Vite 会自动尝试下一个端口（5174） |
| `TS2345` 编译错误 | TypeScript 类型不匹配 | 检查文件完整性，确保未被意外修改 |
| 页面空白（白屏） | JavaScript 加载失败 | 打开浏览器 F12 → Console 查看报错 |

### 7.3 前端页面空白检查清单

```
1. 打开浏览器开发者工具 (F12) → Console 标签
   → 查看是否有红色报错信息

2. 检查 Network 标签
   → 是否能看到对 http://localhost:8000 的请求？
   → 请求是否返回 200 OK？
   → 如果请求失败，确认后端已启动

3. 检查 Application/Storage 标签
   → localStorage 中是否有 token？
   → 如果没有，访问 /login 页面先登录

4. 尝试手动访问
   → http://localhost:8000/api/health
   → 如果打不开，后端未启动

5. 清除浏览器缓存
   → Ctrl + Shift + Delete → 清除缓存和 Cookie
   → 重新访问 http://localhost:5173/login

6. 前端依赖检查
   → cd D:\kg0623\frontend
   → npm install (重新安装)
   → npm run dev (重新启动)
```

### 7.4 ECharts 图谱不显示

| 现象 | 原因 | 解决 |
|------|------|------|
| 图谱区域空白 | 后端返回数据为空 | 打开 F12 → Network → 找到 `/api/kg` → 查看 Response |
| 图谱区域显示但无节点 | nodes 数组为空 | 检查后端 `kg.db` 中 events 表是否有数据 |
| 图例显示但无连线 | links 数组为空 | 检查 event_relations 表 |
| 点击节点无反应 | 未绑定点击事件 | 刷新页面，等待 ECharts 完全初始化 |
| Console 报 `echarts is not defined` | ECharts 未正确导入 | 检查 `package.json` 中是否包含 `echarts` |
| `Cannot read property 'getAttribute'` | DOM 元素未挂载 | 确保 `ref` 正确绑定且在 `onMounted` 中初始化 |
| 图谱显示但非常小/被裁剪 | CSS 容器高度不够 | 检查 `.chart-container` / `.graph-container` 高度设置 |

**快速验证**：
```javascript
// 在浏览器 Console 中执行
fetch('http://localhost:8000/api/kg')
  .then(r => r.json())
  .then(d => console.log('Nodes:', d.nodes?.length, 'Links:', d.links?.length))
// 应输出: Nodes: 42 Links: 36
```

### 7.5 跨域 (CORS) 问题

如果前端请求后端时浏览器 Console 报错：
```
Access to XMLHttpRequest at 'http://127.0.0.1:8000/api/...' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**检查 FastAPI CORS 配置**：

打开 `D:\kg0623\backend\main.py`，确认有以下配置（已默认配置）：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许所有来源（开发环境）
    allow_credentials=True,
    allow_methods=["*"],          # 允许所有 HTTP 方法
    allow_headers=["*"],          # 允许所有请求头
)
```

如果仍然跨域失败：

1. **方案一：使用 Vite 代理（推荐）**

   前端 `vite.config.ts` 已配置代理，将 `/api` 请求转发到后端：
   ```typescript
   server: {
     proxy: {
       '/api': {
         target: 'http://127.0.0.1:8000',
         changeOrigin: true
       }
     }
   }
   ```

   使用代理后，前端 API 调用应使用相对路径（不加 `http://127.0.0.1:8000`）。

   检查 `src/api/request.ts` 中的 `baseURL`：
   ```typescript
   const request = axios.create({
     baseURL: 'http://127.0.0.1:8000',  // 使用代理时改为 ''（空字符串）
     timeout: 30000
   })
   ```

   如果要使用代理模式：
   - 修改 `baseURL` 为 `''`（空字符串）
   - 重启前端 `npm run dev`

2. **方案二：使用绝对路径（当前默认）**

   当前默认配置 `baseURL: 'http://127.0.0.1:8000'` 配合后端 CORS `allow_origins=["*"]` 可直接跨域访问。

3. **方案三：在浏览器中临时禁用 CORS（仅调试用）**
   ```powershell
   # Chrome 快捷方式目标中添加：
   --disable-web-security --user-data-dir="C:\temp\chrome-dev"
   ```

---

## 八、完整联调检查清单

启动顺序：**先后端，再前端**。

```
□ 1.  IntelliJ IDEA 打开 D:\kg0623
□ 2.  Terminal 1: cd backend
□ 3.  Terminal 1: venv\Scripts\activate
□ 4.  Terminal 1: pip install -r requirements.txt (首次)
□ 5.  Terminal 1: python init_db.py (首次)
□ 6.  Terminal 1: python main.py
□ 7.  浏览器验证: http://localhost:8000/api/health → {"status":"healthy"}
□ 8.  Terminal 2: cd frontend
□ 9.  Terminal 2: npm install (首次)
□ 10. Terminal 2: npm run dev
□ 11. 浏览器验证: http://localhost:5173 → 登录页
□ 12. 登录 (admin / admin123) → 进入 Dashboard
□ 13. 检查 Dashboard 指标卡片是否显示数字
□ 14. 打开 /kg → ECharts 图谱是否显示节点和边
□ 15. 打开 /qa → 输入问题 → 是否返回回答
□ 16. 打开 /build-process → 点击「开始构建」→ 10 阶段是否依次完成
□ 17. 打开 /recommend → 选择 LeakageFault → 是否返回维修方案
□ 18. 打开 /admin → 6 个 Tab 是否显示数据
□ 19. 打开 /metrics → 16 项指标表格 + 柱状图 + 雷达图是否显示
□ 20. 打开 /report → 汇报展示页面是否正常渲染
```

---

## 九、关闭与重启

### 关闭

```
1. 前端 Terminal: Ctrl + C
2. 后端 Terminal: Ctrl + C
3. 关闭 IntelliJ IDEA 或关闭 Terminal Tabs
```

### 下次启动（已初始化过）

```powershell
# Terminal 1 - 后端
cd D:\kg0623\backend
venv\Scripts\activate
python main.py

# Terminal 2 - 前端
cd D:\kg0623\frontend
npm run dev
```

### 完全重置数据库

```powershell
cd D:\kg0623\backend
del kg.db
venv\Scripts\activate
python init_db.py
python main.py
```

---

## 十、端口说明

| 服务 | 端口 | 地址 |
|------|------|------|
| 后端 API | 8000 | http://localhost:8000 |
| 后端文档 | 8000 | http://localhost:8000/docs |
| 前端开发 | 5173 | http://localhost:5173 |
| SQLite | 文件 | D:\kg0623\backend\kg.db |
