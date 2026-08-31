const sensors = [
  { key: 'temp', name: '泄油口温度', unit: '°C', color: '#3c91ff', base: 48.2, amp: 2.8, note: '观察泄油介质温度水平和升降过程，应结合运行时长、系统油温与冷却条件解释。' },
  { key: 'casePressure', name: '泄油口压力', unit: 'bar', color: '#31d67b', base: 2.35, amp: 0.32, note: '观察泵壳回油侧压力变化，同时受泵体泄漏、管路阻力、过滤部件和油液黏度影响。' },
  { key: 'portA', name: '油口 A 压力', unit: 'MPa', color: '#ffb020', base: 18.4, amp: 5.2, note: '观察 A 侧工作油路压力。高低压侧可能随方向与负载切换，不能脱离工况判断。' },
  { key: 'portB', name: '油口 B 压力', unit: 'MPa', color: '#ff5364', base: 16.8, amp: 6.1, note: '观察 B 侧工作油路压力，应与控制方向、负载阶段和 A 口变化联合核对。' }
]

const state = { records: [], generated: 0, paused: false, terminalOnline: true, serviceOnline: true, phase: 0, lastDataAt: 0 }
const metricCards = document.querySelector('#metricCards')
const recordRows = document.querySelector('#recordRows')
const chart = document.querySelector('#trendChart')
const ctx = chart.getContext('2d')

metricCards.innerHTML = sensors.map(sensor => `
  <article class="metric" style="--metric:${sensor.color};color:${sensor.color}">
    <div class="metric-head"><span>${sensor.name}</span><span class="metric-status">● 正常</span></div>
    <div class="metric-value" id="value-${sensor.key}">--<small>${sensor.unit}</small></div>
  </article>`).join('')

document.querySelector('#legend').innerHTML = sensors.map(sensor => `<span style="--legend:${sensor.color}">${sensor.name}</span>`).join('')
document.querySelector('#sensorNotes').innerHTML = sensors.map((sensor, index) => `
  <article class="sensor-note" style="--sensor:${sensor.color}">
    <h3>${sensor.name}</h3><p>${sensor.note}</p><code>adc${index + 1} · ${sensor.unit}</code>
  </article>`).join('')

function nextRecord(seedOffset = 0) {
  state.phase += 0.22
  const noise = (scale = 1) => (Math.random() - .5) * scale
  const now = new Date(Date.now() - seedOffset)
  return {
    timestamp: now,
    temp: 48.2 + Math.sin(state.phase) * 2.8 + noise(.35),
    casePressure: 2.35 + Math.sin(state.phase * .43 + .6) * .32 + noise(.05),
    portA: 18.4 + Math.sin(state.phase * 1.55) * 5.2 + noise(.7),
    portB: 16.8 + Math.cos(state.phase * 1.28) * 6.1 + noise(.8)
  }
}

function appendRecord(record) {
  state.records.push(record)
  if (state.records.length > 200) state.records.shift()
  state.generated += 1
  state.lastDataAt = Date.now()
  render()
}

function seedRecords() {
  state.records = []
  state.phase = 0
  for (let i = 48; i >= 0; i -= 1) state.records.push(nextRecord(i * 1000))
  state.generated = state.records.length
  state.lastDataAt = Date.now()
  render()
}

function formatTime(date, withMs = true) {
  const base = date.toLocaleTimeString('zh-CN', { hour12: false })
  return withMs ? `${base}.${String(date.getMilliseconds()).padStart(3, '0')}` : base
}

function render() {
  const latest = state.records.at(-1)
  if (latest) {
    sensors.forEach(sensor => {
      document.querySelector(`#value-${sensor.key}`).innerHTML = `${latest[sensor.key].toFixed(sensor.key === 'temp' ? 1 : 2)}<small>${sensor.unit}</small>`
    })
    document.querySelector('#latestTime').textContent = `最新数据 ${formatTime(latest.timestamp)}`
  }
  document.querySelector('#recordCount').textContent = `${state.records.length} 条`
  document.querySelector('#generatedCount').textContent = `${state.generated} 条`
  renderRows()
  updateStates()
  drawChart()
}

function renderRows() {
  recordRows.innerHTML = [...state.records].reverse().slice(0, 12).map(record => `
    <tr><td>${formatTime(record.timestamp)}</td><td>${record.temp.toFixed(1)} °C</td><td>${record.casePressure.toFixed(2)} bar</td><td>${record.portA.toFixed(2)} MPa</td><td>${record.portB.toFixed(2)} MPa</td></tr>`).join('')
}

