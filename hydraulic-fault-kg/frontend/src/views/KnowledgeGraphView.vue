<template>
  <div class="kg-page report-screen big-font-page">
    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="3" v-for="card in statsCards" :key="card.label">
        <div class="stat-card" :style="{ borderTopColor: card.color }">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="17">
        <div class="graph-panel">
          <div class="panel-header">
            <span class="panel-title">液压伺服阀故障维修知识图谱</span>
            <div class="panel-actions">
              <el-button-group size="small">
                <el-button v-for="t in filterTemplates" :key="t.id"
                  :type="activeChain === t.id ? 'danger' : ''"
                  @click="highlightChain(t.id)">{{ t.id }} {{ t.name }}</el-button>
              </el-button-group>
              <el-checkbox v-model="showOrphans" size="small" style="margin-left:8px">孤立节点</el-checkbox>
              <el-button size="small" @click="resetView">重置</el-button>
              <el-button size="small" type="primary" @click="loadAllData">刷新</el-button>
            </div>
          </div>
          <div class="chart-container" ref="chartRef"></div>
          <div class="legend-bar">
            <span class="legend-item" v-for="leg in legends" :key="leg.name">
              <i class="legend-dot" :style="{ background: leg.color }"></i>{{ leg.name }}
            </span>
          </div>
        </div>
      </el-col>

      <el-col :span="7">
        <div class="detail-panel">
          <div class="panel-header">
            <span class="panel-title">{{ selectedEdge ? '边详情（三元组证据）' : '节点详情' }}</span>
            <el-tag v-if="selectedNode && !selectedEdge" size="small" :type="getTagType(selectedNode.category_zh)">
              {{ selectedNode.category_zh || selectedNode.node_type_zh }}
            </el-tag>
            <el-tag v-if="selectedEdge" size="small" type="warning">{{ selectedEdge.relation_zh }}</el-tag>
          </div>

          <div v-if="!selectedNode && !selectedEdge" class="detail-empty">
            <el-icon :size="48" color="#d9e1e8"><Aim /></el-icon>
            <p>点击节点查看节点详情<br/>点击边查看三元组证据</p>
          </div>

          <!-- 节点详情 -->
          <div v-if="selectedNode && !selectedEdge" class="detail-body">
            <div class="detail-section">
              <div class="detail-section-title">节点信息</div>
              <div class="detail-row"><span class="dk">名称</span><span class="dv accented">{{ selectedNode.name }}</span></div>
              <div class="detail-row"><span class="dk">类型</span><span class="dv">{{ selectedNode.category_zh || '—' }}</span></div>
              <div class="detail-row"><span class="dk">来源</span>
                <el-tag :type="selectedNode.node_source === '机理模板补全' ? 'warning' : 'success'" size="small">
                  {{ selectedNode.node_source || '—' }}
                </el-tag>
              </div>
              <div class="detail-row"><span class="dk">证据数</span><span class="dv">{{ selectedNode.证据数量 || 0 }}</span></div>
              <div class="detail-row"><span class="dk">关联三元组</span><span class="dv">{{ selectedNode.关联三元组数量 || 0 }}</span></div>
              <div class="detail-row"><span class="dk">置信度</span><span class="dv">{{ fmtConf(selectedNode.置信度) }}</span></div>
            </div>
            <div class="detail-section" v-if="selectedNode.matched_template_ids?.length">
              <div class="detail-section-title">匹配模板</div>
              <el-tag v-for="tid in selectedNode.matched_template_ids" :key="tid" size="small" type="warning" style="margin:2px">{{ tid }}</el-tag>
            </div>
            <div class="detail-section" v-if="selectedNode.source_titles?.length">
              <div class="detail-section-title">来源资料</div>
              <div v-for="(t,i) in selectedNode.source_titles" :key="i" class="source-item">{{ i+1 }}. {{ t }}</div>
            </div>
            <div class="detail-section" v-if="selectedNode.paragraph_ids?.length">
              <div class="detail-section-title">段落编号</div>
              <span>{{ selectedNode.paragraph_ids.join(', ') }}</span>
            </div>
            <div class="detail-section" v-if="selectedNode.evidence_texts?.length">
              <div class="detail-section-title">证据原文</div>
              <div v-for="(et,i) in selectedNode.evidence_texts.slice(0,3)" :key="i" class="evidence-item">
                <div class="evidence-text">{{ et.slice(0, 300) }}</div>
              </div>
            </div>
            <div class="detail-section" v-if="selectedNode.说明">
              <el-alert type="warning" :closable="false" :title="selectedNode.说明" />
            </div>
          </div>

          <!-- 边详情 -->
          <div v-if="selectedEdge" class="detail-body">
            <div class="detail-section">
              <div class="detail-section-title">三元组</div>
              <div class="triple-display">
                <span class="triple-subj">{{ selectedEdge.source_name }}</span>
                <span class="triple-pred">{{ selectedEdge.relation_zh }}</span>
                <span class="triple-obj">{{ selectedEdge.target_name }}</span>
              </div>
            </div>
            <div class="detail-section">
              <div class="detail-section-title">边来源</div>
              <el-tag :type="selectedEdge.edge_source === '机理模板补全' ? 'warning' : 'success'" size="small">
                {{ selectedEdge.edge_source || '—' }}
              </el-tag>
            </div>
            <div class="detail-section" v-if="selectedEdge.source_titles?.length">
              <div class="detail-section-title">来源资料</div>
              <div v-for="(t,i) in selectedEdge.source_titles" :key="i" class="source-item">{{ t }}</div>
            </div>
            <div class="detail-section" v-if="selectedEdge.evidence_texts?.length">
              <div class="detail-section-title">证据原文</div>
              <div v-for="(et,i) in selectedEdge.evidence_texts.slice(0,3)" :key="i" class="evidence-item">
                <div class="evidence-text">{{ et.slice(0, 300) }}</div>
              </div>
            </div>
            <div class="detail-section" v-if="selectedEdge.evidence_spans?.length">
              <div class="detail-section-title">证据片段</div>
              <div v-for="(es,i) in selectedEdge.evidence_spans.slice(0,3)" :key="i" class="evidence-item">
                <div class="evidence-text">{{ es }}</div>
              </div>
            </div>
            <div class="detail-section" v-if="selectedEdge.说明">
              <el-alert type="warning" :closable="false" :title="selectedEdge.说明" />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- T1-T6 链 -->
    <div class="chains-panel">
      <div class="panel-header">
        <span class="panel-title">T1-T6 机理模板故障演化链</span>
        <span style="font-size:12px;color:#909399">模板用于校验三元组和补全缺失关系，不是原始数据来源</span>
      </div>
      <el-row :gutter="12">
        <el-col :span="4" v-for="chain in faultChains" :key="chain.id">
          <div class="chain-card" :class="{ active: activeChain === chain.id }"
            :style="{ borderLeftColor: chain.color }" @click="highlightChain(chain.id)">
            <div class="chain-id" :style="{ color: chain.color }">{{ chain.id }} {{ chain.name }}</div>
            <div class="chain-steps">
              <div v-for="step in chain.steps" :key="step.label" class="chain-step">
                <span class="chain-step-dot" :style="{ background: step.color }"></span>
                <span class="chain-step-text">{{ step.label }}</span>
              </div>
            </div>
            <div class="chain-constraint">{{ chain.constraint }}</div>
            <div v-if="chain.linksEmpty" class="chain-warning">
              ⚠ 该链条没有关系边，请检查机理模板补边或三元组抽取结果。
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { getKGGraph, getGraphChains } from '@/api/kgApi'
import { ElMessage } from 'element-plus'

