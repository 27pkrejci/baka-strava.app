// Extracted from templates/profile.html
// Template helper function
function createGroupCheckbox(group, isChecked) {
    const template = document.getElementById('group-checkbox-template');
    const clone = template.content.cloneNode(true);
    
    const id = `grp-${group.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
    const input = clone.querySelector('input');
    const label = clone.querySelector('label');
    
    input.id = id;
    input.value = group;
    input.checked = isChecked;
    
    label.htmlFor = id;
    label.textContent = group;
    
    return clone;
}

async function loadClasses() {
    const select = document.getElementById('class-select');
    if (!select) return;

    try {
        const res = await fetch('/api/classes');
        const data = await res.json();

        if (data.status === 'error') {
            select.innerHTML = '<option value="">Chyba načítání tříd</option>';
            return;
        }

        const classes = data.classes || [];
        select.innerHTML = '<option value="">Vyberte třídu</option>';
        for (const cls of classes) {
            const option = document.createElement('option');
            option.value = cls;
            option.textContent = cls;
            select.appendChild(option);
        }

        // Load saved class
        const savedClass = localStorage.getItem('selectedClass');
        if (savedClass && classes.includes(savedClass)) {
            select.value = savedClass;
            loadGroups(savedClass);
        }

    } catch (err) {
        select.innerHTML = '<option value="">Chyba načítání tříd</option>';
    }
}

async function loadGroups(className) {
    const container = document.getElementById('groups-container');
    const list = document.getElementById('groups-list');
    const buttons = document.getElementById('buttons');
    if (!container || !list || !buttons) return;

    if (!className) {
        list.textContent = 'Vyberte třídu nejprve.';
        container.style.display = 'none';
        buttons.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    buttons.style.display = 'block';
    list.textContent = 'Načítání skupin...';

    try {
        const res = await fetch(`/api/groups/${encodeURIComponent(className)}`);
        const data = await res.json();
        list.innerHTML = '';

        if (data.status === 'error') {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger';
            errorDiv.textContent = data.message;
            list.appendChild(errorDiv);
            return;
        }

        const groups = data.groups || [];
        if (!groups.length) {
            const noGroupsDiv = document.createElement('div');
            noGroupsDiv.className = 'text-muted';
            noGroupsDiv.textContent = 'Žádné skupiny k dispozici pro tuto třídu.';
            list.appendChild(noGroupsDiv);
            return;
        }

        // Load saved groups from localStorage
        const saved = JSON.parse(localStorage.getItem('selectedGroups') || '[]');
        const savedSet = new Set(saved);

        for (const group of groups) {
            list.appendChild(createGroupCheckbox(group, savedSet.has(group)));
        }

    } catch (err) {
        list.innerHTML = '';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-danger';
        errorDiv.textContent = `Chyba načítání: ${err.message}`;
        list.appendChild(errorDiv);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadClasses();

    const classSelect = document.getElementById('class-select');
    if (classSelect) {
        classSelect.addEventListener('change', (e) => {
            const selectedClass = e.target.value;
            localStorage.setItem('selectedClass', selectedClass);
            loadGroups(selectedClass);
        });
    }

    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const selectedClass = localStorage.getItem('selectedClass');
            const checks = Array.from(document.querySelectorAll('#groups-list input[type=checkbox]'));
            const picked = checks.filter(c => c.checked).map(c => c.value);
            localStorage.setItem('selectedGroups', JSON.stringify(picked));
            const status = document.getElementById('status');
            if (status) {
                status.innerHTML = '';
                const successDiv = document.createElement('div');
                successDiv.className = 'text-success';
                successDiv.textContent = 'Uloženo lokálně.';
                status.appendChild(successDiv);
            }
        });
    }

    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            localStorage.removeItem('selectedClass');
            localStorage.removeItem('selectedGroups');
            document.getElementById('class-select').value = '';
            loadGroups('');
            const status = document.getElementById('status');
            if (status) {
                status.innerHTML = '';
                const mutedDiv = document.createElement('div');
                mutedDiv.className = 'text-muted';
                mutedDiv.textContent = 'Výběr vymazán.';
                status.appendChild(mutedDiv);
            }
        });
    }
});

