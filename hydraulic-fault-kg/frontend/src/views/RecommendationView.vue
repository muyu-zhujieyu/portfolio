<template>
  <div class="page-container report-screen big-font-page">
    <h2 style="font-size:34px">维修方案推荐</h2>
    <p class="desc">
      优先级分数 = 症状匹配度 × 0.4 + 机理模板匹配度 × 0.3 + 证据可靠度 × 0.2 + 风险等级权重 × 0.1
    </p>

    <!-- 输入区 -->
    <el-card style="margin-bottom: 20px">
      <el-form :inline="true">
        <el-form-item label="部件">
          <el-select v-model="component" placeholder="选择部件" clearable style="width: 180px">
            <el-option v-for="c in components" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="故障模式">
          <el-select v-model="faultMode" placeholder="选择故障模式" clearable style="width: 180px">
            <el-option v-for="f in faultModes" :key="f" :label="f" :value="f" />
          </el-select>
        </el-form-item>
        <el-form-item label="异常状态">
          <el-select v-model="symptoms" placeholder="选择异常状态" multiple clearable style="width: 300px">
            <el-option v-for="s in symptomOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doRecommend" :loading="loading">开始推荐</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 结果 -->
    <div v-if="result">
      <!-- 顶部评分 -->
      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="6">
          <el-card class="score-card" :style="{ borderTopColor: scoreColor }">
            <div class="big-score" :style="{ color: scoreColor }">{{ fmtPct(result['优先级分数']) }}</div>
            <div class="score-label">优先级分数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="score-card">
            <el-tag :type="riskTag" size="large">{{ result['风险等级'] || '—' }}</el-tag>
            <div class="score-label">风险等级</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="score-card">
            <div class="big-score">{{ (result['推荐维修动作'] || []).length }}</div>
            <div class="score-label">维修动作数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="score-card">
            <el-tag :type="result['是否需要人工复核'] ? 'warning' : 'success'" size="large">
              {{ result['是否需要人工复核'] ? '需要' : '无需' }}
            </el-tag>
            <div class="score-label">人工复核</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 推荐理由 -->
      <el-alert v-if="result['推荐理由']" type="success" :closable="false" style="margin-bottom: 16px">
        <template #title>{{ result['推荐理由'] }}</template>
      </el-alert>

      <!-- 可能故障 + 机理模板 -->
      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="12">
          <el-card header="可能故障">
            <el-tag v-for="f in (result['可能故障'] || [])" :key="f" type="danger" style="margin: 2px 4px">{{ f }}</el-tag>
            <span v-if="!(result['可能故障'] || []).length" style="color:#909399">暂无</span>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card header="命中机理模板">
            <div v-for="t in (result['命中机理模板'] || [])" :key="t" style="margin: 4px 0">
              <el-tag type="primary">{{ t }}</el-tag>
            </div>
            <span v-if="!(result['命中机理模板'] || []).length" style="color:#909399">暂无</span>
          </el-card>
        </el-col>
      </el-row>

      <!-- 维修动作 -->
      <el-card header="推荐维修动作" style="margin-bottom: 16px">
        <el-steps direction="vertical">
          <el-step v-for="(act, i) in (result['推荐维修动作'] || [])" :key="i"
            :title="`步骤 ${i + 1}`" :description="act"
            :status="i < 3 ? 'success' : 'process'" />
        </el-steps>
      </el-card>

      <!-- 注意事项 -->
      <el-card v-if="(result['注意事项'] || []).length" header="注意事项" style="margin-bottom: 16px">
        <el-alert v-for="(n, i) in result['注意事项']" :key="i" :title="n" type="warning" :closable="false" style="margin: 4px 0" />
      </el-card>

      <!-- 匹配事件链 + 支撑证据 -->
      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="12">
          <el-card header="匹配事件链">
            <div v-for="(ch, i) in (result['匹配事件链'] || [])" :key="i" style="margin: 4px 0; font-size:13px">
              <el-tag size="small" type="danger">{{ ch['模板编号'] }}</el-tag>
              {{ ch['中文链式模式'] || ch['链式模式'] || '' }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card header="支撑证据">
            <div v-for="(evd, i) in (result['支撑证据'] || [])" :key="i" style="margin: 4px 0; font-size:12px; padding:6px; background:#f5f7fa; border-radius:4px">
              <el-tag size="small" type="success">{{ evd['证据编号'] || '' }}</el-tag>
              <div>{{ (evd['原文片段'] || evd['证据原文'] || '').slice(0, 150) }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 预计停机 + 规则来源 -->
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="预计停机时间">{{ result['预计停机时间_小时'] ? result['预计停机时间_小时'] + ' 小时' : '—' }}</el-descriptions-item>
        <el-descriptions-item label="规则来源">{{ result['规则来源'] || '—' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!result && !loading" description="请选择部件、故障模式和异常状态，点击[开始推荐]" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { recommendMaintenance } from '@/api/kgApi'
import { ElMessage } from 'element-plus'

const component = ref('')
const faultMode = ref('')
const symptoms = ref<string[]>([])
const loading = ref(false)
const result = ref<any>(null)

const components = ['液压泵', '液压阀', '阀芯', '过滤器', '冷却器', '蓄能器', '执行机构', '溢流阀', '换向阀', '液压缸', '管路', '油箱']
const faultModes = ['内泄漏', '过滤器堵塞', '阀芯卡滞', '冷却器效率下降', '蓄能器预充压力不足', '油液污染', '溢流阀异常', '气蚀', '密封件老化', '容积效率下降']
const symptomOptions = ['压力下降', '流量损失', '油温升高', '压力波动', '动作迟缓', '噪声增大', '振动增大', '保压失败', '负载能力下降', '泄漏增加', '黏度下降']

const scoreColor = computed(() => {
  const s = result.value?.['优先级分数'] || 0
  if (s >= 0.7) return '#67C23A'
  if (s >= 0.5) return '#E6A23C'
  return '#F56C6C'
})

const riskTag = computed(() => {
  const r = result.value?.['风险等级'] || ''
  if (r === '高') return 'danger'
  if (r === '中') return 'warning'
  return 'info'
})

function fmtPct(v: number) { return (v * 100).toFixed(1) + '%' }

async function doRecommend() {
  if (!faultMode.value && !component.value && !symptoms.value.length) {
    ElMessage.warning('请至少选择部件、故障模式或异常状态中的一项')
    return
  }
  loading.value = true
  try {
    const res: any = await recommendMaintenance({
      部件: component.value || undefined,
      故障模式: faultMode.value || undefined,
      异常状态列表: symptoms.value.length ? symptoms.value : undefined,
    })
    result.value = res
    ElMessage.success(`推荐完成，优先级分数: ${fmtPct(res['优先级分数'] || 0)}`)
  } catch (e: any) {
    ElMessage.error('推荐失败: ' + (e?.message || '网络错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page-container { padding: 10px; }
.desc { color: #909399; font-size: 13px; margin-bottom: 16px; }
.score-card { text-align: center; border-top: 4px solid #409EFF; }
.big-score { font-size: 32px; font-weight: 700; }
.score-label { font-size: 12px; color: #909399; margin-top: 6px; }
</style>
