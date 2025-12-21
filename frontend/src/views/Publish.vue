<template>
  <div class="publish-container">
    <h2>MQTT 发布端控制面板</h2>

    <div class="buttons">
      <button @click="startPublish" :disabled="status.running">
        启动发布
      </button>

      <button @click="stopPublish" :disabled="!status.running || stopping">
        停止发布
      </button>

    </div>

    <div class="status">
      <p><b>运行状态：</b>{{ status.running ? "运行中" : "已停止" }}</p>

      <div v-if="status.total > 0" class="progress-area">
        <progress
          :value="status.count"
          :max="status.total"
        ></progress>

        <p class="progress-text">
          已发布：{{ status.count }} / {{ status.total }}
          （{{ progressPercent }}%）
        </p>
      </div>

      <p v-if="status.error" class="error">
        <b>错误：</b>{{ status.error }}
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios"

export default {
  name: "Publish",
  data() {
    return {
      status: {
        running: false,
        count: 0,
        total: 0,
        error: null
      },
      timer: null,
      stopping: false   // ✅ 关键：防止重复 stop
    }
  },
  computed: {
    progressPercent() {
      if (this.status.total === 0) return 0
      return Math.round((this.status.count / this.status.total) * 100)
    }
  },
  methods: {
    async startPublish() {
      try {
        await axios.post("http://127.0.0.1:5000/start")
        this.status.running = true
        this.stopping = false
        this.startPolling()
      } catch (err) {
        this.status.error = "启动发布失败"
      }
    },

    async stopPublish() {
      // 已停止或正在停止，直接忽略
      if (!this.status.running || this.stopping) return

      // ① 前端立即更新（你要的“立刻刷新”）
      this.stopping = true
      this.status.running = false
      this.stopPolling()

      // ② 通知后端（慢也不影响前端）
      try {
        await axios.post("http://127.0.0.1:5000/stop")
      } catch (err) {
        // 后端 400 / 已停止，都视为成功
        console.warn("stop 返回异常，已按停止状态处理")
      } finally {
        this.stopping = false
      }
    },

    async fetchStatus(showText = false) {
      try {
        const res = await axios.get("http://127.0.0.1:5000/status")

        // ⛔ 停止过程中，不允许后端状态覆盖前端
        if (!this.stopping) {
          this.status = res.data
        }
      } catch (err) {
        this.status.error = "获取状态失败"
      }
    },

    startPolling() {
      if (this.timer) return
      this.timer = setInterval(() => {
        this.fetchStatus()
      }, 1000)
    },

    stopPolling() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    }
  },
  mounted() {
    this.fetchStatus()
  },
  beforeUnmount() {
    this.stopPolling()
  }
}
</script>

<style scoped>
.publish-container {
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 6px;
  max-width: 420px;
}

.buttons {
  margin-bottom: 15px;
}

button {
  margin-right: 10px;
  padding: 6px 12px;
}

.status p {
  margin: 6px 0;
}

.progress-area {
  margin-top: 10px;
}

progress {
  width: 100%;
  height: 18px;
}

.progress-text {
  margin-top: 6px;
  font-size: 14px;
}

.error {
  color: red;
}
</style>
