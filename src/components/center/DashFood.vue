<template>
  <div class="food-card" @click.stop>
    <div class="food-head">
      <span class="food-title" @click="toggleMode" title="点击切换">
        {{ currentTitle }}
        <svg class="food-toggle-icon" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
      </span>
      <button class="food-edit" @click.stop="showEditor = true" title="编辑菜单">✏️</button>
    </div>

    <div class="food-bg-deco">
      <span v-for="(d,i) in decoList" :key="i" class="food-bg-item"
        :style="{ left: d.x+'%', top: d.y+'%', fontSize: d.size+'px', opacity: d.opacity, transform: 'rotate('+d.rot+'deg)' }"
      >{{ d.icon }}</span>
    </div>

    <div class="food-floats">
      <span v-for="f in floats" :key="f.id" class="food-float"
        :style="{ left: f.x+'%', top: f.y+'%', fontSize: f.size+'px', color: f.color, animationDelay: f.delay+'s' }"
      >{{ f.text }}</span>
    </div>

    <div class="food-body">
      <div v-if="!spinning && displayText === '🤔'" class="food-icon">🤔</div>
      <div v-else-if="!spinning" class="food-done">
        <span class="food-deco food-deco-l">✦</span>
        <span class="food-result">{{ displayText }}</span>
        <span class="food-deco food-deco-r">✦</span>
      </div>
      <div v-else class="food-spin">{{ displayText }}</div>
    </div>

    <div class="food-foot">
      <button class="food-btn" :class="{ spin: spinning }" @click="spin">
        <svg v-if="!spinning" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1.5"/></svg>
        <span>{{ spinning ? '停下' : '转一下' }}</span>
      </button>
    </div>

    <!-- 编辑弹窗 -->
    <Teleport to="body">
      <div v-if="showEditor" class="food-modal" @click.self="showEditor = false">
        <div class="food-dialog">
          <div class="food-dialog-hd">
            <span>自定义菜单</span>
            <button class="food-dlg-close" @click="showEditor=false">✕</button>
          </div>

          <!-- 已有菜单列表 -->
          <div class="fm-sections">
            <div v-for="(items, title) in editMenus" :key="title" class="fm-section">
              <div class="fm-section-hd">
                <span class="fm-title">{{ title }}</span>
                <button class="fm-del-btn" @click="removeMenu(title)" title="删除此菜单">✕</button>
              </div>
              <div class="fm-tags">
                <span v-for="(it, i) in items" :key="i" class="fm-tag">{{ it }}<button class="fm-tag-del" @click="removeItem(title, i)">✕</button></span>
              </div>
              <div class="fm-add-row">
                <input v-model="editInputs[title]" class="fm-input" placeholder="输入词条，空格分隔多个" @keydown.enter="addItems(title)" />
                <button class="fm-add-btn" @click="addItems(title)">+</button>
              </div>
            </div>
          </div>

          <!-- 新增菜单 -->
          <div class="fm-new">
            <input v-model="newMenuTitle" class="fm-input" placeholder="新菜单标题，如：今天看什么？" @keydown.enter="addMenu" />
            <button class="fm-add-btn" @click="addMenu" :disabled="!newMenuTitle.trim()">新建</button>
          </div>

          <button class="fm-reset" @click="resetAll">恢复默认</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onUnmounted } from 'vue'
import { getMenus, saveMenus } from '@/api/menu'
import { useUserStore } from '@/stores/user'

const COLORS = ['#FF6B6B','#FDCB6E','#6C5CE7','#00CEC9','#FF9FF3','#54A0FF']

