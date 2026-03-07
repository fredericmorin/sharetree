<script setup>
import { cn } from '@/lib/utils.js'
import { ChevronRight } from 'lucide-vue-next'
const props = defineProps({ class: { type: String, default: '' } })
</script>

<template>
  <li :class="cn('[&>svg]:w-3.5 [&>svg]:h-3.5', props.class)" role="presentation" aria-hidden="true">
    <slot>
      <ChevronRight />
    </slot>
  </li>
</template>
