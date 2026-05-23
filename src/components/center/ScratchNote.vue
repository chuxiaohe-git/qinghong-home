<template>
  <div class="scratch-note-view">
    <div class="sn-desk">

      <!-- ═══ 顶部通栏 — 书架区 ═══ -->
      <div class="sn-top-bar">
        <div class="sn-bookshelf" ref="shelfRef" :class="shelfMode">
          <div v-for="(book, i) in store.notebooks" :key="book.id"
            class="sn-book" :class="{ active: book.id === store.currentNotebookId }"
            :style="bookStyle(i)" @click="switchNotebook(book.id)"
            @contextmenu.prevent="showBookMenu($event, book)" :draggable="true"
            @dragstart="onNotebookDragStart($event, i)" @dragover.prevent="onNotebookDragOver($event, i)"
            @dragleave="onNotebookDragLeave($event)" @drop.prevent="onNotebookDrop($event, i)" @dragend="onNotebookDragEnd">
            <div class="sn-book-spine"><span class="sn-book-label">{{ book.title || '新笔记' }}</span></div>
          </div>
          <button class="sn-add-book" @click="addBook" title="新建笔记本">+</button>
        </div>
        <div v-if="bookMenu.visible" class="sn-book-menu" :style="{ left: bookMenu.x + 'px', top: bookMenu.y + 'px' }">
          <button @click="renameBookStart(bookMenu.book)">重命名</button>
          <button v-if="!bookMenu.isLinked" @click="bookMenuToggleTodo">📋 添加到待办</button>
          <button v-else @click="bookMenuRemoveTodo">❌ 从待办删除</button>
          <button @click="deleteBook(bookMenu.book.id)" class="danger">删除</button>
        </div>
        <div v-if="renaming" class="sn-rename-overlay" @click.self="renaming = null">
          <div class="sn-rename-box">
            <input ref="renameInput" v-model="renameText" @keyup.enter="renameBookConfirm" @keyup.escape="renaming = null" placeholder="输入笔记本名称"/>
            <div class="sn-rename-actions">
              <button @click="renaming = null">取消</button>
              <button class="primary" @click="renameBookConfirm">确定</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 下部区域 — 笔记本+目录 ═══ -->
      <div class="sn-bottom-area">
        <div v-if="store.currentNotebook" class="sn-notebook" ref="notebookRef"
          :key="store.currentNotebookId" :style="{ '--nb-color': store.notebookColors.color, '--nb-color2': store.notebookColors.color2 }">

          <!-- 目录弹出面板（笔记本左侧） -->
          <div class="sn-dir-zone" @mouseenter="dirOpen = true" @mouseleave="dirOpen = false">
            <div class="sn-dir-hover-trigger"></div>
            <div class="sn-dir-panel" :class="{ open: dirOpen }">
              <div class="sn-dir-inner">
                <div class="sn-dir-header"><span>{{ store.currentNotebook?.title || '目录' }}</span><button class="sn-dir-add" @click="addNote" title="新增笔记">+</button></div>
                <div class="sn-note-entries">
                  <div v-for="(note, idx) in store.notes" :key="note.id" class="sn-note-entry" :draggable="true"
                    @click="openNote(note.id)" @dragstart="onNoteDragStart($event, idx)" @dragover.prevent="onNoteDragOver($event, idx)"
                    @dragleave="onNoteDragLeave($event)" @drop.prevent="onNoteDrop($event, idx)" @dragend="onNoteDragEnd"
                    @contextmenu.prevent="showNoteEntryMenu($event, note)">
                    <span class="sn-note-entry-title">{{ note.title || '无标题' }}
                      <span v-if="store.linkedTodoIds.includes(note.id)" class="sn-badge" title="有关联待办">📌</span>
                    </span>
                    <span class="sn-note-entry-meta">{{ note.updated_at?.slice(0, 10) || '' }}</span>
                  </div>
                  <div v-if="store.notes.length === 0" class="sn-note-empty">暂无笔记，点击 + 新建</div>
                </div>
              </div>
            </div>
          </div>

          <div class="sn-coils"><div class="sn-coil" v-for="n in coilCount" :key="n"></div></div>
          <div class="sn-ribbon"></div>
          <template v-if="viewMode === 'content'">
            <div class="sn-watermark">{{ store.currentNotebook?.title || '' }}</div>
            <button class="sn-back-btn" @click="backToDirectory" title="返回目录">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5m7-7l-7 7 7 7"/></svg><span>目录</span>
            </button>
            <!-- 标题行（可右键→待办） -->
            <div class="sn-header">
              <input class="sn-note-title-input" v-model="noteTitle" placeholder="无标题" @input="onNoteTitleChange"
                @contextmenu.prevent="showTitleMenu($event, store.currentNote)" />
              <span v-if="store.linkedTodoIds.includes(store.currentNoteId)" class="sn-badge sn-badge-title" title="有关联待办">📌</span>
            </div>
            <!-- 内容编辑区：双模（textarea / contenteditable） -->
            <div class="sn-textarea-wrap">
              <!-- textarea 模式（无高亮 || 用户选择编辑） -->
              <textarea v-if="editorMode === 'textarea'" class="sn-textarea" v-model="noteContent" placeholder="在这里写点什么…"
                @input="onNoteContentChange" rows="1" ref="textareaRef"
                @contextmenu.prevent="onTextareaContextMenu"></textarea>
              <!-- contenteditable 预览模式（有高亮文本） -->
              <div v-else class="sn-contenteditable" ref="contentEditableRef"
                contenteditable="true"
                @input="onContentEditableInput"
                @mouseup="onContentMouseUp"
                @click="floatingMenu.visible = false"
                @contextmenu.prevent="onContentContextMenu"></div>
              <!-- 切换按钮 -->
              <button v-if="hasHighlights" class="sn-mode-toggle" @click="toggleEditorMode" :title="editorMode === 'textarea' ? '预览高亮' : '编辑模式'">
                {{ editorMode === 'textarea' ? '👁️' : '✏️' }}
              </button>
            </div>
            <div class="sn-footer">
              <span>{{ charCount }} 字 · {{ saved ? '已保存' : '输入中…' }}
                <span v-if="editorMode === 'contenteditable'" class="sn-mode-hint">· 预览模式</span>
              </span>
              <span class="sn-date">{{ dateStr }}</span>
              <button class="sn-clear" @click="deleteCurrentNote">删除此页</button>
            </div>
          </template>
          <template v-else>
            <div class="sn-directory-body">
              <div class="sn-directory-head">
                <div class="sn-title">{{ store.currentNotebook?.title || '摸鱼笔记' }}</div>
                <div class="sn-date">{{ dateStr }}</div>
              </div>
              <div class="sn-directory-actions"><button class="sn-new-note-btn" @click="addNote">+ 新建笔记</button></div>
              <div class="sn-note-grid" v-if="store.notes.length > 0">
                <div v-for="(note, idx) in store.notes" :key="note.id" class="sn-grid-item" @click="openNote(note.id)"
                  @contextmenu.prevent="showNoteEntryMenu($event, note)">
                  <span class="sn-grid-num">{{ (idx + 1).toString().padStart(2, '0') }}</span>
                  <span class="sn-grid-title">{{ note.title || '无标题' }}<span v-if="store.linkedTodoIds.includes(note.id)" class="sn-badge" title="有关联待办">📌</span></span>
                </div>
              </div>
              <div v-else class="sn-empty-hint"><p>点击「+ 新建笔记」开始记录摸鱼心得</p></div>
            </div>
          </template>
        </div>
      </div>

    </div>

    <!-- ═══ 笔记条目 / 标题 右键菜单 ═══ -->
    <Teleport to="body">
      <div v-if="noteCtx.visible" class="sn-ctx-menu" :style="{ left: noteCtx.x + 'px', top: noteCtx.y + 'px' }">
        <button v-if="!noteCtx.isLinked" class="sn-ctx-item" @click="noteCtxAddTodo">📋 添加到待办</button>
        <button v-if="!noteCtx.isLinked" class="sn-ctx-item" @click="noteCtxAddCalendarTodo">📅 添加到日历</button>
        <button v-else class="sn-ctx-item" @click="noteCtxRemoveTodo">❌ 从待办删除</button>
        <div class="sn-ctx-divider"></div>
        <button class="sn-ctx-item danger" @click="noteCtxDeleteNote">🗑 删除</button>
      </div>
    </Teleport>

    <!-- ═══ 选中文本浮动菜单 ═══ -->
    <Teleport to="body">
      <div v-if="floatingMenu.visible" class="sn-ctx-menu"
        :style="{ left: floatingMenu.x + 'px', top: floatingMenu.y + 'px' }">
        <button v-if="!floatingMenu.isHighlighted" class="sn-ctx-item" @click="addSelectedTextTodo">📋 添加到待办</button>
        <button v-if="!floatingMenu.isHighlighted" class="sn-ctx-item" @click="addSelectedTextToCalendar">📅 添加到日历</button>
        <button v-else class="sn-ctx-item danger" @click="removeSelectedTextTodo">❌ 删除待办</button>
      </div>
    </Teleport>

    <!-- ═══ 选择日期弹窗 ═══ -->
    <Teleport to="body">
      <div v-if="datePicker.visible" class="sn-date-overlay" @click.self="datePicker.visible = false">
        <div class="sn-date-box">
          <div class="sn-date-title">选择日期</div>
          <input type="date" v-model="datePicker.date" class="sn-date-input" />
          <div class="sn-date-actions">
            <button @click="datePicker.visible = false">取消</button>
            <button class="primary" @click="confirmDatePicker">确定</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useScratchNoteStore } from '@/stores/scratch-note'
