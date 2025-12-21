import { createRouter, createWebHistory } from "vue-router"

import Analyze from "@/views/DataDisplay.vue"

const routes = [
    { path: "/analyze", component: Analyze }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
