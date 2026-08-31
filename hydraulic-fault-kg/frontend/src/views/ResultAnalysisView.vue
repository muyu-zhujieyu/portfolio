<template>
  <div class="ra-page report-screen big-font-page">
    <!-- 标题 -->
    <div class="ra-header">
      <h2>液压伺服阀原始曲线结果分析</h2>
      <p class="ra-subtitle">基于 20201010 文档原始曲线图的部位级样本异常判断</p>
      <el-alert type="info" :closable="false" style="margin-top:8px;font-size:18px">
        本页展示20201010文档中提取的原始曲线图片及分析结果。曲线来源：20201010原始文档提取，未修改原始曲线。
      </el-alert>
    </div>

    <!-- 筛选区 -->
    <el-card class="filter-card" shadow="hover" style="margin-bottom:14px">
      <el-row :gutter="16" align="middle">
        <el-col :span="5">
          <label class="filter-label">选择部位</label>
          <el-select v-model="selectedPart" placeholder="选择部位" size="large" style="width:100%" @change="onPartChange">
            <el-option v-for="p in parts" :key="p['部位名称']" :label="p['部位名称']+' ('+p['样本总数']+'样本)'" :value="p['部位名称']" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <label class="filter-label">选择样本</label>
          <el-select v-model="selectedSample" placeholder="选择样本" size="large" style="width:100%">
            <el-option v-for="s in samples" :key="s['样本编号']" :label="s['样本编号']" :value="s['样本编号']">
              <span>{{ s['样本编号'] }}</span>
              <el-tag :type="s['是否异常']?'danger':'success'" size="small" style="margin-left:8px">{{ s['诊断结论'] }}</el-tag>
            </el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <label class="filter-label">&nbsp;</label>
          <el-button type="primary" size="large" @click="analyzeSample" :loading="loading" style="width:100%">分析样本</el-button>
        </el-col>
        <el-col :span="3">
          <el-button size="large" @click="extractDoc" style="width:100%">重新提取文档</el-button>
        </el-col>
        <el-col :span="3">
          <el-button size="large" type="warning" @click="analyzeAll" :loading="analyzing" style="width:100%">重新分析全部</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 主体：原始曲线图 + 诊断 -->
    <el-row :gutter="16" style="margin-bottom:14px">
      <!-- 左侧：原始曲线图片 -->
      <el-col :span="15">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span class="card-hd">原始曲线图片</span>
            <span v-if="result" style="font-size:15px;color:#909399;margin-left:12px">
              {{ result['样本']['样本编号'] }} | {{ result['样本']['部位名称'] }}
            </span>
          </template>
          <div class="image-container" v-if="result && result['样本']['原始图片路径']">
            <img :src="imgUrl" alt="原始曲线图片" class="original-curve-img" />
          </div>
          <div v-else class="no-image">
            <p>请选择样本并点击"分析样本"查看原始曲线图片</p>
          </div>
          <div class="curve-source-note" v-if="result">
            曲线来源：20201010 原始文档提取，未修改原始曲线。
          </div>
        </el-card>
      </el-col>

      <!-- 右侧诊断结论 -->
      <el-col :span="9">
        <el-card shadow="hover" class="diag-card" :style="{ borderTopColor: diagColor, borderTopWidth: '6px' }">
          <template #header><span class="card-hd">诊断结论</span></template>
          <div class="diag-body" v-if="result">
            <div class="diag-status" :style="{ color: diagColor }">{{ result['样本']['诊断结论'] }}</div>
            <div style="margin:10px 0">
              <el-tag :type="result['样本']['是否异常']?'danger':'success'" size="large" effect="dark">
                {{ result['样本']['是否异常'] ? '异常样本' : '正常样本' }}
              </el-tag>
            </div>
            <div class="diag-confidence">
              <el-progress type="circle" :percentage="confPct" :width="140" :color="diagColor" :stroke-width="12">
                <template #default><span style="font-size:24px;font-weight:800">{{ confPct }}%</span></template>
              </el-progress>
              <div style="margin-top:6px;color:#909399;font-size:16px">置信度</div>
            </div>
            <div class="diag-similarity" style="font-size:18px">
              相似度: <b :style="{ color: diagColor, fontSize:'26px' }">{{ fmtNum(result['样本']['相似度']) }}</b>
            </div>
          </div>
          <div v-else class="diag-empty"><p>请选择部位和样本后点击"分析样本"</p></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 指标卡片 -->
    <el-card shadow="hover" style="margin-bottom:14px" v-if="result">
      <template #header><span class="card-hd">关键指标</span></template>
      <el-row :gutter="10">
        <el-col :span="3" v-for="(meta, key) in indicatorsToShow" :key="key" style="margin-bottom:6px">
          <div class="ind-card" :class="{ 'ind-abnormal': meta.outlier }">
            <div class="ind-val" :style="{ color: meta.outlier ? '#E74C3C' : '#303133' }">{{ meta.display }}</div>
            <div class="ind-key">{{ meta.label }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 异常/正常分流 -->
    <div v-if="result">
      <!-- 正常样本 -->
      <el-card v-if="!result['样本']['是否异常']" shadow="hover" style="margin-bottom:14px">
        <el-alert type="success" :closable="false" title="当前样本关键指标处于阈值范围内，未触发故障链关联分析。" style="font-size:18px" />
      </el-card>

      <!-- 异常样本：故障关联增强 -->
      <div v-if="result['样本']['是否异常']" class="fault-section">
        <!-- 故障关联信息 -->
        <el-card v-if="result['故障关联信息']" shadow="hover" class="fault-info-card" style="margin-bottom:14px">
          <template #header><span class="card-hd" style="color:#E74C3C">故障关联信息</span></template>
          <el-row :gutter="12">
            <el-col :span="6"><div class="fault-field"><b>故障名称：</b>{{ result['故障关联信息']['故障名称'] }}</div></el-col>
            <el-col :span="6"><div class="fault-field"><b>关联部件：</b>{{ result['故障关联信息']['关联部件'] }}</div></el-col>
            <el-col :span="6"><div class="fault-field"><b>异常类型：</b><el-tag type="danger" size="large">{{ result['故障关联信息']['异常类型'] }}</el-tag></div></el-col>
            <el-col :span="6">
              <div class="fault-field"><b>异常指标：</b>
                <el-tag v-for="ai in result['故障关联信息']['异常指标']" :key="ai" type="danger" size="small" style="margin:2px">{{ ai }}</el-tag>
              </div>
            </el-col>
          </el-row>
          <div class="fault-desc" style="margin-top:12px;font-size:18px;color:#606266;line-height:1.8">{{ result['故障关联信息']['故障说明'] }}</div>
        </el-card>

        <!-- Tabs: 链条/子图谱/证据/文档/维修 -->
        <el-card shadow="hover" style="margin-bottom:14px">
          <el-tabs v-model="faultTab" type="border-card">
            <el-tab-pane label="知识图谱相关链条" name="chains">
              <div v-if="(result['知识图谱相关链条']||[]).length">
                <div v-for="ch in result['知识图谱相关链条']" :key="ch['链条编号']" class="chain-block">
                  <div class="chain-header">
                    <el-tag type="danger" size="large">{{ ch['链条编号'] }}</el-tag>
                    <span class="chain-name">{{ ch['链条名称'] }}</span>
                    <el-tag type="warning" size="small">匹配 {{ ch['匹配分数'] }}</el-tag>
                  </div>
                  <div class="chain-text">{{ ch['链条文本'] }}</div>
                  <div class="chain-nodes" style="margin-top:8px">
                    <el-tag v-for="n in ch['命中节点']" :key="n" size="small" type="info" style="margin:2px">{{ n }}</el-tag>
                  </div>
                </div>
              </div>
              <div v-else style="color:#909399;font-size:16px">暂无匹配链条</div>
            </el-tab-pane>

            <el-tab-pane label="相关子图谱" name="subgraph">
              <div ref="faultChartRef" style="height:380px"></div>
            </el-tab-pane>

            <el-tab-pane label="相关证据" name="evidence">
              <div v-if="(result['相关证据']||[]).length">
                <div v-for="evd in result['相关证据']" :key="evd['证据编号']" class="evd-block">
                  <div class="evd-header">
                    <el-tag type="success" size="small">{{ evd['证据编号'] }}</el-tag>
                    <el-tag type="info" size="small">{{ evd['来源类型'] }}</el-tag>
                    <span style="font-size:15px;color:#909399">{{ evd['来源文件'] }}</span>
                    <el-tag :type="(evd['可靠度']||0)>0.8?'success':'warning'" size="small">可靠度 {{ evd['可靠度'] }}</el-tag>
                  </div>
                  <p class="evd-text">{{ evd['证据原文'] }}</p>
                </div>
              </div>
              <div v-else style="color:#909399;font-size:16px">暂无证据</div>
            </el-tab-pane>

            <el-tab-pane label="原始文档上下文" name="doc">
              <div class="doc-ctx" v-if="result['原始文档相关上下文']">
                <p><b>来源文件：</b>{{ result['原始文档相关上下文']['来源文件'] }}</p>
                <div v-for="p in result['原始文档相关上下文']['上下文段落']" :key="p['段落编号']" class="doc-para">
                  <el-tag size="small" type="info">{{ p['段落编号'] }}</el-tag>
                  <span>{{ p['文本'] }}</span>
                </div>
                <el-alert type="info" :closable="false" style="margin-top:8px;font-size:16px">
                  {{ result['原始文档相关上下文']['上下文说明'] }}
                </el-alert>
              </div>
            </el-tab-pane>

            <el-tab-pane label="大模型维修推荐" name="maintenance">
              <div v-if="result['大模型维修推荐方案']" class="maint-block">
                <el-alert type="error" :closable="false" style="margin-bottom:12px;font-size:18px">
                  <template #title>{{ result['大模型维修推荐方案']['推荐结论'] }}</template>
                </el-alert>
                <el-row :gutter="12" style="margin-bottom:12px">
                  <el-col :span="8">
                    <el-statistic title="优先级" :value="result['大模型维修推荐方案']['优先级']" />
                    <el-statistic title="风险等级">
                      <template #default>
                        <el-tag :type="result['大模型维修推荐方案']['风险等级']==='高'?'danger':'warning'" size="large">
                          {{ result['大模型维修推荐方案']['风险等级'] }}
                        </el-tag>
                      </template>
                    </el-statistic>
                  </el-col>
                  <el-col :span="8">
                    <el-statistic title="是否需人工复核">
                      <template #default>
                        <el-tag :type="result['大模型维修推荐方案']['是否需要人工复核']?'warning':'success'" size="large">
                          {{ result['大模型维修推荐方案']['是否需要人工复核'] ? '需要' : '无需' }}
                        </el-tag>
                      </template>
                    </el-statistic>
                  </el-col>
                </el-row>
                <div class="maint-actions">
                  <b style="font-size:18px">推荐措施：</b>
                  <el-steps direction="vertical">
                    <el-step v-for="(a,i) in result['大模型维修推荐方案']['推荐措施']" :key="i"
                      :title="'步骤 '+(i+1)" :description="a" status="process" />
                  </el-steps>
                </div>
                <el-alert type="warning" :closable="false" style="margin-top:8px;font-size:16px">
                  <template #title>推荐依据：{{ result['大模型维修推荐方案']['推荐依据'] }}</template>
                </el-alert>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>
    </div>

    <!-- 底部说明 -->
    <el-divider />
    <div class="bottom-note">
      <p><b>说明：</b>本页面展示20201010文档中提取的原始曲线图片及其分析结果。异常判断基于Pillow+numpy图像特征分析（曲线像素占比、左右不对称度、零位偏移、粗糙度、斜率等），与同部位中位数标准对比计算相似度后得出诊断结论。该曲线图来自20201010原始文档提取，系统仅进行图像特征分析，未修改原始曲线。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getSampleParts, getSampleList, getSampleResult, extractSampleDoc, analyzeAllSamples } from '@/api/kgApi'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const analyzing = ref(false)
