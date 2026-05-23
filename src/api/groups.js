import request from '@/utils/request'

export const getGroups = () => request.get('/groups')
export const createGroup = (name) => request.post('/groups', { name })
export const updateGroup = (id, data) => request.put(`/groups/${id}`, data)
export const deleteGroup = (id) => request.delete(`/groups/${id}`)
export const sortGroups = (order) => request.put('/groups/sort', { order })