const NODE_COLORS: Record<string, string> = {
  '部件': '#9B59B6', '故障模式': '#E74C3C', '异常状态': '#F39C12',
  '检测方式': '#3498DB', '维修动作': '#2ECC71', '机理模板': '#1ABC9C',
  '证据来源': '#95A5A6', '影响结果': '#E91E63',
}

const legends = [
  { name: '故障模式', color: '#E74C3C' }, { name: '异常状态', color: '#F39C12' },
  { name: '检测方式', color: '#3498DB' }, { name: '维修动作', color: '#2ECC71' },
  { name: '部件', color: '#9B59B6' }, { name: '机理模板', color: '#1ABC9C' },
]

const filterTemplates = [
  { id: 'T1', name: '污染卡滞链' }, { id: 'T2', name: '喷嘴堵塞链' },
  { id: 'T3', name: '气隙偏差链' }, { id: 'T4', name: '力矩马达异常链' },
  { id: 'T5', name: '密封内泄漏链' }, { id: 'T6', name: '线圈发热链' },
]

const chartRef = ref<HTMLElement>()
const selectedNode = ref<any>(null)
const selectedEdge = ref<any>(null)
const activeChain = ref<string | null>(null)
const showOrphans = ref(false)
const chainsData = ref<any[]>([])

