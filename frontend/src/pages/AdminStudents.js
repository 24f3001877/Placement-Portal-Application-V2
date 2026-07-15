// RecruitRadar — pages/AdminStudents.js
const AdminStudents = {
  name: 'AdminStudents',
  template: `
    <div class="container py-4">
      <h4 class="fw-bold mb-4"><i class="bi bi-people me-2 text-primary"></i>Student Management</h4>
      <alert-msg></alert-msg>

      <div class="d-flex gap-2 mb-3">
        <input class="form-control" style="max-width:320px;" v-model="search"
          placeholder="Search by name, email, or ID..." @input="fetchStudents" />
        <button class="btn btn-outline-secondary" @click="fetchStudents"><i class="bi bi-search"></i></button>
      </div>

      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

      <div v-else>
        <p class="text-muted small mb-2">{{ students.length }} student(s) found.</p>
        <div v-if="students.length===0" class="text-center text-muted py-5">
          <i class="bi bi-person-x d-block mb-2" style="font-size:2rem;"></i>No students found.
        </div>
        <div class="table-responsive" v-else>
          <table class="table table-hover align-middle">
            <thead class="table-dark">
              <tr><th>ID</th><th>Name</th><th>Branch</th><th>Year</th><th>CGPA</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              <tr v-for="s in students" :key="s.id">
                <td class="text-muted small">#{{ s.id }}</td>
                <td>
                  <strong>{{ s.full_name }}</strong>
                  <div class="text-muted small">{{ s.email }}</div>
                </td>
                <td>{{ s.branch }}</td>
                <td>Year {{ s.year }}</td>
                <td><span class="badge bg-primary">{{ s.cgpa }}</span></td>
                <td>
                  <span class="badge" :class="s.is_active ? 'bg-success':'bg-secondary'">
                    {{ s.is_active ? 'Active':'Inactive' }}
                  </span>
                  <span v-if="s.is_blacklisted" class="badge bg-dark ms-1">Blacklisted</span>
                </td>
                <td>
                  <div class="d-flex gap-1">
                    <button class="btn btn-warning btn-sm" @click="blacklist(s.id, s.is_blacklisted)">
                      {{ s.is_blacklisted ? 'Unblacklist':'Blacklist' }}
                    </button>
                    <button class="btn btn-outline-danger btn-sm" @click="remove(s.id)">
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
  data() { return { students: [], search: '', loading: true } },
  mounted() { this.fetchStudents() },
  methods: {
    async fetchStudents() {
      this.loading = true
      try {
        const res = await rrApi.get('/api/admin/students', { params: { search: this.search } })
        this.students = res.data
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.loading = false }
    },
    async blacklist(id, current) {
      try {
        await rrApi.put(`/api/admin/students/${id}/blacklist`)
        rrShowAlert(current ? 'Student un-blacklisted.':'Student blacklisted.', 'success')
        this.fetchStudents()
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async remove(id) {
      if (!confirm('Remove this student permanently?')) return
      try {
        await rrApi.delete(`/api/admin/students/${id}`)
        rrShowAlert('Student removed.','success')
        this.fetchStudents()
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    }
  }
}
