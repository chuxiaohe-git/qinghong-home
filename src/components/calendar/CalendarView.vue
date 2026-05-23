<template>
  <div class="calendar-view">
    <div class="cal-header">
      <div class="cal-title">
        <h2>🐟 摸鱼日历</h2>
        <span class="year-tag">{{ viewYear }}</span>
        <span class="cal-range">{{ rangeLabel }}</span>
      </div>
      <div class="week-nav">
        <button class="nav-btn" @click="weekOffset(-1)">‹</button>
        <span class="week-label">第{{ weekNumValue }}周</span>
        <button class="nav-btn" @click="weekOffset(1)">›</button>
      </div>
    </div>

    <div class="week-grid-wrap">
    <Transition :name="slideDir">
      <div class="week-grid" :key="viewKey">
        <div v-for="d in weekDays" :key="d.key" class="day-col"
          :class="{ today: d.isToday, weekend: d.isWeekend }"
          @contextmenu.prevent="openDayCtx($event, d.date)">
          <div class="day-header">
            <div class="day-name">{{ d.weekday }}</div>
            <div class="day-date">{{ d.day }}</div>
            <div class="day-month">{{ d.month }}月</div>
          </div>
          <div class="day-notes" :data-date="d.key">
            <div v-for="(n, idx) in getNotes(d.key)" :key="n._key || n.id"
              class="cal-note"
              :class="{ done: n.done, editing: editingId === n.id }"
              :style="getNoteStyle(n, idx)"
              :data-id="n.id"
              @contextmenu.prevent="openCtx($event, n)">
              <label class="note-checkbx" @click.stop>
                <input type="checkbox" :checked="n.done" @change="toggleDone(n)" />
                <span class="bx-icon"></span>
              </label>
              <div v-if="editingId === n.id" ref="editContentRef"
                class="note-content note-editing" contenteditable="true"
                @blur="confirmEdit(n, $event)" @click.stop
                @keydown.ctrl.enter="confirmEdit(n, $event)" @keydown.esc="cancelEdit">{{ n.title }}</div>
              <span v-else class="note-content">{{ n.title }}</span>
              <span v-if="n.reminder_at" class="note-bell">🔔</span>
            </div>
            <div v-if="getNotes(d.key).length === 0" class="empty-hint">
              <div class="empty-icon">🐟</div>
              <div class="empty-text">奉旨摸鱼</div>
              <div class="empty-seal">钦 此</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
    </div>

    <div class="day-nav">
      <button class="nav-btn" @click="dayOffset(-1)">‹ 前一天</button>
      <button class="today-btn" @click="scrollToToday">📅 回到今日</button>
      <button class="nav-btn" @click="dayOffset(1)">后一天 ›</button>
    </div>

    <Teleport to="body"><div v-if="ctxVisible" class="ctx-menu" @click.stop :style="{ left: ctxX + 'px', top: ctxY + 'px' }">
      <button class="ctx-item" @click="startAddNoteFromNote">📝 添加待办</button>
      <button class="ctx-item" @click="startEditNote">✏️ 修改</button>
      <button class="ctx-item" @click="openReminderPicker">🔔 设置提醒</button>
      <button v-if="ctxTodo?.reminder_at" class="ctx-item" @click="clearReminder">🔕 取消提醒</button>
      <button class="ctx-item" @click="deleteNote">🗑 删除</button>
    </div></Teleport>
    <Teleport to="body"><div v-if="dayCtxVisible" class="ctx-menu" @click.stop :style="{ left: dayCtxX + 'px', top: dayCtxY + 'px' }">
      <button class="ctx-item" @click="startAddNote">📝 添加待办</button>
    </div></Teleport>
    <Teleport to="body"><div v-if="showReminderPicker" class="input-overlay" @click.self="showReminderPicker = false">
      <div class="input-card">
        <div class="input-title">🔔 设置提醒时间</div>
        <div class="reminder-target">「{{ ctxTodo?.title }}」</div>
        <input v-model="reminderTime" type="datetime-local" class="input-field" />
        <div class="input-actions">
          <button class="btn-cancel" @click="showReminderPicker = false">取消</button>
          <button class="btn-confirm" @click="confirmReminder">确定</button>
        </div>
      </div>
    </div></Teleport>
    <Teleport to="body"><div v-if="showAddTodo" class="edit-overlay" @click.self="cancelAddTodo">
      <div class="edit-sticky" :style="addTodoStickyStyle">
        <div class="edit-sticky-header">📝 添加待办</div>
        <textarea ref="addTodoInputRef" class="edit-sticky-text" v-model="addTodoText"
          maxlength="200" @keydown.esc="cancelAddTodo"
          @keydown.ctrl.enter="confirmAddTodo"
          placeholder="输入待办内容..."></textarea>
        <div class="edit-sticky-actions">
          <button class="edit-sticky-btn edit-sticky-cancel" @click="cancelAddTodo">取消</button>
          <button class="edit-sticky-btn edit-sticky-confirm" @click="confirmAddTodo">✓ 确定</button>
        </div>
      </div>
    </div></Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch, Transition } from 'vue'
import Sortable from 'sortablejs'
import { getCalendarTodos, createCalendarTodo, updateCalendarTodo, deleteCalendarTodo } from '@/api/calendar'
import { updateTodo } from '@/api/todo'
import { NOTE_COLORS, NOTE_STYLES, NOTE_STYLES_DARK, LIGHT_TO_DARK, randomColor } from '@/constants/colors'

const emit = defineEmits(['todo-changed'])

const props = defineProps({
  refreshKey: { type: Number, default: 0 },
})

watch(() => props.refreshKey, () => { loadTodos() })

