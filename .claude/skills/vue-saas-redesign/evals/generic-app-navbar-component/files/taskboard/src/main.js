import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomeView from './views/HomeView.vue'
import ProjectsView from './views/ProjectsView.vue'
import TeamView from './views/TeamView.vue'
import SettingsView from './views/SettingsView.vue'
import './assets/main.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/projects', component: ProjectsView },
    { path: '/team', component: TeamView },
    { path: '/settings', component: SettingsView }
  ]
})

createApp(App).use(router).mount('#app')
