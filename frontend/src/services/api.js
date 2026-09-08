import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const submitChargingRequest = (data) => api.post('/charging/request', data)
export const getSchedule = (params) => api.get('/charging/schedule', { params })
export const runScheduler = (data) => api.post('/scheduler/run', data)
export const getVehicles = () => api.get('/vehicles')
export const getChargers = () => api.get('/chargers')
export const getEnergy = () => api.get('/energy')
export const adminOverride = (data) => api.post('/admin/override', data)
export const getAuditLog = (limit = 50) => api.get('/admin/audit-log', { params: { limit } })
export const getMetrics = (policy) => api.get('/metrics', { params: { policy } })
export const compareExperiments = () => api.get('/experiment/compare')
export const runScenario = (data) => api.post('/simulation/scenario', data)
export const getCampusConfig = () => api.get('/campus/config')
export const updateCampusConfig = (params) => api.put('/campus/config', null, { params })

export default api
