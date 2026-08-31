<template>
  <div class="dashboard report-screen big-font-page">
    <div class="hero">
      <h1 style="font-size:36px; margin-bottom:10px">液压伺服阀故障知识图谱与智能维护平台</h1>
      <p style="font-size:20px">核心原则：大模型不能直接编造事实，必须基于知识图谱、事件链、证据 span、机理模板和维修规则组织回答</p>
    </div>

    <!-- 研究对象：液压伺服阀 -->
    <div class="servo-valve-module" style="margin-bottom:20px">
      <div class="sv-title">
        <span style="font-size:32px">研究对象：液压伺服阀</span>
        <el-tag type="danger" size="large">核心研究对象</el-tag>
      </div>
      <div class="sv-desc" style="font-size:18px; margin-bottom:14px; line-height:1.7">
        基于 <strong>Y1797-ZT 伺服阀模型</strong>与 20201010 样本文档开展故障知识图谱构建、曲线结果分析和智能维修推荐。
        液压伺服阀是液压系统中的关键精密控制元件，其故障演化过程涉及多种失效模式和机理链。
      </div>
      <el-row :gutter="24">
        <!-- 模型图片区域 -->
        <el-col :span="10" style="text-align:center">
          <div class="model-img-container" v-if="!imgError">
            <img :src="modelImgSrc"
                 alt="液压伺服阀 Y1797-ZT 模型图"
                 class="model-img"
                 @error="imgError = true" />
          </div>
          <div class="model-img-fallback" v-if="imgError">
            <div class="fallback-title">未能加载液压伺服阀图片</div>
            <div class="fallback-desc">
              请检查 D:\kg0623\frontend\public\servo_valve_model.png 是否存在。
            </div>
          </div>
          <div class="model-source">
            图示来源：Y1797-ZT 液压伺服阀模型图片<br/>
            说明：该图用于表明本系统研究对象为液压伺服阀。
          </div>
        </el-col>
        <!-- 右侧文字说明 -->
        <el-col :span="14">
          <div class="sv-desc" style="font-size:18px; line-height:1.8; margin-bottom:10px">
            <strong>典型部位：</strong>
          </div>
          <div class="sv-parts">
            <span class="sv-part-tag">阀芯阀套</span>
            <span class="sv-part-tag">喷嘴挡板</span>
            <span class="sv-part-tag">力矩马达</span>
            <span class="sv-part-tag">衔铁组件</span>
            <span class="sv-part-tag">气隙垫片</span>
            <span class="sv-part-tag">线圈与磁路</span>
            <span class="sv-part-tag">密封组件</span>
            <span class="sv-part-tag">反馈杆</span>
          </div>
          <div style="margin-top:14px; font-size:18px; color:#606266; line-height:1.8">
            <strong>核心功能：</strong>公开资料抽取 | 事件知识图谱构建 | 20201010 曲线结果分析 | 大模型图谱问答 | 维修方案推荐
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="3" v-for="card in stats" :key="card.label">
        <el-card shadow="hover" class="stat-card" :style="{ borderTopColor: card.color }">
          <div class="stat-val" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-lbl">{{ card.label }}</div>
          <div class="stat-sub" v-if="card.sub" style="font-size:12px;color:#909399;margin-top:2px">{{ card.sub }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统主流程 -->
    <el-card header="系统主流程" style="margin-bottom:20px">
      <div class="main-flow">
        <div class="flow-step" v-for="(step, i) in mainFlow" :key="i">
          <div class="flow-icon">{{ step.icon }}</div>
          <div class="flow-name">{{ step.name }}</div>
          <div class="flow-arrow" v-if="i < mainFlow.length - 1">→</div>
        </div>
      </div>
      <el-alert type="info" :closable="false" style="margin-top:12px">
        平台面向液压伺服阀故障知识组织与智能维护决策。资料导入分析是可选增量功能，不是主流程前提。主流程基于伺服阀维修手册、论文、教材、说明书和公开故障案例。
      </el-alert>
    </el-card>

    <!-- 快捷入口 -->
    <el-card header="快捷入口" style="margin-bottom:20px">
      <el-row :gutter="12">
        <el-col :span="6" v-for="item in shortcuts" :key="item.path" style="margin-bottom:12px">
          <el-card shadow="hover" class="shortcut-card" @click="$router.push(item.path)">
            <div class="sc-icon">{{ item.icon }}</div>
            <div class="sc-name">{{ item.name }}</div>
            <div class="sc-desc">{{ item.desc }}</div>
            <el-tag v-if="item.tag" :type="item.tagType" size="small" style="margin-top:4px">{{ item.tag }}</el-tag>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 核心特点 -->
    <el-card header="系统核心特点">
      <el-row :gutter="16">
        <el-col :span="6" v-for="f in features" :key="f.title">
          <el-card shadow="hover" class="feature-card">
            <div class="ft-icon">{{ f.icon }}</div>
            <b>{{ f.title }}</b>
            <p>{{ f.desc }}</p>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDashboardSummary } from '@/api/kgApi'

