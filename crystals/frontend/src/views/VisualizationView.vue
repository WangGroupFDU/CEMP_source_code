<template>
  <div class="viz-page">
    <div class="page-header">
      <h2 class="page-title">Crystal Structure Visualization</h2>
      <p class="page-desc">
        Upload a structure file (.cif, .mol2, .pdb, .xyz, .out) to visualize the 3D crystal structure using JSmol.
      </p>
    </div>

    <el-card shadow="never" class="upload-card">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".cif,.mol2,.pdb,.xyz,.out"
        :on-change="handleFileChange"
        :on-remove="handleRemove"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload" :size="48"><UploadFilled /></el-icon>
        <div class="el-upload__text">Drop file here or <em>click to browse</em></div>
        <template #tip>
          <div class="el-upload__tip">Supported formats: .cif, .mol2, .pdb, .xyz, .out</div>
        </template>
      </el-upload>
      <div style="margin-top: 12px; text-align: center;">
        <el-button
          type="primary"
          :icon="View"
          :loading="uploading"
          :disabled="!selectedFile"
          @click="uploadAndVisualize"
          size="large"
        >
          Upload &amp; Visualize
        </el-button>
      </div>
    </el-card>

    <el-card v-if="fileUrl" shadow="never" class="viewer-card">
      <template #header>
        <span style="font-weight: 600;">3D Structure Viewer</span>
      </template>
      <div ref="jsmolContainer" class="jsmol-container"></div>
    </el-card>

    <el-alert
      v-if="errorMsg"
      :title="errorMsg"
      type="error"
      show-icon
      closable
      @close="errorMsg = ''"
      style="margin-top: 16px;"
    />
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { UploadFilled, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const selectedFile = ref(null)
const fileList = ref([])
const uploading = ref(false)
const fileUrl = ref('')
const errorMsg = ref('')
const jsmolContainer = ref(null)
const uploadRef = ref(null)
let jsmolReady = false

function handleFileChange(file) {
  selectedFile.value = file.raw
}

function handleRemove() {
  selectedFile.value = null
}

function loadJSmolScripts() {
  return new Promise((resolve) => {
    if (window.Jmol) {
      resolve()
      return
    }
    const scripts = [
      '/static/jsmol/JSmol.min.js',
      '/static/jsmol/js/JSmolJME.js',
    ]
    let loaded = 0
    scripts.forEach(src => {
      const s = document.createElement('script')
      s.src = src
      s.onload = () => {
        loaded++
        if (loaded === scripts.length) resolve()
      }
      s.onerror = () => {
        loaded++
        if (loaded === scripts.length) resolve()
      }
      document.head.appendChild(s)
    })
  })
}

async function uploadAndVisualize() {
  if (!selectedFile.value) return
  uploading.value = true
  errorMsg.value = ''
  fileUrl.value = ''

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const csrfToken = getCookie('csrftoken')
    const res = await axios.post('/crystals/crystal_structure_visualization_upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      },
      responseType: 'text',
    })

    const html = res.data
    const match = html.match(/var fileUrl = "([^"]+)"/)
    if (match && match[1]) {
      fileUrl.value = match[1]
      await nextTick()
      renderJSmol(fileUrl.value)
      ElMessage.success('Structure loaded successfully')
    } else if (html.includes('alert-danger')) {
      errorMsg.value = 'Upload failed. Please check your file format.'
    } else {
      errorMsg.value = 'Could not extract file URL from server response.'
    }
  } catch (e) {
    errorMsg.value = 'Upload failed: ' + (e.response?.statusText || e.message)
  } finally {
    uploading.value = false
  }
}

function renderJSmol(url) {
  if (!window.Jmol || !jsmolContainer.value) {
    errorMsg.value = 'JSmol library not loaded. Visualization may not work in SPA mode.'
    return
  }
  const info = {
    width: '100%',
    height: 600,
    debug: false,
    color: 'white',
    use: 'HTML5',
    j2sPath: '/static/jsmol/j2s',
    console: 'none',
    script: `set antialiasDisplay true; set antialiasTranslucent true; set highResolution true; load '${url}';`,
  }
  const applet = window.Jmol.getApplet('jmolApplet0', info)
  jsmolContainer.value.innerHTML = window.Jmol.getAppletHtml(applet)
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? match[2] : null
}

onMounted(async () => {
  await loadJSmolScripts()
  jsmolReady = true
})
</script>

<style scoped>
.viz-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header { margin-bottom: 4px; }
.page-title { font-size: 22px; font-weight: 600; color: #1d2129; }
.page-desc { margin-top: 6px; color: #86909c; font-size: 14px; line-height: 1.6; }
.upload-card { --el-card-padding: 24px; }
.viewer-card { --el-card-padding: 16px; }
.jsmol-container {
  width: 100%;
  min-height: 600px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}
</style>
