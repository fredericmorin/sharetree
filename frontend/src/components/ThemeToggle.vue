<script setup>
import { useColorMode } from '@vueuse/core'
import { Sun, Moon } from 'lucide-vue-next'
import Button from '@/components/ui/button/index.vue'

const mode = useColorMode()

function toggle() {
  mode.value = mode.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <Button variant="ghost" size="icon" @click="toggle" :aria-label="mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'">
    <Sun v-if="mode === 'dark'" class="h-5 w-5" />
    <Moon v-else class="h-5 w-5" />
  </Button>
</template>
