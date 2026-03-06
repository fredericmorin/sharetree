import { createRouter, createWebHistory } from 'vue-router'
import BrowseView from '../views/BrowseView.vue'
import AccessView from '../views/AccessView.vue'

const routes = [
  { path: '/', component: BrowseView },
  { path: '/browse/:path(.*)*', component: BrowseView },
  { path: '/access', component: AccessView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
