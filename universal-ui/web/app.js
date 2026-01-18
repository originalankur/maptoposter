/**
 * Maptoposter Universal UI - Application Logic (DUAL MODE)
 * 
 * MODE A: Automatic generation via localhost server (if available)
 * MODE B: Fallback to command generation (always available)
 */

// Configuration
const SERVER_URL = 'http://127.0.0.1:8001';
const SERVER_CHECK_TIMEOUT = 2000; // 2 seconds

// DOM Elements
const form = document.getElementById('posterForm');
const cityInput = document.getElementById('city');
const countryInput = document.getElementById('country');
const themeSelect = document.getElementById('theme');
const themeDescription = document.getElementById('themeDescription');
const radiusInput = document.getElementById('radius');
const radiusValue = document.getElementById('radiusValue');

const generateBtn = document.getElementById('generateBtn');
const commandSection = document.getElementById('commandSection');
const commandText = document.getElementById('commandText');
const copyBtn = document.getElementById('copyBtn');
const loadPosterBtn = document.getElementById('loadPosterBtn');

const statusSection = document.getElementById('statusSection');
const statusMessage = document.getElementById('statusMessage');

const previewSection = document.getElementById('previewSection');
const posterImage = document.getElementById('posterImage');
const previewDetails = document.getElementById('previewDetails');

const serverStatusBadge = document.getElementById('serverStatus');
const modeIndicator = document.getElementById('modeIndicator');

// State
let currentCommand = '';
let isGenerating = false;
let serverAvailable = false;
let serverMode = 'checking'; // 'checking', 'available', 'unavailable'
let generationStartTime = null;
let progressTimer = null;

/**
 * Initialize the application
 */
function init() {
    populateThemeSelect();
    attachEventListeners();
    checkServerAvailability();
    console.log('Maptoposter Universal UI (Dual Mode) initialized');
}

/**
 * Check if local server is available
 */
async function checkServerAvailability() {
    updateServerStatus('checking');
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), SERVER_CHECK_TIMEOUT);
        
        const response = await fetch(`${SERVER_URL}/health`, {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'ok') {
                serverAvailable = true;
                serverMode = 'available';
                updateServerStatus('available');
                updateGenerateButtonText('automatic');
                return;
            }
        }
    } catch (error) {
        // Server not available - this is expected if not running
        console.log('Server not available, using command generation mode');
    }
    
    serverAvailable = false;
    serverMode = 'unavailable';
    updateServerStatus('unavailable');
    updateGenerateButtonText('manual');
}

/**
 * Update server status display
 */
function updateServerStatus(status) {
    if (!serverStatusBadge || !modeIndicator) return;
    
    serverStatusBadge.className = 'server-status';
    
    switch (status) {
        case 'checking':
            serverStatusBadge.classList.add('checking');
            serverStatusBadge.textContent = '⋯ Checking server...';
            modeIndicator.textContent = 'Checking connection...';
            break;
        case 'available':
            serverStatusBadge.classList.add('online');
            serverStatusBadge.textContent = '● Server Online';
            modeIndicator.innerHTML = '🚀 <strong>Automatic Mode</strong> - One-click generation enabled!';
            break;
        case 'unavailable':
            serverStatusBadge.classList.add('offline');
            serverStatusBadge.textContent = '○ Server Offline';
            modeIndicator.innerHTML = '📋 <strong>Manual Mode</strong> - Run command: <code>python universal-ui/runner/run_local.py --serve</code>';
            break;
    }
}

/**
 * Update generate button text based on mode
 */
function updateGenerateButtonText(mode) {
    const btnText = generateBtn.querySelector('.btn-text');
    if (!btnText) return;
    
    if (mode === 'automatic') {
        btnText.textContent = '🎨 Generate Poster';
    } else {
        btnText.textContent = '📋 Show Command';
    }
}

/**
 * Populate theme select dropdown from themes.js
 */
function populateThemeSelect() {
    themeSelect.innerHTML = '';
    
    AVAILABLE_THEMES.forEach(theme => {
        const option = document.createElement('option');
        option.value = theme.value;
        option.textContent = theme.label;
        option.dataset.description = theme.description;
        
        if (theme.value === DEFAULT_THEME) {
            option.selected = true;
        }
        
        themeSelect.appendChild(option);
    });
    
    updateThemeDescription();
}

/**
 * Update theme description text
 */
function updateThemeDescription() {
    const selectedOption = themeSelect.options[themeSelect.selectedIndex];
    const description = selectedOption.dataset.description || '';
    themeDescription.textContent = description;
}

/**
 * Attach event listeners
 */
function attachEventListeners() {
    form.addEventListener('submit', handleFormSubmit);
    themeSelect.addEventListener('change', updateThemeDescription);
    radiusInput.addEventListener('input', handleRadiusChange);
    copyBtn.addEventListener('click', handleCopyCommand);
    loadPosterBtn.addEventListener('click', handleLoadPoster);
}

/**
 * Handle form submission - DUAL MODE
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (isGenerating) {
        return;
    }
    
    // Validate city input
    const city = cityInput.value.trim();
    if (!city) {
        showStatus('Please enter a city name', 'error');
        cityInput.focus();
        return;
    }
    
    // Get form values
    const country = countryInput.value.trim();
    const theme = themeSelect.value;
    const radius = parseInt(radiusInput.value);
    
    if (serverAvailable) {
        // MODE A: Automatic generation via server
        await generatePosterAutomatic(city, country, theme, radius);
    } else {
        // MODE B: Show command for manual execution
        generateCommandManual(city, country, theme, radius);
    }
}

/**
 * MODE A: Automatic generation via server
 */
