<template>
  <div class="page-container report-screen big-font-page">
    <h2 style="font-size:34px">公开资料来源管理</h2>

    <el-alert type="info" :closable="false" style="margin-bottom: 16px">
      <template #title>
        当前主数据来源聚焦液压伺服阀相关公开资料。本系统知识图谱的主数据来源于伺服阀维修手册、伺服阀故障诊断论文、液压伺服控制教材、伺服阀元件说明书和伺服阀故障案例，经解析、清洗、过滤、事件抽取和机理校验后构建液压伺服阀故障事件知识图谱。
      </template>
    </el-alert>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="4">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="资料总数" :value="sources.length">
            <template #suffix><span style="font-size:14px;color:#409EFF">份</span></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4" v-for="item in typeStats" :key="item.type">
        <el-card shadow="hover" class="stat-card">
          <el-statistic :title="item.label" :value="item.count">
            <template #suffix><span style="font-size:12px;color:#909399">份</span></template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作区 -->
    <el-space style="margin-bottom: 16px">
      <el-button type="primary" @click="refreshSources" :loading="loading">
        刷新来源列表
      </el-button>
      <el-button type="warning" @click="reloadSources" :loading="reloading">
        重新加载资料
      </el-button>
      <el-button type="success" @click="parseAll" :loading="parsing">
        解析全部资料
      </el-button>
      <el-button type="danger" @click="rebuildAll" :loading="rebuilding">
        抽取并重建图谱
      </el-button>
      <el-tag type="info" size="large">{{ sources.length }} 份公开资料</el-tag>
    </el-space>

    <!-- 来源表格 -->
    <el-table :data="sources" border stripe v-loading="loading" style="width: 100%" max-height="500">
      <el-table-column prop="source_id" label="来源编号" width="140" fixed />
      <el-table-column prop="来源类型" label="来源类型" width="130" />
      <el-table-column prop="标题" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="作者" label="作者" width="120" show-overflow-tooltip />
      <el-table-column prop="年份" label="年份" width="70" />
      <el-table-column prop="出版方" label="出版方" width="150" show-overflow-tooltip />
      <el-table-column prop="文件路径" label="文件路径" width="200" show-overflow-tooltip />
      <el-table-column prop="文档类型" label="文档类型" width="80" />
      <el-table-column prop="公开说明" label="公开说明" min-width="200" show-overflow-tooltip />
      <el-table-column prop="资料描述" label="资料描述" min-width="220" show-overflow-tooltip />
    </el-table>

    <el-divider />

    <div class="footer-note">
      <p><strong>说明：</strong>以上公开资料均来自公开渠道，包括：</p>
      <ul>
        <li><el-tag size="small">公开维修手册</el-tag> — 公开发行的液压系统维护培训教材</li>
        <li><el-tag size="small">相关论文</el-tag> — 中文核心期刊公开发表的学术论文</li>
        <li><el-tag size="small">液压教材</el-tag> — 高等学校公开出版发行的规划教材</li>
        <li><el-tag size="small">元件说明书</el-tag> — 制造商公开发布的产品技术文档</li>
        <li><el-tag size="small">公开故障案例</el-tag> — 期刊公开发表的工程设备故障维修报告</li>
      </ul>
      <p style="margin-top: 8px; color: #E6A23C">
        这些公开资料经过解析、清洗、领域过滤、事件抽取和机理模板校验后，构建为事件知识图谱。
        大模型图谱问答基于此知识图谱，不编造事实。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getSources, readSources as readSourcesApi } from '@/api/kgApi'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const reading = ref(false)
const reloading = ref(false)
const parsing = ref(false)
const rebuilding = ref(false)

interface SourceItem {
  source_id: string
  来源类型: string
  标题: string
  作者: string
  年份: number | string
  出版方: string
  文件路径: string
  文档类型: string
  公开说明: string
  资料描述: string
  [key: string]: any
}

const sources = ref<SourceItem[]>([])

// 按类型统计
const typeStats = computed(() => {
  const typeMap: Record<string, string> = {
    '公开维修手册': '维修手册(4)',
    '相关论文': '相关论文(5)',
    '液压教材': '液压教材(4)',
    '元件说明书': '元件说明书(4)',
    '公开故障案例': '故障案例(3)',
  }
  const counts: Record<string, number> = {}
  sources.value.forEach(s => {
    const t = s['来源类型'] || '其他'
    counts[t] = (counts[t] || 0) + 1
  })
  return Object.entries(typeMap).map(([key, label]) => ({
    type: key,
    label,
    count: counts[key] || 0,
  }))
})

// 获取来源列表
async function refreshSources() {
  loading.value = true
  try {
    const res: any = await getSources()
    // 处理后端返回格式: { 总数, 来源列表 }
    sources.value = res['来源列表'] || res.sources || res || []
    ElMessage.success(`已加载 ${sources.value.length} 条公开资料来源`)
  } catch (e: any) {
    ElMessage.error('加载来源失败: ' + (e?.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

// 重新加载资料（从registry写入DB）
async function reloadSources() {
  reloading.value = true
  try {
    const res: any = await request.post('/api/sources/reload')
    ElMessage.success(`重新加载完成: ${res['资料总数'] || '?'} 条资料`)
    await refreshSources()
  } catch (e: any) {
    ElMessage.error('重新加载失败: ' + (e?.message || '网络错误'))
  } finally { reloading.value = false }
}

// 解析全部资料（read+clean+filter）
async function parseAll() {
  parsing.value = true
  try {
    const res: any = await readSourcesApi()
    ElMessage.success(`解析+过滤完成: 液压段落 ${res['液压相关段落数'] || res['段落总数'] || '?'}`)
  } catch (e: any) {
    ElMessage.error('解析失败: ' + (e?.message || '网络错误'))
  } finally { parsing.value = false }
}

// 一键重建
async function rebuildAll() {
  rebuilding.value = true
  try {
    const res: any = await request.post('/api/pipeline/rebuild-all')
    if (res['状态'] === '成功') {
      ElMessage.success(`重建完成! 来源${res['公开资料数量']} 事件${res['抽取事件数量']} 节点${res['图谱节点数量']}`)
    } else {
      ElMessage.error('重建失败: ' + (res['错误'] || '未知'))
    }
  } catch (e: any) {
    ElMessage.error('重建失败: ' + (e?.message || '网络错误'))
  } finally { rebuilding.value = false }
}

// 解析所有文档
async function readSources() {
  reading.value = true
  try {
    const res: any = await readSourcesApi()
    ElMessage.success(`解析完成: 成功 ${res['解析成功数'] || 0} / 失败 ${res['解析失败数'] || 0}，共 ${res['段落总数'] || 0} 个段落`)
  } catch (e: any) {
    ElMessage.error('解析失败: ' + (e?.message || '网络错误'))
  } finally {
    reading.value = false
  }
}

onMounted(() => {
  refreshSources()
})
</script>

<style scoped>
.page-container { padding: 10px; }
.stat-card { text-align: center; }
.footer-note {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
.footer-note ul { margin: 8px 0; padding-left: 20px; }
.footer-note li { margin: 4px 0; }
</style>
