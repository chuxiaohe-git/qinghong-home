import request from '@/utils/request'

export const getUsers = (page = 1) =>
  request.get('/admin/users', { params: { page, per_page: 50 } })

export const createUser = (data) =>
  request.post('/admin/users', data)

export const toggleUser = (id) =>
  request.put(`/admin/users/${id}/toggle`)

export const resetUserPassword = (id, newPassword) =>
  request.put(`/admin/users/${id}/reset-password`, { new_password: newPassword })

export const updateUser = (id, data) =>
  request.put(`/admin/users/${id}`, data)

export const deleteUser = (id) =>
  request.delete(`/admin/users/${id}`)
