<template>
  <div class="todo-panel">
    <div class="todo-header">
      <div class="todo-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span>不想干的待办</span>
      </div>
      <button class="close-btn" @click="$emit('close')" title="收起">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
    </div>
    <div class="progress-text">
      <span>已完成 {{ doneCount }} 项</span>
      <span>{{ progressPct }}%</span>
    </div>

    <!-- 输入框 -->
    <div class="todo-input-line">
      <input
        v-model="newTodo"
        type="text"
        placeholder="添加待办..."
        @keydown.enter="addTodo"
      />
      <button class="add-btn" @click="addTodo">+</button>
    </div>

    <!-- 便签列表 -->
    <div class="sticky-notes">
      <div class="sticky-notes-scroll">
      <TransitionGroup name="note-list">
        <div
          v-for="(todo, idx) in todos"
          :key="todo.id"
          class="sticky-note"
          :class="{ 
            'is-done': todo.done, 
            'is-calendar': todo.date !== null,
            'is-note': todo.note_id != null || todo.notebook_id != null
          }"
          :style="getNoteStyle(todo, idx)"
          :data-id="todo.id"
          @contextmenu="handleCtx($event, todo)"
          @click="onNoteClick(todo)"
        >
          <!-- 上端胶条 -->
          <div class="note-tape"></div>

          <label class="note-check" @click.stop>
            <input
              type="checkbox"
              :checked="todo.done"
              @change="toggleTodo(todo)"
            />
            <span class="check-icon"></span>
          </label>

          <span class="note-text">{{ todo.title }}
            <span v-if="todo.date !== null" class="note-pin" title="来自摸鱼日历">📌</span>
            <!-- 关联标识：三种图标 -->
            <span v-if="todo.note_id && todo.selected_text" class="note-from" title="来自笔记词条">📝</span>
            <span v-else-if="todo.note_id" class="note-from" title="来自笔记条目">📄</span>
            <span v-else-if="todo.notebook_id" class="note-from" title="来自笔记本">📓</span>
          </span>
          <!-- 关联跳转 -->
          <div v-if="todo.note_id || todo.notebook_id" class="note-attach">
            <button v-if="todo.note_id" class="note-jump-btn" @click.stop="jumpToNote(todo)" title="跳转到笔记">🔗</button>
            <button v-else-if="todo.notebook_id" class="note-jump-btn" @click.stop="jumpToNotebook(todo)" title="跳转到笔记本目录">📂</button>
          </div>

          <!-- 打标：只有长期待办显示 -->
          <div v-if="todo.label && !todo.note_id && !todo.notebook_id" class="note-label-tape">
            <span>{{ todo.label }}</span>
          </div>
        </div>

        <div v-if="todos.length === 0" key="empty" class="empty-todo">
          暂无待办，输入内容添加
        </div>
      </TransitionGroup>
      </div>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="ctxVisible"
        class="ctx-menu"
        :style="{ left: ctxX + 'px', top: ctxY + 'px' }"
      >
        <button v-if="!ctxTodo?.date" class="ctx-item" @click.stop="openEdit">✏️ 修改</button>
        <button class="ctx-item" @click.stop="doDeleteCtx">🗑 删除</button>
        <button v-if="!ctxTodo?.note_id && !ctxTodo?.notebook_id && !ctxTodo?.date" class="ctx-item" @click.stop="doToggleLabel">
          {{ ctxTodo?.label ? '✅' : '🏷' }} 打标
        </button>
      </div>

      <!-- 修改弹窗 -->
      <div v-if="editVisible" class="edit-overlay-noblur" @click.self="closeEdit">
        <div class="edit-sticky" :style="editStickyStyle">
          <div class="edit-sticky-header">📝 修改待办</div>
          <textarea ref="editInputRef" class="edit-sticky-text" v-model="editText" maxlength="200" @keydown.esc="closeEdit" placeholder="输入待办内容..."></textarea>
          <div class="edit-sticky-actions">
            <button class="edit-sticky-btn edit-sticky-cancel" @click="closeEdit">取消</button>
            <button class="edit-sticky-btn edit-sticky-confirm" @click="confirmEdit">✓ 确定</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { getTodos, createTodo, updateTodo, deleteTodo, reorderTodos } from '@/api/todo'
import { NOTE_STYLES, NOTE_STYLES_DARK, LIGHT_TO_DARK, randomColor } from '@/constants/colors'

const emit = defineEmits(['close', 'todo-changed', 'jump-to-note'])