const DECOS = [
  {icon:'⭐',x:5,y:8,size:14,opacity:0.12,rot:-15},
  {icon:'🎯',x:82,y:10,size:16,opacity:0.1,rot:10},
  {icon:'🌈',x:78,y:72,size:15,opacity:0.1,rot:25},
  {icon:'🎨',x:8,y:65,size:14,opacity:0.08,rot:-20},
  {icon:'💡',x:50,y:5,size:12,opacity:0.08,rot:45},
  {icon:'🎵',x:45,y:78,size:13,opacity:0.1,rot:-10},
  {icon:'🌍',x:85,y:50,size:11,opacity:0.07,rot:30},
  {icon:'📌',x:15,y:45,size:12,opacity:0.09,rot:-5},
  {icon:'✨',x:60,y:85,size:10,opacity:0.1,rot:60},
  {icon:'🎲',x:30,y:15,size:11,opacity:0.08,rot:-30},
]

const DEFAULT_MENUS = {
  '今天吃什么？': ['麻辣烫','麻辣香锅','饺子','炸鸡','汉堡','螺蛳粉','米线','炒饭','盖浇饭','黄焖鸡','重庆小面','兰州拉面','热干面','凉皮','肉夹馍','煎饼果子','寿司','烤肉饭','煲仔饭','酸菜鱼','水煮鱼','火锅','串串香','冒菜','刀削面','馄饨','小笼包','生煎','肠粉','三明治','意面','披萨','咖喱饭','卤肉饭','牛肉面'],
  '今天喝什么？': ['蜜雪冰城','瑞幸咖啡','星巴克','喜茶','奈雪的茶','古茗','茶百道','一点点','CoCo都可','益禾堂','书亦烧仙草','沪上阿姨','霸王茶姬','茶颜悦色','柠檬水','珍珠奶茶','生椰拿铁','美式','拿铁','卡布奇诺','摩卡','杨枝甘露','多肉葡萄','芝士莓莓','芋泥波波','冰美式','燕麦拿铁'],
}

const userStore = useUserStore()
const menus = ref({...DEFAULT_MENUS})
const titleKeys = ref(Object.keys(DEFAULT_MENUS))
const activeIdx = ref(0)
const displayText = ref('🤔')
const spinning = ref(false)
const showEditor = ref(false)
const newMenuTitle = ref('')
const editInputs = reactive({})
const floats = ref([])
let timer=null,floatTimer=null,floatId=0

onUnmounted(() => { clearInterval(timer); clearInterval(floatTimer) })

const currentTitle = computed(() => titleKeys.value[activeIdx.value] || '今天吃什么？')
const currentList = computed(() => menus.value[currentTitle.value] || [])
const decoList = computed(() => DECOS)
const editMenus = computed(() => menus.value)

// 加载
async function load() {
  try {
    const r = await getMenus()
    if (r.data?.menus && Object.keys(r.data.menus).length > 0) {
      menus.value = r.data.menus
      titleKeys.value = Object.keys(r.data.menus)
      // 初始化编辑输入
      Object.keys(r.data.menus).forEach(k => { editInputs[k] = '' })
    } else {
      initDefault()
    }
  } catch { initDefault() }
}
function initDefault() {
  menus.value = {...DEFAULT_MENUS}
  titleKeys.value = Object.keys(DEFAULT_MENUS)
  Object.keys(DEFAULT_MENUS).forEach(k => { editInputs[k] = '' })
}
load()

function toggleMode() {
  if (spinning.value) return
  activeIdx.value = (activeIdx.value + 1) % titleKeys.value.length
  displayText.value = '🤔'
  floats.value = []
}

function spin() {
  if (!currentList.value.length) return
  if (spinning.value) { stopSpin(); return }
  spinning.value=true;displayText.value='🎰';floats.value=[]
  timer=setInterval(()=>{displayText.value=currentList.value[Math.floor(Math.random()*currentList.value.length)]},70)
  floatTimer=setInterval(()=>{const item=currentList.value[Math.floor(Math.random()*currentList.value.length)];floatId++;floats.value.push({id:floatId,text:item,x:Math.random()*85+5,y:Math.random()*70+5,size:Math.random()*6+8,color:COLORS[Math.floor(Math.random()*COLORS.length)],delay:Math.random()*0.3});if(floats.value.length>25)floats.value.shift()},80)
}
function stopSpin() {
  clearInterval(timer);clearInterval(floatTimer)
  const pick=currentList.value[Math.floor(Math.random()*currentList.value.length)]
  displayText.value='👉 '+pick+' 👈';spinning.value=false
  setTimeout(()=>{floats.value=[]},600)
}

