// RecruitRadar — pages/AdminCompanies.js

const AdminCompanies = {
  name: 'AdminCompanies',
  template: `
    <div class="container py-4">
      <h4 class="fw-bold mb-4"><i class="bi bi-building me-2 text-primary"></i>Company Management</h4>
      <alert-msg></alert-msg>

      <div class="d-flex gap-2 mb-3">
        <input class="form-control" style="max-width:320px;" v-model="search"
          placeholder="Search by name or industry..." @input="fetchCompanies" />
        <button class="btn btn-outline-secondary" @click="fetchCompanies">
          <i class="bi bi-search"></i>
        </button>
      </div>

      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

      <div v-else>
        <div v-if="companies.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-building-x d-block mb-2" style="font-size:2rem;"></i>No companies found.
        </div>
        <div class="table-responsive" v-else>
          <table class="table table-hover align-middle">
            <thead class="table-dark">
              <tr>
                <th>Company</th><th>Industry</th><th>Location</th><th>HR Contact</th>
                <th>Status</th><th>Registered</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in companies" :key="c.id">
                <td>
                  <strong>{{ c.company_name }}</strong>
                  <div class="text-muted small">{{ c.email }}</div>
                </td>
                <td>{{ c.industry || '—' }}</td>
                <td>{{ c.location || '—' }}</td>
                <td>{{ c.hr_contact || '—' }}</td>
                <td>
                  <span :class="'badge rr-badge-' + c.approval_status">{{ c.approval_status }}</span>
                  <span v-if="c.is_blacklisted" class="badge bg-dark ms-1">Blacklisted</span>
                </td>
                <td class="small text-muted">{{ fmtDate(c.registered_at) }}</td>
                <td>
                  <div class="d-flex gap-1 flex-wrap">
                    <button class="btn btn-warning btn-sm" @click="action(c.id,'blacklist')">
                      {{ c.is_blacklisted ? 'Unblacklist' : 'Blacklist' }}
                    </button>
                    <button class="btn btn-outline-danger btn-sm" @click="action(c.id,'delete')">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  data() { return { companies: [], search: '', loading: true } },
  mounted() { this.fetchCompanies() },
  methods: {
    async fetchCompanies() {
      this.loading = true
      try {
        const res = await rrApi.get('/api/admin/companies', { params: { search: this.search } })
        this.companies = res.data
      } catch (e) { rrShowAlert(rrGetError(e), 'danger') }
      finally { this.loading = false }
    },
    async action(id, type) {
      if (type === 'delete' && !confirm('Remove this company? This cannot be undone.')) return
      try {
        if (type === 'approve')    await rrApi.put(`/api/admin/companies/${id}/approve`)
        else if (type === 'reject')     await rrApi.put(`/api/admin/companies/${id}/reject`)
        else if (type === 'blacklist')  await rrApi.put(`/api/admin/companies/${id}/blacklist`)
        else if (type === 'delete')     await rrApi.delete(`/api/admin/companies/${id}`)
        rrShowAlert('Action completed.', 'success')
        this.fetchCompanies()
      } catch (e) { rrShowAlert(rrGetError(e), 'danger') }
    },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—' }
  }
}
