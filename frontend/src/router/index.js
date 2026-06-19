import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ResultView from '../views/ResultView.vue'
import HistoryView from '../views/HistoryView.vue'
import StudentsView from '../views/StudentsView.vue'
import BatchView from '../views/BatchView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/result/:id',
    name: 'result',
    component: ResultView,
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryView,
  },
  {
    path: '/students',
    name: 'students',
    component: StudentsView,
  },
  {
    path: '/batch',
    name: 'batch',
    component: BatchView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