const selectedPart = ref('')
const selectedSample = ref('')
const parts = ref<any[]>([])
const samples = ref<any[]>([])
const result = ref<any>(null)
const faultTab = ref('chains')
const faultChartRef = ref<HTMLElement>()
let faultChart: echarts.ECharts | null = null

// 原始图片URL（通过后端静态文件服务或直接引用）
const imgUrl = computed(() => {
  const path = result.value?.['样本']?.['原始图片路径']
  if (!path) return ''
  // 前端无法直接访问本地文件系统，这里通过Vite的public目录映射
  // 后端应在 /api/sample-analysis/raw-image 端点返回图片
  const sid = result.value?.['样本']?.['样本编号'] || ''
  return `http://127.0.0.1:8000/api/sample-analysis/raw-image?sample_id=${sid}`
})

const indicatorsToShow = computed(() => {
  const s = result.value?.['样本']
  if (!s) return {}
  const ki = s['指标卡片'] || {}
  const out: Record<string, any> = {}
  for (const [k, v] of Object.entries(ki)) {
    const vi = v as any
    const val = vi['值']
    const isNum = typeof val === 'number'
    const shortKey = k.length > 6 ? k.slice(0, 6) + '..' : k
    let outlier = false
    if (isNum) {
      const nv = Number(val)
      if (k === '左右不对称度') outlier = nv > 0.05
      else if (k === '曲线粗糙度') outlier = nv > 2.5
      else if (k === '零位位置') outlier = Math.abs(nv) > 0.04
      else if (k === '估计斜率') outlier = Math.abs(nv) > 0.06
    }
    out[shortKey] = {
      label: k,
      display: isNum ? (Number(val) < 0.01 ? val.toFixed(4) : Number(val).toFixed(3)) : String(val),
      outlier,
    }
  }
  return out
})

