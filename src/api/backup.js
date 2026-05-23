import request from '@/utils/request'

export const exportConfig = () =>
  request.get('/export')

export const importConfig = (data, mode = 'append') =>
  request.post('/import', { data, mode })

export const importBookmarksHtml = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/import/bookmarks', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const createBackup = () =>
  request.post('/backup')

export const listBackups = () =>
  request.get('/backups')

export const downloadBackup = (name) =>
  request.get(`/backup/${name}/download`, { responseType: 'blob' })

export const restoreBackup = (file) => {
  const form = new FormData()
  form.append('file', file)
  form.append('type', 'file')
  return request.post('/restore', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const restoreLocalBackup = (name) => {
  const form = new FormData()
  form.append('name', name)
  form.append('type', 'local')
  return request.post('/restore', form)
}
