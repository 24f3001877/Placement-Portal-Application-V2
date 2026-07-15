// RecruitRadar — pages/StudentDashboard.js
// Student home: shows approved drives with search/filter + apply button.
const StudentDashboard = {
  name: 'StudentDashboard',
  template: `
    <div class="container py-4">
      <h4 class="fw-bold mb-1"><i class="bi bi-mortarboard me-2 text-primary"></i>Student Dashboard</h4>
      <p class="text-muted mb-4">Welcome, <strong>{{ userName }}</strong> — browse and apply to placement drives below.</p>
      <alert-msg></alert-msg>

      <!-- Search & Filter -->
      <div class="card rr-card p-3 mb-4">
        <div class="row g-2 align-items-end">
          <div class="col-md-6">
            <label class="form-label small">Search Drives</label>
            <input class="form-control" v-model="search" placeholder="Job title, company, or skills..." />
          </div>
          <div class="col-md-3">
            <label class="form-label small">Filter by Branch</label>
            <select class="form-select" v-model="branchFilter">
              <option value="">All Branches</option>
              <option>CSE</option><option>ECE</option><option>EEE</option>
              <option>ME</option><option>CE</option><option>IT</option>
            </select>
          </div>
          <div class="col-md-3">
            <button class="btn btn-primary w-100" @click="fetchDrives">
              <i class="bi bi-search me-1"></i>Search
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

      <div v-else>
        <p class="text-muted small mb-3">{{ drives.length }} drive(s) available</p>
        <div v-if="drives.length===0" class="text-center text-muted py-5">
          <i class="bi bi-briefcase-x d-block mb-2" style="font-size:2rem;"></i>No drives match your search.
        </div>

        <div v-for="d in drives" :key="d.id" class="card rr-card mb-3 p-3">
          <div class="row align-items-center g-2">
            <div class="col-md-8">
              <h6 class="fw-bold mb-1">{{ d.job_title }}
                <span class="badge rr-badge-approved ms-2">Approved</span>
              </h6>
              <div class="text-muted small mb-1">
                <i class="bi bi-building me-1"></i>{{ d.company_name }}
                &bull; <i class="bi bi-calendar-x me-1"></i>Deadline: {{ fmtDate(d.deadline) }}
              </div>
              <div class="text-muted small">
                <span v-if="d.salary" class="me-3"><i class="bi bi-cash me-1"></i>{{ d.salary }}</span>
                <span v-if="d.min_cgpa" class="me-3"><i class="bi bi-graph-up me-1"></i>Min CGPA: {{ d.min_cgpa }}</span>
                <span v-if="d.eligible_branch" class="me-3"><i class="bi bi-diagram-3 me-1"></i>{{ d.eligible_branch }}</span>
              </div>
              <div class="mt-2">
                <span v-if="d.skills_required" class="badge bg-light text-dark border me-1" 
                  v-for="skill in (d.skills_required||'').split(',')" :key="skill">{{ skill.trim() }}</span>
              </div>

              <!-- Expandable full details -->
              <button class="btn btn-link btn-sm ps-0 mt-2" @click="d._expanded = !d._expanded">
                {{ d._expanded ? 'Hide Details' : 'View Full Details' }}
                <i :class="d._expanded ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
              </button>
              <div v-if="d._expanded" class="mt-2 p-3 bg-light rounded">
                <div class="mb-2">
                  <div class="fw-semibold small text-muted">Job Description</div>
                  <div class="small" style="white-space:pre-line;">{{ d.job_description }}</div>
                </div>
                <div class="mb-2" v-if="d.experience_required">
                  <div class="fw-semibold small text-muted">Experience Required</div>
                  <div class="small">{{ d.experience_required }}</div>
                </div>
                <div class="mb-2" v-if="d.benefits">
                  <div class="fw-semibold small text-muted">Benefits</div>
                  <div class="small">{{ d.benefits }}</div>
                </div>
                <div v-if="d.eligible_year">
                  <div class="fw-semibold small text-muted">Eligible Year</div>
                  <div class="small">Year {{ d.eligible_year }}</div>
                </div>
              </div>
            </div>
            <div class="col-md-4 text-md-end">
              <div v-if="appliedIds.has(d.id)">
                <span :class="'badge rr-badge-'+getAppStatus(d.id)" style="font-size:0.85rem;">
                  {{ getAppStatus(d.id) }}
                </span>
              </div>
              <button v-else class="btn btn-primary" @click="apply(d.id)"
                :disabled="applying===d.id">
                <span v-if="applying===d.id" class="spinner-border spinner-border-sm me-1"></span>
                Apply Now
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return { drives: [], myApps: [], search: '', branchFilter: '', loading: true, applying: null }
  },
  computed: {
    userName() { return rrStore.user ? (rrStore.user.full_name || rrStore.user.email) : '' },
    appliedIds() {
      const m = new Map()
      this.myApps.forEach(a => m.set(a.drive_id, a.status))
      return m
    }
  },
  async mounted() {
    await this.fetchMyApps()
    await this.fetchDrives()
  },
  methods: {
    async fetchDrives() {
      this.loading = true
      try {
        const res = await rrApi.get('/api/student/drives', {
          params: { search: this.search, branch: this.branchFilter }
        })
        this.drives = res.data.map(d => ({ ...d, _expanded: false }))
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.loading = false }
    },
    async fetchMyApps() {
      try {
        const res = await rrApi.get('/api/student/applications')
        this.myApps = res.data
      } catch(e) { /* non-fatal */ }
    },
    async apply(driveId) {
      this.applying = driveId
      try {
        await rrApi.post(`/api/student/drives/${driveId}/apply`)
        rrShowAlert('Application submitted!','success')
        await this.fetchMyApps()
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.applying = null }
    },
    getAppStatus(driveId) { return this.appliedIds.get(driveId) || '' },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—' }
  }
}