let chart: echarts.ECharts | null = null
let allGraphData: any = null
let allNodesFull: any[] = []
let allLinksFull: any[] = []

const statsCards = ref([
  { label: '图谱节点', value: '--', color: '#1ABC9C' },
  { label: '图谱边', value: '--', color: '#E74C3C' },
  { label: '公开资料抽取', value: '--', color: '#2ECC71' },
  { label: '模板补全', value: '--', color: '#F39C12' },
  { label: '证据覆盖率', value: '--', color: '#3498DB' },
  { label: '孤立节点', value: '--', color: '#E91E63' },
])

const faultChains = ref([
  { id: 'T1', name: '污染卡滞链', color: '#E74C3C', linksEmpty: false,
    steps: [{ label: '油液污染', color: '#E74C3C' }, { label: '阀芯卡滞', color: '#E74C3C' },
    { label: '流量控制异常', color: '#F39C12' }, { label: '压力波动', color: '#F39C12' },
    { label: '响应迟缓', color: '#F39C12' }], constraint: '污染→卡滞→流量异常→压力波动' },
  { id: 'T2', name: '喷嘴堵塞链', color: '#F39C12', linksEmpty: false,
    steps: [{ label: '喷嘴污染', color: '#E74C3C' }, { label: '喷嘴堵塞', color: '#E74C3C' },
    { label: '压差异常', color: '#F39C12' }, { label: '阀芯偏移异常', color: '#F39C12' },
    { label: '流量输出异常', color: '#F39C12' }], constraint: '污染→堵塞→压差异常→阀芯偏移' },
  { id: 'T3', name: '气隙偏差链', color: '#3498DB', linksEmpty: false,
    steps: [{ label: '气隙不对称', color: '#E74C3C' }, { label: '磁路不平衡', color: '#F39C12' },
    { label: '零位漂移', color: '#F39C12' }, { label: '输出偏差', color: '#F39C12' }],
    constraint: '气隙不对称→磁路不平衡→零位漂移' },
  { id: 'T4', name: '力矩马达异常链', color: '#9B59B6', linksEmpty: false,
    steps: [{ label: '力矩马达异常', color: '#E74C3C' }, { label: '电磁力矩波动', color: '#F39C12' },
    { label: '衔铁偏移', color: '#F39C12' }, { label: '零位漂移', color: '#F39C12' }],
    constraint: '马达异常→力矩波动→衔铁偏移→漂移' },
  { id: 'T5', name: '密封内泄漏链', color: '#1ABC9C', linksEmpty: false,
    steps: [{ label: '密封失效', color: '#E74C3C' }, { label: '内泄漏', color: '#F39C12' },
    { label: '压力下降', color: '#F39C12' }, { label: '流量损失', color: '#F39C12' },
    { label: '响应迟缓', color: '#F39C12' }], constraint: '密封失效→内泄漏→压力下降→迟缓' },
  { id: 'T6', name: '线圈发热链', color: '#E91E63', linksEmpty: false,
    steps: [{ label: '线圈发热异常', color: '#E74C3C' }, { label: '电流异常', color: '#F39C12' },
    { label: '电磁力矩波动', color: '#F39C12' }, { label: '输出不稳定', color: '#F39C12' }],
    constraint: '线圈发热→电流异常→力矩波动→不稳定' },
])

function getTagType(cat: string): string {
  const map: Record<string, string> = { '故障模式': 'danger', '异常状态': 'warning', '检测方式': '', '维修动作': 'success', '部件': '', '机理模板': 'success' }
  return map[cat] || 'info'
}

function fmtConf(v: any): string { const n = Number(v); return isNaN(n) ? '—' : (n * 100).toFixed(1) + '%' }

