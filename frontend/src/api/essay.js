import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

// ========== 作文接口 ==========

export function uploadEssay(formData) {
  return api.post('/essays/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export function correctEssay(id) {
  return api.post(`/essays/${id}/correct`)
}

export function getEssayStatus(id) {
  return api.get(`/essays/${id}/status`)
}

export function getEssay(id) {
  return api.get(`/essays/${id}`)
}

export function getEssayImageUrl(id) {
  return `/api/essays/${id}/image`
}

export function getEssayPdfUrl(id) {
  return `/api/essays/${id}/pdf`
}

export function listEssays(params = {}) {
  return api.get('/essays', { params })
}

// ========== 学生接口 ==========

export function listStudents(params = {}) {
  return api.get('/students', { params })
}

export function createStudent(data) {
  return api.post('/students', data)
}

export function updateStudent(id, data) {
  return api.put(`/students/${id}`, data)
}

export function deleteStudent(id) {
  return api.delete(`/students/${id}`)
}

// ========== 批量批改接口 ==========

export function scanBatch(date, ocrEngine = 'kimi', genre = 'narrative', autoCorrect = true) {
  return api.post('/batch/scan', null, {
    params: { date, ocr_engine: ocrEngine, genre, auto_correct: autoCorrect },
  })
}

export function scanToday(ocrEngine = 'kimi', genre = 'narrative', autoCorrect = true) {
  return api.post('/batch/today', null, {
    params: { ocr_engine: ocrEngine, genre, auto_correct: autoCorrect },
  })
}

export function getBatchTask(taskId) {
  return api.get(`/batch/tasks/${taskId}`)
}
