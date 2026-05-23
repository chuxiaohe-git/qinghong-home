import request from '@/utils/request'

export const getSettings = () =>
  request.get('/settings')

export const updateSettings = (data) =>
  request.put('/settings', data)
