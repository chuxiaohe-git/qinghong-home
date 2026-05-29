<template>
  <div class="game-card" ref="cardRef" @contextmenu.prevent>
    <div id="geScene">
      <div id="geBgLayer"></div>
      <div id="geBossLayer">
        <img id="geBossImg" alt="boss" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" />
        <div id="geNameplate">老板</div>
      </div>
      <div id="geGloveLayer">
        <div class="geGlove" id="geGloveL"><img alt="拳套" /></div>
        <div class="geGlove" id="geGloveR"><img alt="拳套" /></div>
      </div>
    </div>
    <canvas id="geFx"></canvas>
    <div id="geUi">
      <div>
        <div class="ge-name-wrap">
          <div class="ge-name-arrow">▶</div>
          <input id="geNameInput" type="text" placeholder="输入名字" maxlength="5" value="老板" />
        </div>
        <div class="ge-char-arrow" @click.stop="togglePicker">▽</div>
      </div>
      <div id="geHitDisplay">💢 0</div>
    </div>

    <Teleport to="body">
      <div v-if="showCharPicker" class="ge-char-picker" @click.stop
           :style="{ left: pickerLeft + 'px', top: pickerTop + 'px' }">
        <div class="ge-char-title">选择形象</div>
        <div class="ge-char-list">
          <div v-for="(set, key) in CHARACTER_SETS" :key="key" class="ge-char-item"
               :class="{ active: currentSet === key }" @click="selectSet(key)">
            <div class="ge-char-thumb"><img :src="set.thumb" /></div>
            <span class="ge-char-name">{{ set.name }}</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getSettings, updateSettings } from '@/api/settings'
const userStore = useUserStore()
const GAME_KEY = 'game_boss_' + (userStore.user?.username || 'default')
const cardRef = ref(null)

// ── 角色形象定义 ──
const CHARACTER_SETS = {
  default: { name: '原始形象', thumb: '/images/game/boss1.png', images: { b0: '/images/game/boss1.png', b1: '/images/game/boss3.png', b2: '/images/game/boss2.png', b3: '/images/game/boss4.png', b4: '/images/game/boss5.png' } },
  engineer: { name: '工科男', thumb: '/characters/engineer/boss1_cutout.png', images: { b0: '/characters/engineer/boss1_cutout.png', b1: '/characters/engineer/boss2_cutout.png', b2: '/characters/engineer/boss3_cutout.png', b3: '/characters/engineer/boss4_cutout.png', b4: '/characters/engineer/boss5_cutout.png' } },
  sleazy: { name: '猥琐男', thumb: '/characters/sleazy/sleazy1_cutout.png', images: { b0: '/characters/sleazy/sleazy1_cutout.png', b1: '/characters/sleazy/sleazy2_cutout.png', b2: '/characters/sleazy/sleazy3_cutout.png', b3: '/characters/sleazy/sleazy4_cutout.png', b4: '/characters/sleazy/sleazy5_cutout.png' } },
}

const showCharPicker = ref(false)
const currentSet = ref(localStorage.getItem('game_char_set') || 'default')
const pickerLeft = ref(16)
const pickerTop = ref(50)

function togglePicker() {
  if (!showCharPicker.value && cardRef.value) {
    const r = cardRef.value.getBoundingClientRect()
    pickerLeft.value = r.left
    pickerTop.value = r.top + 24
  }
  showCharPicker.value = !showCharPicker.value
}

// ── 角色切换：保存 → 刷新页面（最可靠） ──
function selectSet(key) {
  showCharPicker.value = false
  if (key === currentSet.value) return
  currentSet.value = key
  localStorage.setItem('game_char_set', key)
  getSettings().then(res => {
    try { const cfg = JSON.parse(res?.layout_config || '{}'); cfg.game_char_set = key; updateSettings({ layout_config: JSON.stringify(cfg) }) } catch {}
  }).catch(() => {})
  setTimeout(() => location.reload(), 80)
}

// ── 预处理的 dataURL（方便 update 循环使用） ──
let procd = { default: {}, engineer: {}, sleazy: {} }

function closePicker(e) {
  if (e && e.target && e.target.closest('.ge-char-picker, .ge-char-arrow')) return
  showCharPicker.value = false
}