const diagColor = computed(() => {
  const d = result.value?.['样本']?.['诊断结论'] || ''
  if (d.includes('明显异常')) return '#E74C3C'
  if (d.includes('疑似异常')) return '#F56C6C'
  if (d.includes('轻度异常')) return '#E6A23C'
  return '#67C23A'
})
const confPct = computed(() => {
  const c = result.value?.['样本']?.['置信度']
  return c !== undefined ? Math.round(c * 100) : 0
})
function fmtNum(v: any) { if (v === null || v === undefined) return '—'; const n = Number(v); return isNaN(n) ? String(v) : n.toFixed(3) }

async function loadParts() {
  try {
    const res: any = await getSampleParts()
    parts.value = res['部位列表'] || []
    if (parts.value.length && !selectedPart.value) {
      selectedPart.value = parts.value[0]['部位名称']
      await onPartChange(selectedPart.value)
    }
  } catch { ElMessage.error('加载部位失败') }
}
async function onPartChange(part: string) {
  if (!part) return
  try {
    const res: any = await getSampleList(part)
    samples.value = res['样本列表'] || []
    if (samples.value.length) {
      selectedSample.value = samples.value[0]['样本编号']
      await analyzeSample()
    }
  } catch { ElMessage.error('加载样本失败') }
}
async function analyzeSample() {
  if (!selectedPart.value || !selectedSample.value) { ElMessage.warning('请选择部位和样本'); return }
  loading.value = true
  try {
    const res: any = await getSampleResult(selectedPart.value, selectedSample.value)
    result.value = res
    await nextTick()
    if (res['样本']?.['是否异常']) { renderFaultSubGraph() }
  } catch { ElMessage.error('加载分析结果失败') }
  finally { loading.value = false }
}
async function extractDoc() {
  try { await extractSampleDoc(); ElMessage.success('文档提取完成'); await loadParts() }
  catch { ElMessage.error('提取失败') }
}
async function analyzeAll() {
  analyzing.value = true
  try { await analyzeAllSamples(); ElMessage.success('全部分析完成'); await loadParts() }
  catch { ElMessage.error('分析失败') }
  finally { analyzing.value = false }
}