const imgError = ref(false)
const modelImgSrc = '/servo_valve_model.png'

const stats = ref([
  { label: '公开资料', value: '—', color: '#1ABC9C' },
  { label: '液压段落', value: '—', color: '#F39C12' },
  { label: '原始三元组', value: '—', color: '#E74C3C', sub: '规则抽取全部三元组' },
  { label: '融合三元组', value: '—', color: '#F39C12', sub: '同义归一合并后' },
  { label: '证据数量', value: '—', color: '#3498DB', sub: 'evidence表实条数' },
  { label: '图谱节点', value: '—', color: '#2ECC71' },
  { label: '图谱边', value: '—', color: '#E91E63' },
  { label: '问答记录', value: '—', color: '#00BCD4' },
])

const mainFlow = [
  { icon: '📚', name: '公开资料' },
  { icon: '🔍', name: '抽取过滤' },
  { icon: '⚡', name: '事件建模' },
  { icon: '✅', name: '机理校验' },
  { icon: '📊', name: '图谱入库' },
  { icon: '🤖', name: '大模型问答' },
]

const shortcuts = [
  { path: '/sources', icon: '📚', name: '数据源管理', desc: '管理公开维修手册、论文、教材等', tag: '', tagType: '' },
  { path: '/extraction', icon: '🔍', name: '抽取过滤过程', desc: '文档解析→清洗→过滤→抽取→锚定', tag: '', tagType: '' },
  { path: '/kg', icon: '📊', name: '知识图谱展示', desc: 'ECharts 可视化的中文知识图谱', tag: '', tagType: '' },
  { path: '/qa', icon: '🤖', name: '大模型图谱问答', desc: '基于图谱检索+大模型组织回答', tag: '必须功能', tagType: 'danger' },
  { path: '/recommend', icon: '🔧', name: '维修方案推荐', desc: '基于故障模式匹配维修规则', tag: '', tagType: '' },
  { path: '/advantages', icon: '🏆', name: '方法优势', desc: '对比普通大模型的6大突破', tag: '', tagType: '' },
  { path: '/import', icon: '📤', name: '可选资料导入分析', desc: '上传新资料→补充分析→增量入图', tag: '可选功能', tagType: 'info' },
  { path: '/sample-analysis', icon: '📊', name: '结果分析', desc: '液压伺服阀故障样本分析与评估', tag: '新增', tagType: 'warning' },
  { path: '/admin', icon: '⚙', name: '后台管理', desc: '全链路数据查看与管理', tag: '', tagType: '' },
]

const features = [
  { icon: '📝', title: '机理约束', desc: '6条液压机理模板校验事件链物理合理性，防止不符合物理规律的故障推理' },
  { icon: '🔗', title: '证据可追溯', desc: '每个事件锚定到原文具体位置(source_id/paragraph_id/evidence_span)' },
  { icon: '⏱', title: '双时态管理', desc: '记录事件发生时间与录入时间，支持版本追溯和增量融合' },
  { icon: '🎯', title: '大模型约束', desc: '大模型只组织表达，事实来自知识图谱+证据span+机理模板+维修规则' },
]

