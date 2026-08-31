<template>
  <div class="qa-page report-screen big-font-page">
    <div class="qa-header">
      <h2 style="margin: 0">基于三元组的知识图谱问答
        <el-tag type="danger" size="large" style="margin-left: 12px">必须功能</el-tag>
      </h2>
      <el-alert type="warning" :closable="false" style="margin-top: 8px">
        <template #title>
          回答来自三元组知识图谱、证据原文和机理模板。大模型只负责组织语言表达，不直接编造事实。
          所有论断均可追溯至来源资料、段落编号、三元组路径和原文证据。
        </template>
      </el-alert>
    </div>

    <el-row :gutter="16" style="margin-bottom: 16px; height: calc(100vh - 200px)">
      <el-col :span="14" style="height: 100%">
        <div class="chat-panel">
          <div class="chat-header">
            <span><b>问答对话</b></span>
            <el-tag v-if="sessionId" size="small" type="success">会话: {{ sessionId.slice(0, 12) }}...</el-tag>
            <el-button size="small" text @click="newSession">新建会话</el-button>
          </div>

          <div class="chat-messages" ref="chatMsgs">
            <div v-if="chatHistory.length === 0" class="chat-empty">
              <el-icon :size="48" color="#d9e1e8"><ChatDotRound /></el-icon>
              <p>点击下方预设问题或输入问题开始三元组知识图谱问答</p>
              <p style="font-size: 12px; color: #909399">
                系统基于三元组路径、证据原文和机理模板回答，不编造事实
              </p>
            </div>

            <div v-for="(msg, i) in chatHistory" :key="i" class="chat-msg-wrapper">
              <div class="chat-msg user-msg">
                <div class="msg-avatar"><el-icon :size="18"><User /></el-icon></div>
                <div class="msg-bubble user-bubble">{{ msg.question }}</div>
              </div>

              <div class="chat-msg ai-msg" v-if="msg.answer">
                <div class="msg-avatar ai-avatar"><el-icon :size="18"><Cpu /></el-icon></div>
                <div class="msg-content">
                  <!-- 1. 直接回答：放在最上面，突出显示 -->
                  <div v-if="msg.rawData?.direct_answer" class="direct-answer-box">
                    <div class="direct-answer-label">📌 直接回答</div>
                    <div class="direct-answer-text">{{ msg.rawData.direct_answer }}</div>
                  </div>

                  <!-- 完整回答文本 -->
                  <div class="msg-bubble ai-bubble">{{ msg.displayAnswer || msg.answer }}</div>

                  <div class="msg-extras" v-if="msg.rawData">
                    <el-collapse>
                      <!-- 2. 故障演化路径 -->
                      <el-collapse-item v-if="msg.rawData['path_summary']" title="故障演化路径">
                        <div class="path-display">{{ msg.rawData.path_summary }}</div>
                      </el-collapse-item>

                      <el-collapse-item v-if="msg.rawData['匹配三元组路径']?.length" title="三元组详细路径">
                        <div v-for="(path, pi) in msg.rawData['匹配三元组路径']" :key="pi" style="margin-bottom: 8px">
                          <el-tag type="success" size="small">路径: {{ path.start }} → {{ path.end }}</el-tag>
                          <div v-for="(tp, ti) in path.path_triples" :key="ti" class="triple-mini">
                            <span class="tp-subj">{{ tp.subject }}</span>
                            <span class="tp-pred">{{ tp.predicate }}</span>
                            <span class="tp-obj">{{ tp.object }}</span>
                            <el-tag v-if="tp.triple_source === '机理模板补全'" type="warning" size="small">模板补全</el-tag>
                          </div>
                        </div>
                      </el-collapse-item>

                      <!-- 3. 匹配故障演化链 -->
                      <el-collapse-item v-if="msg.rawData['匹配故障演化链']?.length" title="匹配故障演化链">
                        <div v-for="(ch, ci) in msg.rawData['匹配故障演化链']" :key="ci" class="chain-mini">
                          <el-tag size="small" type="danger">{{ ch.template_id || '' }} {{ ch.template_name || '' }}</el-tag>
                          <span> {{ ch.chain_text || '' }}</span>
                        </div>
                      </el-collapse-item>

                      <!-- 4. 原始证据 -->
                      <el-collapse-item v-if="msg.rawData['支撑证据']?.length" title="原始证据">
                        <div v-for="(evd, ei) in msg.rawData['支撑证据']" :key="ei" class="evidence-mini">
                          <el-tag size="small" type="success">{{ evd.triple_id || '' }}</el-tag>
                          <p>{{ (evd.evidence_text || '').slice(0, 200) }}</p>
                        </div>
                      </el-collapse-item>

                      <!-- 5. 检测建议 -->
                      <el-collapse-item v-if="msg.rawData['detections']?.length" title="检测建议">
                        <div v-for="(d, di) in msg.rawData['detections']" :key="di">• {{ d }}</div>
                      </el-collapse-item>

                      <!-- 6. 维修建议 -->
                      <el-collapse-item v-if="msg.rawData['推荐维修措施']?.length" title="维修建议">
                        <div v-for="(m, mi) in msg.rawData['推荐维修措施']" :key="mi">• {{ m }}</div>
                      </el-collapse-item>

                      <!-- 7. 答案依据说明 -->
                      <el-collapse-item title="答案依据说明">
                        <p style="color: #E6A23C">{{ msg.rawData['答案依据说明'] }}</p>
                      </el-collapse-item>

                      <!-- 8. 可继续追问 -->
                      <el-collapse-item v-if="msg.rawData['可继续追问的问题']?.length" title="可继续追问">
                        <el-tag v-for="(fq, fi) in msg.rawData['可继续追问的问题']" :key="fi"
                          size="small" style="margin: 2px 4px; cursor: pointer"
                          @click="quickAsk(fq)">{{ fq }}</el-tag>
                      </el-collapse-item>
                    </el-collapse>
                  </div>

                  <div v-if="msg.rawData?.置信度" class="msg-confidence">
                    置信度: {{ (msg.rawData.置信度 * 100).toFixed(1) }}%
                    <el-tag v-if="msg.rawData?.知识回退" type="warning" size="small" style="margin-left: 8px">
                      领域知识回退
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="loading" class="chat-msg ai-msg">
              <div class="msg-avatar ai-avatar"><el-icon :size="18"><Cpu /></el-icon></div>
              <div class="msg-bubble ai-bubble">
                <el-icon class="is-loading"><Loading /></el-icon> 正在检索三元组知识图谱并组织回答...
              </div>
            </div>
          </div>

          <div class="chat-input">
            <el-input v-model="question" placeholder="输入液压伺服阀故障相关问题..."
              size="large" clearable @keyup.enter="askQuestion" :disabled="loading">
              <template #append>
                <el-button type="primary" @click="askQuestion" :loading="loading">
                  发送
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-col>

      <el-col :span="10" style="height: 100%">
        <div class="subgraph-panel">
          <div class="panel-header">
            <span><b>相关子图谱</b></span>
            <el-tag v-if="subGraphNodes.length" size="small">
              {{ subGraphNodes.length }} 节点 / {{ subGraphLinks.length }} 边
            </el-tag>
          </div>
          <div v-if="subGraphNodes.length === 0" class="subgraph-empty">
            <el-icon :size="48" color="#d9e1e8"><Share /></el-icon>
            <p>提出问题后，此处将展示<br/>相关的三元组知识图谱子图</p>
          </div>
          <div v-else class="subgraph-chart" ref="subChartRef"></div>
          <div class="legend-bar" v-if="subGraphNodes.length">
            <span v-for="leg in subLegends" :key="leg.name" class="legend-item">
              <i class="legend-dot" :style="{ background: leg.color }"></i>{{ leg.name }}
            </span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 预设问题 -->
    <div class="preset-panel">
      <div class="panel-header"><b>推荐问题</b><span style="font-size:12px;color:#909399"> 点击即可提问</span></div>
      <el-row :gutter="8">
        <el-col :span="8" v-for="(ex, i) in presetQuestions" :key="i">
          <el-button size="small" class="preset-btn" @click="quickAsk(ex.question)">
            <el-tag :type="ex.tag" size="small" style="margin-right: 6px">{{ ex.type }}</el-tag>
            {{ ex.question }}
          </el-button>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { askQuestion as apiAsk, getQAExamples } from '@/api/kgApi'

