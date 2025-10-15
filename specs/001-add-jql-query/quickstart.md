# Quickstart: JQL Query Enhancements

**Feature**: 001-add-jql-query  
**Date**: 2025-10-15  
**Purpose**: Key validation scenarios for manual testing and acceptance criteria verification

## Prerequisites

```powershell
# Activate virtual environment and start app
.\.venv\Scripts\activate; python app.py
```

Access application at: `http://localhost:8050`

---

## Validation Scenario 1: Real-time Character Count (Priority: P1)

**User Story**: As a user entering a long JQL query, I want to see the character count in real-time so I can avoid exceeding JIRA's limits.

**Test Steps**:

1. **Navigate to main JQL textarea**
   - Open application
   - Locate "JQL Query" input field

2. **Type short query**
   ```
   project = TEST
   ```
   - **Expected**: Character count shows "14 / 2000 characters"
   - **Expected**: No warning color (plain text)

3. **Type query approaching warning threshold**
   ```
   project = TEST AND status IN ("To Do", "In Progress", "Done") AND created >= -30d AND assignee in (currentUser(), "admin@example.com") AND labels IN ("urgent", "bug-fix", "feature") AND component = "Frontend" AND fixVersion = "1.0.0" AND reporter in membersOf("developers") AND priority IN (Highest, High) AND resolution = Unresolved AND type = Bug AND customfield_12345 > 0 AND customfield_67890 IS NOT EMPTY AND text ~ "search term" AND updated >= startOfWeek() AND duedate <= endOfMonth() AND Sprint in openSprints() AND "Story Points" >= 5 AND parent = PROJ-123 AND issueFunction in linkedIssuesOf("project = TEST") AND cf[10001] in cascadeOption("Option A") AND timespent > 3600 AND workratio > 50 AND votes > 10 AND watches > 5 AND comment ~ "code review" AND description ~ "critical bug" AND summary ~ "urgent fix" AND environment ~ "production" AND ("Epic Link" = PROJ-100 OR "Epic Link" = PROJ-200) AND (labels IS EMPTY OR labels IN ("technical-debt")) AND (attachments IS NOT EMPTY) AND (resolutiondate >= -7d OR resolutiondate IS EMPTY) AND (assignee changed DURING (-1w, now())) AND (status changed FROM "In Progress" TO "Done" DURING (-2w, now())) AND (priority was High AFTER -3w) AND (resolution changed AFTER startOfMonth()) AND (Sprint in futureSprints() OR Sprint IS EMPTY) AND (fixVersion in unreleasedVersions() OR fixVersion IS EMPTY) AND project NOT IN (ARCHIVE, DELETED) AND issuetype NOT IN (Epic, Sub-task) AND status NOT IN (Closed, Resolved, Won\'t Do) AND labels NOT IN (duplicate, invalid) AND (createdDate >= "2024-01-01" AND createdDate <= "2024-12-31")
   ```
   - **Expected**: Character count shows "~1850 / 2000 characters" (exact count may vary)
   - **Expected**: Warning color appears (amber/orange text)
   - **Expected**: Warning icon (exclamation triangle) appears
   - **Expected**: Aria-live announcement: "Warning: 1850 of 2000 characters used"

4. **Verify debouncing (rapid typing)**
   - Type additional characters quickly: `AND test = value`
   - **Expected**: Character count does NOT update on every keystroke
   - **Expected**: Count updates approximately 300ms after typing stops

5. **Clear textarea**
   - Delete all text
   - **Expected**: Character count returns to "0 / 2000 characters"
   - **Expected**: Warning color removed

**Acceptance Criteria Verified**:
- ✅ FR-001: Character count displays "X / 2000 characters" format
- ✅ FR-002: Real-time updates with 300ms debouncing
- ✅ FR-003: Warning color when count exceeds 1800

---

## Validation Scenario 2: Syntax Highlighting (Priority: P2)

**User Story**: As a user editing a JQL query, I want to see syntax highlighting so I can visually distinguish keywords and values.

**Test Steps**:

1. **Type query with keywords**
   ```
   project = TEST AND status = "Done"
   ```
   - **Expected**: "AND" highlighted in blue (keyword color)
   - **Expected**: `"Done"` highlighted in green (string color)
   - **Expected**: "project", "status" in default text color (field names)

2. **Type query with multiple keyword types**
   ```
   status IN ("To Do", "In Progress") OR assignee IS EMPTY
   ```
   - **Expected**: "IN", "OR", "IS" highlighted as keywords (blue)
   - **Expected**: `"To Do"`, `"In Progress"` highlighted as strings (green)
   - **Expected**: "EMPTY" highlighted as keyword (blue)

3. **Open save dialog**
   - Click "Save Query" button
   - Modal opens with JQL textarea pre-filled
   - **Expected**: Same syntax highlighting applied in dialog textarea
   - **Expected**: Character count also visible in dialog

