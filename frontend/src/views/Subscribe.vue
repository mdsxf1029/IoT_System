<template>
  <div class="card">
    <h2 class="title">MQTT 订阅端 · 环境数据实时接收</h2>

    <!-- 连接状态 -->
    <div class="status">
      <span :class="connected ? 'ok' : 'err'">
        {{ connected ? "● 已连接订阅端服务" : "● 未连接" }}
      </span>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>时间戳</th>
            <th>温度 (°C)</th>
            <th>湿度 (%)</th>
            <th>气压 (hPa)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in dataList" :key="index">
            <td>{{ item.timestamp }}</td>
            <td>{{ item.temperature }}</td>
            <td>{{ item.humidity }}</td>
            <td>{{ item.pressure }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue"

const connected = ref(false)
const dataList = ref([])

let ws = null
const MAX_ROWS = 30   // 页面最多显示 30 条，防止无限增长

const connectWebSocket = () => {
  ws = new WebSocket("ws://127.0.0.1:8765")

  ws.onopen = () => {
    connected.value = true
    console.log("WebSocket 已连接")
  }

  ws.onmessage = (event) => {
    console.log("WS 原始数据:", event.data)
    console.debug("WS raw message:", event.data)

    let payload
    try {
      payload = JSON.parse(event.data)
    } catch (e) {
      console.warn("WS 消息非标准 JSON：", e)
      payload = event.data
    }

    if (typeof payload === "string") {
      try {
        payload = JSON.parse(payload)
      } catch (e) {
        // keep as string
      }
    }

    // 支持后端发送的 { event, data } 包装，也兼容直接发送对象
    const msg = payload && payload.data ? payload.data : payload

    // 如果 msg 不是对象，跳过
    if (!msg || typeof msg !== "object") return

    dataList.value.unshift({
      timestamp: msg.timestamp,
      temperature: msg.temperature,
      humidity: msg.humidity,
      pressure: msg.pressure
    })

    if (dataList.value.length > MAX_ROWS) {
      dataList.value.pop()
    }
  }

  ws.onclose = () => {
    connected.value = false
    console.warn("WebSocket 连接关闭")
  }

  ws.onerror = () => {
    connected.value = false
    console.error("WebSocket 发生错误")
  }
}

onMounted(() => {
  connectWebSocket()
})

onBeforeUnmount(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.card {
  max-width: 1200px;
  margin: 20px auto;
  background: #ffffff;
  border-radius: 16px;
  padding: 20px 30px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 26px;
  font-weight: 700;
  color: #334466;
  text-align: center;
  margin-bottom: 10px;
}

.status {
  text-align: center;
  margin-bottom: 20px;
  font-size: 14px;
}

.ok {
  color: #2ecc71;
}

.err {
  color: #e74c3c;
}

.table-container {
  max-height: 500px;
  overflow-y: auto;
  border-radius: 8px;
  border: 1px solid #e0e6f0;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background-color: #f5f8ff;
  position: sticky;
  top: 0;
}

th,
td {
  padding: 10px 12px;
  text-align: center;
  border-bottom: 1px solid #e0e6f0;
  font-size: 14px;
  color: #334466;
}

tbody tr:nth-child(even) {
  background-color: #fafbff;
}
</style>