function chromaKey(img) {
  const c = document.createElement('canvas')
  c.width = img.width; c.height = img.height
  const ctx = c.getContext('2d')
  ctx.drawImage(img, 0, 0)
  const d = ctx.getImageData(0, 0, c.width, c.height)
  for (let i = 0; i < d.data.length; i += 4) {
    const r = d.data[i], g = d.data[i + 1], b = d.data[i + 2]
    if (g > 50 && g > r * 1.15 && g > b * 1.15) d.data[i + 3] = 0
  }
  ctx.putImageData(d, 0, 0)
  return c
}
function toCanvas(img) {
  const c = document.createElement('canvas')
  c.width = img.width; c.height = img.height
  c.getContext('2d').drawImage(img, 0, 0)
  return c
}

let _rAF = null
let _audioCtx = null
const _listeners = []
const sfxPath = '/audio/sfx/sfx.mp3'
const screamPaths = ['/audio/sfx/scream1.mp3','/audio/sfx/scream2.mp3','/audio/sfx/scream3.mp3','/audio/sfx/scream5.mp3','/audio/sfx/scream6.mp3']

// 构建完整图片加载列表
const IMG = { bg: '/images/game/bg_new.png', gloveL: '/images/game/glove_left.png', gloveR: '/images/game/glove_left.png' }
for (const [setKey, set] of Object.entries(CHARACTER_SETS)) {
  for (const [bk, src] of Object.entries(set.images)) {
    IMG[setKey + '_' + bk] = src
  }
}
const TOTAL = Object.keys(IMG).length

// ── 游戏桥接 ref ──
const gameBridge = ref({ bossUrls: null, bossImg: null, currentKey: 'b0', bossEl: null })