const props = defineProps({
  refreshKey: { type: Number, default: 0 },
})

// 监听外部刷新信号
watch(() => props.refreshKey, () => { loadTodos() })

const todos = ref([])
const newTodo = ref('')
// 标记：用户是否曾拥有过真实待办（防止拖拽删除后 reload 时回退到虚拟便签）
let hasEverHadTodo = false

// ── 响应式主题检测（使 getNoteStyle 成为响应式依赖） ──
const isDark = ref(!document.documentElement.classList.contains('light-theme'))
let themeObserver = null

// ── 虚拟示例待办 ──
const VIRTUAL_TODOS = [
  { id: 'v1', title: '用便签写下一天的待办计划', done: false },
  { id: 'v2', title: '去超市买牛奶和面包', done: true },
  { id: 'v3', title: '完成项目的UI重构', done: false },
  { id: 'v4', title: '晚上8点有线上会议', done: false },
  { id: 'v5', title: '整理周报发给领导', done: false },
]

// ── 颜色工具 ──
function getNoteStyle(todo, idx) {
  const lightBg = todo.color || NOTE_STYLES[Math.abs(todo.id) % NOTE_STYLES.length].bg
  // 随机纹理偏移，每张便签不同
  const posX = Math.round((todo.id * 37 + idx * 73) % 71)
  const posY = Math.round((todo.id * 53 + idx * 97) % 71)
  const bgPos = `${posX}% ${posY}%`
  // 纹理参数：浅色模式用 multiply 更明显，深色模式用 overlay 保留纹理
  const texBlend = isDark.value ? 'overlay' : 'multiply'
  const texOpacity = isDark.value ? '0.3' : '0.15'
  if (!isDark.value) {
    // 浅色模式：直接用存储的颜色值
    const match = NOTE_STYLES.find(s => s.bg === lightBg)
    return { backgroundColor: lightBg, color: match ? match.text : '#fff', '--bg-pos': bgPos, '--tex-blend': texBlend, '--tex-opacity': texOpacity }
  }
  // 深色模式：用 Map 直接查表 O(1)
  const dark = LIGHT_TO_DARK.get(lightBg)
  if (dark) {
    return { backgroundColor: dark.bg, color: dark.text, '--bg-pos': bgPos, '--tex-blend': texBlend, '--tex-opacity': texOpacity }
  }
  return { backgroundColor: lightBg, color: '#fff', '--bg-pos': bgPos, '--tex-blend': texBlend, '--tex-opacity': texOpacity }
}

function isVirtual(todo) {
  return String(todo.id).startsWith('v')
}

// ── 已完成统计 ──
const doneCount = computed(() => todos.value.filter(t => t.done).length)
const progressPct = computed(() => {
  const total = todos.value.length
  if (total === 0) return 0
  return Math.round(doneCount.value / total * 100)
})

// ── 排序 ──
function sortTodos(list) {
  return [...list].sort((a, b) => {
    if (a.done === b.done) return 0
    return a.done ? 1 : -1
  })
}

// ── 加载 ──
async function loadTodos() {
  try {
    const res = await getTodos()
    const real = (res.data || []).map(t => ({
      ...t,
      // 旧数据如果没有存储颜色，分配一个随机色
      color: t.color || NOTE_STYLES[Math.abs(t.id) % NOTE_STYLES.length].bg,
    }))
    if (real.length > 0) {
      hasEverHadTodo = true
      todos.value = real.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    } else if (!hasEverHadTodo) {
      todos.value = VIRTUAL_TODOS.map(t => ({ ...t }))
    } else {
      todos.value = []
    }
  } catch {
    if (!hasEverHadTodo) {
      todos.value = VIRTUAL_TODOS.map(t => ({ ...t }))
    } else {
      todos.value = []
    }
  }
}

// ── 新增 ──
async function addTodo() {
  const title = newTodo.value.trim()
  if (!title) return
  const color = randomColor()
  try {
    const res = await createTodo(title, 0, color)
    hasEverHadTodo = true
    // 清除虚拟项
    todos.value = [
      { ...res.data, color },
      ...todos.value.filter(t => !isVirtual(t)),
    ]
    newTodo.value = ''
    emit('todo-changed')
  } catch (e) {
    console.error(e)
  }
}

// ── 排序持久化 ──
function saveOrder() {
  const real = todos.value.filter(t => !isVirtual(t))
  if (real.length === 0) return
  const orderData = real.map((t, i) => ({ id: t.id, sort_order: i }))
  reorderTodos(orderData).catch(() => {})
}

