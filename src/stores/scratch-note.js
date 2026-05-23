import { defineStore } from 'pinia'
import {
  getNotebooks, createNotebook, updateNotebook, reorderNotebooks, deleteNotebook,
  getNotes, getNote, createNote, updateNote, reorderNotes, deleteNote,
} from '@/api/scratch-note'
import { getTodosByNoteBatch, deleteTodo, createTodo } from '@/api/todo'
import { NOTE_COLORS, randomColor } from '@/constants/colors'
const DEFAULT_COVERS = [
  ['#8B4513', '#5C2E0A'], ['#2E4057', '#1a2a3a'], ['#6B3A3A', '#3d1f1f'],
  ['#3D5A3C', '#1e2f1d'], ['#5C4A3A', '#302820'], ['#4A3A5C', '#251f30'],
  ['#4A6741', '#2d3d27'], ['#7B3F3F', '#4a2525'], ['#3D5C6B', '#1f3340'],
  ['#5C3D6B', '#301d3d'], ['#6B5B3D', '#3d3020'], ['#3D4A5C', '#1d2533'],
  ['#6B4D3D', '#3d281f'], ['#4D5C3D', '#2a3520'], ['#5C3D4A', '#33202a'],
  ['#4A4D5C', '#242633'],
  ['#C0392B', '#7B241C'], ['#2980B9', '#1a5276'], ['#27AE60', '#145A32'],
  ['#8E44AD', '#4A235A'], ['#D35400', '#6E2C00'], ['#1ABC9C', '#0E6251'],
  ['#E67E22', '#7D3C00'], ['#9B59B6', '#512E5F'], ['#F39C12', '#7D6608'],
  ['#2ECC71', '#1D8348'],
]

// 便签颜色池（与 TodoPanel.NOTE_STYLES 一致，供外部引用）
function randomCover() {
  return DEFAULT_COVERS[Math.floor(Math.random() * DEFAULT_COVERS.length)]
}

