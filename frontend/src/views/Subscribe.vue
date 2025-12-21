<template>
  <div class="card">
    <h2 class="title">MQTT 订阅端 · 实时环境数据</h2>

    <div class="status">
      <span :class="connected ? 'ok' : 'err'">
        ● {{ connected ? "WebSocket 已连接" : "未连接" }}
      </span>
    </div>

    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue"
import * as echarts from "echarts"

const chartRef = ref(null)
let chartInstance = null
let ws = null

const connected = ref(false)

const maxPoints = 50
const labels = []
const temperature = []
const humidity = []
const pressure = []

const renderChart = () => {
  if (!chartInstance) return

  const option = {
    backgroundColor: "#f5f8ff",
    title: {
      text: "实时订阅数据曲线",
      left: "center",
      textStyle: { color: "#334466", fontSize: 20 }
    },
    tooltip: { trigger: "axis" },
    legend: {
      top: 50,
      data: ["温度 (°C)", "湿度 (%)", "气压 (hPa)"]
    },
    grid: {
      left: "6%",
      right: "6%",
      top: 100,
      bottom: "10%",
      containLabel: true
    },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { type: "dashed" } }
    },
    series: [
      { name: "温度 (°C)", type: "line", data: temperature },
      { name: "湿度 (%)", type: "line", data: humidity },
      { name: "气压 (hPa)", type: "line", data: pressure }
    ]
  }

  chartInstance.setOption(option)
}

const connectWebSocket = () => {
  ws = new WebSocket("ws://127.0.0.1:8765")

  ws.onopen = () => {
    connected.value = true
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    labels.push(data.timestamp)
    temperature.push(data.temperature)
    humidity.push(data.humidity)
    pressure.push(data.pressure)

    if (labels.length > maxPoints) {
      labels.shift()
      temperature.shift()
      humidity.shift()
      pressure.shift()
    }

    renderChart()
  }

  ws.onclose = () => {
    connected.value = false
  }

  ws.onerror = () => {
    connected.value = false
  }
}

onMounted(() => {
  chartInstance = echarts.init(chartRef.value)
  renderChart()
  connectWebSocket()

  window.addEventListener("resize", () => chartInstance.resize())
})

onBeforeUnmount(() => {
  if (ws) ws.close()
  window.removeEventListener("resize", () => chartInstance.resize())
})
</script>

<style scoped>
.card {
  max-width: 1400px;
  margin: 20px auto;
  background: #ffffff;
  border-radius: 20px;
  padding: 20px 40px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 28px;
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

.chart {
  width: 100%;
  height: 600px;
}
</style>
