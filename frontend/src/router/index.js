import { createRouter, createWebHistory } from 'vue-router'
import BrowseView from '../views/BrowseView.vue'
import AccessView from '../views/AccessView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'

const routes = [
  { path: '/', component: BrowseView },
  { path: '/browse/:path(.*)*', component: BrowseView },
  { path: '/access', component: AccessView },
  { path: '/admin/login', component: AdminLoginView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
