import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { title: '登录' } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: '系统首页' } },
  { path: '/sources', name: 'Sources', component: () => import('@/views/SourceManageView.vue'), meta: { title: '公开资料来源管理' } },
  { path: '/extraction', name: 'Extraction', component: () => import('@/views/ExtractionView.vue'), meta: { title: '事件抽取与证据锚定' } },
  { path: '/build-process', name: 'BuildProcess', component: () => import('@/views/BuildProcessView.vue'), meta: { title: '知识图谱构建过程' } },
  { path: '/kg', name: 'KnowledgeGraph', component: () => import('@/views/KnowledgeGraphView.vue'), meta: { title: '知识图谱展示' } },
  { path: '/qa', name: 'KGQA', component: () => import('@/views/KGQAView.vue'), meta: { title: '大模型图谱问答（必须功能）' } },
  { path: '/recommend', name: 'Recommendation', component: () => import('@/views/RecommendationView.vue'), meta: { title: '维修方案推荐' } },
  { path: '/sample-analysis', name: 'SampleAnalysis', component: () => import('@/views/ResultAnalysisView.vue'), meta: { title: '伺服阀样本结果分析' } },
  { path: '/admin', name: 'Admin', component: () => import('@/views/AdminView.vue'), meta: { title: '后台管理' } },
  { path: '/metrics', name: 'Metrics', component: () => import('@/views/MetricsView.vue'), meta: { title: '构建质量评价' } },
  { path: '/advantages', name: 'Advantages', component: () => import('@/views/AdvantagesView.vue'), meta: { title: '系统方法优势' } },
  { path: '/import', name: 'Import', component: () => import('@/views/ImportAnalyzeView.vue'), meta: { title: '资料导入分析（可选）' } },
  { path: '/report', name: 'Report', component: () => import('@/views/ReportView.vue'), meta: { title: '汇报展示' } },
]

// Hash routing avoids server-side rewrite requirements on GitHub Pages.
const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to, _from, next) => {
  document.title = (to.meta.title as string) || '液压故障知识图谱系统'
  next()
})

export default router
