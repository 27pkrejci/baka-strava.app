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

async function loadGroups() {
    const container = document.getElementById('groups-container');
    if (!container) return;

    try {
        const res = await fetch('/api/groups');
        const data = await res.json();
        container.innerHTML = '';

        if (data.status === 'error') {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger';
            errorDiv.textContent = data.message;
            container.appendChild(errorDiv);
            return;
        }

        const groups = data.groups || [];
        if (!groups.length) {
            const noGroupsDiv = document.createElement('div');
            noGroupsDiv.className = 'text-muted';
            noGroupsDiv.textContent = 'Žádné skupiny k dispozici.';
            container.appendChild(noGroupsDiv);
            return;
        }

        // Load saved groups from localStorage
        const saved = JSON.parse(localStorage.getItem('selectedGroups') || '[]');
        const savedSet = new Set(saved);

        for (const group of groups) {
            container.appendChild(createGroupCheckbox(group, savedSet.has(group)));
        }

    } catch (err) {
        const container = document.getElementById('groups-container');
        if (container) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger';
            errorDiv.textContent = `Chyba načítání: ${err.message}`;
            container.innerHTML = '';
            container.appendChild(errorDiv);
        }
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadGroups();

    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const checks = Array.from(document.querySelectorAll('#groups-container input[type=checkbox]'));
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
            localStorage.removeItem('selectedGroups');
            loadGroups();
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

