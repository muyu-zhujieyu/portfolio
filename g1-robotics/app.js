const canvas = document.querySelector('#navMap')
const ctx = canvas.getContext('2d')
const cols = 20, rows = 14
const blocked = new Set()
for (let x = 5; x <= 13; x += 1) blocked.add(`${x},5`)
for (let y = 6; y <= 10; y += 1) blocked.add(`13,${y}`)
for (let y = 1; y <= 7; y += 1) blocked.add(`7,${y}`)
;['1,3','2,3','3,3','16,7','17,7','18,7','10,11','10,12'].forEach(key => blocked.add(key))

const state = { robot:{x:2,y:11}, goal:null, path:[], step:0, running:false, timer:null, targetLocked:false }
const start = {x:2,y:11}

function key(p){ return `${p.x},${p.y}` }
function neighbors(p){ return [{x:p.x+1,y:p.y},{x:p.x-1,y:p.y},{x:p.x,y:p.y+1},{x:p.x,y:p.y-1}].filter(n=>n.x>=0&&n.x<cols&&n.y>=0&&n.y<rows&&!blocked.has(key(n))) }
function heuristic(a,b){ return Math.abs(a.x-b.x)+Math.abs(a.y-b.y) }
function findPath(from,to){
  const open=[from], came=new Map(), g=new Map([[key(from),0]]), f=new Map([[key(from),heuristic(from,to)]])
  while(open.length){
    open.sort((a,b)=>(f.get(key(a))??Infinity)-(f.get(key(b))??Infinity))
    const current=open.shift()
    if(key(current)===key(to)){ const path=[current]; let cursor=key(current); while(came.has(cursor)){ const prev=came.get(cursor); path.unshift(prev); cursor=key(prev) } return path }
    for(const next of neighbors(current)){ const score=(g.get(key(current))??Infinity)+1; if(score<(g.get(key(next))??Infinity)){came.set(key(next),current);g.set(key(next),score);f.set(key(next),score+heuristic(next,to));if(!open.some(item=>key(item)===key(next)))open.push(next)} }
  }
  return []
}

