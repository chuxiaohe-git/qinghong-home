import request from '@/utils/request'

// 对话列表
export function getConversations() {
  return request.get('/conversations')
}

// 创建对话
export function createConversation(title = '') {
  return request.post('/conversations', { title })
}

// 获取单条对话（含消息）
export function getConversation(id) {
  return request.get(`/conversations/${id}`)
}

// 更新对话（标题 / 消息）
export function updateConversation(id, data) {
  return request.put(`/conversations/${id}`, data)
}

// 删除对话
export function deleteConversation(id) {
  return request.delete(`/conversations/${id}`)
}
