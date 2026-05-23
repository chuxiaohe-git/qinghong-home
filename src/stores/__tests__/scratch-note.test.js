/**
 * scratch-note 状态管理测试
 *
 * 使用 vi.mock 模拟 API 调用，聚焦 Store 逻辑
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// ── 模拟所有 API 模块 ──
vi.mock('@/api/scratch-note', () => ({
  getNotebooks: vi.fn(),
  createNotebook: vi.fn(),
  updateNotebook: vi.fn(),
  reorderNotebooks: vi.fn(),
  deleteNotebook: vi.fn(),
  getNotes: vi.fn(),
  getNote: vi.fn(),
  createNote: vi.fn(),
  updateNote: vi.fn(),
  reorderNotes: vi.fn(),
  deleteNote: vi.fn(),
}))

vi.mock('@/api/todo', () => ({
  getTodosByNoteBatch: vi.fn(),
  deleteTodo: vi.fn(),
  createTodo: vi.fn(),
}))

import * as scratchApi from '@/api/scratch-note'
import * as todoApi from '@/api/todo'
import { useScratchNoteStore } from '@/stores/scratch-note'

// 测试数据
const fakeNotebooks = [
  { id: 1, title: '工作笔记', color: '#8B4513', color2: '#5C2E0A', sort_order: 0 },
  { id: 2, title: '个人日记', color: '#2E4057', color2: '#1a2a3a', sort_order: 1 },
]

const fakeNotes = [
  { id: 10, notebook_id: 1, title: '周一计划', content: '开会', sort_order: 0 },
  { id: 11, notebook_id: 1, title: '周二计划', content: '写代码', sort_order: 1 },
]

describe('scratchNote store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('初始值正确', () => {
      const store = useScratchNoteStore()
      expect(store.notebooks).toEqual([])
      expect(store.notes).toEqual([])
      expect(store.currentNotebookId).toBeNull()
      expect(store.currentNoteId).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.linkedTodoIds).toEqual([])
      expect(store.highlightedTexts).toEqual({})
      expect(store.pendingOpenNoteId).toBeNull()
    })
  })

  describe('getters', () => {
    it('currentNotebook 返回当前笔记本', () => {
      const store = useScratchNoteStore()
      store.notebooks = fakeNotebooks
      store.currentNotebookId = 1
      expect(store.currentNotebook?.title).toBe('工作笔记')
    })

    it('currentNotebook 无选中时返回 null', () => {
      const store = useScratchNoteStore()
      store.notebooks = fakeNotebooks
      expect(store.currentNotebook).toBeNull()
    })

    it('currentNote 返回当前笔记', () => {
      const store = useScratchNoteStore()
      store.notes = fakeNotes
      store.currentNoteId = 10
      expect(store.currentNote?.title).toBe('周一计划')
    })

    it('notebookColors 返回当前笔记本配色', () => {
      const store = useScratchNoteStore()
      store.notebooks = fakeNotebooks
      store.currentNotebookId = 1
      expect(store.notebookColors).toEqual({ color: '#8B4513', color2: '#5C2E0A' })
    })

    it('notebookColors 无选中时返回默认配色', () => {
      const store = useScratchNoteStore()
      expect(store.notebookColors).toEqual({ color: '#8B4513', color2: '#5C2E0A' })
    })
  })

  describe('笔记本 CRUD', () => {
    it('init() 加载笔记本和笔记', async () => {
      scratchApi.getNotebooks.mockResolvedValue({ code: 0, data: fakeNotebooks })
      scratchApi.getNotes.mockResolvedValue({ code: 0, data: fakeNotes })

      const store = useScratchNoteStore()
      await store.init()

      expect(store.notebooks).toEqual(fakeNotebooks)
      expect(store.notes).toEqual(fakeNotes)
    })

    it('addNotebook 创建笔记本', async () => {
      const newNb = { id: 3, title: '新笔记本', color: '#6B3A3A', color2: '#3d1f1f', sort_order: 2 }
      scratchApi.createNotebook.mockResolvedValue({ code: 0, data: newNb })
      scratchApi.getNotebooks.mockResolvedValue({ code: 0, data: [...fakeNotebooks, newNb] })

      const store = useScratchNoteStore()
      store.notebooks = fakeNotebooks
      const result = await store.addNotebook('新笔记本')

      expect(result.data).toEqual(newNb)
      expect(store.notebooks.length).toBe(3)
    })

    it('removeNotebook 删除笔记本', async () => {
      scratchApi.deleteNotebook.mockResolvedValue({ code: 0 })
      scratchApi.getNotebooks.mockResolvedValue({ code: 0, data: [fakeNotebooks[1]] })
      scratchApi.getNotes.mockResolvedValue({ code: 0, data: [] })
      todoApi.getTodosByNoteBatch.mockResolvedValue({ code: 0, data: {} })

      const store = useScratchNoteStore()
      store.notebooks = fakeNotebooks
      store.currentNotebookId = 1
      await store.removeNotebook(1)

      expect(store.notebooks.length).toBe(1)
      // 删除的是当前笔记本，自动切换到第一个剩下的
      expect(store.currentNotebookId).toBe(fakeNotebooks[1].id)
    })
  })

  describe('笔记 CRUD', () => {
    it('addNote 创建笔记', async () => {
      const newNote = { id: 12, notebook_id: 1, title: '', content: '', sort_order: 2 }
      scratchApi.createNote.mockResolvedValue({ code: 0, data: newNote })
      scratchApi.getNotes.mockResolvedValue({ code: 0, data: [...fakeNotes, newNote] })
      todoApi.getTodosByNoteBatch.mockResolvedValue({ code: 0, data: {} })

      const store = useScratchNoteStore()
      store.currentNotebookId = 1
      store.notes = fakeNotes
      const result = await store.addNote(1)

      expect(result.id).toBe(12)
    })

    it('selectNote 切换当前笔记', async () => {
      const store = useScratchNoteStore()
      store.notes = fakeNotes
      store.selectNote(10)
      expect(store.currentNoteId).toBe(10)
    })

    it('removeNote 删除笔记并清理联动数据', async () => {
      scratchApi.deleteNote.mockResolvedValue({ code: 0 })
      scratchApi.getNotes.mockResolvedValue({ code: 0, data: [fakeNotes[1]] })
      scratchApi.getNotebooks.mockResolvedValue({ code: 0, data: fakeNotebooks })
      todoApi.getTodosByNoteBatch.mockResolvedValue({ code: 0, data: {} })

      const store = useScratchNoteStore()
      store.notebooks = fakeNotebooks
      store.currentNotebookId = 1
      store.notes = fakeNotes
      store.linkedTodoIds = [10, 11]
      store.highlightedTexts = { 10: [{ text: '开会', todo_id: 1 }], 11: [] }
      store.currentNoteId = 11

      await store.removeNote(10)

      expect(store.notes.length).toBe(1)
      // ensureLinkedTodoIds 重新加载后 linkedTodoIds 由 mock 数据决定
      expect(store.linkedTodoIds).toEqual([])
      expect(store.highlightedTexts[10]).toBeUndefined()
      expect(store.currentNoteId).toBe(11)
    })
  })

  describe('待办联动', () => {
    it('addNoteTodo 添加待办', async () => {
      todoApi.createTodo.mockResolvedValue({ code: 0, data: { id: 99 } })

      const store = useScratchNoteStore()
      store.linkedTodoIds = []
      store.highlightedTexts = {}
      const result = await store.addNoteTodo(10, '测试笔记', '选中文本', 5)

      // 至少调用了 createTodo
      expect(todoApi.createTodo).toHaveBeenCalled()
      expect(result.action).toBe('added')
    })

    it('addNoteTodo 相同文本触发删除', async () => {
      const store = useScratchNoteStore()
      store.linkedTodoIds = [10]
      store.highlightedTexts = {
        10: [{ text: '选中文本', todo_id: 1, color: '#FF6B6B' }],
      }
      todoApi.deleteTodo.mockResolvedValue({ code: 0 })

      const result = await store.addNoteTodo(10, '测试', '选中文本', 5)

      expect(todoApi.deleteTodo).toHaveBeenCalledWith(1)
      expect(result.action).toBe('removed')
    })

    it('ensureLinkedTodoIds 加载关联待办', async () => {
      todoApi.getTodosByNoteBatch.mockResolvedValue({
        code: 0, data: { '10': [{ id: 1, selected_text: '测试', color: '#FF6B6B' }] },
      })
      scratchApi.getNotebooks.mockResolvedValue({ code: 0, data: fakeNotebooks })

      const store = useScratchNoteStore()
      store.notebooks = fakeNotebooks
      store.currentNotebookId = 1
      store.notes = fakeNotes
      store.linkedTodoIds = [10]
      await store.ensureLinkedTodoIds()

      expect(store.highlightedTexts[10]).toBeDefined()
      expect(store.highlightedTexts[10][0].text).toBe('测试')
    })
  })

  describe('pendingOpenNoteId', () => {
    it('直接设置 pendingOpenNoteId', () => {
      const store = useScratchNoteStore()
      store.pendingOpenNoteId = 10
      expect(store.pendingOpenNoteId).toBe(10)
    })
  })
})
