<script setup>
import { cn } from '@/lib/utils.js'
const props = defineProps({ class: { type: String, default: '' } })
</script>

<template>
  <li :class="cn('inline-flex items-center gap-1.5', props.class)">
    <slot />
  </li>
</template>