4. **Edit query in save dialog**
   - Add: `AND priority = High`
   - **Expected**: "AND" highlighted as keyword
   - **Expected**: "High" in default text color
   - **Expected**: Character count updates in dialog

5. **Verify consistency**
   - Compare main textarea highlighting with dialog textarea highlighting
   - **Expected**: Identical color scheme and styling
   - **Expected**: Both textareas have same syntax highlighting behavior

**Acceptance Criteria Verified**:
- ✅ FR-004: Keywords (AND, OR, IN, IS, etc.) highlighted
- ✅ FR-005: String values (quoted text) highlighted
- ✅ FR-007: Consistent feature parity between main and dialog textareas

---

## Validation Scenario 3: Mobile Responsiveness (Priority: P3)

**User Story**: As a mobile user, I want character count and syntax highlighting to work on small screens without breaking layout.

**Test Steps**:

1. **Open browser DevTools**
   - Press F12
   - Click "Toggle device toolbar" (Ctrl+Shift+M)

2. **Test 320px viewport (iPhone SE)**
   - Set viewport to 320px × 568px
   - **Expected**: Character count displays below textarea (no horizontal scroll)
   - **Expected**: Character count text wraps if needed
   - **Expected**: Textarea remains usable with touch

3. **Type query on 320px viewport**
   ```
   project = TEST AND status = "Done"
   ```
   - **Expected**: Syntax highlighting visible
   - **Expected**: Keywords/strings colored appropriately
   - **Expected**: Text wraps at viewport edge (no horizontal scroll)

4. **Test 768px viewport (iPad)**
   - Set viewport to 768px × 1024px
   - **Expected**: Character count displays properly
   - **Expected**: More horizontal space utilized
   - **Expected**: Font size may be slightly larger

5. **Test 1024px viewport (Desktop)**
   - Set viewport to 1024px × 768px
   - **Expected**: Full desktop layout
   - **Expected**: All features functional
   - **Expected**: Optimal readability

6. **Rotate device (portrait ↔ landscape)**
   - Switch between portrait and landscape orientations
   - **Expected**: Layout reflows appropriately
   - **Expected**: No horizontal scrolling introduced
   - **Expected**: Character count remains visible

**Acceptance Criteria Verified**:
- ✅ FR-008: Mobile-responsive layout for 320px+ viewports
- ✅ SC-002: Character count readable without horizontal scrolling
- ✅ User Story 3: Proper display on mobile screens

---

## Validation Scenario 4: Performance (60fps Target)

**User Story**: As a user typing large queries, I want the interface to remain responsive without lag.

**Test Steps**:

1. **Open browser DevTools Performance tab**
   - Press F12 → Performance tab
   - Click "Record" button

2. **Type long query (2000+ characters)**
   - Paste the long query from Scenario 1
   - Continue typing additional characters
   - Stop recording after 5 seconds

3. **Analyze Performance Profile**
   - Check "Frames" section for dropped frames
   - **Expected**: Consistent 60fps (16.7ms per frame)
   - **Expected**: No yellow/red flame chart bars (long tasks)
   - **Expected**: Callback execution time < 10ms

4. **Type rapidly (stress test)**
   - Type as fast as possible for 10 seconds
   - **Expected**: Character count updates smoothly (no freezing)
   - **Expected**: Syntax highlighting applies without lag
   - **Expected**: No error messages in console

5. **Paste extremely long text (5000 characters)**
   - Copy 5000-character query
   - Paste into textarea
   - **Expected**: Character count shows "5000 / 2000 characters"
   - **Expected**: Warning color appears
   - **Expected**: No browser hang or freeze

**Acceptance Criteria Verified**:
- ✅ FR-010: 60fps maintained during typing up to 5000 characters
- ✅ SC-004: No performance degradation with syntax highlighting active

---

## Validation Scenario 5: Accessibility (Screen Reader)

**User Story**: As a screen reader user, I want to be notified when character count approaches the limit.

**Test Steps**:

1. **Enable screen reader**
   - Windows: Open Narrator (Win + Ctrl + Enter)
   - Enable browse mode

2. **Navigate to JQL textarea**
   - Tab to "JQL Query" field
   - **Expected**: Narrator announces "JQL Query, edit"

3. **Type query approaching warning threshold**
   - Type ~1850 characters (use Scenario 1 long query)
   - **Expected**: After 300ms, Narrator announces "Warning: 1850 of 2000 characters used"

4. **Continue typing below threshold**
   - Delete characters to bring count to 1700
   - **Expected**: Narrator announces "1700 of 2000 characters"
   - **Expected**: No "warning" in announcement

5. **Test keyboard navigation**
   - Tab through all interactive elements
   - **Expected**: Character count display receives focus (if interactive)
   - **Expected**: Logical tab order maintained

6. **Test high contrast mode**
   - Enable Windows High Contrast (Alt + Shift + Print Screen)
   - **Expected**: Warning color still distinguishable
   - **Expected**: Warning icon visible
   - **Expected**: Text remains readable