onMounted(async () => {
  try {
    const res: any = await getDashboardSummary()
    stats.value = [
      { label: '公开资料', value: String(res['公开资料'] || res['sources'] || '—'), color: '#1ABC9C' },
      { label: '液压段落', value: String(res['液压段落'] || '—'), color: '#F39C12' },
      { label: '原始三元组', value: String(res['原始三元组'] || '—'), color: '#E74C3C', sub: '规则抽取全部三元组' },
      { label: '融合三元组', value: String(res['融合三元组'] || '—'), color: '#F39C12', sub: '同义归一合并后' },
      { label: '证据数量', value: String(res['证据数量'] || '—'), color: '#3498DB', sub: 'evidence表实条数' },
      { label: '图谱节点', value: String(res['图谱节点'] || '—'), color: '#2ECC71' },
      { label: '图谱边', value: String(res['图谱边'] ?? res['graph_link_count'] ?? '—'), color: '#E91E63' },
      { label: '问答记录', value: String(res['问答记录'] || '—'), color: '#00BCD4' },
    ]
  } catch { /* keep defaults */ }
})
</script>

<style scoped>
.dashboard { padding: 10px; }
.hero { text-align: center; margin-bottom: 24px; padding: 20px; background: linear-gradient(135deg, #1a3a5c 0%, #304156 100%); border-radius: 12px; color: #fff; }
.hero h1 { margin: 0 0 10px 0; font-size: 28px; }
.hero p { margin: 0; font-size: 13px; opacity: 0.85; }

.stat-card { text-align: center; border-top: 5px solid #1ABC9C; padding: 16px 10px; }
.stat-val { font-size: 42px; font-weight: 800; }
.stat-lbl { font-size: 18px; color: #303133; margin-top: 6px; font-weight: 600; }

.main-flow { display: flex; align-items: center; justify-content: center; gap: 4px; flex-wrap: wrap; padding: 14px 0; }
.flow-step { display: flex; flex-direction: column; align-items: center; padding: 12px 20px; background: #f5f7fa; border-radius: 10px; min-width: 110px; }
.flow-icon { font-size: 34px; }
.flow-name { font-size: 15px; margin-top: 6px; color: #303133; font-weight: 600; }
.flow-arrow { font-size: 28px; color: #409EFF; margin: 0 10px; }

.shortcut-card { text-align: center; cursor: pointer; transition: all 0.2s; padding: 14px 10px; }
.shortcut-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
.sc-icon { font-size: 38px; }
.sc-name { font-size: 16px; font-weight: 600; margin: 6px 0 4px 0; }
.sc-desc { font-size: 14px; color: #909399; }

.feature-card { text-align: center; }
.ft-icon { font-size: 40px; }
.feature-card b { display: block; margin: 8px 0; font-size: 16px; }
.feature-card p { font-size: 14px; color: #606266; line-height: 1.6; margin: 0; }

.servo-valve-module { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.sv-title { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.sv-desc { color: #606266; }
.sv-parts { display: flex; flex-wrap: wrap; gap: 8px; }
.sv-part-tag {
  background: #f0f5fa; color: #304156; padding: 6px 14px;
  border-radius: 20px; font-size: 18px; font-weight: 600;
  border: 1px solid #d9e1e8;
}
.model-img-container { max-width: 350px; margin: 0 auto; }
.model-img { width: 100%; border-radius: 8px; border: 1px solid #e4e7ed; }
.model-img-fallback {
  background: #f5f7fa; border: 2px dashed #d9e1e8; border-radius: 8px;
  padding: 40px; text-align: center;
}
.model-source { font-size: 13px; color: #909399; margin-top: 8px; }
</style>