const question = ref('')
const sessionId = ref('')
const loading = ref(false)
const chatMsgs = ref<HTMLElement>()

interface ChatMsg {
  question: string
  answer?: string
  displayAnswer?: string
  rawData?: any
  timestamp: number
}

const chatHistory = ref<ChatMsg[]>([])

const subChartRef = ref<HTMLElement>()
const subGraphNodes = ref<any[]>([])
const subGraphLinks = ref<any[]>([])
let subChart: echarts.ECharts | null = null

const NODE_COLORS: Record<string, string> = {
  '故障模式': '#E74C3C', '异常状态': '#F39C12',
  '检测方式': '#3498DB', '维修动作': '#2ECC71',
  '部件': '#9B59B6', '机理模板': '#1ABC9C',
}

const subLegends = [
  { name: '故障模式', color: '#E74C3C' },
  { name: '异常状态', color: '#F39C12' },
  { name: '检测方式', color: '#3498DB' },
  { name: '维修动作', color: '#2ECC71' },
  { name: '部件', color: '#9B59B6' },
]

const presetQuestions = ref([
  { type: '故障演化', tag: 'danger', question: '油液污染可能如何演化为压力波动？' },
  { type: '故障演化', tag: 'danger', question: '喷嘴堵塞会导致什么连锁反应？' },
  { type: '原因查询', tag: 'danger', question: '压力波动的原因有哪些？' },
  { type: '原因查询', tag: 'danger', question: '零位漂移是什么原因导致的？' },
  { type: '维修建议', tag: 'success', question: '阀芯卡滞应该如何处理？' },
  { type: '维修建议', tag: 'success', question: '喷嘴堵塞的维修方案是什么？' },
  { type: '证据追溯', tag: 'info', question: '阀芯卡滞有什么证据？' },
  { type: '机理解释', tag: 'info', question: '为什么油液污染会导致阀芯卡滞？' },
  { type: '方法对比', tag: '', question: '这和普通大模型直接回答有什么区别？' },
])

