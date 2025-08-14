# EscaGCP Frontend Test Plan - Phase 8

## Overview

This document outlines the comprehensive testing strategy for the EscaGCP React frontend, designed to validate UI functionality, data integration with the Python escagcp tool, and ensure production readiness.

## Testing Objectives

### Primary Goals
1. **Functional Validation**: Ensure all UI components work correctly with real escagcp data
2. **Integration Testing**: Validate seamless integration with Python backend JSON output
3. **User Experience**: Verify intuitive user workflows and interactions
4. **Performance**: Ensure acceptable performance with various data sizes
5. **Accessibility**: Meet WCAG 2.1 AA standards
6. **Cross-browser Compatibility**: Support major browsers and viewports

### Success Criteria
- 100% of critical user paths tested and passing
- Zero accessibility violations on key pages
- All components handle edge cases gracefully
- Performance within acceptable thresholds (< 3s initial load, < 100ms interactions)
- Full compatibility with escagcp JSON data formats

## Test Scope

### In Scope
- All React frontend components and pages
- Data loading and visualization from escagcp JSON files
- Interactive graph features (node/edge selection, panels)
- Navigation and routing
- Settings and preferences
- Error handling and empty states
- Responsive design (mobile, tablet, desktop)
- Accessibility features
- Performance with large datasets

### Out of Scope
- Python backend testing (handled separately)
- GCP API integrations (mocked in tests)
- Authentication/authorization (not implemented yet)
- Real-time data updates (future feature)

## Test Categories

### 1. Unit Tests (Jest + React Testing Library)

**Target**: Individual components and utility functions
**Coverage Goal**: 85%+ line coverage

#### Components to Test:
- `LoadingSpinner` ✅ (Complete)
- `Header` (Navigation, theme toggle)
- `StatisticsCard` (Metric display, click handlers)
- `RiskBadge` (Risk level display)
- `NodeIcon` (Node type icons)
- `DataTable` (Sorting, filtering, pagination)
- `SidePanelLayout` (Panel open/close, animations)

#### Utility Functions:
- `lib/utils.ts` ✅ (Complete)
- `types/index.ts` helpers ✅ (Complete)
- Data formatting functions
- Color scheme utilities
- Risk calculation functions

#### Testing Patterns:
```typescript
describe('ComponentName', () => {
  it('should render without crashing', () => {
    render(<ComponentName />);
    expect(screen.getByRole('...')).toBeInTheDocument();
  });

  it('should handle props correctly', () => {
    render(<ComponentName prop="value" />);
    expect(screen.getByText('value')).toBeVisible();
  });

  it('should handle user interactions', async () => {
    const user = setupUser();
    const mockFn = jest.fn();
    render(<ComponentName onClick={mockFn} />);
    
    await user.click(screen.getByRole('button'));
    expect(mockFn).toHaveBeenCalled();
  });
});
```

### 2. Component Integration Tests (React Testing Library)

**Target**: Components with complex state and context interactions

#### Context Integration:
- `ThemeContext` with theme switching
- `SettingsContext` with settings persistence
- `GraphContext` with node/edge selection
- `QueryClient` integration with data fetching

#### Multi-Component Interactions:
- Dashboard page with statistics cards
- Graph page with canvas and panels
- Settings page with form controls
- Navigation between pages

### 3. End-to-End Tests (Playwright)

**Target**: Complete user workflows and browser behavior

#### Test Files Created:
- `dashboard.spec.ts` ✅ (Complete)
- `graph.spec.ts` ✅ (Complete)
- `findings.spec.ts` (Planned)
- `nodes.spec.ts` (Planned)
- `edges.spec.ts` (Planned)
- `settings.spec.ts` (Planned)

#### Key Workflows:
1. **Dashboard Navigation**
   - Load dashboard and verify statistics
   - Navigate to different pages
   - Handle loading and error states

2. **Graph Interaction**
   - Load graph visualization
   - Click nodes/edges to open panels
   - Use zoom and filter controls
   - Search for specific nodes

3. **Data Management**
   - View nodes and edges in table format
   - Sort and filter data tables
   - Export data functionality

4. **Settings Management**
   - Change theme preferences
   - Modify graph display settings
   - Persist settings across sessions

### 4. Accessibility Tests (Axe-Playwright)

**Target**: WCAG 2.1 AA compliance

#### Automated Checks:
- Color contrast ratios
- Keyboard navigation
- Screen reader compatibility
- Focus management
- Semantic HTML structure

#### Manual Verification:
- Tab order logic
- Skip links functionality
- Form label associations
- Error message clarity

### 5. Performance Tests

#### Metrics to Measure:
- Initial page load time (< 3 seconds)
- Time to interactive (< 5 seconds)
- Component render time (< 100ms)
- Large dataset handling (1000+ nodes)
- Memory usage with complex graphs

#### Test Scenarios:
- Small graph (< 50 nodes): Baseline performance
- Medium graph (100-500 nodes): Typical usage
- Large graph (1000+ nodes): Stress testing
- Empty data: Edge case handling

## Test Data Strategy

### EscaGCP Integration

#### Test Data Manager
**Location**: `src/test/data/testDataManager.ts` ✅ (Complete)

**Scenarios Available**:
1. `small_graph_high_risk`: 3 nodes, 2 edges, 1 critical attack path
2. `large_graph_mixed_risk`: 100+ nodes, mixed risk levels
3. `minimal_findings`: Low-risk scenario with minimal attack paths
4. `no_findings`: Empty/safe environment
5. `complex_attack_paths`: Multi-hop escalation scenarios
6. `empty_data`: No data available