import { NOTE_COLORS, randomColor } from '@/constants/colors'
import { deleteTodo, getTodosByNote, createTodo } from '@/api/todo'

const emit = defineEmits(['todo-changed'])

const store = useScratchNoteStore()
const viewMode = ref('directory')
const dirOpen = ref(false)
const saved = ref(true)
let saveTimer = null

// ── 书架状态 ──
const shelfRef = ref(null)
const notebookRef = ref(null)
const coilCount = ref(0)
const shelfMode = ref('')
const bookMenu = ref({ visible: false, x: 0, y: 0, book: null })
const renaming = ref(null)
const renameText = ref('')
const renameInput = ref(null)

// ── 本地编辑状态 ──
const noteTitle = ref('')
const noteContent = ref('')

// ── 编辑器双模 ──
const editorMode = ref('textarea')   // 'textarea' | 'contenteditable'
const textareaRef = ref(null)
const contentEditableRef = ref(null)

// ── 笔记右键菜单 ──
const noteCtx = ref({ visible: false, x: 0, y: 0, note: null, isLinked: false })

// ── 选中文本浮动菜单 ──
const floatingMenu = ref({ visible: false, x: 0, y: 0, text: '' })

// ── 日期选择器 ──
const datePicker = ref({ visible: false, date: '', context: null })
// context: { type: 'note', note } | { type: 'text', text, startPos }