export const useScratchNoteStore = defineStore('scratchNote', {
  state: () => ({
    notebooks: [],
    currentNotebookId: null,
    notes: [],
    currentNoteId: null,
    loading: false,
    // ── 待办联动状态 ──
    linkedTodoIds: [],            // 当前笔记本中有关联待办的 note_id 列表
    highlightedTexts: {},         // { note_id: [{ text, todo_id, color }] }
    // ── 跳转专用（Home → ScratchNote 跨组件通信） ──
    pendingOpenNoteId: null,      // Home 设置 → ScratchNote 读取后清空
  }),

  getters: {
    currentNotebook: (state) =>
      state.notebooks.find(nb => nb.id === state.currentNotebookId) || null,

    currentNote: (state) =>
      state.notes.find(n => n.id === state.currentNoteId) || null,

    notebookColors: (state) => {
      const nb = state.notebooks.find(nb => nb.id === state.currentNotebookId)
      return nb ? { color: nb.color, color2: nb.color2 } : { color: '#8B4513', color2: '#5C2E0A' }
    },

    // 当前笔记的高亮文本列表
    currentHighlights: (state) => {
      if (!state.currentNoteId) return []
      return state.highlightedTexts[state.currentNoteId] || []
    },
  },

  actions: {
    // ── 初始化：加载笔记本 + 若首次使用则创建默认笔记本 ──
    async init() {
      this.loading = true
      try {
        await this.fetchNotebooks()
        if (this.notebooks.length === 0) {
          await this._createDefaultNotebooks()
          await this.fetchNotebooks()
        }
        if (!this.currentNotebookId && this.notebooks.length > 0) {
          this.currentNotebookId = this.notebooks[0].id
          await this.fetchNotes(this.currentNotebookId)
          await this.ensureLinkedTodoIds()
        }
      } finally {
        this.loading = false
      }
    },

    async _createDefaultNotebooks() {
      const defaults = [
        { title: '摸鱼笔记', color: randomCover()[0], color2: randomCover()[1] },
        { title: '摸鱼计划', color: randomCover()[0], color2: randomCover()[1] },
        { title: '摸鱼灵感', color: randomCover()[0], color2: randomCover()[1] },
      ]
      for (const nb of defaults) {
        const res = await createNotebook(nb.title, nb.color, nb.color2)
        // 每个默认笔记本创建一条空笔记
        if (res.code === 0 && res.data) {
          await createNote(res.data.id, '', '')
        }
      }
    },

    // ── Notebook CRUD ──
    async fetchNotebooks() {
      const res = await getNotebooks()
      if (res.code === 0) {
        this.notebooks = res.data || []
      }
    },

    async addNotebook(title) {
      const [color, color2] = randomCover()
      const res = await createNotebook(title, color, color2)
      if (res.code === 0) {
        await this.fetchNotebooks()
        this.currentNotebookId = res.data.id
        await this.fetchNotes(res.data.id)
        await this.ensureLinkedTodoIds()
      }
      return res
    },

    async renameNotebook(id, title) {
      const res = await updateNotebook(id, { title })
      if (res.code === 0) {
        await this.fetchNotebooks()
      }
      return res
    },

    async removeNotebook(id) {
      const res = await deleteNotebook(id)
      if (res.code === 0) {
        await this.fetchNotebooks()
        // 如果删除的是当前笔记本，切换到第一个
        if (this.currentNotebookId === id) {
          if (this.notebooks.length > 0) {
            this.currentNotebookId = this.notebooks[0].id
            await this.fetchNotes(this.currentNotebookId)
            await this.ensureLinkedTodoIds()
          } else {
            this.currentNotebookId = null
            this.notes = []
            this.currentNoteId = null
            this.linkedTodoIds = []
            this.highlightedTexts = {}
          }
        }
      }
      return res
    },

    async reorderNotebooks(orderedIds) {
      const res = await reorderNotebooks(orderedIds)
      if (res.code === 0) {
        await this.fetchNotebooks()
      }
      return res
    },

    // ── 切换当前笔记本 ──
    async switchNotebook(id) {
      this.currentNotebookId = id
      this.currentNoteId = null
      await this.fetchNotes(id)
      await this.ensureLinkedTodoIds()
    },

    // ── 待办联动 ──
    async fetchLinkedTodoIds(notebookId) {
      if (!notebookId) {
        this.linkedTodoIds = []
        this.highlightedTexts = {}
        return
      }
      // 获取当前笔记本所有笔记的 id
      const noteIds = this.notes
        .filter(n => n.notebook_id === notebookId)
        .map(n => n.id)

      // 从 highlightedTexts 中清除不属于当前笔记本的数据
      const currentIds = new Set(noteIds)
      for (const nid of Object.keys(this.highlightedTexts)) {
        if (!currentIds.has(Number(nid))) {
          delete this.highlightedTexts[nid]
        }
      }

      if (noteIds.length === 0) {
        this.linkedTodoIds = []
        return
      }

      try {
        const res = await getTodosByNoteBatch(noteIds)
        if (res.code === 0) {
          const batch = res.data || {}
          // 先清空当前笔记本所有笔记的高亮，再重新构建
          for (const nid of noteIds) {
            delete this.highlightedTexts[nid]
          }
          this.linkedTodoIds = Object.keys(batch).map(Number)
          for (const [nid, todos] of Object.entries(batch)) {
            const numId = Number(nid)
            const hls = todos
              .filter(t => t.selected_text)
              .map(t => ({
                text: t.selected_text,
                todo_id: t.id,
                color: t.color || '#FF6B6B',
                start: t.highlight_start != null ? t.highlight_start : undefined,
              }))
            if (hls.length > 0) {
              this.highlightedTexts[numId] = hls
            }
          }
        }
      } catch (e) {
        console.error('fetchLinkedTodoIds error:', e)
      }
    },

    async ensureLinkedTodoIds() {
      await this.fetchLinkedTodoIds(this.currentNotebookId)
    },

    async addNoteTodo(noteId, title, selectedText = '', startPos = -1) {
      const existingHighlights = this.highlightedTexts[noteId] || []
      if (selectedText) {
        const existing = existingHighlights.find(h => h.text === selectedText)
        if (existing) {
          try {
            await deleteTodo(existing.todo_id)
          } catch (e) {
            console.error('delete todo error:', e)
          }
          // 直接删除本地高亮，不调 ensureLinkedTodoIds（避免数组重建造成位置丢失）
          this.highlightedTexts[noteId] = existingHighlights.filter(h => h.todo_id !== existing.todo_id)
          if (this.highlightedTexts[noteId].length === 0) {
            delete this.highlightedTexts[noteId]
          }
          return { action: 'removed' }
        }
      }

      // 添加新待办
      const todoColor = randomColor()
      try {
        const res = await createTodo(title, 0, todoColor, {
          note_id: noteId,
          notebook_id: this.currentNotebookId,
          selected_text: selectedText || null,
          highlight_start: startPos >= 0 ? startPos : undefined,
        })
        if (res.code === 0) {
          // 直接追加到本地高亮，不调 ensureLinkedTodoIds（避免数组重建造成旧高亮位置丢失）
          if (!this.highlightedTexts[noteId]) {
            this.highlightedTexts[noteId] = []
          }
          this.highlightedTexts[noteId].push({
            text: selectedText || title,
            todo_id: res.data.id,
            color: res.data.color || '#FF6B6B',
            start: startPos >= 0 ? startPos : (res.data.highlight_start != null ? res.data.highlight_start : undefined),
          })
          // 更新 linkedTodoIds
          if (!this.linkedTodoIds.includes(noteId)) {
            this.linkedTodoIds.push(noteId)
          }
          return { action: 'added', todo: res.data }
        }
      } catch (e) {
        console.error('create todo error:', e)
      }
      return { action: 'none' }
    },

    // ── Note CRUD ──
    async fetchNotes(notebookId) {
      const res = await getNotes(notebookId)
      if (res.code === 0) {
        this.notes = res.data || []
      }
    },

    async fetchNoteDetail(id) {
      const res = await getNote(id)
      if (res.code === 0) {
        return res.data
      }
      return null
    },

    async addNote(notebookId, title = '', content = '') {
      const res = await createNote(notebookId, title, content)
      if (res.code === 0) {
        await this.fetchNotes(notebookId)
        await this.ensureLinkedTodoIds()
        return res.data
      }
      return null
    },

    async editNote(id, data) {
      const res = await updateNote(id, data)
      if (res.code === 0) {
        // 更新本地 notes 列表中的项
        const idx = this.notes.findIndex(n => n.id === id)
        if (idx !== -1) {
          this.notes[idx] = { ...this.notes[idx], ...data }
        }
      }
      return res
    },

    async removeNote(id) {
      const notebookId = this.currentNotebookId
      const res = await deleteNote(id)
      if (res.code === 0 && notebookId) {
        await this.fetchNotes(notebookId)
        // 清理关联数据
        delete this.highlightedTexts[id]
        this.linkedTodoIds = this.linkedTodoIds.filter(nid => nid !== id)
        await this.ensureLinkedTodoIds()
        if (this.currentNoteId === id) {
          this.currentNoteId = null
        }
      }
      return res
    },

    async reorderNotesInNotebook(orderedIds) {
      const res = await reorderNotes(orderedIds)
      if (res.code === 0 && this.currentNotebookId) {
        await this.fetchNotes(this.currentNotebookId)
      }
      return res
    },

    // ── 选中笔记 ──
    selectNote(id) {
      this.currentNoteId = id
    },

    clearSelection() {
      this.currentNoteId = null
    },
  },
})
