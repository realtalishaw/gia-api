import { useState, useEffect } from 'react'

export default function FlowerMonitoring() {
  const [activeView, setActiveView] = useState('workers')
  const [connectionError, setConnectionError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const [workers, setWorkers] = useState([])
  const [tasks, setTasks] = useState([])
  const [queues, setQueues] = useState([])
  
  // Get API URL from environment variable, fallback to localhost for development
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  
  // Fetch data from API proxy endpoint (which fetches from Flower)
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Only show loading on initial load, not on refreshes
        if (isInitialLoad) {
          setIsLoading(true)
        }
        setConnectionError(false)
        
        if (activeView === 'workers') {
          const response = await fetch(`${apiUrl}/api/monitoring/workers`, {
            method: 'GET',
            mode: 'cors',
          })
          if (response.ok) {
            const data = await response.json()
            const workersData = data.workers || []
            // Log for debugging
            if (workersData.length > 0) {
              console.log('Workers data:', workersData[0])
            }
            setWorkers(workersData)
          } else if (response.status === 404) {
            // No workers connected yet
            setWorkers([])
          } else {
            throw new Error(`HTTP ${response.status}`)
          }
        } else if (activeView === 'tasks') {
          const response = await fetch(`${apiUrl}/api/monitoring/tasks?limit=50`, {
            method: 'GET',
            mode: 'cors',
          })
          if (response.ok) {
            const data = await response.json()
            setTasks(data.tasks || [])
          } else {
            throw new Error(`HTTP ${response.status}`)
          }
        } else if (activeView === 'queues') {
          const response = await fetch(`${apiUrl}/api/monitoring/queues`, {
            method: 'GET',
            mode: 'cors',
          })
          if (response.ok) {
            const data = await response.json()
            console.log('Queues data received:', data)
            const queuesData = data.queues || {}
            console.log('Queues object:', queuesData, 'Keys:', Object.keys(queuesData))
            setQueues(queuesData)
          } else {
            throw new Error(`HTTP ${response.status}`)
          }
        }
      } catch (error) {
        console.error('Flower API error:', error)
        setConnectionError(true)
      } finally {
        setIsLoading(false)
        setIsInitialLoad(false)
      }
    }
    
    fetchData()
    
    // Auto-refresh every 5 seconds (but don't show loading spinner)
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [activeView, apiUrl, isInitialLoad])
  
  const getStateColor = (state) => {
    const colors = {
      'SUCCESS': '#4ade80',
      'FAILURE': '#f87171',
      'PENDING': '#fbbf24',
      'STARTED': '#60a5fa',
      'RETRY': '#a78bfa',
      'REVOKED': '#9ca3af',
    }
    return colors[state] || '#9ca3af'
  }
  
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp * 1000).toLocaleString()
  }
  
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>Celery Monitoring</h2>
        <div style={styles.tabs}>
          <button
            onClick={() => {
              setActiveView('workers')
              setIsInitialLoad(true)
            }}
            style={{
              ...styles.tab,
              ...(activeView === 'workers' ? styles.tabActive : styles.tabInactive)
            }}
          >
            Workers
          </button>
          <button
            onClick={() => {
              setActiveView('tasks')
              setIsInitialLoad(true)
            }}
            style={{
              ...styles.tab,
              ...(activeView === 'tasks' ? styles.tabActive : styles.tabInactive)
            }}
          >
            Tasks
          </button>
          <button
            onClick={() => {
              setActiveView('queues')
              setIsInitialLoad(true)
            }}
            style={{
              ...styles.tab,
              ...(activeView === 'queues' ? styles.tabActive : styles.tabInactive)
            }}
          >
            Queues
          </button>
        </div>
      </div>
      
      <div style={styles.content}>
        {isLoading && !connectionError && (
          <div style={styles.loadingContainer}>
            <div style={styles.loadingText}>Loading...</div>
          </div>
        )}
        {connectionError ? (
          <div style={styles.errorContainer}>
            <div style={styles.errorText}>
              Unable to connect to Flower monitoring service.
            </div>
            <div style={styles.errorSubtext}>
              Please ensure:
            </div>
            <ul style={styles.errorList}>
              <li>The API service is running at {apiUrl}</li>
              <li>The Flower service is running and accessible to the API</li>
              <li>The CLOUDAMQP_URL environment variable is set</li>
              <li>The Celery worker is running and connected to the broker</li>
            </ul>
          </div>
        ) : (
          <>
            {activeView === 'workers' && (
              <div style={styles.tableContainer}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Hostname</th>
                      <th style={styles.th}>Status</th>
                      <th style={styles.th}>Active Tasks</th>
                      <th style={styles.th}>Processed</th>
                      <th style={styles.th}>Pool</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workers.length === 0 ? (
                      <tr>
                        <td colSpan="5" style={styles.emptyCell}>
                          No workers connected
                        </td>
                      </tr>
                    ) : (
                      workers.map((worker, idx) => {
                        // Flower API returns workers with different structure
                        // Handle both possible formats
                        const hostname = worker.hostname || worker.name || 'N/A'
                        const status = worker.status || worker.alive ? 'online' : 'offline'
                        const active = worker.active || worker.active_tasks || 0
                        const processed = worker.processed || worker.total || 0
                        const poolType = worker.pool?.type || worker.pool || 'N/A'
                        
                        return (
                          <tr key={idx}>
                            <td style={styles.td}>{hostname}</td>
                            <td style={styles.td}>
                              <span style={{
                                ...styles.badge,
                                backgroundColor: status === 'online' ? '#4ade80' : '#f87171'
                              }}>
                                {status}
                              </span>
                            </td>
                            <td style={styles.td}>{active}</td>
                            <td style={styles.td}>{processed}</td>
                            <td style={styles.td}>{poolType}</td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}
            
            {activeView === 'tasks' && (
              <div style={styles.tableContainer}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Name</th>
                      <th style={styles.th}>UUID</th>
                      <th style={styles.th}>State</th>
                      <th style={styles.th}>Received</th>
                      <th style={styles.th}>Runtime</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!tasks || tasks.length === 0 ? (
                      <tr>
                        <td colSpan="5" style={styles.emptyCell}>
                          No tasks found
                        </td>
                      </tr>
                    ) : (
                      tasks.map((task, idx) => (
                        <tr key={idx}>
                          <td style={styles.td}>{task.name || 'N/A'}</td>
                          <td style={styles.td}>
                            <span style={styles.uuid}>{task.uuid?.substring(0, 8) || 'N/A'}...</span>
                          </td>
                          <td style={styles.td}>
                            <span style={{
                              ...styles.badge,
                              backgroundColor: getStateColor(task.state)
                            }}>
                              {task.state || 'UNKNOWN'}
                            </span>
                          </td>
                          <td style={styles.td}>{formatTimestamp(task.received)}</td>
                          <td style={styles.td}>
                            {task.runtime ? `${(task.runtime).toFixed(2)}s` : 'N/A'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
            
            {activeView === 'queues' && (
              <div style={styles.tableContainer}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Queue Name</th>
                      <th style={styles.th}>Messages</th>
                      <th style={styles.th}>Consumers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!queues || Object.keys(queues).length === 0 ? (
                      <tr>
                        <td colSpan="3" style={styles.emptyCell}>
                          No queues found
                        </td>
                      </tr>
                    ) : (
                      Object.entries(queues).map(([name, queue], idx) => (
                        <tr key={idx}>
                          <td style={styles.td}>{name}</td>
                          <td style={styles.td}>{queue.messages || 0}</td>
                          <td style={styles.td}>{queue.consumers || 0}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
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
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem 2rem',
    borderBottom: '1px solid #333333',
    backgroundColor: '#000000',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 400,
    color: '#ffffff',
    margin: 0,
    letterSpacing: '0.05em',
  },
  tabs: {
    display: 'flex',
    gap: '0.5rem',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    border: '1px solid #333333',
    backgroundColor: 'transparent',
    color: '#ffffff',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 400,
    letterSpacing: '0.05em',
    transition: 'all 0.2s ease',
    outline: 'none',
  },
  tabActive: {
    backgroundColor: '#ffffff',
    color: '#000000',
    border: '1px solid #ffffff',
  },
  tabInactive: {
    backgroundColor: 'transparent',
    color: '#ffffff',
  },
  content: {
    flex: 1,
    position: 'relative',
    overflow: 'auto',
    backgroundColor: '#000000',
    padding: '2rem',
  },
  tableContainer: {
    width: '100%',
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    color: '#ffffff',
  },
  th: {
    padding: '1rem',
    textAlign: 'left',
    borderBottom: '1px solid #333333',
    fontSize: '0.875rem',
    fontWeight: 400,
    letterSpacing: '0.05em',
    color: '#cccccc',
  },
  td: {
    padding: '1rem',
    borderBottom: '1px solid #1a1a1a',
    fontSize: '0.875rem',
    letterSpacing: '0.05em',
    color: '#ffffff',
  },
  emptyCell: {
    padding: '2rem',
    textAlign: 'center',
    color: '#999999',
    fontSize: '0.875rem',
    letterSpacing: '0.05em',
  },
  badge: {
    display: 'inline-block',
    padding: '0.25rem 0.75rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: 500,
    letterSpacing: '0.05em',
  },
  uuid: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#999999',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    padding: '2rem',
    textAlign: 'center',
  },
  errorText: {
    fontSize: '1rem',
    color: '#ffffff',
    marginBottom: '0.5rem',
    letterSpacing: '0.05em',
  },
  errorSubtext: {
    fontSize: '0.875rem',
    color: '#999999',
    letterSpacing: '0.05em',
    marginTop: '1rem',
  },
  errorList: {
    fontSize: '0.875rem',
    color: '#cccccc',
    marginTop: '1rem',
    marginLeft: '2rem',
    lineHeight: '1.8',
    letterSpacing: '0.05em',
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    padding: '2rem',
  },
  loadingText: {
    fontSize: '1rem',
    color: '#ffffff',
    letterSpacing: '0.05em',
  },
  code: {
    backgroundColor: '#1a1a1a',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontFamily: 'monospace',
    fontSize: '0.875rem',
    color: '#ffffff',
  },
}
