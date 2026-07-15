// RecruitRadar — pages/AdminDashboard.js

const AdminDashboard = {
  name: 'AdminDashboard',
  template: `
    <div class="container py-4">
      <h4 class="fw-bold mb-4"><i class="bi bi-speedometer2 me-2 text-primary"></i>Admin Dashboard</h4>
      <alert-msg></alert-msg>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary"></div>
      </div>

      <div v-else>
        <!-- Stat cards -->
        <div class="row g-3 mb-4">
          <div class="col-6 col-md-3" v-for="s in stats" :key="s.label">
            <div class="card rr-card rr-stat-card p-3">
              <div class="d-flex align-items-center gap-3">
                <i :class="s.icon" style="font-size:1.8rem;color:var(--rr-primary);"></i>
                <div>
                  <div class="fs-4 fw-bold">{{ s.value }}</div>
                  <div class="text-muted small">{{ s.label }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pending approvals — two columns -->
        <div class="row g-4 mb-4">
          <div class="col-md-6">
            <div class="card rr-card p-3 h-100">
              <h6 class="fw-bold mb-3">
                <i class="bi bi-building me-2 text-warning"></i>Pending Company Approvals ({{ pendingCompanies.length }})
              </h6>
              <div v-if="pendingCompanies.length===0" class="text-muted small text-center py-3">
                No pending companies.
              </div>
              <div v-for="c in pendingCompanies" :key="c.id" class="border-bottom py-2">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <div class="fw-semibold">{{ c.company_name }}</div>
                    <div class="text-muted small">{{ c.email }} &bull; {{ c.industry || '—' }}</div>
                  </div>
                  <div class="d-flex gap-1">
                    <button class="btn btn-success btn-sm" @click="approveCompany(c.id)">Approve</button>
                    <button class="btn btn-danger btn-sm" @click="rejectCompany(c.id)">Reject</button>
                  </div>
                </div>
                <button class="btn btn-link btn-sm ps-0" @click="c._expanded = !c._expanded">
                  {{ c._expanded ? 'Hide Details' : 'View Full Details' }}
                  <i :class="c._expanded ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                </button>
                <div v-if="c._expanded" class="p-2 bg-light rounded small">
                  <div><strong>Location:</strong> {{ c.location || '—' }}</div>
                  <div><strong>Website:</strong> {{ c.website || '—' }}</div>
                  <div><strong>HR Contact:</strong> {{ c.hr_contact || '—' }}</div>
                  <div><strong>Description:</strong> {{ c.description || 'No description provided.' }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-md-6">
            <div class="card rr-card p-3 h-100">
              <h6 class="fw-bold mb-3">
                <i class="bi bi-briefcase me-2 text-warning"></i>Pending Drive Approvals ({{ pendingDrives.length }})
              </h6>
              <div v-if="pendingDrives.length===0" class="text-muted small text-center py-3">
                No pending drives.
              </div>
              <div v-for="d in pendingDrives" :key="d.id" class="border-bottom py-2">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <div class="fw-semibold">{{ d.job_title }}</div>
                    <div class="text-muted small">{{ d.company_name }} &bull; Deadline: {{ fmtDate(d.deadline) }}</div>
                  </div>
                  <div class="d-flex gap-1">
                    <button class="btn btn-success btn-sm" @click="approveDrive(d.id)">Approve</button>
                    <button class="btn btn-danger btn-sm" @click="rejectDrive(d.id)">Reject</button>
                  </div>
                </div>
                <button class="btn btn-link btn-sm ps-0" @click="d._expanded = !d._expanded">
                  {{ d._expanded ? 'Hide Details' : 'View Full Details' }}
                  <i :class="d._expanded ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                </button>
                <div v-if="d._expanded" class="p-2 bg-light rounded small">
                  <div class="mb-1"><strong>Description:</strong></div>
                  <div class="mb-2" style="white-space:pre-line;">{{ d.job_description }}</div>
                  <div><strong>Skills:</strong> {{ d.skills_required || '—' }}</div>
                  <div><strong>Experience:</strong> {{ d.experience_required || '—' }}</div>
                  <div><strong>Salary:</strong> {{ d.salary || '—' }}</div>
                  <div><strong>Benefits:</strong> {{ d.benefits || '—' }}</div>
                  <div><strong>Min CGPA:</strong> {{ d.min_cgpa }} &bull; <strong>Branch:</strong> {{ d.eligible_branch || 'All' }} &bull; <strong>Year:</strong> {{ d.eligible_year || 'All' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick links -->
        <div class="row g-3 mt-2">
          <div class="col-md-3" v-for="link in quickLinks" :key="link.to">
            <router-link :to="link.to" class="btn btn-outline-primary w-100 py-3">
              <i :class="link.icon" class="d-block mb-1" style="font-size:1.4rem;"></i>
              {{ link.label }}
            </router-link>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      loading: true,
      data: {},
      stats: [],
      pendingCompanies: [],
      pendingDrives: [],
      quickLinks: [
        { to: '/admin/companies',    icon: 'bi bi-building',         label: 'Manage Companies' },
        { to: '/admin/students',     icon: 'bi bi-people',           label: 'Manage Students' },
        { to: '/admin/drives',       icon: 'bi bi-briefcase',        label: 'Manage Drives' },
        { to: '/admin/applications', icon: 'bi bi-file-earmark-text',label: 'All Applications' },
      ]
    }
  },
  async mounted() {
    await this.loadDashboard()
  },
  methods: {
    async loadDashboard() {
      this.loading = true
      try {
        const res = await rrApi.get('/api/admin/dashboard')
        this.data = res.data
        this.stats = [
          { label: 'Total Students',    value: res.data.total_students,    icon: 'bi bi-mortarboard' },
          { label: 'Total Companies',   value: res.data.total_companies,   icon: 'bi bi-building' },
          { label: 'Placement Drives',  value: res.data.total_drives,      icon: 'bi bi-briefcase' },
          { label: 'Total Applications',value: res.data.total_applications,icon: 'bi bi-file-earmark-text' },
          { label: 'Students Placed',   value: res.data.total_placed,      icon: 'bi bi-trophy' },
        ]
        await this.fetchPending()
      } catch (e) {
        rrShowAlert(rrGetError(e), 'danger')
      } finally {
        this.loading = false
      }
    },
    async fetchPending() {
      try {
        const [cRes, dRes] = await Promise.all([
          rrApi.get('/api/admin/companies', { params: { status: 'pending' } }),
          rrApi.get('/api/admin/drives',    { params: { status: 'pending' } }),
        ])
        this.pendingCompanies = cRes.data.map(c => ({ ...c, _expanded: false }))
        this.pendingDrives = dRes.data.map(d => ({ ...d, _expanded: false }))
      } catch (e) {
        rrShowAlert(rrGetError(e), 'danger')
      }
    },
    async approveCompany(id) {
      try {
        await rrApi.put(`/api/admin/companies/${id}/approve`)
        rrShowAlert('Company approved.', 'success')
        await this.loadDashboard()
      } catch (e) { rrShowAlert(rrGetError(e), 'danger') }
    },
    async rejectCompany(id) {
      try {
        await rrApi.put(`/api/admin/companies/${id}/reject`)
        rrShowAlert('Company rejected.', 'info')
        await this.loadDashboard()
      } catch (e) { rrShowAlert(rrGetError(e), 'danger') }
    },
    async approveDrive(id) {
      try {
        await rrApi.put(`/api/admin/drives/${id}/approve`)
        rrShowAlert('Drive approved.', 'success')
        await this.loadDashboard()
      } catch (e) { rrShowAlert(rrGetError(e), 'danger') }
    },
    async rejectDrive(id) {
      try {
        await rrApi.put(`/api/admin/drives/${id}/reject`)
        rrShowAlert('Drive rejected.', 'info')
        await this.loadDashboard()
      } catch (e) { rrShowAlert(rrGetError(e), 'danger') }
    },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—' }
  }
}