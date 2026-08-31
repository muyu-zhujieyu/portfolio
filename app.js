const STORAGE_KEY = 'liteHabitData';
const EMOJIS = ['🌿', '📚', '🏃', '🧘', '✍️', '💧', '🌙', '🎯'];
const PRESET_HABITS = [
    { name: '早起不赖床', icon: '🌤️', category: '生活', note: '固定起床时间，给一天一个清晰开始' },
    { name: '阅读 10 分钟', icon: '📚', category: '成长', note: '每天读一点，比偶尔读很多更有效' },
    { name: '散步 20 分钟', icon: '🚶', category: '健康', note: '低压力活动，适合建立运动节奏' },
    { name: '冥想 5 分钟', icon: '🧘', category: '专注', note: '短暂暂停，让注意力重新归位' },
    { name: '喝够 8 杯水', icon: '💧', category: '健康', note: '用可见次数降低健康目标的难度' },
    { name: '每日复盘', icon: '✍️', category: '成长', note: '写下一个收获和一个待改进点' },
    { name: '23 点前入睡', icon: '🌙', category: '健康', note: '稳定作息比周末补觉更重要' },
    { name: '专注 25 分钟', icon: '🎯', category: '专注', note: '一次只推进一件最重要的事' },
    { name: '整理桌面', icon: '🧹', category: '生活', note: '两分钟收尾，减少明天的启动阻力' },
    { name: '背 10 个单词', icon: '🗣️', category: '成长', note: '控制每日数量，让复习可以持续' },
    { name: '拉伸 8 分钟', icon: '🤸', category: '健康', note: '久坐后舒展身体，缓解紧张感' },
    { name: '不刷短视频', icon: '📵', category: '专注', note: '为真正重要的事情留出注意力' }
];

let activeCategory = '全部';
let selectedEmoji = EMOJIS[0];
let toastTimer = null;

function emptyData() {
    return { version: 2, habits: [], checkins: [], settings: { theme: 'light', reminders: true } };
}

function getData() {
    try {
        const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY));
        if (!parsed || !Array.isArray(parsed.habits) || !Array.isArray(parsed.checkins)) return emptyData();
        parsed.version = 2;
        parsed.settings = { ...emptyData().settings, ...(parsed.settings || {}) };
        parsed.habits = parsed.habits.map(habit => ({ category: '生活', reminder: '', ...habit }));
        return parsed;
    } catch (_) {
        return emptyData();
    }
}

