// RecruitRadar — store.js
// Global reactive auth store using Vue.reactive().
// JWT token stored under key "rr_token" in localStorage.

/**
 * @typedef {Object} AuthUser
 * @property {number}  user_id        - DB user ID
 * @property {string}  email          - User email
 * @property {string}  role           - 'admin' | 'company' | 'student'
 * @property {string}  [full_name]    - Student/admin display name
 * @property {string}  [company_name] - Company display name
 */

/** @type {{ token: string|null, user: AuthUser|null, loading: boolean, alertMsg: string|null, alertType: string }} */
const rrStore = Vue.reactive({
  token: localStorage.getItem('rr_token') || null,
  user: JSON.parse(localStorage.getItem('rr_user') || 'null'),
  loading: false,
  alertMsg: null,
  alertType: 'success',
})

/**
 * Persist auth after login.
 * @param {string}   token
 * @param {AuthUser} user
 */
function rrSetAuth(token, user) {
  rrStore.token = token
  rrStore.user = user
  localStorage.setItem('rr_token', token)
  localStorage.setItem('rr_user', JSON.stringify(user))
}

/** Clear auth on logout. */
function rrClearAuth() {
  rrStore.token = null
  rrStore.user = null
  localStorage.removeItem('rr_token')
  localStorage.removeItem('rr_user')
}

/**
 * Show a timed global alert.
 * @param {string} msg
 * @param {'success'|'danger'|'warning'|'info'} [type='success']
 */
function rrShowAlert(msg, type = 'success') {
  rrStore.alertMsg = msg
  rrStore.alertType = type
  setTimeout(() => { rrStore.alertMsg = null }, 4000)
}

/** @returns {boolean} */
function rrIsLoggedIn() { return !!rrStore.token && !!rrStore.user }

/** @returns {string|null} */
function rrRole() { return rrStore.user ? rrStore.user.role : null }