// ── 勾选 ──
async function toggleTodo(todo) {
  if (isVirtual(todo)) {
    const newDone = !todo.done
    try {
      const color = randomColor()
      const res = await createTodo(todo.title, 0, color)
      if (newDone) {
        const updated = await updateTodo(res.data.id, { done: true })
        Object.assign(res.data, updated.data)
      }
      Object.assign(res.data, { color })
      todos.value = todos.value.map(t =>
        t.id === todo.id ? res.data : t
      )
      todos.value = sortTodos(todos.value)
    } catch (e) { console.error(e) }
    return
  }
  try {
    const newDone = !todo.done
    await updateTodo(todo.id, { done: newDone })
    todo.done = newDone
    todos.value = sortTodos(todos.value)
    emit('todo-changed')
  } catch (e) {
    console.error(e)
  }
}

// ── 删除 ──
async function removeTodo(id) {
  closeCtx()
  if (String(id).startsWith('v')) {
    todos.value = todos.value.filter(t => t.id !== id)
    return
  }
  try {
    await deleteTodo(id)
    todos.value = todos.value.filter(t => t.id !== id)
    emit('todo-changed')
  } catch (e) {
    console.error(e)
  }
}

// ── SortableJS 拖拽排序（含与日历跨组件拖拽） ──
import Sortable from 'sortablejs'
let todoSortable = null

function initTodoSortable() {
  if (todoSortable) todoSortable.destroy()
  const el = document.querySelector('.sticky-notes-scroll')
  if (!el) return
  todoSortable = new Sortable(el, {
    group: 'shared-todos',
    animation: 250,
    easing: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
    ghostClass: 'todo-ghost',
    onStart: (evt) => {
      const id = parseInt(evt.item.dataset.id)
      const todo = todos.value.find(t => t.id === id)
      if (todo) window.__dragPayload = { type:'todo', id:todo.id, title:todo.title, color:todo.color }
    },
    onEnd: async (evt) => {
      // 跨组件拖拽（拖到日历）：立即从本地数据移除避免视觉闪烁
      if (evt.from === evt.to) {
        const order = [...evt.from.querySelectorAll('.sticky-note')].map(el => parseInt(el.dataset.id))
        todos.value = order.map(id => todos.value.find(t => t.id === id)).filter(Boolean)
        saveOrder()
        window.__dragPayload = null
      } else {
        // 跨组件拖拽到日历：从右侧面板移除
        const itemId = parseInt(evt.item.dataset.id)
        todos.value = todos.value.filter(t => t.id !== itemId)
        // 不清理 payload，让目标 onAdd 处理
      }
    },
    onAdd: async (evt) => {
      const p = window.__dragPayload
      evt.item.remove()
      if (!p || p.type !== 'calendar') { window.__dragPayload = null; return }
      // 日历 → 右侧：将 date 置为 null
      try {
        const res = await updateTodo(p.id, { date: null })
        // 该 todo 可能已在列表中（date=today 时两个面板都有），
        // 已存在则原地更新避免重复，不存在则新增
        const existing = todos.value.find(t => t.id === p.id)
        if (existing) {
          Object.assign(existing, res.data)
        } else {
          todos.value.unshift(res.data)
        }
        todos.value = sortTodos(todos.value)
        emit('todo-changed')
      } catch {}
      window.__dragPayload = null
    },
  })
}

// ── 右键菜单 ──
const ctxVisible = ref(false)
const ctxX = ref(0)
const ctxY = ref(0)
const ctxTodo = ref(null)

function handleCtx(e, todo) {
  e.preventDefault()
  openCtx(e, todo)
}

function openCtx(e, todo) {
  ctxVisible.value = true
  ctxX.value = Math.min(e.clientX, window.innerWidth - 120)
  ctxY.value = Math.min(e.clientY, window.innerHeight - 80)
  ctxTodo.value = todo
}

function closeCtx() {
  ctxVisible.value = false
}

// ── 修改弹窗 ──
const editVisible = ref(false)
const editText = ref('')
const editInputRef = ref(null)
const editStickyColor = ref({ bg: '#FFEAA7', text: '#2d3436' })
const editStickyStyle = computed(() => ({
  left: Math.min(ctxX.value, window.innerWidth - 340) + 'px',
  top: Math.min(ctxY.value, window.innerHeight - 200) + 'px',
  backgroundColor: editStickyColor.value.bg,
  color: editStickyColor.value.text,
}))

