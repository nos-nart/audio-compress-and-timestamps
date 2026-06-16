<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{ src: string; duration?: number }>()
const emit = defineEmits<{ timeupdate: [time: number] }>()

const audioRef = ref<HTMLAudioElement | null>(null)
const sliderRef = ref<HTMLInputElement | null>(null)
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const hoverTime = ref(0)
const hoverPct = ref(0)
const showTooltip = ref(false)
let rafId = 0

function getDuration(): number {
  if (props.duration && props.duration > 0) return props.duration
  if (!audioRef.value) return 0
  const d = audioRef.value.duration
  if (d && isFinite(d) && d > 0) return d
  const s = audioRef.value.seekable
  if (s && s.length > 0) {
    const end = s.end(s.length - 1)
    if (end > 0 && isFinite(end)) return end
  }
  const b = audioRef.value.buffered
  if (b && b.length > 0) {
    const end = b.end(b.length - 1)
    if (isFinite(end) && end > 0) return end
  }
  return 0
}

function tick() {
  if (!audioRef.value) return
  currentTime.value = audioRef.value.currentTime
  const d = getDuration()
  if (d > 0 && d !== duration.value) {
    duration.value = d
  }
  emit('timeupdate', currentTime.value)
  if (!audioRef.value.paused) {
    rafId = requestAnimationFrame(tick)
  }
}

function onTimeUpdate() {
  if (!audioRef.value) return
  currentTime.value = audioRef.value.currentTime
  const d = getDuration()
  if (d > 0 && d !== duration.value) {
    duration.value = d
  }
  emit('timeupdate', currentTime.value)
}


function onPlay() {
  playing.value = true
  cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(tick)
}

function onPause() {
  playing.value = false
  cancelAnimationFrame(rafId)
}

function onEnded() {
  playing.value = false
  cancelAnimationFrame(rafId)
}

async function togglePlay() {
  if (!audioRef.value) return
  if (playing.value) {
    audioRef.value.pause()
  } else {
    try {
      await audioRef.value.play()
    } catch {}
  }
}

function onSeek(e: Event) {
  const target = e.target as HTMLInputElement
  const t = parseFloat(target.value)
  if (audioRef.value) {
    audioRef.value.currentTime = t
  }
  currentTime.value = t
  emit('timeupdate', t)
}

function seek(time: number) {
  if (audioRef.value) {
    audioRef.value.currentTime = time
  }
  currentTime.value = time
  emit('timeupdate', time)
}

watch(() => props.src, () => {
  playing.value = false
  currentTime.value = 0
  duration.value = 0
  cancelAnimationFrame(rafId)
})

function onSliderHover(e: MouseEvent) {
  if (!sliderRef.value || duration.value === 0) return
  const rect = sliderRef.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
  const pct = x / rect.width
  hoverPct.value = pct
  hoverTime.value = pct * duration.value
  showTooltip.value = true
}

function onSliderLeave() {
  showTooltip.value = false
}

function formatTime(sec: number): string {
  if (!isFinite(sec) || isNaN(sec)) return '--:--'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onDurationChange() {
  const d = getDuration()
  if (d > 0) {
    duration.value = d
  }
}

defineExpose({ seek })

onMounted(() => {
  rafId = requestAnimationFrame(tick)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
})
</script>

<template>
  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 shadow-sm">
    <audio
      ref="audioRef"
      :src="src"
      preload="auto"
      @loadedmetadata="onDurationChange()"
      @durationchange="onDurationChange"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      @pause="onPause"
      @play="onPlay"
    />

    <div class="flex items-center gap-3">
      <button
        @click="togglePlay"
        class="w-10 h-10 rounded-lg bg-emerald-600 hover:bg-emerald-500 flex items-center justify-center shrink-0 transition-colors cursor-pointer"
      >
        <span v-if="playing" class="text-sm text-white">&#9646;&#9646;</span>
        <span v-else class="text-sm text-white ml-0.5">&#9654;</span>
      </button>

      <div class="flex-1 relative pt-2 pb-1 group" @mousemove="onSliderHover" @mouseleave="onSliderLeave">
        <div
          v-if="showTooltip && duration > 0"
          class="absolute -top-1 z-10 px-2 py-0.5 rounded bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 text-xs font-medium pointer-events-none whitespace-nowrap"
          :style="{ left: `calc(${hoverPct * 100}% - 16px)` }"
        >
          {{ formatTime(hoverTime) }}
        </div>
        <input
          ref="sliderRef"
          type="range"
          :min="0"
          :max="duration"
          :value="currentTime"
          @input="onSeek"
          class="block w-full h-2 rounded-full appearance-none cursor-pointer bg-gray-200 dark:bg-gray-700 accent-emerald-500 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-emerald-600 [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white dark:[&::-webkit-slider-thumb]:border-gray-900 [&::-webkit-slider-thumb]:shadow-sm"
        />
      </div>

      <span class="text-xs tabular-nums text-gray-500 dark:text-gray-400 w-16 text-right font-medium shrink-0">
        {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
      </span>
    </div>
  </div>
</template>
