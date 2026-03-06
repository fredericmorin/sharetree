<script setup>
defineProps({
  entries: { type: Array, required: true },
})

function formatSize(bytes) {
  if (bytes === null) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>

<template>
  <ul class="entry-list">
    <li v-if="!entries.length" class="empty">This directory is empty.</li>
    <li v-for="entry in entries" :key="entry.path" class="entry">
      <template v-if="entry.type === 'directory'">
        <span class="icon">📁</span>
        <RouterLink :to="'/browse' + entry.path" class="entry-name dir">{{ entry.name }}</RouterLink>
      </template>
      <template v-else>
        <span class="icon">📄</span>
        <span class="entry-name file">{{ entry.name }}</span>
        <span class="size">{{ formatSize(entry.size) }}</span>
      </template>
    </li>
  </ul>
</template>

<style scoped>
.entry-list {
  list-style: none;
  padding: 0;
  margin: 0;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
}

.empty {
  padding: 1rem;
  color: #6c757d;
}

.entry {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid #f1f3f5;
}

.entry:last-child {
  border-bottom: none;
}

.entry:hover {
  background: #f8f9fa;
}

.icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.entry-name {
  flex: 1;
  font-size: 0.95rem;
}

.entry-name.dir {
  font-weight: 500;
}

.size {
  font-size: 0.8rem;
  color: #6c757d;
  flex-shrink: 0;
}
</style>