function openEdit() {
  const todo = ctxTodo.value
  if (!todo) return
  editText.value = todo.title
  // 随机选一个便签色
  const col = todo.color || NOTE_STYLES[Math.floor(Math.random() * NOTE_STYLES.length)].bg
  const match = NOTE_STYLES.find(s => s.bg === col)
  editStickyColor.value = match || { bg: col, text: '#fff' }
  editVisible.value = true
  closeCtx()
  nextTick(() => editInputRef.value?.focus())
}

function closeEdit() {
  editVisible.value = false
  editText.value = ''
}

function confirmEdit() {
  const todo = ctxTodo.value
  if (!todo) return
  const title = editText.value.trim()
  if (!title) return
  if (isVirtual(todo)) {
    todo.title = title
  } else {
    updateTodo(todo.id, { title }).then(() => {
      todo.title = title
      emit('todo-changed')
    }).catch(() => {})
  }
  closeEdit()
}

function jumpToNote(todo) {
  if (todo.note_id) {
    emit('jump-to-note', { noteId: todo.note_id, notebookId: todo.notebook_id })
  }
}
function jumpToNotebook(todo) {
  if (todo.notebook_id) {
    emit('jump-to-note', { notebookId: todo.notebook_id, isNotebook: true })
  }
}
function onNoteClick(todo) {
  // 有 note_id 的跳转到笔记正文，有 notebook_id 的跳转到笔记本目录
  if (todo.note_id) {
    jumpToNote(todo)
  } else if (todo.notebook_id) {
    jumpToNotebook(todo)
  }
}

function doDeleteCtx() {
  const todo = ctxTodo.value
  if (todo) removeTodo(todo.id)
}

// ── 打标词库 ──
const LABEL_POOL = ['不想干', '拖着吧', '好烦哦', '明天吧', '啊啊啊', '懒得弄', '麻了', '缓缓', '摸鱼', '再说', '下次', '算了', '好累哦', '不想动', '溜了']

async function doToggleLabel() {
  const todo = ctxTodo.value
  if (!todo) return
  const newLabel = todo.label ? null : LABEL_POOL[Math.floor(Math.random() * LABEL_POOL.length)]
  if (isVirtual(todo)) {
    todo.label = newLabel
  } else {
    try {
      await updateTodo(todo.id, { label: newLabel })
      todo.label = newLabel
      emit('todo-changed')
    } catch (e) {
      console.error(e)
    }
  }
  closeCtx()
}

onMounted(() => {
  loadTodos()
  document.addEventListener('click', closeCtx)
  themeObserver = new MutationObserver(() => { isDark.value = !document.documentElement.classList.contains('light-theme') })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  setTimeout(() => nextTick(initTodoSortable), 100)
})

onUnmounted(() => {
  document.removeEventListener('click', closeCtx)
  if (themeObserver) themeObserver.disconnect()
  if (todoSortable) todoSortable.destroy()
})
</script>

<style scoped>
/* ── 乐米小奶泡体 ── */
@font-face {
  font-family: 'LemiXiaoNaiPaoTi';
  src: url('/fonts/lemixiaonaipao.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
}

.todo-panel {
  display: flex;
  flex-direction: column;
  padding: 20px 16px 24px;
  height: 100%;
  position: relative;
  overflow-y: auto;
}

/* ── 头部 ── */
.todo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 0 4px;
  position: sticky;
  top: 0;
  z-index: 2;
}
/* 进度条和输入框也跟着粘住 */
.progress-bar, .todo-input-line { position: sticky; z-index: 2; }
.progress-bar { top: 38px; }
.todo-input-line { top: 48px; }
.todo-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 26px;
  font-family: "LemiXiaoNaiPaoTi", cursive;
  letter-spacing: -5px;
  color: var(--text);
  font-weight: 700;
  text-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-glass);
  border-radius: 8px;
  color: var(--text3);
  transition: all 0.2s;
}
.close-btn:hover {
  background: rgba(255,255,255,0.1);
  color: var(--text);
}

/* ── 进度条 ── */
.progress-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
  margin: 0 4px 5px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6C5CE7, #00CEC9);
  border-radius: 3px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(108, 92, 231, 0.4);
}
.progress-text {
  font-size: 11px;
  color: var(--text3);
  margin: 0 4px 12px;
  display: flex;
  justify-content: space-between;
}

