import request from '@/utils/request'

export const gequhaiSearch = (keyword) =>
  request.get('/music/gequhai/search', { params: { keyword } })

export const gequhaiUrl = (songId) =>
  request.post('/music/gequhai/url', { id: songId })

export const gequhaiLyric = (songId) =>
  request.get('/music/gequhai/lyric', { params: { id: songId } })

export const getPlaylist = () =>
  request.get('/music/playlist')

export const addToPlaylist = (data) =>
  request.post('/music/playlist', data)

export const removeFromPlaylist = (id) =>
  request.delete(`/music/playlist/${id}`)

export const refreshPlaylistUrl = (data) =>
  request.post('/music/playlist/refresh', data)
