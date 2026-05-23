/**
 * 颜色常量工具函数测试
 */
import { describe, it, expect } from 'vitest'
import { NOTE_COLORS, NOTE_STYLES, NOTE_STYLES_DARK, LIGHT_TO_DARK, randomColor } from '@/constants/colors'

describe('NOTE_COLORS', () => {
  it('10 种颜色', () => {
    expect(NOTE_COLORS.length).toBe(10)
  })

  it('每个都是 7 位 hex', () => {
    NOTE_COLORS.forEach(c => {
      expect(c).toMatch(/^#[0-9A-Fa-f]{6}$/)
    })
  })
})

describe('NOTE_STYLES', () => {
  it('与 NOTE_COLORS 长度一致', () => {
    expect(NOTE_STYLES.length).toBe(NOTE_COLORS.length)
  })

  it('每个都有 bg 和 text', () => {
    NOTE_STYLES.forEach(s => {
      expect(s).toHaveProperty('bg')
      expect(s).toHaveProperty('text')
    })
  })

  it('浅色背景的文字色为深色', () => {
    // #FDCB6E 和 #FFEAA7 是浅色 → text 应为深色
    const light = NOTE_STYLES.find(s => s.bg === '#FDCB6E')
    expect(light?.text).toBe('#2d3436')
  })

  it('深色背景的文字色为白色', () => {
    const dark = NOTE_STYLES.find(s => s.bg === '#FF6B6B')
    expect(dark?.text).toBe('#fff')
  })
})

describe('NOTE_STYLES_DARK', () => {
  it('与 NOTE_COLORS 长度一致', () => {
    expect(NOTE_STYLES_DARK.length).toBe(NOTE_COLORS.length)
  })
})

describe('LIGHT_TO_DARK', () => {
  it('浅色键能找到深色值', () => {
    const darkStyle = LIGHT_TO_DARK.get('#FF6B6B')
    expect(darkStyle).toBeDefined()
    expect(darkStyle?.bg).toBe('#8B3A3A')
  })

  it('未知颜色返回 undefined', () => {
    expect(LIGHT_TO_DARK.get('#000000')).toBeUndefined()
  })
})

describe('randomColor', () => {
  it('返回 NOTE_COLORS 中的颜色', () => {
    for (let i = 0; i < 50; i++) {
      const c = randomColor()
      expect(NOTE_COLORS).toContain(c)
    }
  })
})