/* ── 输入框 ── */
.todo-input-line {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  padding: 0 4px;
}
.todo-input-line input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  font-size: 13px;
}
.todo-input-line input::placeholder {
  color: var(--text3);
}
.todo-input-line input:focus {
  border-color: var(--primary);
}
.add-btn {
  width: 36px;
  height: 36px;
  background: var(--primary);
  border-radius: 10px;
  color: white;
  font-size: 20px;
  font-weight: 600;
  transition: opacity 0.2s;
  flex-shrink: 0;
}
.add-btn:hover {
  opacity: 0.85;
}

/* ── 便签列表容器 ── */
.sticky-notes {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 2px 8px;
  min-height: 0;
}
.sticky-notes-scroll {
  overflow: visible;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 0;
}

/* 拖拽中禁用 FLIP 动画 */
.sticky-notes.drag-active .note-list-move {
  transition: none !important;
}

/* ── 单条便签 ── */
.sticky-note {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px 7px 14px;
  border-radius: 3px;
  transition: box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease;
  cursor: grab;
  transform: none;
  box-shadow:
    0 2px 4px rgba(0,0,0,0.12),
    0 1px 2px rgba(0,0,0,0.08),
    inset 0 1px 0 rgba(255,255,255,0.3),
    inset 0 -1px 0 rgba(0,0,0,0.04);
  flex-shrink: 0;
  overflow: visible;
  user-select: none;
}
/* 纸张纹理叠加 — 图片噪点（GPU加速） */
.sticky-note::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: url('/images/textures/noisy.png') repeat;
  background-size: 60% 60%;
  background-position: var(--bg-pos, 0% 0%);
  mix-blend-mode: var(--tex-blend, multiply);
  opacity: var(--tex-opacity, 0.55);
  border-radius: inherit;
}
.sticky-note::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.06) 50%);
  border-radius: 0 0 3px 0;
  pointer-events: none;
}
.sticky-note:active {
  cursor: grabbing;
}
.sticky-note.is-note {
  cursor: pointer;
}
.sticky-note.dragging {
  opacity: 0.4;
  box-shadow:
    0 8px 20px rgba(0,0,0,0.25),
    0 4px 8px rgba(0,0,0,0.15);
  transform: scale(1.03);
  z-index: 10;
}

/* 上端胶条 */
.note-tape {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40%;
  height: 6px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 0 0 2px 2px;
  pointer-events: none;
}

/* 悬停微抬起 */
.sticky-note:hover {
  transform: translateY(-2px);
  box-shadow:
    0 4px 8px rgba(0,0,0,0.15),
    0 2px 4px rgba(0,0,0,0.1);
}

/* 已完成态 */
.sticky-note.is-done {
  opacity: 0.55;
}
.sticky-note.is-done .note-text {
  text-decoration: line-through;
}

/* 日历同步便签 */
.sticky-note.is-calendar {
  cursor: default;
}
.sticky-note.is-calendar:hover {
  transform: none;
}
.note-pin {
  font-size: 10px;
  margin-left: 4px;
  vertical-align: middle;
  filter: drop-shadow(0 1px 1px rgba(0,0,0,0.2));
}
.note-from {
  font-size: 10px;
  margin-left: 4px;
  vertical-align: middle;
}
.note-from.note-deleted {
  opacity: 0.4;
  cursor: default;
}
.note-attach {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  margin-left: auto;
  padding-left: 4px;
}
.note-jump-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: rgba(255,255,255,0.15);
  cursor: pointer;
  font-size: 11px;
  flex-shrink: 0;
  transition: background .12s;
}
.note-jump-btn:hover {
  background: rgba(255,255,255,0.3);
}
.note-selected-preview {
  font-size: 9px;
  color: rgba(0,0,0,0.3);
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ── 复选框 ── */
.note-check {
  position: relative;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  cursor: pointer;
}
.note-check input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}
.check-icon {
  position: absolute;
  inset: 0;
  border: 2px solid;
  border-color: inherit;
  border-radius: 3px;
  transition: all 0.2s;
}
.note-check input:checked ~ .check-icon {
  border-color: rgba(0,0,0,0.25);
  background: rgba(0,0,0,0.25);
}
.note-check input:checked ~ .check-icon::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 5px;
  height: 9px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
  opacity: 0.85;
}
.sticky-note .check-icon {
  border-color: inherit;
}
.note-check input:checked ~ .check-icon {
  border-color: rgba(0,0,0,0.2);
  background: rgba(0,0,0,0.2);
}

/* ── 文本 ── */
.note-text {
  flex: 1;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
  font-weight: 500;
  padding-right: 28px;
}

