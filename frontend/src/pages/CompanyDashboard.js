// RecruitRadar — pages/CompanyDashboard.js
const CompanyDashboard = {
  name: 'CompanyDashboard',
  template: `
    <div class="container py-4">
      <h4 class="fw-bold mb-4"><i class="bi bi-building me-2 text-primary"></i>Company Dashboard</h4>
      <alert-msg></alert-msg>

      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

      <div v-else>
        <!-- Company info card -->
        <div class="card rr-card p-4 mb-4">
          <div class="d-flex align-items-center gap-3">
            <i class="bi bi-building-check text-primary" style="font-size:2.5rem;"></i>
            <div>
              <h5 class="fw-bold mb-1">{{ data.company.company_name }}</h5>
              <div class="text-muted small">{{ data.company.industry }} &bull; {{ data.company.location }}</div>
              <div class="text-muted small">{{ data.company.email }}</div>
            </div>
            <span class="badge rr-badge-approved ms-auto">Approved</span>
          </div>
        </div>

        <!-- Stats -->
        <div class="row g-3 mb-4">
          <div class="col-6 col-md-3" v-for="s in stats" :key="s.label">
            <div class="card rr-card rr-stat-card p-3 text-center">
              <div class="fs-3 fw-bold" style="color:var(--rr-primary);">{{ s.value }}</div>
              <div class="text-muted small">{{ s.label }}</div>
            </div>
          </div>
        </div>

        <!-- Quick links -->
        <div class="row g-3">
          <div class="col-md-6">
            <router-link to="/company/drives" class="btn btn-primary w-100 py-3">
              <i class="bi bi-plus-circle me-2"></i>Post New Drive / Manage Drives
            </router-link>
          </div>
          <div class="col-md-6">
            <button class="btn btn-outline-secondary w-100 py-3" @click="exportCSV">
              <i class="bi bi-download me-2"></i>Export Applications CSV
            </button>

            <div v-if="exportJobId && !exportFile" class="text-center mt-2">
              <button class="btn btn-sm btn-outline-info" @click="checkExport">Check Export Status</button>
            </div>

            <div v-if="exportFile" class="text-center mt-2">
              <button class="btn btn-sm btn-success" @click="downloadCSV">
                <i class="bi bi-file-earmark-arrow-down me-1"></i>Download CSV
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      data: { company:{} },
      stats: [],
      loading: true,
      exportJobId: null,
      exportFile: null
    }
  },
  async mounted() {
    try {
      const res = await rrApi.get('/api/company/dashboard')
      this.data = res.data
      this.stats = [
        { label:'Total Drives',     value: res.data.total_drives },
        { label:'Total Applicants', value: res.data.total_applicants },
        { label:'Shortlisted',      value: res.data.shortlisted },
        { label:'Placed',           value: res.data.placed },
      ]
    } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    finally { this.loading = false }
  },
  methods: {
    async exportCSV() {
      this.exportFile = null
      try {
        const res = await rrApi.post('/api/company/export')
        this.exportJobId = res.data.export_job_id
        rrShowAlert(res.data.message, 'info')
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async checkExport() {
      if (!this.exportJobId) return
      try {
        const res = await rrApi.get(`/api/company/export/${this.exportJobId}/status`)
        if (res.data.status === 'done') {
          this.exportFile = res.data.file_path
          rrShowAlert('Export ready — click Download.', 'success')
        } else if (res.data.status === 'failed') {
          rrShowAlert('Export failed. Please try again.', 'danger')
          this.exportJobId = null
        } else {
          rrShowAlert('Still processing...', 'info')
        }
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async downloadCSV() {
      try {
        const res = await rrApi.get(`/api/company/export/${this.exportFile}/download`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.download = this.exportFile
        a.click()
      } catch(e) { rrShowAlert('Could not download file.', 'danger') }
    }
  }
}