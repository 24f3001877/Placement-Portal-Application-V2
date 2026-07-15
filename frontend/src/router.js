// RecruitRadar — router.js
// Vue Router 4 configuration with role-based navigation guards.
// All route guards check rrStore.user.role before allowing access.

const { createRouter, createWebHashHistory } = VueRouter

const routes = [
  { path: '/',                         component: LandingPage },
  { path: '/login',                    component: LoginPage },

  // Admin routes (role='admin' required)
  { path: '/admin/dashboard',          component: AdminDashboard,    meta: { role: 'admin' } },
  { path: '/admin/companies',          component: AdminCompanies,    meta: { role: 'admin' } },
  { path: '/admin/students',           component: AdminStudents,     meta: { role: 'admin' } },
  { path: '/admin/drives',             component: AdminDrives,       meta: { role: 'admin' } },
  { path: '/admin/applications',       component: AdminApplications, meta: { role: 'admin' } },

  // Company routes (role='company' required)
  { path: '/company/dashboard',        component: CompanyDashboard,     meta: { role: 'company' } },
  { path: '/company/drives',           component: CompanyDrives,        meta: { role: 'company' } },
  { path: '/company/applications/:id', component: CompanyApplications,  meta: { role: 'company' } },

  // Student routes (role='student' required)
  { path: '/student/dashboard',        component: StudentDashboard,  meta: { role: 'student' } },
  { path: '/student/profile',          component: StudentProfile,    meta: { role: 'student' } },
  { path: '/student/history',          component: StudentHistory,    meta: { role: 'student' } },
  { path: '/student/ats-check',        component: StudentATS,        meta: { role: 'student' } },

  // Catch-all redirect
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  // Hash history: URLs look like http://localhost:5000/#/login
  // Flask never sees the # part — it always serves index.html for /
  // This avoids the catch-all conflict with static file serving.
  history: createWebHashHistory(),
  routes,
})

// ── Navigation guard: role-based access control
router.beforeEach((to, from, next) => {
  const requiredRole = to.meta.role

  if (!requiredRole) {
    // Public route — allow always
    return next()
  }

  if (!rrIsLoggedIn()) {
    // Not logged in — send to login
    return next('/login')
  }

  const currentRole = rrRole()
  if (currentRole !== requiredRole) {
    // Wrong role — redirect to their own dashboard
    const redirects = { admin: '/admin/dashboard', company: '/company/dashboard', student: '/student/dashboard' }
    return next(redirects[currentRole] || '/')
  }

  next()
})

// Expose router on window so api.js interceptor can redirect on 401

window.__rrRouter__ = router
