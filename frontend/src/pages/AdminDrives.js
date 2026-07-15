// RecruitRadar — pages/AdminDrives.js

const AdminDrives = {
  name: 'AdminDrives',
  template: `
    <div class="container py-4">
      <h4 class="fw-bold mb-4"><i class="bi bi-briefcase me-2 text-primary"></i>Placement Drive Management</h4>
      <alert-msg></alert-msg>

      <div class="d-flex gap-2 mb-3">
        <select class="form-select" style="max-width:200px;" v-model="statusFilter" @change="fetchDrives">
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

      <div v-else>
        <div v-if="drives.length===0" class="text-center text-muted py-5">
          <i class="bi bi-briefcase-x d-block mb-2" style="font-size:2rem;"></i>No drives found.
        </div>
        <div v-for="d in drives" :key="d.id" class="card rr-card mb-3 p-3">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <h6 class="fw-bold mb-1">{{ d.job_title }}
                <span :class="'badge rr-badge-'+d.status + ' ms-2'">{{ d.status }}</span>
              </h6>
              <div class="text-muted small">{{ d.company_name }} &bull; Deadline: {{ fmtDate(d.deadline) }}</div>
              <div class="text-muted small mt-1">
                Min CGPA: {{ d.min_cgpa }} &bull; Branch: {{ d.eligible_branch || 'All' }} &bull;
                Salary: {{ d.salary || 'N/A' }} &bull; Applicants: {{ d.applicant_count }}
              </divv>
          </div>
          <p class="text-muted small mt-2 mb-0" style="white-space:pre-line;">{{ d.job_description }}</p>
        </div>
      </div>
    </div>
  `,
  data() { return { drives: [], statusFilter: '', loading: true } },
  mounted() { this.fetchDrives() },
  methods: {
    async fetchDrives() {
      this.loading = true
      try {
        const res = await rrApi.get('/api/admin/drives', { params: { status: this.statusFilter } })
        this.drives = res.data
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.loading = false }
    },
    async act(id, type) {
      if (type === 'delete' && !confirm('Delete this drive?')) return
      try {
        await rrApi.delete(`/api/admin/drives/${id}`)
        rrShowAlert('Done.', 'success')
        this.fetchDrives()
      } catch(e) { 
        rrShowAlert(rrGetError(e), 'danger') 
      }
    },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—' }
  }
}

// Admin — All Applications page 
const AdminApplications = {
  name: 'AdminApplications',
  template: `
    <div class="container py-4">
      <h4 class="fw-bold mb-4"><i class="bi bi-file-earmark-text me-2 text-primary"></i>All Applications</h4>
      <alert-msg></alert-msg>
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
      <div v-else>
        <p class="text-muted small mb-2">{{ apps.length }} application(s)</p>
        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead class="table-dark">
              <tr><th>Student</th><th>Company</th><th>Drive</th><th>Applied</th><th>Status</th><th>Interview</th></tr>
            </thead>
            <tbody>
              <tr v-for="a in apps" :key="a.id">
                <td>{{ a.student_name }}<div class="text-muted small">{{ a.student_email }}</div></td>
                <td>{{ a.company_name }}</td>
                <td>{{ a.job_title }}</td>
                <td class="small text-muted">{{ fmtDate(a.applied_at) }}</td>
                <td><span :class="'badge rr-badge-'+a.status">{{ a.status }}</span></td>
                <td class="small text-muted">{{ a.interview_date ? fmtDate(a.interview_date) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  data() { return { apps: [], loading: true } },
  async mounted() {
    try {
      const res = await rrApi.get('/api/admin/applications')
      this.apps = res.data
    } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    finally { this.loading = false }
  },
  methods: { fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—' } }
}
