<template>
  <div class="page-container">
    <h2>方法优势与难点突破</h2>
    <p class="subtitle">对比普通大模型直接回答，本系统如何突破液压故障知识问答的六大核心难点</p>

    <!-- 六大难点对比卡片 -->
    <div v-for="(item, idx) in difficulties" :key="idx" class="diff-card">
      <el-card>
        <template #header>
          <div class="diff-header">
            <el-tag :type="item.tagType" size="large">难点 {{ idx + 1 }}</el-tag>
            <span class="diff-title">{{ item.title }}</span>
          </div>
        </template>
        <el-row :gutter="20">
          <!-- 左侧：普通大模型不足 -->
          <el-col :span="12">
            <div class="side-box weak-box">
              <div class="side-label"><el-tag type="danger">普通大模型不足</el-tag></div>
              <p>{{ item.weakness }}</p>
            </div>
          </el-col>
          <!-- 中间箭头 -->
          <el-col :span="12">
            <div class="side-box strong-box">
              <div class="side-label"><el-tag type="success">本系统方法优势</el-tag></div>
              <p>{{ item.strength }}</p>
              <div v-if="item.tech" class="tech-tag">
                <el-tag size="small" type="info">{{ item.tech }}</el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 总结 -->
    <el-card style="margin-top: 20px">
      <template #header><b>核心结论</b></template>
      <el-row :gutter="16">
        <el-col :span="8" v-for="s in summaries" :key="s.label">
          <el-statistic :title="s.label" :value="s.value" />
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
const difficulties = [
  {
    title: '公开资料中的故障知识分散',
    tagType: 'danger',
    weakness: '普通大模型只能基于输入文本回答，难以将来自维修手册、论文、教材、说明书和故障案例等多个来源的分散知识整合为统一的知识结构。每次对话独立，知识无法积累和复用。',
    strength: '本系统从公开维修手册、论文、教材、元件说明书和故障案例中系统性地抽取事件，将分散的文本知识统一转化为结构化的事件知识图谱（92个节点+177条边），知识持久化存储在SQLite中，可复用、可更新。',
    tech: 'source_reader + text_clean + domain_filter + event_extract → graph_build',
  },
  {
    title: '故障演化链需要液压机理约束',
    tagType: 'danger',
    weakness: '普通大模型可能生成不符合液压物理机理的故障传播链。例如，可能将「冷却器效率下降」直接关联到「阀芯磨损」，而忽略了油温升高→黏度下降→泄漏增加的正确因果路径。模型缺乏液压领域的物理约束。',
    strength: '本系统定义了6条液压机理模板（T1泄漏链/T2堵塞链/T3冷却链/T4蓄能器链/T5污染链/T6溢流阀链）进行事件链校验。每条模板都有明确的物理约束说明，确保故障推理符合液压机理。校验结果分为：完整匹配链、部分匹配链、违规链和待审核链。',
    tech: 'mechanism_validation_service + mechanism_templates表 + 物理约束',
  },
  {
    title: '答案必须可追溯至原始资料',
    tagType: 'warning',
    weakness: '普通大模型的回答往往没有source_id、paragraph_id、evidence_span，用户无法验证答案的准确性和权威性。即使是带引用的回答，引用也可能不精确或无法定位到原文具体位置。',
    strength: '本系统每个事件绑定证据原文，通过evidence_anchor_service将抽取结果锚定到原始资料的具体位置（来源编号+段落编号+句子编号+起始位置+结束位置）。图谱节点详情面板可直接查看证据原文和来源追溯链。',
    tech: 'evidence_anchor_service + evidence表 + source_id/paragraph_id追溯',
  },
  {
    title: '知识会随维修记录更新',
    tagType: 'warning',
    weakness: '普通大模型无法区分有效事实、过期事实和冲突事实。当新的维修记录表明旧故障已修复时，模型无法自动更新知识状态。不能正确处理“这个故障在2023年存在，但在2024年已修复”这样的时态信息。',
    strength: '本系统采用双时态记录机制：valid_time（事件发生时间）+ observed_time（系统录入时间）+ version_status（active/expired/resolved）+ conflict_flag（冲突标记）。version_logs表记录每次变更的旧值和新值，支持完整版本追溯和审计。',
    tech: 'version_logs表 + 双时态字段 + conflict_flag + 增量融合',
  },
  {
    title: '新增资料可以增量入图谱',
    tagType: 'info',
    weakness: '普通大模型对上传资料通常只给出一次性回答。无法从新资料中自动抽取结构化知识并融合到已有的知识体系中。每次对话都是独立的，知识无法积累和增长。',
    strength: '本系统提供可选的资料导入分析功能：用户上传新资料→自动解析/清洗/过滤/抽取/锚定→用户选择是否增量加入知识图谱。新知识自动与已有事件进行归一化和冲突检测，保留历史版本，不覆盖已有数据。注意：主流程不依赖此功能。',
    tech: 'import_service + upload/analyze/add-to-kg + fusion_service增量融合',
  },
  {
    title: '大模型问答需要可解释',
    tagType: 'info',
    weakness: '普通大模型问答结果不一定说明依据。用户无法区分模型是基于真实知识还是幻觉生成。维修建议可能不适用于具体机型或工况，且无法提供置信度评估。',
    strength: '本系统大模型问答具有完整的可解释性：每条回答同时展示匹配故障演化链、命中机理模板、支撑证据原文、推荐维修措施、置信度百分比和答案依据说明。大模型只负责基于检索到的图谱上下文组织语言表达，不编造事实。',
    tech: 'kg_context_service + llm_provider(Mock/OpenAI) + 8类问答+可折叠证据面板',
  },
]

const summaries = [
  { label: '核心创新', value: '事件化建模 + 机理约束 + 证据锚定' },
  { label: '知识来源', value: '公开维修手册/论文/教材/说明书/案例' },
  { label: '方法定位', value: '大模型从知识生成者变为知识组织者' },
]
</script>

<style scoped>
.page-container { padding: 10px; }
.subtitle { color: #909399; font-size: 14px; margin-bottom: 20px; }

.diff-card { margin-bottom: 16px; }
.diff-header { display: flex; align-items: center; gap: 12px; }
.diff-title { font-size: 15px; font-weight: 700; color: #303133; }

.side-box {
  padding: 16px; border-radius: 8px; min-height: 120px;
  line-height: 1.8; font-size: 13px;
}
.weak-box { background: #fef0f0; border-left: 4px solid #F56C6C; }
.strong-box { background: #f0f9eb; border-left: 4px solid #67C23A; }
.side-label { margin-bottom: 8px; }
.tech-tag { margin-top: 10px; }
</style>