function saveData(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function dateKey(date = new Date()) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function offsetDateKey(offset) {
    const date = new Date();
    date.setHours(12, 0, 0, 0);
    date.setDate(date.getDate() + offset);
    return dateKey(date);
}

function parseDate(key) {
    const [year, month, day] = key.split('-').map(Number);
    return new Date(year, month - 1, day, 12);
}

function dayDistance(first, second) {
    return Math.round((parseDate(second) - parseDate(first)) / 86400000);
}

function checkedToday(habitId, checkins) {
    const today = dateKey();
    return checkins.some(item => item.habitId === habitId && item.date === today);
}

function checkinDates(checkins, habitId = null) {
    return [...new Set(checkins.filter(item => !habitId || item.habitId === habitId).map(item => item.date))].sort();
}

function streakMetrics(checkins, habitId = null) {
    const dates = checkinDates(checkins, habitId);
    if (!dates.length) return { current: 0, longest: 0 };
    let longest = 1;
    let running = 1;
    for (let index = 1; index < dates.length; index += 1) {
        if (dayDistance(dates[index - 1], dates[index]) === 1) running += 1;
        else running = 1;
        longest = Math.max(longest, running);
    }
    const set = new Set(dates);
    let cursor = set.has(dateKey()) ? new Date() : new Date(Date.now() - 86400000);
    cursor.setHours(12, 0, 0, 0);
    let current = 0;
    while (set.has(dateKey(cursor))) {
        current += 1;
        cursor.setDate(cursor.getDate() - 1);
    }
    return { current, longest };
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function generateCoachTip(habits, checkins) {
    if (!habits.length) return '先建立一个足够小的目标，比追求完美更容易坚持。';
    const done = habits.filter(habit => checkedToday(habit.id, checkins)).length;
    const streak = streakMetrics(checkins).current;
    if (done === habits.length) return streak >= 7 ? `今天全部完成，连续 ${streak} 天的节奏已经很稳了。` : '今日清单已全部完成。现在停下来庆祝这次小胜利。';
    if (new Date().getHours() >= 20 && done === 0) return '时间有点晚了，选最容易的一项完成即可，不必追求全部。';
    if (done > 0) return `已经完成 ${done} 项。下一项从最省力的动作开始，会更容易继续。`;
    if (checkins.length >= 7) return '过去的记录证明你做得到。今天只需要再完成一次。';
    return '先完成最小的一项，为今天建立一个明确的“已开始”信号。';
}

function renderHome(data) {
    const { habits, checkins, settings } = data;
    const done = habits.filter(habit => checkedToday(habit.id, checkins)).length;
    const percent = habits.length ? Math.round(done / habits.length * 100) : 0;
    const streak = streakMetrics(checkins).current;
    const now = new Date();
    const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][now.getDay()];
    document.getElementById('todayLabel').textContent = `${now.getMonth() + 1}月${now.getDate()}日 · ${weekday}`;
    document.getElementById('streakDisplay').textContent = `🔥 ${streak} 天`;
    document.getElementById('doneToday').textContent = done;
    document.getElementById('leftToday').textContent = Math.max(0, habits.length - done);
    document.getElementById('progressPercent').textContent = `${percent}%`;
    document.getElementById('progressRing').style.setProperty('--progress', `${percent * 3.6}deg`);
    document.getElementById('progressHeadline').textContent = !habits.length ? '从一件小事开始' : percent === 100 ? '今天，圆满收官' : done ? '保持这个节奏' : '迈出今天第一步';
    document.getElementById('progressCaption').textContent = !habits.length ? '添加一个想坚持的习惯，今天就能开始。' : percent === 100 ? '你已经完成今日全部习惯，做得很好。' : `今日 ${habits.length} 项习惯，完成任意一项都算进步。`;
    document.getElementById('coachTip').textContent = generateCoachTip(habits, checkins);

    const list = document.getElementById('habitList');
    const empty = document.getElementById('emptyHint');
    empty.hidden = habits.length > 0;
    list.innerHTML = habits.map(habit => {
        const doneToday = checkedToday(habit.id, checkins);
        const count = checkins.filter(item => item.habitId === habit.id).length;
        const habitStreak = streakMetrics(checkins, habit.id).current;
        const reminder = settings.reminders && habit.reminder ? ` · ${habit.reminder} 提醒` : '';
        return `<article class="habit-card ${doneToday ? 'done' : ''}">
            <div class="habit-icon" aria-hidden="true">${escapeHtml(habit.icon)}</div>
            <div class="habit-info"><div class="habit-title"><strong>${escapeHtml(habit.name)}</strong><small>${escapeHtml(habit.category)}</small></div>
            <p class="habit-meta">累计 ${count} 次 · 连续 ${habitStreak} 天${reminder}</p></div>
            <div class="habit-actions"><button class="delete-habit" data-delete-habit="${habit.id}" aria-label="删除${escapeHtml(habit.name)}">×</button>
            <button class="check-button" data-toggle-habit="${habit.id}" aria-label="${doneToday ? '取消今日打卡' : '完成今日打卡'}">✓</button></div>
        </article>`;
    }).join('');
}

function renderDiscover(data) {
    const categories = ['全部', ...new Set(PRESET_HABITS.map(item => item.category))];
    document.getElementById('categoryTabs').innerHTML = categories.map(category => `<button class="category-tab ${category === activeCategory ? 'active' : ''}" data-category="${category}">${category}</button>`).join('');
    const names = new Set(data.habits.map(habit => habit.name));
    const filtered = activeCategory === '全部' ? PRESET_HABITS : PRESET_HABITS.filter(item => item.category === activeCategory);
    document.getElementById('presetGrid').innerHTML = filtered.map(item => {
        const added = names.has(item.name);
        return `<button class="preset-card ${added ? 'added' : ''}" data-preset-name="${escapeHtml(item.name)}" ${added ? 'disabled' : ''}>
            <span class="preset-emoji">${item.icon}</span><strong>${item.name}</strong><small>${item.note}</small><em>${added ? '✓ 已添加' : '＋ 添加习惯'}</em>
        </button>`;
    }).join('');
}

function weeklyCounts(checkins, numberOfDays = 7) {
    return Array.from({ length: numberOfDays }, (_, index) => {
        const offset = index - numberOfDays + 1;
        const key = offsetDateKey(offset);
        return { key, count: checkins.filter(item => item.date === key).length };
    });
}

function drawWeekChart(checkins) {
    const canvas = document.getElementById('weekChart');
    if (!canvas || !canvas.clientWidth) return;
    const data = weeklyCounts(checkins);
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = 170;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    const ctx = canvas.getContext('2d');
    ctx.scale(ratio, ratio);
    const styles = getComputedStyle(document.body);
    const primary = styles.getPropertyValue('--primary').trim();
    const muted = styles.getPropertyValue('--muted').trim();
    const line = styles.getPropertyValue('--line').trim();
    const left = 12, right = 8, top = 18, bottom = 28;
    const max = Math.max(3, ...data.map(item => item.count));
    ctx.clearRect(0, 0, width, height);
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = muted;
    ctx.strokeStyle = line;
    ctx.lineWidth = 1;
    for (let row = 0; row <= 3; row += 1) {
        const y = top + (height - top - bottom) * row / 3;
        ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(width - right, y); ctx.stroke();
    }
    const points = data.map((item, index) => ({
        x: left + index * (width - left - right) / (data.length - 1),
        y: top + (max - item.count) / max * (height - top - bottom),
        ...item
    }));
    const gradient = ctx.createLinearGradient(0, top, 0, height - bottom);
    gradient.addColorStop(0, `${primary}45`); gradient.addColorStop(1, `${primary}00`);
    ctx.beginPath(); ctx.moveTo(points[0].x, height - bottom); points.forEach(point => ctx.lineTo(point.x, point.y)); ctx.lineTo(points.at(-1).x, height - bottom); ctx.closePath(); ctx.fillStyle = gradient; ctx.fill();
    ctx.beginPath(); points.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y)); ctx.strokeStyle = primary; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'; ctx.stroke();
    points.forEach(point => { ctx.beginPath(); ctx.arc(point.x, point.y, 3.5, 0, Math.PI * 2); ctx.fillStyle = primary; ctx.fill(); });
    data.forEach((item, index) => { const date = parseDate(item.key); ctx.fillStyle = muted; ctx.fillText(['日','一','二','三','四','五','六'][date.getDay()], points[index].x, height - 8); });
}