// 编辑操作
function addItems(title) {
  const raw = editInputs[title]?.trim()
  if (!raw) return
  const items = raw.split(/[\s,，、]+/).filter(Boolean)
  if (!items.length) return
  const set = new Set(menus.value[title] || [])
  items.forEach(i => set.add(i))
  menus.value[title] = [...set]
  editInputs[title] = ''
  saveAll()
}
function removeItem(title, i) {
  menus.value[title].splice(i, 1)
  if (!menus.value[title].length) delete menus.value[title]
  saveAll()
}
function addMenu() {
  const t = newMenuTitle.value.trim()
  if (!t || menus.value[t]) return
  menus.value[t] = []
  titleKeys.value = Object.keys(menus.value)
  editInputs[t] = ''
  newMenuTitle.value = ''
  saveAll()
}
function removeMenu(title) {
  if (!confirm(`删除「${title}」？`)) return
  delete menus.value[title]
  titleKeys.value = Object.keys(menus.value)
  if (activeIdx.value >= titleKeys.value.length) activeIdx.value = Math.max(0, titleKeys.value.length - 1)
  displayText.value = '🤔'
  saveAll()
}
function resetAll() {
  if (!confirm('恢复默认将丢弃所有自定义菜单')) return
  menus.value = {...DEFAULT_MENUS}
  titleKeys.value = Object.keys(DEFAULT_MENUS)
  activeIdx.value = 0
  Object.keys(DEFAULT_MENUS).forEach(k => { editInputs[k] = '' })
  displayText.value = '🤔'
  saveAll()
}
function saveAll() { saveMenus(menus.value) }
</script>