const viewStart = ref(getMonday(new Date()))
const todos = ref([])
const showReminderPicker = ref(false)
const reminderTime = ref('')
const editingId = ref(null)
const editContentRef = ref(null)
const showAddTodo = ref(false)
const addTodoText = ref('')
const addTodoDate = ref(null)
const addTodoColor = ref({ bg: '#FFEAA7', text: '#2d3436' })
const addTodoInputRef = ref(null)
const addTodoStickyStyle = computed(() => ({
  left: Math.min(dayCtxX.value, window.innerWidth - 340) + 'px',
  top: Math.min(dayCtxY.value, window.innerHeight - 200) + 'px',
  backgroundColor: addTodoColor.value.bg,
  color: addTodoColor.value.text,
}))
const ctxVisible = ref(false)
const ctxX = ref(0)
const ctxY = ref(0)
const ctxTodo = ref(null)
const dayCtxVisible = ref(false)
const dayCtxX = ref(0)
const dayCtxY = ref(0)
const dayCtxDate = ref(null)
const slideDir = ref('slide-left')
const viewKey = ref(0)
let sortableInstances = []
const isDark = ref(!document.documentElement.classList.contains('light-theme'))
let themeObserver = null

function getNoteStyle(n, idx) {
  let bgColor = n.color
  if (!bgColor) {
    bgColor = NOTE_STYLES[Math.abs(n.id) % NOTE_STYLES.length].bg
  }
  const posX = Math.round((n.id * 37 + idx * 73) % 71)
  const posY = Math.round((n.id * 53 + idx * 97) % 71)
  const texBlend = isDark.value ? 'overlay' : 'multiply'
  const texOpacity = isDark.value ? '0.3' : '0.15'
  if (!isDark.value) {
    const match = NOTE_STYLES.find(s => s.bg === bgColor)
    return { backgroundColor: bgColor, color: match ? match.text : '#2d3436', '--bg-pos': `${posX}% ${posY}%`, '--tex-blend': texBlend, '--tex-opacity': texOpacity }
  }
  const dark = LIGHT_TO_DARK.get(bgColor)
  if (dark) {
    return { backgroundColor: dark.bg, color: dark.text, '--bg-pos': `${posX}% ${posY}%`, '--tex-blend': texBlend, '--tex-opacity': texOpacity }
  }
  return { backgroundColor: bgColor, color: '#2d3436', '--bg-pos': `${posX}% ${posY}%`, '--tex-blend': texBlend, '--tex-opacity': texOpacity }
}

function getMonday(d) {
  const date = new Date(d); const day = date.getDay(); const diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff); date.setHours(0, 0, 0, 0); return date
}
function fmtKey(d) { const y=d.getFullYear();const m=String(d.getMonth()+1).padStart(2,'0');const dd=String(d.getDate()).padStart(2,'0');return `${y}-${m}-${dd}` }
function weekNum(d) { const s=new Date(d.getFullYear(),0,1);return Math.ceil(((d-s+(s.getTimezoneOffset()-d.getTimezoneOffset())*60000)/86400000+s.getDay()+1)/7) }
function isToday(d) { const t=new Date();return d.getFullYear()===t.getFullYear()&&d.getMonth()===t.getMonth()&&d.getDate()===t.getDate() }
const weekDays = computed(() => Array.from({length:7},(_,i)=>{const d=new Date(viewStart.value);d.setDate(viewStart.value.getDate()+i);return{key:fmtKey(d),date:fmtKey(d),weekday:['日','一','二','三','四','五','六'][d.getDay()],month:d.getMonth()+1,day:d.getDate(),isToday:isToday(d),isWeekend:d.getDay()===0||d.getDay()===6}}))
const viewYear = computed(() => viewStart.value.getFullYear())
const weekNumValue = computed(() => weekNum(viewStart.value))
const rangeLabel = computed(() => {const f=weekDays.value[0],l=weekDays.value[6];return `${f.month}月${f.day}日 - ${l.month}月${l.day}日`})
function getNotes(k) { return todos.value.filter(t=>t.date===k) }
async function loadTodos() { const s=weekDays.value[0].key,e=weekDays.value[6].key; try{const r=await getCalendarTodos(s,e);todos.value=r.data||[]}catch{todos.value=[]}; nextTick(()=>setTimeout(initSortable,50)) }
function weekOffset(o) { slideDir.value=o<0?'slide-right':'slide-left'; viewKey.value++; viewStart.value.setDate(viewStart.value.getDate()+o*7);viewStart.value=new Date(viewStart.value);setTimeout(loadTodos,260) }
function dayOffset(o) { slideDir.value=o<0?'day-right':'day-left'; viewKey.value++; viewStart.value.setDate(viewStart.value.getDate()+o);viewStart.value=new Date(viewStart.value);setTimeout(loadTodos,260) }
function openDayCtx(e,d) { dayCtxX.value=Math.min(e.clientX,window.innerWidth-120);dayCtxY.value=Math.min(e.clientY,window.innerHeight-100);dayCtxDate.value=d;dayCtxVisible.value=true }
function startAddNote() { dayCtxVisible.value=false;addTodoDate.value=dayCtxDate.value;addTodoText.value='';const col=randomColor();const m=NOTE_STYLES.find(s=>s.bg===col);addTodoColor.value=m||{bg:col,text:'#fff'};showAddTodo.value=true;nextTick(()=>addTodoInputRef.value?.focus()) }
function startAddNoteFromNote() { if(!ctxTodo.value)return;const date=ctxTodo.value.date;closeAllMenus();addTodoDate.value=date;addTodoText.value='';const col=randomColor();const m=NOTE_STYLES.find(s=>s.bg===col);addTodoColor.value=m||{bg:col,text:'#fff'};showAddTodo.value=true;nextTick(()=>addTodoInputRef.value?.focus()) }
async function confirmAddTodo() { const t=addTodoText.value.trim();if(!t)return; try{const r=await createCalendarTodo({date:addTodoDate.value,title:t,color:addTodoColor.value.bg});todos.value.push(r.data);emit('todo-changed')}catch{} showAddTodo.value=false }
function cancelAddTodo() { showAddTodo.value=false }
function startEditNote() { if(!ctxTodo.value)return;editingId.value=ctxTodo.value.id;closeAllMenus();nextTick(()=>{const el=editContentRef.value;if(!el)return;const r=document.createRange();r.selectNodeContents(el);r.collapse(false);const s=window.getSelection();s?.removeAllRanges();s?.addRange(r)}) }
async function confirmEdit(n,e) { const el=e?.target||editContentRef.value,t=el?.innerText?.trim();if(!t){editingId.value=null;return} try{const r=await updateCalendarTodo(n.id,{title:t});Object.assign(n,r.data);emit('todo-changed')}catch{} editingId.value=null }
function cancelEdit() { editingId.value=null }
async function toggleDone(n) { try{const r=await updateCalendarTodo(n.id,{done:!n.done});Object.assign(n,r.data);emit('todo-changed')}catch{} }
async function deleteNote() { if(!ctxTodo.value)return;const id=ctxTodo.value.id;closeAllMenus();try{await deleteCalendarTodo(id);todos.value=todos.value.filter(t=>t.id!==id);emit('todo-changed')}catch(e){console.error('delete calendar todo error:',e)} }
function openReminderPicker() { if(!ctxTodo.value)return;const n=new Date();n.setMinutes(0,0,0);n.setHours(n.getHours()+1);const y=n.getFullYear(),m=String(n.getMonth()+1).padStart(2,'0'),d=String(n.getDate()).padStart(2,'0'),h=String(n.getHours()).padStart(2,'0'),mi=String(n.getMinutes()).padStart(2,'0');reminderTime.value=`${y}-${m}-${d}T${h}:${mi}`;showReminderPicker.value=true;closeAllMenus() }
function confirmReminder() { if(!reminderTime.value||!ctxTodo.value)return;const dt=reminderTime.value.replace('T',' ');updateCalendarTodo(ctxTodo.value.id,{reminder_at:dt}).then(r=>{Object.assign(ctxTodo.value,r.data);showReminderPicker.value=false}).catch(()=>{}) }
function clearReminder() { const t=ctxTodo.value;if(!t)return;closeAllMenus();updateCalendarTodo(t.id,{reminder_at:null}).then(r=>{Object.assign(t,r.data)}).catch(()=>{}) }
function openCtx(e,t) { e.stopPropagation();ctxTodo.value=t;ctxX.value=Math.min(e.clientX,window.innerWidth-120);ctxY.value=Math.min(e.clientY,window.innerHeight-100);ctxVisible.value=true }
function closeAllMenus() { ctxVisible.value=false;ctxTodo.value=null;dayCtxVisible.value=false }