#### Real EscaGCP Data Testing
```bash
# Generate test data using actual escagcp
cd /path/to/escagcp
python -m escagcp collect --projects test-project --output frontend/e2e/test-data/
python -m escagcp build-graph --input frontend/e2e/test-data/ --output frontend/e2e/test-data/
python -m escagcp analyze --graph frontend/e2e/test-data/graph.json --output frontend/e2e/test-data/
```

#### Data Validation Tests
- Verify frontend can parse all escagcp JSON formats
- Test with various project configurations
- Handle malformed or incomplete data gracefully

## Test Environment Setup

### Prerequisites
```bash
# Install test dependencies
npm install

# Install Playwright browsers
npm run playwright:install

# Verify test environment
npm run test -- --version
npm run test:e2e -- --version
```

### Configuration Files
- `jest.config.js` ✅ (Complete)
- `playwright.config.ts` ✅ (Complete)
- `src/test/setup.ts` ✅ (Complete)

### Mock Services
- API route interception for escagcp data
- localStorage mocking for settings
- Network request mocking for error scenarios

## Test Execution Strategy

### Development Workflow
```bash
# Run unit tests during development
npm run test:watch

# Run specific test file
npm run test -- LoadingSpinner.test.tsx

# Run E2E tests locally
npm run test:e2e:headed

# Run accessibility tests
npm run test:accessibility
```

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run unit tests
        run: npm run test:coverage
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Run accessibility tests
        run: npm run test:accessibility
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Data Management
1. **Static Test Data**: Committed JSON files for consistent testing
2. **Generated Test Data**: Created on-demand using test data manager
3. **Real EscaGCP Data**: Periodically updated from actual scans

## Performance Testing Strategy

### Load Testing Scenarios
1. **Baseline**: Empty graph, measure base performance
2. **Small Dataset**: 10-50 nodes, typical small environment
3. **Medium Dataset**: 100-500 nodes, medium enterprise
4. **Large Dataset**: 1000+ nodes, large enterprise
5. **Stress Test**: 5000+ nodes, performance limits

### Metrics Collection
```typescript
// Performance test example
test('should load large graph within performance budget', async ({ page }) => {
  const startTime = performance.now();
  
  await page.goto('/graph');
  await page.waitForSelector('[data-testid="graph-canvas"]');
  
  const loadTime = performance.now() - startTime;
  expect(loadTime).toBeLessThan(3000); // 3 second limit
});
```

### Memory Monitoring
- Track memory usage during graph rendering
- Monitor for memory leaks in long-running sessions
- Validate garbage collection efficiency

## Accessibility Testing Strategy

### Automated Testing
```typescript
// Accessibility test example
test('should have no accessibility violations', async ({ page }) => {
  await page.goto('/dashboard');
  await injectAxe(page);
  
  await checkA11y(page, null, {
    detailedReport: true,
    detailedReportOptions: { html: true }
  });
});
```

### Manual Testing Checklist
- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are clearly visible
- [ ] Screen reader announcements are appropriate
- [ ] Color contrast meets WCAG standards
- [ ] Content structure is logical and semantic

### Assistive Technology Testing
- Test with screen readers (NVDA, JAWS, VoiceOver)
- Verify keyboard-only navigation
- Test with high contrast mode
- Validate zoom functionality (up to 200%)

## Risk Management

### High-Risk Areas
1. **Graph Visualization**: Complex vis.js integration
2. **Large Datasets**: Performance with 1000+ nodes
3. **Cross-browser**: Compatibility across browsers
4. **Data Integration**: Handling various escagcp formats

### Mitigation Strategies
1. **Comprehensive Mocking**: Isolated testing of components
2. **Performance Budgets**: Hard limits on load times
3. **Browser Matrix**: Test on Chrome, Firefox, Safari, Edge
4. **Data Validation**: Strict schema validation for inputs

## Test Reporting

### Coverage Reports
- Line coverage minimum: 85%
- Branch coverage minimum: 80%
- Function coverage minimum: 90%

### Test Results Documentation
- Automated test reports in CI/CD
- Performance metrics tracking
- Accessibility audit results
- Cross-browser compatibility matrix

### Issue Tracking
- Link test failures to GitHub issues
- Track performance regressions
- Monitor accessibility compliance trends

## Phase 9 Preparation

### Auto-Fix Loop Readiness
1. **Comprehensive Test Suite**: All critical paths covered
2. **Clear Failure Messages**: Actionable error descriptions
3. **Fast Feedback**: Tests complete in < 5 minutes
4. **Reliable Tests**: Minimal flaky test issues

### Debugging Support
- Detailed error messages with context
- Screenshot capture on E2E failures
- Video recording of complex interactions
- Performance timeline analysis

## Timeline and Milestones

### Week 1: Foundation
- [x] Test environment setup
- [x] Unit test framework configuration
- [x] Basic component tests (LoadingSpinner)
- [x] Test data manager implementation

### Week 2: Core Testing
- [ ] Dashboard page E2E tests
- [ ] Graph page E2E tests
- [ ] Component integration tests
- [ ] Basic accessibility tests

### Week 3: Advanced Testing
- [ ] Performance testing implementation
- [ ] Cross-browser compatibility tests
- [ ] Data integration tests with real escagcp data
- [ ] Error handling and edge case tests

### Phase 8 Completion Criteria
- [ ] All test files created and functional
- [ ] Test documentation complete
- [ ] CI/CD integration configured
- [ ] Performance baselines established
- [ ] Accessibility compliance verified

## Conclusion

This comprehensive test plan ensures the EscaGCP frontend meets enterprise standards for reliability, performance, and accessibility. The combination of unit, integration, E2E, and accessibility tests provides confidence in the application's functionality across all user scenarios and data configurations.

The test suite is designed to catch regressions early, provide fast feedback to developers, and ensure seamless integration with the existing escagcp Python tool. With this foundation, Phase 9 can focus on execution and refinement of the testing strategy. 