<template>
  <div class="m-cal">
    <div class="mc-header">
      <span class="mc-title">🐟 摸鱼日历</span>
      <span class="mc-date">{{ viewDateStr }}</span>
    </div>

    <div class="mc-nav">
      <button class="mc-btn" @click="dayOffset(-1)">‹</button>
      <button class="mc-btn today" @click="scrollToToday">📅 今日</button>
      <button class="mc-btn" @click="dayOffset(1)">›</button>
    </div>

    <div class="mc-notes">
      <div v-for="note in todayNotes" :key="note.id" class="mc-note"
        :style="{ background: note.color || '#FFEAA7' }">
        <label class="mc-check" @click="toggleDone(note)">
          <input type="checkbox" :checked="note.done" />
          <span class="mc-checkmark"></span>
        </label>
        <span class="mc-text" :class="{done:note.done}">{{ note.title }}</span>
        <button class="mc-del" @click="deleteTodo(note.id)">×</button>
      </div>

      <div v-if="todayNotes.length === 0" class="mc-empty">
        <div class="mc-empty-icon">🐟</div>
        <div class="mc-empty-text">奉旨摸鱼</div>
        <div class="mc-empty-seal">钦 此</div>
      </div>
    </div>

    <button class="mc-add" @click="startAdd">+</button>

    <!-- 添加弹窗 -->
    <Teleport to="body">
      <div v-if="showAdd" class="mc-overlay" @click.self="showAdd=false">
        <div class="mc-dialog">
          <input v-model="newText" class="mc-input" placeholder="写一条待办..." maxlength="200"
            @keyup.enter="doAdd" autofocus />
          <div class="mc-dlg-actions">
            <button class="mc-dlg-btn cancel" @click="showAdd=false">取消</button>
            <button class="mc-dlg-btn ok" @click="doAdd">确定</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCalendarTodos, createCalendarTodo, updateCalendarTodo, deleteCalendarTodo } from '@/api/calendar'

const viewDate = ref(new Date())
const todos = ref([])
const showAdd = ref(false)
const newText = ref('')

const todayKey = computed(() => {
  const d = viewDate.value
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
})

const todayNotes = computed(() => todos.value.filter(t => t.date === todayKey.value))

