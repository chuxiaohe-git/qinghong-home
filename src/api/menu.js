import request from '@/utils/request'

export function getMenus() {
  return request.get('/menu')
}

export function saveMenus(menus) {
  return request.put('/menu', { menus })
}
