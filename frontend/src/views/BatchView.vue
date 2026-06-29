<template>
  <div class="container">
    <div class="page-title">
      <h1>批量批改</h1>
      <p>扫描指定日期目录中的作文图片，自动识别并批改</p>
    </div>

    <div class="card">
      <div class="card-title">扫描设置</div>
      <el-form :inline="true" :model="form">
        <el-form-item label="日期">
          <el-input v-model="form.date" placeholder="YYYYMMDD" />
        </el-form-item>
        <el-form-item label="OCR 引擎">
          <el-select v-model="form.ocr_engine" style="width: 150px">
            <el-option label="Kimi 视觉识别" value="kimi" />
            <el-option label="百度手写 OCR" value="baidu" />
            <el-option label="腾讯手写 OCR" value="tencent" />
          </el-select>
        </el-form-item>
        <el-form-item label="文体">
          <el-select v-model="form.genre" clearable placeholder="不选择" style="width: 150px">
            <el-option label="不选择" value="" />
            <el-option label="记叙文" value="narrative" />
            <el-option label="议论文" value="argumentation" />
            <el-option label="说明文" value="description" />
            <el-option label="散文" value="prose" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="scanning" @click="handleScan">
            扫描并批改
          </el-button>
          <el-button @click="setToday">今天</el-button>
        </el-form-item>
      </el-form>
      <el-alert
        title="文件命名规则"
        type="info"
        :closable="false"
        description="单张图片：人名_作文题目.jpg，例如：张三_我的家乡.jpg。多张图片：人名_作文题目_序号.jpg，例如：张三_我的家乡_1.jpg、张三_我的家乡_2.jpg，同一姓名题目下最多3张，按序号从小到大组成一篇文章。扫描目录：/mnt/hgfs/vm_share/workspace/essay-correction/YYYYMMDD/"
      />
    </div>

    <div v-if="task.status" class="card">
      <div class="card-title">任务进度</div>
      <el-steps :active="stepActive" finish-status="success">
        <el-step title="扫描目录" />
        <el-step title="识别批改" />
        <el-step title="完成" />
      </el-steps>
      <div style="margin-top: 20px">
        <p>状态：{{ task.status === 'processing' ? '处理中' : task.status === 'done' ? '完成' : task.status }}</p>
        <p>总数：{{ task.total }}，已完成：{{ task.completed }}，失败：{{ task.failed }}</p>
        <p v-if="task.message">{{ task.message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { scanBatch, getBatchTask } from '../api/essay'

const form = reactive({
  date: new Date().toISOString().slice(0, 10).replace(/-/g, ''),
  ocr_engine: 'kimi',
  genre: '',
})

const scanning = ref(false)
const task = reactive({
  task_id: '',
  status: '',
  total: 0,
  completed: 0,
  failed: 0,
  message: '',
})

const stepActive = computed(() => {
  if (!task.status) return 0
  if (task.status === 'pending') return 0
  if (task.status === 'processing') return 1
  if (task.status === 'done') return 3
  return 0
})

function setToday() {
  form.date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
}

async function pollTask(taskId) {
  const maxAttempts = 120
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await getBatchTask(taskId)
      const data = res.data
      task.status = data.status
      task.total = data.total
      task.completed = data.completed
      task.failed = data.failed
      task.message = data.message

      if (data.status === 'done' || data.status === 'failed') {
        scanning.value = false
        return
      }
    } catch (error) {
      console.error(error)
    }
    await new Promise((resolve) => setTimeout(resolve, 2000))
  }
  scanning.value = false
  ElMessage.warning('轮询超时')
}

async function handleScan() {
  if (!/^\d{8}$/.test(form.date)) {
    ElMessage.warning('日期格式错误，请使用 YYYYMMDD')
    return
  }

  scanning.value = true
  try {
    const res = await scanBatch(form.date, form.ocr_engine, form.genre || null, true)
    const data = res.data
    task.task_id = data.task_id
    task.status = data.status
    task.total = data.total
    task.completed = data.completed
    task.failed = data.failed
    task.message = data.message

    ElMessage.info(`扫描完成，共 ${data.total} 篇作文，开始批改...`)

    // 轮询任务状态
    await pollTask(data.task_id)

    if (task.status === 'done') {
      ElMessage.success('批量批改完成')
    }
  } catch (error) {
    console.error(error)
    const msg = error.response?.data?.detail || error.message || '扫描失败'
    ElMessage.error(msg)
    scanning.value = false
  }
}
</script>
