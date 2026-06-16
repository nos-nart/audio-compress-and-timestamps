<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AudioPlayer from './components/AudioPlayer.vue'
import TranscriptViewer from './components/TranscriptViewer.vue'

interface Word {
  start: number
  end: number
  word: string
}

interface Segment {
  start: number
  end: number
  text: string
  words: Word[]
}

interface Transcription {
  file: string
  duration_sec: number
  segments: Segment[]
}

const recordings = ref<string[]>([])
const selected = ref('')
const audioUrl = ref('')
const transcription = ref<Transcription | null>(null)
const currentTime = ref(0)
const playerRef = ref<any>(null)
const loading = ref(false)
const error = ref('')
const dark = ref(true)

function applyTheme(isDark: boolean) {
  document.documentElement.classList.toggle('dark', isDark)
  dark.value = isDark
  localStorage.setItem('theme', isDark ? 'dark' : 'light')
}

function toggleTheme() {
  const next = !dark.value
  if (!document.startViewTransition) {
    applyTheme(next)
    return
  }
  document.startViewTransition(() => applyTheme(next))
}

onMounted(async () => {
  const stored = localStorage.getItem('theme')
  if (stored === 'light') {
    applyTheme(false)
  } else if (stored === 'dark') {
    applyTheme(true)
  } else {
    applyTheme(window.matchMedia('(prefers-color-scheme: dark)').matches)
  }

  try {
    const res = await fetch('/api/list-recordings')
    recordings.value = await res.json()
    if (recordings.value.length > 0) {
      selectRecording(recordings.value[0])
    }
  } catch {
    error.value = 'Failed to list recordings'
  }
})

async function selectRecording(name: string) {
  selected.value = name
  loading.value = true
  error.value = ''
  audioUrl.value = `/output/audio/${name}.ogg`
  try {
    const res = await fetch(`/output/transcription/${name}.json`)
    transcription.value = await res.json()
  } catch {
    error.value = `Failed to load transcription for ${name}`
    transcription.value = null
  }
  loading.value = false
}

function onTimeUpdate(time: number) {
  currentTime.value = time
}

function onSeek(time: number) {
  playerRef.value?.seek(time)
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors font-sans" style="font-family:var(--font-ui)">
    <div class="max-w-3xl mx-auto p-6 space-y-5">
      <header class="flex items-center justify-between">
        <h1 class="text-xl font-semibold tracking-tight text-gray-800 dark:text-gray-200">
          transcription viewer
        </h1>
        <div class="flex items-center gap-3">
          <select
            v-model="selected"
            @change="selectRecording(selected)"
            class="appearance-none bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-800 rounded-lg px-3 py-1.5 pr-8 text-sm font-medium focus:outline-none focus:border-emerald-500 dark:focus:border-emerald-400 transition-colors text-gray-700 dark:text-gray-300 cursor-pointer"
          >
            <option v-for="r in recordings" :key="r" :value="r">{{ r }}</option>
          </select>
          <button
            @click="toggleTheme"
            class="w-9 h-9 rounded-lg bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-800 flex items-center justify-center hover:border-gray-300 dark:hover:border-gray-700 transition-colors cursor-pointer"
            :aria-label="dark ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            <span v-if="dark" class="i-carbon-moon text-lg" />
            <span v-else class="i-carbon-sun text-lg" />
          </button>
        </div>
      </header>

      <p v-if="error" class="text-red-500 dark:text-red-400 text-sm">{{ error }}</p>
      <p v-if="loading" class="text-gray-400 dark:text-gray-500 text-sm">Loading...</p>
      <p v-if="!loading && recordings.length === 0" class="text-gray-400 dark:text-gray-500 text-sm">
        No recordings found. Run <code class="text-gray-600 dark:text-gray-300">python compress.py</code> first.
      </p>

      <template v-if="audioUrl && transcription">
        <AudioPlayer ref="playerRef" :src="audioUrl" :duration="transcription.duration_sec" @timeupdate="onTimeUpdate" />
        <TranscriptViewer
          :segments="transcription.segments"
          :current-time="currentTime"
          @seek="onSeek"
        />
      </template>
    </div>
  </div>
</template>
