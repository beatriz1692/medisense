const COLORS = ["#FF8A8A", "#8FD6A1", "#F4D06F", "#A3BFFA", "#F7A6E0", "#9EDCE6"];
let donutChart;

function renderDonut(labels, values){
  const ctx = document.getElementById('donutChart').getContext('2d');
  if (donutChart) donutChart.destroy();
  donutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: COLORS.slice(0, values.length), borderWidth: 0, hoverOffset: 4 }]
    },
    options: { cutout: '60%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 14 } } } }
  });
}

function renderBars(top3){
  const bars = document.getElementById('bars');
  bars.innerHTML = '';
  const title = document.createElement('div');
  title.className = 'muted'; title.style.marginBottom = '6px';
  title.textContent = 'Top 3 diagnósticos prováveis';
  bars.appendChild(title);

  top3.forEach((item, i) => {
    const row = document.createElement('div'); row.className = 'bar-row';
    const lbl = document.createElement('div'); lbl.className = 'label'; lbl.textContent = item.label;
    const bar = document.createElement('div'); bar.className = 'bar';
    const fill = document.createElement('span'); fill.style.background = COLORS[i]; fill.style.width = `${(item.prob*100).toFixed(0)}%`;
    bar.appendChild(fill);
    const pct = document.createElement('div'); pct.className = 'pct'; pct.textContent = `${(item.prob*100).toFixed(0)}%`;
    row.appendChild(lbl); row.appendChild(bar); row.appendChild(pct);
    bars.appendChild(row);
  });
}

function getFormData(){
  return {
    nome: document.getElementById('nome').value.trim(),
    sexo: document.getElementById('sexo').value,
    idade: document.getElementById('idade').value || 0,
    temperatura: document.getElementById('temperatura').value || 0,
    frequencia_cardiaca: document.getElementById('frequencia_cardiaca').value || 0,
    pressao_sistolica: document.getElementById('pressao_sistolica').value || 0,
    pressao_diastolica: document.getElementById('pressao_diastolica').value || 0,
    saturacao: document.getElementById('saturacao').value || 0,
    tosse: document.getElementById('tosse').checked ? 1 : 0,
    fadiga: document.getElementById('fadiga').checked ? 1 : 0,
    sede_excessiva: document.getElementById('sede_excessiva').checked ? 1 : 0,
    vomitos: document.getElementById('vomitos').checked ? 1 : 0,
    falta_ar: document.getElementById('falta_ar').checked ? 1 : 0,
    sintomas_texto: document.getElementById('sintomas_texto').value || "",
  };
}

document.getElementById('btnDiag').addEventListener('click', async () => {
  try{
    const payload = getFormData();
    const res = await fetch('/api/predict', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    const data = await res.json();
    if(!data.ok) throw new Error(data.error || 'Erro desconhecido');
    renderDonut(data.top3.map(t => t.label), data.top3.map(t => t.prob));
    renderBars(data.top3);
  }catch(err){
    alert('Erro: ' + err.message);
  }
});

renderDonut(['—'], [1]);
