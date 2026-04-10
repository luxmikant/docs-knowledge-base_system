import { useEffect, useMemo, useState } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function TasksPage() {
  const { isAdmin } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [assignedToFilter, setAssignedToFilter] = useState('');
  const [formData, setFormData] = useState({ title: '', description: '', assigned_to: '', status: 'pending' });
  const [error, setError] = useState('');

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (assignedToFilter) params.set('assigned_to', assignedToFilter);
      const response = await api.get(`/tasks${params.toString() ? `?${params.toString()}` : ''}`);
      setTasks(response.data.tasks || []);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    if (!isAdmin) return;
    try {
      const response = await api.get('/users');
      setUsers(response.data.users || []);
    } catch {
      setUsers([]);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [isAdmin]);

  useEffect(() => {
    fetchTasks();
  }, [statusFilter, assignedToFilter]);

  const createTask = async (event) => {
    event.preventDefault();
    setError('');
    try {
      await api.post('/tasks', {
        ...formData,
        assigned_to: Number(formData.assigned_to),
      });
      setFormData({ title: '', description: '', assigned_to: '', status: 'pending' });
      fetchTasks();
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to create task');
    }
  };

  const completeTask = async (taskId) => {
    try {
      await api.put(`/tasks/${taskId}`, { status: 'completed' });
      fetchTasks();
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to update task');
    }
  };

  const userOptions = useMemo(
    () => users.map((user) => ({ value: String(user.id), label: `${user.username} (${user.role})` })),
    [users],
  );

  return (
    <section>
      <h2>Tasks</h2>

      {isAdmin && (
        <form className="panel" onSubmit={createTask}>
          <h3>Create Task</h3>
          <div className="grid-2">
            <input
              placeholder="Title"
              value={formData.title}
              onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
              required
            />
            <select
              value={formData.assigned_to}
              onChange={(e) => setFormData((prev) => ({ ...prev, assigned_to: e.target.value }))}
              required
            >
              <option value="">Assign to...</option>
              {userOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <textarea
              className="span-2"
              rows={3}
              placeholder="Description"
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              required
            />
          </div>
          <button type="submit">Create Task</button>
        </form>
      )}

      <div className="panel">
        <h3>Filters</h3>
        <div className="grid-2">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
          </select>
          {isAdmin && (
            <select value={assignedToFilter} onChange={(e) => setAssignedToFilter(e.target.value)}>
              <option value="">All users</option>
              {userOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="panel">
        <h3>Task List</h3>
        {loading ? (
          <p>Loading tasks...</p>
        ) : tasks.length === 0 ? (
          <p>No tasks found.</p>
        ) : (
          <div className="list">
            {tasks.map((task) => (
              <article key={task.id} className="list-item">
                <div>
                  <h4>{task.title}</h4>
                  <p>{task.description}</p>
                  <small>
                    Assigned: {task.assigned_to_username} | Status: <strong>{task.status}</strong>
                  </small>
                </div>
                {task.status === 'pending' && (
                  <button onClick={() => completeTask(task.id)}>Mark Completed</button>
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