function renderInsights(data) {
    const metrics = streakMetrics(data.checkins);
    document.getElementById('statCheckins').textContent = data.checkins.length;
    document.getElementById('statCurrentStreak').textContent = metrics.current;
    document.getElementById('statLongestStreak').textContent = metrics.longest;
    const week = weeklyCounts(data.checkins);
    const recent = week.slice(-3).reduce((sum, item) => sum + item.count, 0);
    const previous = week.slice(-6, -3).reduce((sum, item) => sum + item.count, 0);
    document.getElementById('trendBadge').textContent = recent > previous ? '↗ 状态上升' : recent ? '保持节奏' : '等待积累';
    const maxDay = Math.max(1, ...weeklyCounts(data.checkins, 28).map(item => item.count));
    document.getElementById('heatmap').innerHTML = weeklyCounts(data.checkins, 28).map(item => {
        const level = item.count ? Math.min(3, Math.ceil(item.count / maxDay * 3)) : 0;
        return `<span class="heat-cell level-${level}" title="${item.key}：${item.count} 次"></span>`;
    }).join('');
    const achievements = [
        { icon: '🌱', title: '第一次开始', note: '完成 1 次打卡', unlocked: data.checkins.length >= 1 },
        { icon: '✨', title: '积少成多', note: '累计完成 7 次', unlocked: data.checkins.length >= 7 },
        { icon: '🔥', title: '一周节奏', note: '连续活跃 7 天', unlocked: metrics.longest >= 7 },
        { icon: '🏅', title: '习惯养成者', note: '累计完成 30 次', unlocked: data.checkins.length >= 30 }
    ];
    document.getElementById('achievementCount').textContent = `${achievements.filter(item => item.unlocked).length} / ${achievements.length}`;
    document.getElementById('achievementList').innerHTML = achievements.map(item => `<article class="achievement ${item.unlocked ? 'unlocked' : ''}"><span class="achievement-icon">${item.icon}</span><div><strong>${item.title}</strong><small>${item.note}</small></div><b>${item.unlocked ? '已解锁' : '未解锁'}</b></article>`).join('');
}

