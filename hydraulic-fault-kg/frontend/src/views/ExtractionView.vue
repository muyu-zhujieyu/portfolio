<template>
  <div class="page-container report-screen big-font-page">
    <h2 style="font-size:34px">液压伺服阀故障维修三元组抽取</h2>
    <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
      <template #title>
        从公开维修手册、论文、教材等资料中抽取故障维修三元组（实体—关系—实体）。
        T1-T6机理模板只在三元组融合后用于校验和补全，不是原始来源。
      </template>
    </el-alert>

    <div class="pipeline">
      <div class="pipeline-step" v-for="(step,i) in pipelineSteps" :key="i">
        <div class="step-box" :class="{ done: step.done }">
          <div class="step-icon">{{ step.icon }}</div><div class="step-name">{{ step.name }}</div>
        </div>
        <div class="step-arrow" v-if="i < pipelineSteps.length - 1">→</div>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="3" v-for="stat in statsCards" :key="stat.label">
        <el-card shadow="hover" class="stat-card">
          <el-statistic :title="stat.label" :value="stat.value"><template #suffix v-if="stat.suffix"><span style="font-size:12px;color:#909399">{{ stat.suffix }}</span></template></el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-space style="margin-bottom: 20px">
      <el-button type="warning" @click="runFilter" :loading="filtering">步骤1: 领域过滤</el-button>
      <el-button type="primary" @click="runExtraction" :loading="extracting">步骤2: 三元组抽取与证据锚定</el-button>
      <el-button @click="loadData">刷新</el-button>
      <el-tag type="success" v-if="filterDone">过滤完成</el-tag>
      <el-tag type="primary" v-if="extractDone">三元组抽取完成</el-tag>
    </el-space>

    <el-card style="margin-bottom: 20px">
      <template #header><span><b>抽取三元组列表</b></span><el-tag type="primary" size="small" style="margin-left:8px">共 {{ tripleTotal }} 条</el-tag></template>
      <el-table :data="triples" border stripe v-loading="extracting" max-height="450" size="small">
        <el-table-column prop="triple_id" label="编号" width="110" />
        <el-table-column label="头实体" width="130"><template #default="{ row }"><span style="color:#E74C3C;font-weight:600">{{ row.subject }}</span><el-tag size="small" style="margin-left:4px">{{ row.subject_type }}</el-tag></template></el-table-column>
        <el-table-column prop="predicate" label="关系" width="110"><template #default="{ row }"><el-tag :type="predTag(row.predicate)" size="small">{{ row.predicate }}</el-tag></template></el-table-column>
        <el-table-column label="尾实体" width="130"><template #default="{ row }"><span style="color:#2ECC71;font-weight:600">{{ row.object }}</span><el-tag size="small" style="margin-left:4px">{{ row.object_type }}</el-tag></template></el-table-column>
        <el-table-column prop="source_title" label="来源资料" min-width="140" show-overflow-tooltip />
        <el-table-column prop="paragraph_id" label="段落" width="70" align="center" />
        <el-table-column prop="evidence_span" label="证据片段" min-width="180" show-overflow-tooltip />
        <el-table-column prop="extraction_method" label="抽取方式" width="90" align="center"><template #default="{ row }"><el-tag :type="row.extraction_method==='规则抽取'?'success':''" size="small">{{ row.extraction_method }}</el-tag></template></el-table-column>
        <el-table-column prop="confidence" label="置信度" width="80" align="center"><template #default="{ row }"><el-progress :percentage="Number(((row.confidence||0.5)*100).toFixed(0))" :stroke-width="8" :color="row.confidence>0.6?'#67C23A':'#E6A23C'" /></template></el-table-column>
      </el-table>
      <div style="text-align:center;margin-top:8px;color:#909399;font-size:12px">显示前50条，共 {{ tripleTotal }} 条</div>
    </el-card>

    <el-card style="margin-bottom: 20px">
      <template #header><span><b>证据锚定记录</b></span><el-tag type="success" size="small" style="margin-left:8px">共 {{ evidenceTotal }} 条</el-tag></template>
      <el-table :data="evidenceList" border stripe max-height="350" size="small">
        <el-table-column prop="evidence_id" label="证据编号" width="130" />
        <el-table-column prop="triple_id" label="三元组编号" width="110" />
        <el-table-column prop="source_title" label="来源资料" min-width="140" show-overflow-tooltip />
        <el-table-column prop="evidence_text" label="证据原文" min-width="280" show-overflow-tooltip />
        <el-table-column prop="reliability" label="可靠度" width="80" align="center"><template #default="{ row }"><el-tag :type="row.reliability==='高'?'success':row.reliability==='低'?'danger':'warning'" size="small">{{ row.reliability||'中' }}</el-tag></template></el-table-column>
      </el-table>
      <div style="text-align:center;margin-top:8px;color:#909399;font-size:12px">显示前50条，共 {{ evidenceTotal }} 条</div>
    </el-card>

    <el-divider />
    <div class="footer-note">
      <p><strong>三元组抽取流程说明：</strong></p>
      <p>以上三元组数据来源于公开维修手册、论文、教材、说明书和公开故障案例。每条三元组均锚定到原始公开资料的原文片段作为证据。</p>
      <p style="color:#E6A23C;margin-top:8px">T1-T6机理模板只在三元组融合之后用于校验链条完整性和补全缺失关系，不是三元组的原始来源。模板补全的三元组标注"机理模板补全"。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { filterSources, runExtraction as runExtApi, getFilteredParagraphs, getExtractionTriples, getExtractionEvidence, getExtractionStatistics } from '@/api/kgApi'
