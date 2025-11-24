# Sales Intelligence Web Application

Professional Streamlit-based web interface for the Sales Intelligence & Automation System.

## Features

### Professional UI/UX
- ✅ Modern, clean design with professional styling
- ✅ Custom CSS for enhanced visual appeal
- ✅ Responsive layout for all screen sizes
- ✅ Professional color scheme and typography
- ✅ Enhanced metric cards and visualizations
- ✅ Improved sidebar with gradient background

### Pages

1. **Dashboard** - Real-time metrics and top priority accounts
2. **Account Scoring** - AI-powered account scoring with charts
3. **Natural Language Query** - Ask questions in plain English
4. **Semantic Search** - AI-powered intent-based search
5. **Unmatched Emails** - Create leads from unmatched emails
6. **Account Details** - Complete account information view
7. **Email Threads** - View conversations and generate AI replies

## Styling Improvements

### Custom CSS Injection
The app includes professional custom CSS for:
- Enhanced headers and typography
- Professional metric cards with hover effects
- Improved button styling with gradients
- Better info/warning/error boxes
- Enhanced table styling
- Professional sidebar with gradient
- Responsive design elements

### Color Scheme
- Primary: #1f77b4 (Professional Blue)
- Secondary: #2c3e50 (Dark Gray)
- Success: #27ae60 (Green)
- Warning: #f39c12 (Orange)
- Error: #e74c3c (Red)

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT_ID="maharani-sales-hub-11-2025"
export GCP_REGION="us-central1"

# Run the application
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Configuration

### Streamlit Config
Configuration file: `.streamlit/config.toml`

### Environment Variables
- `GCP_PROJECT_ID` - Google Cloud Project ID
- `GCP_REGION` - GCP Region
- `GOOGLE_CLIENT_ID` - Google OAuth Client ID (optional)

## Deployment

### Deploy to Cloud Run

```bash
gcloud run deploy sales-intelligence-web \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=maharani-sales-hub-11-2025,GCP_REGION=us-central1 \
  --project=maharani-sales-hub-11-2025
```

## Professional Features

### Enhanced Metrics
- Large, readable numbers
- Color-coded values
- Professional card styling
- Hover effects

### Improved Navigation
- Clean sidebar design
- Professional branding
- Clear page navigation
- Status indicators

### Better User Experience
- Professional loading states
- Enhanced error messages
- Improved form inputs
- Better table presentation

## Screenshots

### Dashboard
- Real-time metrics in professional cards
- Top priority accounts table
- Refresh functionality

### Account Scoring
- Distribution charts
- Detailed score breakdowns
- AI reasoning display

### Natural Language Query
- Plain English input
- SQL generation preview
- Results table with summaries

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari

## Notes

- The app uses Streamlit's built-in components with custom CSS enhancements
- Authentication is currently simple email-based (Google OAuth ready)
- BigQuery integration requires GCP credentials
- Cloud Functions integration requires deployed functions
