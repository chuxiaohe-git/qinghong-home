import request from '@/utils/request'

export const getBookmarks = (groupId) =>
  request.get('/bookmarks', { params: { group_id: groupId } })

export const searchBookmarks = (q) =>
  request.get('/bookmarks/search', { params: { q } })

export const createBookmark = (data) =>
  request.post('/bookmarks', data)

export const updateBookmark = (id, data) =>
  request.put(`/bookmarks/${id}`, data)

export const deleteBookmark = (id) =>
  request.delete(`/bookmarks/${id}`)

export const reorderBookmarks = (groupId, ids) =>
  request.put('/bookmarks/reorder', { group_id: groupId, ids })

export const updateBookmarkMarker = (id, marker) =>
  request.patch(`/bookmarks/${id}/marker`, { marker })
