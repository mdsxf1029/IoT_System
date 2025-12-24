<template>
  <div class="card">
    <!-- 项目标题区 -->
    <div class="header">
      <h1>IoT_System</h1>
      <h2>同济大学 2025 年《物联网应用概论》期末项目</h2>
      <p class="subtitle">
        某区域温度 / 湿度 / 气压数据发布订阅与分析系统（订阅端）
      </p>
    </div>

    <!-- 连接状态 -->
    <div class="status">
      <span :class="connected ? 'ok' : 'err'">
        {{ connected ? "● 已连接订阅端服务（WebSocket）" : "● 未连接订阅端服务" }}
      </span>
    </div>

    <!-- 实时数据概览 -->
    <div class="overview">
      <div class="overview-item">
        <span class="label">当前温度</span>
        <span class="value">{{ latest.temperature ?? "--" }} °C</span>
      </div>
      <div class="overview-item">
        <span class="label">当前湿度</span>
        <span class="value">{{ latest.humidity ?? "--" }} %</span>
      </div>
      <div class="overview-item">
        <span class="label">当前气压</span>
        <span class="value">{{ latest.pressure ?? "--" }} hPa</span>
      </div>
      <div class="overview-item">
        <span class="label">接收数据条数</span>
        <span class="value">{{ totalCount }}</span>
      </div>
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
const totalCount = ref(0)

const latest = ref({
  temperature: null,
  humidity: null,
  pressure: null
})

let ws = null
const MAX_ROWS = 30   // 表格最多显示条数

const connectWebSocket = () => {
  ws = new WebSocket("ws://121.43.119.155:8765")

  ws.onopen = () => {
    connected.value = true
    console.log("WebSocket 已连接")
  }

  ws.onmessage = (event) => {
    let msg
    try {
      msg = JSON.parse(event.data)
    } catch (e) {
      console.warn("WebSocket 消息解析失败", e)
      return
    }

    // 更新表格数据
    dataList.value.unshift({
      timestamp: msg.timestamp,
      temperature: msg.temperature,
      humidity: msg.humidity,
      pressure: msg.pressure
    })

    // 更新实时概览
    latest.value = {
      temperature: msg.temperature,
      humidity: msg.humidity,
      pressure: msg.pressure
    }

    totalCount.value++

    if (dataList.value.length > MAX_ROWS) {
      dataList.value.pop()
    }
  }

  ws.onclose = () => {
    connected.value = false
    console.warn("WebSocket 已断开")
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
  padding: 24px 32px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}

.header {
  text-align: center;
  margin-bottom: 16px;
}

.header h1 {
  font-size: 30px;
  color: #2c3e50;
  margin: 0;
}

.header h2 {
  font-size: 16px;
  color: #667799;
  margin: 6px 0;
}

.subtitle {
  font-size: 14px;
  color: #8899aa;
}

.status {
  text-align: center;
  margin: 16px 0;
  font-size: 14px;
}

.ok {
  color: #2ecc71;
}

.err {
  color: #e74c3c;
}

.overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.overview-item {
  background: #f6f9ff;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}

.label {
  display: block;
  font-size: 13px;
  color: #667799;
}

.value {
  font-size: 20px;
  font-weight: 600;
  color: #334466;
  margin-top: 4px;
}

.table-container {
  max-height: 420px;
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
