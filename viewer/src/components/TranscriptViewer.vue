<script setup lang="ts">
import { computed } from 'vue'

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

const props = defineProps<{
  segments: Segment[]
  currentTime: number
}>()

const emit = defineEmits<{ seek: [time: number] }>()

const words = computed(() => {
  return props.segments.flatMap(s => s.words)
})

const activeIndex = computed(() => {
  const t = props.currentTime * 1000
  return words.value.findIndex(w => t >= w.start * 1000 && t < w.end * 1000)
})

const pastCount = computed(() => {
  const t = props.currentTime * 1000
  return words.value.filter(w => w.end * 1000 <= t).length
})

function wordClass(i: number): string {
  const pc = pastCount.value
  if (i < pc) {
    return 'text-gray-400 dark:text-gray-500'
  }
  if (i === activeIndex.value) {
    return 'text-emerald-600 dark:text-emerald-400'
  }
  return 'text-gray-500 dark:text-gray-400'
}

function onClickWord(w: Word) {
  emit('seek', w.start)
}
</script>

<template>
  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 min-h-[200px] shadow-sm">
    <div v-if="words.length > 0" class="leading-relaxed text-lg font-serif" style="font-family:var(--font-body)">
      <span
        v-for="(w, i) in words"
        :key="i"
        @click="onClickWord(w)"
        :class="[wordClass(i), 'inline-block cursor-pointer mr-1.5 transition-colors duration-75 rounded hover:bg-gray-100 dark:hover:bg-gray-800 px-0.5 -mx-0.5']"
      >{{ w.word }}</span>
    </div>
    <p v-else class="text-gray-400 dark:text-gray-500 text-sm text-center py-8">
      {{ segments.length > 0 ? 'No word-level timestamps in this transcription' : 'No segments in this transcription' }}
    </p>
  </div>
</template>
