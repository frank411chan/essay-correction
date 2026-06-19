<template>
  <div ref="chartRef" class="radar-chart"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  scores: {
    type: Object,
    required: true,
  },
})

const chartRef = ref(null)
let chart = null

function initChart() {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()

  const resizeHandler = () => chart.resize()
  window.addEventListener('resize', resizeHandler)

  onUnmounted(() => {
    window.removeEventListener('resize', resizeHandler)
    chart.dispose()
  })
}

function updateChart() {
  if (!chart) return

  const indicator = [
    { name: '内容', max: 30 },
    { name: '结构', max: 20 },
    { name: '语言', max: 25 },
    { name: '书写', max: 25 },
  ]

  const data = [
    props.scores.content || 0,
    props.scores.structure || 0,
    props.scores.language || 0,
    props.scores.writing || 0,
  ]

  chart.setOption({
    tooltip: {
      trigger: 'item',
    },
    radar: {
      indicator,
      radius: '65%',
      splitNumber: 4,
      axisName: {
        color: '#606266',
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: data,
            name: '得分',
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.3)',
            },
            lineStyle: {
              color: '#409eff',
            },
            itemStyle: {
              color: '#409eff',
            },
          },
        ],
      },
    ],
  })
}

watch(() => props.scores, updateChart, { deep: true })

onMounted(initChart)
</script>

<style scoped>
.radar-chart {
  width: 100%;
  height: 320px;
}
</style>
