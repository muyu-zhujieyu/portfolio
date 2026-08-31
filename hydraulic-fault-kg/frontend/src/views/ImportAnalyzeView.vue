<template>
  <div class="page-container">
    <h2>资料导入与补充分析
      <el-tag type="info" size="large" style="margin-left:12px">可选子功能</el-tag>
    </h2>

    <el-alert type="warning" :closable="false" style="margin-bottom:16px">
      <template #title>
        该功能用于对新增资料、图片或数据文件进行补充分析，并可选择将结果增量加入已有知识图谱。
        系统主图谱仍以公开维修手册、论文、教材、说明书和公开故障案例抽取构建为主。
        资料导入分析不是系统主流程前提，是可选的增量功能。
      </template>
    </el-alert>

    <!-- 步骤条 -->
    <el-steps :active="currentStep" align-center style="margin-bottom:24px">
      <el-step title="上传文件" description="选择文件上传" />
      <el-step title="开始分析" description="解析/清洗/过滤/抽取/锚定" />
      <el-step title="查看结果" description="事件/证据/故障链/维修建议" />
      <el-step title="加入图谱" description="增量融合到知识图谱" />
    </el-steps>

    <!-- 步骤1: 上传区 -->
    <el-card style="margin-bottom:16px">
      <template #header><b>步骤1: 上传文件</b></template>
      <el-row :gutter="16">
        <el-col :span="16">
          <el-upload
            ref="uploadRef"
            :action="uploadUrl"
            :on-success="onUploadSuccess"
            :on-error="onUploadError"
            :before-upload="beforeUpload"
            :show-file-list="false"
            drag>
            <el-icon class="el-icon--upload" :size="48"><UploadFilled /></el-icon>
            <div class="upload-text">
              <p>将文件拖拽到此处，或<em>点击上传</em></p>
              <p style="font-size:12px;color:#909399">
                支持: 图片(.png .jpg .jpeg) | 文档(.pdf .docx .txt .md) | 表格(.csv .xlsx) — 最大50MB
              </p>
            </div>
          </el-upload>
        </el-col>
        <el-col :span="8">
          <div class="type-cards">
            <el-card shadow="hover" class="type-card"><b>图片</b><br/>模拟OCR识别</el-card>
            <el-card shadow="hover" class="type-card"><b>文档</b><br/>解析/清洗/过滤</el-card>
            <el-card shadow="hover" class="type-card"><b>表格</b><br/>传感器趋势检测</el-card>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 上传文件列表 -->
    <el-card v-if="uploadedFiles.length" style="margin-bottom:16px">
      <template #header><b>已上传文件 ({{ uploadedFiles.length }})</b></template>
      <el-table :data="uploadedFiles" border stripe size="small" max-height="300">
        <el-table-column prop="文件编号" label="文件编号" width="140" />
        <el-table-column prop="文件名称" label="文件名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="文件类型" label="文件类型" width="80" />
        <el-table-column prop="文件大小_可读" label="文件大小" width="90" />
        <el-table-column prop="上传时间" label="上传时间" width="160" />
        <el-table-column prop="解析状态" label="解析状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row['解析状态'] === '已分析' ? 'success' : 'info'" size="small">{{ row['解析状态'] || '待分析' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="analyzeFile(row['文件编号'])" :loading="analyzing === row['文件编号']">开始分析</el-button>
            <el-button size="small" type="success" @click="addToKG(row['文件编号'])" :loading="adding === row['文件编号']" :disabled="row['解析状态'] !== '已分析'">加入图谱</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 步骤2-3: 分析结果 -->
    <el-card v-if="analysisResult" style="margin-bottom:16px">
      <template #header>
        <b>分析结果</b>
        <el-tag v-if="analysisResult['文件类型']" size="small" style="margin-left:8px">{{ analysisResult['文件类型'] }}</el-tag>
        <el-tag :type="analysisResult['置信度'] > 0.5 ? 'success' : 'warning'" size="small" style="margin-left:4px">
          置信度: {{ fmtPct(analysisResult['置信度']) }}
        </el-tag>
        <el-tag :type="riskTag" size="small" style="margin-left:4px">风险: {{ analysisResult['风险等级'] || '—' }}</el-tag>
      </template>

      <el-tabs v-model="resultTab">
        <el-tab-pane label="抽取事件" name="events">
          <el-table :data="analysisResult['抽取事件'] || []" border size="small" max-height="300">
            <el-table-column prop="事件编号" label="事件编号" width="100" />
            <el-table-column prop="事件类型" label="事件类型" width="100" />
            <el-table-column prop="触发词" label="触发词" width="80" />
            <el-table-column prop="故障模式" label="故障模式" width="120" />
            <el-table-column prop="异常状态" label="异常状态" width="120" />
            <el-table-column prop="事件描述" label="描述" min-width="150" show-overflow-tooltip />
            <el-table-column prop="置信度" label="置信度" width="80" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="证据span" name="evidence">
          <div v-for="(evd, i) in (analysisResult['证据span'] || [])" :key="i" style="padding:8px;margin:4px 0;background:#f5f7fa;border-radius:4px">
            <el-tag size="small" type="success" style="margin-right:8px">{{ evd['证据编号'] }}</el-tag>
            <span style="font-size:12px">{{ (evd['证据原文'] || '').slice(0, 200) }}</span>
          </div>
        </el-tab-pane>
        <el-tab-pane label="生成故障链" name="chains">
          <div v-for="(ch, i) in (analysisResult['生成故障链'] || [])" :key="i" style="padding:6px;margin:4px 0">
            <el-tag type="danger" size="small">{{ ch['模板编号'] }} {{ ch['模板名称'] }}</el-tag>
            <span style="font-size:13px;margin-left:8px">{{ ch['链式模式'] }}</span>
            <el-tag size="small" type="info" style="margin-left:8px">{{ ch['状态'] }}</el-tag>
          </div>
        </el-tab-pane>
        <el-tab-pane label="异常指标" name="anomalies">
          <div v-for="(a, i) in (analysisResult['异常指标'] || [])" :key="i" style="padding:6px;margin:4px 0;background:#fef0f0;border-radius:4px">
            <b>{{ a['指标'] }}</b>: {{ a['描述'] }}
          </div>
          <span v-if="!(analysisResult['异常指标']||[]).length" style="color:#909399">无异常指标（此文件非表格数据）</span>
        </el-tab-pane>
        <el-tab-pane label="维修建议" name="maintenance">
          <div v-for="(m, i) in (analysisResult['维修建议'] || [])" :key="i" style="padding:4px 0">• {{ m }}</div>
        </el-tab-pane>
        <el-tab-pane label="解析文本/清洗段落" name="text">
          <el-input type="textarea" :rows="8" :model-value="(analysisResult['解析文本'] || '').slice(0, 2000)" readonly />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 右侧子图谱 (用下方卡片展示) -->
    <el-card v-if="subGraphNodes.length" style="margin-bottom:16px">
      <template #header><b>本次分析生成的小型故障链图谱</b></template>
      <div ref="subChartRef" style="height:320px"></div>
    </el-card>

    <!-- 底部说明 -->
    <el-divider />
    <div class="footer-note">
      <p><b>说明：</b></p>
      <p>导入分析不是直接让大模型生成答案，而是对新增资料进行解析、清洗、过滤、事件抽取、证据锚定和机理模板校验；用户确认后，可信结果可增量加入事件知识图谱。</p>
      <p style="color:#E6A23C">此功能为可选增量功能。系统主流程基于 data/raw_sources/ 中的公开资料，不依赖此功能。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { analyzeFile as apiAnalyze, addToKG as apiAddToKG, getUploadedFiles } from '@/api/kgApi'
import { ElMessage } from 'element-plus'

const uploadUrl = 'http://127.0.0.1:8000/api/import/upload'
const uploadRef = ref<any>()
const currentStep = ref(0)
const uploadedFiles = ref<any[]>([])
const analyzing = ref('')
const adding = ref('')
const analysisResult = ref<any>(null)
const resultTab = ref('events')
const subChartRef = ref<HTMLElement>()

// 子图谱
const subGraphNodes = ref<any[]>([])
const subGraphLinks = ref<any[]>([])

const riskTag = computed(() => {
  const r = analysisResult.value?.['风险等级'] || ''
  return r === '高' ? 'danger' : r === '低' ? 'success' : 'warning'
})

function fmtPct(v: any) { const n = Number(v); return isNaN(n) ? '—' : (n * 100).toFixed(1) + '%' }

// 上传成功
function onUploadSuccess(response: any) {
  ElMessage.success('文件上传成功！')
  currentStep.value = 1
  loadFiles()
}

function onUploadError() {
  ElMessage.error('上传失败，请确认后端已启动')
}

function beforeUpload(file: File) {
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小超过50MB限制')
    return false
  }
  return true
}

// 加载文件列表
async function loadFiles() {
  try {
    const res: any = await getUploadedFiles()
    uploadedFiles.value = res['文件列表'] || res || []
  } catch { /* ignore */ }
}

// 分析文件
async function analyzeFile(fileId: string) {
  analyzing.value = fileId
  currentStep.value = 2
  try {
    const res: any = await apiAnalyze(fileId)
    if (res['状态'] === '成功') {
      analysisResult.value = res
      currentStep.value = 3
      ElMessage.success('分析完成')
      // 构建子图谱
      buildSubGraph(res)
    } else {
      ElMessage.error('分析失败: ' + (res['错误'] || '未知错误'))
    }
  } catch (e: any) {
    ElMessage.error('分析失败: ' + (e?.message || '网络错误'))
  } finally {
    analyzing.value = ''
  }
}

// 加入图谱
async function addToKG(fileId: string) {
  adding.value = fileId
  try {
    const res: any = await apiAddToKG(fileId)
    if (res['状态'] === '成功') {
      currentStep.value = 4
      ElMessage.success(`已加入图谱: ${res['加入事件数']} 事件 + ${res['加入证据数']} 证据`)
      loadFiles()
    } else {
      ElMessage.error('加入失败: ' + (res['错误'] || '无事件可加入'))
    }
  } catch (e: any) {
    ElMessage.error('加入失败: ' + (e?.message || '网络错误'))
  } finally {
    adding.value = ''
  }
}

// 构建子图谱
function buildSubGraph(data: any) {
  const events = data['抽取事件'] || []
  const chains = data['生成故障链'] || []

  const nodes: any[] = []
  const links: any[] = []
  const colors = ['#E74C3C', '#F39C12', '#3498DB', '#2ECC71', '#9B59B6', '#1ABC9C']

  // 从事件创建节点
  events.forEach((ev: any, i: number) => {
    nodes.push({
      id: ev['事件编号'] || `evt-${i}`,
      name: (ev['故障模式'] || ev['异常状态'] || ev['事件类型'] || '').slice(0, 16),
      category: ev['事件类型'] || '事件',
      symbolSize: 24,
      itemStyle: { color: colors[i % colors.length] },
      properties: ev,
    })
  })

  // 从故障链创建边
  chains.forEach((ch: any) => {
    const pattern = ch['链式模式'] || ''
    const steps = pattern.split('→').map((s: string) => s.trim())
    for (let j = 0; j < steps.length - 1; j++) {
      // 查找匹配的节点
      const src = nodes.find((n: any) => n.name.includes(steps[j]) || steps[j].includes(n.name))
      const tgt = nodes.find((n: any) => n.name.includes(steps[j + 1]) || steps[j + 1].includes(n.name))
      if (src && tgt) {
        links.push({ source: src.id, target: tgt.id, label: { show: true, formatter: '→', fontSize: 12 }, lineStyle: { color: '#E74C3C', width: 2 } })
      }
    }
  })

  // 如果没有边，为连续事件添加边
  if (links.length === 0 && nodes.length >= 2) {
    for (let i = 0; i < nodes.length - 1; i++) {
      links.push({ source: nodes[i].id, target: nodes[i + 1].id, label: { show: true, formatter: '关联', fontSize: 10 }, lineStyle: { color: '#95A5A6', width: 1 } })
    }
  }

  subGraphNodes.value = nodes
  subGraphLinks.value = links

  if (nodes.length === 0) return

  nextTick(() => {
    if (!subChartRef.value) return
    const chart = echarts.init(subChartRef.value)
    chart.setOption({
      tooltip: { trigger: 'item', formatter: (p: any) => p.dataType === 'node' ? `<b>${p.data.name}</b><br/>${p.data.properties?.['事件描述'] || ''}` : '' },
      series: [{
        type: 'graph', layout: 'force', roam: true, draggable: true,
        data: nodes, links,
        force: { repulsion: 200, edgeLength: [100, 250], gravity: 0.1 },
        label: { show: true, fontSize: 10, formatter: (p: any) => (p.data.name || '').slice(0, 14) },
        emphasis: { focus: 'adjacency' },
        lineStyle: { curveness: 0.2, opacity: 0.7 },
      }],
    })
  })
}

// 初始化
import { onMounted, computed } from 'vue'
onMounted(() => loadFiles())
</script>

<style scoped>
.page-container { padding: 10px; }
.upload-text { text-align: center; padding: 20px; }
.type-cards { display: flex; flex-direction: column; gap: 8px; }
.type-card { text-align: center; font-size: 13px; }
.type-card b { display: block; font-size: 15px; margin-bottom: 4px; }
.footer-note { background: #f5f7fa; padding: 16px; border-radius: 8px; font-size: 13px; color: #606266; line-height: 1.8; }
</style>
