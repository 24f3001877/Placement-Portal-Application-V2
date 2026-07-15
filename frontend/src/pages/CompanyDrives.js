// RecruitRadar — pages/CompanyDrives.js
// Company manages their drives and creates new ones.
const CompanyDrives = {
  name: 'CompanyDrives',
  template: `
    <div class="container py-4">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="fw-bold mb-0"><i class="bi bi-briefcase me-2 text-primary"></i>My Placement Drives</h4>
        <button class="btn btn-primary" @click="showForm=!showForm">
          <i class="bi bi-plus-lg me-1"></i>{{ showForm ? 'Cancel' : 'New Drive' }}
        </button>
      </div>
      <alert-msg></alert-msg>

      <!-- Create Drive Form -->
      <div v-if="showForm" class="card rr-card p-4 mb-4">
        <h6 class="fw-semibold mb-3">Create New Placement Drive</h6>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Job Title <span class="text-danger">*</span></label>
            <input class="form-control" v-model="form.job_title" placeholder="e.g. Software Engineer" />
          </div>
          <div class="col-md-3">
            <label class="form-label">Salary Package</label>
            <input class="form-control" v-model="form.salary" placeholder="e.g. 8-12 LPA" />
          </div>
          <div class="col-md-3">
            <label class="form-label">Experience Required</label>
            <input class="form-control" v-model="form.experience_required" placeholder="e.g. 0-2 years" />
          </div>
          <div class="col-12">
            <label class="form-label">Job Description <span class="text-danger">*</span></label>
            <textarea class="form-control" v-model="form.job_description" rows="3"></textarea>
          </div>
          <div class="col-md-6">
            <label class="form-label">Skills Required</label>
            <input class="form-control" v-model="form.skills_required" placeholder="Python, SQL, ..." />
          </div>
          <div class="col-md-6">
            <label class="form-label">Benefits</label>
            <input class="form-control" v-model="form.benefits" placeholder="Health insurance, Remote, ..." />
          </div>
          <div class="col-md-4">
            <label class="form-label">Eligible Branches</label>
            <input class="form-control" v-model="form.eligible_branch" placeholder="CSE,ECE (comma-sep)" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Min CGPA</label>
            <input type="number" step="0.1" min="0" max="10" class="form-control" v-model.number="form.min_cgpa" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Eligible Year</label>
            <select class="form-select" v-model.number="form.eligible_year">
              <option :value="null">All Years</option>
              <option :value="1">1st</option><option :value="2">2nd</option>
              <option :value="3">3rd</option><option :value="4">4th</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Application Deadline <span class="text-danger">*</span></label>
            <input type="datetime-local" class="form-control" v-model="form.deadline" />
          </div>
          <div class="col-12">
            <button class="btn btn-success fw-semibold" @click="createDrive" :disabled="rrStore.loading">
              <span v-if="rrStore.loading" class="spinner-border spinner-border-sm me-2"></span>
              Submit Drive for Approval
            </button>
          </div>
        </div>
      </div>

      <!-- Drives List -->
      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
      <div v-else-if="drives.length===0" class="text-center text-muted py-5">
        <i class="bi bi-briefcase-x d-block mb-2" style="font-size:2rem;"></i>No drives yet. Create your first one!
      </div>
      <div v-else>
        <div v-for="d in drives" :key="d.id" class="card rr-card mb-3 p-3">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <h6 class="fw-bold mb-1">{{ d.job_title }}
                <span :class="'badge rr-badge-'+d.status+' ms-2'">{{ d.status }}</span>
              </h6>
              <div class="text-muted small">
                Deadline: {{ fmtDate(d.deadline) }} &bull;
                Applicants: <strong>{{ d.applicant_count }}</strong> &bull;
                Salary: {{ d.salary || 'N/A' }}
              </div>
            </div>
            <div class="d-flex gap-2">
              <router-link v-if="d.applicant_count>0" :to="'/company/applications/'+d.id"
                class="btn btn-outline-primary btn-sm">
                <i class="bi bi-people me-1"></i>View Applicants
              </router-link>
              <button v-if="d.status==='approved'" class="btn btn-outline-secondary btn-sm"
                @click="closeDrive(d.id)">Close</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      drives: [], loading: true, showForm: false,
      form: { job_title:'', job_description:'', salary:'', experience_required:'',
               skills_required:'', benefits:'', eligible_branch:'',
               min_cgpa: 0, eligible_year: null, deadline:'' }
    }
  },
  mounted() { this.fetchDrives() },
  methods: {
    async fetchDrives() {
      this.loading = true
      try {
        const res = await rrApi.get('/api/company/drives')
        this.drives = res.data
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.loading = false }
    },
    async createDrive() {
      if (!this.form.job_title || !this.form.job_description || !this.form.deadline) {
        return rrShowAlert('Job title, description, and deadline are required.','warning')
      }
      rrStore.loading = true
      try {
        await rrApi.post('/api/company/drives', this.form)
        rrShowAlert('Drive submitted for admin approval.','success')
        this.showForm = false
        this.fetchDrives()
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { rrStore.loading = false }
    },
    async closeDrive(id) {
      if (!confirm('Close this drive? No new applications will be accepted.')) return
      try {
        await rrApi.put(`/api/company/drives/${id}`, { status:'closed' })
        rrShowAlert('Drive closed.','success')
        this.fetchDrives()
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—' }
  }
}
