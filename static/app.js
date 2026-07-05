// Function to handle clean separate layout navigation tabs toggle rules
function switchTab(tabId) {
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => { 
        content.classList.remove('block'); 
        content.classList.add('hidden'); 
    });

    const activeSection = document.getElementById(tabId);
    if (activeSection) { 
        activeSection.classList.remove('hidden'); 
        activeSection.classList.add('block'); 
    }

    const buttons = document.querySelectorAll('nav button');
    buttons.forEach(btn => {
        btn.classList.remove('bg-gradient-to-r', 'from-cyan-600', 'to-blue-600', 'text-white', 'shadow-lg');
        btn.classList.add('text-slate-400', 'hover:text-slate-200');
    });

    const currentBtn = document.getElementById(`btn-${tabId}`);
    if (currentBtn) {
        currentBtn.classList.remove('text-slate-400', 'hover:text-slate-200');
        currentBtn.classList.add('bg-gradient-to-r', 'from-cyan-600', 'to-blue-600', 'text-white', 'shadow-lg');
    }
}

// Real-Time Live API Integration Dynamic Mapping Wrapper logic
async function handleValidation(event) {
    event.preventDefault();
    const ideaText = document.getElementById('startup-input').value.trim();

    if (!ideaText) {
        alert("Please enter your startup idea statement first!");
        return;
    }

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea: ideaText })
        });

        if (!response.ok) {
            throw new Error(`Server returned error payload token: ${response.status}`);
        }

        const report = await response.json();

        // 1. Live Mapping Numeric Score Analytics Blocks
        document.getElementById('score-market').innerText = `${report.market_score || '0'} %`;
        document.getElementById('score-moat').innerText = `${report.moat_score || '0'} %`;
        document.getElementById('score-vc').innerText = `${report.vc_score || '0'} %`;
        document.getElementById('score-overall').innerText = `${report.overall_score || '0'} %`;

        // 2. Loop Map Strategic SWOT Strings Blocks
        document.getElementById('swot-strengths').innerHTML = (report.strengths || []).map(str => `<li>${str}</li>`).join('') || "<li>No properties detected.</li>";
        document.getElementById('swot-weaknesses').innerHTML = (report.weaknesses || []).map(str => `<li>${str}</li>`).join('') || "<li>No parameters detected.</li>";
        document.getElementById('swot-opportunities').innerHTML = (report.opportunities || []).map(str => `<li>${str}</li>`).join('') || "<li>No routes detected.</li>";
        document.getElementById('swot-threats').innerHTML = (report.threats || []).map(str => `<li>${str}</li>`).join('') || "<li>No bottlenecks detected.</li>";

        // 3. Populate Business Plan Canvas Sheets Text Frameworks
        document.getElementById('canvas-values').innerText = report.value_proposition || "No data.";
        document.getElementById('canvas-segments').innerText = report.target_demographics || "No data.";
        document.getElementById('canvas-channels').innerText = report.channels || "No data.";
        document.getElementById('canvas-revenue').innerText = report.revenue_streams || "No data.";
        document.getElementById('canvas-costs').innerText = report.operational_costs || "No data.";

        // Instantly flip visual view route screen navigation directly to metrics block tab 2
        switchTab('metrics-tab');

    } catch (err) {
        alert(`API Integration Pipeline Error: ${err.message}. Please verify local workspace setups.`);
    }
}

// Fixed Lifecycle Hook Integration Rule
document.addEventListener('DOMContentLoaded', () => {
    const formElement = document.getElementById('analyze-form');
    if (formElement) {
        formElement.addEventListener('submit', handleValidation);
    }
});