async function generatePosterAutomatic(city, country, theme, radius) {
    setGenerating(true);
    generationStartTime = Date.now();
    showStatus('⏳ Generating poster... This typically takes 3-5 minutes for large cities.', 'info');
    
    // Start progress timer
    startProgressTimer();
    
    // Hide previous results
    previewSection.classList.add('hidden');
    
    try {
        const response = await fetch(`${SERVER_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                city: city,
                country: country || '',
                theme: theme || '',
                radius: radius
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'ok') {
            showStatus(`Poster generated successfully! ${data.message || ''}`, 'success');
            
            // Load the generated image
            if (data.image_path) {
                showStatus('Loading poster image...', 'info');
                // Since we can't directly load local files, show instructions
                previewDetails.textContent = `Image saved to: ${data.image_path}`;
                previewSection.classList.remove('hidden');
                
                showStatus('✓ Poster saved! Click "Load Poster" below to view it.', 'success');
            }
        } else {
            const errorMsg = data.message || 'Unknown error occurred';
            showStatus(`Error: ${errorMsg}`, 'error');
        }
    } catch (error) {
        showStatus(`Error connecting to server: ${error.message}`, 'error');
    } finally {
        stopProgressTimer();
        setGenerating(false);
    }
}

/**
 * MODE B: Generate command for manual execution
 */
function generateCommandManual(city, country, theme, radius) {
    const command = generateCommand(city, country, theme, radius);
    currentCommand = command;
    
    // Display command
    commandText.textContent = command;
    commandSection.classList.remove('hidden');
    
    // Scroll to command section
    commandSection.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
    });
    
    // Show success message
    showStatus('Command generated! Copy and run it in your terminal.', 'info');
}

/**
 * Generate the terminal command
 */
function generateCommand(city, country, theme, radius) {
    const runnerPath = '../runner/run_local.py';
    
    let cmd = `python3 ${runnerPath}`;
    cmd += ` --city "${city}"`;
    
    if (country) {
        cmd += ` --country "${country}"`;
    }
    
    if (theme && theme !== DEFAULT_THEME) {
        cmd += ` --theme ${theme}`;
    }
    
    if (radius && radius !== 5000) {
        cmd += ` --radius ${radius}`;
    }
    
    return cmd;
}

/**
 * Handle radius slider change
 */
function handleRadiusChange(e) {
    const value = e.target.value;
    radiusValue.textContent = value;
}

/**
 * Handle copy command button click
 */
function handleCopyCommand() {
    const command = commandText.textContent;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(command)
            .then(() => showCopySuccess())
            .catch(() => fallbackCopy(command));
    } else {
        fallbackCopy(command);
    }
}

/**
 * Fallback copy method for older browsers
 */
function fallbackCopy(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopySuccess();
        } else {
            showStatus('Failed to copy command', 'error');
        }
    } catch (err) {
        showStatus('Failed to copy command', 'error');
    }
    
    document.body.removeChild(textArea);
}

/**
 * Show copy success feedback
 */
function showCopySuccess() {
    const originalText = copyBtn.querySelector('.btn-text').textContent;
    const btnText = copyBtn.querySelector('.btn-text');
    
    btnText.textContent = '✓ Copied!';
    copyBtn.style.background = 'var(--color-success)';
    copyBtn.style.color = 'white';
    copyBtn.style.borderColor = 'var(--color-success)';
    
    setTimeout(() => {
        btnText.textContent = originalText;
        copyBtn.style.background = '';
        copyBtn.style.color = '';
        copyBtn.style.borderColor = '';
    }, 2000);
}

/**
 * Handle load poster button click
 */
function handleLoadPoster() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/png,image/jpeg,image/jpg';
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            loadPosterFile(file);
        }
    });
    
    fileInput.click();
}

/**
 * Load and display poster file
 */
function loadPosterFile(file) {
    if (!file.type.startsWith('image/')) {
        showStatus('Please select a valid image file', 'error');
        return;
    }
    
    showStatus('Loading poster...', 'info');
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        posterImage.src = e.target.result;
        
        const fileSize = formatFileSize(file.size);
        const fileName = file.name;
        previewDetails.textContent = `${fileName} • ${fileSize}`;
        
        previewSection.classList.remove('hidden');
        
        previewSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest' 
        });
        
        showStatus('Poster loaded successfully!', 'success');
    };
    
    reader.onerror = function() {
        showStatus('Failed to load poster image', 'error');
    };
    
    reader.readAsDataURL(file);
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Set generating state
 */
function startProgressTimer() {
    progressTimer = setInterval(() => {
        if (generationStartTime) {
            const elapsed = Math.floor((Date.now() - generationStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            showStatus(`⏳ Still generating... Elapsed time: ${timeStr} (typically 3-5 minutes)`, 'info');
        }
    }, 5000); // Update every 5 seconds
}

function stopProgressTimer() {
    if (progressTimer) {
        clearInterval(progressTimer);
        progressTimer = null;
    }
    generationStartTime = null;
}

function setGenerating(generating) {
    isGenerating = generating;
    const btnText = generateBtn.querySelector('.btn-text');
    
    if (generating) {
        btnText.textContent = '⏳ Generating...';
        generateBtn.disabled = true;
        generateBtn.style.opacity = '0.6';
        generateBtn.style.cursor = 'not-allowed';
    } else {
        updateGenerateButtonText(serverAvailable ? 'automatic' : 'manual');
        generateBtn.disabled = false;
        generateBtn.style.opacity = '';
        generateBtn.style.cursor = '';
    }
}

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusSection.classList.remove('hidden');
    
    // Auto-hide after 5 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            statusSection.classList.add('hidden');
        }, 5000);
    }
    
    // Scroll status into view if needed
    if (type === 'error') {
        statusSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest' 
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