async function loadAllData() {
  try {
    const res: any = await getKGGraph()
    allGraphData = res
    allNodesFull = res?.nodes || []
    allLinksFull = res?.links || []
    console.log('KG:', allNodesFull.length, 'nodes,', allLinksFull.length, 'links')

    const publicNodes = allNodesFull.filter((n: any) => n.node_source === '公开资料抽取' || n.node_source === '多来源融合').length
    const tplNodes = allNodesFull.filter((n: any) => n.node_source === '机理模板补全').length
    const nodesWithEv = allNodesFull.filter((n: any) => n.evidence_texts?.length > 0).length
    const coverage = allNodesFull.length > 0 ? Math.round((nodesWithEv / allNodesFull.length) * 100) : 0

    statsCards.value = [
      { label: '图谱节点', value: String(allNodesFull.length), color: '#1ABC9C' },
      { label: '图谱边', value: String(allLinksFull.length), color: '#E74C3C' },
      { label: '公开资料抽取', value: String(publicNodes), color: '#2ECC71' },
      { label: '模板补全', value: String(tplNodes), color: '#F39C12' },
      { label: '证据覆盖率', value: coverage + '%', color: '#3498DB' },
      { label: 'T1-T6链条', value: '6', color: '#9B59B6' },
    ]

    try {
      const cr: any = await getGraphChains()
      chainsData.value = cr?.事件链列表 || cr || []
      // 检查每条链的links是否为空
      chainsData.value.forEach((ch: any) => {
        const fc = faultChains.value.find(f => f.id === ch.template_id)
        if (fc) fc.linksEmpty = !ch.chain_links || ch.chain_links.length === 0
      })
    } catch { /* ignore */ }

    renderGraph(allNodesFull, allLinksFull)
  } catch (e: any) {
    ElMessage.error('加载图谱失败: ' + (e?.message || String(e)))
  }
}

function renderGraph(nodes: any[], links: any[]) {
  if (!chartRef.value) return
  if (!chart) try { chart = echarts.init(chartRef.value) } catch (e) { return }
  chart.clear()

  if (!nodes.length) { ElMessage.warning('图谱节点为空，请先执行图谱构建'); return }

  const nodeIdSet = new Set<string>()
  for (const n of nodes) { const id = String(n.id || n.name); nodeIdSet.add(id) }

  const validLinks: any[] = []
  for (const l of links) {
    const src = String(l.source), tgt = String(l.target)
    if (nodeIdSet.has(src) && nodeIdSet.has(tgt)) validLinks.push({ ...l, _src: src, _tgt: tgt })
  }

  const catNames = [...new Set(nodes.map((n: any) => n.category_zh || n.node_type_zh || '其他'))]
  const catIndex = new Map<string, number>()
  const categories = catNames.map((cn, i) => { catIndex.set(cn, i); return { name: cn, itemStyle: { color: NODE_COLORS[cn] || '#95A5A6' } } })

  const chartNodes = nodes.map((n: any) => {
    const cat = n.category_zh || n.node_type_zh || '其他'
    const isTemplate = n.node_source === '机理模板补全'
    return {
      id: String(n.id || n.name), name: String(n.id || n.name),
      displayName: n.label_zh || n.name || n.id,
      category: catIndex.get(cat) ?? 0,
      symbolSize: isTemplate ? 20 : (Number(n.symbolSize) || 24),
      itemStyle: n.itemStyle || { color: NODE_COLORS[cat] || '#95A5A6' },
      raw: n, _node_source: n.node_source || '', _evidence_count: n.证据数量 || 0,
      _triple_count: n.关联三元组数量 || 0, _templates: n.matched_template_ids || [],
    }
  })

  const chartLinks = validLinks.map((l: any) => ({
    source: l._src, target: l._tgt,
    value: l.relation_zh || '', label: { show: true, fontSize: 11, formatter: l.relation_zh || '' },
    lineStyle: l.lineStyle || { color: '#95A5A6', width: 1.5, opacity: 0.7, curveness: 0.08 },
    _relation_zh: l.relation_zh || '', _edge_source: l.edge_source || '',
    _evidence_count: (l.evidence_texts || []).length, _evidence_span: (l.evidence_spans || []).slice(0, 2),
    raw: l,
  }))

  const option: any = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          const s = params.data._edge_source || ''
          return `<strong>${params.data._relation_zh || params.data.value}</strong><br/>${s}<br/>证据: ${params.data._evidence_count || 0}`
        }
        const r = (params.data as any)?.raw || {}
        return `<strong>${r.label_zh || r.name || ''}</strong><br/>类型: ${r.node_type_zh || r.category_zh || ''}<br/>来源: ${r.node_source || ''}<br/>证据: ${r.证据数量 || 0}<br/>三元组: ${r.关联三元组数量 || 0}`
      },
      backgroundColor: 'rgba(48,65,86,0.95)', borderColor: '#304156', textStyle: { color: '#fff', fontSize: 14 },
    },
    legend: [{ data: categories.map(c => c.name), bottom: 0, textStyle: { fontSize: 14, color: '#606266' }, itemWidth: 14, itemHeight: 14, itemGap: 16 }],
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true, categories,
      data: chartNodes, links: chartLinks,
      force: { initIterations: 200, repulsion: 500, edgeLength: [80, 180], gravity: 0.08, friction: 0.1 },
      label: { show: true, fontSize: 15, color: '#303133', formatter: (p: any) => { const n = p.data?.displayName || ''; return n.length > 14 ? n.slice(0,13)+'…' : n } },
      edgeLabel: { show: true, fontSize: 11, formatter: (p: any) => (p.data?.value || '').length > 6 ? (p.data?.value||'').slice(0,5)+'…' : (p.data?.value||'') },
      emphasis: { focus: 'adjacency', lineStyle: { width: 4 }, itemStyle: { shadowBlur: 20 } },
      lineStyle: { curveness: 0.08, opacity: 0.7 },
    }],
  }

  try { chart.setOption(option, true) } catch (e: any) { ElMessage.error('渲染失败: ' + e?.message) }

  chart.off('click')
  chart.on('click', (params: any) => {
    if (params.dataType === 'node' && params.data) {
      const raw = params.data.raw || {}
      selectedEdge.value = null
      selectedNode.value = { id: params.data.id, name: params.data.displayName || raw.label_zh || params.data.name, category_zh: raw.category_zh || raw.node_type_zh || '', node_type_zh: raw.node_type_zh || raw.category_zh || '', node_source: raw.node_source || '', source_titles: raw.source_titles || [], source_ids: raw.source_ids || [], evidence_texts: raw.evidence_texts || [], paragraph_ids: raw.paragraph_ids || [], 证据数量: raw.证据数量 || 0, 关联三元组数量: raw.关联三元组数量 || 0, 置信度: raw.置信度 || 0, matched_template_ids: raw.matched_template_ids || [], 说明: raw.说明 || '' }
    } else if (params.dataType === 'edge' && params.data) {
      const raw = params.data.raw || {}
      selectedNode.value = null
      selectedEdge.value = { id: raw.id || '', source_name: raw.source_name || '', target_name: raw.target_name || '', relation_zh: raw.relation_zh || '', edge_source: raw.edge_source || '', source_titles: raw.source_titles || [], evidence_texts: raw.evidence_texts || [], evidence_spans: raw.evidence_spans || [], 说明: raw.说明 || '' }
    }
  })
  chart.getZr().off('click')
  chart.getZr().on('click', (p: any) => { if (!p.target) { selectedNode.value = null; selectedEdge.value = null } })
}