import { ElMessage } from 'element-plus'

const pipelineSteps = ref([{ name: '公开资料', icon: '📚', done: true },{ name: '文档解析', icon: '📄', done: true },{ name: '段落清洗', icon: '🧹', done: true },{ name: '液压领域过滤', icon: '🔍', done: false },{ name: '三元组抽取', icon: '⚡', done: false },{ name: '证据锚定', icon: '📌', done: false }])
const filtering = ref(false); const extracting = ref(false)
const filterDone = ref(false); const extractDone = ref(false)
const filterTotal = ref(0); const tripleTotal = ref(0); const evidenceTotal = ref(0)
const cleanedTotal = ref(0)
const relationTypeCount = ref<Record<string, number>>({})

const retentionRate = computed(() => cleanedTotal.value === 0 ? '—' : ((filterTotal.value / cleanedTotal.value) * 100).toFixed(1))

const statsCards = computed(() => [
  { label: '公开资料', value: 5, suffix: '份' },
  { label: '液压段落', value: filterTotal.value, suffix: '段' },
  { label: '原始三元组', value: tripleTotal.value, suffix: '条' },
  { label: '有证据三元组', value: evidenceTotal.value, suffix: '条' },
  { label: '关系类型', value: Object.keys(relationTypeCount.value).length, suffix: '种' },
  { label: '模板补全', value: '—', suffix: '条' },
  { label: '过滤保留率', value: retentionRate.value, suffix: '%' },
  { label: '低贡献资料', value: '—', suffix: '份' },
])

const triples = ref<any[]>([])
const evidenceList = ref<any[]>([])

function predTag(pred: string): string {
  const map: Record<string, string> = { '导致': 'danger', '表现为': 'warning', '由检测确认': '', '由维修处理': 'success', '包含': '', '发生于': 'info', '复测验证': 'success' }
  return map[pred] || 'info'
}

async function runFilter() {
  filtering.value = true
  try {
    const res: any = await filterSources()
    if (res['状态'] === '成功') {
      filterTotal.value = res['液压相关段落数'] || 0; cleanedTotal.value = res['清洗后段落数'] || 0
      pipelineSteps.value[3].done = true; filterDone.value = true
      ElMessage.success(`过滤完成: ${cleanedTotal.value} → ${filterTotal.value} 段`)
    } else ElMessage.error('过滤失败')
  } catch (e: any) { ElMessage.error(String(e)) } finally { filtering.value = false }
}

async function runExtraction() {
  extracting.value = true
  try {
    const res: any = await runExtApi()
    if (res['状态'] === '成功') {
      tripleTotal.value = res['三元组总数'] || 0; evidenceTotal.value = res['证据总数'] || 0
      pipelineSteps.value[4].done = true; pipelineSteps.value[5].done = true; extractDone.value = true
      relationTypeCount.value = res['类型统计'] || {}
      ElMessage.success(`三元组抽取完成: ${tripleTotal.value} 条`)
      await loadDetails()
    } else ElMessage.error('抽取失败: ' + (res['错误']||''))
  } catch (e: any) { ElMessage.error(String(e)) } finally { extracting.value = false }
}

async function loadDetails() {
  try {
    const [tr, evd, st] = await Promise.all([getExtractionTriples(), getExtractionEvidence(), getExtractionStatistics()])
    triples.value = ((tr as any)['三元组列表'] || []).slice(0, 50); evidenceList.value = ((evd as any)['证据列表'] || []).slice(0, 50)
    tripleTotal.value = (st as any)['三元组总数'] || tripleTotal.value; evidenceTotal.value = (st as any)['证据总数'] || evidenceTotal.value
    relationTypeCount.value = (st as any)['关系类型统计'] || relationTypeCount.value
  } catch { /* ignore */ }
}

async function loadData() {
  try { const fp: any = await getFilteredParagraphs(); if (fp?.['液压相关段落数']) { filterTotal.value = fp['液压相关段落数']; filterDone.value = true; pipelineSteps.value[3].done = true } } catch { /* */ }
  try { const st: any = await getExtractionStatistics(); if (st?.['三元组总数']) { tripleTotal.value = st['三元组总数']; extractDone.value = true; pipelineSteps.value[4].done = true; pipelineSteps.value[5].done = true; await loadDetails() } } catch { /* */ }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.page-container { padding: 10px; }
.stat-card { text-align: center; }
.pipeline { display: flex; align-items: center; justify-content: center; margin-bottom: 24px; padding: 20px; background: #f5f7fa; border-radius: 8px; flex-wrap: wrap; gap: 6px; }
.pipeline-step { display: flex; align-items: center; }
.step-box { padding: 12px 16px; border-radius: 10px; background: #e4e7ed; text-align: center; min-width: 90px; }
.step-box.done { background: #67C23A; color: #fff; }
.step-icon { font-size: 22px; } .step-name { font-size: 12px; margin-top: 4px; }
.step-arrow { font-size: 24px; margin: 0 6px; color: #909399; }
.footer-note { background: #f5f7fa; padding: 16px; border-radius: 8px; font-size: 13px; color: #606266; line-height: 1.8; }
</style>
