// RecruitRadar — api.js
// Axios wrapper — attaches rr_token JWT to every request header.

const rrApi = axios.create({ baseURL: '', headers: { 'Content-Type': 'application/json' } })

rrApi.interceptors.request.use((config) => {
  const token = rrStore.token
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

rrApi.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401) {
      rrClearAuth()
      if (window.__rrRouter__) window.__rrRouter__.push('/login')
    }
    return Promise.reject(err)
  }
)

/**
 * Extract readable error message from Axios error.
 * @param {any} err
 * @param {string} [fallback]
 * @returns {string}
 */
function rrGetError(err, fallback = 'Something went wrong. Please try again.') {
  if (err.response && err.response.data) {
    return err.response.data.error || err.response.data.message || fallback
  }
  return fallback
}
