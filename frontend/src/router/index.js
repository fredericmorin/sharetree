import { createRouter, createWebHistory } from 'vue-router'
import BrowseView from '../views/BrowseView.vue'
import AccessView from '../views/AccessView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import AdminView from '../views/AdminView.vue'
import AdminSessionsView from '../views/AdminSessionsView.vue'
import AdminBrowseView from '../views/AdminBrowseView.vue'
import AdminCreateAccessCodeView from '../views/AdminCreateAccessCodeView.vue'

const routes = [
  { path: '/', component: BrowseView },
  { path: '/browse/:path(.*)*', component: BrowseView },
  { path: '/access', component: AccessView },
  { path: '/admin/login', component: AdminLoginView },
  { path: '/admin', component: AdminView },
  { path: '/admin/sessions', component: AdminSessionsView },
  { path: '/admin/browse', component: AdminBrowseView },
  { path: '/admin/browse/:path(.*)*', component: AdminBrowseView },
  { path: '/admin/access/create', component: AdminCreateAccessCodeView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
