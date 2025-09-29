# AI Travel Advisor - Streamlit Frontend

A comprehensive Streamlit frontend for the AI Travel Advisor application, featuring conversational planning, knowledge management, and destination tracking.

## 🌟 Features

### 📍 Destinations Page
- **Search & Filter**: Search destinations by name with tag-based filtering
- **Tag System**: Auto-categorization (Beach, Mountains, City, Cultural, Adventure, Luxury, Budget, Family-Friendly)
- **CRUD Operations**: Create, Read, Update, Soft Delete destinations
- **Agent Run History**: View last agent run for each destination with status and details
- **Enhanced Cards**: Rich destination cards showing tags, creation date, and last planning activity

### 📚 Knowledge Base Page
- **File Management**: Upload PDF, Markdown, and Text files
- **Version History**: Track file versions and changes over time
- **Ingestion Progress**: Real-time progress tracking for document processing
- **Chunk Preview**: Search and preview document chunks with metadata
- **Processing Options**: Configurable chunk size and overlap settings
- **Status Tracking**: Visual indicators for processing status (Completed, Processing, Failed, Pending)

### 🗺️ Plan & Chat Page
- **Conversational Interface**: Natural language travel planning with constraint extraction
- **Live Progress Tracking**: Real-time node/tool execution progress
- **Structured Outputs**: JSON itinerary + Markdown explanation + citations
- **What-If Refinements**: Dynamic refinement suggestions based on current plan
- **Constraint Management**: Automatic extraction and tracking of budget, dates, preferences
- **Enhanced Right Rail**:
  - **Tools Used**: Execution times, performance metrics, argument details
  - **Decisions**: AI reasoning with impact assessment and confidence scores
  - **Constraint Checks**: Violation detection and resolution tracking
  - **Planning Summary**: Quality scores and process metrics

## 🏗️ Architecture

### Core Components
```
frontend/
├── app.py                 # Main application entry point
├── pages/
│   ├── destinations.py    # Destinations management
│   ├── knowledge_base.py  # Knowledge base operations
│   └── plan.py           # Conversational planning interface
├── utils/
│   └── api_client.py     # Backend API communication
└── README.md             # This file
```

### Key Features Implementation

#### Conversational Planning
- **Thread Management**: Persistent conversation threads with refinement support
- **Constraint Extraction**: Automatic parsing of budget, dates, airports, preferences
- **Live Progress**: Simulated real-time updates (WebSocket-ready architecture)
- **Refinement Engine**: Context-aware what-if suggestions

#### Enhanced Right Rail
- **Tool Analytics**: Performance monitoring with duration tracking
- **Decision Intelligence**: Categorized AI decisions with impact scoring
- **Constraint Verification**: Real-time constraint checking and violation resolution
- **Quality Assessment**: Planning quality scoring and recommendations

#### Knowledge Management
- **Multi-format Support**: PDF, Markdown, Text file processing
- **Progress Tracking**: Multi-stage ingestion with visual progress indicators
- **Chunk Intelligence**: Searchable document chunks with metadata
- **Version Control**: File versioning with restore capabilities

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Streamlit 1.28+
- Backend API running on http://localhost:8000

### Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install streamlit pandas requests httpx asyncio websockets
   ```

2. **Environment Setup**
   ```bash
   export BACKEND_URL="http://localhost:8000"  # Optional, defaults to localhost:8000
   ```

3. **Start Frontend**
   ```bash
   # From project root
   ./start-frontend.sh

   # Or manually from frontend directory
   cd frontend
   streamlit run app.py --server.port 8501
   ```

4. **Access Application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000

## 📊 Usage Guide

### Planning a Trip
1. Navigate to **Plan & Chat** page
2. Enter natural language request: *"Plan a 5-day family trip to Tokyo with $3000 budget, arriving March 15th"*
3. Watch live progress in the interface
4. Review structured itinerary with JSON data
5. Use refinement suggestions for modifications
6. Monitor tools, decisions, and constraints in the right rail

### Managing Destinations
1. Go to **Destinations** page
2. Use search and tag filters to find destinations
3. Create new destinations with the **Add Destination** button
4. View agent run history for planning context
5. Edit or soft delete destinations as needed

### Knowledge Base Operations
1. Visit **Knowledge Base** page
2. Create knowledge entries linked to destinations
3. Upload PDF/Markdown/Text files with processing options
4. Monitor ingestion progress with real-time updates
5. Preview document chunks and search within content
6. Track version history and manage file versions

## 🔧 Configuration

### Environment Variables
- `BACKEND_URL`: Backend API endpoint (default: http://localhost:8000)
- `STREAMLIT_SERVER_PORT`: Frontend port (default: 8501)

### API Integration
The frontend communicates with the backend through:
- Authentication endpoints (`/api/v1/auth/*`)
- Destination management (`/api/v1/destinations/*`)
- Knowledge base operations (`/api/v1/knowledge/*`)
- Agent planning (`/api/v1/qa/*`)

### Session Management
- Automatic token refresh
- Persistent conversation threads
- State management across page navigation
- Graceful error handling and user feedback

## 🎨 UI/UX Features

### Design Principles
- **Conversational First**: Natural language interaction
- **Progressive Disclosure**: Information revealed as needed
- **Real-time Feedback**: Live progress and status updates
- **Context Preservation**: Thread-based conversations
- **Visual Intelligence**: Rich data visualization

### Responsive Design
- **Grid Layouts**: Adaptive destination cards
- **Flexible Columns**: Dynamic content sizing
- **Mobile Friendly**: Streamlit's responsive framework
- **Accessibility**: Semantic HTML and clear navigation

### Interactive Elements
- **Live Progress Bars**: Multi-stage processing visualization
- **Expandable Sections**: Collapsible content areas
- **Search & Filter**: Real-time content filtering
- **Modal Dialogs**: Context-aware action panels

## 🔮 Future Enhancements

### WebSocket Integration
- Real-time streaming updates
- Live tool execution progress
- Instant refinement feedback

### Advanced Features
- Collaborative planning sessions
- Plan versioning and comparison
- Advanced constraint templating
- Integration with external booking APIs

### Analytics Dashboard
- Planning success metrics
- Tool performance analytics
- User interaction patterns
- Knowledge base usage statistics

## 🐛 Troubleshooting

### Common Issues
1. **Connection Errors**: Verify backend is running on correct port
2. **Authentication Failures**: Check API credentials and token refresh
3. **File Upload Issues**: Ensure proper file permissions and size limits
4. **Performance**: Monitor tool execution times in right rail

### Debug Mode
Enable Streamlit debug mode for detailed error information:
```bash
streamlit run app.py --logger.level=debug
```

## 📝 Development Notes

### Code Organization
- **Modular Design**: Separate pages for different functionality
- **Shared Components**: Reusable UI elements and utilities
- **State Management**: Centralized session state handling
- **Error Handling**: Graceful degradation and user feedback

### Testing Considerations
- API endpoint validation
- Authentication flow testing
- File upload edge cases
- Conversation thread persistence
- Real-time update simulation

## 🎯 Implementation Highlights

### Conversational Thread Features
```python
# Constraint extraction from natural language
def extract_constraints_from_response(response, user_input):
    # Extract budget: "$3000" -> budget_usd: 3000
    # Extract dates: "March 15th" -> dates: {start: "March 15, 2024"}
    # Extract preferences: "family trip" -> preferences: {family: true}
```

### What-If Refinements
```python
# Dynamic refinement suggestions
def generate_refinement_suggestions(response):
    # "$300 cheaper", "Make it 7 days", "More adventurous"
    # Context-aware based on current constraints and itinerary
```

### Right Rail Intelligence
```python
# Enhanced tool tracking with performance metrics
def display_enhanced_tools_log():
    # Tool execution times, performance indicators
    # Arguments, call counts, success rates
```

### Live Progress Simulation
```python
# WebSocket-ready architecture for real-time updates
def display_live_progress_indicator():
    # Node progress, tool status, constraint checking
    # Streaming updates for seamless user experience
```

This frontend application provides a complete travel planning experience with intelligent conversation handling, comprehensive knowledge management, and detailed planning analytics.