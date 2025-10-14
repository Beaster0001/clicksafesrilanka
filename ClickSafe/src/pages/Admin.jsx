import { useState, useEffect } from 'react';
import { 
  Users, 
  Shield, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Search,
  Eye,
  UserX,
  UserCheck,
  RefreshCw
} from 'lucide-react';
import { useAuth, withAdminAuth } from '../contexts/AuthContext';
import { adminAPI } from '../services/api';

const Admin = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userActivities, setUserActivities] = useState([]);
  const [showUserModal, setShowUserModal] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchAdminData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAdminData(false);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [searchTerm, filterActive]);

  const fetchAdminData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoadingStats(true);
      } else {
        setIsRefreshing(true);
      }
      
      const adminStats = await adminAPI.getStats();
      setStats(adminStats);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching admin stats:', error);
    } finally {
      if (showLoading) {
        setLoadingStats(false);
      } else {
        setIsRefreshing(false);
      }
    }
  };

  const fetchUsers = async () => {
    try {
      setLoadingUsers(true);
      const query = new URLSearchParams();
      if (searchTerm) query.append('search', searchTerm);
      if (filterActive !== null) query.append('is_active', filterActive.toString());
      
      const userList = await adminAPI.getUsers(query.toString());
      setUsers(userList);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleUserClick = async (userId) => {
    try {
      const userDetails = await adminAPI.getUserDetails(userId);
      const activities = await adminAPI.getUserActivities(userId);
      setSelectedUser(userDetails);
      setUserActivities(activities);
      setShowUserModal(true);
    } catch (error) {
      console.error('Error fetching user details:', error);
    }
  };

  const handleManualRefresh = () => {
    fetchAdminData(false);
    fetchUsers();
  };

  const handleSuspendUser = async (userId) => {
    const userToSuspend = users.find(u => u.id === userId);
    if (!userToSuspend) return;

    if (window.confirm(`Are you sure you want to suspend ${userToSuspend.full_name}? They will not be able to access the application.`)) {
      try {
        await adminAPI.deactivateUser(userId);
        // Refresh the user list to show updated status
        fetchUsers();
        alert('User suspended successfully');
      } catch (error) {
        console.error('Error suspending user:', error);
        alert('Failed to suspend user. Please try again.');
      }
    }
  };

  const handleActivateUser = async (userId) => {
    const userToActivate = users.find(u => u.id === userId);
    if (!userToActivate) return;

    if (window.confirm(`Are you sure you want to activate ${userToActivate.full_name}? They will regain access to the application.`)) {
      try {
        await adminAPI.activateUser(userId);
        // Refresh the user list to show updated status
        fetchUsers();
        alert('User activated successfully');
      } catch (error) {
        console.error('Error activating user:', error);
        alert('Failed to activate user. Please try again.');
      }
    }
  };

  const handleDeleteUser = async (userId) => {
    const userToDelete = users.find(u => u.id === userId);
    if (!userToDelete) return;

    if (window.confirm(`Are you sure you want to permanently delete ${userToDelete.full_name}? This action cannot be undone.`)) {
      try {
        await adminAPI.deleteUser(userId);
        // Refresh the user list to remove deleted user
        fetchUsers();
        alert('User deleted successfully');
      } catch (error) {
        console.error('Error deleting user:', error);
        alert('Failed to delete user. Please try again.');
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const StatCard = ({ title, value, icon, color = 'blue' }) => (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-600">{title}</p>
          <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
        </div>
        <div className={`w-12 h-12 bg-${color}-100 rounded-lg flex items-center justify-center`}>
          {icon}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen w-full bg-slate-50">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-800 mb-2">
                Admin Dashboard
              </h1>
              <p className="text-slate-600">Welcome, {user?.full_name}! Monitor and manage ClickSafe users.</p>
            </div>
            <div className="flex items-center space-x-3">
              {lastUpdated && (
                <span className="text-sm text-slate-500">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={handleManualRefresh}
                disabled={isRefreshing}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {loadingStats ? (
            Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
                  <div className="h-8 bg-slate-200 rounded w-1/2"></div>
                </div>
              </div>
            ))
          ) : stats ? (
            <>
              <StatCard
                title="Total Users"
                value={stats.total_users}
                icon={<Users className="w-6 h-6 text-blue-600" />}
                color="blue"
              />
              <StatCard
                title="Active Users"
                value={stats.active_users}
                icon={<Activity className="w-6 h-6 text-green-600" />}
                color="green"
              />
              <StatCard
                title="Total Scans"
                value={stats.total_scans}
                icon={<Shield className="w-6 h-6 text-purple-600" />}
                color="purple"
              />
              <StatCard
                title="Threats Today"
                value={stats.dangerous_scans_today}
                icon={<AlertTriangle className="w-6 h-6 text-red-600" />}
                color="red"
              />
            </>
          ) : null}
        </div>

        {/* Users Management */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-slate-800">User Management</h2>
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              {/* Filter */}
              <select
                value={filterActive === null ? 'all' : filterActive.toString()}
                onChange={(e) => {
                  const value = e.target.value;
                  setFilterActive(value === 'all' ? null : value === 'true');
                }}
                className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Users</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive Only</option>
              </select>
            </div>
          </div>

          {/* Users Table */}
          <div className="overflow-x-auto">
            {loadingUsers ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-slate-600">Loading users...</span>
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">User</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Email</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Scans</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Last Login</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((tableUser) => (
                    <tr key={tableUser.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-4 px-4">
                        <div>
                          <p className="font-medium text-slate-800">{tableUser.full_name}</p>
                          <p className="text-sm text-slate-600">@{tableUser.username}</p>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-slate-700">{tableUser.email}</td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          tableUser.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {tableUser.is_active ? (
                            <>
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Active
                            </>
                          ) : (
                            <>
                              <UserX className="w-3 h-3 mr-1" />
                              Inactive
                            </>
                          )}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-slate-700">{tableUser.scan_count || 0}</td>
                      <td className="py-4 px-4 text-slate-700">
                        {tableUser.last_login ? formatDate(tableUser.last_login) : 'Never'}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleUserClick(tableUser.id)}
                            className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                            <span>View</span>
                          </button>
                          
                          {user && tableUser.id !== 1 && tableUser.id !== user.id && ( // Don't show actions for admin user (ID 1) or current user
                            <>
                              {tableUser.is_active ? (
                                <button
                                  onClick={() => handleSuspendUser(tableUser.id)}
                                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-yellow-50 text-yellow-600 rounded hover:bg-yellow-100 transition-colors"
                                >
                                  <UserX className="w-4 h-4" />
                                  <span>Suspend</span>
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleActivateUser(tableUser.id)}
                                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-50 text-green-600 rounded hover:bg-green-100 transition-colors"
                                >
                                  <UserCheck className="w-4 h-4" />
                                  <span>Activate</span>
                                </button>
                              )}
                              
                              <button
                                onClick={() => handleDeleteUser(tableUser.id)}
                                className="flex items-center space-x-1 px-3 py-1 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors"
                              >
                                <UserX className="w-4 h-4" />
                                <span>Delete</span>
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* User Details Modal */}
        {showUserModal && selectedUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-slate-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold text-slate-800">User Details</h3>
                  <button
                    onClick={() => setShowUserModal(false)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    ×
                  </button>
                </div>
              </div>
              
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <h4 className="font-semibold text-slate-800 mb-3">User Information</h4>
                    <div className="space-y-2">
                      <p><span className="font-medium">Name:</span> {selectedUser.full_name}</p>
                      <p><span className="font-medium">Username:</span> @{selectedUser.username}</p>
                      <p><span className="font-medium">Email:</span> {selectedUser.email}</p>
                      <p><span className="font-medium">Status:</span> 
                        <span className={`ml-2 px-2 py-1 rounded text-xs ${
                          selectedUser.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {selectedUser.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </p>
                      <p><span className="font-medium">Joined:</span> {formatDate(selectedUser.created_at)}</p>
                      <p><span className="font-medium">Last Login:</span> {selectedUser.last_login ? formatDate(selectedUser.last_login) : 'Never'}</p>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-slate-800 mb-3">Activity Summary</h4>
                    <div className="space-y-2">
                      <p><span className="font-medium">Total Activities:</span> {userActivities.length}</p>
                      <p><span className="font-medium">Recent Activity:</span> {
                        userActivities.length > 0 
                          ? formatDate(userActivities[0].created_at)
                          : 'No activity'
                      }</p>
                    </div>
                  </div>
                </div>
                
                {/* Recent Activities */}
                <div>
                  <h4 className="font-semibold text-slate-800 mb-3">Recent Activities</h4>
                  <div className="bg-slate-50 rounded-lg p-4 max-h-60 overflow-y-auto">
                    {userActivities.length > 0 ? (
                      <div className="space-y-2">
                        {userActivities.slice(0, 10).map((activity, index) => (
                          <div key={index} className="flex items-center justify-between text-sm">
                            <span className="font-medium text-slate-700">{activity.activity_type}</span>
                            <span className="text-slate-500">{formatDate(activity.created_at)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-500 text-center">No activities recorded</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default withAdminAuth(Admin);