// ── SortableJS（同列+跨列+跨组件） ──
function initSortable() {
  sortableInstances.forEach(s=>s.destroy())
  sortableInstances = []
  document.querySelectorAll('.day-notes').forEach(el => {
    const s = new Sortable(el, {
      group: 'shared-todos',
      animation: 250,
      easing: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
      ghostClass: 'cal-note-ghost',
      scroll: false, sort: true,
      onStart: (evt) => {
        const id = parseInt(evt.item.dataset.id)
        const todo = todos.value.find(t => t.id === id)
        if (todo) window.__dragPayload = { type:'calendar', id:todo.id, title:todo.title, color:todo.color }
      },
      onEnd: async (evt) => {
        // 跨组件拖拽（拖到右侧待办面板）：立即移除本地数据，由 onAdd 处理
        if (!evt.to || !evt.to.dataset || !evt.to.dataset.date) {
          const itemId = parseInt(evt.item.dataset.id)
          todos.value = todos.value.filter(t => t.id !== itemId)
          return
        }
        // 日历内部拖拽
        const fromDate = evt.from.dataset.date
        const toDate = evt.to.dataset.date
        const itemId = parseInt(evt.item.dataset.id)
        const newIdx = evt.newIndex
        if (evt.from === evt.to) {
          await updateCalendarTodo(itemId, { sort_order: newIdx }).catch(()=>{})
        } else {
          await updateCalendarTodo(itemId, { date: toDate, sort_order: newIdx }).catch(()=>{})
          emit('todo-changed')
        }
        loadTodos()
      },
      onAdd: async (evt) => {
        evt.item.remove()
        const p = window.__dragPayload
        if (!p || p.type !== 'todo') { window.__dragPayload = null; return }
        // TodoPanel 待办拖入日历：更新 date 字段即可
        const targetDate = evt.to.dataset.date
        const itemId = p.id
        try {
          const r = await updateTodo(itemId, { date: targetDate })
          Object.assign(p, r.data)
          // 该 todo 可能已在日历列表中（date=today 时两个面板都有），
          // 已存在则原地更新避免重复，不存在则新增
          const existing = todos.value.find(t => t.id === itemId)
          if (existing) {
            Object.assign(existing, r.data)
          } else {
            todos.value = [...todos.value, r.data]
          }
          emit('todo-changed')
        } catch {}
        window.__dragPayload = null
      },
    })
    sortableInstances.push(s)
  })
}

onMounted(()=>{loadTodos()
themeObserver=new MutationObserver(()=>{isDark.value=!document.documentElement.classList.contains('light-theme')})
themeObserver.observe(document.documentElement,{attributes:true,attributeFilter:['class']})})
watch([viewStart], ()=>{nextTick(()=>setTimeout(initSortable,100))})
onUnmounted(()=>{themeObserver?.disconnect();sortableInstances.forEach(s=>s.destroy())})