async function askQuestion() {
  const q = question.value.trim()
  if (!q || loading.value) return
  question.value = ''

  const msg: ChatMsg = { question: q, timestamp: Date.now() }
  chatHistory.value.push(msg)
  loading.value = true

  await nextTick()
  scrollToBottom()

  try {
    const res: any = await apiAsk(q, sessionId.value || undefined)
    if (!sessionId.value && res['session_id']) {
      sessionId.value = res['session_id']
    }

    const fullAnswer = res['中文答案'] || res['answer'] || ''
    msg.displayAnswer = fullAnswer.slice(0, 800) + (fullAnswer.length > 800 ? '...' : '')
    msg.answer = fullAnswer
    msg.rawData = res

    updateSubGraph(res)
  } catch (e: any) {
    msg.answer = '抱歉，问答服务暂时不可用。请确认后端已启动 (http://127.0.0.1:8000)。'
    msg.displayAnswer = msg.answer
  }

  loading.value = false
  await nextTick()
  scrollToBottom()
}

function quickAsk(q: string) {
  question.value = q
  askQuestion()
}

function newSession() {
  sessionId.value = ''
  chatHistory.value = []
  subGraphNodes.value = []
  subGraphLinks.value = []
}

function updateSubGraph(data: any) {
  const nodes = data['相关节点'] || []
  const links = data['相关边'] || []

  subGraphNodes.value = nodes
  subGraphLinks.value = links

  if (nodes.length === 0) return

  nextTick(() => {
    if (!subChartRef.value) return
    if (!subChart) subChart = echarts.init(subChartRef.value)

    const chartNodes = nodes.map((n: any) => ({
      id: n.id || n.name,
      name: n.label_zh || n.name || n.id,
      category: n.category_zh || n.node_type_zh || '故障模式',
      symbolSize: 24,
      itemStyle: { color: NODE_COLORS[n.category_zh || n.node_type_zh] || '#95A5A6' },
      properties: n,
    }))

    const chartLinks = links.map((l: any) => ({
      source: l.source || '',
      target: l.target || '',
      label: { show: true, fontSize: 9, formatter: l.relation_zh || l.label_zh || '' },
      lineStyle: { color: '#95A5A6', width: 1.5 },
    }))

    const categories = subLegends.map(l => ({
      name: l.name, itemStyle: { color: l.color },
    }))

    subChart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (p: any) => p.dataType === 'node'
          ? `<strong>${p.data.name}</strong><br/>类型: ${p.data.category}`
          : `${p.data.label?.formatter || ''}`,
      },
      legend: [{ data: categories.map(c => c.name), bottom: 0, textStyle: { fontSize: 9 } }],
      series: [{
        type: 'graph', layout: 'force', roam: true, categories, draggable: true,
        data: chartNodes, links: chartLinks,
        force: { repulsion: 300, edgeLength: [80, 200], gravity: 0.1 },
        label: { show: true, fontSize: 10, formatter: (p: any) => (p.data.name || '').slice(0, 12) },
        emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
        lineStyle: { curveness: 0.1, opacity: 0.6 },
      }],
    }, true)
  })
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatMsgs.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