function highlightChain(tid: string) {
  if (activeChain.value === tid) { resetView(); return }
  activeChain.value = tid

  const chainData = chainsData.value?.find((c: any) => c.template_id === tid)
  if (!chainData) {
    ElMessage.warning(`链条 ${tid} 数据不存在，请检查 chains.json`)
    return
  }
  if (!chainData.chain_links || chainData.chain_links.length === 0) {
    ElMessage.error(`链条 ${tid} chain_links为空，请检查mechanism_validation_service`)
    return
  }

  // Strategy 1: Filter links by matching chain_links IDs directly against link.id
  const chainLinkIds: Set<string> = new Set((chainData.chain_links || []).map((s: string) => String(s)))
  let chainLinks = allLinksFull.filter((l: any) => chainLinkIds.has(String(l.id || '')))

  // Strategy 2: If no match, try matched_template_ids
  if (chainLinks.length === 0) {
    chainLinks = allLinksFull.filter((l: any) => {
      return (l.matched_template_ids || []).includes(tid)
    })
  }

  // Strategy 3: Fall back to source/target both in chain_nodes
  if (chainLinks.length === 0) {
    const chainNodes = new Set((chainData.chain_nodes || []).map((s: string) => String(s).trim()))
    chainLinks = allLinksFull.filter((l: any) => {
      return chainNodes.has(String(l.source || '').trim()) && chainNodes.has(String(l.target || '').trim())
    })
  }

  if (chainLinks.length === 0) {
    ElMessage.error(`链条 ${tid} 没有匹配到任何边。chain_links=${chainData.chain_links?.length}条，links总数=${allLinksFull.length}条。请检查chain_links中的边ID是否与links.json一致。`)
    return
  }

  // Build visible node set from matched chain links + chain_nodes
  const chainNodesSet = new Set((chainData.chain_nodes || []).map((s: string) => String(s).trim()))
  chainLinks.forEach((l: any) => {
    chainNodesSet.add(String(l.source || '').trim())
    chainNodesSet.add(String(l.target || '').trim())
  })

  const highlightedNodes = allNodesFull.map((n: any) => {
    const nid = String(n.id || n.name || '').trim()
    const inChain = chainNodesSet.has(nid)
    return {
      ...n,
      itemStyle: { color: inChain ? (NODE_COLORS[n.category_zh || '故障模式'] || '#E74C3C') : '#e0e0e0', borderColor: inChain ? '#E74C3C' : 'transparent', borderWidth: inChain ? 3 : 0, opacity: inChain ? 1 : 0.04 },
      symbolSize: inChain ? 36 : 10,
    }
  })

  const highlightedLinks = chainLinks.map((l: any) => ({
    ...l,
    lineStyle: { color: '#E74C3C', width: 3, opacity: 1 },
  }))

  renderGraph(highlightedNodes, highlightedLinks)
}