// ── 回到今日：快速回滚动画 ──
function scrollToToday() {
  const target = getMonday(new Date())
  const diffWeeks = Math.round((target - viewStart.value) / (7 * 24 * 60 * 60 * 1000))
  if (diffWeeks === 0) return
  const dir = diffWeeks > 0 ? 1 : -1
  const absWeeks = Math.abs(diffWeeks)
  const wrap = () => document.querySelector('.week-grid-wrap')

  const finalJump = () => {
    slideDir.value = dir > 0 ? 'slide-left' : 'slide-right'
    viewKey.value++
    viewStart.value = target
    wrap()?.classList.remove('fast-scroll')
    setTimeout(loadTodos, 350)
  }

  if (absWeeks <= 3) { finalJump(); return }

  // 多周回滚：先跳动靠近，再平滑过渡到目标
  wrap()?.classList.add('fast-scroll')
  const stepSize = Math.max(1, Math.floor((absWeeks - 3) / 6))
  let remaining = absWeeks - 3

  const tick = () => {
    const step = Math.min(remaining, stepSize)
    remaining -= step
    slideDir.value = dir > 0 ? 'slide-left' : 'slide-right'
    viewKey.value++
    viewStart.value.setDate(viewStart.value.getDate() + step * dir * 7)
    viewStart.value = new Date(viewStart.value)
    if (remaining <= 0) { setTimeout(finalJump, 80) }
    else { setTimeout(tick, 60) }
  }
  tick()
}
</script>

<style scoped>
/* ── ① 容器 — 卷轴书页质感 ── */
.calendar-view {
  flex:1; display:flex; flex-direction:column;
  background:var(--bg-card);
  border-radius:12px;
  overflow:hidden; min-height:0;
  position:relative;
  border:1px solid rgba(255,255,255,0.06);
  box-shadow:
    0 1px 0 rgba(255,255,255,0.03) inset,
    0 8px 40px rgba(0,0,0,0.5),
    0 2px 6px rgba(0,0,0,0.3);
}
.calendar-view::before {
  content:''; position:absolute; top:0; left:0; right:0;
  height:2px;
  background:linear-gradient(90deg,
    transparent 0%,
    rgba(124,106,240,0.3) 20%,
    rgba(124,106,240,0.5) 50%,
    rgba(124,106,240,0.3) 80%,
    transparent 100%
  );
}

/* ── ② 头部 ── */
.cal-header {
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 20px 14px;
  background:rgba(255,255,255,0.015);
  border-bottom:1px solid rgba(255,255,255,0.05);
  position:relative; z-index:2;
  flex-shrink:0;
  box-shadow:0 2px 6px rgba(0,0,0,0.15);
}
.cal-header::before {
  content:''; position:absolute; inset:0;
  pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Cfilter id='t'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.3 0.45' numOctaves='5' seed='31' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='300' height='100' filter='url(%23t)' opacity='1'/%3E%3C/svg%3E");
  background-repeat:repeat;
  mix-blend-mode:overlay;
  opacity:0.5;
}
.cal-title { display:flex; align-items:center; gap:10px; position:relative; z-index:1; }
.cal-title h2 {
  font-size:15px; font-weight:700; letter-spacing:0.5px;
  color:var(--text);
}
.year-tag {
  font-size:10px; font-weight:700; letter-spacing:1.5px;
  color:rgba(139,115,85,0.85);
  background:rgba(139,115,85,0.1);
  border:1px solid rgba(139,115,85,0.2);
  padding:2px 8px; border-radius:2px;
}
.cal-range {
  font-size:10px; font-weight:600; letter-spacing:0.5px;
  color:var(--text3);
  padding:2px 0; margin-left:2px;
}
.week-nav { display:flex; align-items:center; gap:6px; position:relative; z-index:1; }
.week-label { font-size:12px; font-weight:700; color:var(--text2); min-width:54px; text-align:center; letter-spacing:0.5px; }

/* ── ③ 导航按钮 — 复古铜色质感 ── */
.nav-btn {
  width:30px; height:30px;
  display:flex; align-items:center; justify-content:center;
  background:rgba(255,255,255,0.02);
  border:1px solid rgba(139,115,85,0.2);
  border-radius:3px;
  color:var(--text2); cursor:pointer;
  font-size:16px; font-weight:400;
  transition:all .15s; user-select:none;
}
.nav-btn:hover {
  background:rgba(139,115,85,0.1);
  border-color:rgba(139,115,85,0.4);
  color:rgba(139,115,85,0.9);
}
.nav-btn:active { transform:scale(0.93); }

/* ── ④ 滑动动画 ── */
.week-grid-wrap { position:relative; overflow:hidden; flex:1; min-height:0; display:flex; flex-direction:column; }
.slide-left-enter-active,.slide-left-leave-active,.slide-right-enter-active,.slide-right-leave-active { transition:transform .3s cubic-bezier(.25,.1,.25,1); position:absolute!important; top:0; left:0; right:0; }
.week-grid-wrap.fast-scroll .slide-left-enter-active,
.week-grid-wrap.fast-scroll .slide-left-leave-active,
.week-grid-wrap.fast-scroll .slide-right-enter-active,
.week-grid-wrap.fast-scroll .slide-right-leave-active,
.week-grid-wrap.fast-scroll .day-left-enter-active,
.week-grid-wrap.fast-scroll .day-left-leave-active,
.week-grid-wrap.fast-scroll .day-right-enter-active,
.week-grid-wrap.fast-scroll .day-right-leave-active {
  transition-duration:50ms !important;
}
.slide-left-enter-from { transform:translateX(100%); }
.slide-left-leave-to { transform:translateX(-100%); }
.slide-right-enter-from { transform:translateX(-100%); }
.slide-right-leave-to { transform:translateX(100%); }
.day-left-enter-active,.day-left-leave-active,
.day-right-enter-active,.day-right-leave-active {
  transition:transform .2s cubic-bezier(.25,.1,.25,1);
  position:absolute!important; top:0; left:0; right:0;
}
.day-left-enter-from { transform:translateX(14.28%); }
.day-left-leave-to { transform:translateX(-14.28%); }
.day-right-enter-from { transform:translateX(-14.28%); }
.day-right-leave-to { transform:translateX(14.28%); }