function renderProfile(data) {
    const metrics = streakMetrics(data.checkins);
    document.getElementById('profileSummary').textContent = data.habits.length ? `正在坚持 ${data.habits.length} 项习惯，历史最长连续 ${metrics.longest} 天。` : '从今天开始，积累微小改变。';
    document.getElementById('reminderToggle').checked = data.settings.reminders;
    document.getElementById('themeToggle').checked = data.settings.theme === 'dark';
}

function renderAll() {
    const data = getData();
    document.body.classList.toggle('dark', data.settings.theme === 'dark');
    renderHome(data); renderDiscover(data); renderInsights(data); renderProfile(data);
    if (document.getElementById('page-insights').classList.contains('active')) requestAnimationFrame(() => drawWeekChart(data.checkins));
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 1900);
}

function celebrate() {
    const container = document.getElementById('celebration');
    const colors = ['#e6ad52', '#67b795', '#f08b75', '#6d93c6'];
    container.innerHTML = Array.from({ length: 18 }, (_, index) => `<i class="spark" style="left:${45 + Math.random() * 10}%;background:${colors[index % colors.length]};--x:${(Math.random() - .5) * 260}px;--y:${-70 - Math.random() * 210}px"></i>`).join('');
    setTimeout(() => { container.innerHTML = ''; }, 900);
}

function toggleHabit(habitId) {
    const data = getData();
    const index = data.checkins.findIndex(item => item.habitId === habitId && item.date === dateKey());
    if (index >= 0) {
        data.checkins.splice(index, 1); showToast('已取消今日打卡');
    } else {
        data.checkins.push({ habitId, date: dateKey(), createdAt: new Date().toISOString() });
        showToast('完成一次小坚持 ✓'); celebrate();
    }
    saveData(data); renderAll();
}

function addHabit(habit) {
    const data = getData();
    if (data.habits.some(item => item.name === habit.name)) return showToast('这个习惯已经在清单里了');
    data.habits.push({ id: `h_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`, createdAt: new Date().toISOString(), reminder: '', ...habit });
    saveData(data); renderAll(); showToast(`已添加「${habit.name}」`);
}

function deleteHabit(habitId) {
    const data = getData();
    const habit = data.habits.find(item => item.id === habitId);
    if (!habit || !confirm(`删除「${habit.name}」及其全部打卡记录吗？`)) return;
    data.habits = data.habits.filter(item => item.id !== habitId);
    data.checkins = data.checkins.filter(item => item.habitId !== habitId);
    saveData(data); renderAll(); showToast('习惯已删除');
}

function switchPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.toggle('active', page.id === pageId));
    document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('active', item.dataset.page === pageId));
    document.getElementById(pageId)?.scrollTo({ top: 0 });
    if (pageId === 'page-insights') requestAnimationFrame(() => drawWeekChart(getData().checkins));
}

