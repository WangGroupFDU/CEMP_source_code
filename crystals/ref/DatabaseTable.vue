<template>
  <div class="content-section">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon>
          <component :is="titleIcon" />
        </el-icon>
        {{ title }}
      </h2>
      <p class="page-description">{{ description }}</p>
    </div>

    <el-card class="database-card">
      
      <div class="database-controls">
        <el-row :gutter="20" class="control-row">
          <el-col :span="8">
            <el-input
              :model-value="searchValue"
              :placeholder="searchPlaceholder"
              @input="$emit('search-change', $event)"
              clearable>
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="3">
            <el-select
              :model-value="pageSize"
              @change="$emit('page-size-change', $event)"
              style="width: 100%">
              <el-option label="10 / page" :value="10" />
              <el-option label="20 / page" :value="20" />
              <el-option label="50 / page" :value="50" />
              <el-option label="100 / page" :value="100" />
            </el-select>
          </el-col>
          <el-col :span="3">
            <el-button
              @click="$emit('export-data')"
              type="primary"
              :loading="exportLoading"
              style="width: 100%">
              <el-icon><Download /></el-icon>
              <span v-if="exportButtonText">{{ exportButtonText }}</span>
            </el-button>
          </el-col>
          <el-col :span="4">
            <el-button
              @click="openSmilesDialog"
              type="success"
              plain
              style="width: 100%">
              <el-icon><View /></el-icon>
              <span v-if="smilesButtonText">{{ smilesButtonText }}</span>
            </el-button>
          </el-col>
          <el-col :span="6" class="stats-info">
            <span v-if="total > 0" class="total-info">
              Total: {{ total }} entries
            </span>
          </el-col>
        </el-row>
      </div>

      
      <el-table
        :data="data"
        v-loading="loading"
        stripe
        border
        height="600"
        @sort-change="$emit('sort-change', $event)"
        style="width: 100%">

        
        <el-table-column
          v-for="column in responsiveColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :width="column.width"
          :min-width="column.minWidth"
          :sortable="column.sortable"
          :fixed="column.fixed"
          :show-overflow-tooltip="column.showOverflowTooltip">

          
          <template #default="scope" v-if="column.type === 'smiles'">
            <code class="smiles-code">{{ scope.row[column.prop] }}</code>
          </template>

          
          <template #default="scope" v-else>
            <span v-if="scope.row[column.prop] === '' || scope.row[column.prop] === null">
              -
            </span>
            <span v-else>
              {{ scope.row[column.prop] }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      
      <div class="pagination-wrapper">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="$emit('page-size-change', $event)"
          @current-change="$emit('current-change', $event)"
        />
      </div>
    </el-card>

    
    <el-dialog
      v-model="smilesDialogVisible"
      title="SMILES 2D Render"
      width="600px"
      :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="SMILES式">
          <el-input
            v-model="smilesInput"
            placeholder="请输入SMILES式，例如: CCO"
            clearable
            @keyup.enter="renderSmiles">
            <template #append>
              <el-button
                type="primary"
                @click="renderSmiles"
                :loading="renderLoading">
                Render
              </el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="分子结构">
          <div class="smiles-structure-container">
            <canvas
              ref="moleculeCanvas"
              width="450"
              height="400"
              class="molecule-canvas">
            </canvas>
          </div>
        </el-form-item>

        <el-form-item v-if="!showStructure && !renderLoading">
          <el-alert
            title="请输入SMILES式并点击渲染按钮查看分子结构"
            type="info"
            :closable="false"
            show-icon />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="closeSmilesDialog">Close</el-button>
        <el-button type="primary" @click="clearStructure">Clear</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, Download, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'


const props = defineProps({
  title: {
    type: String,
    required: true
  },
  titleIcon: {
    type: [String, Object],
    required: true
  },
  description: {
    type: String,
    required: true
  },
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  searchValue: {
    type: String,
    default: ''
  },
  searchPlaceholder: {
    type: String,
    default: 'Search...'
  },
  total: {
    type: Number,
    default: 0
  },
  currentPage: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 20
  },
  exportLoading: {
    type: Boolean,
    default: false
  },
  columns: {
    type: Array,
    required: true
  }
})


defineEmits([
  'search-change',
  'page-size-change',
  'current-change',
  'sort-change',
  'export-data'
])


