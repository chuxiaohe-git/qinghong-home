<template>
  <div class="notes-view">
    <div class="desk">
      <div class="file-rack">
        <div class="rack-body">
          <div class="rack-top">📚 笔记本</div>
          <div class="rack-inner">
            <div v-for="(b, i) in books" :key="i"
              class="nb-spine" :class="{ active: curIdx === i }"
              :style="{ background: `linear-gradient(180deg, ${b.c1}, ${b.c2})` }"
              @click="switchBook(i)">
              <span class="nb-spine-label">{{ b.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="book-wrap">
        <div class="book-shadow"></div>
        <div class="book-outer">
          <div class="cover-shell">
            <div class="cover-half-l" :style="{ background: `linear-gradient(160deg, ${cur.c1}, ${cur.c2} 50%, ${cur.c1})` }"></div>
            <div class="cover-half-r" :style="{ background: `linear-gradient(160deg, ${cur.c1}, ${cur.c2} 50%, ${cur.c1})` }"></div>
          </div>
          <div class="bookmark" :style="{ background: `linear-gradient(180deg, ${cur.c1}, ${cur.c2})` }"></div>
          <div class="book-thick"></div>
          <div class="book-inner" ref="flipRef"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { PageFlip } from 'page-flip'

const books = [
  { name:'项目笔记', c1:'#B03A2E', c2:'#922B21',
    pages:[
      '<div class="toc-title">目 录</div><div class="toc-line"></div><div class="toc-row"><span class="n01">01</span> 项目规划</div><div class="toc-row"><span class="n01">02</span> 技术调研</div><div class="toc-row"><span class="n01">03</span> 系统设计</div>',
      '<div class="tt">项目规划</div><div class="nb"><p>1. 确定需求</p><p>2. 搭建环境</p><p>3. 设计模型</p><p>4. 开发功能</p><p>5. 测试优化</p></div>',
      '<div class="tt">技术调研</div><div class="nb"><p>• Vue 3 生态</p><p>• StPageFlip</p><p>• CSS vs Canvas</p></div>',
      '<div class="tt">系统设计</div><div class="nb"><p>• 前端架构</p><p>• 后端 API</p><p>• 数据库</p></div>',
      '<div class="tt">开发日志</div><div class="nb"><p>Day1 初始化</p><p>Day2 功能开发</p><p>Day3 联调</p></div>',
      '<div class="tt">问题记录</div><div class="nb"><p>翻页卡顿→降帧</p><p>数据不同步→防抖</p></div>',
    ]},
  { name:'日常随记', c1:'#2471A3', c2:'#1A5276',
    pages:[
      '<div class="toc-title">目 录</div><div class="toc-line"></div><div class="toc-row"><span class="n01">01</span> 本周计划</div><div class="toc-row"><span class="n01">02</span> 购物清单</div>',
      '<div class="tt">本周计划</div><div class="nb"><p>• 整理房间</p><p>• 超市采购</p><p>• 看书</p></div>',
      '<div class="tt">购物清单</div><div class="nb"><p>牛奶</p><p>面包</p><p>水果</p></div>',
      '<div class="tt">旅行计划</div><div class="nb"><p>大理</p><p>下个月</p><p>预算3000</p></div>',
    ]},
  { name:'技术学习', c1:'#1E8449', c2:'#145A32',
    pages:[
      '<div class="toc-title">目 录</div><div class="toc-line"></div><div class="toc-row"><span class="n01">01</span> Vue 3</div>',
      '<div class="tt">Vue 3 笔记</div><div class="nb"><p>• Composition API</p><p>• Teleport</p><p>• Suspense</p></div>',
    ]},
  { name:'创意构思', c1:'#7D3C98', c2:'#5B2C6F',
    pages:[
      '<div class="toc-title">目 录</div><div class="toc-line"></div><div class="toc-row"><span class="n01">01</span> App 灵感</div>',
      '<div class="tt">App 灵感</div><div class="nb"><p>→ 跨平台同步</p><p>→ AI 写作</p><p>→ 语音输入</p></div>',
    ]},
  { name:'读书笔记', c1:'#CA6F1E', c2:'#A04000',
    pages:[
      '<div class="toc-title">目 录</div><div class="toc-line"></div><div class="toc-row"><span class="n01">01</span> 设计模式</div>',
      '<div class="tt">设计模式</div><div class="nb"><p>• 单例模式</p><p>• 观察者模式</p><p>• 工厂模式</p></div>',
    ]},
]

const curIdx = ref(0)
const flipRef = ref(null)
const cur = computed(() => books[curIdx.value])
let pf = null

function buildPages() {
  return books[curIdx.value].pages.map(html => {
    const div = document.createElement('div')
    div.style.cssText = 'width:360px;height:440px;overflow:hidden;backface-visibility:hidden'
    div.innerHTML = '<div style="width:100%;height:100%;padding:48px 20px 20px 24px;background:#F5F0E0;box-sizing:border-box;overflow-y:auto">' + html + '</div>'
    return div
  })
}

function init() {
  if (!flipRef.value) return
  if (pf) { pf.destroy(); pf = null }
  const el = flipRef.value
  el.innerHTML = ''
  const pages = buildPages()
  pages.forEach(p => el.appendChild(p))
  pf = new PageFlip(el, { width:360, height:440, flippingTime:600, drawShadow:true })
  pf.loadFromHTML(el.querySelectorAll(':scope > div'))
}

function switchBook(i) {
  curIdx.value = i
  if (pf) { pf.destroy(); pf = null }
  nextTick(() => init())
}

onMounted(() => nextTick(init))
onUnmounted(() => { if (pf) pf.destroy() })
</script>

<style scoped>
.notes-view{flex:1;display:flex;flex-direction:column;min-height:0}
.desk{
  flex:1;min-height:0;
  background:linear-gradient(160deg,#2A1610,#3D2015 25%,#2C1810 50%,#1A0F0A 75%,#2A1610);
  border-radius:12px;position:relative;overflow:hidden;
}
.desk::before{
  content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 4px,rgba(0,0,0,0.04) 4px,rgba(0,0,0,0.04) 5px);
  pointer-events:none;z-index:1;
}
.file-rack{position:absolute;top:16px;right:20px;z-index:20;width:168px}
.rack-body{background:linear-gradient(160deg,#6B4C2A,#4A2E16 60%,#3D2317);border-radius:3px;padding:3px 4px 5px;box-shadow:0 4px 16px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.06)}
.rack-top{text-align:center;font-size:8px;color:#B8956A;letter-spacing:2px;font-weight:700;padding:2px 0 3px}
.rack-inner{display:flex;gap:2px}
.nb-spine{flex:1;cursor:pointer;transition:all .2s;border-radius:1px 1px 0 0;height:72px;display:flex;align-items:center;justify-content:center}
.nb-spine:hover{transform:translateY(-3px);filter:brightness(1.15)}
.nb-spine.active{box-shadow:0 0 0 2px #F1C40F,0 3px 8px rgba(241,196,15,0.3)}
.nb-spine-label{writing-mode:vertical-rl;font-size:7px;color:rgba(255,255,255,0.85);letter-spacing:1.5px;font-weight:600}

.book-wrap{position:absolute;top:55%;left:50%;transform:translate(-50%,-50%);z-index:5}
.book-shadow{position:absolute;left:-40px;right:-40px;bottom:-25px;height:50px;background:radial-gradient(ellipse at center,rgba(0,0,0,0.35) 0%,transparent 70%)}
.book-outer{position:relative;width:720px;height:460px;transform:perspective(1200px) rotateX(2deg)}
.cover-shell{position:absolute;inset:-10px;z-index:0;border-radius:4px;overflow:hidden;box-shadow:0 0 12px rgba(0,0,0,0.2)}
.cover-half-l,.cover-half-r{position:absolute;top:0;bottom:0;width:369px}
.cover-half-l{left:0}.cover-half-r{right:0}
.cover-half-l::after,.cover-half-r::after{content:'';position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent,transparent 8px,rgba(0,0,0,0.02) 8px,rgba(0,0,0,0.02) 9px);border-radius:inherit}
.book-thick{position:absolute;bottom:-16px;left:-12px;right:-12px;height:16px;background:linear-gradient(180deg,#7B241C,#5C1A14);border-radius:0 0 4px 4px;z-index:-1}
.book-thick::before{content:'';position:absolute;top:0;left:6px;right:6px;height:4px;background:linear-gradient(180deg,#EDE6D0,#D4C9A8)}
.bookmark{position:absolute;left:50%;transform:translateX(-50%);bottom:-24px;width:16px;height:28px;z-index:6;border-radius:0 0 2px 2px;box-shadow:0 2px 4px rgba(0,0,0,0.2)}
.bookmark::after{content:'';position:absolute;bottom:0;left:0;right:0;height:6px;background:#7B241C;clip-path:polygon(0 0,50% 100%,100% 0)}

.book-inner{position:absolute;left:0;top:0;width:720px;height:460px;z-index:3;background:#F5F0E0}
/* 装订线 */
.book-inner::before{
  content:'';position:absolute;left:50%;top:0;bottom:0;
  width:6px;transform:translateX(-50%);
  z-index:50;pointer-events:none;
  background:linear-gradient(90deg,rgba(180,165,130,0.18),rgba(200,185,150,0.08) 30%,rgba(180,165,130,0.15) 50%,rgba(200,185,150,0.08) 70%,rgba(180,165,130,0.18));
  box-shadow:
    -6px 0 8px -4px rgba(0,0,0,0.06),
    6px 0 8px -4px rgba(0,0,0,0.06),
    inset 0 0 2px rgba(0,0,0,0.04);
}

.toc-title{font-size:15px;font-weight:700;color:#5D4E37;text-align:center;letter-spacing:8px;margin-bottom:4px}
.toc-line{width:60px;height:1.5px;background:#C4A97D;margin:0 auto 16px}
.toc-row{padding:5px 6px;font-size:12px;color:#5D4E37;display:flex;align-items:center;gap:6px}.toc-row:hover{background:rgba(108,92,231,0.08);border-radius:4px}
.n01{width:20px;font-size:11px;font-weight:600;color:#8B7355;font-family:Georgia,serif}.tt{font-size:14px;font-weight:700;color:#5D4E37;margin-bottom:4px}
.nb{font-size:12px;color:#5D4E37;line-height:22px}.nb p{margin:0}
</style>

<style>
.light-theme .notes-view .desk{
  background:linear-gradient(160deg,#D4C4A8,#C4B498 25%,#D4C4A8 50%,#C9BAA0 75%,#D4C4A8) !important;
}
</style>