function renderFaultSubGraph() {
  if (!faultChartRef.value) return
  const sg = result.value?.['相关子图谱']
  if (!sg) return
  if (!faultChart) faultChart = echarts.init(faultChartRef.value)
  const nodes = (sg['nodes'] || []).map((n: any) => ({ ...n, symbolSize: n.symbolSize || 32 }))
  const links = (sg['links'] || []).map((l: any) => ({ ...l, label: { show: true, formatter: l.label || '', fontSize: 13 } }))
  faultChart.setOption({
    tooltip: { trigger: 'item', formatter: (p: any) => p.dataType === 'node' ? `<b>${p.data.name}</b>` : p.data.label || '' },
    legend: [{ data: ['部件','故障事件','状态事件','维修事件','证据事件'], bottom: 0, textStyle: { fontSize: 12 } }],
    series: [{ type: 'graph', layout: 'force', roam: true, draggable: true, data: nodes, links,
      force: { repulsion: 250, edgeLength: [120, 250], gravity: 0.08 },
      label: { show: true, fontSize: 13, formatter: (p: any) => (p.data.name || '').slice(0, 14) },
      emphasis: { focus: 'adjacency' }, lineStyle: { curveness: 0.1, opacity: 0.7 } }],
  }, true)
}
watch(faultTab, (val) => { if (val === 'subgraph') { setTimeout(() => renderFaultSubGraph(), 200) } })