/* ── ⑤ 周网格 — 书页折痕感 ── */
.week-grid {
  display:grid; grid-template-columns:repeat(7,1fr);
  flex:1; min-height:0; height:100%;
  position:relative;
}
.week-grid::after {
  content:''; position:absolute; bottom:0; left:0; right:0;
  height:1px;
  background:linear-gradient(90deg,
    transparent 0%,
    rgba(0,0,0,0.3) 10%,
    rgba(0,0,0,0.3) 90%,
    transparent 100%
  );
}

/* ── ⑥ 日列 — 装订线缝线风格 ── */
.day-col {
  display:flex; flex-direction:column;
  background:var(--bg-card);
  min-height:0;
  position:relative;
  border-left:none;
  box-shadow:inset 0 1px 3px rgba(0,0,0,0.08), -1px 0 0 rgba(255,255,255,0.02) inset;
  transition:background .15s;
}
.day-col::before {
  content:''; position:absolute; left:0; top:2px; bottom:2px; width:2px;
  background:repeating-linear-gradient(to bottom,
    rgba(139,115,85,0.2) 0px,
    rgba(139,115,85,0.2) 3px,
    transparent 3px,
    transparent 5px
  );
  border-radius:1px; pointer-events:none; z-index:1;
}
.day-col::after {
  content:''; position:absolute; left:0; top:0; bottom:0; width:1px;
  background:rgba(0,0,0,0.03);
  pointer-events:none; z-index:0;
}
.day-col:first-child { border-left:none; box-shadow:none; }
.day-col:first-child::before { display:none; }
.day-col:first-child::after { display:none; }

/* ── ⑦ 今天列 — 顶部暖金宽条 ── */
.day-col.today {
  background:rgba(196,162,101,0.04);
  box-shadow:inset 0 8px 0 #b89450,
             0 -2px 6px rgba(184,148,80,0.12),
             inset 0 1px 3px rgba(0,0,0,0.08),
             -1px 0 0 rgba(255,255,255,0.02) inset;
}
/* 今天列不需要额外的 after 伪元素，使用 box-shadow 实现顶部条 */
.day-col.today::after {
  display:none;
}

/* ── ⑧ 周末列 ── */
.day-col.weekend:not(.today) {
  background:rgba(200,85,85,0.04);
}

/* ── ⑨ 日头部 — 质感页眉 ── */
.day-header {
  text-align:center; width:100%;
  padding:16px 6px 12px;
  position:relative;
  border-bottom:1px solid rgba(0,0,0,0.15);
  box-shadow:0 1px 0 rgba(255,255,255,0.02) inset, 0 -1px 0 rgba(255,255,255,0.02) inset;
  background:rgba(255,255,255,0.015);
  display:flex; flex-direction:column;
  align-items:center; gap:6px;
}
.day-header::after {
  content:'';
  position:absolute; bottom:0; left:15%; right:15%;
  height:1px;
  background:linear-gradient(90deg,
    transparent 0%,
    rgba(139,115,85,0.2) 30%,
    rgba(139,115,85,0.35) 50%,
    rgba(139,115,85,0.2) 70%,
    transparent 100%
  );
}

.day-name {
  font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase;
  color:var(--text3);
  padding:3px 8px;
  border:1px solid rgba(139,115,85,0.15);
  border-radius:2px;
  background:rgba(139,115,85,0.05);
}

.day-date {
  font-size:26px; font-weight:900; line-height:1;
  letter-spacing:-1px;
  color:var(--text2);
  text-shadow:0 1px 2px rgba(0,0,0,0.5);
}

.day-month {
  font-size:8px; font-weight:700; letter-spacing:2px; text-transform:uppercase;
  color:var(--text3);
  padding:2px 8px;
  border:1px solid rgba(139,115,85,0.12);
  border-radius:2px;
  background:rgba(139,115,85,0.04);
}

/* 今天：头部暖色调高亮 */
.day-col.today .day-header {
  background:rgba(196,162,101,0.08);
  border-bottom-color:rgba(196,162,101,0.2);
}
.day-col.today .day-header::after {
  background:linear-gradient(90deg,
    transparent 0%,
    rgba(196,162,101,0.25) 30%,
    rgba(196,162,101,0.4) 50%,
    rgba(196,162,101,0.25) 70%,
    transparent 100%
  );
}
.day-col.today .day-name {
  background:rgba(196,162,101,0.15);
  border-color:rgba(196,162,101,0.25);
  color:rgb(220,195,140);
}
.day-col.today .day-date {
  color:rgb(220,195,140);
  text-shadow:0 1px 3px rgba(0,0,0,0.4);
}
.day-col.today .day-month {
  background:rgba(196,162,101,0.1);
  border-color:rgba(124,106,240,0.2);
  color:rgba(170,160,255,0.6);
}

/* 周末：头部实体红调 */
.day-col.weekend:not(.today) .day-name {
  background:rgba(200,85,85,0.08);
  border-color:rgba(200,85,85,0.15);
  color:rgba(200,120,120,0.7);
}
.day-col.weekend:not(.today) .day-date {
  color:rgba(200,120,120,0.7);
}
.day-col.weekend:not(.today) .day-month {
  border-color:rgba(200,85,85,0.1);
  color:rgba(200,120,120,0.5);
}
.day-col.weekend:not(.today) .day-header {
  border-bottom-color:rgba(200,85,85,0.1);
}

/* ── ⑩ 便签容器 ── */
.day-notes { flex:1; width:100%; display:flex; flex-direction:column; gap:4px; padding:10px 6px 16px; overflow-y:auto; }
.day-notes::-webkit-scrollbar { width:3px; }
.day-notes::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:3px; }

