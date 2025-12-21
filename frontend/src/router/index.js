import { createRouter, createWebHistory } from "vue-router"

import Subscribe from "../views/Subscribe.vue"
import Publish from "../views/Publish.vue"
import DataDisplay from "../views/DataDisplay.vue"

const routes = [
  {
    path: "/",
    redirect: "/subscribe"
  },
  {
    path: "/subscribe",
    component: Subscribe
  },
  {
    path: "/publish",
    component: Publish
  },
  {
    path: "/analyze",
    component: DataDisplay
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