**Acceptance Criteria Verified**:
- ✅ Accessibility: aria-live regions announce updates
- ✅ Accessibility: Warning indicated with color AND text
- ✅ Accessibility: Keyboard navigation functional

---

## Validation Scenario 6: Feature Parity (Main vs Dialog)

**User Story**: As a user, I expect consistent behavior when editing queries in main textarea vs save dialog.

**Test Steps**:

1. **Type query in main textarea**
   ```
   project = TEST AND status = "Done"
   ```
   - Note character count: "31 / 2000 characters"
   - Note syntax highlighting: "AND" blue, `"Done"` green

2. **Open save dialog**
   - Click "Save Query" button
   - **Expected**: Query pre-populated in dialog textarea
   - **Expected**: Character count shows "31 / 2000 characters"
   - **Expected**: Same syntax highlighting applied

3. **Edit query in dialog**
   - Add: ` OR assignee = currentUser()`
   - **Expected**: Character count updates in dialog
   - **Expected**: "OR" highlighted as keyword
   - **Expected**: Debouncing works in dialog (300ms)

4. **Copy from main, paste into dialog**
   - Type long query (1850 chars) in main textarea
   - Copy text (Ctrl+C)
   - Open dialog, paste text (Ctrl+V)
   - **Expected**: Character count updates immediately to 1850
   - **Expected**: Warning color appears in dialog
   - **Expected**: Syntax highlighting applies to pasted text

5. **Verify no feature loss**
   - Compare all features available in main textarea vs dialog
   - **Expected**: Character count: ✅ Both locations
   - **Expected**: Warning indicator: ✅ Both locations
   - **Expected**: Syntax highlighting: ✅ Both locations
   - **Expected**: Debouncing: ✅ Both locations

**Acceptance Criteria Verified**:
- ✅ FR-007: Consistent feature parity between main and dialog
- ✅ SC-007: Users experience consistent behavior when switching contexts

---

## Edge Case Validation

### Edge Case 1: Unicode Characters
```
project = TEST AND summary ~ "emoji 🚀🔥✨"
```
- **Expected**: Character count includes emoji (each emoji = 1 character)
- **Expected**: Syntax highlighting works with unicode

### Edge Case 2: Malformed Syntax
```
project = TEST AND status = "unclosed quote
```
- **Expected**: Character count still updates
- **Expected**: Best-effort syntax highlighting (no error messages)
- **Expected**: No application crash

### Edge Case 3: Empty Textarea
- Clear all text
- **Expected**: Character count shows "0 / 2000 characters"
- **Expected**: No warning color
- **Expected**: No errors

### Edge Case 4: Rapid Copy/Paste
- Copy 3000-character text
- Paste multiple times rapidly
- **Expected**: Character count updates to latest value
- **Expected**: No race conditions or stale state

---

## Success Criteria Summary

| Criterion                          | Scenario   | Status |
| ---------------------------------- | ---------- | ------ |
| FR-001: Character count display    | Scenario 1 | ✅      |
| FR-002: Real-time updates (300ms)  | Scenario 1 | ✅      |
| FR-003: Warning color (>1800)      | Scenario 1 | ✅      |
| FR-004-006: Syntax highlighting    | Scenario 2 | ✅      |
| FR-007: Feature parity             | Scenario 6 | ✅      |
| FR-008: Mobile responsive          | Scenario 3 | ✅      |
| FR-010: 60fps performance          | Scenario 4 | ✅      |
| Accessibility                      | Scenario 5 | ✅      |
| SC-001: 300ms update time          | Scenario 1 | ✅      |
| SC-002: Mobile readability         | Scenario 3 | ✅      |
| SC-004: No performance degradation | Scenario 4 | ✅      |

---

## Known Limitations

1. **JQL Validation**: Syntax highlighting does NOT validate JQL correctness (out of scope)
2. **Custom Keywords**: Only standard JQL keywords highlighted (extensible in future)
3. **Character Limit**: 2000-character limit is typical but may vary by JIRA instance
4. **Browser Support**: Tested on Chrome/Edge/Firefox (modern browsers only)

---

## Troubleshooting

**Issue**: Character count not updating
- **Fix**: Check browser console for JavaScript errors
- **Fix**: Verify `dcc.Interval` component is not disabled

**Issue**: Syntax highlighting not visible
- **Fix**: Check `assets/custom.css` loaded correctly
- **Fix**: Verify `.jql-keyword` and `.jql-string` CSS classes defined

**Issue**: Performance lag on mobile
- **Fix**: Test on actual device (DevTools may not accurately simulate)
- **Fix**: Verify debouncing is active (300ms interval)

**Issue**: Screen reader not announcing updates
- **Fix**: Verify `aria-live="polite"` attribute present
- **Fix**: Check screen reader settings (may need to enable announcements)
