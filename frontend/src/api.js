import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120_000, // LLM can take a while
  headers: { 'Content-Type': 'application/json' },
})

/**
 * POST /api/query — send a natural-language question and get SQL + results.
 */
export async function askQuestion(question) {
  const { data } = await api.post('/query', { question })
  return data
}

/**
 * GET /api/schema/tables — list all tables with metadata.
 */
export async function fetchTables() {
  const { data } = await api.get('/schema/tables')
  return data.tables
}

/**
 * GET /api/schema/relationships — list all FK relationships.
 */
export async function fetchRelationships() {
  const { data } = await api.get('/schema/relationships')
  return data.relationships
}

/**
 * GET /api/health — server health check.
 */
export async function fetchHealth() {
  const { data } = await api.get('/health')
  return data
}

export default api
