<template>
  <div class="admin-layout">
    <Sidebar />
    <div class="admin-main">
      <div class="topbar">
        <h2>用户管理</h2>
        <span class="topbar-count">共 {{ total }} 位用户</span>
      </div>
      <el-card shadow="never" class="search-card">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="手机号/昵称" clearable style="width:180px" />
          </el-form-item>
          <el-form-item label="会员等级">
            <el-select v-model="searchForm.level" placeholder="全部" clearable style="width:130px">
              <el-option label="免费" value="free" /><el-option label="基础" value="basic" /><el-option label="高级" value="premium" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="全部" clearable style="width:120px">
              <el-option label="正常" value="active" /><el-option label="禁用" value="disabled" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      <el-card shadow="never">
        <el-table :data="users" stripe v-loading="loading" border class="manage-table">
          <el-table-column prop="id" label="ID" width="70" align="center" />
          <el-table-column label="用户信息" min-width="180">
            <template #default="{row}">
              <div class="user-cell">
                <el-avatar :size="36" :src="row.avatar||''" style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;">
                  {{ row.nickname?.charAt(0)||row.phone?.slice(-2)||'U' }}
                </el-avatar>
                <div class="user-info">
                  <div class="user-name">{{ row.nickname||'-' }}</div>
                  <div class="user-phone">{{ row.phone||'未绑定' }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="会员" width="100" align="center">
            <template #default="{row}"><el-tag :type="levelTag(row.membership_level)" size="small" effect="light">{{ levelLabel(row.membership_level) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="积分" width="80" align="center">
            <template #default="{row}">{{ row.remaining_credits??0 }}</template>
          </el-table-column>
          <el-table-column label="到期时间" width="140" align="center">
            <template #default="{row}">{{ row.membership_expire_at?row.membership_expire_at.substring(0,10):'永久' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{row}"><el-tag :type="row.status==='active'?'success':'danger'" size="small">{{ row.status==='active'?'正常':'禁用' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" width="160" align="center" />
          <el-table-column label="操作" width="220" align="center" fixed="right">
            <template #default="{row}">
              <el-button link type="primary" size="small" @click="viewDetail(row)">详情</el-button>
              <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
              <el-button :link="true" :type="row.status==='active'?'danger':'success'" size="small" @click="toggleStatus(row)">{{ row.status==='active'?'禁用':'启用' }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next, jumper" style="margin-top:20px;justify-content:center;" @current-change="fetchUsers" />
      </el-card>
    </div>

    <el-dialog v-model="editVisible" title="编辑用户" width="480px" destroy-on-close>
      <el-form :model="editForm" label-width="110px" size="default">
        <el-form-item label="昵称"><el-input v-model="editForm.nickname" /></el-form-item>
        <el-form-item label="会员等级">
          <el-select v-model="editForm.membership_level" style="width:100%">
            <el-option label="免费" value="free" /><el-option label="基础" value="basic" /><el-option label="高级" value="premium" />
          </el-select>
        </el-form-item>
        <el-form-item label="剩余积分"><el-input-number v-model="editForm.remaining_credits" :min="0" /></el-form-item>
        <el-form-item label="到期时间"><el-input v-model="editForm.membership_expire_at" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" @click="saveEdit">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="用户详情" width="500px" destroy-on-close>
      <el-descriptions :column="2" border v-if="currentUser">
        <el-descriptions-item label="昵称">{{ currentUser.nickname||'-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ currentUser.phone||'未绑定' }}</el-descriptions-item>
        <el-descriptions-item label="会员"><el-tag :type="levelTag(currentUser.membership_level)" size="small">{{ levelLabel(currentUser.membership_level) }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="剩余积分">{{ currentUser.remaining_credits??0 }}</el-descriptions-item>
        <el-descriptions-item label="会员到期">{{ currentUser.membership_expire_at?currentUser.membership_expire_at.substring(0,10):'永久免费' }}</el-descriptions-item>
        <el-descriptions-item label="微信OpenID">{{ currentUser.wechat_openid||'未绑定' }}</el-descriptions-item>
        <el-descriptions-item label="状态"><el-tag :type="currentUser.status==='active'?'success':'danger'">{{ currentUser.status==='active'?'正常':'禁用' }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ currentUser.created_at }}</el-descriptions-item>
        <el-descriptions-item label="最后登录">{{ currentUser.last_login_at||'从未登录' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { Search } from "@element-plus/icons-vue"
import Sidebar from "@/components/Sidebar.vue"
import { listUsers, toggleUser, updateUser, getUserDetail } from "@/api/admin"

const users=ref([]); const loading=ref(false); const page=ref(1); const pageSize=ref(20); const total=ref(0)
const searchForm=reactive({ keyword:"", level:"", status:"" })
const editVisible=ref(false); const editForm=reactive({ id:null,nickname:"",membership_level:"free",remaining_credits:0,membership_expire_at:"" })
const detailVisible=ref(false); const currentUser=ref(null)

function levelTag(l){return{free:"info",basic:"warning",premium:"danger"}[l]||"info"}
function levelLabel(l){return{free:"免费",basic:"基础",premium:"高级"}[l]||l}

async function fetchUsers(){
  loading.value=true; try{
    const res=await listUsers(page.value,pageSize.value,{keyword:searchForm.keyword||undefined,membership_level:searchForm.level||undefined,status:searchForm.status||undefined})
    if(res.code===200){users.value=res.data?.records||res.data?.items||[];total.value=res.data?.total||res.data?.count||0}
  }catch(e){ElMessage.error("加载失败")}finally{loading.value=false}
}
function handleSearch(){page.value=1;fetchUsers()}
function handleReset(){searchForm.keyword="";searchForm.level="";searchForm.status="";page.value=1;fetchUsers()}

async function viewDetail(row){try{const res=await getUserDetail(row.id);if(res.code===200){currentUser.value=res.data;detailVisible.value=true}}catch(e){ElMessage.error("获取详情失败")}}
function openEdit(row){editForm.id=row.id;editForm.nickname=row.nickname||"";editForm.membership_level=row.membership_level||"free";editForm.remaining_credits=row.remaining_credits??0;editForm.membership_expire_at=row.membership_expire_at||"";editVisible.value=true}
async function saveEdit(){try{const data={};if(editForm.nickname)data.nickname=editForm.nickname;if(editForm.membership_level)data.membership_level=editForm.membership_level;if(editForm.remaining_credits!==undefined)data.remaining_credits=editForm.remaining_credits;if(editForm.membership_expire_at)data.membership_expire_at=editForm.membership_expire_at
  await updateUser(editForm.id,data);ElMessage.success("已更新");editVisible.value=false;fetchUsers()}catch(e){ElMessage.error("保存失败")}}
async function toggleStatus(row){try{await ElMessageBox.confirm(`确定要${row.status==='active'?'禁用':'启用'}该用户吗？`,'提示',{type:'warning'});await toggleUser(row.id);ElMessage.success('操作成功');fetchUsers()}catch(e){if(e!=='cancel')ElMessage.error('操作失败')}}

onMounted(fetchUsers)
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }
.admin-main { flex: 1; margin-left: 240px; padding: 24px; background: var(--admin-bg); min-height: 100vh; }
.topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.topbar h2 { font-size:1.3rem; font-weight:700; color:var(--admin-primary); margin:0; }
.topbar-count { font-size:0.85rem; color:var(--admin-text-light); }
.search-card { margin-bottom:16px; border-radius:var(--admin-radius-lg); }
.search-form { display:flex; flex-wrap:wrap; gap:0; }
.manage-table { border-radius:var(--admin-radius); overflow:hidden; }
.user-cell { display:flex; align-items:center; gap:10px; }
.user-info .user-name { font-weight:600; font-size:0.9rem; }
.user-info .user-phone { font-size:0.78rem; color:var(--admin-text-light); }
@media(max-width:768px){ .admin-main{margin-left:0} }
</style>