onMounted(() => {
  const card = cardRef.value; if (!card) return
  const W = 264, H = 130
  const loaded = {}
  const keyedUrls = {}
  const bossUrls = {}
  let nReady = 0

  const bossEl = card.querySelector('#geBossLayer')
  const bossImg = card.querySelector('#geBossImg')
  const bgLayer = card.querySelector('#geBgLayer')
  const gloveL = card.querySelector('#geGloveL')
  const gloveR = card.querySelector('#geGloveR')
  const gloveImgL = gloveL.querySelector('img')
  const gloveImgR = gloveR.querySelector('img')
  const fxCanvas = card.querySelector('#geFx')
  const FXC = fxCanvas.getContext('2d')
  const hitEl = card.querySelector('#geHitDisplay')
  const nameplate = card.querySelector('#geNameplate')
  fxCanvas.width = W; fxCanvas.height = H

  gameBridge.value = { bossUrls, bossImg, currentKey: 'b0', bossEl }

  // ── 音效 ──
  let audioCtx = null
  function getAudio() { if (!audioCtx) { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); _audioCtx = audioCtx } return audioCtx }
  function playPunch() {
    try {
      const ctx = getAudio()
      const buf = ctx.createBuffer(1, ctx.sampleRate * 0.04, ctx.sampleRate)
      const d = buf.getChannelData(0)
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 6)
      const src = ctx.createBufferSource()
      src.buffer = buf
      const f = ctx.createBiquadFilter()
      f.type = 'lowpass'; f.frequency.value = 800
      const g = ctx.createGain()
      g.gain.setValueAtTime(0.08, ctx.currentTime)
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04)
      src.connect(f); f.connect(g); g.connect(ctx.destination)
      src.start()
    } catch (e) {}
  }
  function playHit() {
    try {
      const ctx = getAudio()
      const osc = ctx.createOscillator()
      osc.type = 'sine'; osc.frequency.setValueAtTime(80, ctx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(20, ctx.currentTime + 0.35)
      const g1 = ctx.createGain()
      g1.gain.setValueAtTime(0.7, ctx.currentTime)
      g1.gain.linearRampToValueAtTime(0.5, ctx.currentTime + 0.02)
      g1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4)
      osc.connect(g1); g1.connect(ctx.destination)
      osc.start(); osc.stop(ctx.currentTime + 0.4)
      const buf = ctx.createBuffer(1, ctx.sampleRate * 0.015, ctx.sampleRate)
      const nd = buf.getChannelData(0)
      for (let i = 0; i < nd.length; i++) nd[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / nd.length, 10)
      const src = ctx.createBufferSource()
      src.buffer = buf
      const f2 = ctx.createBiquadFilter()
      f2.type = 'highpass'; f2.frequency.value = 500
      const g2 = ctx.createGain()
      g2.gain.setValueAtTime(0.3, ctx.currentTime)
      g2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.02)
      src.connect(f2); f2.connect(g2); g2.connect(ctx.destination)
      src.start()
      const osc2 = ctx.createOscillator()
      osc2.type = 'triangle'; osc2.frequency.setValueAtTime(200, ctx.currentTime)
      osc2.frequency.exponentialRampToValueAtTime(60, ctx.currentTime + 0.15)
      const g3 = ctx.createGain()
      g3.gain.setValueAtTime(0.15, ctx.currentTime)
      g3.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2)
      osc2.connect(g3); g3.connect(ctx.destination)
      osc2.start(); osc2.stop(ctx.currentTime + 0.2)
      setTimeout(() => {
        try {
          if (!window.audioSfx) { window.audioSfx = new Audio(sfxPath); window.audioSfx.volume = 0.6 }
          window.audioSfx.currentTime = 0; window.audioSfx.play().catch(()=>{})
          const chosen = screamPaths[Math.floor(Math.random() * screamPaths.length)]
          if (!window._screamAudios) window._screamAudios = {}
          if (!window._screamAudios[chosen]) { window._screamAudios[chosen] = new Audio(chosen); window._screamAudios[chosen].volume = 0.5 }
          window._screamAudios[chosen].currentTime = 0; window._screamAudios[chosen].play().catch(()=>{})
        } catch (e) {}
      }, 30)
    } catch (e) {}
  }

  const S = { name: '老板', hits: 0, lastHitTime: 0, decayAcc: 0, anim: 'idle', aTime: 0, angle: 0, tiltZ: 0, offY: 0, gx: 0.5, tgx: 0.5, pL: 0, pR: 0, side: 'right', shake: 0, shock: 0 }
  try {
    const saved = localStorage.getItem(GAME_KEY)
    if (saved) { const p = JSON.parse(saved); if (p.hits > 0) S.hits = p.hits; if (p.name) { S.name = p.name; nameplate.textContent = p.name; const inp = document.getElementById('geNameInput'); if (inp) inp.value = p.name } }
  } catch {}
  // 恢复后立即刷新显示
  hitEl.textContent = `💢 ${S.hits}`
  getSettings().then(res => {
    try {
      const cfg = JSON.parse(res?.layout_config || '{}')
      if (cfg.game_name) { S.name = cfg.game_name; const inp = document.getElementById('geNameInput'); if (inp) inp.value = cfg.game_name; const nm = document.getElementById('geNameplate'); if (nm) nm.textContent = cfg.game_name }
    } catch {}
  }).catch(() => {})
  function saveGame() {
    try { localStorage.setItem(GAME_KEY, JSON.stringify({ hits: S.hits, name: S.name })) } catch {}
    try {
      getSettings().then(res => {
        const cfg = JSON.parse(res?.layout_config || '{}')
        cfg.game_hits = S.hits
        updateSettings({ layout_config: JSON.stringify(cfg) })
      }).catch(() => {})
    } catch {}
  }
  let currentBossKey = ''
  let lastAngle = -999, lastTiltZ = -999, lastGx = -999, lastLoy = -999, lastRoy = -999, lastLox = -999, lastRox = -999
  let lastT = 0

  function relX(e) { const r = card.getBoundingClientRect(); const x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left; return Math.max(0.05, Math.min(0.95, x / r.width)) }
  const onMouseMove = e => S.tgx = relX(e)
  const onMouseDown = e => { if (e.button === 0) punch('left'); if (e.button === 2) punch('right') }
  const onTouchMove = e => { e.preventDefault(); S.tgx = relX(e) }
  const onTouchStart = e => { e.preventDefault(); punch('left') }
  const onInput = e => { S.name = e.target.value || '老板'; nameplate.textContent = S.name; saveGame(); syncGameName() }
  card.addEventListener('mousemove', onMouseMove)
  card.addEventListener('mousedown', onMouseDown)
  card.addEventListener('touchmove', onTouchMove, { passive: false })
  card.addEventListener('touchstart', onTouchStart, { passive: false })
  const nameInput = card.querySelector('#geNameInput')
  nameInput.addEventListener('input', onInput)
  _listeners.push([card, 'mousemove', onMouseMove], [card, 'mousedown', onMouseDown], [card, 'touchmove', onTouchMove, { passive: false }], [card, 'touchstart', onTouchStart, { passive: false }], [nameInput, 'input', onInput])
  let nameSyncTimer = null
  function syncGameName() {
    clearTimeout(nameSyncTimer); nameSyncTimer = setTimeout(() => {
      getSettings().then(res => { try { const cfg = JSON.parse(res?.layout_config || '{}'); cfg.game_name = S.name; updateSettings({ layout_config: JSON.stringify(cfg) }) } catch {} }).catch(() => {})
    }, 500)
  }

  function punch(side) {
    if (side === 'left') S.pL = 0.01; else S.pR = 0.01
    S.side = side; S.hits++; S.decayAcc = 0; hitEl.textContent = `💢 ${S.hits}`; saveGame()
    S.shake = 6; S.shock = 1; playPunch(); setTimeout(playHit, 30)
    S.anim = 'hit'; S.aTime = 0; S.angle = 85; S.tiltZ = S.side === 'left' ? 12 : -12; S.offY = 0
  }
  function updateGloveImage() { if (keyedUrls.gloveL) gloveImgL.src = keyedUrls.gloveL; if (keyedUrls.gloveR) gloveImgR.src = keyedUrls.gloveR }
  function hook(p, dir) {
    if (p <= 0) return { x: 0, y: 0 }
    if (p < 0.4) { const t = p / 0.4; return { x: dir * 50 * Math.sin(t * Math.PI / 2), y: -65 * Math.sin(t * Math.PI / 2) } }
    else { const t = (p - 0.4) / 0.6; return { x: dir * 50 * (1 - t), y: -65 * (1 - t) } }
  }
  function update(dt) {
    S.gx += (S.tgx - S.gx) * 0.18
    const pl = 80
    if (S.pL > 0) { S.pL += dt / pl; if (S.pL >= 1) S.pL = 0 }
    if (S.pR > 0) { S.pR += dt / pl; if (S.pR >= 1) S.pR = 0 }
    if (S.shake > 0) { S.shake *= 0.88; if (S.shake < 0.5) S.shake = 0 }
    if (S.shock > 0) { S.shock -= dt / 200; if (S.shock < 0) S.shock = 0 }
    if (S.hits > 0) { S.decayAcc += dt; if (S.decayAcc >= 5000) { S.decayAcc = 0; if (S.hits > 0) S.hits--; hitEl.textContent = `💢 ${S.hits}`; saveGame() } }
    { let k = 'b0'; const h = S.hits; if (h >= 500) k = 'b4'; else if (h >= 301) k = 'b3'; else if (h >= 101) k = 'b2'; else if (h >= 1) k = 'b1'
      if (k !== currentBossKey) { currentBossKey = k; gameBridge.value.currentKey = k; const isPig = h >= 500; bossEl.classList.toggle('pig', isPig); if (bossUrls[k]) { document.querySelector('#geBossImg').src = bossUrls[k]; const el = document.querySelector('#geBossImg'); if (el && (bossEl.dataset.set === 'engineer' || bossEl.dataset.set === 'sleazy')) { el.classList.add('ge-boss-portrait') } else if (el) { el.classList.remove('ge-boss-portrait') } } } }
    if (S.anim === 'hit') {
      S.aTime += dt; const fall = 120, bounce = 550, total = fall + bounce
      if (S.aTime < fall) { const p = S.aTime / fall; S.angle = 85 * p * p }
      else if (S.aTime < total) { let p = (S.aTime - fall) / bounce; const n1 = 7.5625, d1 = 2.75; let bp
        if (p < 1 / d1) bp = n1 * p * p; else if (p < 2 / d1) bp = n1 * (p -= 1.5 / d1) * p + 0.75; else if (p < 2.5 / d1) bp = n1 * (p -= 2.25 / d1) * p + 0.9375; else bp = n1 * (p -= 2.625 / d1) * p + 0.984375
        S.angle = 85 * (1 - bp) }
      else { S.anim = 'idle'; S.angle = 0 }
      S.tiltZ *= 0.95; if (Math.abs(S.tiltZ) < 0.5) S.tiltZ = 0
    }
    if (S.angle !== lastAngle) { lastAngle = S.angle; bossEl.style.setProperty('--bx', S.angle + 'deg') }
    if (S.tiltZ !== lastTiltZ) { lastTiltZ = S.tiltZ; bossEl.style.setProperty('--bz', S.tiltZ + 'deg') }
    bossEl.style.setProperty('--by', S.offY + 'px')
    const gxp = S.gx * W
    if (gxp !== lastGx) { lastGx = gxp; card.style.setProperty('--gx', gxp + 'px') }
    const lh = hook(S.pL, 1), rh = hook(S.pR, -1)
    if (lh.y !== lastLoy) { lastLoy = lh.y; card.style.setProperty('--lo', lh.y + 'px') }
    if (rh.y !== lastRoy) { lastRoy = rh.y; card.style.setProperty('--ro', rh.y + 'px') }
    if (lh.x !== lastLox) { lastLox = lh.x; card.style.setProperty('--lx', lh.x + 'px') }
    if (rh.x !== lastRox) { lastRox = rh.x; card.style.setProperty('--rx', rh.x + 'px') }
  }
  function drawFX() {
    FXC.clearRect(0, 0, W, H)
    if (S.shock > 0 && S.anim === 'hit') {
      const t = Math.min(1, S.shock * 2); const cx = W / 2, cy = H * 0.28; const side = S.side === 'left' ? 1 : -1
      FXC.save(); FXC.globalAlpha = 1 - t * 0.4; const size = 18 + t * 18
      FXC.font = `${size}px sans-serif`; FXC.textAlign = 'center'; FXC.textBaseline = 'middle'
      FXC.fillText('💥', cx + side * 8, cy - t * 5); FXC.restore()
    }
  }
  function load() {
    for (const [k, src] of Object.entries(IMG)) {
      const i = new Image()
      i.onload = () => { loaded[k] = i; if (k === 'bg') bgLayer.style.backgroundImage = `url(${i.src})`; else keyedUrls[k] = i.src; nReady++; if (nReady === TOTAL) ready() }
      i.onerror = () => { nReady++; if (nReady === TOTAL) ready() }; i.src = src
    }
  }
  function ready() {
    for (const [setKey] of Object.entries(CHARACTER_SETS)) {
      const pUrls = procd[setKey]
      for (const bk of ['b0', 'b1', 'b2', 'b3', 'b4']) {
        const key = setKey + '_' + bk; const img = loaded[key]
        if (!img) continue
        pUrls[bk] = (setKey === 'engineer' ? chromaKey(img) : toCanvas(img)).toDataURL('image/png')
      }
    }
    const chosen = (procd[currentSet.value]?.b0) ? procd[currentSet.value] : procd.default
    Object.assign(bossUrls, chosen)
    if (chosen.b0) bossImg.src = chosen.b0
    bossEl.dataset.set = currentSet.value
    if (currentSet.value !== 'default') {
      bossImg.classList.add('ge-boss-portrait')
    } else {
      bossImg.classList.remove('ge-boss-portrait')
    }
    updateGloveImage(); _rAF = requestAnimationFrame(loop)
  }
  function loop(t) { const dt = lastT ? t - lastT : 16; lastT = t; update(Math.min(dt, 30)); drawFX(); _rAF = requestAnimationFrame(loop) }
  load()
})

