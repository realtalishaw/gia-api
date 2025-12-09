import { supabase } from '../lib/supabase'
import { useState, useEffect } from 'react'

export default function AgentSessions() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Fetch initial sessions
    const fetchSessions = async () => {
      try {
        const { data, error } = await supabase
          .from('agent_sessions')
          .select('*')
          .order('created_at', { ascending: false })
          .limit(50)

        if (error) throw error
        setSessions(data || [])
        setLoading(false)
      } catch (err) {
        console.error('Error fetching sessions:', err)
        setError(err.message)
        setLoading(false)
      }
    }

    fetchSessions()

    // Subscribe to real-time changes
    const channel = supabase
      .channel('agent_sessions_changes')
      .on(
        'postgres_changes',
        {
          event: '*', // Listen to all events (INSERT, UPDATE, DELETE)
          schema: 'public',
          table: 'agent_sessions',
        },
        (payload) => {
          console.log('Session change received:', payload)
          
          if (payload.eventType === 'INSERT') {
            // Add new session to the top of the list
            setSessions((prev) => [payload.new, ...prev])
          } else if (payload.eventType === 'UPDATE') {
            // Update existing session
            setSessions((prev) =>
              prev.map((session) =>
                session.session_key === payload.new.session_key
                  ? payload.new
                  : session
              )
            )
          } else if (payload.eventType === 'DELETE') {
            // Remove deleted session
            setSessions((prev) =>
              prev.filter(
                (session) => session.session_key !== payload.old.session_key
              )
            )
          }
        }
      )
      .subscribe((status) => {
        console.log('Subscription status:', status)
        if (status === 'SUBSCRIBED') {
          console.log('✅ Subscribed to agent_sessions real-time updates')
        }
      })

    // Cleanup subscription on unmount
    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'routed':
        return '#4A90E2' // Blue
      case 'routed_to_fly':
        return '#9B59B6' // Purple
      case 'executing':
        return '#F39C12' // Orange
      case 'completed':
        return '#27AE60' // Green
      case 'failed':
        return '#E74C3C' // Red
      default:
        return '#95A5A6' // Gray
    }
  }

  const getExecutionTypeBadge = (executionType) => {
    return executionType === 'remote' ? '🌐 Remote' : '⚙️ Local'
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingText}>Loading sessions...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.errorText}>Error: {error}</div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>Agent Sessions</h2>
        <div style={styles.badge}>
          <span style={styles.badgeDot}></span>
          Live
        </div>
      </div>
      <div style={styles.tableContainer}>
        {sessions.length === 0 ? (
          <div style={styles.emptyState}>No sessions found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Session Key</th>
                <th style={styles.th}>Agent</th>
                <th style={styles.th}>Project</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Worker</th>
                <th style={styles.th}>Created</th>
                <th style={styles.th}>Updated</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.session_key} style={styles.tr}>
                  <td style={styles.td}>
                    <div style={styles.sessionKey}>
                      {session.session_key.split(':')[2]?.substring(0, 8) || session.session_key.substring(0, 8)}
                    </div>
                  </td>
                  <td style={styles.td}>{session.agent_name}</td>
                  <td style={styles.td}>
                    <div style={styles.projectId}>
                      {session.project_id.substring(0, 8)}...
                    </div>
                  </td>
                  <td style={styles.td}>
                    <span style={styles.typeBadge}>
                      {getExecutionTypeBadge(session.execution_type)}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <span
                      style={{
                        ...styles.statusBadge,
                        backgroundColor: getStatusColor(session.status),
                      }}
                    >
                      {session.status}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.workerId}>
                      {session.worker_id === 'celery' ? '⚙️ Celery' : session.worker_id}
                    </div>
                  </td>
                  <td style={styles.td}>{formatDate(session.created_at)}</td>
                  <td style={styles.td}>{formatDate(session.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

const styles = {
  container: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#000000',
    color: '#ffffff',
    padding: '2rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 400,
    color: '#ffffff',
    margin: 0,
    letterSpacing: '0.05em',
  },
  badge: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.5rem 1rem',
    backgroundColor: '#1a1a1a',
    border: '1px solid #333333',
    borderRadius: '4px',
    fontSize: '0.875rem',
    color: '#27AE60',
  },
  badgeDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#27AE60',
    animation: 'pulse 2s ease-in-out infinite',
  },
  tableContainer: {
    flex: 1,
    overflow: 'auto',
    border: '1px solid #333333',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.875rem',
  },
  th: {
    padding: '1rem',
    textAlign: 'left',
    borderBottom: '1px solid #333333',
    color: '#cccccc',
    fontWeight: 400,
    letterSpacing: '0.05em',
    backgroundColor: '#1a1a1a',
    position: 'sticky',
    top: 0,
    zIndex: 1,
  },
  tr: {
    borderBottom: '1px solid #222222',
    transition: 'background-color 0.2s ease',
  },
  td: {
    padding: '1rem',
    color: '#ffffff',
  },
  sessionKey: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#4A90E2',
  },
  projectId: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#cccccc',
  },
  typeBadge: {
    padding: '0.25rem 0.5rem',
    backgroundColor: '#1a1a1a',
    border: '1px solid #333333',
    borderRadius: '4px',
    fontSize: '0.75rem',
  },
  statusBadge: {
    padding: '0.25rem 0.75rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: 500,
    color: '#ffffff',
    textTransform: 'capitalize',
  },
  workerId: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#cccccc',
  },
  loadingText: {
    fontSize: '1rem',
    color: '#cccccc',
    textAlign: 'center',
    padding: '2rem',
  },
  errorText: {
    fontSize: '1rem',
    color: '#E74C3C',
    textAlign: 'center',
    padding: '2rem',
  },
  emptyState: {
    fontSize: '1rem',
    color: '#cccccc',
    textAlign: 'center',
    padding: '2rem',
  },
}
