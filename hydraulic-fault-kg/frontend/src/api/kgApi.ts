/**
 * 液压伺服阀故障知识图谱后端 API 封装
 * 所有接口调用 http://127.0.0.1:8000
 * 基于三元组的知识图谱系统
 */
import request from './request'

// ── 系统 ──
export function healthCheck() { return request.get('/api/health') }

// ── 来源资料 ──
export function getSources() { return request.get('/api/sources') }
export function readSources() { return request.post('/api/sources/read') }
export function cleanSources() { return request.post('/api/sources/clean') }
export function filterSources() { return request.post('/api/sources/filter') }
export function getFilteredParagraphs() { return request.get('/api/sources/filtered') }

// ── 三元组抽取 ──
export function runExtraction() { return request.post('/api/extraction/run') }
export function getExtractionTriples() { return request.get('/api/extraction/triples') }
export function getExtractionEvidence() { return request.get('/api/extraction/evidence') }
export function getExtractionStatistics() { return request.get('/api/extraction/statistics') }

// 兼容旧API别名
export function getExtractionEvents() { return request.get('/api/extraction/triples') }

// ── 构建流程 ──
export function getBuildSteps() { return request.get('/api/build/steps') }
export function getBuildStatus() { return request.get('/api/build/status') }
export function getBuildResult() { return request.get('/api/build/result') }

// ── 知识图谱 ──
export function buildGraph() { return request.post('/api/graph/build') }
export function getKGGraph() { return request.get('/api/kg') }
export function getGraphNodes(nodeType?: string) {
  const params = nodeType ? { node_type: nodeType } : {}
  return request.get('/api/graph/nodes', { params })
}
export function getGraphLinks(relation?: string) {
  const params = relation ? { relation } : {}
  return request.get('/api/graph/links', { params })
}
export function getGraphChains() { return request.get('/api/graph/chains') }
export function getGraphNodeDetail(nodeId: string) { return request.get(`/api/graph/node/${nodeId}`) }
export function getGraphLinkDetail(linkId: string) { return request.get(`/api/graph/link/${linkId}`) }

// ── 大模型图谱问答 ──
export function askQuestion(question: string, sessionId?: string) {
  return request.post('/api/qa', { question, session_id: sessionId })
}
export function getQAExamples() { return request.get('/api/qa/examples') }
export function getQASessionHistory(sessionId: string) {
  return request.get(`/api/qa/history/${sessionId}`)
}

// ── 一键重建 ──
export function rebuildAll() { return request.post('/api/pipeline/rebuild-all') }
export function getPipelineStatus() { return request.get('/api/pipeline/status') }
export function getPipelineAudit() { return request.get('/api/pipeline/audit') }

// ── 大模型状态 ──
export function getLLMStatus() { return request.get('/api/llm/status') }

// ── 维修方案推荐 ──
export function recommendMaintenance(params: {
  部件?: string; 故障模式?: string; 异常状态列表?: string[]
}) { return request.post('/api/recommend', params) }
export function getMaintenanceRules() { return request.get('/api/recommend/rules') }

// ── 后台管理 ──
export function getAdminEvents() { return request.get('/api/admin/events') }
export function getAdminEvidence() { return request.get('/api/admin/evidence') }
export function getAdminTemplates() { return request.get('/api/admin/templates') }
export function getAdminVersionLogs() { return request.get('/api/admin/version-logs') }
export function getAdminSummary() { return request.get('/api/admin/summary') }

// ── Dashboard ──
export function getDashboardSummary() { return request.get('/api/dashboard/summary') }

// ── 构建质量评价 ──
export function getMetrics() { return request.get('/api/metrics') }

// ── 系统优势 ──
export function getAdvantages() { return request.get('/api/advantages') }
export function getAdvantagesTable() { return request.get('/api/advantages/table') }

// ── 资源导入 ──
export function uploadFile(formData: FormData) {
  return request.post('/api/import/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export function analyzeFile(fileId: string) { return request.post(`/api/import/analyze/${fileId}`) }
export function getImportResult(fileId: string) { return request.get(`/api/import/result/${fileId}`) }
export function addToKG(fileId: string) { return request.post(`/api/import/add-to-kg/${fileId}`) }
export function getUploadedFiles() { return request.get('/api/import/files') }
export function getAnalysisResults() { return request.get('/api/import/results') }

// ── 兼容旧版视图的函数别名 ──
export const loginApi = (u: string, p: string) => request.post('/api/auth/login', { username: u, password: p })
export const runBuildPipeline = buildGraph
export const getKGEventDetail = getGraphNodeDetail
export const getKGChain = getGraphChains
export const getKGEdges = getGraphLinks
export const getAdminConflicts = () => request.get('/api/admin/version-logs')

// ── 样本结果分析 ──
export function extractSampleDoc() { return request.post('/api/sample-analysis/extract-doc') }
export function analyzeAllSamples() { return request.post('/api/sample-analysis/analyze-all') }
export function getSampleFileInfo() { return request.get('/api/sample-analysis/file-info') }
export function getSampleManifest() { return request.get('/api/sample-analysis/manifest') }
export function getSampleParts() { return request.get('/api/sample-analysis/parts') }
export function getSampleList(part: string) { return request.get('/api/sample-analysis/samples', { params: { part } }) }
export function getSampleResult(part: string, sampleId: string) {
  return request.get('/api/sample-analysis/result', { params: { part, sample_id: sampleId } })
}
export function getSampleRawImageUrl(sampleId: string) {
  return `http://127.0.0.1:8000/api/sample-analysis/raw-image?sample_id=${sampleId}`
}
export function bootstrapSampleAnalysis() { return request.post('/api/sample-analysis/bootstrap') }