onUnmounted(() => {
  cancelAnimationFrame(_rAF)
  if (_audioCtx) _audioCtx.close()
  for (const [el, evt, fn, opts] of _listeners) el.removeEventListener(evt, fn, opts || false)
  _listeners.length = 0
  document.removeEventListener('click', closePicker)
})

onMounted(() => { setTimeout(() => document.addEventListener('click', closePicker), 0) })
</script>

<style scoped>
.game-card { height:100%; position:relative; overflow:hidden; border-radius:12px; cursor:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="8" fill="none" stroke="white" stroke-width="1.5"/><circle cx="12" cy="12" r="2" fill="white"/></svg>') 12 12, crosshair; }
#geScene { position:absolute; inset:0; perspective:300px; perspective-origin:50% 100%; }
#geBgLayer { position:absolute; inset:0; background-size:cover; background-position:center; }
#geBossLayer { position:absolute; bottom:0; left:50%; transform-origin:50% 100%; transform:translateX(-50%) perspective(300px) rotateX(var(--bx,0deg)) rotateZ(var(--bz,0deg)) translateY(var(--by,0px)); will-change:transform; }
#geBossLayer img { display:block; }
#geBossLayer[data-set="default"] img { width:260px; height:auto; max-height:145px; }
#geBossLayer.pig[data-set="default"] img { width:210px; }
.ge-boss-portrait { width:auto; display:block; }
#geBossLayer[data-set="engineer"] img { height:280px !important; margin-top:-55px !important; }
#geBossLayer[data-set="sleazy"] img { height:220px !important; margin-top:-30px !important; }
#geBossLayer[data-set="engineer"] { bottom:auto !important; top:0 !important; }
#geBossLayer[data-set="sleazy"] { bottom:auto !important; top:0 !important; }
#geBossLayer.pig #geNameplate { bottom:14%; }
#geBossLayer[data-set="engineer"] #geNameplate { bottom:auto; top:112px; }
#geBossLayer[data-set="sleazy"] #geNameplate { bottom:auto; top:112px; }
#geBossLayer.pig[data-set="engineer"] #geNameplate { bottom:auto; top:110px; }
#geBossLayer.pig[data-set="sleazy"] #geNameplate { bottom:auto; top:110px; }
#geNameplate { position:absolute; bottom:24%; left:50%; transform:translateX(calc(-50% - 2px)); font:bold 18px/1 'Press Start 2P','Courier New',monospace; color:#222; text-align:center; white-space:nowrap; text-shadow:0 0 3px rgba(255,255,255,0.8); pointer-events:none; z-index:3; }
#geGloveLayer { position:absolute; bottom:0; left:0; right:0; height:100%; pointer-events:none; }
.geGlove { position:absolute; bottom:-20px; width:100px; will-change:transform; }
.geGlove img { display:block; width:100%; height:auto; }
.geGlove#geGloveL { left:calc(var(--gx) - 130px); transform:translate(var(--lx,0px),var(--lo,0px)); }
.geGlove#geGloveR { left:calc(var(--gx) + 30px); transform:translate(var(--rx,0px),var(--ro,0px)) scaleX(-1); }
#geFx { position:absolute; top:0; left:0; width:100%; height:100%; z-index:5; pointer-events:none; }
#geUi { position:absolute; top:4px; left:6px; right:6px; z-index:20; display:flex; justify-content:space-between; align-items:flex-start; pointer-events:none; }
#geUi > * { pointer-events:auto; }
.ge-ui-left { display:flex; flex-direction:column; gap:2px; align-items:flex-start; }
.ge-name-wrap { display:flex; align-items:center; gap:4px; cursor:default; position:relative; }
.ge-name-arrow { font-size:8px; color:rgba(255,255,255,0.3); width:14px; height:14px; flex-shrink:0; display:flex; align-items:center; justify-content:center; border-radius:4px; background:rgba(0,0,0,0.2); transition:all .2s; cursor:pointer; }
.ge-name-wrap:hover .ge-name-arrow { color:rgba(255,255,255,0.7); background:rgba(0,0,0,0.4); }
.ge-char-arrow { font-size:8px; color:rgba(255,255,255,0.3); width:14px; height:14px; flex-shrink:0; display:flex; align-items:center; justify-content:center; border-radius:4px; background:rgba(0,0,0,0.2); transition:all .2s; cursor:pointer; margin-left:0; }
.ge-char-arrow:hover { color:rgba(255,255,255,0.7); background:rgba(0,0,0,0.4); }
.ge-char-picker { position:fixed; left:16px; top:50px; z-index:9999; background:var(--bg-menu); border:1px solid var(--border); border-radius:10px; padding:6px; box-shadow:0 6px 24px rgba(0,0,0,.4); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); min-width:120px; }
.ge-char-title { font-size:11px; font-weight:600; color:var(--text); margin-bottom:4px; padding-left:4px; }
.ge-char-list { display:flex; flex-direction:column; gap:4px; }
.ge-char-item { display:flex; align-items:center; gap:6px; padding:4px 6px; border-radius:6px; cursor:pointer; transition:all .15s; }
.ge-char-item:hover { background:var(--bg-glass); }
.ge-char-item.active { background:var(--primary-light); outline:1px solid var(--primary); }
.ge-char-thumb { width:32px; height:32px; border-radius:5px; overflow:hidden; flex-shrink:0; background:var(--bg-glass); }
.ge-char-thumb img { width:100%; height:100%; object-fit:cover; }
.ge-char-name { font-size:11px; font-weight:500; color:var(--text2); }
.ge-char-item.active .ge-char-name { color:var(--primary); font-weight:600; }
#geNameInput { padding:3px 8px; border:1px solid rgba(255,255,255,.25); border-radius:8px; background:rgba(0,0,0,.4); backdrop-filter:blur(4px); color:#fff; font-size:12px; width:0; min-width:0; text-align:center; outline:none; transition:width .25s ease,padding .25s ease,border-color .2s; border-color:transparent; padding-left:0; padding-right:0; cursor:pointer; }
.ge-name-wrap:hover #geNameInput, #geNameInput:focus { width:72px; border-color:rgba(255,255,255,.25); padding:3px 8px; cursor:text; }
#geNameInput::placeholder { color:rgba(255,255,255,.4); }
#geHitDisplay { font-size:13px; font-weight:bold; color:#ff6b6b; text-shadow:0 1px 3px rgba(0,0,0,.7); background:rgba(0,0,0,.3); padding:3px 10px; border-radius:8px; backdrop-filter:blur(3px); }
</style>