/* ── ⑪ 便签样式（保持原设计） ── */
.cal-note { position:relative; display:flex; align-items:center; gap:10px; padding:8px 10px 6px 12px; border-radius:4px; font-size:12px; line-height:1.4; font-weight:500; cursor:grab; word-break:break-word; box-shadow:0 2px 4px rgba(0,0,0,0.2),0 1px 2px rgba(0,0,0,0.12),inset 0 1px 0 rgba(255,255,255,0.2),inset 0 -1px 0 rgba(0,0,0,0.08); flex-shrink:0; transition:box-shadow .25s cubic-bezier(.4,0,.2,1),opacity .25s ease; overflow:visible; user-select:none; }
.cal-note::before { content:''; position:absolute; inset:0; z-index:1; pointer-events:none; background:url('/images/textures/noisy.png') repeat; background-size:60% 60%; background-position:var(--bg-pos,0% 0%); mix-blend-mode:var(--tex-blend,multiply); opacity:var(--tex-opacity,0.5); border-radius:inherit; }
.cal-note::after { content:''; position:absolute; bottom:0; right:0; width:10px; height:10px; background:linear-gradient(135deg,transparent 50%,rgba(0,0,0,0.08) 50%); border-radius:0 0 4px 0; pointer-events:none; }
.cal-note:active { cursor:grabbing; }
.cal-note:hover { transform:translateY(-2px); box-shadow:0 4px 10px rgba(0,0,0,0.25),0 2px 4px rgba(0,0,0,0.15); }
.cal-note.done { opacity:0.4; }
.cal-note.editing { padding:7px 10px 5px 12px; }
.note-content { flex:1; min-width:0; position:relative; z-index:2; }
.cal-note.done .note-content { text-decoration:line-through; }
.note-checkbx { position:relative; width:13px; height:13px; flex-shrink:0; cursor:pointer; }
.note-checkbx input { position:absolute; opacity:0; }
.bx-icon { position:absolute; inset:0; border:1.5px solid rgba(0,0,0,0.3); border-radius:3px; transition:all .12s; }
.note-checkbx input:checked~.bx-icon { background:rgba(0,0,0,0.2); border-color:rgba(0,0,0,0.15); }
.note-checkbx input:checked~.bx-icon::after { content:''; position:absolute; left:3px; top:0px; width:4px; height:7px; border:solid #fff; border-width:0 2px 2px 0; transform:rotate(45deg); }
.note-editing { outline:1px dashed rgba(0,0,0,0.25); outline-offset:1px; cursor:text; min-height:1.2em; }
.note-bell { font-size:10px; margin-left:2px; }

/* ── ⑫ 空状态 — 奉旨摸鱼 ── */
.empty-hint {
  font-size:11px; text-align:center; padding:20px 8px; margin:4px 3px;
  color:var(--text3); letter-spacing:2px;
  border:1px dashed rgba(139,115,85,0.1);
  border-radius:3px;
  transition:all .2s;
  flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px;
}
.empty-hint .empty-icon { font-size:24px; }
.empty-hint .empty-text {
  font-size:12px; font-weight:700;
  color:var(--text3);
  letter-spacing:4px;
  padding:5px 18px;
  border-top:1.5px solid rgba(139,115,85,0.2);
  border-bottom:1.5px solid rgba(139,115,85,0.2);
  background:rgba(139,115,85,0.03);
  line-height:1.4;
}
.empty-hint .empty-seal {
  font-size:9px; font-weight:700;
  color:rgba(200,80,80,0.5);
  border:1.5px solid rgba(200,80,80,0.12);
  padding:1px 6px; border-radius:2px;
  letter-spacing:2px;
  transform:rotate(-4deg);
  margin-top:2px;
}
.empty-hint:hover { border-color:rgba(139,115,85,0.2); }
.empty-hint:hover .empty-text { color:rgba(180,160,120,0.9); }
.empty-hint:hover .empty-seal { color:rgba(200,80,80,0.7); border-color:rgba(200,80,80,0.2); }

/* ── ⑬ SortableJS 拖拽样式 ── */
.cal-note-ghost { opacity:0.3; background:rgba(255,255,255,0.04)!important; border:2px dashed var(--primary)!important; border-radius:4px!important; box-shadow:none!important; }
.cal-note-ghost::before,.cal-note-ghost::after { display:none!important; }

/* ── ⑭ 底部导航 ── */
.day-nav {
  display:flex; align-items:center; justify-content:space-between;
  padding:12px 20px 14px;
  border-top:1px solid rgba(255,255,255,0.05);
  flex-shrink:0;
  background:rgba(255,255,255,0.015);
  position:relative;
  box-shadow:0 -2px 6px rgba(0,0,0,0.12);
}
.day-nav>* { position:relative; z-index:1; }
.day-nav::after {
  content:''; position:absolute; inset:0;
  pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='100'%3E%3Cfilter id='t'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.3 0.45' numOctaves='5' seed='31' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='300' height='100' filter='url(%23t)' opacity='1'/%3E%3C/svg%3E");
  background-repeat:repeat;
  mix-blend-mode:overlay;
  opacity:0.5;
}
.day-nav .nav-btn {
  width:auto; height:34px; padding:0 18px;
  border-radius:3px;
  background:rgba(139,115,85,0.08);
  border:1px solid rgba(139,115,85,0.2);
  color:rgba(139,115,85,0.9); font-size:12px; font-weight:600;
  box-shadow:0 2px 8px rgba(0,0,0,0.2);
  letter-spacing:0.5px;
}
.day-nav .nav-btn:hover { background:rgba(139,115,85,0.15); border-color:rgba(139,115,85,0.35); }
.day-nav .nav-btn:active { transform:scale(0.96); }
.today-btn {
  height:34px; padding:0 16px;
  border-radius:6px;
  background:rgba(124,106,240,0.12);
  border:1.5px solid rgba(124,106,240,0.25);
  color:var(--primary); font-size:12px; font-weight:600;
  cursor:pointer; letter-spacing:0.5px;
  transition:all .15s;
  box-shadow:0 2px 8px rgba(0,0,0,0.2);
}
.today-btn:hover { background:rgba(124,106,240,0.22); border-color:var(--primary); }
.today-btn:active { transform:scale(0.96); }
.range-label { font-size:11px; font-weight:600; letter-spacing:0.5px; color:var(--text3); }

/* ── ⑮ 覆盖层/模态框 ── */
.input-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:99999; display:flex; align-items:center; justify-content:center; }
.input-card { width:320px; background:var(--bg-modal); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:20px; box-shadow:0 12px 40px rgba(0,0,0,0.5); }
.input-title { font-size:14px; font-weight:600; color:var(--text); margin-bottom:12px; }
.reminder-target { font-size:13px; color:var(--text2); margin-bottom:10px; padding:6px 10px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06); border-radius:6px; }
.input-field { width:100%; padding:10px 14px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:8px; color:var(--text); font-size:13px; outline:none; }
.input-field:focus { border-color:var(--primary); }
.input-actions { display:flex; gap:8px; margin-top:12px; justify-content:flex-end; }
.input-actions button { padding:8px 20px; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer; border:none; }
.btn-cancel { background:rgba(255,255,255,0.06); color:var(--text2); border:1px solid rgba(255,255,255,0.1); }
.btn-confirm { background:var(--primary); color:#fff; }

/* ── ⑯ 右键菜单 ── */
.ctx-menu { position:fixed; z-index:999; min-width:110px; background:var(--bg-menu); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:4px; box-shadow:0 4px 20px rgba(0,0,0,0.4); }
.ctx-item { display:flex; align-items:center; gap:6px; width:100%; padding:8px 12px; background:none; border:none; border-radius:5px; color:var(--text2); font-size:12px; text-align:left; cursor:pointer; white-space:nowrap; }
.ctx-item:hover { background:rgba(255,255,255,0.05); color:var(--text); }

/* ── ⑰ 添加待办弹窗 ── */
.edit-overlay { position:fixed; inset:0; z-index:99999; }
.edit-sticky {
  width:320px; max-width:85vw;
  border-radius:12px; padding:20px 20px 16px;
  box-shadow:0 8px 32px rgba(0,0,0,0.5),0 2px 0 0 rgba(0,0,0,0.1) inset;
  position:fixed; z-index:99999;
  display:flex; flex-direction:column; gap:12px;
  border:1px solid rgba(0,0,0,0.2);
}
.edit-sticky::before {
  content:''; position:absolute; top:0; left:50%; transform:translateX(-50%);
  width:70%; height:14px;
  background:rgba(255,255,255,0.4);
  border-radius:0 0 4px 4px;
}
.edit-sticky-header { font-size:15px; font-weight:700; color:#2d3436; margin-top:4px; }
.edit-sticky-text {
  width:100%; min-height:80px; padding:10px 12px;
  font-size:14px; line-height:1.5;
  border:none; border-radius:8px;
  background:rgba(255,255,255,0.65);
  color:#2d3436; outline:none; resize:vertical;
  font-family:inherit; box-sizing:border-box;
}
.edit-sticky-text:focus { background:rgba(255,255,255,0.8); box-shadow:0 0 0 2px rgba(255,183,77,0.5); }
.edit-sticky-actions { display:flex; justify-content:flex-end; gap:8px; }
.edit-sticky-btn { padding:7px 18px; font-size:13px; font-weight:600; border:none; border-radius:8px; cursor:pointer; transition:all .12s; }
.edit-sticky-cancel { background:rgba(0,0,0,0.08); color:#2d3436; border:1px solid rgba(0,0,0,0.1); }
.edit-sticky-cancel:hover { background:rgba(0,0,0,0.14); }
.edit-sticky-confirm { background:#6C5CE7; color:#fff; }
.edit-sticky-confirm:hover { filter:brightness(1.15); }

</style>

<style>
/* ════════════════════════════════════════
   白天模式 — 暖色纸张质感（和预览一致）
   ════════════════════════════════════════ */
.light-theme .calendar-view {
  background: #f5f1e8;
  border-radius:12px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 1px 0 rgba(255,255,255,0.5) inset, 0 8px 40px rgba(0,0,0,0.1), 0 2px 6px rgba(0,0,0,0.05);
}
.light-theme .calendar-view::before {
  background: linear-gradient(90deg, transparent 0%, rgba(123,107,199,0.25) 20%, rgba(123,107,199,0.4) 50%, rgba(123,107,199,0.25) 80%, transparent 100%);
}
.light-theme .cal-header {
  background: #ebe6dd;
  border-bottom-color: rgba(0,0,0,0.04);
  box-shadow:0 2px 6px rgba(0,0,0,0.08);
}
.light-theme .cal-header::before {
  mix-blend-mode:multiply;
  opacity:0.12;
}
.light-theme .year-tag {
  color: rgba(154,130,96,0.85);
  background: rgba(154,130,96,0.08);
  border-color: rgba(154,130,96,0.15);
}
.light-theme .cal-range { color: var(--text3); }
.light-theme .nav-btn {
  background: rgba(0,0,0,0.01);
  border-color: rgba(154,130,96,0.15);
  color: var(--text2);
}
.light-theme .nav-btn:hover {
  background: rgba(154,130,96,0.06);
  border-color: rgba(154,130,96,0.25);
  color: rgba(154,130,96,0.85);
}
.light-theme .week-grid::after {
  background: linear-gradient(90deg, transparent 0%, rgba(0,0,0,0.08) 10%, rgba(0,0,0,0.08) 90%, transparent 100%);
}
.light-theme .day-col {
  background: #f5f1e8;
  border-left:none;
  box-shadow:inset 0 1px 2px rgba(0,0,0,0.03), -1px 0 0 rgba(255,255,255,0.3) inset;
}
.light-theme .day-col:first-child { border-left: none; box-shadow: none; }
.light-theme .day-col:first-child::before { display:none; }
.light-theme .day-col:first-child::after { display:none; }
.light-theme .day-header {
  border-bottom-color: rgba(0,0,0,0.06);
  background: rgba(0,0,0,0.01);
  box-shadow: 0 1px 0 rgba(255,255,255,0.3) inset, 0 -1px 0 rgba(255,255,255,0.3) inset;
}
.light-theme .day-header::after {
  background: linear-gradient(90deg, transparent 0%, rgba(154,130,96,0.15) 30%, rgba(154,130,96,0.3) 50%, rgba(154,130,96,0.15) 70%, transparent 100%);
}
.light-theme .day-name {
  border-color: rgba(154,130,96,0.12);
  background: rgba(154,130,96,0.04);
}
.light-theme .day-month {
  border-color: rgba(154,130,96,0.1);
  background: rgba(154,130,96,0.03);
}
.light-theme .day-date {
  color: var(--text2);
  text-shadow: 0 1px 1px rgba(255,255,255,0.5);
}
.light-theme .day-col.today {
  background: rgba(196,162,101,0.04);
}
.light-theme .day-col.weekend:not(.today) {
  background: rgba(196,112,112,0.03);
}
.light-theme .day-col.today .day-header {
  background: rgba(196,162,101,0.06);
  border-bottom-color: rgba(196,162,101,0.2);
}
.light-theme .day-col.today .day-header::after {
  background: linear-gradient(90deg, transparent 0%, rgba(196,162,101,0.25) 30%, rgba(196,162,101,0.4) 50%, rgba(196,162,101,0.25) 70%, transparent 100%);
}
.light-theme .day-col.today .day-name {
  background: rgba(196,162,101,0.12);
  border-color: rgba(196,162,101,0.2);
  color: rgba(139,115,85,0.85);
}
.light-theme .day-col.today .day-date {
  color: rgba(139,115,85,0.9);
  text-shadow: 0 1px 2px rgba(255,255,255,0.5);
}
.light-theme .day-col.today .day-month {
  background: rgba(196,162,101,0.08);
  border-color: rgba(196,162,101,0.15);
  color: rgba(139,115,85,0.6);
}
.light-theme .day-col.weekend:not(.today) .day-name {
  background: rgba(196,112,112,0.06);
  border-color: rgba(196,112,112,0.12);
  color: rgba(180,90,90,0.7);
}
.light-theme .day-col.weekend:not(.today) .day-date {
  color: rgba(180,90,90,0.7);
}
.light-theme .day-col.weekend:not(.today) .day-month {
  border-color: rgba(196,112,112,0.1);
  color: rgba(180,90,90,0.5);
}
.light-theme .day-col.weekend:not(.today) .day-header {
  border-bottom-color: rgba(196,112,112,0.1);
}
.light-theme .empty-hint {
  border-color: rgba(154,130,96,0.1);
}
.light-theme .empty-hint .empty-text {
  border-color: rgba(154,130,96,0.2);
  background: rgba(154,130,96,0.03);
}
.light-theme .empty-hint .empty-seal {
  color: rgba(200,80,80,0.45);
  border-color: rgba(200,80,80,0.1);
}
.light-theme .empty-hint:hover {
  border-color: rgba(154,130,96,0.2);
}
.light-theme .empty-hint:hover .empty-text {
  color: rgba(154,130,96,0.85);
}
.light-theme .day-nav {
  background: #ebe6dd;
  border-top-color: rgba(0,0,0,0.04);
  box-shadow:0 -2px 6px rgba(0,0,0,0.08);
}
.light-theme .day-nav::after {
  mix-blend-mode:multiply;
  opacity:0.12;
}
.light-theme .day-nav .nav-btn {
  background: rgba(154,130,96,0.06);
  border-color: rgba(154,130,96,0.15);
  color: rgba(154,130,96,0.8);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.light-theme .day-nav .nav-btn:hover {
  background: rgba(154,130,96,0.12);
  border-color: rgba(154,130,96,0.25);
}
.light-theme .today-btn {
  background: rgba(108,92,231,0.1);
  border-color: rgba(108,92,231,0.2);
  color: var(--primary);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.light-theme .today-btn:hover {
  background: rgba(108,92,231,0.16);
  border-color: rgba(108,92,231,0.35);
}
.light-theme .day-notes::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.1);
}
.light-theme .bx-icon {
  border-color: rgba(0,0,0,0.2);
}
.light-theme .cal-note-ghost {
  background: rgba(0,0,0,0.04)!important;
}

@media (max-width: 768px) {
  .cal-header { padding:10px 12px 10px; }
  .cal-title h2 { font-size:13px; }
  .cal-range { font-size:9px; }
  .year-tag { font-size:8px; padding:1px 5px; }
  .week-nav { gap:4px; }
  .week-label { font-size:11px; }
  .day-header { padding:10px 3px 8px; }
  .day-name { font-size:9px; padding:1px 4px; }
  .day-date { font-size:20px; }
  .day-month { font-size:7px; padding:1px 5px; }
  .day-nav { padding:8px 12px 10px; }
  .day-nav .nav-btn { height:30px; padding:0 12px; font-size:11px; }
  .today-btn { height:30px; padding:0 12px; font-size:11px; }
  .empty-hint { padding:12px 4px; }
  .empty-hint .empty-icon { font-size:20px; }
  .empty-hint .empty-text { font-size:11px; padding:4px 12px; letter-spacing:2px; }
  .cal-note { padding:6px 8px; font-size:11px; }
  .note-text { font-size:11px; }
  .empty-hint:hover .empty-text { color:rgba(180,160,120,0.9); }
}
</style>
