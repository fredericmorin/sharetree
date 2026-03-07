<script setup>
import { cn } from '@/lib/utils.js'
const props = defineProps({ class: { type: String, default: '' } })
</script>

<template>
  <span
    :class="cn('font-normal text-foreground', props.class)"
    role="link"
    aria-disabled="true"
    aria-current="page"
  >
    <slot />
  </span>
</template>