<style scoped>
.food-card{height:100%;display:flex;flex-direction:column;cursor:default;position:relative;overflow:hidden;background:radial-gradient(ellipse at 80% 20%,color-mix(in srgb,#FDCB6E 12%,transparent) 0%,transparent 50%),radial-gradient(ellipse at 20% 80%,color-mix(in srgb,#6C5CE7 8%,transparent) 0%,transparent 50%),color-mix(in srgb,var(--bg-card) 65%,transparent);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.food-head{display:flex;align-items:center;justify-content:space-between;padding:10px 12px 0;z-index:2;position:relative}
.food-title{font-size:14px;font-weight:700;color:var(--text);cursor:pointer;display:flex;align-items:center;gap:3px;user-select:none}
.food-title:hover{color:var(--primary)}
.food-toggle-icon{transition:transform 0.2s;color:var(--text3)}
.food-title:hover .food-toggle-icon{color:var(--primary)}
.food-edit{background:none;border:none;font-size:12px;cursor:pointer;opacity:0;transition:opacity 0.15s;padding:2px;line-height:1}
.food-card:hover .food-edit{opacity:0.3}
.food-card:hover .food-edit:hover{opacity:1}
.food-bg-deco{position:absolute;inset:0;z-index:0;pointer-events:none}
.food-bg-item{position:absolute;pointer-events:none;user-select:none}
.food-floats{position:absolute;inset:0;z-index:1;pointer-events:none;overflow:hidden}
.food-float{position:absolute;white-space:nowrap;font-weight:600;opacity:0;animation:float-up 1.3s ease-out forwards;pointer-events:none}
@keyframes float-up{0%{opacity:0.8;transform:translateY(0)scale(0.7)}50%{opacity:0.5;transform:translateY(-20px)scale(1.15)}100%{opacity:0;transform:translateY(-45px)scale(0.5)}}
.food-body{flex:1;display:flex;align-items:center;justify-content:center;z-index:2;position:relative;min-height:0}
.food-icon{font-size:30px;line-height:1;filter:grayscale(0.2)}
.food-done{display:flex;align-items:center;justify-content:center;gap:4px;width:100%;padding:0 8px}
.food-deco{font-size:11px;color:var(--accent);opacity:0.5;flex-shrink:0;animation:deco-spin 2s linear infinite}
.food-deco-r{animation-direction:reverse}
@keyframes deco-spin{0%{transform:rotate(0deg)scale(1)}50%{transform:rotate(180deg)scale(1.2)}100%{transform:rotate(360deg)scale(1)}}
.food-result{font-size:15px;font-weight:800;color:var(--text);text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0;animation:pop-in 0.3s ease-out}
@keyframes pop-in{0%{transform:scale(0.3);opacity:0}70%{transform:scale(1.15)}100%{transform:scale(1);opacity:1}}
.food-spin{font-size:16px;font-weight:800;color:var(--text);text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0 10px;max-width:100%;animation:bounce 0.07s infinite;letter-spacing:1px}
@keyframes bounce{0%,100%{transform:scale(1)translateY(0)}50%{transform:scale(1.1)translateY(-2px)}}
.food-foot{display:flex;justify-content:center;padding:0 0 8px;z-index:2;position:relative}
.food-btn{display:flex;align-items:center;justify-content:center;gap:5px;padding:3px 14px;height:24px;background:var(--primary);border:none;border-radius:6px;color:white;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.15s;opacity:0.85;letter-spacing:0.5px}
.food-btn:hover{opacity:1;background:color-mix(in srgb,var(--primary) 85%,white)}
.food-btn:active{transform:scale(0.95)}
.food-btn.spin{background:var(--danger);opacity:1}
.food-btn svg{width:11px;height:11px;flex-shrink:0}

/* 编辑弹窗 */
.food-modal{position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.5);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center}
.food-dialog{width:380px;max-width:90vw;max-height:70vh;background:var(--bg-modal);border:1px solid var(--border);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:12px}
.food-dialog-hd{display:flex;align-items:center;justify-content:space-between;font-size:15px;font-weight:700;color:var(--text)}
.food-dlg-close{width:26px;height:26px;background:var(--bg-glass);border:none;border-radius:6px;color:var(--text2);cursor:pointer;font-size:12px}
.fm-sections{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
.fm-section{border:1px solid var(--border);border-radius:10px;padding:10px}
.fm-section-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.fm-title{font-size:13px;font-weight:700;color:var(--text)}
.fm-del-btn{width:18px;height:18px;background:none;border:none;color:var(--text3);cursor:pointer;font-size:10px;border-radius:4px}
.fm-del-btn:hover{background:rgba(255,80,80,0.15);color:#ff5050}
.fm-tags{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px;max-height:80px;overflow-y:auto}
.fm-tag{display:inline-flex;align-items:center;gap:2px;padding:3px 7px;background:color-mix(in srgb,var(--primary) 10%,transparent);border-radius:5px;font-size:11px;color:var(--text2)}
.fm-tag-del{width:13px;height:13px;display:inline-flex;align-items:center;justify-content:center;background:none;border:none;color:var(--text3);cursor:pointer;font-size:7px;border-radius:50%;padding:0}
.fm-tag-del:hover{background:rgba(255,80,80,0.2);color:#ff5050}
.fm-add-row{display:flex;gap:4px}
.fm-input{flex:1;padding:5px 8px;font-size:11px;border:1px solid var(--border);border-radius:6px;background:var(--bg-input);color:var(--text);outline:none}
.fm-input:focus{border-color:var(--primary)}
.fm-add-btn{padding:5px 10px;font-size:12px;font-weight:700;background:var(--primary);border:none;border-radius:6px;color:white;cursor:pointer;flex-shrink:0}
.fm-add-btn:disabled{opacity:0.4;cursor:default}
.fm-new{display:flex;gap:6px}
.fm-reset{align-self:center;font-size:10px;color:var(--text3);background:none;border:none;cursor:pointer;padding:4px 8px}
.fm-reset:hover{color:var(--danger)}
</style>
