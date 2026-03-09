<script setup>
import { RouterLink, RouterView } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { Share2 } from 'lucide-vue-next'
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <header class="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="mx-auto max-w-4xl px-4 sm:px-6">
        <div class="flex h-14 items-center justify-between">
          <RouterLink to="/" class="flex items-center gap-2 font-semibold text-foreground hover:text-foreground/80 transition-colors no-underline">
            <Share2 class="h-5 w-5" />
            <span>sharetree</span>
          </RouterLink>
          <ThemeToggle />
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-4xl px-4 sm:px-6 py-8">
      <RouterView v-slot="{ Component, route }">
        <Transition name="fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
