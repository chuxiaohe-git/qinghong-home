import request from '@/utils/request'

export const getCalendarTodos = (start, end) =>
  request.get('/calendar/todos', { params: { start, end } })

export const createCalendarTodo = (data) =>
  request.post('/calendar/todos', data)

export const updateCalendarTodo = (id, data) =>
  request.put(`/calendar/todos/${id}`, data)

export const deleteCalendarTodo = (id) =>
  request.delete(`/calendar/todos/${id}`)

export const getReminders = () =>
  request.get('/calendar/reminders')
