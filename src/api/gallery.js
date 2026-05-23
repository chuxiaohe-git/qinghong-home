import request from '@/utils/request'

export const getGallery = (type = 'all') =>
  request.get('/gallery', { params: { type } })

export const uploadImage = (file, type = 'wallpaper') => {
  const form = new FormData()
  form.append('file', file)
  form.append('type', type)
  return request.post('/gallery', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const deleteImage = (id) =>
  request.delete(`/gallery/${id}`)
