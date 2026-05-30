import request from '@/utils/request'

export const getWikiDocs = () =>
  request.get('/wiki/docs')

export const getWikiDoc = (id) =>
  request.get(`/wiki/docs/${id}`)

export const createWikiDoc = (title = '', content = '') =>
  request.post('/wiki/docs', { title, content })

export const updateWikiDoc = (id, data) =>
  request.put(`/wiki/docs/${id}`, data)

export const deleteWikiDoc = (id) =>
  request.delete(`/wiki/docs/${id}`)

export const uploadWikiImage = (docId, file) => {
  const formData = new FormData()
  formData.append('image', file)
  return request.post(`/wiki/docs/${docId}/upload-image`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
