<template>
  <div class="page-content">
    <h2 class="page-title">用户与权限管理</h2>
    <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px"
              title="管理员可创建用户、分配角色，并在角色权限基础上为单个用户勾选菜单权限。角色是权限模板，用户权限 = 用户自身菜单权限（优先），为空时回退取所属角色权限。" />

    <el-tabs v-model="activeTab" class="perm-tabs">
      <!-- ============ 用户管理 ============ -->
      <el-tab-pane label="用户管理" name="users">
        <div class="toolbar" style="margin-bottom:16px">
          <el-button type="primary" @click="openUserDialog()">
            <el-icon style="margin-right:4px"><Plus /></el-icon>新建用户
          </el-button>
          <span class="cur-tip">共 {{ users.length }} 名用户</span>
        </div>

        <div class="card">
          <el-table :data="users" style="width:100%" v-loading="loadingUsers">
            <el-table-column prop="username" label="登录账号" min-width="140" />
            <el-table-column prop="nickname" label="昵称" min-width="120" />
            <el-table-column label="角色" width="140">
              <template #default="{ row }">
                <el-tag v-if="row.role_name" size="small" effect="light" type="primary">{{ row.role_name }}</el-tag>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'active' ? 'success' : 'info'" effect="light">
                  {{ row.status === 'active' ? '正常' : '已禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="菜单权限" min-width="220">
              <template #default="{ row }">
                <el-tag v-for="k in row.menus.slice(0, 4)" :key="k" size="small" class="menu-chip">{{ menuTitle(k) }}</el-tag>
                <span v-if="row.menus.length > 4" class="muted">+{{ row.menus.length - 4 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170" />
            <el-table-column label="操作" width="160" align="right" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openUserDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="onDeleteUser(row)">删除</el-button>
              </template>
            </el-table-column>
            <template #empty><div class="empty-text">暂无用户</div></template>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- ============ 角色管理 ============ -->
      <el-tab-pane label="角色管理" name="roles">
        <div class="toolbar" style="margin-bottom:16px">
          <el-button type="primary" @click="openRoleDialog()">
            <el-icon style="margin-right:4px"><Plus /></el-icon>新建角色
          </el-button>
          <span class="cur-tip">共 {{ roles.length }} 个角色</span>
        </div>

        <div class="card">
          <el-table :data="roles" style="width:100%" v-loading="loadingRoles">
            <el-table-column prop="name" label="角色名称" min-width="160" />
            <el-table-column prop="code" label="角色编码" min-width="140">
              <template #default="{ row }"><code class="role-code">{{ row.code }}</code></template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
            <el-table-column label="菜单权限" min-width="220">
              <template #default="{ row }">
                <el-tag v-for="k in row.menu_keys.slice(0, 4)" :key="k" size="small" class="menu-chip">{{ menuTitle(k) }}</el-tag>
                <span v-if="row.menu_keys.length > 4" class="muted">+{{ row.menu_keys.length - 4 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="110" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_system" size="small" type="warning" effect="light">内置</el-tag>
                <el-tag v-else size="small" effect="light">自定义</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" align="right" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openRoleDialog(row)">编辑</el-button>
                <el-button link type="danger" :disabled="row.is_system" @click="onDeleteRole(row)">删除</el-button>
              </template>
            </el-table-column>
            <template #empty><div class="empty-text">暂无角色</div></template>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- ============ 用户表单 ============ -->
    <el-dialog v-model="userDialog" :title="userForm.id ? '编辑用户' : '新建用户'" width="720px">
      <el-form :model="userForm" label-width="96px">
        <el-form-item label="登录账号" required>
          <el-input v-model="userForm.username" :disabled="!!userForm.id" placeholder="登录用户名，不可重复" />
        </el-form-item>
        <el-form-item :label="userForm.id ? '重置密码' : '初始密码'" required>
          <el-input v-model="userForm.password" type="password" show-password
                    :placeholder="userForm.id ? '留空则不修改密码（至少6位）' : '至少6位'" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="userForm.nickname" placeholder="展示名称（可选）" />
        </el-form-item>
        <el-form-item label="分配角色" required>
          <el-select v-model="userForm.role_id" placeholder="选择角色（决定默认菜单权限）" style="width:100%"
                     @change="onRoleChange">
            <el-option v-for="r in roles" :key="r.id" :label="`${r.name}（${r.code}）`" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号状态">
          <el-switch v-model="userForm.statusActive" active-text="正常" inactive-text="禁用" />
        </el-form-item>

        <div class="form-section-title">菜单权限（在角色权限基础上勾选 / 微调）</div>
        <div class="menu-grid">
          <el-checkbox v-for="m in menuCatalog" :key="m.key" v-model="userForm.menus[m.key]"
                       :label="m.title" :value="m.key" border class="menu-check" />
        </div>
        <div class="perm-hint">
          <el-button link type="primary" @click="syncFromRole">沿用所选角色的全部权限</el-button>
          <el-button link @click="clearMenus('user')">清空</el-button>
          <span class="cur-tip">已选 {{ selectedUserMenus.length }} 项</span>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="userDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUser" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- ============ 角色表单 ============ -->
    <el-dialog v-model="roleDialog" :title="roleForm.id ? '编辑角色' : '新建角色'" width="720px">
      <el-form :model="roleForm" label-width="96px">
        <el-form-item label="角色名称" required>
          <el-input v-model="roleForm.name" placeholder="如：测试工程师" />
        </el-form-item>
        <el-form-item label="角色编码" required>
          <el-input v-model="roleForm.code" :disabled="roleForm.is_system" placeholder="英文唯一标识，如 tester" />
        </el-form-item>
        <el-form-item label="角色描述">
          <el-input v-model="roleForm.description" type="textarea" :rows="2" placeholder="角色用途说明（可选）" />
        </el-form-item>

        <div class="form-section-title">菜单权限</div>
        <div class="menu-grid">
          <el-checkbox v-for="m in menuCatalog" :key="m.key" v-model="roleForm.menus[m.key]"
                       :label="m.title" :value="m.key" border class="menu-check" />
        </div>
        <div class="perm-hint">
          <el-button link type="primary" @click="selectAll('role')">全选</el-button>
          <el-button link @click="clearMenus('role')">清空</el-button>
          <span class="cur-tip">已选 {{ selectedRoleMenus.length }} 项</span>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="roleDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRole" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api } from '../api'

const activeTab = ref('users')

// 目录与数据
const menuCatalog = ref([])
const roles = ref([])
const users = ref([])
const loadingUsers = ref(false)
const loadingRoles = ref(false)
const submitting = ref(false)

const menuTitleMap = computed(() => {
  const m = {}
  ;(menuCatalog.value || []).forEach((x) => { m[x.key] = x.title })
  return m
})
const menuTitle = (k) => menuTitleMap.value[k] || k

async function loadMenus() {
  try { menuCatalog.value = await api.listMenus() || [] } catch (e) { /* ignore */ }
}
async function loadRoles() {
  loadingRoles.value = true
  try { roles.value = await api.listRoles() || [] } catch (e) { /* ignore */ } finally { loadingRoles.value = false }
}
async function loadUsers() {
  loadingUsers.value = true
  try { users.value = await api.listUsers() || [] } catch (e) { /* ignore */ } finally { loadingUsers.value = false }
}

// ---------------- 用户表单 ----------------
const userDialog = ref(false)
const userForm = reactive({
  id: null, username: '', password: '', nickname: '', role_id: null,
  statusActive: true, menus: {}
})
const selectedUserMenus = computed(() => Object.keys(userForm.menus).filter((k) => userForm.menus[k]))

async function openUserDialog(row) {
  if (row) {
    userForm.id = row.id
    userForm.username = row.username
    userForm.password = ''
    userForm.nickname = row.nickname || ''
    userForm.role_id = row.role_id || null
    userForm.statusActive = row.status === 'active'
    const set = {}
    ;(menuCatalog.value || []).forEach((m) => { set[m.key] = (row.menus || []).includes(m.key) })
    userForm.menus = set
  } else {
    userForm.id = null
    userForm.username = ''
    userForm.password = ''
    userForm.nickname = ''
    userForm.role_id = roles.value.length ? roles.value[0].id : null
    userForm.statusActive = true
    const set = {}
    ;(menuCatalog.value || []).forEach((m) => { set[m.key] = false })
    userForm.menus = set
  }
  userDialog.value = true
}

function onRoleChange(rid) {
  const r = roles.value.find((x) => x.id === rid)
  if (r) {
    const set = {}
    ;(menuCatalog.value || []).forEach((m) => { set[m.key] = (r.menu_keys || []).includes(m.key) })
    userForm.menus = set
  }
}
function syncFromRole() {
  onRoleChange(userForm.role_id)
}
function clearMenus(kind) {
  const target = kind === 'user' ? userForm : roleForm
  const set = {}
  ;(menuCatalog.value || []).forEach((m) => { set[m.key] = false })
  target.menus = set
}

async function submitUser() {
  if (!userForm.username.trim()) { ElMessage.warning('请输入登录账号'); return }
  if (!userForm.id && !userForm.password) { ElMessage.warning('请设置初始密码'); return }
  if (userForm.password && userForm.password.length < 6) { ElMessage.warning('密码至少6位'); return }
  if (!userForm.role_id) { ElMessage.warning('请分配角色'); return }
  submitting.value = true
  const payload = {
    username: userForm.username.trim(),
    password: userForm.password || undefined,
    nickname: userForm.nickname.trim(),
    role_id: userForm.role_id,
    status: userForm.statusActive ? 'active' : 'disabled',
    menu_keys: selectedUserMenus.value
  }
  try {
    if (userForm.id) {
      await api.updateUser(userForm.id, payload)
      ElMessage.success('用户更新成功')
    } else {
      await api.createUser(payload)
      ElMessage.success('用户创建成功')
    }
    userDialog.value = false
    loadUsers()
  } catch (e) { /* 错误已在 api 层处理 */ } finally { submitting.value = false }
}

async function onDeleteUser(row) {
  await ElMessageBox.confirm(`确认删除用户「${row.username}」？该操作不可恢复。`, '删除确认', { type: 'warning' })
    .catch(() => { throw new Error('cancel') })
  try { await api.deleteUser(row.id); ElMessage.success('用户已删除'); loadUsers() } catch (e) { /* ignore */ }
}

// ---------------- 角色表单 ----------------
const roleDialog = ref(false)
const roleForm = reactive({ id: null, name: '', code: '', description: '', is_system: false, menus: {} })
const selectedRoleMenus = computed(() => Object.keys(roleForm.menus).filter((k) => roleForm.menus[k]))

function openRoleDialog(row) {
  if (row) {
    roleForm.id = row.id
    roleForm.name = row.name
    roleForm.code = row.code
    roleForm.description = row.description || ''
    roleForm.is_system = row.is_system
    const set = {}
    ;(menuCatalog.value || []).forEach((m) => { set[m.key] = (row.menu_keys || []).includes(m.key) })
    roleForm.menus = set
  } else {
    roleForm.id = null
    roleForm.name = ''
    roleForm.code = ''
    roleForm.description = ''
    roleForm.is_system = false
    const set = {}
    ;(menuCatalog.value || []).forEach((m) => { set[m.key] = false })
    roleForm.menus = set
  }
  roleDialog.value = true
}
function selectAll(kind) {
  const target = kind === 'role' ? roleForm : userForm
  const set = {}
  ;(menuCatalog.value || []).forEach((m) => { set[m.key] = true })
  target.menus = set
}

async function submitRole() {
  if (!roleForm.name.trim()) { ElMessage.warning('请输入角色名称'); return }
  if (!roleForm.code.trim()) { ElMessage.warning('请输入角色编码'); return }
  submitting.value = true
  const payload = {
    name: roleForm.name.trim(),
    code: roleForm.code.trim(),
    description: roleForm.description.trim(),
    menu_keys: selectedRoleMenus.value
  }
  try {
    if (roleForm.id) { await api.updateRole(roleForm.id, payload); ElMessage.success('角色更新成功') }
    else { await api.createRole(payload); ElMessage.success('角色创建成功') }
    roleDialog.value = false
    loadRoles()
    loadUsers() // 角色变更后用户展示的角色名可能变化
  } catch (e) { /* ignore */ } finally { submitting.value = false }
}

async function onDeleteRole(row) {
  await ElMessageBox.confirm(`确认删除角色「${row.name}」？`, '删除确认', { type: 'warning' })
    .catch(() => { throw new Error('cancel') })
  try { await api.deleteRole(row.id); ElMessage.success('角色已删除'); loadRoles() } catch (e) { /* ignore */ }
}

onMounted(() => {
  loadMenus()
  loadRoles()
  loadUsers()
})
</script>

<style scoped>
.perm-tabs { margin-top: 4px; }
.cur-tip { color: var(--text-3); font-size: 13px; }
.muted { color: var(--text-3); font-size: 13px; }
.menu-chip { margin: 0 6px 4px 0; }
.role-code { background: #f5f7fa; border-radius: 4px; padding: 1px 8px; color: var(--text-2); font-size: 12px; }
.form-section-title {
  font-size: 13px; font-weight: 600; color: var(--text-1);
  border-left: 3px solid var(--primary); padding-left: 8px; margin: 4px 0 12px;
}
.menu-grid { display: flex; flex-wrap: wrap; gap: 10px; }
.menu-check { margin-right: 0 !important; }
.perm-hint { margin-top: 10px; display: flex; align-items: center; gap: 8px; }
</style>
