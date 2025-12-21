<template>
  <div class="card">
    <h2 class="title">环境数据分析</h2>

    <div class="controls">
      <label>选择指标：</label>
      <select v-model="currentMetric" @change="renderChart">
        <option v-for="m in availableMetrics" :key="m" :value="m">
          {{ m }}
        </option>
      </select>
    </div>

    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue"
import * as echarts from "echarts"
import axios from "axios"

const chartRef = ref(null)
const availableMetrics = ref([])
const currentMetric = ref("temperature")
let chartInstance = null
let analysisData = null
let labels = []

const renderChart = () => {
  if (!analysisData) return
  const metricData = analysisData[currentMetric.value]

  const option = {
    backgroundColor: "#f5f8ff",
    color: ["#5470c6", "#91cc75", "#fac858"],
    title: {
        text: `${currentMetric.value} 趋势分析`,
        left: "center",
        top: 20, // 增加顶部距离
        textStyle: {
        color: "#334466",
        fontSize: 20,
        fontWeight: 600
        }
    },
    tooltip: { trigger: "axis" },
    legend: {
        top: 60, // 增加与标题距离
        data: ["原始数据", "平滑数据", "拟合曲线"],
        textStyle: { color: "#334466" }
    },
    grid: {
        left: "6%",
        right: "6%",
        bottom: "10%",
        top: 120, // 整体上移，避免覆盖标题/图例
        containLabel: true
    },
    xAxis: {
        type: "category",
        data: labels,
        axisLine: { lineStyle: { color: "#cbd6e2" } },
        axisLabel: { color: "#334466", rotate: 45 } // x轴标签可以旋转避免重叠
    },
    yAxis: {
        type: "value",
        axisLine: { lineStyle: { color: "#cbd6e2" } },
        splitLine: { lineStyle: { type: "dashed", color: "#e0e6f0" } },
        axisLabel: { color: "#334466" }
    },
    series: [
        { name: "原始数据", type: "line", data: metricData.raw, smooth: false },
        { name: "平滑数据", type: "line", data: metricData.smooth, smooth: true },
        { name: "拟合曲线", type: "line", data: metricData.fitted, smooth: true, lineStyle: { type: "dashed" } }
    ]
    }

  chartInstance.setOption(option, true)
}

onMounted(async () => {
  try {
    const res = await axios.get("http://127.0.0.1:5002/api/analyze")
    analysisData = res.data.data
    labels = res.data.labels
    availableMetrics.value = res.data.available_metrics
    currentMetric.value = availableMetrics.value[0]
  } catch (err) {
    console.warn("无法获取真实数据，使用模拟数据调试前端")

    // ---------------- 模拟数据 ----------------
    labels = Array.from({ length: 30 }, (_, i) => `T${i+1}`)
    availableMetrics.value = ["temperature", "humidity", "pressure"]
    currentMetric.value = "temperature"

    analysisData = {
      temperature: {
        raw: labels.map(() => 20 + Math.random() * 5),
        smooth: labels.map(() => 20 + Math.random() * 5),
        fitted: labels.map(() => 20 + Math.random() * 5),
      },
      humidity: {
        raw: labels.map(() => 50 + Math.random() * 10),
        smooth: labels.map(() => 50 + Math.random() * 10),
        fitted: labels.map(() => 50 + Math.random() * 10),
      },
      pressure: {
        raw: labels.map(() => 1010 + Math.random() * 5),
        smooth: labels.map(() => 1010 + Math.random() * 5),
        fitted: labels.map(() => 1010 + Math.random() * 5),
      }
    }
  }

  // 初始化图表
  chartInstance = echarts.init(chartRef.value)
  renderChart()

  // 窗口自适应
  window.addEventListener("resize", () => chartInstance && chartInstance.resize())
})


onBeforeUnmount(() => {
  window.removeEventListener("resize", () => chartInstance && chartInstance.resize())
})
</script>

<style scoped>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: "Helvetica Neue", Arial, sans-serif;

  /* 整个页面背景渐变 */
  background: linear-gradient(to bottom, #e6f0ff, #f5f8ff);
}

.card {
  max-width: 1400px;
  min-width: 800px;
  margin: 20px auto;
  background: #ffffff;
  border-radius: 20px;
  padding: 16px 40px;
  
  /* 卡片阴影让卡片浮起来 */
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #334466;
  text-align: center;
  margin-bottom: 30px;
}

.controls {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  margin-bottom: 30px;
}

select {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid #cbd6e2;
  background-color: #f5f8ff;
  color: #334466;
  font-size: 14px;
}

.chart {
  width: 100%;
  height: 600px; /* 大屏效果 */
  min-height: 500px;
}
</style>
