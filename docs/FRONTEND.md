# Frontend Documentation

This document explains all components and functions in the MediGuard AI Next.js frontend.

## Table of Contents

- [Project Structure](#project-structure)
- [Main Page (`app/page.tsx`)](#main-page-apppagetsx)
- [Components](#components)
- [API Routes](#api-routes)
- [Styling](#styling)

---

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Main dashboard page
│   ├── layout.tsx            # Root layout
│   ├── globals.css           # Global styles
│   └── api/                  # API routes (proxies to backend)
│       ├── analyze/route.ts  # Analysis endpoint
│       └── sample-ids/route.ts # Sample IDs endpoint
├── components/
│   ├── Sidebar.tsx           # Navigation sidebar
│   ├── PatientInput.tsx     # Patient ID input form
│   ├── WorkflowVisualization.tsx # Workflow progress indicator
│   ├── AgentCard.tsx        # Individual agent results display
│   ├── RiskScoreBadge.tsx   # Risk score indicator
│   └── ResultsDisplay.tsx   # Combined results view
└── package.json             # Dependencies
```

---

## Main Page (`app/page.tsx`)

### Component: `Home()`

**Purpose:** Main dashboard page that orchestrates the entire analysis workflow.

**State Management:**
- `results` - Stores analysis results from all agents
- `isLoading` - Tracks if analysis is in progress
- `currentStep` - Tracks which agent is currently processing
- `error` - Stores error messages

**Key Functions:**

#### `handleAnalyze(patientId: string)`

**What it does:**
1. Resets state and sets loading to true
2. Sends POST request to `/api/analyze` with patient ID
3. Progressively updates UI as each agent completes:
   - Shows identity results → sets step to 'billing'
   - Shows billing results → sets step to 'discharge'
   - Shows discharge results → sets step to 'complete'
4. Handles errors and displays error messages
5. Sets loading to false when complete

**Progressive Loading:**
- Uses `setTimeout` to simulate progressive agent completion
- Updates results incrementally for better UX
- Shows workflow visualization updating in real-time

**Error Handling:**
- Catches network errors
- Displays user-friendly error messages
- Resets state on error

---

## Components

### `Sidebar.tsx`

**Purpose:** Fixed left navigation sidebar.

**What it displays:**
- MediGuard AI logo and branding
- Navigation links (Dashboard, Analysis History, Reports)
- Footer with version info

**Styling:**
- Fixed position, full height
- White background with shadow
- Active link highlighted in primary color

**Note:** Currently navigation links are placeholders (href="#")

---

### `PatientInput.tsx`

**Purpose:** Form component for entering patient ID and starting analysis.

**Props:**
- `onAnalyze: (patientId: string) => void` - Callback when form is submitted
- `isLoading: boolean` - Disables form during analysis

**Features:**
1. **Patient ID Input:**
   - Text input for UUID
   - Placeholder text
   - Disabled during loading

2. **Sample IDs Display:**
   - Fetches sample IDs from `/api/sample-ids` on mount
   - Shows first 4 sample IDs as clickable buttons
   - Clicking a sample ID fills the input field

3. **Submit Button:**
   - "Start Analysis" button
   - Shows loading spinner when `isLoading` is true
   - Disabled if input is empty or loading

**User Flow:**
1. User enters UUID or clicks sample ID
2. Clicks "Start Analysis"
3. Form calls `onAnalyze` callback with patient ID
4. Button shows "Analyzing..." with spinner

---

### `WorkflowVisualization.tsx`

**Purpose:** Visual indicator showing which agent is currently processing.

**Props:**
- `currentStep: 'identity' | 'billing' | 'discharge' | 'complete' | null`

**What it displays:**
- Three steps with icons:
  1. 🔍 Identity & Claims Fraud
  2. 💰 Billing Fraud
  3. 🚪 Discharge Blockers

**Visual States:**
- **Pending:** Gray icon, gray text
- **Active:** Primary color icon with pulse animation, "Processing..." badge
- **Completed:** Green checkmark icon, "Completed" badge

**Progress Indicators:**
- Shows connecting lines between steps
- Progress bar fills as steps complete
- Smooth transitions between states

**Usage:** Only displays when `currentStep` is not null or analysis is loading

---

### `AgentCard.tsx`

**Purpose:** Displays results from a single agent in a card format.

**Props:**
- `title: string` - Agent name
- `icon: string` - Emoji icon
- `data: any` - Agent results object
- `isLoading?: boolean` - Shows loading skeleton

**What it displays:**

1. **Loading State:**
   - Skeleton loader with animated pulse
   - Placeholder bars

2. **Risk Score:**
   - Uses `RiskScoreBadge` component
   - Shows `fraud_risk_score` or `billing_fraud_score`

3. **Flags:**
   - `identity_misuse_flag` - Shows "Detected" or "Not Detected" badge
   - `unnecessary_procedure_flag` - Same format
   - `discharge_ready` - Shows "Yes" or "No" badge

4. **Lists:**
   - `reasons` - Bulleted list of fraud reasons
   - `billing_flags` - Billing anomalies
   - `blockers` - Discharge blockers

5. **Explanations:**
   - `explanation` or `billing_explanation` - Text description

6. **Delay Hours:**
   - Shows estimated delay if available

**Color Coding:**
- Green badges for safe/normal states
- Red badges for detected issues
- Orange badges for warnings

---

### `RiskScoreBadge.tsx`

**Purpose:** Color-coded badge showing risk score.

**Props:**
- `score: number` - Risk score (0-100)
- `label?: string` - Label text (default: "Risk Score")

**Color Logic:**
- **0-39:** Green (success) - Low risk
- **40-69:** Orange (warning) - Medium risk
- **70-100:** Red (danger) - High risk

**Display:**
- Shows label, score, and "/100"
- Border and background match risk level

---

### `ResultsDisplay.tsx`

**Purpose:** Main container displaying results from all three agents.

**Props:**
- `results: { identity?, billing?, discharge?, final? }`
- `isLoading: { identity, billing, discharge }`

**Layout:**
- Three-column grid on large screens
- Single column on mobile
- Each agent in its own `AgentCard`

**Final Summary:**
- Shows combined results in gradient card
- Displays overall fraud risk, identity misuse status, discharge status
- Only shows if `results.final` exists

**Conditional Rendering:**
- Only renders if at least one result exists
- Hides if no results and not loading

---

## API Routes

### `app/api/analyze/route.ts`

**Purpose:** Proxy endpoint that forwards analysis requests to Python backend.

**Endpoint:** `POST /api/analyze`

**What it does:**
1. Receives patient_id from request body
2. Validates patient_id exists
3. Forwards request to Python backend (`PYTHON_API_URL/api/analyze`)
4. Returns backend response to frontend
5. Handles errors and returns appropriate status codes

**Request:**
```json
{
    "patient_id": "uuid-here"
}
```

**Response:** Backend analysis results (see backend docs)

**Error Handling:**
- 400 if patient_id missing
- 500 for backend errors
- Returns error message in response

---

### `app/api/sample-ids/route.ts`

**Purpose:** Proxy endpoint for getting sample patient IDs.

**Endpoint:** `GET /api/sample-ids`

**What it does:**
1. Forwards request to Python backend
2. Returns list of sample patient IDs
3. Returns empty array if backend unavailable (graceful degradation)

**Response:**
```json
{
    "ids": ["uuid1", "uuid2", ...]
}
```

---

## Styling

### Tailwind CSS Configuration

**Color Palette:**
- `primary`: #00BFA5 (Teal)
- `secondary`: #7B68EE (Purple)
- `success`: #10B981 (Green)
- `warning`: #F59E0B (Orange)
- `danger`: #EF4444 (Red)

**Usage:**
- All components use Tailwind utility classes
- Responsive design with `lg:` breakpoints
- Consistent spacing and shadows

### Component Styling Patterns

**Cards:**
- White background
- Rounded corners (`rounded-lg`)
- Subtle shadow (`shadow-sm`)
- Border (`border border-gray-200`)

**Buttons:**
- Primary color background
- Hover states
- Disabled states with opacity
- Loading spinners

**Tables:**
- Striped rows
- Hover effects
- Responsive with horizontal scroll on mobile

---

## State Flow

```
User enters patient ID
    ↓
handleAnalyze() called
    ↓
POST /api/analyze
    ↓
Backend processes (identity → billing → discharge)
    ↓
Frontend receives results progressively
    ↓
State updates: results.identity → results.billing → results.discharge
    ↓
UI updates: WorkflowVisualization shows progress
    ↓
ResultsDisplay shows each agent's results
    ↓
Final summary displayed
```

---

## Error Handling

**Network Errors:**
- Caught in `handleAnalyze()`
- Error message displayed in red banner
- State reset to allow retry

**Backend Errors:**
- Error message from backend displayed
- User-friendly error text
- No technical details exposed

**Loading States:**
- Buttons disabled during loading
- Loading spinners shown
- Skeleton loaders for results

---

## Responsive Design

**Breakpoints:**
- Mobile: Single column layout
- Tablet: 2-column grid for agent cards
- Desktop: 3-column grid for agent cards

**Sidebar:**
- Fixed on desktop
- Hidden on mobile (can be made toggleable)

**Tables:**
- Horizontal scroll on mobile
- Full width on desktop

---

## Performance Considerations

**Optimizations:**
- Progressive loading for better perceived performance
- Client-side state management (no unnecessary re-renders)
- API routes act as thin proxies (minimal processing)

**Future Improvements:**
- Add caching for sample IDs
- Implement request debouncing
- Add loading skeletons for better UX

