import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

// Configure axios defaults
axios.defaults.timeout = 30000 // 30 seconds default timeout

function App() {
  const [city, setCity] = useState('')
  const [country, setCountry] = useState('')
  const [theme, setTheme] = useState('feature_based')
  const [distance, setDistance] = useState(29000)
  const [themes, setThemes] = useState([])
  const [loading, setLoading] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [generatedImage, setGeneratedImage] = useState(null)
  const [selectedThemeInfo, setSelectedThemeInfo] = useState(null)

  // Fetch available themes on mount
  useEffect(() => {
    fetchThemes()
  }, [])

  // Poll job status when we have a job ID
  useEffect(() => {
    if (jobId && jobStatus?.status !== 'completed' && jobStatus?.status !== 'failed') {
      const interval = setInterval(() => {
        checkJobStatus(jobId)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [jobId, jobStatus])

  // Update selected theme info when theme changes
  useEffect(() => {
    const themeInfo = themes.find(t => t.name === theme)
    setSelectedThemeInfo(themeInfo)
  }, [theme, themes])

  const fetchThemes = async () => {
    try {
      const response = await axios.get('/api/themes', {
        timeout: 10000 // 10 second timeout
      })
      setThemes(response.data)
    } catch (error) {
      console.error('Error fetching themes:', error)
      // Set a default theme if fetch fails
      setThemes([{
        name: 'feature_based',
        display_name: 'Feature-Based Shading',
        description: 'Classic black & white with road hierarchy',
        colors: {
          bg: '#FFFFFF',
          text: '#000000',
          water: '#C0C0C0',
          parks: '#F0F0F0',
          road_motorway: '#0A0A0A',
          road_primary: '#1A1A1A'
        }
      }])
    }
  }

  const generatePoster = async (e) => {
    e.preventDefault()
    setLoading(true)
    setJobStatus(null)
    setGeneratedImage(null)

    try {
      const response = await axios.post('/api/generate', {
        city,
        country,
        theme,
        distance: parseInt(distance)
      }, {
        timeout: 30000 // 30 second timeout for initial request
      })
      setJobId(response.data.job_id)
      setJobStatus(response.data)
    } catch (error) {
      console.error('Error generating poster:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Error generating poster'
      alert(errorMsg)
      setLoading(false)
    }
  }

  const checkJobStatus = async (id) => {
    try {
      const response = await axios.get(`/api/job/${id}`, {
        timeout: 10000 // 10 second timeout for status checks
      })
      setJobStatus(response.data)

      if (response.data.status === 'completed') {
        setGeneratedImage(response.data.file_url)
        setLoading(false)
      } else if (response.data.status === 'failed') {
        alert('Poster generation failed: ' + response.data.message)
        setLoading(false)
        setJobId(null)
      }
    } catch (error) {
      console.error('Error checking job status:', error)
      // Don't alert on polling errors, just log them
    }
  }

  const downloadImage = () => {
    if (generatedImage) {
      const link = document.createElement('a')
      link.href = generatedImage
      link.download = `${city.toLowerCase()}_${theme}_poster.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  return (
    <div className="App">
      <header className="header">
        <h1>🗺️ Map Poster Generator</h1>
        <p>Create beautiful, minimalist map posters for any city in the world</p>
      </header>

      <div className="container">
        <div className="form-section">
          <form onSubmit={generatePoster}>
            <div className="form-group">
              <label htmlFor="city">City</label>
              <input
                type="text"
                id="city"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g., New York"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="country">Country</label>
              <input
                type="text"
                id="country"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                placeholder="e.g., USA"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="theme">Theme</label>
              <select
                id="theme"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
              >
                {themes.map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.display_name}
                  </option>
                ))}
              </select>
              {selectedThemeInfo && (
                <p className="theme-description">{selectedThemeInfo.description}</p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="distance">
                Map Radius: {(distance / 1000).toFixed(1)} km
              </label>
              <input
                type="range"
                id="distance"
                min="4000"
                max="30000"
                step="1000"
                value={distance}
                onChange={(e) => setDistance(e.target.value)}
              />
              <div className="distance-guide">
                <small>Small (4-6km) • Medium (8-12km) • Large (15-30km)</small>
              </div>
            </div>

            {selectedThemeInfo && (
              <div className="theme-preview">
                <h3>Theme Colors</h3>
                <div className="color-palette">
                  <div className="color-item">
                    <div className="color-box" style={{ backgroundColor: selectedThemeInfo.colors.bg }}></div>
                    <span>Background</span>
                  </div>
                  <div className="color-item">
                    <div className="color-box" style={{ backgroundColor: selectedThemeInfo.colors.text }}></div>
                    <span>Text</span>
                  </div>
                  <div className="color-item">
                    <div className="color-box" style={{ backgroundColor: selectedThemeInfo.colors.water }}></div>
                    <span>Water</span>
                  </div>
                  <div className="color-item">
                    <div className="color-box" style={{ backgroundColor: selectedThemeInfo.colors.parks }}></div>
                    <span>Parks</span>
                  </div>
                  <div className="color-item">
                    <div className="color-box" style={{ backgroundColor: selectedThemeInfo.colors.road_motorway }}></div>
                    <span>Motorway</span>
                  </div>
                  <div className="color-item">
                    <div className="color-box" style={{ backgroundColor: selectedThemeInfo.colors.road_primary }}></div>
                    <span>Primary</span>
                  </div>
                </div>
              </div>
            )}

            <button type="submit" disabled={loading} className="generate-btn">
              {loading ? 'Generating...' : 'Generate Poster'}
            </button>
          </form>

          {jobStatus && (
            <div className="status-section">
              <div className="status-message">
                <strong>Status:</strong> {jobStatus.status}
              </div>
              <div className="status-message">
                {jobStatus.message}
              </div>
              {jobStatus.status === 'processing' && (
                <>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${jobStatus.progress}%` }}
                    ></div>
                  </div>
                  <div className="status-note">
                    <small>⏱️ This may take 2-5 minutes depending on map size...</small>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="preview-section">
          {generatedImage ? (
            <div className="result">
              <h2>Your Poster</h2>
              <img
                src={generatedImage}
                alt="Generated map poster"
                className="generated-image"
              />
              <button onClick={downloadImage} className="download-btn">
                Download Poster
              </button>
            </div>
          ) : (
            <div className="placeholder">
              <div className="placeholder-content">
                <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                  <rect x="20" y="20" width="80" height="80" rx="4" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4"/>
                  <path d="M40 60 L50 50 L60 60 L70 45 L80 55" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <circle cx="45" cy="40" r="3" fill="currentColor"/>
                </svg>
                <p>Your generated poster will appear here</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <footer className="footer">
        <p>Powered by OpenStreetMap • Map data © OpenStreetMap contributors</p>
      </footer>
    </div>
  )
}

export default App
