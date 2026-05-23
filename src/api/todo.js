import request from '@/utils/request'

export const getTodos = (done) =>
  request.get('/todos', { params: { done } })

export const createTodo = (title, priority = 0, color = null, extra = {}) =>
  request.post('/todos', { title, priority, color, ...extra })

export const updateTodo = (id, data) =>
  request.put(`/todos/${id}`, data)

export const deleteTodo = (id) =>
  request.delete(`/todos/${id}`)

export const reorderTodos = (orderData) =>
  request.post('/todos/reorder', orderData)

export const getTodosByNote = (noteId, notebookId) => {
  if (notebookId) return request.get('/todos', { params: { notebook_id: notebookId } })
  return request.get(`/todos/by-note/${noteId}`)
}

export const getTodosByNoteBatch = (noteIds) =>
  request.get('/todos/by-note-batch', { params: { note_ids: noteIds.join(',') } })
