<template>
  <div class="database-page">
    <div class="page-header">
      <h2 class="page-title">Crystal Database</h2>
      <p class="page-desc">Browse crystal data from Materials Project. Select a crystal type and explore properties.</p>
    </div>

    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="toolbar-label">Crystal Type:</span>
          <el-select
            v-model="selectedCrystal"
            placeholder="Select crystal"
            @change="fetchData"
            style="width: 160px"
          >
            <el-option
              v-for="t in crystalTypes"
              :key="t"
              :label="t"
              :value="t"
            />
          </el-select>

          <el-input
            v-model="searchText"
            placeholder="Search..."
            clearable
            style="width: 260px; margin-left: 16px;"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="toolbar-right">
          <el-tag type="info" effect="plain" size="large">
            {{ filteredData.length }} records
          </el-tag>
          <el-button type="success" :icon="Download" @click="exportCSV" :loading="exporting">
            Export CSV
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table
        :data="paginatedData"
        stripe
        border
        :height="tableHeight"
        v-loading="loading"
        @sort-change="handleSortChange"
        style="width: 100%"
        size="small"
      >
        <el-table-column
          v-for="field in fieldNames"
          :key="field"
          :prop="field"
          :label="formatLabel(field)"
          :sortable="'custom'"
          :min-width="columnWidth(field)"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span v-if="row[field] === null || row[field] === undefined || row[field] === ''">
              <el-tag type="info" size="small" effect="plain">N/A</el-tag>
            </span>
            <span v-else>{{ formatValue(row[field]) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[25, 50, 100, 200]"
        :total="filteredData.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="currentPage = 1"
        @current-change="() => {}"
        style="margin-top: 16px; justify-content: center;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getCrystalList, getCrystalData } from '../api/crystal'

const crystalTypes = ref([])
const selectedCrystal = ref('Al')
const fieldNames = ref([])
const tableData = ref([])
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(25)
const loading = ref(false)
const exporting = ref(false)
const sortProp = ref('')
const sortOrder = ref('')
const tableHeight = ref(560)

const filteredData = computed(() => {
  let data = tableData.value
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    data = data.filter(row =>
      fieldNames.value.some(f => {
        const v = row[f]
        if (v === null || v === undefined) return false
        return String(v).toLowerCase().includes(q)
      })
    )
  }
  if (sortProp.value && sortOrder.value) {
    const prop = sortProp.value
    const asc = sortOrder.value === 'ascending'
    data = [...data].sort((a, b) => {
      const va = a[prop], vb = b[prop]
      if (va === null || va === undefined) return 1
      if (vb === null || vb === undefined) return -1
      if (typeof va === 'number' && typeof vb === 'number') {
        return asc ? va - vb : vb - va
      }
      return asc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va))
    })
  }
  return data
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

function handleSortChange({ prop, order }) {
  sortProp.value = prop
  sortOrder.value = order
}

function formatLabel(field) {
  return field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatValue(val) {
  if (typeof val === 'number') {
    return Number.isInteger(val) ? val : val.toFixed(4)
  }
  return val
}

function columnWidth(field) {
  if (field === 'label' || field === 'formula_pretty') return 160
  if (field.startsWith('is_') || field === 'deprecated' || field === 'theoretical') return 100
  return 130
}

async function fetchCrystalTypes() {
  try {
    const res = await getCrystalList()
    crystalTypes.value = res.data.crystal_types
    if (crystalTypes.value.length && !crystalTypes.value.includes(selectedCrystal.value)) {
      selectedCrystal.value = crystalTypes.value[0]
    }
  } catch (e) {
    ElMessage.error('Failed to load crystal types')
  }
}

async function fetchData() {
  loading.value = true
  currentPage.value = 1
  try {
    const res = await getCrystalData(selectedCrystal.value)
    fieldNames.value = res.data.field_names
    tableData.value = res.data.data
  } catch (e) {
    ElMessage.error('Failed to load crystal data')
  } finally {
    loading.value = false
  }
}

function exportCSV() {
  exporting.value = true
  try {
    const rows = filteredData.value
    const header = fieldNames.value.join(',')
    const body = rows.map(row =>
      fieldNames.value.map(f => {
        const v = row[f]
        if (v === null || v === undefined) return ''
        return `"${String(v).replace(/"/g, '""')}"`
      }).join(',')
    ).join('\n')
    const csv = header + '\n' + body
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `crystal_${selectedCrystal.value}_data.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    ElMessage.success('CSV exported successfully')
  } catch (e) {
    ElMessage.error('Export failed: ' + e.message)
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await fetchCrystalTypes()
  await fetchData()
})
</script>

<style scoped>
.database-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  margin-bottom: 4px;
}
.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
}
.page-desc {
  margin-top: 6px;
  color: #86909c;
  font-size: 14px;
}
.toolbar-card {
  --el-card-padding: 16px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.toolbar-label {
  font-weight: 500;
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}
.table-card {
  --el-card-padding: 16px;
}
</style>
