import request from '@/utils/request'

export function getGuestStatus() {
  return request.get('/guest/status')
}

export function getGuestGroups() {
  return request.get('/guest/groups')
}
