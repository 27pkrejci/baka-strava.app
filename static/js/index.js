// Extracted from templates/index.html
// Map time slots to lesson order numbers
const TIME_SLOT_ORDER = {
    "8:00- 8:45": 1, "8:55- 9:40": 2, "10:00-10:45": 3, "10:55-11:40": 4,
    "11:50-12:35": 5, "12:45-13:30": 6, "13:35-14:20": 7, "14:25-15:10": 8,
    "15:15-16:00": 9
};

// Helper to pick lesson matching selected groups or any with no group
function pickLesson(lessons) {
    if (!lessons || !lessons.length) return null;
    let selected = [];
    try { selected = JSON.parse(localStorage.getItem('selectedGroups') || '[]'); } catch (e) { selected = []; }
    
    // If no groups selected, return first lesson
    if (!selected.length) return lessons[0];
    
    // Prefer lessons matching selected groups
    for (const l of lessons) {
        if (selected.includes(l.group)) return l;
    }
    
    // Fall back to any lesson with no/empty group
    for (const l of lessons) {
        if (!l.group || l.group === '') return l;
    }
    return null;
}

// Template helper function
function createPeriodCard(period) {
    const template = document.getElementById('period-card-template');
    const clone = template.content.cloneNode(true);
    
    const order = TIME_SLOT_ORDER[period.time_slot] || '?';
    
    clone.querySelector('.period-order').textContent = `${order}.`;
    clone.querySelector('.period-time').textContent = period.time_slot;
    clone.querySelector('.period-room').textContent = period.room || '';
    clone.querySelector('.period-subject').textContent = period.subject || '';
    clone.querySelector('.period-teacher').textContent = `(${period.teacher || ''})`;
    
    return clone;
}

async function updateTimetable() {
    // Update last update time
    const now = new Date();
    const timeString = now.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const lastUpdateEl = document.getElementById('last-update');
    if (lastUpdateEl) {
        lastUpdateEl.textContent = `Poslední aktualizace: ${timeString}`;
    }

    try {
        const response = await fetch('/api/current-period');
        const data = await response.json();

        if (data.status === 'success') {
            // Update previous period
            const prevEl = document.getElementById('previous-period');
            if (prevEl) {
                prevEl.innerHTML = '';
                if (data.previous) {
                    const prevLesson = pickLesson(data.previous.lessons) || {};
                    const periodData = {
                        time_slot: data.previous.time_slot,
                        room: prevLesson.room || '',
                        subject: prevLesson.subject || '',
                        teacher: prevLesson.teacher || ''
                    };
                    prevEl.appendChild(createPeriodCard(periodData));
                } else {
                    const p = document.createElement('p');
                    p.textContent = 'Žádná předchozí hodina';
                    prevEl.appendChild(p);
                }
            }

            // Update current period
            const curEl = document.getElementById('current-period');
            if (curEl) {
                curEl.innerHTML = '';
                if (data.current) {
                    const currLesson = pickLesson(data.current.lessons) || {};
                    const periodData = {
                        time_slot: data.current.time_slot,
                        room: currLesson.room || '',
                        subject: currLesson.subject || '',
                        teacher: currLesson.teacher || ''
                    };
                    curEl.appendChild(createPeriodCard(periodData));
                } else {
                    const p = document.createElement('p');
                    p.textContent = 'Žádná aktuální hodina';
                    curEl.appendChild(p);
                }
            }

            // Update next period
            const nextEl = document.getElementById('next-period');
            if (nextEl) {
                nextEl.innerHTML = '';
                if (data.next) {
                    const nextLesson = pickLesson(data.next.lessons) || {};
                    const periodData = {
                        time_slot: data.next.time_slot,
                        room: nextLesson.room || '',
                        subject: nextLesson.subject || '',
                        teacher: nextLesson.teacher || ''
                    };
                    nextEl.appendChild(createPeriodCard(periodData));
                } else {
                    const p = document.createElement('p');
                    p.textContent = 'Žádná následující hodina';
                    nextEl.appendChild(p);
                }
            }
        } else {
            // Handle errors or weekend
            const message = data.message || 'Chyba při načítání rozvrhu';
            const elements = ['previous-period', 'current-period', 'next-period'];
            elements.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.innerHTML = '';
                    const p = document.createElement('p');
                    p.textContent = message;
                    el.appendChild(p);
                }
            });
        }
    } catch (error) {
        console.error('Error fetching timetable:', error);
    }
}

// Fetch today's lunch and update the lunch card
async function updateLunch() {
    try {
        const res = await fetch('/api/today-lunch');
        const data = await res.json();

        // If API returned error-style object
        if (data && data.status === 'error') {
            const msg = data.message || 'Nelze načíst oběd';
            const ids = ['lunch-first', 'lunch-second', 'lunch-soup', 'lunch-dopln'];
            ids.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = msg;
            });
            return;
        }

        const firstEl = document.getElementById('lunch-first');
        const secondEl = document.getElementById('lunch-second');
        const doplEl = document.getElementById('lunch-dopln');
        const soupEl = document.getElementById('lunch-soup');
        
        if (firstEl) firstEl.textContent = data.first || '';
        if (secondEl) secondEl.textContent = data.second || '';
        if (doplEl) doplEl.textContent = data['doplněk'] || data.dopln || '';
        if (soupEl) soupEl.textContent = data.soup || '';
    } catch (err) {
        console.error('Error fetching lunch:', err);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initial load
    updateTimetable();
    updateLunch();

    // Update every 30 seconds
    setInterval(updateTimetable, 30000);

    // Update lunch every 60 seconds
    setInterval(updateLunch, 60000);
});

