import { createRouter, createWebHistory } from 'vue-router'
import BrowseView from '../views/BrowseView.vue'
import AccessView from '../views/AccessView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import AdminView from '../views/AdminView.vue'
import AdminSessionsView from '../views/AdminSessionsView.vue'

const routes = [
  { path: '/', component: BrowseView },
  { path: '/browse/:path(.*)*', component: BrowseView },
  { path: '/access', component: AccessView },
  { path: '/admin/login', component: AdminLoginView },
  { path: '/admin', component: AdminView },
  { path: '/admin/sessions', component: AdminSessionsView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
