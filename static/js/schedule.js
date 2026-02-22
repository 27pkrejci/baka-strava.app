// Extracted from templates/rozvrh-hodin.html
// Constants
const TIME_SLOTS = [
    "8:00- 8:45", "8:55- 9:40", "10:00-10:45", "10:55-11:40",
    "11:50-12:35", "12:45-13:30", "13:35-14:20", "14:25-15:10",
    "15:15-16:00"
];

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

const DAYS_FORMATTED = {
    'Monday': 'Po',
    'Tuesday': 'Út',
    'Wednesday': 'St',
    'Thursday': 'Čt',
    'Friday': 'Pá'
};

// Helper to build query string for API calls
function buildQueryString() {
    const params = new URLSearchParams();
    const selectedClass = localStorage.getItem('selectedClass');
    const selectedGroups = JSON.parse(localStorage.getItem('selectedGroups') || '[]');
    
    if (selectedClass) {
        params.append('class', selectedClass);
    }
    selectedGroups.forEach(group => {
        params.append('groups', group);
    });
    
    return params.toString();
}

// Template helper functions
function createLessonCell(lesson) {
    const template = document.getElementById('lesson-cell-template');
    const clone = template.content.cloneNode(true);
    
    clone.querySelector('.group-text').textContent = lesson.group || '-';
    clone.querySelector('.room-text').textContent = lesson.room || '-';
    clone.querySelector('.subject-text').textContent = lesson.subject || '-';
    clone.querySelector('.teacher-text').textContent = lesson.teacher || '-';
    
    return clone;
}

function createMultipleLessonsCell(lessons) {
    const template = document.getElementById('multiple-lessons-cell-template');
    const clone = template.content.cloneNode(true);
    
    const cellElement = clone.querySelector('td');
    const itemTemplate = document.getElementById('lesson-item-template');
    
    for (const lesson of lessons) {
        const itemClone = itemTemplate.content.cloneNode(true);
        itemClone.querySelector('.group-text').textContent = lesson.group || '-';
        itemClone.querySelector('.room-text').textContent = lesson.room || '-';
        itemClone.querySelector('.subject-text').textContent = lesson.subject || '-';
        itemClone.querySelector('.teacher-text').textContent = lesson.teacher || '-';
        cellElement.appendChild(itemClone);
    }
    
    return clone;
}

// Data access functions
function getSelectedGroups() {
    try {
        return JSON.parse(localStorage.getItem('selectedGroups') || '[]');
    } catch (e) {
        return [];
    }
}

function getSelectedWeek() {
    return new URLSearchParams(window.location.search).get('week') || 'all';
}

function setSelectedWeek(week) {
    const url = new URL(window.location);
    if (week === 'all') {
        url.searchParams.delete('week');
    } else {
        url.searchParams.set('week', week);
    }
    window.history.replaceState({}, '', url);
}

// Filtering functions
function shouldShowLesson(lesson, selectedWeek) {
    if (!lesson.week || lesson.week === '') {
        return true;
    }
    if (selectedWeek === 'all') {
        return true;
    }
    return lesson.week === selectedWeek;
}

function filterLessonsForDisplay(lessons, selectedGroups, selectedWeek) {
    let filtered = [...lessons];

    if (selectedGroups.size > 0) {
        filtered = filtered.filter(l => !l.group || l.group === '' || selectedGroups.has(l.group));
    }

    filtered = filtered.filter(l => shouldShowLesson(l, selectedWeek));
    
    return filtered;
}

// Rendering function
function renderScheduleTable(schedule) {
    const tbody = document.getElementById('schedule-tbody');
    if (!tbody) return;

    const fragment = document.createDocumentFragment();
    const selected = new Set(getSelectedGroups());
    const selectedWeek = getSelectedWeek();

    for (const englishDay of DAYS) {
        const dayData = schedule[englishDay];
        if (!dayData) continue;

        const row = document.createElement('tr');
        
        // Day header cell
        const dayCell = document.createElement('th');
        dayCell.scope = 'row';
        dayCell.innerHTML = `<div class="col">${DAYS_FORMATTED[englishDay]}</div>`;
        row.appendChild(dayCell);

        // Lesson cells for each time slot
        for (const timeSlot of TIME_SLOTS) {
            const lessons = dayData.lessons[timeSlot] || [];
            const filtered = filterLessonsForDisplay(lessons, selected, selectedWeek);

            if (filtered.length === 0) {
                const emptyCell = document.createElement('td');
                row.appendChild(emptyCell);
            } else if (filtered.length === 1) {
                row.appendChild(createLessonCell(filtered[0]));
            } else {
                row.appendChild(createMultipleLessonsCell(filtered));
            }
        }

        fragment.appendChild(row);
    }

    tbody.innerHTML = '';
    tbody.appendChild(fragment);
}

// Main data loading function
async function loadWeekSchedule() {
    try {
        const query = buildQueryString();
        const url = query ? `/api/week-schedule?${query}` : '/api/week-schedule';
        const response = await fetch(url);
        const schedule = await response.json();

        if (schedule.status === 'error') {
            const el = document.getElementById('schedule-tbody');
            if (el) {
                const errorRow = document.createElement('tr');
                const errorCell = document.createElement('td');
                errorCell.colSpan = '10';
                errorCell.className = 'text-danger text-center';
                errorCell.textContent = schedule.message;
                errorRow.appendChild(errorCell);
                el.innerHTML = '';
                el.appendChild(errorRow);
            }
            return;
        }

        renderScheduleTable(schedule);
    } catch (error) {
        console.error('Error loading week schedule:', error);
        const el = document.getElementById('schedule-tbody');
        if (el) {
            const errorRow = document.createElement('tr');
            const errorCell = document.createElement('td');
            errorCell.colSpan = '10';
            errorCell.className = 'text-danger text-center';
            errorCell.textContent = `Error loading schedule: ${error.message}`;
            errorRow.appendChild(errorCell);
            el.innerHTML = '';
            el.appendChild(errorRow);
        }
    }
}

// Event handlers
document.addEventListener('DOMContentLoaded', () => {
    // Load schedule on page load
    loadWeekSchedule();

    // Set initial week button state from URL
    const savedWeek = getSelectedWeek();
    const weekButton = document.getElementById(`week-${savedWeek}`);
    if (weekButton) {
        weekButton.checked = true;
    }

    // Add event listeners to week toggle buttons
    document.querySelectorAll('input[name="week-option"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            setSelectedWeek(e.target.value);
            loadWeekSchedule();
        });
    });
});

