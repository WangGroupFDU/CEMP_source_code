import { createRouter, createWebHistory } from 'vue-router'
import DatabaseView from '../views/DatabaseView.vue'
import PredictionView from '../views/PredictionView.vue'
import VisualizationView from '../views/VisualizationView.vue'

const routes = [
  { path: '/', redirect: '/database' },
  { path: '/database', name: 'database', component: DatabaseView },
  { path: '/prediction', name: 'prediction', component: PredictionView },
  { path: '/visualization', name: 'visualization', component: VisualizationView },
]

const router = createRouter({
  history: createWebHistory('/crystals/app/'),
  routes,
})

export default router