/* ── "不想干" 标签：红色小便签贴 ── */
.note-label-tape {
  position: absolute;
  bottom: 8px;
  right: -8px;
  padding: 1px 6px;
  background: #E74C3C;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  border-radius: 3px;
  transform: rotate(-20deg);
  box-shadow: 0 2px 6px rgba(0,0,0,0.18);
  pointer-events: none;
  z-index: 10;
}
/* 标签纹理叠加 */
.note-label-tape::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: url('/images/textures/noisy.png') repeat;
  background-size: 60% 60%;
  mix-blend-mode: var(--tex-blend, multiply);
  opacity: var(--tex-opacity, 0.55);
  border-radius: inherit;
}
.note-label-tape.floating {
  position: fixed;
  z-index: 99999;
  pointer-events: none;
}
.note-label-tape::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 0 0 1px 1px;
}
.note-label-tape span {
  font-size: 16px;
  font-weight: 700;
  font-family: "LemiXiaoNaiPaoTi", cursive;
  letter-spacing: -3px;
}

/* ── 空状态 ── */
.empty-todo {
  text-align: center;
  color: var(--text3);
  font-size: 13px;
  padding: 40px 0;
}

/* ── TransitionGroup 动画 ── */
.note-list-move {
  transition: transform 0.45s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.35s ease;
}
.note-list-enter-active {
  transition: all 0.3s ease;
}
.note-list-leave-active {
  transition: all 0.25s ease;
  position: absolute;
}
.note-list-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.95);
}
.note-list-leave-to {
  opacity: 0;
  transform: scale(0.85);
}

/* ── 右键菜单 ── */
.ctx-menu {
  position: fixed;
  z-index: 999;
  min-width: 110px;
  background: var(--bg-menu);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.ctx-item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  border-radius: 5px;
  color: var(--text2);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.1s;
  white-space: nowrap;
}
.ctx-item:hover {
  background: var(--bg-glass);
  color: var(--text);
}

/* ── 修改弹窗（便签风格） ── */
.edit-overlay-noblur {
  position: fixed; inset: 0; z-index: 99999;
}
.edit-sticky {
  width: 320px; max-width: 85vw;
  border-radius: 12px; padding: 20px 20px 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 2px 0 0 rgba(0,0,0,0.06) inset;
  position: fixed; z-index: 99999;
  display: flex; flex-direction: column; gap: 12px;
}
.edit-sticky::before {
  content: ''; position: absolute; top: 0; left: 50%;
  transform: translateX(-50%);
  width: 70%; height: 14px;
  background: rgba(255,255,255,0.35);
  border-radius: 0 0 4px 4px;
}
.edit-sticky-header {
  font-size: 15px; font-weight: 700; color: #2d3436;
  margin-top: 4px;
}
.edit-sticky-text {
  width: 100%; min-height: 80px; padding: 10px 12px;
  font-size: 14px; line-height: 1.5;
  border: none; border-radius: 8px;
  background: rgba(255,255,255,0.55);
  color: #2d3436; outline: none; resize: vertical;
  font-family: inherit; box-sizing: border-box;
}
.edit-sticky-text:focus {
  background: rgba(255,255,255,0.75);
  box-shadow: 0 0 0 2px rgba(255,183,77,0.5);
}
.edit-sticky-actions {
  display: flex; justify-content: flex-end; gap: 8px;
}
.edit-sticky-btn {
  padding: 7px 18px; font-size: 13px; font-weight: 600;
  border: none; border-radius: 8px; cursor: pointer; transition: all 0.12s;
}
.edit-sticky-cancel {
  background: rgba(0,0,0,0.06); color: #2d3436;
}
.edit-sticky-cancel:hover { background: rgba(0,0,0,0.12); }
.edit-sticky-confirm {
  background: #6C5CE7; color: #fff;
}
.edit-sticky-confirm:hover { filter: brightness(1.15); }

@media (max-width: 768px) {
  .todo-panel { padding:12px 10px 16px; }
  .todo-header { padding:0 2px; }
  .todo-header h2 { font-size:20px; }
  .todo-add { padding:6px 12px; gap:6px; font-size:12px; }
  .sticky-note { padding:7px 8px; gap:6px; font-size:12px; }
  .note-check { width:16px; height:16px; }
  .note-tag { font-size:8px; padding:1px 4px; }
  .edit-sticky { width:85vw; max-width:320px; padding:16px; }
}
</style>
