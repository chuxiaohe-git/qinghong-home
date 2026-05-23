import request from '@/utils/request'

// ═══ Notebook API ═══

export const getNotebooks = () =>
  request.get('/notebooks')

export const createNotebook = (title, color = '#8B4513', color2 = '#5C2E0A') =>
  request.post('/notebooks', { title, color, color2 })

export const updateNotebook = (id, data) =>
  request.put(`/notebooks/${id}`, data)

export const reorderNotebooks = (orderedIds) =>
  request.put('/notebooks/reorder', { ordered_ids: orderedIds })

export const deleteNotebook = (id) =>
  request.delete(`/notebooks/${id}`)

// ═══ Note API ═══

export const getNotes = (notebookId) =>
  request.get('/notes', { params: { notebook_id: notebookId } })

export const getNote = (id) =>
  request.get(`/notes/${id}`)

export const createNote = (notebookId, title, content = '') =>
  request.post('/notes', { notebook_id: notebookId, title, content })

export const updateNote = (id, data) =>
  request.put(`/notes/${id}`, data)

export const reorderNotes = (orderedIds) =>
  request.put('/notes/reorder', { ordered_ids: orderedIds })

export const deleteNote = (id) =>
  request.delete(`/notes/${id}`)