onMounted(async () => { await loadParts() })
</script>

<style scoped>
.ra-page { padding: 10px; max-width: 100%; }
.ra-header { margin-bottom: 10px; }
.ra-header h2 { font-size: 34px; font-weight: 800; color: #1a3a5c; margin: 0 0 2px 0; }
.ra-subtitle { font-size: 18px; color: #909399; margin: 0; }
.filter-card { margin-bottom: 14px; }
.filter-label { font-size: 17px; font-weight: 600; color: #303133; display: block; margin-bottom: 4px; }
.card-hd { font-size: 20px; font-weight: 700; color: #1a3a5c; }

.image-container { text-align: center; padding: 10px; background: #fafafa; border-radius: 6px; min-height: 300px; display: flex; align-items: center; justify-content: center; }
.original-curve-img { max-width: 100%; max-height: 480px; object-fit: contain; border: 1px solid #e4e7ed; border-radius: 4px; }
.no-image { text-align: center; padding: 80px 20px; color: #c0c4cc; font-size: 18px; }
.curve-source-note { text-align: center; margin-top: 8px; font-size: 15px; color: #E6A23C; font-weight: 600; }
.diag-card { border-top: 6px solid #67C23A; }
.diag-body { text-align: center; }
.diag-status { font-size: 36px; font-weight: 800; margin-bottom: 8px; }
.diag-confidence { margin: 16px 0; }
.diag-similarity { font-size: 18px; color: #606266; margin: 8px 0; }
.diag-empty { text-align: center; padding: 60px 20px; color: #c0c4cc; font-size: 18px; }

.ind-card { text-align: center; padding: 14px 8px; background: #f5f7fa; border-radius: 10px; }
.ind-card.ind-abnormal { background: #fef0f0; border: 1px solid #F56C6C; }
.ind-val { font-size: 30px; font-weight: 700; }
.ind-key { font-size: 15px; color: #909399; margin-top: 4px; }

.fault-section {}
.fault-info-card { border-left: 6px solid #E74C3C; }
.fault-field { font-size: 17px; color: #303133; line-height: 2; }
.fault-desc { font-size: 18px; }
.chain-block { padding: 14px; margin-bottom: 10px; background: #fef0f0; border-radius: 10px; border-left: 5px solid #E74C3C; }
.chain-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.chain-name { font-size: 18px; font-weight: 700; color: #303133; }
.chain-text { font-size: 17px; color: #E74C3C; font-weight: 700; padding: 8px 0; }
.evd-block { padding: 12px; margin-bottom: 8px; background: #f5f7fa; border-radius: 8px; }
.evd-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.evd-text { font-size: 17px; color: #606266; line-height: 1.8; margin: 0; }
.doc-ctx { font-size: 17px; line-height: 1.8; }
.doc-para { padding: 10px; margin: 6px 0; background: #f5f7fa; border-radius: 8px; font-size: 16px; }
.doc-para span { margin-left: 10px; }
.maint-block { font-size: 17px; }
.maint-actions { margin: 14px 0; }
.bottom-note { background: #f5f7fa; padding: 16px 20px; border-radius: 10px; font-size: 16px; color: #606266; line-height: 1.8; }
.bottom-note b { color: #303133; }
</style>