const smilesDialogVisible = ref(false)
const smilesInput = ref('')
const showStructure = ref(false)
const renderLoading = ref(false)
const moleculeCanvas = ref(null)
let rdkitModule = null


const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value <= 768)


const exportButtonText = computed(() => {
  if (windowWidth.value < 500) return ''
  if (windowWidth.value < 1300) return 'Export'
  return 'Export CSV'
})

const smilesButtonText = computed(() => {
  if (windowWidth.value < 500) return ''
  if (windowWidth.value < 1300) return '2D Render'
  return 'SMILES 2D Render'
})


const responsiveColumns = computed(() => {
  if (isMobile.value) {

    return props.columns.map(col => {
      const { fixed, ...rest } = col
      return rest
    })
  }
  return props.columns
})


const handleResize = () => {
  windowWidth.value = window.innerWidth
}


onMounted(async () => {
  await initializeRDKit()

  window.addEventListener('resize', handleResize)
})


onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const initializeRDKit = async () => {
  try {
    const baseUrl = import.meta.env.BASE_URL
    console.log('Initializing RDKit from:', baseUrl + 'RDKit_minimal.wasm')

    rdkitModule = await window.initRDKitModule({
      locateFile: () => baseUrl + 'RDKit_minimal.wasm'
    })

    console.log('RDKit module loaded successfully')
  } catch (error) {
    console.error('RDKit initialization failed:', error)
    ElMessage.error(`RDKit初始化失败: ${error.message}`)
  }
}


const openSmilesDialog = () => {
  smilesDialogVisible.value = true
}


const closeSmilesDialog = () => {
  smilesDialogVisible.value = false
}


const renderSmiles = async () => {
  if (!rdkitModule) {
    ElMessage.error('RDKit模块未初始化')
    return
  }

  if (!smilesInput.value.trim()) {
    ElMessage.warning('请输入SMILES式')
    return
  }

  try {
    renderLoading.value = true

    const mol = rdkitModule.get_mol(smilesInput.value.trim())

    if (!mol || !mol.is_valid()) {
      throw new Error('无效的SMILES字符串')
    }

    const canvas = moleculeCanvas.value
    if (!canvas) {
      throw new Error('Canvas元素未找到')
    }

    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const svg = mol.get_svg(450, 400)

    const img = new Image()
    const svgBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(svgBlob)

    img.onload = () => {
      ctx.drawImage(img, 0, 0)
      URL.revokeObjectURL(url)
      showStructure.value = true
      renderLoading.value = false
      ElMessage.success('分子结构渲染成功')
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      throw new Error('SVG图像加载失败')
    }

    img.src = url
    mol.delete()

  } catch (error) {
    console.error('SMILES rendering error:', error)
    ElMessage.error(`渲染失败: ${error.message}`)
    showStructure.value = false
    renderLoading.value = false
  }
}


const clearStructure = () => {
  smilesInput.value = ''
  showStructure.value = false
  const canvas = moleculeCanvas.value
  if (canvas) {
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}
</script>

<style scoped>
.database-card {
  margin-bottom: 1rem;
}

.database-controls {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
}

.control-row {
  align-items: center;
}

.stats-info {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.total-info {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 0.5rem;
}

.smiles-code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: #2c3e50;
  border: 1px solid #e4e7ed;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-title {
  display: flex;
  align-items: center;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.page-title .el-icon {
  margin-right: 0.5rem;
  font-size: 1.25rem;
}

.page-description {
  color: #606266;
  font-size: 0.875rem;
  margin: 0;
}


:deep(.el-table__header) {
  background-color: #f1f5f9;
}

:deep(.el-table__header th) {
  background-color: #f1f5f9;
  color: #334155;
  font-weight: 600;
}

:deep(.el-table__row:hover) {
  background-color: #f8fafc;
}

:deep(.el-table__fixed-right) {
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-table__fixed) {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}


.smiles-structure-container {
  width: 90%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
}

.molecule-canvas {
  border: 1px solid #ccc;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}


@media (max-width: 768px) {
  .control-row .el-col {
    margin-bottom: 0.5rem;
  }

  :deep(.el-table) {
    font-size: 0.875rem;
  }

  
  :deep(.el-table__fixed),
  :deep(.el-table__fixed-right) {
    box-shadow: none;
  }

  
  .database-card :deep(.el-card__body) {
    overflow-x: auto;
  }

  :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
}
</style>
