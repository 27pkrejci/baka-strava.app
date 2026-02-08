// Extracted from templates/rozvrh-obedu.html
// Template helper function
function createLunchDayCard(day) {
    const template = document.getElementById('lunch-day-template');
    const clone = template.content.cloneNode(true);
    
    const title = `${day.day_name} ${day.formatted_date} ${new Date(day.date).getFullYear()}`;
    
    clone.querySelector('.day-title').textContent = title;
    clone.querySelector('.soup-item').textContent = day.soup || 'Není v databázi';
    clone.querySelector('.first-item').textContent = day.first || 'Není v databázi';
    clone.querySelector('.second-item').textContent = day.second || 'Není v databázi';
    clone.querySelector('.doplnek-item').textContent = day.doplněk || 'Není v databázi';
    
    return clone;
}

async function loadLunchSchedule() {
    const container = document.getElementById('lunch-schedule-container');
    if (!container) return;

    try {
        const response = await fetch('/api/lunch-schedule');
        const schedule = await response.json();

        if (schedule.status === 'error') {
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger text-center';
            errorAlert.textContent = schedule.message;
            container.innerHTML = '';
            container.appendChild(errorAlert);
            return;
        }

        const fragment = document.createDocumentFragment();
        for (const day of schedule) {
            fragment.appendChild(createLunchDayCard(day));
        }

        container.innerHTML = '';
        container.appendChild(fragment);
    } catch (error) {
        console.error('Error loading lunch schedule:', error);
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger text-center';
        errorAlert.textContent = `Chyba při načítání rozvrhu obědů: ${error.message}`;
        container.innerHTML = '';
        container.appendChild(errorAlert);
    }
}

// Load lunch schedule on page load
document.addEventListener('DOMContentLoaded', loadLunchSchedule);

