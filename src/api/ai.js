import request from '@/utils/request'

/**
 * AI 聊天 — 推送消息，返回 SSE 事件流
 * onData(msg)   - 收到文本片段：{ type: 'text', content: '...' }
 *                 - 工具开始：{ type: 'tool_start', tool: 'add_bookmark' }
 *                 - 工具结束：{ type: 'tool_end', tool: '...', result: {...} }
 * onError(err)  - 出错
 * onDone()     - 流结束
 */
export function streamChat(messages, { onData, onError, onDone }) {
  const token = localStorage.getItem('token')

  fetch('/api/ai/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ messages }),
  }).then(async (response) => {
    if (!response.ok) {
      const errBody = await response.text().catch(() => '')
      onError(new Error(errBody || `请求失败: ${response.status}`))
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''  // 保留未完成的行

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = line.slice(6)
        if (payload === '[DONE]') {
          onDone && onDone()
          return
        }
        try {
          const data = JSON.parse(payload)
          onData(data)
        } catch {
          // skip malformed
        }
      }
    }
    onDone && onDone()
  }).catch((err) => {
    onError(err)
  })
}

/**
 * AI 设置
 */
export function getAISettings() {
  return request.get('/settings')
}

export function saveAISettings(config) {
  return request.put('/settings', {
    layout_config: JSON.stringify(config),
  })
}
