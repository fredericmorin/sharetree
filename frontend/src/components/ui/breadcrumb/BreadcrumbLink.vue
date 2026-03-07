<script setup>
import { cn } from '@/lib/utils.js'
const props = defineProps({
  class: { type: String, default: '' },
  href: { type: String, default: '' },
})
</script>

<template>
  <a :href="href" :class="cn('transition-colors hover:text-foreground', props.class)">
    <slot />
  </a>
</template>
