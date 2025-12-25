<template>
  <div class="card">
    <h2 class="title">环境数据分析</h2>

    <!-- 统计卡片区域 -->
    <div class="stats-cards" v-if="sensorInfo">
      <div class="stat-card">
        <div class="stat-icon">📍</div>
        <div class="stat-content">
          <div class="stat-label">传感器位置</div>
          <div class="stat-value">{{ sensorInfo.location }}</div>
          <div class="stat-sub">设备ID: {{ sensorInfo.sensor_id }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-label">数据统计</div>
          <div class="stat-value">{{ dataQuality?.total_records || 0 }} 条</div>
          <div class="stat-sub">分析: {{ dataQuality?.analyzed_records || 0 }} 条</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏱️</div>
        <div class="stat-content">
          <div class="stat-label">采集时长</div>
          <div class="stat-value">{{ timeRange?.duration_hours || 0 }} 小时</div>
          <div class="stat-sub" v-if="timeRange?.start">{{ formatShortTime(timeRange.start) }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-label">数据质量</div>
          <div class="stat-value">{{ (100 - (dataQuality?.missing_rate || 0)).toFixed(1) }}%</div>
          <div class="stat-sub">完整率</div>
        </div>
      </div>
    </div>

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

        <p class="analysis-item" v-if="predictTrend">
          🔮 <strong>预测趋势：</strong><br />
          根据线性回归模型，预测未来 5 个时间点
          <strong>{{ currentMetric }}</strong> 将呈现
          <strong style="color: #ee6666">{{ predictTrend }}</strong>趋势，
          预测值范围 {{ predictRange }}。
        </p>

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

        <p class="analysis-item" v-if="dataQuality">
          ✅ <strong>数据质量：</strong><br />
          本次分析共使用 <strong>{{ dataQuality.total_records }}</strong> 条数据，
          数据完整率 <strong>{{ (100 - dataQuality.missing_rate).toFixed(1) }}%</strong>，
          分析结果具有较高可信度。
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
const sensorInfo = ref(null)
const timeRange = ref(null)
const dataQuality = ref(null)

let chartInstance = null
let correlationChartInstance = null 
let analysisData = null
const correlationData = ref(null)
let labels = []

const renderChart = () => {
  if (!analysisData) return
  const metricData = analysisData[currentMetric.value]

  // 构建预测数据：在现有数据后追加预测点
  const predictLabels = metricData.predict?.map((_, i) => `预测+${i + 1}`) || []
  const allLabels = [...labels, ...predictLabels]
  
  // 为预测数据补齐前面的空值
  const predictData = [
    ...Array(labels.length).fill(null),
    ...metricData.predict
  ]

  const option = {
    backgroundColor: "#f5f8ff",
    color: ["#5470c6", "#91cc75", "#fac858", "#ee6666"],
    title: {
        text: `${currentMetric.value} 趋势分析与预测`,
        left: "center",
        top: 20,
        textStyle: {
        color: "#334466",
        fontSize: 20,
        fontWeight: 600
        }
    },
    tooltip: { trigger: "axis" },
    legend: {
        top: 60,
        data: ["原始数据", "平滑数据", "拟合曲线", "预测趋势"],
        textStyle: { color: "#334466" }
    },
    grid: {
        left: "6%",
        right: "6%",
        bottom: "10%",
        top: 120,
        containLabel: true
    },
    xAxis: {
        type: "category",
        data: allLabels,
        axisLine: { lineStyle: { color: "#cbd6e2" } },
        axisLabel: { color: "#334466", rotate: 45 }
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
        { name: "拟合曲线", type: "line", data: metricData.fitted, smooth: true, lineStyle: { type: "dashed" } },
        { 
          name: "预测趋势", 
          type: "line", 
          data: predictData, 
          smooth: true,
          lineStyle: { type: "dotted", width: 2 },
          itemStyle: { color: "#ee6666" },
          connectNulls: true
        }
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

const formatShortTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 计算预测趋势和范围
const predictTrend = computed(() => {
  if (!analysisData || !currentMetric.value) return null
  const metricData = analysisData[currentMetric.value]
  if (!metricData?.predict || metricData.predict.length < 2) return null

  const firstVal = metricData.predict[0]
  const lastVal = metricData.predict[metricData.predict.length - 1]
  const diff = lastVal - firstVal

  if (Math.abs(diff) < 0.1) return '稳定'
  return diff > 0 ? '上升' : '下降'
})

const predictRange = computed(() => {
  if (!analysisData || !currentMetric.value) return ''
  const metricData = analysisData[currentMetric.value]
  if (!metricData?.predict || metricData.predict.length === 0) return ''

  const values = metricData.predict
  const min = Math.min(...values).toFixed(2)
  const max = Math.max(...values).toFixed(2)
  return `${min} ~ ${max}`
})

onMounted(async () => {
  const res = await axios.get("http://121.43.119.155:5000/api/analyze")

  analysisData = res.data.data
  labels = res.data.labels
  availableMetrics.value = res.data.available_metrics
  correlationData.value = res.data.correlation
  sensorInfo.value = res.data.sensor_info
  timeRange.value = res.data.time_range
  dataQuality.value = res.data.data_quality
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

/* 统计卡片样式 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px;
  color: white;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
}

.stat-card:nth-child(2) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card:nth-child(3) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card:nth-child(4) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon {
  font-size: 32px;
  opacity: 0.9;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 2px;
}

.stat-sub {
  font-size: 11px;
  opacity: 0.8;
}
</style>
