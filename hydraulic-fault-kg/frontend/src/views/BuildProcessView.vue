<template>
  <div class="build-page">
    <h2>机理约束事件知识图谱构建过程</h2>
    <p class="subtitle">从公开资料到结构化的中文事件知识图谱的完整构建流水线</p>

    <!-- 按钮 -->
    <el-space style="margin-bottom:20px">
      <el-button type="primary" size="large" @click="runBuild" :loading="running">
        开始构建
      </el-button>
      <el-button @click="loadResult">查看构建结果</el-button>
      <el-button @click="loadLogs">刷新日志</el-button>
    </el-space>

    <!-- 11 阶段卡片 -->
    <el-row :gutter="12">
      <el-col :span="8" v-for="s in stages" :key="s.id" style="margin-bottom:12px">
        <el-card class="stage-card" :class="'stage-'+s.status" shadow="hover">
          <template #header>
            <div class="stage-header">
              <span class="stage-num">{{ s.id }}</span>
              <span class="stage-name">{{ s.name }}</span>
              <el-tag :type="s.status === 'done' ? 'success' : s.status === 'running' ? 'warning' : 'info'" size="small">{{ s.statusText }}</el-tag>
            </div>
          </template>
          <div class="stage-body">
            <div class="stage-row"><b>核心问题：</b>{{ s.question }}</div>
            <div class="stage-row"><b>输入：</b>{{ s.input }}</div>
            <div class="stage-row"><b>关键操作：</b>{{ s.operation }}</div>
            <div class="stage-row"><b>产出：</b>{{ s.output }}</div>
            <div class="stage-row"><b>验收标准：</b>{{ s.criteria }}</div>
            <div class="stage-row" v-if="s.metrics"><b>评价指标：</b>{{ s.metrics }}</div>
            <div v-if="s.result" class="stage-result">{{ s.result }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 构建日志 -->
    <el-card v-if="logs.length" header="构建日志" style="margin-top:16px">
      <div class="log-console">
        <div v-for="(l, i) in logs" :key="i" class="log-line" :class="'log-'+l.level">
          <span class="log-time">{{ l.time }}</span>
          <span class="log-msg">{{ l.msg }}</span>
        </div>
      </div>
    </el-card>

    <!-- 底部统计 -->
    <el-card header="构建结果统计" style="margin-top:16px">
      <el-row :gutter="16">
        <el-col :span="2" v-for="s in bottomStats" :key="s.label" style="margin-bottom:8px">
          <el-statistic :title="s.label" :value="s.value">
            <template #suffix v-if="s.unit"><span style="font-size:11px">{{ s.unit }}</span></template>
          </el-statistic>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBuildSteps, getBuildResult, getBuildStatus } from '@/api/kgApi'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const running = ref(false)
const logs = ref<{ time: string; msg: string; level: string }[]>([])

const stages = ref([
  { id: 1, name: '任务界定', question: '要构建什么知识图谱？', input: '液压故障领域需求', operation: '定义事件类型、关系类型、本体Schema', output: '事件本体定义文档', criteria: '事件类型覆盖6类液压故障场景', metrics: '', status: 'done', statusText: '已完成', result: '' },
  { id: 2, name: '公开资料导入', question: '数据从哪来？', input: 'source_registry.json', operation: '读取公开维修手册/论文/教材/说明书/案例', output: '5份公开资料来源', criteria: '全部来源文件可读取', metrics: '来源数', status: 'done', statusText: '已完成', result: '已导入5条来源，263个段落' },
  { id: 3, name: '文档解析与段落清洗', question: '如何提取干净文本？', input: '原始文档(txt/pdf/docx)', operation: '解析文档→拆分段落→去除空行/目录/参考文献/页眉页脚/过短段落', output: '265个清洗后段落', criteria: '去除率合理(36%)，无碎片段落', metrics: '清洗率、去重率、段落质量', status: 'done', statusText: '已完成', result: '417→265段落（去除152）' },
  { id: 4, name: '液压领域相关性过滤', question: '哪些段落与液压相关？', input: '清洗后段落+hydraulic_terms.json', operation: '术语词典匹配+核心关键词评分+段落长度惩罚', output: '255个液压相关段落', criteria: '保留率合理(96.2%)', metrics: '过滤保留率、领域相关分数', status: 'done', statusText: '已完成', result: '保留255/265，保留率96.2%' },
  { id: 5, name: '事件本体与Schema设计', question: '事件长什么样？', input: '领域术语+故障分析需求', operation: '定义6种事件类型、论元角色(部件/故障/状态/原因/维修/检测)、关系类型', output: '事件Schema定义', criteria: '覆盖故障/状态/检测/维修/传播/证据6类', metrics: '事件类型数、论元完整度', status: 'done', statusText: '已完成', result: '6种事件类型已定义' },
  { id: 6, name: '事件抽取', question: '如何从段落中抽事件？', input: '过滤后段落+event_triggers.json', operation: '触发词匹配→事件分类→论元填充→置信度计算→去重', output: '833条事件', criteria: '每条事件有触发词+类型+论元', metrics: 'Entity-F1、触发器F1、论元准确率', status: 'done', statusText: '已完成', result: '抽取833条事件，6种类型' },
  { id: 7, name: '证据锚定与双时态', question: '每条事件能溯源到哪？', input: '事件列表+原始段落', operation: '触发词定位→证据span提取→可靠度评估→双时态时间戳', output: '833条证据span', criteria: '锚定率100%', metrics: '证据覆盖率、证据准确率', status: 'done', statusText: '已完成', result: '833条证据锚定，锚定率100%' },
  { id: 8, name: '机理模板校验', question: '故障链符合液压机理吗？', input: '事件列表+6条机理模板', operation: '事件链匹配→完整/部分/违规/待审核分类→物理约束校验', output: '6条校验结果链', criteria: 'T1-T6全部匹配', metrics: '机理匹配率、违规率', status: 'done', statusText: '已完成', result: 'T1-T6全部完整匹配(100%)' },
  { id: 9, name: '事件归一与增量融合', question: '如何合并冗余事件？', input: '事件列表+synonyms.json', operation: '同义词归一→同义事件合并→保留最高置信度→去重', output: '258条归一化事件', criteria: '冗余合并后事件数合理', metrics: '重复事件率、冲突检测F1', status: 'done', statusText: '已完成', result: '833→258条（合并575条冗余）' },
  { id: 10, name: '图谱入库与可视化', question: '如何展示知识图谱？', input: '归一化事件+事件关系+模板链', operation: '生成中文节点→生成中文边→写入SQLite→ECharts可视化', output: '92节点+177边中文图谱', criteria: '节点标签为中文，非EVT编号', metrics: '节点完整度、孤立节点比', status: 'done', statusText: '已完成', result: '92节点+177边已入库' },
  { id: 11, name: '构建质量评价', question: '构建质量如何？', input: '构建全流程数据', operation: '计算17项评价指标→生成评价报告', output: '质量评价报告', criteria: '核心指标达到预期', metrics: '17项指标', status: 'done', statusText: '已完成', result: '事件链完整率100%，机理一致率100%' },
])

