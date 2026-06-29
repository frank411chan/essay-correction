<template>
  <div class="card">
    <div class="card-title">上传作文图片</div>

    <el-form :model="form" label-position="top">
      <el-form-item label="选择学生" required>
        <el-select-v2
          v-model="form.student_id"
          :options="studentOptions"
          placeholder="请选择或搜索学生"
          filterable
          clearable
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="作文标题">
        <el-input v-model="form.title" placeholder="请输入作文标题（可选）" />
      </el-form-item>

      <el-form-item label="年级">
        <el-select v-model="form.grade" placeholder="请选择年级" style="width: 100%">
          <el-option label="小学" value="小学" />
          <el-option label="初中" value="初中" />
          <el-option label="高中" value="高中" />
          <el-option label="大学/成人" value="大学/成人" />
        </el-select>
      </el-form-item>

      <el-form-item label="OCR 识别引擎">
        <el-radio-group v-model="form.ocr_engine">
          <el-radio label="kimi">Kimi 视觉识别</el-radio>
          <el-radio label="baidu">百度手写 OCR</el-radio>
          <el-radio label="tencent">腾讯手写 OCR</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="文体模板">
        <el-select v-model="form.genre" placeholder="不选择则按通用要求批改" clearable style="width: 100%">
          <el-option label="不选择" value="" />
          <el-option label="记叙文" value="narrative" />
          <el-option label="议论文" value="argumentation" />
          <el-option label="说明文" value="description" />
          <el-option label="散文" value="prose" />
        </el-select>
      </el-form-item>

      <el-form-item label="作文图片" required>
        <el-upload
          class="upload-demo"
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleChange"
          :on-remove="handleRemove"
          :limit="3"
          multiple
          accept=".jpg,.jpeg,.png,.webp"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽图片到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 jpg/png/webp 格式，最多3张，每张不超过10MB。批量命名规则：姓名_题目_序号.jpg
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!form.files.length || !form.student_id"
          @click="submit"
          style="width: 100%"
        >
          {{ loading ? '正在批改...' : '开始批改' }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  students: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['submit'])

const form = reactive({
  student_id: null,
  title: '',
  grade: '初中',
  ocr_engine: 'kimi',
  genre: '',
  files: [],
})

const studentOptions = computed(() => {
  return props.students.map((s) => ({
    value: s.id,
    label: `${s.name}${s.class_name ? ' (' + s.class_name + ')' : ''}`,
  }))
})

function handleChange(file, fileList) {
  form.files = fileList.map((f) => f.raw)
}

function handleRemove(file, fileList) {
  form.files = fileList.map((f) => f.raw)
}

function submit() {
  emit('submit', { ...form })
}
</script>

<style scoped>
:deep(.el-upload-dragger) {
  width: 100%;
}
</style>