onMounted(async () => {
  try {
    const res: any = await getQAExamples()
    if (res['问答类型']) {
      const allQs: any[] = []
      res['问答类型'].forEach((t: any) => {
        (t['示例问题'] || []).forEach((q: string) => {
          allQs.push({ type: t['类型'] || '', tag: 'info', question: q })
        })
      })
      if (allQs.length) presetQuestions.value = allQs.slice(0, 9)
    }
  } catch { /* use defaults */ }
})
</script>

<style scoped>
.qa-page { max-width: 1400px; margin: 0 auto; }
.qa-header { margin-bottom: 16px; }

.chat-panel {
  background: #fff; border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  height: 100%; display: flex; flex-direction: column;
}
.chat-header { display: flex; align-items: center; gap: 12px; padding: 12px 20px; border-bottom: 1px solid #ebeef5; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px; }
.chat-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #c0c4cc; gap: 8px; }

.chat-msg-wrapper { margin-bottom: 16px; }
.chat-msg { display: flex; gap: 10px; margin-bottom: 8px; }
.user-msg { justify-content: flex-end; }
.msg-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ai-avatar { background: #E74C3C; color: #fff; }
.user-msg .msg-avatar { background: #409EFF; color: #fff; order: 2; }
.msg-bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.user-bubble { background: #409EFF; color: #fff; border-bottom-right-radius: 4px; }
.ai-bubble { background: #f5f7fa; color: #303133; border-bottom-left-radius: 4px; }
.msg-content { flex: 1; min-width: 0; }
.msg-extras { margin-top: 6px; }

.triple-mini {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 8px; margin: 4px 0; background: #f5f7fa; border-radius: 4px;
}
.tp-subj { color: #E74C3C; font-weight: 600; }
.tp-pred { color: #3498DB; font-size: 12px; background: #e8f4fd; padding: 1px 6px; border-radius: 8px; }
.tp-obj { color: #2ECC71; font-weight: 600; }

.evidence-mini { padding: 6px; margin-bottom: 4px; background: #f5f7fa; border-radius: 4px; }
.evidence-mini p { font-size: 12px; color: #606266; margin: 4px 0 0 0; }
.chain-mini { padding: 4px 0; }
.msg-confidence { font-size: 11px; color: #909399; margin-top: 6px; }

/* Direct answer box */
.direct-answer-box {
  background: linear-gradient(135deg, #e8f4fd 0%, #f0f9ff 100%);
  border-left: 4px solid #3498DB;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 10px;
}
.direct-answer-label {
  font-size: 12px;
  font-weight: 700;
  color: #3498DB;
  margin-bottom: 6px;
}
.direct-answer-text {
  font-size: 14px;
  color: #303133;
  line-height: 1.7;
  font-weight: 500;
}

/* Path display */
.path-display {
  font-size: 13px;
  color: #E74C3C;
  font-weight: 600;
  padding: 8px 12px;
  background: #fef0f0;
  border-radius: 6px;
  line-height: 1.6;
}

.chat-input { padding: 12px 16px; border-top: 1px solid #ebeef5; }

.subgraph-panel { background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); height: 100%; display: flex; flex-direction: column; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid #ebeef5; }
.subgraph-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #c0c4cc; gap: 8px; }
.subgraph-chart { flex: 1; height: 0; }
.legend-bar { display: flex; flex-wrap: wrap; gap: 10px; padding: 6px 16px; border-top: 1px solid #ebeef5; }
.legend-item { display: flex; align-items: center; font-size: 10px; color: #606266; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; margin-right: 3px; }

.preset-panel { background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); padding: 16px; }
.preset-btn { width: 100%; margin-bottom: 6px; justify-content: flex-start; height: auto; padding: 8px 10px; font-size: 12px; white-space: normal; text-align: left; line-height: 1.4; }
</style>