function resetView() {
  activeChain.value = null
  selectedNode.value = null; selectedEdge.value = null
  renderGraph(allNodesFull, allLinksFull)
}

onMounted(() => { loadAllData() })
onUnmounted(() => { chart?.dispose() })
</script>

<style scoped>
.kg-page { max-width: 1400px; margin: 0 auto; }
.stat-card { background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); padding: 16px; text-align: center; border-top: 4px solid #1a3a5c; }
.stat-card:hover { transform: translateY(-2px); }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.graph-panel { background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); overflow: hidden; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; border-bottom: 1px solid #ebeef5; background: #fafbfc; }
.panel-title { font-size: 15px; font-weight: 700; color: #304156; border-left: 3px solid #E74C3C; padding-left: 10px; }
.panel-actions { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.chart-container { width: 100%; height: 620px; }
.legend-bar { display: flex; flex-wrap: wrap; gap: 14px; padding: 8px 20px; border-top: 1px solid #ebeef5; background: #fafbfc; }
.legend-item { display: flex; align-items: center; font-size: 11px; color: #606266; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }
.detail-panel { background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); height: 698px; display: flex; flex-direction: column; overflow: hidden; }
.detail-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #c0c4cc; }
.detail-body { flex: 1; overflow-y: auto; padding: 12px; }
.detail-section { margin-bottom: 14px; }
.detail-section-title { font-size: 13px; font-weight: 700; color: #304156; padding-bottom: 6px; border-bottom: 1px dashed #d9e1e8; margin-bottom: 8px; }
.detail-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; }
.dk { color: #909399; margin-right: 8px; }
.dv { color: #303133; text-align: right; }
.dv.accented { color: #E74C3C; font-weight: 600; }
.triple-display { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 10px; background: #f5f7fa; border-radius: 6px; }
.triple-subj { color: #E74C3C; font-weight: 600; }
.triple-pred { color: #3498DB; font-weight: 600; background: #e8f4fd; padding: 2px 8px; border-radius: 10px; }
.triple-obj { color: #2ECC71; font-weight: 600; }
.source-item { font-size: 12px; color: #606266; padding: 2px 0; }
.evidence-item { padding: 8px; background: #f5f7fa; border-radius: 4px; border-left: 3px solid #3498DB; margin-bottom: 6px; }
.evidence-text { font-size: 12px; color: #606266; line-height: 1.5; }
.chains-panel { background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-top: 16px; }
.chain-card { padding: 12px; border-left: 4px solid #E74C3C; background: #fafbfc; border-radius: 0 6px 6px 0; cursor: pointer; margin: 4px; height: 100%; }
.chain-card:hover { background: #f0f5fa; }
.chain-card.active { background: #e8f0f8; border-left-width: 6px; }
.chain-id { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.chain-steps { margin-bottom: 6px; }
.chain-step { display: flex; align-items: center; padding: 2px 0; }
.chain-step-dot { width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
.chain-step-text { font-size: 11px; color: #606266; }
.chain-constraint { font-size: 10px; color: #909399; margin-top: 4px; font-style: italic; }
.chain-warning { font-size: 10px; color: #E74C3C; margin-top: 6px; font-weight: 600; }
</style>
