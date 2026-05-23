import request from '@/utils/request'

export const login = (username, password) =>
  request.post('/auth/login', { username, password })

export const getMe = () =>
  request.get('/auth/me')

export const changePassword = (oldPassword, newPassword) =>
  request.put('/auth/change-password', { old_password: oldPassword, new_password: newPassword })

export const uploadAvatar = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/auth/avatar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