function openHabitDialog() {
    const dialog = document.getElementById('habitDialog');
    document.getElementById('habitForm').reset();
    document.getElementById('habitReminder').value = '20:00';
    selectedEmoji = EMOJIS[0]; renderEmojiPicker();
    dialog.showModal();
    setTimeout(() => document.getElementById('habitName').focus(), 100);
}

function renderEmojiPicker() {
    document.getElementById('emojiPicker').innerHTML = EMOJIS.map(emoji => `<button class="emoji-option ${emoji === selectedEmoji ? 'selected' : ''}" type="button" data-emoji="${emoji}">${emoji}</button>`).join('');
}

function download(filename, content, mime) {
    const url = URL.createObjectURL(new Blob([content], { type: mime }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

document.addEventListener('click', event => {
    const toggle = event.target.closest('[data-toggle-habit]'); if (toggle) return toggleHabit(toggle.dataset.toggleHabit);
    const remove = event.target.closest('[data-delete-habit]'); if (remove) return deleteHabit(remove.dataset.deleteHabit);
    const nav = event.target.closest('[data-page]'); if (nav) return switchPage(nav.dataset.page);
    const jump = event.target.closest('[data-page-jump]'); if (jump) return switchPage(jump.dataset.pageJump);
    if (event.target.closest('[data-open-habit-dialog]')) return openHabitDialog();
    const category = event.target.closest('[data-category]'); if (category) { activeCategory = category.dataset.category; return renderDiscover(getData()); }
    const preset = event.target.closest('[data-preset-name]'); if (preset && !preset.disabled) { const item = PRESET_HABITS.find(entry => entry.name === preset.dataset.presetName); if (item) addHabit(item); return; }
    const emoji = event.target.closest('[data-emoji]'); if (emoji) { selectedEmoji = emoji.dataset.emoji; renderEmojiPicker(); }
});

document.getElementById('habitForm').addEventListener('submit', event => {
    event.preventDefault();
    const name = document.getElementById('habitName').value.trim();
    if (!name) return;
    addHabit({ name, icon: selectedEmoji, category: document.getElementById('habitCategory').value, reminder: document.getElementById('habitReminder').value });
    document.getElementById('habitDialog').close();
});

document.getElementById('reminderToggle').addEventListener('change', event => { const data = getData(); data.settings.reminders = event.target.checked; saveData(data); renderAll(); showToast(event.target.checked ? '已显示习惯提醒时间' : '已隐藏提醒时间'); });
document.getElementById('themeToggle').addEventListener('change', event => { const data = getData(); data.settings.theme = event.target.checked ? 'dark' : 'light'; saveData(data); renderAll(); });
document.getElementById('exportJson').addEventListener('click', () => { download(`LiteHabit-backup-${dateKey()}.json`, JSON.stringify(getData(), null, 2), 'application/json;charset=utf-8'); showToast('备份文件已生成'); });
document.getElementById('exportCsv').addEventListener('click', () => {
    const data = getData(); const names = new Map(data.habits.map(habit => [habit.id, habit.name]));
    const escapeCsv = value => `"${String(value).replaceAll('"', '""')}"`;
    const rows = [['日期', '习惯', '习惯ID'], ...data.checkins.map(item => [item.date, names.get(item.habitId) || '已删除习惯', item.habitId])];
    download(`LiteHabit-checkins-${dateKey()}.csv`, '\ufeff' + rows.map(row => row.map(escapeCsv).join(',')).join('\r\n'), 'text/csv;charset=utf-8'); showToast('CSV 记录已生成');
});
document.getElementById('resetData').addEventListener('click', () => { if (!confirm('确认清除全部习惯、打卡记录与设置吗？此操作无法撤销。')) return; localStorage.removeItem(STORAGE_KEY); renderAll(); switchPage('page-home'); showToast('全部数据已重置'); });
window.addEventListener('resize', () => { if (document.getElementById('page-insights').classList.contains('active')) drawWeekChart(getData().checkins); });

renderEmojiPicker();
renderAll();