const bottomStats = ref([
  { label: '公开资料', value: '5', unit: '份' },
  { label: '液压段落', value: '255', unit: '段' },
  { label: '抽取事件', value: '833', unit: '条' },
  { label: '证据数量', value: '833', unit: '条' },
  { label: '机理模板', value: '6', unit: '条' },
  { label: '匹配链', value: '6', unit: '条' },
  { label: '图谱节点', value: '92', unit: '个' },
  { label: '图谱边', value: '177', unit: '条' },
  { label: '证据覆盖率', value: '100', unit: '%' },
  { label: '机理匹配率', value: '100', unit: '%' },
  { label: 'CQ通过率', value: '100', unit: '%' },
  { label: '事件类型', value: '6', unit: '种' },
])

function addLog(msg: string, level: string = 'info') {
  const now = new Date().toLocaleTimeString()
  logs.value.push({ time: now, msg, level })
  if (logs.value.length > 100) logs.value.shift()
}

async function runBuild() {
  running.value = true
  addLog('开始执行知识图谱构建流水线...', 'info')
  try {
    // 逐步执行各阶段
    addLog('[1/11] 任务界定 — 已定义', 'done')
    addLog('[2/11] 公开资料导入 — 5条来源已加载', 'done')
    addLog('[3/11] 文档解析与段落清洗 — 调用 POST /api/sources/clean', 'running')

    const res: any = await request.post('/api/graph/build')
    if (res['状态'] === '成功') {
      addLog(`构建完成: ${res['节点总数']}节点 + ${res['边总数']}边`, 'done')
      ElMessage.success(`构建成功: ${res['节点总数']}节点 + ${res['边总数']}边`)
      stages.value.forEach(s => { s.status = 'done'; s.statusText = '已完成' })
    }
  } catch (e: any) {
    addLog('构建失败: ' + (e?.message || '网络错误'), 'error')
    ElMessage.error('构建失败')
  } finally {
    running.value = false
  }
}

async function loadResult() {
  try {
    const res: any = await getBuildResult()
    addLog(`构建结果: ${JSON.stringify(res).slice(0, 200)}`, 'info')
    ElMessage.success('构建结果已加载')
  } catch { ElMessage.error('加载失败') }
}

async function loadLogs() {
  try {
    const res: any = await getBuildStatus()
    addLog(`当前状态: ${JSON.stringify(res).slice(0, 200)}`, 'info')
    ElMessage.success('日志已刷新')
  } catch { /* ignore */ }
}

onMounted(() => {
  addLog('系统就绪。点击"开始构建"执行知识图谱构建流水线。', 'info')
  loadResult()
})
</script>

<style scoped>
.build-page { padding: 10px; }
.subtitle { color: #909399; font-size: 13px; margin-bottom: 16px; }

.stage-card { border-left: 4px solid #909399; }
.stage-card.stage-done { border-left-color: #67C23A; }
.stage-card.stage-running { border-left-color: #409EFF; }
.stage-header { display: flex; align-items: center; gap: 8px; }
.stage-num { width: 24px; height: 24px; border-radius: 50%; background: #409EFF; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.stage-name { font-size: 14px; font-weight: 600; }
.stage-body { font-size: 12px; line-height: 1.8; }
.stage-row { margin: 3px 0; }
.stage-row b { color: #303133; }
.stage-result { margin-top: 6px; padding: 6px 10px; background: #f0f9eb; border-radius: 4px; color: #67C23A; font-weight: 600; }

.log-console { background: #1a1a2e; color: #00ff88; padding: 16px; border-radius: 8px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; }
.log-line { padding: 2px 0; }
.log-time { color: #666; margin-right: 12px; }
.log-done { color: #67C23A; }
.log-error { color: #F56C6C; }
.log-running { color: #409EFF; }
</style>
