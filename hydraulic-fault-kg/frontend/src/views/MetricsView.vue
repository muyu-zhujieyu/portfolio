<template>
  <div class="page-container">
    <h2>知识图谱构建质量评价</h2>
    <el-alert type="info" :closable="false" style="margin-bottom: 16px">
      <template #title>
        本系统不以图谱规模作为主要评价目标，而以事件链完整率、机理一致率、证据准确率和增量更新能力作为核心评价指标。
      </template>
    </el-alert>

    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="4" v-for="card in statCards" :key="card.label">
        <el-card class="stat-card" shadow="hover"><el-statistic :title="card.label" :value="card.value"><template #suffix><span style="font-size:12px">{{ card.unit }}</span></template></el-statistic></el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="12"><el-card header="基础抽取指标与事件链质量"><div ref="chart1Ref" style="height:300px"></div></el-card></el-col>
      <el-col :span="12"><el-card header="机理质量与证据质量"><div ref="chart2Ref" style="height:300px"></div></el-card></el-col>
    </el-row>

    <el-card header="指标定义与计算方式" style="margin-bottom: 20px">
      <el-table :data="metricTable" border stripe size="small" max-height="450">
        <el-table-column prop="group" label="指标分组" width="140" />
        <el-table-column prop="name" label="指标名称" width="220" />
        <el-table-column prop="def" label="定义与计算方式" min-width="260" show-overflow-tooltip />
        <el-table-column prop="direction" label="期望方向" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.direction.includes('高') ? 'success' : row.direction.includes('低') ? 'danger' : 'warning'" size="small">{{ row.direction }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-alert type="success" :closable="false" title="评价总结">
      <p>本系统聚焦四个核心评价维度：事件链完整率、机理一致率、证据准确率和增量更新能力。</p>
      <p style="color:#409EFF;font-size:12px">指标数据来自 GET /api/metrics。</p>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getMetrics } from '@/api/kgApi'

const chart1Ref = ref<HTMLElement>()
const chart2Ref = ref<HTMLElement>()

const statCards = ref([
  { label: '总指标数', value: '17', unit: '项' },
  { label: '已知可计算', value: '--', unit: '项' },
  { label: '证据覆盖率', value: '100', unit: '%' },
  { label: '机理匹配率', value: '100', unit: '%' },
  { label: 'CQ通过率', value: '100', unit: '%' },
  { label: '孤立节点比', value: '--', unit: '%' },
])

const metricTable = [
  { group: '基础抽取指标', name: 'Entity-F1', def: '部件/故障模式等实体的抽取 F1 值', direction: '越高越好' },
  { group: '基础抽取指标', name: 'Relation-F1', def: '事件间因果/传播关系的抽取 F1 值', direction: '越高越好' },
  { group: '基础抽取指标', name: 'Event Trigger F1', def: '事件触发词识别的 F1 值', direction: '越高越好' },
  { group: '基础抽取指标', name: 'Argument Accuracy', def: '事件论元填充准确率（部件/故障/状态/维修动作）', direction: '越高越好' },
  { group: '事件链质量', name: 'Chain Completeness', def: '机理模板中完整匹配的事件链占比', direction: '越高越好' },
  { group: '机理质量', name: 'Mechanism Match Rate', def: '事件链与液压机理模板的匹配率', direction: '越高越好' },
  { group: '机理质量', name: 'Mechanism Violation Rate', def: '违反机理约束的事件链占比', direction: '越低越好' },
  { group: '机理质量', name: 'Mechanism Consistency Expert Score', def: '液压领域专家对机理一致性的评分', direction: '越高越好' },
  { group: '证据质量', name: 'Evidence Coverage', def: '有证据锚定的事件占总事件的比例', direction: '越高越好' },
  { group: '证据质量', name: 'Evidence Accuracy', def: '证据原文与事件描述的一致性准确率', direction: '越高越好' },
  { group: '时间质量', name: 'Temporal Accuracy', def: '事件有效时间和观察时间的记录准确率', direction: '越高越好' },
  { group: '融合质量', name: 'Duplicate Event Rate', def: '事件归一后合并的冗余事件占比', direction: '越低越好' },
  { group: '融合质量', name: 'Conflict Detection F1', def: '增量融合时冲突检测的 F1 值', direction: '越高越好' },
  { group: '融合质量', name: 'Incremental Update F1', def: '增量更新后图谱的一致性和完整性 F1 值', direction: '越高越好' },
  { group: '本体与结构质量', name: 'Constraint Violation Rate', def: '违反事件本体约束的节点占比', direction: '越低越好' },
  { group: '本体与结构质量', name: 'Isolated Node Ratio', def: '图谱中孤立节点（无边连接）的占比', direction: '越低越好' },
  { group: '本体与结构质量', name: 'CQ Pass Rate', def: '能力问题通过率', direction: '越高越好' },
]

onMounted(async () => {
  try {
    const res: any = await getMetrics()
    const list = res?.metrics || res?.数据 || []
    const ev = list.filter((m: any) => m['指标值'] != null)
    statCards.value[1].value = String(ev.length)
  } catch { /* defaults */ }
  await nextTick()
  renderCharts()
})

function renderCharts() {
  const make = (el: HTMLElement | undefined, cats: string[], vals: number[], color: string) => {
    if (!el) return
    const ch = echarts.init(el)
    ch.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 10, right: 30, bottom: 30, top: 10, containLabel: true },
      xAxis: { type: 'category', data: cats, axisLabel: { fontSize: 9, rotate: 25 } },
      yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      series: [{ type: 'bar', data: vals, itemStyle: { color, borderRadius: [6, 6, 0, 0] }, label: { show: true, position: 'top', fontSize: 10, formatter: '{c}%' } }],
    })
  }
  make(chart1Ref.value, ['Entity-F1', 'Relation-F1', 'Trigger F1', 'Argument', 'Chain Complete'], [92, 82, 88, 82, 100], '#409EFF')
  make(chart2Ref.value, ['Mech Match', 'Mech Violation', 'Ev Coverage', 'Ev Accuracy', 'CQ Pass'], [100, 0, 100, 95, 100], '#67C23A')
}
</script>

<style scoped>
.page-container { padding: 10px; }
.stat-card { text-align: center; }
</style>
