import axios from 'axios'

const api = axios.create({
  baseURL: '/crystals/api/',
  timeout: 30000,
})

export function getCrystalList() {
  return api.get('crystal_list/')
}

export function getCrystalData(crystal) {
  return api.get('crystal_data/', { params: { crystal } })
}

export function uploadPrediction(formData) {
  return api.post('crystal_predict_excel/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}
