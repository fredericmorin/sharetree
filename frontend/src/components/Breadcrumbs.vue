<script setup>
import { computed } from 'vue'

const props = defineProps({
  path: { type: String, default: '' },
})

const segments = computed(() => {
  const parts = props.path.split('/').filter(Boolean)
  return parts.map((part, i) => ({
    label: part,
    to: '/browse/' + parts.slice(0, i + 1).join('/'),
  }))
})
</script>

<template>
  <nav class="breadcrumbs" aria-label="breadcrumb">
    <RouterLink to="/" class="crumb">Home</RouterLink>
    <template v-for="seg in segments" :key="seg.to">
      <span class="sep">/</span>
      <RouterLink :to="seg.to" class="crumb">{{ seg.label }}</RouterLink>
    </template>
  </nav>
</template>

<style scoped>
.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.crumb {
  color: #0d6efd;
}

.crumb:last-child {
  color: #212529;
  pointer-events: none;
}

.sep {
  color: #6c757d;
}
</style>
