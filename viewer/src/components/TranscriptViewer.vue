<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

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

interface WordRef extends Word {
  segIdx: number
  wordIdx: number
}

const props = defineProps<{
  segments: Segment[]
  currentTime: number
}>()

const emit = defineEmits<{
  seek: [time: number]
  update: [segments: Segment[]]
}>()

const localSegments = ref<Segment[]>([])
watch(() => props.segments, (s) => {
  localSegments.value = JSON.parse(JSON.stringify(s))
}, { immediate: true })

const words = computed(() => {
  return localSegments.value.flatMap((s, si) =>
    s.words.map((w, wi) => ({ ...w, segIdx: si, wordIdx: wi }))
  )
})

const activeIndex = computed(() => {
  const t = props.currentTime * 1000
  return words.value.findIndex(w => t >= w.start * 1000 && t < w.end * 1000)
})

const pastCount = computed(() => {
  const t = props.currentTime * 1000
  return words.value.filter(w => w.end * 1000 <= t).length
})

const editingIdx = ref(-1)
const editText = ref('')

function startEdit(i: number) {
  editingIdx.value = i
  editText.value = words.value[i].word
  nextTick(() => {
    const el = document.getElementById(`edit-${i}`) as HTMLInputElement | null
    el?.focus()
    el?.select()
  })
}

function commitEdit() {
  const i = editingIdx.value
  if (i < 0) return
  const w = words.value[i]
  const seg = localSegments.value[w.segIdx]
  const trimmed = editText.value.trim()
  if (trimmed && trimmed !== seg.words[w.wordIdx].word) {
    seg.words[w.wordIdx].word = trimmed
    seg.text = seg.words.map(w => w.word).join(' ')
    emit('update', localSegments.value)
  }
  editingIdx.value = -1
  editText.value = ''
}

function cancelEdit() {
  editingIdx.value = -1
  editText.value = ''
}

function wordClass(i: number): string[] {
  const pc = pastCount.value
  const cls = ['inline-block', 'cursor-pointer', 'mr-1.5', 'transition-colors', 'duration-75', 'rounded', 'px-0.5', '-mx-0.5']
  if (i < pc) cls.push('text-gray-400', 'dark:text-gray-500')
  else if (i === activeIndex.value) cls.push('text-emerald-600', 'dark:text-emerald-400')
  else cls.push('text-gray-500', 'dark:text-gray-400')
  if (editingIdx.value !== i) cls.push('hover:bg-gray-100', 'dark:hover:bg-gray-800')
  return cls
}

function onClickWord(w: WordRef) {
  if (editingIdx.value >= 0) commitEdit()
  emit('seek', w.start)
}

function onDblClickWord(i: number) {
  startEdit(i)
}

function onEditKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') { e.preventDefault(); commitEdit() }
  if (e.key === 'Escape') { e.preventDefault(); cancelEdit() }
}
</script>

<template>
  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 min-h-[200px] shadow-sm">
    <div v-if="words.length > 0" class="leading-relaxed text-lg font-serif" style="font-family:var(--font-body)">
      <span
        v-for="(w, i) in words"
        :key="`${w.segIdx}-${w.wordIdx}`"
        class="inline-block mr-1.5 relative"
      >
        <span
          v-if="editingIdx !== i"
          @click="onClickWord(w)"
          @dblclick="onDblClickWord(i)"
          :class="wordClass(i)"
        >{{ w.word }}</span>
        <input
          v-else
          :id="`edit-${i}`"
          v-model="editText"
          :size="Math.max(editText.length + 2, 5)"
          @blur="commitEdit"
          @keydown="onEditKeydown"
          class="outline-none border-b-2 border-emerald-500 bg-transparent text-emerald-600 dark:text-emerald-400 font-sans text-lg"
          style="font-family:var(--font-ui)"
        />
      </span>
    </div>
    <p v-else class="text-gray-400 dark:text-gray-500 text-sm text-center py-8">
      {{ segments.length > 0 ? 'No word-level timestamps in this transcription' : 'No segments in this transcription' }}
    </p>
  </div>
</template>