function fitCanvas(){ const rect=canvas.getBoundingClientRect(),ratio=window.devicePixelRatio||1;canvas.width=Math.round(rect.width*ratio);canvas.height=Math.round(rect.height*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);draw() }
function draw(){
  const {width,height}=canvas.getBoundingClientRect(),cell=Math.min((width-42)/cols,(height-42)/rows),ox=(width-cell*cols)/2,oy=(height-cell*rows)/2
  ctx.clearRect(0,0,width,height);ctx.fillStyle='#0c1114';ctx.fillRect(0,0,width,height)
  ctx.strokeStyle='rgba(124,142,150,.12)';ctx.lineWidth=1
  for(let x=0;x<=cols;x++){ctx.beginPath();ctx.moveTo(ox+x*cell,oy);ctx.lineTo(ox+x*cell,oy+rows*cell);ctx.stroke()}
  for(let y=0;y<=rows;y++){ctx.beginPath();ctx.moveTo(ox,oy+y*cell);ctx.lineTo(ox+cols*cell,oy+y*cell);ctx.stroke()}
  blocked.forEach(item=>{const[x,y]=item.split(',').map(Number);ctx.fillStyle='#4a5258';ctx.fillRect(ox+x*cell+2,oy+y*cell+2,cell-4,cell-4)})
  if(state.path.length){ctx.strokeStyle='#48d9e8';ctx.lineWidth=Math.max(2,cell*.12);ctx.lineJoin='round';ctx.beginPath();state.path.forEach((p,i)=>{const px=ox+(p.x+.5)*cell,py=oy+(p.y+.5)*cell;i?ctx.lineTo(px,py):ctx.moveTo(px,py)});ctx.stroke()}
  if(state.goal){ctx.strokeStyle='#ff9b42';ctx.lineWidth=3;ctx.beginPath();ctx.arc(ox+(state.goal.x+.5)*cell,oy+(state.goal.y+.5)*cell,cell*.32,0,Math.PI*2);ctx.stroke()}
  const rx=ox+(state.robot.x+.5)*cell,ry=oy+(state.robot.y+.5)*cell;ctx.fillStyle='#b8f34a';ctx.beginPath();ctx.arc(rx,ry,cell*.3,0,Math.PI*2);ctx.fill();ctx.fillStyle='#111';ctx.font=`800 ${Math.max(8,cell*.22)}px sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('G1',rx,ry)
  ctx.fillStyle='#758087';ctx.font='10px ui-monospace,monospace';ctx.textAlign='left';ctx.fillText('SYNTHETIC MAP · 0.20 m/cell',ox,oy-10)
}

function log(message){const p=document.createElement('p'),time=document.createElement('time');time.textContent=new Date().toLocaleTimeString('zh-CN',{hour12:false});p.append(time,message);const box=document.querySelector('#eventLog');box.prepend(p)}
function allGatesReady(){return [...document.querySelectorAll('.gate')].every(item=>item.checked)}
function refreshStart(){document.querySelector('#startMission').disabled=!(allGatesReady()&&state.goal&&!state.running)}
function setGlobal(mode,label){const el=document.querySelector('#globalState');el.className=`state ${mode}`;el.innerHTML=`<i></i>${label}`}
function stopMission(reason='用户执行 STOP'){
  clearInterval(state.timer);state.running=false;document.querySelector('#bridgeText').textContent='LOCKED';document.querySelector('#taskText').textContent='STOPPED';document.querySelector('#missionBadge').className='mission-badge';document.querySelector('#missionBadge').textContent='已停止';document.querySelector('#motionHealth').classList.remove('done');document.querySelector('#motionHealth').querySelector('strong').textContent='已锁定 / stop_move';setGlobal('stopped','安全停止');log(reason);refreshStart()
}
function startMission(){
  state.path=findPath(state.robot,state.goal);if(!state.path.length){log('规划失败：目标不可达');return}
  state.step=0;state.running=true;document.querySelector('#bridgeText').textContent='ENABLED';document.querySelector('#taskText').textContent='NAVIGATING';document.querySelector('#missionBadge').className='mission-badge running';document.querySelector('#missionBadge').textContent='导航中';document.querySelector('#plannerHealth').classList.add('done');document.querySelector('#plannerHealth strong').textContent=`路径 ${state.path.length} 格`;document.querySelector('#motionHealth').classList.add('done');document.querySelector('#motionHealth strong').textContent='限幅桥接已启用';setGlobal('running','任务执行中');log(`规划成功，开始前往 (${state.goal.x}, ${state.goal.y})`);refreshStart();draw()
  state.timer=setInterval(()=>{state.step+=1;if(state.step>=state.path.length){clearInterval(state.timer);state.robot={...state.goal};state.running=false;document.querySelector('#bridgeText').textContent='LOCKED';document.querySelector('#taskText').textContent='DONE';document.querySelector('#missionBadge').className='mission-badge done';document.querySelector('#missionBadge').textContent='已到达';document.querySelector('#motionHealth strong').textContent='桥接关闭 / stop_move';setGlobal('ready','系统待命');log('目标到达：关闭桥接并调用 stop_move');refreshStart();draw();return}state.robot={...state.path[state.step]};document.querySelector('#positionText').textContent=`(${((state.robot.x-start.x)*.2).toFixed(2)}, ${((start.y-state.robot.y)*.2).toFixed(2)})`;draw()},170)
}

document.querySelectorAll('.goal').forEach(button=>button.addEventListener('click',()=>{if(state.running)return;document.querySelectorAll('.goal').forEach(item=>item.classList.remove('active'));button.classList.add('active');state.goal={x:Number(button.dataset.x),y:Number(button.dataset.y)};state.path=findPath(state.robot,state.goal);document.querySelector('#missionBadge').textContent=`目标 (${state.goal.x}, ${state.goal.y})`;document.querySelector('#plannerHealth strong').textContent=state.path.length?`预规划 ${state.path.length} 格`:'目标不可达';log(`选择目标 ${button.textContent.trim()}`);refreshStart();draw()}))
document.querySelectorAll('.gate').forEach(box=>box.addEventListener('change',refreshStart))
document.querySelector('#startMission').addEventListener('click',startMission)
document.querySelector('#stopMission').addEventListener('click',()=>stopMission())
document.querySelector('#resetDemo').addEventListener('click',()=>{clearInterval(state.timer);Object.assign(state,{robot:{...start},goal:null,path:[],step:0,running:false});document.querySelectorAll('.goal,.gate').forEach(item=>{item.classList?.remove('active');if('checked'in item)item.checked=false});document.querySelector('#positionText').textContent='(0.00, 0.00)';document.querySelector('#bridgeText').textContent='LOCKED';document.querySelector('#taskText').textContent='IDLE';document.querySelector('#missionBadge').className='mission-badge';document.querySelector('#missionBadge').textContent='等待目标';document.querySelector('#plannerHealth').classList.remove('done');document.querySelector('#plannerHealth strong').textContent='等待目标';document.querySelector('#motionHealth').classList.remove('done');document.querySelector('#motionHealth strong').textContent='默认锁定';setGlobal('ready','系统待命');log('仿真已重置到固定起点');refreshStart();draw()})

document.querySelector('#lockTarget').addEventListener('click',()=>{state.targetLocked=true;document.querySelector('#solveIk').disabled=false;document.querySelector('#armStatus').className='arm-status';document.querySelector('#armStatus').textContent='目标已锁定；下一步只计算 IK，不运动。';log('视觉目标已手动锁定（dry-run）')})
document.querySelector('#solveIk').addEventListener('click',()=>{const residual=1.1+Math.random()*.7,condition=42+Math.floor(Math.random()*28);document.querySelector('#residualValue').textContent=`${residual.toFixed(1)} mm`;document.querySelector('#conditionValue').textContent=String(condition);const pass=residual<=2&&condition<=100;const status=document.querySelector('#armStatus');status.className=`arm-status ${pass?'pass':'reject'}`;status.textContent=pass?'IK 预检通过，但因缺少碰撞与接触安全链，真机执行保持禁用。':'IK 安全拒绝：指标未通过，不生成执行命令。';log(`IK dry-run：residual=${residual.toFixed(1)} mm, condition=${condition}, ${pass?'PASS':'REJECT'}`)})

window.addEventListener('resize',fitCanvas)
fitCanvas();refreshStart();log('仿真初始化完成：运动桥接默认锁定')
