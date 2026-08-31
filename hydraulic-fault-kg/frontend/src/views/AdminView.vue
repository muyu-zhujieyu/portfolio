<template>
  <div class="admin-page report-screen big-font-page">
    <h2>后台管理 — 完整数据链路</h2>
    <p class="subtitle">从公开资料来源到知识图谱节点、从事件抽取到大模型问答记录的全链路数据管理</p>

    <!-- 统计卡片 -->
    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="3" v-for="s in stats" :key="s.label">
        <el-card shadow="hover" class="stat-mini" @click="activeTab = s.tab">
          <div class="stat-num">{{ s.value }}</div>
          <div class="stat-lbl">{{ s.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索与筛选 -->
    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="8">
        <el-input v-model="searchKeyword" placeholder="搜索关键词..." clearable size="default">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </el-col>
      <el-col :span="3" v-if="showTypeFilter">
        <el-select v-model="typeFilter" placeholder="事件类型" clearable style="width:100%">
          <el-option v-for="t in eventTypes" :key="t" :label="t" :value="t" />
        </el-select>
      </el-col>
      <el-col :span="3" v-if="showStatusFilter">
        <el-select v-model="statusFilter" placeholder="版本状态" clearable style="width:100%">
          <el-option label="活跃(active)" value="active" />
          <el-option label="过期(expired)" value="expired" />
          <el-option label="已解决(resolved)" value="resolved" />
        </el-select>
      </el-col>
      <el-col :span="3">
        <el-button @click="loadCurrentTab">刷新数据</el-button>
      </el-col>
    </el-row>

    <!-- 10个Tab -->
    <el-tabs v-model="activeTab" @tab-change="onTabChange" type="border-card">
      <el-tab-pane label="数据来源" name="sources">
        <el-table :data="filtered(sourcesData)" border stripe size="small" max-height="450">
          <el-table-column prop="source_id" label="来源编号" width="140" />
          <el-table-column prop="来源类型" label="来源类型" width="120" />
          <el-table-column prop="标题" label="标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="作者" label="作者" width="100" />
          <el-table-column prop="年份" label="年份" width="70" />
          <el-table-column prop="出版方" label="出版方" width="140" show-overflow-tooltip />
          <el-table-column prop="文件路径" label="文件路径" width="180" show-overflow-tooltip />
          <el-table-column prop="公开说明" label="公开说明" min-width="160" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="过滤段落" name="paragraphs">
        <el-table :data="filtered(paragraphsData)" border stripe size="small" max-height="450">
          <el-table-column prop="filtered_id" label="段落编号" width="160" />
          <el-table-column prop="source_id" label="来源编号" width="140" />
          <el-table-column prop="过滤后内容" label="清洗文本" min-width="250" show-overflow-tooltip />
          <el-table-column prop="相关度评分" label="领域相关分数" width="110" align="center" />
          <el-table-column label="是否保留" width="90" align="center">
            <template #default="{ row }"><el-tag :type="(row['相关度评分']||0) > 0.02 ? 'success' : 'danger'" size="small">{{ (row['相关度评分']||0) > 0.02 ? '保留' : '过滤' }}</el-tag></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="事件管理" name="events">
        <el-table :data="filtered(eventsData)" border stripe size="small" max-height="450">
          <el-table-column prop="事件编号" label="事件编号" width="100" v-if="false" />
          <el-table-column prop="event_id" label="事件编号" width="100" />
          <el-table-column prop="事件类型" label="事件类型" width="100">
            <template #default="{ row }"><el-tag :type="evtTypeTag(row['事件类型'])" size="small">{{ row['事件类型'] }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="事件触发词" label="触发词" width="80" />
          <el-table-column prop="事件描述" label="事件描述" min-width="180" show-overflow-tooltip />
          <el-table-column prop="部件" label="部件" width="100" />
          <el-table-column prop="故障模式" label="故障模式" width="110" />
          <el-table-column prop="异常状态" label="异常状态" width="110" />
          <el-table-column prop="原因" label="原因" width="100" />
          <el-table-column prop="维修动作" label="维修动作" width="120" />
          <el-table-column prop="置信度" label="置信度" width="80" align="center" />
          <el-table-column prop="版本状态" label="版本状态" width="90" align="center">
            <template #default="{ row }"><el-tag :type="row['版本状态'] === 'active' ? 'success' : 'info'" size="small">{{ row['版本状态'] || 'active' }}</el-tag></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="证据管理" name="evidence">
        <el-table :data="filtered(evidenceData)" border stripe size="small" max-height="450">
          <el-table-column prop="证据编号" label="证据编号" width="130" v-if="false" />
          <el-table-column prop="evidence_id" label="证据编号" width="130" />
          <el-table-column prop="event_id" label="事件编号" width="100" />
          <el-table-column prop="来源编号" label="来源编号" width="130" v-if="false" />
          <el-table-column prop="来源文件" label="来源编号" width="140" />
          <el-table-column prop="段落编号" label="段落编号" width="80" v-if="false" />
          <el-table-column prop="起始位置" label="段落编号" width="80" />
          <el-table-column prop="证据原文" label="证据原文" min-width="250" show-overflow-tooltip v-if="false" />
          <el-table-column prop="原文片段" label="证据原文" min-width="250" show-overflow-tooltip />
          <el-table-column prop="可靠度" label="可靠度" width="80" align="center">
            <template #default="{ row }"><el-tag :type="(row['可靠度']||'中')==='高'?'success':(row['可靠度']||'中')==='低'?'danger':'warning'" size="small">{{ row['可靠度'] || '中' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="审核状态" label="审核状态" width="90" align="center" v-if="false">
            <template #default="{ row }"><el-tag :type="row['审核状态']==='已通过'?'success':'info'" size="small">{{ row['审核状态'] || '待审核' }}</el-tag></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="机理模板" name="templates">
        <el-table :data="filtered(templatesData)" border stripe size="small" max-height="450">
          <el-table-column prop="template_id" label="模板编号" width="100" />
          <el-table-column prop="模板名称" label="模板名称" width="100" />
          <el-table-column prop="模板描述" label="中文链式模式" min-width="250" show-overflow-tooltip />
          <el-table-column prop="适用事件类型" label="适用部件" width="120" />
          <el-table-column prop="物理约束" label="校验规则" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="事件关系" name="relations">
        <el-table :data="filtered(relationsData)" border stripe size="small" max-height="450">
          <el-table-column prop="source_event_id" label="源事件" width="100" />
          <el-table-column prop="关系类型" label="关系类型" width="120">
            <template #default="{ row }"><el-tag size="small">{{ row['关系类型'] }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="target_event_id" label="目标事件" width="100" />
          <el-table-column prop="关系描述" label="模板编号" width="200" show-overflow-tooltip />
          <el-table-column prop="置信度" label="置信度" width="80" align="center" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="版本日志" name="versions">
        <el-table :data="filtered(versionsData)" border stripe size="small" max-height="450">
          <el-table-column prop="log_id" label="版本编号" width="130" />
          <el-table-column prop="实体类型" label="事件编号" width="120" v-if="false" />
          <el-table-column prop="实体ID" label="实体ID" width="100" />
          <el-table-column prop="操作类型" label="操作类型" width="100">
            <template #default="{ row }"><el-tag :type="row['操作类型']==='更新'?'warning':'info'" size="small">{{ row['操作类型'] }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="新值JSON" label="新值" min-width="200" show-overflow-tooltip />
          <el-table-column prop="操作时间" label="观察时间" width="160" />
          <el-table-column label="冲突标记" width="90" align="center">
            <template #default="{ row }"><el-tag :type="row['冲突标记'] ? 'danger' : 'success'" size="small">{{ row['冲突标记'] ? '有冲突' : '无冲突' }}</el-tag></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="问答记录" name="qa">
        <el-table :data="filtered(qaRecordsData)" border stripe size="small" max-height="450">
          <el-table-column prop="session_id" label="会话编号" width="140" />
          <el-table-column prop="用户问题" label="用户问题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="模型回答" label="检索事件链" min-width="200" show-overflow-tooltip>
            <template #default="{ row }"><span style="font-size:12px">{{ (row['模型回答'] || '').slice(0, 80) }}</span></template>
          </el-table-column>
          <el-table-column prop="检索证据JSON" label="命中模板" width="120" show-overflow-tooltip />
          <el-table-column prop="创建时间" label="创建时间" width="160" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="导入文件" name="import">
        <el-table :data="filtered(importFilesData)" border stripe size="small" max-height="450">
          <el-table-column prop="文件编号" label="文件编号" width="140" v-if="false" />
          <el-table-column prop="file_id" label="文件编号" width="140" />
          <el-table-column prop="文件名" label="文件名称" min-width="150" show-overflow-tooltip />
          <el-table-column prop="文件类型" label="文件类型" width="80" />
          <el-table-column prop="上传时间" label="上传时间" width="160" />
          <el-table-column prop="处理状态" label="解析状态" width="100">
            <template #default="{ row }"><el-tag :type="row['处理状态']==='已分析'?'success':'info'" size="small">{{ row['处理状态'] || '待分析' }}</el-tag></template>
          </el-table-column>
          <el-table-column label="是否已入图谱" width="110" align="center">
            <template #default="{ row }"><el-tag :type="row['是否入图谱'] ? 'success' : 'warning'" size="small">{{ row['是否入图谱'] ? '已入图谱' : '未入图谱' }}</el-tag></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getSources, getFilteredParagraphs, getExtractionEvents, getExtractionEvidence,
  getAdminTemplates, getAdminVersionLogs, getAdminSummary,
  getUploadedFiles, getAnalysisResults,
} from '@/api/kgApi'
import request from '@/api/request'

const activeTab = ref('sources')
const searchKeyword = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const loading = ref(false)

const eventTypes = ['故障事件', '状态事件', '检测事件', '维修事件', '传播事件', '证据事件']

// 数据
const sourcesData = ref<any[]>([])
const paragraphsData = ref<any[]>([])
const eventsData = ref<any[]>([])
const evidenceData = ref<any[]>([])
const templatesData = ref<any[]>([])
const relationsData = ref<any[]>([])
const versionsData = ref<any[]>([])
const qaRecordsData = ref<any[]>([])
const importFilesData = ref<any[]>([])

const stats = ref([
  { label: '来源', value: '—', tab: 'sources' },
  { label: '段落', value: '—', tab: 'paragraphs' },
  { label: '事件', value: '—', tab: 'events' },
  { label: '证据', value: '—', tab: 'evidence' },
  { label: '模板', value: '—', tab: 'templates' },
  { label: '关系', value: '—', tab: 'relations' },
  { label: '版本', value: '—', tab: 'versions' },
  { label: '问答', value: '—', tab: 'qa' },
])

const showTypeFilter = computed(() => activeTab.value === 'events')
const showStatusFilter = computed(() => activeTab.value === 'events' || activeTab.value === 'versions')

function evtTypeTag(t: string) {
  const m: Record<string, string> = { '故障事件': 'danger', '状态事件': 'warning', '检测事件': 'info', '维修事件': 'success', '传播事件': '', '证据事件': '' }
  return m[t] || 'info'
}

// 搜索过滤
function filtered(data: any[]) {
  if (!searchKeyword.value) return applyFilters(data)
  const kw = searchKeyword.value.toLowerCase()
  return applyFilters(data).filter((row: any) => {
    return Object.values(row).some(v => String(v || '').toLowerCase().includes(kw))
  })
}

function applyFilters(data: any[]) {
  let d = data
  if (typeFilter.value && activeTab.value === 'events') {
    d = d.filter((r: any) => r['事件类型'] === typeFilter.value || r['event_type'] === typeFilter.value)
  }
  if (statusFilter.value) {
    d = d.filter((r: any) => {
      const vs = r['版本状态'] || r['version_status'] || ''
      return vs === statusFilter.value
    })
  }
  return d
}

async function onTabChange(tab: any) {
  searchKeyword.value = ''
  typeFilter.value = ''
  statusFilter.value = ''
  await loadCurrentTab()
}

async function loadCurrentTab() {
  loading.value = true
  try {
    switch (activeTab.value) {
      case 'sources': {
        const res: any = await getSources()
        sourcesData.value = res['来源列表'] || res.sources || res || []
        break
      }
      case 'paragraphs': {
        const res: any = await getFilteredParagraphs()
        paragraphsData.value = res['过滤后段落'] || res.data || []
        break
      }
      case 'events': {
        const res: any = await getExtractionEvents()
        const raw = res['事件列表'] || res.events || []
        // Parse 论元JSON into top-level fields
        eventsData.value = raw.map((ev: any) => {
          try {
            const args = typeof ev['论元JSON'] === 'string' ? JSON.parse(ev['论元JSON']) : (ev['论元JSON'] || ev.properties || {})
            return {
              ...ev,
              事件编号: ev['event_id'] || ev['事件编号'],
              部件: args['部件'] || ev['部件'] || '',
              故障模式: args['故障模式'] || ev['故障模式'] || '',
              异常状态: args['异常状态'] || ev['异常状态'] || '',
              原因: args['原因'] || ev['原因'] || '',
              维修动作: args['维修动作'] || ev['维修动作'] || '',
              事件触发词: ev['事件触发词'] || ev['trigger'] || '',
              版本状态: ev['版本状态'] || 'active',
            }
          } catch { return ev }
        })
        break
      }
      case 'evidence': {
        const res: any = await getExtractionEvidence()
        evidenceData.value = (res['证据列表'] || res.evidence_list || []).map((evd: any) => ({
          ...evd,
          证据编号: evd['evidence_id'] || evd['证据编号'],
          原文片段: evd['原文片段'] || evd['证据原文'] || '',
          可靠度: evd['可靠度'] || '中',
        }))
        break
      }
      case 'templates': {
        const res: any = await getAdminTemplates()
        templatesData.value = res['模板列表'] || res.templates || []
        break
      }
      case 'relations': {
        const res: any = await request.get('/api/admin/relations')
        relationsData.value = (res as any)['关系列表'] || (res as any).relations || []
        break
      }
      case 'versions': {
        const res: any = await getAdminVersionLogs()
        versionsData.value = (res['版本日志列表'] || res.version_logs || []).map((v: any) => ({
          ...v,
          冲突标记: v['冲突标记'] || (v['操作类型'] === '更新'),
        }))
        break
      }
      case 'qa': {
        const res: any = await request.get('/api/admin/qa-records')
        qaRecordsData.value = (res as any)['问答记录'] || (res as any)['qa_records'] || []
        break
      }
      case 'import': {
        const [filesRes, resultsRes] = await Promise.all([getUploadedFiles(), getAnalysisResults()])
        const files = (filesRes as any)['文件列表'] || []
        const results = (resultsRes as any)['分析结果列表'] || []
        importFilesData.value = files.map((f: any) => {
          const r = results.find((r2: any) => r2['file_id'] === f['file_id'])
          return {
            ...f,
            文件编号: f['file_id'],
            文件名: f['文件名'] || f['文件名称'],
            是否入图谱: r ? (r['是否加入图谱'] || 0) : 0,
          }
        })
        break
      }
    }
  } catch (e: any) {
    console.error('Load tab error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadCurrentTab()
  // Load summary stats
  try {
    const res: any = await getAdminSummary()
    const counts = res['各表行数'] || res.counts || {}
    stats.value[0].value = String(counts['sources'] || sourcesData.value.length || '—')
    stats.value[1].value = String(counts['filtered_paragraphs'] || paragraphsData.value.length || '—')
    stats.value[2].value = String(counts['events'] || '—')
    stats.value[3].value = String(counts['evidence'] || '—')
    stats.value[4].value = String(counts['mechanism_templates'] || '—')
    stats.value[5].value = String(counts['event_relations'] || '—')
    stats.value[6].value = String(counts['version_logs'] || '—')
    stats.value[7].value = String(counts['qa_records'] || '—')
  } catch { /* ignore */ }
})
</script>

<style scoped>
.admin-page { padding: 10px; }
.subtitle { color: #909399; font-size: 13px; margin-bottom: 16px; }
.stat-mini { text-align: center; cursor: pointer; }
.stat-mini:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.stat-num { font-size: 24px; font-weight: 700; color: #409EFF; }
.stat-lbl { font-size: 11px; color: #909399; margin-top: 4px; }
</style>
