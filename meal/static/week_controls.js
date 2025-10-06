(function () {
  const body = document.body;
  if (!body.dataset.week || !body.dataset.year) return;

  const curWeek = parseInt(body.dataset.week, 10);
  const curYear = parseInt(body.dataset.year, 10);

  const resetBtn = document.getElementById("resetWeek");
  const randomBtn = document.getElementById("randomizeWeek");
  const exportBtn = document.getElementById("exportPDF");
  const todayBtn = document.getElementById("todayWeek");
  const modal = document.getElementById("advRandModal");
  const closeBtn = document.getElementById("advRandClose");
  const cancelBtn = document.getElementById("advRandCancel");
  const form = document.getElementById("advRandForm");
  const replaceChk = document.getElementById("arReplaceExisting");

  // Reset week
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (confirm("Are you sure you want to reset this week?")) {
        window.location.href = `/reset_week?week=${curWeek}&year=${curYear}`;
      }
    });
  }

  // Export PDF
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      if (confirm("Do you want to export this week to PDF?")) {
        window.location.href = `/export_pdf?week=${curWeek}&year=${curYear}`;
      }
    });
  }

  if (todayBtn) {
    todayBtn.addEventListener("click", () => {
      const today = new Date();
      const tmp = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
      const dayNum = tmp.getUTCDay() || 7;
      tmp.setUTCDate(tmp.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1));
      const weekNo = Math.ceil((((tmp - yearStart) / 86400000) + 1) / 7);
      const isoYear = tmp.getUTCFullYear();


      window.location.href = `/?week=${weekNo}&year=${isoYear}`;
    });
  }

  function openAdv(){ if(modal){ modal.style.display = 'flex'; } }
  function closeAdv(){ if(modal){ modal.style.display = 'none'; } }

  if(randomBtn) randomBtn.addEventListener('click', openAdv);
  if(closeBtn) closeBtn.addEventListener('click', closeAdv);
  if(cancelBtn) cancelBtn.addEventListener('click', closeAdv);

  if(form){
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const days = Array.from(form.querySelectorAll('input.ar-day:checked')).map(i=>i.value);
      const payload = { week: curWeek, year: curYear, days: days.length? days : null, replace_existing: !!(replaceChk && replaceChk.checked) };
      try {
        const resp = await fetch('/randomize_custom', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        if(!resp.ok){ alert('Randomize failed'); return; }
        const data = await resp.json();
        window.location.href = `/?week=${curWeek}&year=${curYear}&notice=random&chg=${data.modified}`;
      } catch(err){ console.error(err); alert('Unexpected error'); }
    });
  }
})();
