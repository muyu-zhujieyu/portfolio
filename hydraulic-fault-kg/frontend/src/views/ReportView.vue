<template>
  <div class="report-root">
    <!-- ═══════ 顶部标题栏 ═══════ -->
    <div class="title-bar">
      <div class="title-tag">二、课题研究进展</div>
      <div class="title-main">任务四：智能决策维护方法与健康管理运维平台</div>
      <div class="title-sub">液压故障演化过程的机理约束事件知识图谱与大模型问答系统</div>
    </div>

    <!-- ═══════ 阶段进展说明 ═══════ -->
    <div class="intro-box">
      <p>针对液压系统服役阶段故障演化知识组织与维修决策需求，系统以<strong>公开维修手册、相关论文、教材、液压元件说明书和公开故障案例</strong>为主要数据来源，经过文档解析、段落清洗、液压领域过滤、事件抽取、证据锚定、机理模板校验和增量融合，构建<strong>机理约束事件知识图谱</strong>；同时引入<strong>大模型图谱问答模块</strong>，使用户能够围绕故障链、证据来源、机理模板和维修措施进行连续追问。系统还提供资料、图片和数据导入分析作为<strong>补充功能</strong>，用于新增资料的增量入图谱。</p>
    </div>

    <!-- ═══════ 第一行：数据来源 + 主流程 ═══════ -->
    <div class="row-2col">
      <!-- 主要数据来源 -->
      <div class="card-panel">
        <div class="card-title"><span class="num-badge">1</span> 主要数据来源</div>
        <div class="card-body">
          <div class="source-grid">
            <div class="source-item" v-for="s in sources" :key="s.name">
              <div class="source-icon">{{ s.icon }}</div>
              <div class="source-name">{{ s.name }}</div>
              <div class="source-note">{{ s.note }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 主流程模块 -->
      <div class="card-panel">
        <div class="card-title"><span class="num-badge">2</span> 主流程模块</div>
        <div class="card-body">
          <div class="pipeline-horiz">
            <div class="pipe-step" v-for="(s,i) in mainPipeline" :key="i">
              <div class="pipe-dot" :style="{ background: s.color }"></div>
              <div class="pipe-label">{{ s.label }}</div>
            </div>
          </div>
          <div class="pipe-arrow-row">
            <span v-for="i in 7" :key="i" class="pipe-arrow">→</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 第二行：可选导入 + 图谱构建 ═══════ -->
    <div class="row-2col">
      <!-- 可选导入分析 -->
      <div class="card-panel dashed-border">
        <div class="card-title">
          <span class="num-badge optional">3</span> 可选导入分析模块
          <el-tag type="info" size="small" style="margin-left:8px">可选增量功能</el-tag>
        </div>
        <div class="card-body">
          <div class="import-flow">
            <div class="import-step" v-for="s in importSteps" :key="s.label">
              <div class="is-icon">{{ s.icon }}</div>
              <div class="is-label">{{ s.label }}</div>
            </div>
          </div>
          <p class="optional-note">此模块为可选增量功能，主图谱仍以公开资料抽取构建为主。系统的主流程不依赖此功能。</p>
        </div>
      </div>

      <!-- 图谱构建模块 -->
      <div class="card-panel">
        <div class="card-title"><span class="num-badge">4</span> 图谱构建模块</div>
        <div class="card-body">
          <div class="kg-build-steps">
            <div class="kbs" v-for="s in kgBuildSteps" :key="s">{{ s }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 第三行：大模型问答 ═══════ -->
    <div class="card-panel highlight-panel">
      <div class="card-title">
        <span class="num-badge core">5</span> 大模型图谱问答（核心功能）
        <el-tag type="danger" size="small" style="margin-left:8px">必须功能</el-tag>
      </div>
      <div class="card-body">
        <div class="qa-types">
          <div class="qa-type" v-for="qt in qaTypes" :key="qt.label">
            <div class="qt-icon">{{ qt.icon }}</div>
            <div class="qt-label">{{ qt.label }}</div>
            <div class="qt-desc">{{ qt.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 第四行：中文故障链图谱 ═══════ -->
    <div class="card-panel">
      <div class="card-title"><span class="num-badge">6</span> 中文知识图谱——典型故障演化链</div>
      <div class="card-body">
        <div class="chains-display">
          <div class="chain-row" v-for="ch in faultChains" :key="ch.id">
            <div class="chain-tag" :style="{ background: ch.color }">{{ ch.id }}</div>
            <div class="chain-steps">
              <template v-for="(step, si) in ch.steps" :key="si">
                <span class="cs-node" :style="{ borderColor: step.color, color: step.color }">{{ step.label }}</span>
                <span class="cs-arrow" v-if="si < ch.steps.length - 1">→</span>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 第五行：方法优势 ═══════ -->
    <div class="row-2col">
      <div class="card-panel weak-panel">
        <div class="card-title"><span class="num-badge">7</span> 普通大模型难以做到</div>
        <div class="card-body">
          <div class="compare-list">
            <div class="cl-item fail" v-for="w in weaknesses" :key="w">
              <span class="cl-mark">✗</span> {{ w }}
            </div>
          </div>
        </div>
      </div>
      <div class="card-panel strong-panel">
        <div class="card-title"><span class="num-badge">8</span> 本系统能够做到</div>
        <div class="card-body">
          <div class="compare-list">
            <div class="cl-item pass" v-for="s in strengths" :key="s">
              <span class="cl-mark">✓</span> {{ s }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 第六行：界面展示 ═══════ -->
    <div class="card-panel">
      <div class="card-title"><span class="num-badge">9</span> 系统界面模块</div>
      <div class="card-body">
        <div class="iface-grid">
          <div class="iface-card" v-for="ifc in interfaces" :key="ifc.name">
            <div class="ifc-icon">{{ ifc.icon }}</div>
            <div class="ifc-name">{{ ifc.name }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ 底部横幅 ═══════ -->
    <div class="bottom-banner">
      搭建面向公开资料抽取的液压故障演化事件知识图谱与大模型问答系统，<br/>
      实现数据抽取过滤、图谱构建、机理校验、证据追溯、维修推荐与智能问答功能
    </div>
  </div>
</template>

<script setup lang="ts">
const sources = [
  { icon: '📖', name: '公开维修手册', note: '液压系统日常维护与故障检修手册' },
  { icon: '📄', name: '相关论文', note: '基于油液分析与振动监测的故障诊断研究' },
  { icon: '📚', name: '液压教材', note: '液压传动与控制（第三版）' },
  { icon: '📋', name: '元件说明书', note: 'A11VO恒压变量柱塞泵技术说明书' },
  { icon: '📝', name: '公开故障案例', note: '某型液压机压力不足与油温过高案例' },
]

const mainPipeline = [
  { label: '资料整理', color: '#1ABC9C' },
  { label: '文档解析', color: '#3498DB' },
  { label: '段落清洗', color: '#3498DB' },
  { label: '领域过滤', color: '#F39C12' },
  { label: '事件抽取', color: '#E74C3C' },
  { label: '证据锚定', color: '#E74C3C' },
  { label: '机理校验', color: '#9B59B6' },
  { label: '图谱入库', color: '#2ECC71' },
]

const importSteps = [
  { icon: '📷', label: '图片' },
  { icon: '📄', label: 'PDF' },
  { icon: '📝', label: 'DOCX' },
  { icon: '📊', label: 'CSV' },
  { icon: '📈', label: 'XLSX' },
  { icon: '🔍', label: '点击分析' },
  { icon: '✅', label: '查看结果' },
  { icon: '📥', label: '选择入图谱' },
]

const kgBuildSteps = ['事件本体设计', '机理模板校验', '事件归一融合', '图谱入库', '中文图谱展示']

const qaTypes = [
  { icon: '🔗', label: '事件链问答', desc: '油液污染如何演化为压力波动？' },
  { icon: '🔍', label: '证据追溯问答', desc: '这个故障结论有什么证据支撑？' },
  { icon: '🔧', label: '维修建议问答', desc: '阀芯卡滞应该如何处理？' },
  { icon: '⚙', label: '机理解释问答', desc: '冷却器效率下降为什么导致泄漏？' },
  { icon: '💬', label: '连续追问', desc: '支持session_id上下文连续追问' },
]

const faultChains = [
  { id: 'T1', color: '#E74C3C', steps: [
      { label: '内泄漏', color: '#E74C3C' }, { label: '流量损失', color: '#F39C12' },
      { label: '压力下降', color: '#F39C12' }, { label: '执行机构动作迟缓', color: '#F39C12' }] },
  { id: 'T2', color: '#F39C12', steps: [
      { label: '过滤器堵塞', color: '#E74C3C' }, { label: '吸入口阻力增大', color: '#F39C12' },
      { label: '气蚀', color: '#E74C3C' }, { label: '噪声增大', color: '#F39C12' }] },
  { id: 'T5', color: '#1ABC9C', steps: [
      { label: '油液污染', color: '#E74C3C' }, { label: '阀芯卡滞', color: '#E74C3C' },
      { label: '流量控制异常', color: '#F39C12' }, { label: '压力波动', color: '#F39C12' }] },
]

const weaknesses = ['无证据追溯 — 无法说明答案来源', '无机理校验 — 可能生成不符合物理规律的故障链', '无图谱入库 — 知识不持久化', '难处理版本冲突 — 无法区分新旧事实', '难解释回答依据 — 回答可能无据可查']
const strengths = ['证据span锚定 — 追溯至source_id/段落编号/原文片段', '机理模板校验 — T1-T6六条液压机理模板约束', '事件知识图谱入库 — 92节点+177边SQLite持久化', '双时态增量融合 — 版本日志+冲突标记+历史追溯', '图谱问答可解释 — 展示事件链+模板+证据+置信度', '可选新增资料增量入图谱 — 上传→分析→选择入图']

const interfaces = [
  { icon: '🔑', name: '登录页面' }, { icon: '📚', name: '数据源管理页' }, { icon: '🔍', name: '抽取过滤过程页' },
  { icon: '📊', name: '知识图谱展示页' }, { icon: '🤖', name: '大模型图谱问答页' }, { icon: '🔧', name: '维修推荐页' },
  { icon: '⚙', name: '后台管理页' }, { icon: '🏆', name: '方法优势页' }, { icon: '📤', name: '可选导入分析页' },
  { icon: '📊', name: '伺服阀样本分析页' },
]
</script>

<style scoped>
/* ═══════ 全局 ═══════ */
.report-root {
  max-width: 1280px; margin: 0 auto; padding: 20px;
  background: #fff; font-family: 'Microsoft YaHei', sans-serif;
  min-height: 100vh;
}

/* ═══════ 标题栏 ═══════ */
.title-bar {
  background: linear-gradient(135deg, #1a3a5c 0%, #304156 100%);
  padding: 28px 36px; border-radius: 12px; color: #fff; margin-bottom: 20px;
}
.title-tag { font-size: 14px; opacity: 0.8; }
.title-main { font-size: 22px; font-weight: 700; margin: 8px 0; }
.title-sub { font-size: 15px; opacity: 0.9; }

/* ═══════ 说明框 ═══════ */
.intro-box {
  background: #f0f5fa; padding: 14px 20px; border-radius: 8px;
  border-left: 4px solid #1a3a5c; margin-bottom: 20px;
  font-size: 13px; line-height: 1.8; color: #303133;
}
.intro-box strong { color: #E74C3C; }

/* ═══════ 两列布局 ═══════ */
.row-2col {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;
}

/* ═══════ 卡片面板 ═══════ */
.card-panel {
  background: #fff; border-radius: 10px; box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  padding: 16px 20px; border: 1px solid #e4e7ed;
}
.card-panel.highlight-panel { border: 2px solid #E74C3C; background: #fff5f5; }
.card-panel.dashed-border { border: 2px dashed #909399; }
.card-title { font-size: 15px; font-weight: 700; color: #1a3a5c; margin-bottom: 12px; display: flex; align-items: center; }
.num-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%; background: #1a3a5c;
  color: #fff; font-size: 13px; font-weight: 700; margin-right: 8px; flex-shrink: 0;
}
.num-badge.core { background: #E74C3C; }
.num-badge.optional { background: #909399; }
.card-body { font-size: 12px; }

/* ═══════ 数据来源 ═══════ */
.source-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.source-item { text-align: center; padding: 10px; background: #f5f7fa; border-radius: 8px; }
.source-icon { font-size: 28px; }
.source-name { font-size: 13px; font-weight: 600; color: #303133; margin: 4px 0; }
.source-note { font-size: 11px; color: #909399; }

/* ═══════ 主流程 ═══════ */
.pipeline-horiz { display: flex; justify-content: space-between; gap: 2px; }
.pipe-step { text-align: center; flex: 1; }
.pipe-dot { width: 12px; height: 12px; border-radius: 50%; margin: 0 auto 4px auto; }
.pipe-label { font-size: 10px; color: #606266; }
.pipe-arrow-row { display: flex; justify-content: space-between; padding: 0 20px; margin-top: 4px; }
.pipe-arrow { color: #409EFF; font-weight: 700; font-size: 14px; }

/* ═══════ 导入流程 ═══════ */
.import-flow { display: flex; justify-content: space-between; gap: 4px; margin-bottom: 8px; }
.import-step { text-align: center; flex: 1; padding: 6px; background: #f5f7fa; border-radius: 6px; }
.is-icon { font-size: 20px; }
.is-label { font-size: 10px; color: #606266; margin-top: 2px; }
.optional-note { font-size: 11px; color: #909399; text-align: center; margin-top: 8px; }

/* ═══════ 图谱构建 ═══════ */
.kg-build-steps { display: flex; justify-content: space-between; gap: 8px; }
.kbs { flex: 1; text-align: center; padding: 12px 8px; background: #f5f7fa; border-radius: 8px; font-size: 13px; font-weight: 600; color: #1a3a5c; }

/* ═══════ 问答类型 ═══════ */
.qa-types { display: flex; justify-content: space-between; gap: 8px; }
.qa-type { flex: 1; text-align: center; padding: 14px 8px; background: #fff; border-radius: 8px; border: 1px solid #fde2e2; }
.qt-icon { font-size: 28px; }
.qt-label { font-size: 13px; font-weight: 700; color: #E74C3C; margin: 6px 0 4px 0; }
.qt-desc { font-size: 11px; color: #909399; }

/* ═══════ 故障链 ═══════ */
.chains-display { display: flex; flex-direction: column; gap: 14px; }
.chain-row { display: flex; align-items: center; gap: 10px; }
.chain-tag { padding: 6px 12px; border-radius: 6px; color: #fff; font-weight: 700; font-size: 13px; flex-shrink: 0; }
.chain-steps { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.cs-node { padding: 5px 12px; border: 2px solid; border-radius: 20px; font-size: 12px; font-weight: 600; background: #fff; }
.cs-arrow { color: #E74C3C; font-weight: 700; font-size: 16px; }

/* ═══════ 方法对比 ═══════ */
.weak-panel { border-left: 4px solid #F56C6C; }
.strong-panel { border-left: 4px solid #67C23A; }
.compare-list { display: flex; flex-direction: column; gap: 6px; }
.cl-item { font-size: 12px; padding: 6px 10px; border-radius: 4px; }
.cl-item.fail { background: #fef0f0; color: #F56C6C; }
.cl-item.pass { background: #f0f9eb; color: #67C23A; }
.cl-mark { font-weight: 700; margin-right: 4px; }

/* ═══════ 界面展示 ═══════ */
.iface-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.iface-card { text-align: center; padding: 14px 8px; background: #f5f7fa; border-radius: 8px; border: 1px dashed #d9e1e8; }
.ifc-icon { font-size: 28px; }
.ifc-name { font-size: 12px; color: #303133; margin-top: 4px; font-weight: 600; }

/* ═══════ 底部横幅 ═══════ */
.bottom-banner {
  background: linear-gradient(135deg, #1a3a5c 0%, #409EFF 100%);
  padding: 20px 36px; border-radius: 10px; color: #fff;
  text-align: center; font-size: 15px; line-height: 1.8; margin-top: 20px; font-weight: 600;
}
</style>
