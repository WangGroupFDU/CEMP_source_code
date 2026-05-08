<template>
  <div class="prediction-page">
    <div class="page-header">
      <h2 class="page-title">Crystal Property Prediction</h2>
      <p class="page-desc">
        Predict average voltage (V), gravimetric capacity (mAh/g), and gravimetric energy density (mWh/g) of crystals.
        Applicable domain: crystals containing Li, Na, Mg, Ca, K, Zn, and Al.
      </p>
    </div>

    <el-card shadow="never" class="upload-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="Model">
          <el-select v-model="modelType" style="width: 180px">
            <el-option label="MOCO+GAT" value="MOCO+GAT" />
            <el-option label="GAT" value="GAT" />
            <el-option label="GCN" value="GCN" />
          </el-select>
        </el-form-item>
        <el-form-item label="CIF File">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".cif"
            :on-change="handleFileChange"
            :on-remove="() => (cifFile = null)"
          >
            <template #trigger>
              <el-button type="primary" :icon="Upload">Choose CIF</el-button>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button
            type="success"
            :icon="Promotion"
            :loading="predicting"
            :disabled="!cifFile"
            @click="predict"
          >
            Predict
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" shadow="never" class="result-card">
      <template #header>
        <span style="font-weight: 600;">Prediction Results</span>
      </template>
      <el-table :data="[result]" border stripe style="width: 100%">
        <el-table-column prop="average_voltage" label="Average Voltage (V)" align="center">
          <template #default="{ row }">
            {{ formatResult(row.average_voltage) }}
          </template>
        </el-table-column>
        <el-table-column prop="capacity_grav" label="Gravimetric Capacity (mAh/g)" align="center">
          <template #default="{ row }">
            {{ formatResult(row.capacity_grav) }}
          </template>
        </el-table-column>
        <el-table-column prop="energy_grav" label="Gravimetric Energy (mWh/g)" align="center">
          <template #default="{ row }">
            {{ formatResult(row.energy_grav) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" class="accuracy-card">
      <template #header>
        <span style="font-weight: 600;">Model Accuracy (Test Dataset)</span>
      </template>
      <el-table :data="accuracyModels" border style="width: 100%">
        <el-table-column prop="name" label="Model" width="140" align="center" />
        <el-table-column label="Average Voltage Accuracy" align="center">
          <template #default="{ row }">
            <img :src="accuracyImg('average_voltage', row.name)" class="accuracy-img" />
          </template>
        </el-table-column>
        <el-table-column label="Gravimetric Capacity Accuracy" align="center">
          <template #default="{ row }">
            <img :src="accuracyImg('capacity_grav', row.name)" class="accuracy-img" />
          </template>
        </el-table-column>
        <el-table-column label="Gravimetric Energy Accuracy" align="center">
          <template #default="{ row }">
            <img :src="accuracyImg('energy_grav', row.name)" class="accuracy-img" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const modelType = ref('MOCO+GAT')
const cifFile = ref(null)
const predicting = ref(false)
const result = ref(null)
const uploadRef = ref(null)

const accuracyModels = [
  { name: 'MOCO+GAT' },
  { name: 'GAT' },
  { name: 'GCN' },
]

function accuracyImg(metric, model) {
  return `/static/images/${metric}_${model}.png`
}

function handleFileChange(file) {
  cifFile.value = file.raw
}

function formatResult(val) {
  if (Array.isArray(val)) {
    const inner = Array.isArray(val[0]) ? val[0][0] : val[0]
    return typeof inner === 'number' ? inner.toFixed(4) : inner
  }
  return typeof val === 'number' ? val.toFixed(4) : val
}

async function predict() {
  if (!cifFile.value) {
    ElMessage.warning('Please choose a CIF file first')
    return
  }
  predicting.value = true
  result.value = null
  try {
    const formData = new FormData()
    formData.append('modelSelect', modelType.value)
    formData.append('cifFile', cifFile.value)
    const res = await axios.post('/crystals/crystal_prediction_upload/', formData)
    if (res.data.error) {
      ElMessage.error(res.data.error)
    } else {
      result.value = res.data
      ElMessage.success('Prediction completed')
    }
  } catch (e) {
    ElMessage.error('Prediction failed: ' + (e.response?.data?.error || e.message))
  } finally {
    predicting.value = false
  }
}
</script>

<style scoped>
.prediction-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header { margin-bottom: 4px; }
.page-title { font-size: 22px; font-weight: 600; color: #1d2129; }
.page-desc { margin-top: 6px; color: #86909c; font-size: 14px; line-height: 1.6; }
.upload-card { --el-card-padding: 20px; }
.result-card { --el-card-padding: 20px; }
.accuracy-card { --el-card-padding: 20px; }
.accuracy-img {
  max-width: 200px;
  height: auto;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}
</style>
