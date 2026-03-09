import { createRouter, createWebHistory } from 'vue-router'
import BrowseView from '../views/BrowseView.vue'
import AccessView from '../views/AccessView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import AdminView from '../views/AdminView.vue'
import AdminSessionsView from '../views/AdminSessionsView.vue'
import AdminBrowseView from '../views/AdminBrowseView.vue'
import AdminCreateAccessCodeView from '../views/AdminCreateAccessCodeView.vue'
import AdminDownloadLogsView from '../views/AdminDownloadLogsView.vue'
import NotFoundView from '../views/NotFoundView.vue'

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
  { path: '/admin/logs', component: AdminDownloadLogsView },
  { path: '/:pathMatch(.*)*', component: NotFoundView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
