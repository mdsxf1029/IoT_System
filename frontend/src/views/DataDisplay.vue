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

    <!-- 主体区域：左图右文 -->
    <div class="content">
      <!-- 左侧：图表 -->
      <div class="charts">
        <div ref="chartRef" class="chart"></div>
        <div ref="correlationChartRef" class="chart correlation-chart"></div>
      </div>

      <!-- 右侧：分析解读 -->
      <div class="analysis-panel">
        <h3>分析解读</h3>

        <p class="analysis-item" v-if="strongestCorrelation">
          📈 <strong>趋势特征：</strong><br />
          当前选中指标 <strong>{{ currentMetric }}</strong>
          与 <strong>{{ strongestCorrelation.metric }}</strong>
          表现出最强相关性（相关系数
          <strong>{{ strongestCorrelation.value.toFixed(2) }}</strong>），
          表明两者在时间变化上具有明显联动特征。
        </p>

        <p class="analysis-item" v-else>
          📈 <strong>趋势特征：</strong><br />
          当前选中指标 <strong>{{ currentMetric }}</strong>
          的相关性分析结果尚不足以形成明确结论。
        </p>

        <p class="analysis-item">
          🔗 <strong>参数关联：</strong><br />
          下方相关性热力图展示了温度、湿度与气压等参数之间的相关程度，
          颜色越深表示相关性越强。
        </p>

        <p class="analysis-item">
          🧠 <strong>分析说明：</strong><br />
          该分析结果可用于理解环境参数之间的相互影响关系，
          为后续预测分析和异常检测提供依据。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from "vue"
import * as echarts from "echarts"
import axios from "axios"

const chartRef = ref(null)
const correlationChartRef = ref(null)  
const availableMetrics = ref([])
const currentMetric = ref("temperature")

let chartInstance = null
let correlationChartInstance = null 
let analysisData = null
const correlationData = ref(null)
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

const renderCorrelationChart = () => {
  if (!correlationData.value) return

  const metrics = Object.keys(correlationData.value)
  const heatmapData = []

  metrics.forEach((m1, i) => {
    metrics.forEach((m2, j) => {
      heatmapData.push([i, j, correlationData.value[m1][m2]])
    })
  })

  const option = {
    title: {
      text: "参数相关性分析",
      left: "center",
      top: 20
    },
    tooltip: {
      formatter: (p) =>
        `${metrics[p.data[1]]} vs ${metrics[p.data[0]]}<br/>相关系数：${p.data[2].toFixed(2)}`
    },
    grid: {
      top: 80,
      left: "10%",
      right: "10%",
      bottom: "10%"
    },
    xAxis: {
      type: "category",
      data: metrics
    },
    yAxis: {
      type: "category",
      data: metrics
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: -20,
      inRange: {
        color: ["#5470c6", "#ffffff", "#d94e5d"]
      }
    },
    series: [
      {
        type: "heatmap",
        data: heatmapData,
        label: {
          show: true,
          formatter: (p) => p.data[2].toFixed(2)
        }
      }
    ]
  }

  correlationChartInstance.setOption(option, true)
}

const strongestCorrelation = computed(() => {
  if (!correlationData.value || !currentMetric.value) return null

  const corrMap = correlationData.value[currentMetric.value]
  if (!corrMap) return null

  let maxItem = null
  let maxValue = 0

  Object.entries(corrMap).forEach(([metric, value]) => {
    // 排除自己和无效值
    if (metric === currentMetric.value || value == null) return

    const absVal = Math.abs(value)
    if (absVal > maxValue) {
      maxValue = absVal
      maxItem = { metric, value }
    }
  })

  return maxItem
})

onMounted(async () => {
  const res = await axios.get("http://127.0.0.1:5002/api/analyze")

  analysisData = res.data.data
  labels = res.data.labels
  availableMetrics.value = res.data.available_metrics
  correlationData.value = res.data.correlation
  currentMetric.value = availableMetrics.value[0]

  // 初始化图表
  chartInstance = echarts.init(chartRef.value)
  correlationChartInstance = echarts.init(correlationChartRef.value)

  renderChart()
  renderCorrelationChart()

  // 窗口自适应
  window.addEventListener("resize", () => {
    chartInstance.resize()
    correlationChartInstance.resize()
  })
})

onBeforeUnmount(() => {
  window.removeEventListener("resize", () => {})
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
  height: 600px; 
  min-height: 500px; 
  width: 1000px;
  min-width: 600px;
}

.correlation-chart {
  height: 500px;
  margin-top: 40px;
}

/* 主体左右布局 */
.content {
  display: flex;
  gap: 32px;
  align-items: flex-start;
}

/* 左侧图表区域 */
.charts {
  flex: 3;
}

/* 右侧分析解读栏 */
.analysis-panel {
  flex: 1;
  background: linear-gradient(180deg, #f7f9fc, #ffffff);
  border-radius: 16px;
  padding: 24px;
  box-shadow: inset 0 0 0 1px #e3e8f0;
}

/* 分析栏标题 */
.analysis-panel h3 {
  margin-bottom: 16px;
  font-size: 20px;
  color: #334466;
  border-left: 4px solid #5470c6;
  padding-left: 12px;
}

/* 每条分析说明 */
.analysis-item {
  font-size: 14px;
  line-height: 1.7;
  color: #555;
  margin-bottom: 18px;
}
</style>