const dateStr = computed(() => {
  const d = new Date()
  const w = ['日','一','二','三','四','五','六']
  return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 星期${w[d.getDay()]}`
})

const charCount = computed(() => (noteContent.value || '').length)

// 当前笔记是否有关联高亮
const hasHighlights = computed(() => {
  if (!store.currentNoteId) return false
  return (store.highlightedTexts[store.currentNoteId] || []).length > 0
})

function escapeHtml(str) {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

// ── 切换笔记本 ──
async function switchNotebook(id) {
  await store.switchNotebook(id)
  viewMode.value = 'directory'
  editorMode.value = 'textarea'
}

// ── 目录页操作 ──
async function addNote() {
  if (!store.currentNotebookId) return
  const n = await store.addNote(store.currentNotebookId)
  if (n) await openNote(n.id)
}

async function openNote(id) {
  // 打开笔记前确保高亮数据最新（可能从右侧面板删除了关联待办）
  await store.ensureLinkedTodoIds()
  await store.selectNote(id)
  // 获取笔记详情（含正文内容）
  const detail = await store.fetchNoteDetail(id)
  if (detail) {
    noteTitle.value = detail.title || ''
    noteContent.value = detail.content || ''
  } else if (store.currentNote) {
    noteTitle.value = store.currentNote.title || ''
    noteContent.value = store.currentNote.content || ''
  }
  // 先设置视图和编辑器模式（让 DOM 先渲染出 contenteditable div）
  const highlights = store.highlightedTexts[id] || []
  editorMode.value = highlights.length > 0 ? 'contenteditable' : 'textarea'
  viewMode.value = 'content'
  // DOM 渲染完成后填充高亮内容
  if (editorMode.value === 'contenteditable') {
    await nextTick()
    buildHighlightHtml()
  }
}

function backToDirectory() {
  viewMode.value = 'directory'
  editorMode.value = 'textarea'
  floatingMenu.value.visible = false
}

// 高亮变化时自动同步 contenteditable 内容
watch(() => store.currentHighlights?.length, () => {
  if (editorMode.value === 'contenteditable') {
    nextTick(syncContentEditable)
  }
}, { deep: true })

// ── 编辑器模式切换 ──
let settingContentHtml = false

function toggleEditorMode() {
  if (editorMode.value === 'textarea') {
    editorMode.value = 'contenteditable'
    nextTick(syncContentEditable)
  } else {
    if (contentEditableRef.value) {
      noteContent.value = contentEditableRef.value.innerText || ''
      onNoteContentChange()
    }
    editorMode.value = 'textarea'
  }
}

function syncContentEditable() {
  refreshContenteditable()
}

function refreshContenteditable() {
  buildHighlightHtml()
}

// ── 编辑笔记 ──
function onNoteTitleChange() {
  if (!store.currentNote) return
  saveTimer && clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    await store.editNote(store.currentNote.id, { title: noteTitle.value })
  }, 600)
}

function onNoteContentChange() {
  if (!store.currentNote) return
  saved.value = false
  saveTimer && clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    await store.editNote(store.currentNote.id, { content: noteContent.value })
    saved.value = true
  }, 600)
}

function onContentEditableInput() {
  if (settingContentHtml) return
  if (!store.currentNote || !contentEditableRef.value) return
  saved.value = false
  // contenteditable 模式下存 pure text
  const text = contentEditableRef.value.innerText || ''
  noteContent.value = text
  saveTimer && clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    await store.editNote(store.currentNote.id, { content: text })
    saved.value = true
  }, 600)
}

async function deleteCurrentNote() {
  if (!store.currentNote) return
  if (!confirm('删除此笔记？')) return
  await store.removeNote(store.currentNote.id)
  viewMode.value = 'directory'
  editorMode.value = 'textarea'
}

// ── 笔记本CRUD ──
async function addBook() {
  const nb = await store.addNotebook('新笔记本')
  if (nb) {
    viewMode.value = 'directory'
    await store.addNote(nb.id)
  }
}

async function deleteBook(id) {
  if (!confirm('删除笔记本及其所有内容？')) return
  await store.removeNotebook(id)
  bookMenu.value.visible = false
  viewMode.value = 'directory'
}

async function showBookMenu(e, book) {
  let linked = false
  try {
    const { data: todos } = await getTodosByNote(0, book.id)
    // 只检查笔记本级待办（note_id 为空）
    linked = todos && todos.some(t => !t.note_id)
  } catch (e) {}
  bookMenu.value = { visible: true, x: e.clientX + 6, y: e.clientY + 6, book, isLinked: linked }
}

function closeBookMenu(e) {
  if (bookMenu.value.visible && shelfRef.value && !shelfRef.value.contains(e.target)) {
    bookMenu.value.visible = false
  }
  // 点击笔记区域外关闭笔记右键菜单
  if (noteCtx.value.visible && !e.target.closest('.sn-ctx-menu,.sn-note-entry,.sn-ctx-overlay')) {
    noteCtx.value.visible = false
  }
  // 关闭选中文本浮动菜单
  if (floatingMenu.value.visible && !e.target.closest('.sn-ctx-menu')) {
    floatingMenu.value.visible = false
  }
}

function renameBookStart(book) {
  bookMenu.value.visible = false
  renaming.value = book
  renameText.value = book.title
  nextTick(() => renameInput.value?.focus())
}

async function renameBookConfirm() {
  if (renaming.value && renameText.value.trim()) {
    await store.renameNotebook(renaming.value.id, renameText.value.trim())
  }
  renaming.value = null
}

async function bookMenuToggleTodo() {
  const book = bookMenu.value.book
  if (!book) return
  bookMenu.value.visible = false
  try {
    const res = await createTodo(book.title || '新笔记本', 0, book.color || '#8B4513', { notebook_id: book.id })
    if (res.code === 0) emit('todo-changed')
  } catch (e) { console.error(e) }
}

async function bookMenuRemoveTodo() {
  const book = bookMenu.value.book
  if (!book) return
  bookMenu.value.visible = false
  try {
    // 只删除笔记本级待办（note_id 为空的），保留笔记和词条待办
    const { data: allTodos } = await getTodosByNote(0, book.id)
    const bookTodos = (allTodos || []).filter(t => !t.note_id)
    if (bookTodos.length > 0) {
      await Promise.all(bookTodos.map(t => deleteTodo(t.id)))
    }
    emit('todo-changed')
  } catch (e) { console.error(e) }
}

// ── 笔记条目右键菜单 ──
function showNoteEntryMenu(e, note) {
  noteCtx.value = {
    visible: true,
    x: Math.min(e.clientX, window.innerWidth - 160),
    y: Math.min(e.clientY, window.innerHeight - 100),
    note: note,
    isLinked: store.linkedTodoIds.includes(note.id),
  }
}

function showTitleMenu(e, note) {
  if (!note) return
  showNoteEntryMenu(e, note)
}

function closeNoteCtx() {
  noteCtx.value.visible = false
}

async function noteCtxAddTodo() {
  const note = noteCtx.value.note
  if (!note) return
  closeNoteCtx()
  await store.addNoteTodo(note.id, note.title || '无标题', '')
  emit('todo-changed')
}

function noteCtxAddCalendarTodo() {
  const note = noteCtx.value.note
  if (!note) return
  closeNoteCtx()
  // 打开日期选择器
  const today = new Date()
  datePicker.value = {
    visible: true,
    date: today.toISOString().slice(0, 10),
    context: { type: 'note', note },
  }
}

async function noteCtxDeleteNote() {
  const note = noteCtx.value.note
  if (!note) return
  closeNoteCtx()
  if (!confirm('删除此笔记？')) return
  // 如果当前正在查看的就是这个笔记，切回目录
  if (store.currentNoteId === note.id) {
    viewMode.value = 'directory'
    editorMode.value = 'textarea'
  }
  await store.removeNote(note.id)
  emit('todo-changed')
}

function addSelectedTextToCalendar() {
  const text = floatingMenu.value.text
  if (!text || !store.currentNote) return
  const savedRange = floatingMenu.value.savedRange
  let startPos = 0
  if (savedRange) {
    const container = contentEditableRef.value
    if (container && container.contains(savedRange.startContainer)) {
      startPos = getTextOffset(container, savedRange.startContainer, savedRange.startOffset)
    }
  }
  if (startPos <= 0 && text) {
    const lastIdx = noteContent.value.lastIndexOf(text)
    if (lastIdx >= 0) startPos = lastIdx
  }
  floatingMenu.value.visible = false
  window.getSelection()?.removeAllRanges()
  const today = new Date()
  datePicker.value = {
    visible: true,
    date: today.toISOString().slice(0, 10),
    context: { type: 'text', text, startPos },
  }
}

async function confirmDatePicker() {
  const dp = datePicker.value
  if (!dp.date || !dp.context) return
  dp.visible = false
  const ctx = dp.context
  const dateStr = dp.date
  const todoColor = randomColor()

  try {
    if (ctx.type === 'note') {
      await createTodo(ctx.note.title || '无标题', 0, todoColor, {
        notebook_id: store.currentNotebookId,
        note_id: ctx.note.id,
        date: dateStr,
      })
    } else if (ctx.type === 'text') {
      const res = await createTodo(ctx.text, 0, todoColor, {
        note_id: store.currentNoteId,
        notebook_id: store.currentNotebookId,
        selected_text: ctx.text,
        date: dateStr,
        highlight_start: ctx.startPos >= 0 ? ctx.startPos : undefined,
      })
      // 同步到本地高亮
      if (res.code === 0 && store.currentNoteId) {
        if (!store.highlightedTexts[store.currentNoteId]) {
          store.highlightedTexts[store.currentNoteId] = []
        }
        store.highlightedTexts[store.currentNoteId].push({
          text: ctx.text,
          todo_id: res.data.id,
          color: todoColor,
          start: ctx.startPos >= 0 ? ctx.startPos : undefined,
        })
        if (!store.linkedTodoIds.includes(store.currentNoteId)) {
          store.linkedTodoIds.push(store.currentNoteId)
        }
        if (editorMode.value === 'contenteditable') {
          await nextTick()
          buildHighlightHtml()
        }
      }
    }
    emit('todo-changed')
  } catch (e) {
    console.error(e)
  }
}

async function noteCtxRemoveTodo() {
  const note = noteCtx.value.note
  if (!note) return
  closeNoteCtx()
  // 只删除笔记级待办（selected_text 为空），保留词条级高亮待办
  try {
    const { data: linkedTodos } = await getTodosByNote(note.id)
    const noteTodos = linkedTodos.filter(t => !t.selected_text)
    if (noteTodos.length > 0) {
      await Promise.all(noteTodos.map(t => deleteTodo(t.id)))
    }
  } catch (e) { console.error(e) }
  // 只清除笔记级关联标记，词条高亮保留
  store.linkedTodoIds = store.linkedTodoIds.filter(nid => nid !== note.id)
  // 如果没有任何词条待办了才清除 highlightedTexts
  const { data: remaining } = await getTodosByNote(note.id).catch(() => ({ data: [] }))
  const hasTextTodos = remaining.some(t => t.selected_text)
  if (!hasTextTodos) {
    delete store.highlightedTexts[note.id]
  }
  emit('todo-changed')
}

// ── 选中文本浮动菜单（仅右键触发） ──
let floatingHideTimer = null

function onContentMouseUp(e) {
  // 不再在此处弹出菜单，统一由 onContentContextMenu（右键）处理
  clearTimeout(floatingHideTimer)
}

// 选中文本右键菜单（适配 textarea 和 contenteditable）
function onTextareaContextMenu(e) {
  e.preventDefault()
  const el = e.target
  const start = el.selectionStart
  const end = el.selectionEnd
  if (start === end) return
  const text = el.value.substring(start, end).trim()
  if (!text || text.length > 100) return
  showFloatingAt(e.clientX, e.clientY, text)
}

function onContentContextMenu(e) {
  e.preventDefault()  // 显式阻止系统菜单（contenteditable 下 .prevent 可能不稳定）
  // 检查是否点在高亮 span 元素上
  const uEl = e.target.closest('span[data-todo-id]')
  if (uEl) {
    const todoId = parseInt(uEl.dataset.todoId)
    const text = uEl.textContent
    showFloatingAt(e.clientX, e.clientY, text, true, todoId)
    return
  }
  // 否则检查是否有选中文字
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || !sel.toString().trim()) return
  const text = sel.toString().trim()
  if (!text || text.length > 100) return
  const highlights = store.currentHighlights
  const existing = highlights.find(h => h.text === text)
  if (existing) {
    showFloatingAt(e.clientX, e.clientY, text, true, existing.todo_id)
  } else {
    showFloatingAt(e.clientX, e.clientY, text)
  }
}

function showFloatingAt(x, y, text, isHighlighted = false, todoId = null) {
  const sel = window.getSelection()
  const savedRange = sel && sel.rangeCount > 0 ? sel.getRangeAt(0).cloneRange() : null
  // textarea 模式下保存 selectionStart（点击按钮后选区会丢失）
  const savedTextareaPos = textareaRef.value?.selectionStart ?? -1
  floatingMenu.value = {
    visible: true,
    x: Math.min(x, window.innerWidth - 180),
    y: Math.max(y - 45, 10),
    text: text,
    isHighlighted,
    todoId,
    savedRange,
    savedTextareaPos,
  }
}

async function addSelectedTextTodo() {
  const text = floatingMenu.value.text
  if (!text || !store.currentNote) return
  floatingMenu.value.visible = false

  // 使用浮动菜单弹出时保存的选区（点击按钮后选区会丢失）
  let startPos = 0
  const savedRange = floatingMenu.value.savedRange
  if (savedRange) {
    const container = contentEditableRef.value
    if (container && container.contains(savedRange.startContainer)) {
      startPos = getTextOffset(container, savedRange.startContainer, savedRange.startOffset)
    }
  }
  if (startPos === 0 && floatingMenu.value.savedTextareaPos >= 0) {
    startPos = floatingMenu.value.savedTextareaPos
  }
  // 兜底：在正文内容中按文本搜索（从末尾匹配，避免 "哈哈哈哈" 匹配到开头）
  if (startPos <= 0 && text) {
    const lastIdx = noteContent.value.lastIndexOf(text)
    if (lastIdx >= 0) startPos = lastIdx
  }

  window.getSelection()?.removeAllRanges()

  await store.addNoteTodo(store.currentNote.id, text, text, startPos)
  const highlights = store.highlightedTexts?.[store.currentNote?.id]
  if (highlights?.length) {
    editorMode.value = 'contenteditable'
    await nextTick()
    buildHighlightHtml()
  }
  emit('todo-changed')
}

// 计算 contenteditable 中某文本节点的偏移在纯文本中的位置
function getTextOffset(root, targetNode, nodeOffset) {
  let pos = 0
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null)
  while (walker.nextNode()) {
    const n = walker.currentNode
    if (n === targetNode) return pos + nodeOffset
    pos += (n.textContent || '').length
  }
  return pos
}

async function removeSelectedTextTodo() {
  const todoId = floatingMenu.value.todoId
  if (!todoId) return
  floatingMenu.value.visible = false
  try {
    await deleteTodo(todoId)
    await store.ensureLinkedTodoIds()
    nextTick(syncContentEditable)
    emit('todo-changed')
  } catch (e) { console.error(e) }
}

// 关闭浮动菜单（点击其他地方）
function closeFloatingMenu(e) {
  if (floatingMenu.value.visible) {
    floatingMenu.value.visible = false
  }
}

// ── 从 Home 跳转过来打开笔记 ──
// 监听 store 的 pendingOpenNoteId（Home → ScratchNote 跨组件通信）
watch(() => store.pendingOpenNoteId, (val) => {
  if (val === 'directory') {
    viewMode.value = 'directory'
    store.pendingOpenNoteId = null
  } else if (val != null) {
    const id = val
    store.pendingOpenNoteId = null
    openNote(id)
  }
})

function onRefreshHighlights() {
  if (editorMode.value !== 'contenteditable') return
  // 先同步 store 数据（删除/新增待办后高亮列表可能已变化）
  store.ensureLinkedTodoIds().then(() => {
    buildHighlightHtml()
  })
}

function buildHighlightHtml() {
  const el = contentEditableRef.value
  if (!el) return
  const highlights = store.highlightedTexts?.[store.currentNote?.id]
  // ⚠️ contenteditable div 刚创建时 innerText 是空的，必须用 noteContent.value
  const currentText = noteContent.value || el.innerText || ''
  if (!highlights?.length) {
    if (el.innerHTML !== escapeHtml(currentText)) {
      el.innerHTML = escapeHtml(currentText)
    }
    return
  }

  // 对所有高亮先确定位置，再合起来一次排序渲染
  // 有 start 的直接用，没有的通过 lastIndexOf 在全文查找
  const resolved = [...highlights]
    .map(h => {
      let start = (h.start != null && h.start >= 0) ? h.start : -1
      if (start < 0 && h.text) {
        start = currentText.lastIndexOf(h.text)
      }
      const end = start >= 0 ? start + (h.text?.length || 0) : -1
      return { ...h, start, end }
    })
    // 只保留能找到位置的
    .filter(h => h.start >= 0)
    // 按位置排序
    .sort((a, b) => a.start - b.start)

  // 处理重叠：短文本被长文本包含时跳过；
  // 部分重叠时合并范围（扩展 end），避免视觉上文字重复
  let deduped = []
  for (const h of resolved) {
    let merged = false
    for (const ex of deduped) {
      if (ex.start <= h.start && ex.end >= h.end) {
        // h 完全被 ex 覆盖，跳过
        merged = true
        break
      }
      if (h.start < ex.end && h.end > ex.start) {
        // 部分重叠：合并范围
        ex.start = Math.min(ex.start, h.start)
        ex.end = Math.max(ex.end, h.end)
        merged = true
        break
      }
    }
    if (!merged) {
      deduped.push(h)
    }
  }

  // 合并后重新排序
  deduped.sort((a, b) => a.start - b.start)

  // 单次渲染 — 使用背景色高亮（颜色取自待办卡片颜色）
  let html = ''
  let pos = 0
  for (const h of deduped) {
    if (h.start > pos) html += escapeHtml(currentText.slice(pos, h.start))
    const color = h.color || '#FF6B6B'
    const highlightBg = color + 'AA'  // 药丸风格高亮，alpha 67%
    html += `<span data-todo-id="${h.todo_id}" style="background-color:${highlightBg};border-radius:2px;padding:0 1px;">${escapeHtml(currentText.slice(h.start, h.end))}</span>`
    pos = h.end
  }
  if (pos < currentText.length) html += escapeHtml(currentText.slice(pos))

  el.innerHTML = html
}

// ── 书架布局计算 ──
function checkShelfLayout() {
  const el = shelfRef.value
  if (!el) return
  const bookCount = store.notebooks.length
  const normalW = bookCount * 58 + 28
  const stackedW = bookCount * 46 + 28
  const availW = el.parentElement.getBoundingClientRect().width - 40
  if (shelfMode.value === '') {
    if (normalW > availW) shelfMode.value = 'stacked'
  } else if (shelfMode.value === 'stacked') {
    if (stackedW > availW) shelfMode.value = 'compact'
    else if (normalW + 120 < availW) shelfMode.value = ''
  } else {
    if (normalW < availW) shelfMode.value = 'stacked'
  }
}

function updateCoilCount() {
  const nb = notebookRef.value
  if (!nb) return
  const h = nb.getBoundingClientRect().height - 40
  coilCount.value = Math.floor(h / 16)
}

function bookStyle(i) {
  const book = store.notebooks[i]
  return {
    '--rot': ['-6deg','3deg','-2deg','5deg','-4deg','2deg'][i % 6],
    '--bc1': book.color,
    '--bc2': book.color2,
    zIndex: store.notebooks.length - i,
  }
}

// ── 笔记本拖拽排序 ──
let dragIdx = null
function onNotebookDragStart(e, i) { dragIdx = i; e.dataTransfer.effectAllowed = 'move' }
function onNotebookDragOver(e, i) {
  if (dragIdx === null || dragIdx === i) return
  const arr = store.notebooks
  const item = arr.splice(dragIdx, 1)[0]
  arr.splice(i, 0, item)
  dragIdx = i
}
function onNotebookDragLeave(e) {}
function onNotebookDrop(e, i) {}
function onNotebookDragEnd() {
  dragIdx = null
  store.reorderNotebooks(store.notebooks.map(nb => nb.id))
}

// ── 笔记拖拽排序 ──
let noteDragIdx = null
function onNoteDragStart(e, i) { noteDragIdx = i; e.dataTransfer.effectAllowed = 'move' }
function onNoteDragOver(e, i) {
  if (noteDragIdx === null || noteDragIdx === i) return
  const arr = store.notes
  const item = arr.splice(noteDragIdx, 1)[0]
  arr.splice(i, 0, item)
  noteDragIdx = i
}
function onNoteDragLeave(e) {}
function onNoteDrop(e, i) {}
function onNoteDragEnd() {
  noteDragIdx = null
  if (store.currentNotebookId) {
    store.reorderNotesInNotebook(store.notes.map(n => n.id))
  }
}

// ── 生命周期 ──
onMounted(async () => {
  // scratch-note-refresh-highlights 用于删除待办后刷新高亮
  window.addEventListener('scratch-note-refresh-highlights', onRefreshHighlights)
  // 在 init 前捕获 store 的跳转目标（init 是异步的，可能耗时较长）
  const pendingId = store.pendingOpenNoteId
  store.pendingOpenNoteId = null
  await store.init()
  // init 完成后处理跳转
  if (pendingId === 'directory') {
    viewMode.value = 'directory'
  } else if (pendingId != null) {
    openNote(pendingId)
  }
  document.addEventListener('click', closeBookMenu)
  document.addEventListener('click', closeNoteCtx)
  document.addEventListener('click', closeFloatingMenu)
  nextTick(() => { updateCoilCount(); checkShelfLayout() })
  window.addEventListener('resize', () => { updateCoilCount(); checkShelfLayout() })
})
onBeforeUnmount(() => {
  document.removeEventListener('click', closeBookMenu)
  document.removeEventListener('click', closeNoteCtx)
  document.removeEventListener('click', closeFloatingMenu)
  window.removeEventListener('scratch-note-refresh-highlights', onRefreshHighlights)
})
watch(() => store.notebooks.length, () => nextTick(checkShelfLayout))
watch(() => store.currentNotebookId, () => { editorMode.value = 'textarea'; nextTick(updateCoilCount) })
</script>

<style scoped>
@font-face {
  font-family:'XiaoLai';
  src:url('/fonts/XiaoLai.woff2') format('woff2');
  font-display:swap;
}
.scratch-note-view { height:100%; display:flex; font-family:'XiaoLai',serif; }
.sn-desk {
  width:100%; height:100%;
  background:url('/images/backgrounds/desk-bg.jpg') center/cover no-repeat;
  border-radius:12px; position:relative;
  box-shadow:0 1px 0 rgba(255,255,255,0.03) inset,0 8px 40px rgba(0,0,0,0.5),0 2px 6px rgba(0,0,0,0.3);
  display:flex; flex-direction:column; padding:4px 24px 24px;
}
.sn-top-bar {
  height:76px; flex-shrink:0; position:relative;
  overflow:visible; z-index:10;
}
.sn-bottom-area {
  flex:1; display:flex;
  align-items:center; justify-content:center; min-height:0;
  padding-bottom:10px;
}
.sn-book-menu {
  position:fixed; z-index:100;
  background:rgba(249,245,238,0.98);
  border:1px solid rgba(139,115,85,0.12);
  border-radius:6px; box-shadow:0 4px 12px rgba(0,0,0,0.12);
  padding:3px; min-width:100px;
}
.sn-book-menu button {
  display:block; width:100%; padding:6px 12px;
  border:none; border-radius:4px; background:transparent;
  font-size:12px; color:#5a4a38; cursor:pointer; text-align:left;
}
.sn-book-menu button:hover { background:rgba(139,115,85,0.06); }
.sn-book-menu .danger { color:#b03a2e; }
.sn-book-menu .danger:hover { background:rgba(200,80,80,0.08); }
.sn-rename-overlay {
  position:fixed; inset:0; z-index:200; display:flex; align-items:center; justify-content:center;
  background:rgba(0,0,0,0.15);
}
.sn-rename-box {
  background:rgba(249,245,238,0.98); border-radius:8px;
  padding:16px; box-shadow:0 4px 20px rgba(0,0,0,0.15);
}
.sn-rename-box input {
  border:1px solid rgba(139,115,85,0.15); border-radius:4px;
  padding:6px 10px; font-size:13px; width:200px; outline:none;
  font-family:inherit; background:rgba(200,180,160,0.08);
}
.sn-rename-actions { display:flex; gap:6px; justify-content:flex-end; margin-top:10px; }
.sn-rename-actions button {
  padding:4px 12px; border:1px solid rgba(139,115,85,0.12);
  border-radius:4px; background:transparent; font-size:11px; cursor:pointer; color:#5a4a38;
}
.sn-rename-actions .primary { background:rgba(139,115,85,0.1); border-color:rgba(139,115,85,0.2); }

/* ═══ 书架 ═══ */
.sn-bookshelf {
  position:absolute; top:6px; right:0; z-index:5;
  display:flex; align-items:flex-end; gap:6px;
}
.sn-bookshelf.stacked { gap:0; }
.sn-bookshelf.stacked .sn-book,
.sn-bookshelf.stacked .sn-add-book { margin-left:-12px; }
.sn-book {
  width:52px; height:64px;
  border-radius:3px 8px 8px 3px;
  cursor:pointer; position:relative;
  transform:rotate(var(--rot,0deg));
  transition:transform .18s,box-shadow .18s,margin .18s;
  box-shadow:2px 4px 10px rgba(0,0,0,0.35);
  flex-shrink:0;
  background:linear-gradient(180deg,var(--bc1),var(--bc2));
  overflow:hidden;
}
.sn-book::after {
  content:''; position:absolute; inset:0;
  background:url('/images/textures/leather-texture.png') repeat; background-size:cover;
  opacity:0.3; mix-blend-mode:multiply; pointer-events:none;
}
.sn-bookshelf.stacked .sn-book:first-child { margin-left:0; }
.sn-book:hover { transform:rotate(0deg) translateY(-4px); box-shadow:3px 6px 16px rgba(0,0,0,0.45); z-index:2; }
.sn-book.active { transform:rotate(0deg) !important; z-index:10; }
.sn-book.active::after {
  content:''; position:absolute; left:-3px; top:3px; bottom:3px; width:4px;
  background:rgba(255,255,255,0.1); border-radius:1px;
}
.sn-bookshelf.compact { flex-wrap:wrap; gap:2px; right:0; left:0; top:4px; align-items:flex-start; max-height:64px; overflow-y:auto; }
.sn-bookshelf.compact .sn-book { width:18px; height:56px; margin-left:0; border-radius:2px 6px 6px 2px; flex-shrink:0; }
.sn-bookshelf.compact .sn-book-spine { position:static; display:flex; align-items:center; justify-content:center; padding:4px 2px; height:100%; }
.sn-bookshelf.compact .sn-book-label { writing-mode:vertical-rl; font-size:10px; font-weight:600; white-space:nowrap; letter-spacing:0.5px; }
.sn-bookshelf.compact .sn-add-book { width:18px; height:56px; border-radius:2px 6px 6px 2px; font-size:12px; }
.sn-book-spine { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding:8px 4px; overflow:hidden; z-index:1; }
.sn-book-label { writing-mode:vertical-rl; text-orientation:mixed; font-size:11px; font-weight:700; color:rgba(230,215,195,0.85); letter-spacing:1px; line-height:1.3; font-family:'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif; text-shadow:0 1px 2px rgba(0,0,0,0.5); }
.sn-add-book { width:52px; height:64px; border-radius:3px 8px 8px 3px; background:rgba(0,0,0,0.2); border:1px dashed rgba(255,255,255,0.15); color:rgba(255,255,255,0.3); font-size:18px; cursor:pointer; flex-shrink:0; display:flex; align-items:center; justify-content:center; position:relative; }
.sn-add-book::after { content:''; position:absolute; inset:0; background:url('/images/textures/leather-texture.png') repeat; background-size:cover; opacity:0.15; mix-blend-mode:multiply; pointer-events:none; border-radius:inherit; }
.sn-add-book:hover { color:rgba(255,255,255,0.5); border-color:rgba(255,255,255,0.25); background:rgba(0,0,0,0.3); }

/* ═══ 目录弹出面板 ═══ */
.sn-dir-zone { position:absolute; right:100%; top:0; bottom:0; z-index:2; display:flex; align-items:stretch; width:220px; }
.sn-dir-hover-trigger { flex:1; cursor:default; }
.sn-dir-panel { width:0; overflow:hidden; transition:width .22s cubic-bezier(0.4,0,0.2,1); display:flex; flex-direction:column; background:rgba(249,245,238,0.98); box-shadow:2px 0 12px rgba(0,0,0,0.08); }
.sn-dir-panel.open { width:220px; border-radius:8px 0 0 8px; }
.sn-dir-inner { width:220px; flex:1; display:flex; flex-direction:column; min-height:0; position:relative; overflow:hidden; }
.sn-dir-inner::after { content:''; position:absolute; inset:0; background:url('/images/textures/noisy.png') repeat; background-size:50% 50%; opacity:0.08; pointer-events:none; z-index:0; }
.sn-dir-header { display:flex; justify-content:space-between; align-items:center; padding:16px 14px 10px; font-size:13px; font-weight:700; color:#5a4a38; letter-spacing:2px; position:relative; z-index:1; }
.sn-dir-header::after { content:''; position:absolute; left:14px; right:14px; bottom:0; height:1px; background:linear-gradient(90deg,transparent 0%,rgba(139,115,85,0.12) 50%,transparent 100%); }
.sn-dir-add { width:22px; height:22px; border-radius:50%; border:1px dashed rgba(139,115,85,0.25); background:transparent; font-size:14px; color:rgba(139,115,85,0.35); cursor:pointer; display:flex; align-items:center; justify-content:center; }
.sn-dir-add:hover { color:rgba(139,115,85,0.6); border-color:rgba(139,115,85,0.35); }

/* ═══ 笔记本 ═══ */
.sn-notebook {
  width:82%; max-width:650px;
  align-self:stretch;
  background:#f9f5ee;
  border-radius:3px 8px 8px 3px;
  box-shadow:3px 4px 18px rgba(0,0,0,0.35),inset 0 0 40px rgba(139,115,85,0.03);
  border:1px solid rgba(139,115,85,0.15);
  position:relative; display:flex; flex-direction:column;
  padding:16px 16px 10px; padding-left:26px;
}
.sn-notebook::before {
  content:''; position:absolute; left:0; top:10px; bottom:10px; width:18px;
  background:linear-gradient(90deg,rgba(139,115,85,0.12),rgba(139,115,85,0.04) 40%,transparent 60%);
  border-right:1px solid rgba(139,115,85,0.1);
}
.sn-notebook::after {
  content:''; position:absolute; inset:0;
  background:url('/images/textures/noisy.png') repeat; background-size:50% 50%;
  opacity:0.08; pointer-events:none; z-index:0; border-radius:inherit;
}
.sn-coils {
  position:absolute; left:-9px; top:20px; bottom:20px; width:18px;
  display:flex; flex-direction:column; gap:2px; z-index:3;
  overflow:hidden; pointer-events:none;
}
.sn-coil {
  width:18px; height:14px; border-radius:9px; flex-shrink:0;
  border:2px solid var(--nb-color2,#c8b898);
  background:linear-gradient(180deg,color-mix(in srgb,var(--nb-color) 60%,#e0d5c5),var(--nb-color2),var(--nb-color));
  box-shadow:inset 0 1px 2px rgba(255,255,255,0.3);
}
.sn-ribbon {
  position:absolute; top:-6px; right:8px; z-index:5;
  width:12px; height:56px;
  background:linear-gradient(180deg,var(--nb-color),var(--nb-color2));
  border-radius:2px; box-shadow:0 1px 2px rgba(0,0,0,0.2);
}
.sn-ribbon::after {
  content:''; position:absolute; bottom:-5px; left:50%; transform:translateX(-50%);
  border-left:6px solid var(--nb-color2); border-right:6px solid var(--nb-color2);
  border-bottom:7px solid transparent; border-radius:0 0 2px 2px;
}
.sn-watermark {
  position:absolute; top:10px; left:26px; z-index:1;
  font-size:16px; opacity:0.18; color:#3a3028;
  pointer-events:none; white-space:nowrap; letter-spacing:4px;
  font-weight:600;
}
.sn-back-btn {
  position:absolute; top:10px; right:16px; z-index:2;
  display:flex; align-items:center; gap:3px;
  padding:4px 10px; border:1px solid rgba(139,115,85,0.12);
  border-radius:4px; background:transparent;
  font-size:11px; color:rgba(139,115,85,0.5); cursor:pointer; font-family:inherit;
}
.sn-back-btn:hover { color:rgba(139,115,85,0.8); border-color:rgba(139,115,85,0.25); }
.sn-back-btn svg { width:14px; height:14px; }
.sn-header { text-align:center; margin-bottom:32px; position:relative; z-index:1; }
.sn-title { font-size:15px; font-weight:700; color:#5a4a38; letter-spacing:3px; }
.sn-date { font-size:10px; color:rgba(139,115,85,0.4); margin-top:1px; }
.sn-note-title-input {
  border:none; outline:none; background:transparent;
  font-family:inherit; font-size:18px; font-weight:700; color:#5a4a38;
  letter-spacing:3px; width:200px; text-align:center;
}
.sn-textarea-wrap { flex:1; position:relative; margin-left:4px; z-index:1; display:flex; flex-direction:column; min-height:0; }
.sn-textarea-wrap::before {
  content:''; position:absolute; inset:0;
  background:repeating-linear-gradient(to bottom, transparent, transparent 29px, rgba(139,115,85,0.06) 29px, rgba(139,115,85,0.06) 30px);
  pointer-events:none;
}
.sn-textarea {
  flex:1; width:100%; min-height:0;
  border:none; outline:none; resize:none;
  background:transparent;
  font-size:17px; line-height:30px; color:#3a3028;
  position:relative; z-index:1;
}
.sn-textarea::placeholder { color:rgba(139,115,85,0.2); }

/* ═══ contenteditable 预览模式 ═══ */
.sn-contenteditable {
  flex:1; width:100%; min-height:80px;
  border:none; outline:none;
  background:transparent;
  font-size:17px; line-height:30px; color:#3a3028;
  position:relative; z-index:1;
  white-space:pre-wrap; word-wrap:break-word;
}
.sn-contenteditable:focus {
  border:none; outline:none;
}
.sn-contenteditable span[data-todo-id] {
  cursor: pointer;
  transition: opacity 0.15s;
}
.sn-contenteditable span[data-todo-id]:hover {
  opacity: 0.75;
}
.sn-mode-toggle {
  position:absolute; top:4px; right:4px; z-index:3;
  width:24px; height:24px;
  border:1px solid rgba(139,115,85,0.12);
  border-radius:4px; background:rgba(249,245,238,0.8);
  font-size:12px; cursor:pointer; display:flex; align-items:center; justify-content:center;
  padding:0; line-height:1;
  opacity:0.4; transition:opacity .15s;
}
.sn-mode-toggle:hover { opacity:0.8; }
.sn-mode-hint { font-size:9px; color:rgba(139,115,85,0.3); margin-left:4px; }

.sn-footer {
  display:flex; justify-content:space-between; align-items:center;
  margin-top:2px; padding-top:4px; position:relative; z-index:1;
  font-size:10px; color:rgba(139,115,85,0.4); letter-spacing:1px;
}
.sn-footer::before {
  content:''; position:absolute; left:0; right:4px; top:0; height:1px;
  background:linear-gradient(90deg,transparent 0%,rgba(139,115,85,0.10) 10%,rgba(139,115,85,0.10) 90%,transparent 100%);
}
.sn-clear {
  padding:2px 10px; border:1px solid rgba(139,115,85,0.15);
  border-radius:4px; background:transparent;
  font-size:10px; color:rgba(139,115,85,0.4); cursor:pointer;
}
.sn-clear:hover { color:rgba(200,80,80,0.6); border-color:rgba(200,80,80,0.2); }

/* ═══ 日期选择弹窗 ═══ */
.sn-date-overlay {
  position:fixed; inset:0; z-index:99999;
  display:flex; align-items:center; justify-content:center;
  background:rgba(0,0,0,0.15);
}
.sn-date-box {
  background:rgba(249,245,238,0.98);
  border-radius:8px; padding:20px;
  box-shadow:0 4px 20px rgba(0,0,0,0.15);
  display:flex; flex-direction:column; gap:14px;
}
.sn-date-title {
  font-size:14px; font-weight:700; color:#5a4a38; text-align:center;
}
.sn-date-input {
  border:1px solid rgba(139,115,85,0.15); border-radius:4px;
  padding:8px 10px; font-size:14px; outline:none;
  font-family:inherit; color:#5a4a38;
}
.sn-date-actions {
  display:flex; gap:8px; justify-content:flex-end;
}
.sn-date-actions button {
  padding:6px 16px; border:1px solid rgba(139,115,85,0.12);
  border-radius:4px; background:transparent; font-size:12px;
  cursor:pointer; color:#5a4a38; font-family:inherit;
}
.sn-date-actions .primary {
  background:rgba(139,115,85,0.1); border-color:rgba(139,115,85,0.2);
}

/* ═══ 目录页（默认视图）- 两栏纵向排列 ═══ */
.sn-directory-body {
  flex:1; display:flex; flex-direction:column;
  padding:0 8px; position:relative; z-index:1;
  min-height:0; overflow:hidden;
}
.sn-directory-head { text-align:center; flex-shrink:0; }
.sn-directory-actions { text-align:center; margin:10px 0; flex-shrink:0; }
.sn-new-note-btn {
  padding:6px 16px; border:1px dashed rgba(139,115,85,0.2);
  border-radius:6px; background:transparent;
  font-size:12px; color:rgba(139,115,85,0.4); cursor:pointer; font-family:inherit;
}
.sn-new-note-btn:hover { color:rgba(139,115,85,0.6); border-color:rgba(139,115,85,0.35); }
.sn-note-grid {
  flex:1; min-height:0;
  column-count:2; column-gap:16px; column-fill:auto;
  overflow:hidden;
}
.sn-grid-item {
  display:flex; align-items:center; gap:12px;
  padding:7px 8px; border-radius:4px; cursor:pointer;
  transition:background .12s;
  break-inside:avoid;
  margin-bottom:2px;
}
.sn-grid-item:hover { background:rgba(139,115,85,0.06); }
.sn-grid-num {
  font-size:13px; color:#5a4a38; font-weight:700;
  flex-shrink:0; width:24px; text-align:right;
}
.sn-grid-title {
  font-size:13px; color:#5a4a38; font-weight:700;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.sn-empty-hint { text-align:center; margin-top:30px; }
.sn-empty-hint p { font-size:12px; color:rgba(139,115,85,0.25); }
.sn-note-entries { flex:1; overflow-y:auto; padding:4px; position:relative; z-index:1; }
.sn-note-entry {
  display:flex; justify-content:space-between; align-items:center;
  padding:8px 10px; cursor:pointer; border-radius:4px;
  transition:background .12s; margin-bottom:1px;
}
.sn-note-entry:hover { background:rgba(139,115,85,0.06); }
.sn-note-entry.dragging { opacity:0.4; }
.sn-note-entry-title { font-size:12px; color:#5a4a38; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:120px; }
.sn-note-entry-meta { font-size:9px; color:rgba(139,115,85,0.25); flex-shrink:0; }
.sn-note-empty { text-align:center; padding:20px; font-size:11px; color:rgba(139,115,85,0.2); }

/* ═══ 角标 ═══ */
.sn-badge { font-size:11px; margin-left:2px; vertical-align:middle; }
.sn-badge-title { position:absolute; right:80px; top:10px; font-size:14px; }

/* ═══ 笔记右键菜单 ═══ */
.sn-ctx-menu {
  position:fixed; z-index:999;
  background:rgba(249,245,238,0.98);
  border:1px solid rgba(139,115,85,0.12);
  border-radius:6px; box-shadow:0 4px 12px rgba(0,0,0,0.12);
  padding:3px; min-width:120px;
}
.sn-ctx-item {
  display:block; width:100%; padding:6px 12px;
  border:none; border-radius:4px; background:transparent;
  font-size:12px; color:#5a4a38; cursor:pointer; text-align:left; white-space:nowrap;
  font-family:inherit;
}
.sn-ctx-item:hover { background:rgba(139,115,85,0.06); }
.sn-ctx-item.danger { color:#b03a2e; }
.sn-ctx-item.danger:hover { background:rgba(200,80,80,0.08); }
.sn-ctx-divider { height:1px; background:rgba(139,115,85,0.1); margin:3px 0; }

/* ═══ 选中文本浮动菜单 ═══ */
.sn-float-menu {
  position:fixed; z-index:999;
  display:flex; align-items:center; gap:6px;
  background:rgba(249,245,238,0.95);
  border:1px solid rgba(139,115,85,0.15);
  border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,0.15);
  padding:4px 8px;
  transform:translateX(-50%);
}
.sn-float-btn {
  padding:4px 10px; border:none; border-radius:4px;
  background:rgba(139,115,85,0.1); color:#5a4a38;
  font-size:11px; cursor:pointer; white-space:nowrap;
  font-family:inherit;
}
</style>