const viewDateStr = computed(() => {
  const d = viewDate.value
  const weekdays = ['周日','周一','周二','周三','周四','周五','周六']
  return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 ${weekdays[d.getDay()]}`
})

function dayOffset(n) {
  viewDate.value = new Date(viewDate.value.getTime() + n * 86400000)
  loadTodos()
}

function scrollToToday() {
  viewDate.value = new Date()
  loadTodos()
}

async function loadTodos() {
  const key = todayKey.value
  try {
    const res = await getCalendarTodos(key, key)
    todos.value = res.data || []
  } catch(e) { todos.value = [] }
}

async function toggleDone(note) {
  await updateCalendarTodo(note.id, { done: !note.done })
  await loadTodos()
}

async function deleteTodo(id) {
  await deleteCalendarTodo(id)
  await loadTodos()
}

function startAdd() { showAdd.value = true; newText.value = '' }

async function doAdd() {
  if (!newText.value.trim()) return
  await createCalendarTodo({ title: newText.value.trim(), date: todayKey.value })
  showAdd.value = false
  await loadTodos()
}

onMounted(() => { loadTodos() })
</script>

<style scoped>
.m-cal {
  display:flex; flex-direction:column; height:100%;
  padding:12px; box-sizing:border-box;
  background:var(--bg-card);
  border-radius:12px;
  border:1px solid rgba(255,255,255,0.06);
  box-shadow:0 1px 0 rgba(255,255,255,0.03) inset,
             0 8px 40px rgba(0,0,0,0.5),
             0 2px 6px rgba(0,0,0,0.3);
}
.mc-header {
  display:flex; flex-direction:column; align-items:center; gap:4px;
  padding:8px 0 12px; text-align:center;
}
.mc-title { font-size:15px; font-weight:700; color:var(--text); }
.mc-date { font-size:12px; font-weight:600; color:var(--text3); }

.mc-nav {
  display:flex; align-items:center; justify-content:center; gap:12px;
  padding:8px 0 12px;
}
.mc-btn {
  height:36px; padding:0 16px; border-radius:6px;
  background:rgba(139,115,85,0.08);
  border:1px solid rgba(139,115,85,0.2);
  color:rgba(139,115,85,0.9); font-size:14px; font-weight:600;
  cursor:pointer; transition:all .12s;
}
.mc-btn.today { background:rgba(124,106,240,0.12); border-color:rgba(124,106,240,0.25); color:var(--primary); }
.mc-btn:active { transform:scale(0.95); }

.mc-notes { flex:1; display:flex; flex-direction:column; gap:6px; overflow-y:auto; padding-bottom:60px; }

.mc-note {
  display:flex; align-items:center; gap:8px;
  padding:10px 12px; border-radius:8px;
  font-size:13px; position:relative;
  border:1px solid rgba(0,0,0,0.04);
  box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.mc-text { flex:1; color:#2d3436; }
.mc-text.done { text-decoration:line-through; opacity:0.5; }
.mc-del {
  width:20px; height:20px; border:none; background:rgba(0,0,0,0.06);
  border-radius:50%; cursor:pointer; font-size:14px; line-height:1;
  color:rgba(0,0,0,0.3); flex-shrink:0;
}
.mc-check { position:relative; width:18px; height:18px; cursor:pointer; flex-shrink:0; }
.mc-check input { position:absolute; opacity:0; }
.mc-checkmark { position:absolute; inset:0; border:2px solid rgba(0,0,0,0.2); border-radius:4px; }
.mc-check input:checked + .mc-checkmark { background:#6C5CE7; border-color:#6C5CE7; }
.mc-check input:checked + .mc-checkmark::after {
  content:''; position:absolute; left:4px; top:1px;
  width:5px; height:8px; border:solid #fff;
  border-width:0 2px 2px 0; transform:rotate(45deg);
}

.mc-empty {
  flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px;
  border:1px dashed rgba(139,115,85,0.1); border-radius:8px;
  padding:24px;
}
.mc-empty-icon { font-size:28px; }
.mc-empty-text {
  font-size:13px; font-weight:700; color:var(--text3); letter-spacing:4px;
  padding:5px 18px; border-top:1.5px solid rgba(139,115,85,0.2);
  border-bottom:1.5px solid rgba(139,115,85,0.2);
  background:rgba(139,115,85,0.03); line-height:1.4;
}
.mc-empty-seal {
  font-size:9px; font-weight:700; color:rgba(200,80,80,0.5);
  border:1.5px solid rgba(200,80,80,0.12);
  padding:1px 6px; border-radius:2px; letter-spacing:2px;
  transform:rotate(-4deg);
}

.mc-add {
  position:fixed; bottom:72px; right:16px; z-index:999;
  width:48px; height:48px; border-radius:50%;
  background:linear-gradient(135deg,#6C5CE7,#00CEC9);
  border:none; color:#fff; font-size:24px; font-weight:300;
  box-shadow:0 4px 12px rgba(108,92,231,0.4);
  cursor:pointer;
}
.mc-add:active { transform:scale(0.92); }

.mc-overlay { position:fixed; inset:0; z-index:99999; background:rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:center; }
.mc-dialog { width:85vw; max-width:340px; background:var(--bg-card); border-radius:12px; padding:20px; }
.mc-input { width:100%; padding:10px 12px; font-size:14px; border:1px solid var(--border); border-radius:8px; background:var(--bg); color:var(--text); outline:none; box-sizing:border-box; }
.mc-dlg-actions { display:flex; justify-content:flex-end; gap:8px; margin-top:12px; }
.mc-dlg-btn { padding:8px 18px; border-radius:8px; font-size:13px; font-weight:600; border:none; cursor:pointer; }
.mc-dlg-btn.cancel { background:rgba(0,0,0,0.06); color:var(--text2); }
.mc-dlg-btn.ok { background:#6C5CE7; color:#fff; }
</style>
