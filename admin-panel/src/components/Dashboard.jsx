import { supabase } from '../lib/supabase'
import { useState, useEffect } from 'react'
import FlowerMonitoring from './FlowerMonitoring'
import AgentSessions from './AgentSessions'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('sessions')

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const handleLogout = async () => {
    await supabase.auth.signOut()
  }

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.loadingText}>Loading...</div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Admin Panel</h1>
        <div style={styles.userInfo}>
          <span style={styles.userEmail}>{user?.email}</span>
          <button onClick={handleLogout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </div>
      <div style={styles.content}>
        <div style={styles.tabs}>
          <div style={styles.tabContainer}>
            <button
              onClick={() => setActiveTab('sessions')}
              style={{
                ...styles.tab,
                ...(activeTab === 'sessions' ? styles.tabActive : {}),
              }}
            >
              Agent Sessions
            </button>
            <button
              onClick={() => setActiveTab('flower')}
              style={{
                ...styles.tab,
                ...(activeTab === 'flower' ? styles.tabActive : {}),
              }}
            >
              Flower Monitoring
            </button>
            <button
              onClick={() => setActiveTab('context-worker')}
              style={{
                ...styles.tab,
                ...(activeTab === 'context-worker' ? styles.tabActive : {}),
              }}
            >
              Context Worker
            </button>
          </div>
        </div>
        <div style={styles.tabContent}>
          {activeTab === 'sessions' ? (
            <AgentSessions />
          ) : activeTab === 'flower' ? (
            <FlowerMonitoring />
          ) : (
            <FlowerMonitoring
              title="Context Worker Monitoring"
              basePath="/api/context-monitoring"
            />
          )}
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    width: '100%',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#000000',
    color: '#ffffff',
  },
  loadingContainer: {
    width: '100%',
    height: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
    color: '#ffffff',
  },
  loadingText: {
    fontSize: '1rem',
    fontWeight: 400,
    letterSpacing: '0.05em',
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
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem',
  },
  userEmail: {
    fontSize: '0.875rem',
    color: '#cccccc',
    letterSpacing: '0.05em',
  },
  logoutButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'transparent',
    color: '#ffffff',
    border: '1px solid #333333',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 400,
    letterSpacing: '0.05em',
    transition: 'all 0.2s ease',
    outline: 'none',
  },
  content: {
    flex: 1,
    overflow: 'hidden',
    backgroundColor: '#000000',
    display: 'flex',
    flexDirection: 'column',
  },
  tabs: {
    borderBottom: '1px solid #333333',
    backgroundColor: '#000000',
  },
  tabContainer: {
    display: 'flex',
    gap: '0.5rem',
    padding: '0 2rem',
  },
  tab: {
    padding: '1rem 1.5rem',
    backgroundColor: 'transparent',
    color: '#cccccc',
    border: 'none',
    borderBottom: '2px solid transparent',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 400,
    letterSpacing: '0.05em',
    transition: 'all 0.2s ease',
    outline: 'none',
  },
  tabActive: {
    color: '#ffffff',
    borderBottomColor: '#4A90E2',
  },
  tabContent: {
    flex: 1,
    overflow: 'hidden',
  },
}


