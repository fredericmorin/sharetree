<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import FileIcon from '@/components/FileIcon.vue'
import Badge from '@/components/ui/badge/index.vue'
import { Download, FolderOpen } from 'lucide-vue-next'

const props = defineProps({
  entries: { type: Array, required: true },
  searchQuery: { type: String, default: '' },
})

const router = useRouter()

const filteredEntries = computed(() => {
  const q = props.searchQuery.trim().toLowerCase()
  if (!q) return props.entries
  return props.entries.filter((e) => e.name.toLowerCase().includes(q))
})

function formatSize(bytes) {
  if (bytes === null || bytes === undefined) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function navigateTo(entry) {
  router.push('/browse' + entry.path)
}
</script>

<template>
  <div>
    <!-- empty directory -->
    <div v-if="!entries.length" class="flex flex-col items-center gap-3 py-16 text-center">
      <FolderOpen class="h-10 w-10 text-muted-foreground/50" />
      <p class="text-sm text-muted-foreground">This directory is empty.</p>
    </div>

    <!-- no search results -->
    <div v-else-if="!filteredEntries.length" class="flex flex-col items-center gap-3 py-16 text-center">
      <FolderOpen class="h-10 w-10 text-muted-foreground/50" />
      <p class="text-sm text-muted-foreground">No matches for "<span class="font-medium text-foreground">{{ searchQuery }}</span>"</p>
    </div>

    <!-- entry list -->
    <ul v-else class="rounded-lg border divide-y divide-border overflow-hidden">
      <li
        v-for="entry in filteredEntries"
        :key="entry.path"
        class="group flex items-center gap-3 px-4 py-2.5 bg-card hover:bg-accent/50 transition-colors"
        :class="{ 'cursor-pointer': entry.type === 'directory' }"
        @click="entry.type === 'directory' ? navigateTo(entry) : undefined"
      >
        <FileIcon :filename="entry.name" :is-directory="entry.type === 'directory'" />

        <template v-if="entry.type === 'directory'">
          <span class="flex-1 text-sm font-medium text-foreground min-w-0 truncate">{{ entry.name }}</span>
        </template>

        <template v-else>
          <a
            :href="'/download' + entry.path"
            class="flex-1 text-sm text-foreground hover:underline min-w-0 truncate no-underline hover:text-foreground"
            download
            @click.stop
          >
            {{ entry.name }}
          </a>
          <Badge v-if="entry.size !== null && entry.size !== undefined" variant="secondary" class="shrink-0 font-mono text-xs">
            {{ formatSize(entry.size) }}
          </Badge>
          <a
            :href="'/download' + entry.path"
            :aria-label="`Download ${entry.name}`"
            class="shrink-0 text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover:opacity-100 no-underline"
            download
            @click.stop
          >
            <Download class="h-4 w-4" />
          </a>
        </template>
      </li>
    </ul>
  </div>
</template>