function updateStates() {
  const stale = Date.now() - state.lastDataAt > 3000
  const service = document.querySelector('#serviceState')
  const device = document.querySelector('#deviceState')
  const freshness = document.querySelector('#freshnessState')
  service.className = state.serviceOnline ? '' : 'bad'
  service.innerHTML = `<i></i>${state.serviceOnline ? '已连接' : '未连接'}`
  device.className = state.terminalOnline ? '' : 'bad'
  device.innerHTML = `<i></i>${state.terminalOnline ? '在线' : '离线'}`
  freshness.className = stale ? 'warn' : ''
  freshness.innerHTML = `<i></i>${stale ? (state.paused ? '显示已暂停' : '接收暂停') : '正常接收'}`
  const badge = document.querySelector('#terminalBadge')
  badge.className = `status-badge ${state.terminalOnline ? 'online' : 'offline'}`
  badge.innerHTML = `<i></i>${state.terminalOnline ? '采集终端在线' : '采集终端离线'}`
}

function drawChart() {
  const box = chart.getBoundingClientRect()
  const ratio = window.devicePixelRatio || 1
  chart.width = Math.max(1, Math.round(box.width * ratio))
  chart.height = Math.max(1, Math.round(box.height * ratio))
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
  const width = box.width, height = box.height
  const pad = { l: 46, r: 18, t: 18, b: 30 }
  ctx.clearRect(0, 0, width, height)
  ctx.strokeStyle = 'rgba(87,132,172,.22)'; ctx.lineWidth = 1
  for (let i = 0; i <= 5; i += 1) {
    const y = pad.t + (height - pad.t - pad.b) * i / 5
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(width - pad.r, y); ctx.stroke()
  }
  const data = state.records.slice(-70)
  if (data.length < 2) return
  sensors.forEach(sensor => {
    const values = data.map(item => item[sensor.key])
    const min = Math.min(...values), max = Math.max(...values), span = Math.max(max - min, .1)
    ctx.beginPath(); ctx.strokeStyle = sensor.color; ctx.lineWidth = 2
    values.forEach((value, index) => {
      const x = pad.l + index / (values.length - 1) * (width - pad.l - pad.r)
      const normalized = (value - min) / span
      const y = height - pad.b - normalized * (height - pad.t - pad.b) * .78 - (sensors.indexOf(sensor) % 2) * 3
      index ? ctx.lineTo(x, y) : ctx.moveTo(x, y)
    })
    ctx.stroke()
  })
  ctx.fillStyle = '#7895ae'; ctx.font = '11px sans-serif'
  ctx.fillText(formatTime(data[0].timestamp, false), pad.l, height - 9)
  const lastLabel = formatTime(data.at(-1).timestamp, false)
  ctx.fillText(lastLabel, width - pad.r - ctx.measureText(lastLabel).width, height - 9)
}

document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(item => { item.classList.remove('active'); item.setAttribute('aria-pressed', 'false') })
  document.querySelectorAll('.view').forEach(view => { view.classList.remove('active-view'); view.hidden = true })
  button.classList.add('active'); button.setAttribute('aria-pressed', 'true')
  const target = document.querySelector(`#${button.dataset.tab}`)
  target.hidden = false; target.classList.add('active-view')
  if (button.dataset.tab === 'monitor') requestAnimationFrame(drawChart)
}))

document.querySelector('#pauseButton').addEventListener('click', event => {
  state.paused = !state.paused
  event.currentTarget.textContent = state.paused ? '继续显示' : '暂停显示'
  event.currentTarget.setAttribute('aria-pressed', String(state.paused))
  updateStates()
})

document.querySelector('#disconnectButton').addEventListener('click', event => {
  state.terminalOnline = !state.terminalOnline
  event.currentTarget.textContent = state.terminalOnline ? '模拟终端离线' : '恢复终端连接'
  updateStates()
})

document.querySelector('#resetButton').addEventListener('click', seedRecords)
document.querySelector('#exportButton').addEventListener('click', () => {
  const header = ['采集时间','泄油口温度(°C)','泄油口压力(bar)','油口A压力(MPa)','油口B压力(MPa)']
  const rows = state.records.map(r => [r.timestamp.toISOString(),r.temp.toFixed(2),r.casePressure.toFixed(3),r.portA.toFixed(3),r.portB.toFixed(3)])
  const csv = '\ufeff' + [header, ...rows].map(row => row.join(',')).join('\r\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  link.download = `近端巡检演示数据_${new Date().toISOString().slice(0,10)}.csv`
  link.click(); URL.revokeObjectURL(link.href)
})

window.addEventListener('resize', drawChart)
setInterval(() => {
  if (!state.paused && state.terminalOnline && state.serviceOnline) appendRecord(nextRecord())
  else updateStates()
}, 1000)

seedRecords()
